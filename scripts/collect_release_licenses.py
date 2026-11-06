"""Inventory licenses from a real bundle and its exact build environment.

Run with the Python used to build the release. This is evidence collection,
not a legal clearance or a claim that metadata describes every vendored binary.
No installed credential/configuration files or direct_url metadata are exported.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
from email.parser import Parser
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote
import uuid


def canonical(name):
    return re.sub(r"[-_.]+", "-", str(name)).lower()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def license_path(path):
    name = path.name.lower()
    return bool(re.match(r"^(licen[cs]e|copying|copyright|notice|authors)([._-]|$)", name)) or any(
        part.lower() in {"licenses", "licences"} for part in path.parts[:-1]
    )


def toc_sources(path):
    if not path:
        return set()
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("Analysis TOC is unexpectedly large")
    value = ast.literal_eval(path.read_text(encoding="utf-8"))
    found = set()

    def visit(item):
        if isinstance(item, (list, tuple)):
            if len(item) == 3 and isinstance(item[1], str) and isinstance(item[2], str) and item[2] in {
                "PYMODULE", "PYSOURCE", "EXTENSION", "BINARY", "DATA"
            }:
                found.add(str(Path(item[1]).resolve()).casefold())
            for child in item:
                visit(child)

    visit(value)
    return found


def copy_text(source, target, provenance):
    if not source.is_file() or source.is_symlink() or source.stat().st_size > 8 * 1024 * 1024:
        return None
    raw = source.read_bytes()
    if b"\x00" in raw:
        return None
    # License text can use legacy encodings; preserve original bytes verbatim.
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return {"path": target.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "provenance": provenance}


def collect(bundle, output, analysis_toc=None, sdk_sites=(), node_license=None,
            node_version=None, project_license=None, supplements=None):
    bundle, output = bundle.resolve(), output.resolve()
    if not bundle.is_dir():
        raise ValueError("Bundle must be an existing directory")
    if output.exists() or output.is_relative_to(bundle):
        raise ValueError("Use a fresh output outside the bundle")
    sources = toc_sources(analysis_toc)
    output.mkdir(parents=True)
    components, failures, binary_paths = {}, [], []

    def component(kind, name, version, declaration="UNKNOWN"):
        key = (kind, canonical(name), str(version))
        if key not in components:
            components[key] = {"ecosystem": kind, "name": str(name), "version": str(version),
                "declared_license": str(declaration)[:12000], "evidence": [], "license_texts": [],
                "review_flags": []}
        return components[key]

    def preserve(c, source, relative, provenance):
        safe_id = re.sub(r"[^a-zA-Z0-9._-]", "_", f"{c['ecosystem']}-{c['name']}-{c['version']}")
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", source.name)
        target = output / "texts" / safe_id / (hashlib.sha256(relative.encode()).hexdigest()[:12] + "-" + safe_name)
        result = copy_text(source, target, provenance + ":" + relative)
        if result:
            result["path"] = target.relative_to(output).as_posix()
            if result not in c["license_texts"]:
                c["license_texts"].append(result)

    files = list(bundle.rglob("*"))
    for path in files:
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(bundle).as_posix()
        if path.suffix.lower() in {".exe", ".dll", ".pyd", ".so", ".dylib", ".node"}:
            binary_paths.append({"path": rel, "sha256": digest(path)})
        if path.name == "METADATA" and path.parent.name.endswith(".dist-info"):
            info = Parser().parsestr(path.read_text(encoding="utf-8"))
            if not info.get("Name") or not info.get("Version"):
                failures.append({"path": rel, "issue": "invalid_python_metadata"})
                continue
            c = component("pypi", info["Name"], info["Version"], info.get("License-Expression") or info.get("License") or "UNKNOWN")
            c["evidence"].append({"kind": "bundle_metadata", "path": rel, "sha256": digest(path)})
            for candidate in path.parent.rglob("*"):
                if license_path(candidate):
                    preserve(c, candidate, candidate.relative_to(bundle).as_posix(), "bundle")
        elif path.name == "package.json" and "node_modules" in path.parts:
            try:
                info = json.loads(path.read_text(encoding="utf-8"))
                if not info.get("name") or not info.get("version"):
                    continue
                c = component("npm", info["name"], info["version"], info.get("license", "UNKNOWN"))
                c["evidence"].append({"kind": "bundle_metadata", "path": rel, "sha256": digest(path)})
                # Do not attribute nested dependency licenses to their parent.
                for candidate in path.parent.rglob("*"):
                    local = candidate.relative_to(path.parent)
                    if "node_modules" not in local.parts and license_path(local):
                        preserve(c, candidate, candidate.relative_to(bundle).as_posix(), "bundle")
            except (ValueError, UnicodeError) as exc:
                failures.append({"path": rel, "issue": type(exc).__name__})

    environments = [("build_environment", list(metadata.distributions()))]
    for index, site in enumerate(sdk_sites):
        environments.append((f"sdk_environment_{index + 1}", list(metadata.distributions(path=[str(site)]))))
    build_pins = set()
    for label, distributions in environments:
        for distribution in distributions:
            name, version = distribution.metadata.get("Name"), distribution.version
            if not name or not version:
                continue
            if label == "build_environment":
                build_pins.add(f"{name}=={version}")
            key = ("pypi", canonical(name), version)
            owned = []
            for relative in distribution.files or []:
                source = Path(distribution.locate_file(relative))
                if str(source.resolve()).casefold() in sources:
                    owned.append(str(relative).replace("\\", "/"))
            if key not in components and not owned:
                continue
            c = component("pypi", name, version, distribution.metadata.get("License-Expression") or distribution.metadata.get("License") or "UNKNOWN")
            if owned:
                c["evidence"].append({"kind": "analysis_toc_exact_distribution_file_match", "environment": label,
                                      "matched_files": sorted(owned)})
            for relative in distribution.files or []:
                if license_path(Path(relative)):
                    preserve(c, Path(distribution.locate_file(relative)), str(relative).replace("\\", "/"), label)

    python = component("runtime", "Python", sys.version.split()[0], "PSF-2.0")
    python["evidence"].append({"kind": "collector_interpreter", "bundle_matching_required": True})
    preserve(python, Path(sys.base_prefix) / "LICENSE.txt", "Python-LICENSE.txt", "build_environment")
    if node_license:
        node = component("runtime", "Node.js", node_version or "UNSPECIFIED", "MIT AND bundled third-party notices")
        node["evidence"].append({"kind": "operator_supplied_official_license", "binary_version_independently_verify": True})
        preserve(node, node_license, "Node-LICENSE.txt", "official_runtime_license")
    if project_license:
        project = component("application", "K-Studio", "source-checkout", "SEE LICENSE")
        preserve(project, project_license, "LICENSE", "source_checkout")

    if supplements:
        supplement_root=supplements.resolve().parent
        entries=json.loads(supplements.read_text(encoding="utf-8"))
        for row in entries.get("components",[]):
            key=(row.get("ecosystem"),canonical(row.get("name","")),str(row.get("version","")))
            if key not in components or row.get("status") not in {"FETCHED_EXACT_REGISTRY_COMMIT","FETCHED_OFFICIAL_VERSION_TAG","FETCHED_REGISTRY_ATTESTATION_COMMIT","SAME_VERSION_PARENT_PACKAGE_LICENSE","BUNDLED_PARENT_EXAMPLE_LICENSE","CANONICAL_TERMS_FOR_EXPLICIT_DECLARATION"}:
                continue
            source=(supplement_root/row["path"]).resolve()
            if not source.is_relative_to(supplement_root) or digest(source)!=row["sha256"]:
                raise ValueError("Supplement license path/hash mismatch")
            c=components[key]
            preserve(c,source,row["path"],"verified_license_supplement")
            c["evidence"].append({"kind":"official_source_license_supplement","source_url":row["source_url"],
                "sha256":row["sha256"],"version_binding":row["status"],"git_commit":row.get("git_commit"),
                "verified_package_url":row.get("verified_package_url"),
                **{k:row[k] for k in ("declaration_evidence","parent_package","scope_note","registry_attestation_url","attestation_signature_independently_verified") if k in row}})
            if row.get("upstream_original_license_text_absent"):
                c["review_flags"].extend(["UPSTREAM_ORIGINAL_LICENSE_TEXT_ABSENT","STANDARD_LICENSE_TERMS_SUPPLIED_NOT_UPSTREAM_ORIGINAL"])
            if row.get("status")=="FETCHED_REGISTRY_ATTESTATION_COMMIT":c["review_flags"].append("ATTESTATION_SIGNATURE_NOT_INDEPENDENTLY_VERIFIED")
            if c["name"]=="benchmark" and row.get("status")=="CANONICAL_TERMS_FOR_EXPLICIT_DECLARATION":c["review_flags"].append("EMBEDDED_EXAMPLE_LICENSE_SCOPE_REVIEW")

    for c in components.values():
        if not c["license_texts"]:
            c["review_flags"].append("LICENSE_TEXT_MISSING")
        if c["declared_license"] in {"UNKNOWN", "None", ""}:
            c["review_flags"].append("LICENSE_DECLARATION_UNKNOWN")
        if re.search(r"(?i)(GPL|AGPL|LGPL|CPAL|MPL|EPL|CC-BY|BSD-4)", c["declared_license"]):
            c["review_flags"].append("RECIPROCAL_OR_ATTRIBUTION_TERMS_REVIEW")
    rows = sorted(components.values(), key=lambda c: (c["ecosystem"], c["name"].lower(), c["version"]))
    report = {"schema": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "components": rows,
        "analysis_toc": {"supplied": bool(analysis_toc), "sha256": digest(analysis_toc) if analysis_toc else None,
                         "source_file_count": len(sources)},
        "native_binaries_requiring_vendor_notice_review": binary_paths,
        "parse_failures": failures,
        "limitations": ["Evidence inventory, not legal approval or exhaustive transitive source audit.",
            "Bundled binary vendored components may not appear in package metadata; inspect vendor notices.",
            "Build environment pins are reproducibility evidence, not all shipped dependencies.",
            "Runtime version declarations require independent binary/build verification.",
            "Without Analysis TOC, Python modules hidden inside PYZ may not be enumerated."],
        "license_clearance": "REVIEW_REQUIRED"}
    (output / "license-inventory.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    pins = sorted({f"{c['name']}=={c['version']}" for c in rows if c["ecosystem"] == "pypi"}, key=str.lower)
    for filename, lines in [("requirements-bundled.lock", pins), ("requirements-build-environment.lock", sorted(build_pins, key=str.lower))]:
        (output / filename).write_text("# Exact observed versions; not a dependency resolver or source hash lock.\n" + "\n".join(lines) + "\n", encoding="utf-8")
    bom = {"bomFormat": "CycloneDX", "specVersion": "1.6", "serialNumber": "urn:uuid:" + str(uuid.uuid4()), "version": 1,
        "metadata": {"timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
        "components": [{"type": "application" if c["ecosystem"] in {"application", "runtime"} else "library",
            "bom-ref": f"{c['ecosystem']}:{c['name']}@{c['version']}", "name": c["name"], "version": c["version"],
            **({"purl": f"pkg:{c['ecosystem']}/{quote(c['name'], safe='/')}@{quote(c['version'], safe='')}"} if c["ecosystem"] in {"npm", "pypi"} else {}),
            "properties": [{"name": "kstudio:license-evidence", "value": json.dumps(c["license_texts"], ensure_ascii=False)},
                           {"name": "kstudio:declared-license-unverified", "value": c["declared_license"]},
                           {"name": "kstudio:review-flags", "value": ",".join(c["review_flags"])}]} for c in rows]}
    (output / "sbom.cdx.json").write_text(json.dumps(bom, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"components": len(rows), "license_texts": sum(len(c["license_texts"]) for c in rows),
               "missing_text_components": sum(not c["license_texts"] for c in rows), "native_binaries": len(binary_paths),
               "upstream_original_text_absent_standard_terms_supplied": sum("UPSTREAM_ORIGINAL_LICENSE_TEXT_ABSENT" in c["review_flags"] for c in rows),
               "bundled_python_pins": len(pins), "clearance": "REVIEW_REQUIRED"}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--analysis-toc", type=Path)
    parser.add_argument("--sdk-site", type=Path, action="append", default=[])
    parser.add_argument("--node-license", type=Path)
    parser.add_argument("--node-version")
    parser.add_argument("--project-license", type=Path)
    parser.add_argument("--supplements", type=Path)
    args = parser.parse_args()
    print(json.dumps(collect(args.bundle, args.output, args.analysis_toc, args.sdk_site,
                             args.node_license, args.node_version, args.project_license, args.supplements)))
