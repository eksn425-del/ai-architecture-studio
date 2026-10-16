"""Read-only audit of actual host masked-path snapshots and committed receipt.

Geometry protection is independent of source fidelity and native delivery. The
model GUID can legitimately advance on a native write; bind it to the actual
committed writer receipt instead of silently ignoring identity changes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def validate_protected_graph(snapshot: dict) -> None:
    pool = snapshot.get("protected_definition_graph", {})
    definitions = pool.get("definitions")
    identities = pool.get("identities")
    if not isinstance(definitions, dict) or not definitions or not isinstance(identities, list):
        raise ValueError("Incomplete protected definition graph")
    parsed = {}
    for ref, entry in definitions.items():
        canonical = entry.get("canonical_payload_json")
        if not isinstance(canonical, str) or hashlib.sha256(canonical.encode("utf8")).hexdigest() != ref:
            raise ValueError("Protected native definition payload SHA mismatch")
        parsed[ref] = json.loads(canonical)
    roots = set()
    def nodes(value):
        if isinstance(value, dict):
            if "canonical_geometry_json" in value:
                canonical = value["canonical_geometry_json"]
                if hashlib.sha256(canonical.encode("utf8")).hexdigest() != value.get("geometry_material_sha256"):
                    raise ValueError("Protected instance payload SHA mismatch")
                ref = json.loads(canonical)["instance"]["definition_ref"]
                if ref != value.get("definition_ref"):
                    raise ValueError("Protected instance reference mismatch")
                roots.add(ref)
            for child in value.values():
                nodes(child)
        elif isinstance(value, list):
            for child in value:
                nodes(child)
    for key in ("masked_root", "external", "required_deep_keep"):
        nodes(snapshot.get(key))
    active, visited = set(), set()
    def visit(ref, depth=0):
        if ref not in parsed or ref in active or depth > 24:
            raise ValueError("Missing, cyclic or too-deep protected definition reference")
        if ref in visited:
            return
        active.add(ref)
        for child in parsed[ref]["instances"]:
            visit(child["definition_ref"], depth+1)
        active.remove(ref)
        visited.add(ref)
    for ref in roots:
        visit(ref)
    if not roots or visited != set(parsed):
        raise ValueError("Protected reference graph missing roots or contains unreferenced definitions")
    identity_refs = set()
    for entry in identities:
        ref = entry.get("definition_ref")
        if (ref not in parsed or entry.get("name") != parsed[ref]["definition_name"]
                or not isinstance(entry.get("child_instance_pids"), list)
                or len(entry["child_instance_pids"]) != len(parsed[ref]["instances"])
                or any(type(pid) is not int or pid <= 0 for pid in entry["child_instance_pids"])):
            raise ValueError("Protected persistent identity table is incomplete")
        identity_refs.add(ref)
    if identity_refs != set(parsed):
        raise ValueError("Protected definition identity coverage missing")


def audit(before: dict, after: dict, writer: dict) -> dict:
    result = {"schema_version": 1, "status": "BLOCKED", "failures": [],
              "visual_quality": "NOT_ASSESSED", "native_delivery": "NOT_ASSESSED"}
    try:
        for value in (before, after):
            if value.get("collector") != "KStudioPathScopeNative/1" or value.get("geometry_writes") != 0:
                raise ValueError("Requires genuine host read-only path snapshots")
            snap = value["snapshot"]
            for key in ("paths", "masked_root", "document_loose_sha", "external", "presentation_sha", "model_path", "model_guid"):
                if key not in snap:
                    raise ValueError(f"Incomplete native path snapshot: {key}")
        old, new = before["snapshot"], after["snapshot"]
        scope = writer["last_edit_scope_receipt"]
        if scope.get("status") != "passed" or scope.get("guard") not in {"deep_exact_paths_v1", "deep_exact_paths_v2", "deep_exact_paths_graph_v1"}:
            raise ValueError("Missing actual exact-path precommit receipt")
        if scope.get("guard") == "deep_exact_paths_graph_v1":
            for snap in (old, new):
                if snap.get("contract") != "deep_exact_paths_graph_v1":
                    raise ValueError("Native scope contract mismatch")
                validate_protected_graph(snap)
            if scope.get("allowed_creation_paths") != old.get("creation_paths") or old.get("creation_paths") != new.get("creation_paths"):
                raise ValueError("Host-approved exact creation paths differ")
        if scope.get("allowed_paths") != old["paths"] or old["paths"] != new["paths"]:
            raise ValueError("Native snapshots and actual writer target declarations differ")
        if writer["root_pid"] != old["masked_root"]["metadata"]["pid"]:
            raise ValueError("Writer/owned-root PID mismatch")
        if writer["revision"] != after["revision"] or after["revision"] != before["revision"] + 1:
            raise ValueError("Requires one actual committed revision step")
        identity_source = "committed_writer_receipt"
        if writer["model_guid"] != new["model_guid"]:
            proof = after.get("identity_proof", {})
            root_name = old["masked_root"]["metadata"].get("name", "")
            if not (proof.get("collector") == "KStudioOwnedGuidReadback/1" and proof.get("read_only") is True
                    and proof.get("model_guid") == new["model_guid"] and proof.get("model_path") == old["model_path"]
                    and proof.get("root_pid") == writer["root_pid"] and proof.get("revision") == writer["revision"]
                    and proof.get("project_id") and root_name == "Architecture " + proof["project_id"]):
                raise ValueError("GUID drift requires actual native path/root/project/revision readback")
            identity_source = "native_owned_identity_readback_after_autosave_or_save"
        if not writer["last_verification"].get("verified") or not writer["last_precommit_keep_guard"].get("passed"):
            raise ValueError("Actual committed verification/KEEP missing")
        left = {k: v for k, v in old.items() if k != "model_guid"}
        right = {k: v for k, v in new.items() if k != "model_guid"}
        equal = left == right
        digest = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        result.update(status="PASS" if equal else "FAIL", protected_snapshot_equal=equal,
                      before_protected_sha256=digest(left), after_protected_sha256=digest(right),
                      before_guid=old["model_guid"], after_guid=new["model_guid"],
                      guid_transition_verified=True, revision=after["revision"],
                      guid_identity_verification=identity_source,
                      allowed_paths=old["paths"], root_pid=writer["root_pid"])
        if not equal:
            result["failures"].append("Native protected geometry/material/PID/ancestor/loose/presentation snapshot changed")
    except (KeyError, TypeError, ValueError) as exc:
        result["failures"].append(str(exc))
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path); p.add_argument("after", type=Path); p.add_argument("writer", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args(); r = audit(*(json.loads(x.read_text(encoding="utf-8")) for x in (a.before, a.after, a.writer)))
    text = json.dumps(r, ensure_ascii=False, indent=2) + "\n"
    if a.output: a.output.write_text(text, encoding="utf-8")
    print(text); return 0 if r["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
