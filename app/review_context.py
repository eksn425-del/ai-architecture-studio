"""Provider-neutral, host-bound independent review evidence and intent contract.

Transport runtimes supply validated capture paths; no provider may infer image
roles, approval, or requirement resolution from Builder prose.
"""
from __future__ import annotations
import hashlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from .reference_assets import discover_project_reference_images
from .reference_roles import (reference_manifest, manifest_fingerprint, role_labels,
    load_review_history, requirement_states, load_approved_design_scope,
    validate_review_requirements, validate_review_resolutions, current_model_revisions)
from .modeling_quality import build_visual_critic_prompt, parse_visual_critique_response, load_facade_schedule
from .reconstruction_evidence import load_reconstruction_evidence, fidelity_contract_summary


def review_intent_context(project_dir: Path) -> dict:
    from .design_scope_approval import current_execution_instruction, current_reference_fingerprint
    scope = load_approved_design_scope(project_dir)
    # Preserve invalidation/version metadata for identity, but never give stale
    # or invalid scope features authority to supersede protected requirements.
    if scope and (scope.get('valid') is not True or
                  scope.get('reference_manifest_fingerprint') != current_reference_fingerprint(project_dir)):
        # Even invalid plan prose can bias a reviewer toward an obsolete goal.
        # Expose only typed audit metadata, retaining raw identity by digest.
        # The original host scope remains unchanged on disk for audit.
        scope = {'version': scope.get('version') if type(scope.get('version')) is int else 0,
                 'features': [], 'valid': False,
                 'invalidation_reason': 'invalid_or_stale_host_scope',
                 'invalid_scope_sha256': review_context_fingerprint(scope)}
    return {'approved_design_scope': scope,
            'current_user_instruction': current_execution_instruction(project_dir)}


def review_context_fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def current_review_context_fingerprint(project_dir: Path) -> str:
    manifest = reference_manifest(project_dir, discover_project_reference_images(project_dir, categories=('reference',)))
    return review_context_fingerprint({
        'target_manifest_fingerprint': manifest_fingerprint([item for item in manifest if item['role'] == 'target_building']),
        **review_intent_context(project_dir)})


@dataclass
class ReviewContext:
    project_dir: Path
    revisions: dict
    manifest: list
    history: list
    images: list
    image_hashes: dict
    evidence_hashes: dict
    prompt: str
    evidence_prompt: str
    metadata: dict


def prepare_review_context(project_dir: Path, revisions: dict, captures: dict, pairs: list) -> ReviewContext:
    sources = discover_project_reference_images(project_dir, categories=("reference",))
    manifest = reference_manifest(project_dir, sources)
    fingerprint = manifest_fingerprint(manifest)
    targets = {item['source'] for item in manifest if item['role'] == 'target_building'}
    if not targets:
        raise ValueError("Reference roles are unresolved: confirm target_building versus defect_location before visual review.")
    if any(pair.get('source_ref') not in targets for pair in pairs):
        raise ValueError("Source-matched fidelity pairs may cite only target_building images, not defect screenshots.")
    labels = role_labels(manifest)
    target_fingerprint = manifest_fingerprint([item for item in manifest if item["role"] == "target_building"])
    history = load_review_history(project_dir, target_fingerprint)
    images = list(sources)
    for name, path in captures.items():
        labels.append("CURRENT canonical " + name)
        images.append(path)
    for pair in pairs:
        path = (project_dir / pair["current_view"]).resolve()
        label = "CURRENT source-matched " + pair["label"] + " [SOURCE TARGET " + pair["source_ref"] + "]"
        # Multiple source pairs can reference the same current screenshot.
        # Keep every association in its caption, attach the actual image once.
        existing = next((i for i, image in enumerate(images) if image.resolve() == path), None)
        if existing is None:
            labels.append(label)
            images.append(path)
        elif label not in labels[existing].split("; "):
            labels[existing] += "; " + label
    intent_context = review_intent_context(project_dir)
    approved_scope = intent_context["approved_design_scope"]
    current_instruction = intent_context["current_user_instruction"]
    image_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in images}
    prompt = build_visual_critic_prompt([label for label, item in zip(labels, manifest) if item["role"] == "target_building"], labels[len(sources):])
    prompt += "\nImages below follow this exact order:\n" + "\n".join(
        f"{index + 1}. {label}" for index, label in enumerate(labels))
    prompt += ("\nInventory only elements actually shown by this project's SOURCE before judging CURRENT. "
               "If a source contact sheet has multiple views, use their shared landmarks to infer one consistent "
               "building; do not borrow a roof, canopy, annex, plants or other element from a previous test case. "
               "Prioritize source-backed silhouette, openings, roof/wall/window assembly, clearances and joints; "
               "unobserved hidden regions are inferred, not proof of mismatch. Do not trust Builder claims. "
               "KEEP only geometry whose source-backed proportions are correct; use named paths only when known. "
               "Do not protect an entire roof or volume unless all its visible source-backed parts are correct. "
               "Do not run commands or edit files; answer the review envelope directly from images.")
    prompt += ("\nISSUE LOCATION images are historical defect evidence, never a restoration target. "
               "UNKNOWN ROLE and SUPPORTING images cannot prove source fidelity. Their absence of an element is not evidence to remove it. "
               "Use stable feature_id values and explicit desired_state for each correction. "
               "Return <review_requirements>JSON array</review_requirements>, one entry per issue, or [] for no issues. "
               "Each entry must contain feature_id (stable lowercase path), desired_state, source_ref (exact SOURCE TARGET path), "
               "and model_revisions equal to " + json.dumps(revisions, sort_keys=True) + ". "
               "If prior intent contradicts current evidence, do not oscillate or hide it; report unresolved uncertainty. "
               "Requirement states (resolved intent remains protected; omission does not resolve): " + json.dumps(requirement_states(history), ensure_ascii=False)
               + "\nUse relation new for new features. For relation unchanged, copy the prior desired_state and any prior intent "
               "exactly, including its original language; put new observations, scope exclusions and remaining uncertainty in evidence. "
               "Unchanged means unchanged requirement text, not a translation or paraphrase of the same intent. "
               "For same-intent translation/paraphrase/refinement use equivalent/refines, "
               "prior_requirement_id and evidence explaining the SAME intent from current source/capture. Use regression for the same defect reappearing after resolution. Preserve a stable intent "
               "{property,value} when provided; changed wording alone is not conflict. Opposite intent is NOT refinement. "
               "Only a feature-specific host approved scope permits supersedes: cite design_scope_version and approved_requested_state exactly. "
               "To retire a satisfied old requirement return <requirement_resolutions>JSON array</requirement_resolutions> with feature_id, "
               "prior_requirement_id, status=resolved, source_ref, model_revisions and current evidence. Never resolve by omission. "
               "Host-approved design scope: " + json.dumps(approved_scope, ensure_ascii=False))
    prompt += ("\nExact current host-granted user instruction: " + json.dumps(current_instruction, ensure_ascii=False)
               + "\nAssess the requested change separately from remaining whole-source differences. "
               "Do not tell the Builder to reverse an explicitly requested change merely to restore an old requirement. "
               "When feature approval is stale or conflicts, retain the unresolved requirement and clearly report the "
               "scope conflict; do not silently supersede it, grant new permission or demand oscillating edits. "
               "Builder-authored notes are not a substitute for this host-bound input.")
    schedule = load_facade_schedule(project_dir)
    reconstruction_evidence = load_reconstruction_evidence(project_dir, strict=True)
    fidelity_rule = fidelity_contract_summary(reconstruction_evidence)
    evidence_prompt = (
        "SOURCE images come first. CURRENT SketchUp review images follow in canonical order. "
        "Judge visible source fidelity independently from the Builder. Do not infer success from tool logs, code, receipts or prior prose. "
        "The compact facade schedule below is source-facing project evidence: user_confirmed facts outrank observed estimates; inferred facts are advisory and may be wrong.\n"
        "Apply the reconstruction fidelity contract strictly. For a single image, judge the source-visible view hardest and do not penalize plausible hidden inference unless it contradicts visible evidence. "
        "For full evidence, any supplied CAD/floorplan/exterior/interior fact is a hard constraint; do not return NEEDS_FIX:NO while an evidenced region visibly contradicts it.\n"
        "FIDELITY_CONTRACT: " + fidelity_rule + "\n"
        + ("RECONSTRUCTION_EVIDENCE:\n" + json.dumps(reconstruction_evidence, ensure_ascii=False)[:12000] + "\n"
           if reconstruction_evidence else "RECONSTRUCTION_EVIDENCE: unavailable\n")
        + ("FACADE_SCHEDULE:\n" + json.dumps(schedule, ensure_ascii=False)[:12000]
           if schedule else "FACADE_SCHEDULE: unavailable")
    )
    evidence_paths = [path.with_suffix('.evidence.json') for path in images]
    evidence_paths += [project_dir / 'runtime/agent_workspace/notes' / name
                       for name in ('reconstruction_evidence.json', 'facade_schedule.json')]
    evidence_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
                       for path in evidence_paths}
    metadata = {'reference_manifest': manifest, 'reference_manifest_fingerprint': fingerprint,
                'target_manifest_fingerprint': target_fingerprint,
                'approved_design_scope': approved_scope, 'current_user_instruction': current_instruction}
    metadata['review_context_fingerprint'] = review_context_fingerprint({
        'target_manifest_fingerprint': target_fingerprint,
        'approved_design_scope': approved_scope, 'current_user_instruction': current_instruction})
    return ReviewContext(project_dir, dict(revisions), manifest, history, images, image_hashes, evidence_hashes, prompt, evidence_prompt, metadata)


def validate_review_context_current(context: ReviewContext) -> None:
    project = context.project_dir
    sources = discover_project_reference_images(project, categories=('reference',))
    if reference_manifest(project, sources) != context.manifest:
        raise ValueError('Review references changed during review; recapture current evidence.')
    fallback = {key: {'revision': value} for key, value in context.revisions.items()}
    if current_model_revisions(project, fallback) != context.revisions:
        raise ValueError('Review model revision changed during review; recapture current evidence.')
    if any(hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest
           for path, digest in context.image_hashes.items()):
        raise ValueError('Review image changed during inference; recapture before correction.')
    for filename, digest in context.evidence_hashes.items():
        path = Path(filename)
        current = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if current != digest:
            raise ValueError('Review evidence changed during inference; recapture current evidence.')
    intent = review_intent_context(project)
    if intent['approved_design_scope'] != context.metadata['approved_design_scope']:
        raise ValueError('Approved design scope changed during review; repeat against current intent.')
    if intent['current_user_instruction'] != context.metadata['current_user_instruction']:
        raise ValueError('Current user instruction changed during review; repeat against current intent.')
    if load_review_history(project, context.metadata['target_manifest_fingerprint']) != context.history:
        raise ValueError('Requirement history changed during review; repeat against current intent.')


def finalize_review_context(context: ReviewContext, reply: str) -> dict:
    validate_review_context_current(context)
    critique = parse_visual_critique_response(reply)
    if critique.malformed or critique.needs_fix is None:
        raise ValueError('Independent Critic returned an invalid envelope; no Builder fallback is permitted.')
    try:
        resolutions = validate_review_resolutions(reply, manifest=context.manifest,
            revisions=context.revisions, history=context.history)
        requirements = validate_review_requirements(reply, manifest=context.manifest,
            revisions=context.revisions, history=context.history, issue_count=len(critique.issues),
            approved_scope=context.metadata['approved_design_scope'])
        if {item['feature_id'] for item in resolutions} & {item['feature_id'] for item in requirements}:
            raise ValueError('A feature cannot be resolved and still require correction in one review.')
    except ValueError as error:
        rejected = context.project_dir / 'runtime/rejected_visual_reviews'
        if rejected.is_symlink():
            raise ValueError('Unsafe rejected review evidence directory.') from error
        rejected.mkdir(parents=True, exist_ok=True)
        rejection_id = uuid.uuid4().hex
        with (rejected / (rejection_id + '.json')).open('x', encoding='utf-8') as stream:
            json.dump({'schema_version': 1, 'status': 'rejected_not_accepted', 'error': str(error),
                'model_revisions': context.revisions, **context.metadata,
                'image_sha256': context.image_hashes, 'prior_requirements': requirement_states(context.history),
                'critique': reply}, stream, ensure_ascii=False, indent=2)
        raise ValueError(f'{error} Rejected independent review evidence: {rejection_id}.') from error
    record = {'manifest_fingerprint': context.metadata['target_manifest_fingerprint'],
        'model_revisions': context.revisions, 'requirements': requirements, 'resolutions': resolutions,
        'approved_design_scope': context.metadata['approved_design_scope'],
        'current_user_instruction': context.metadata['current_user_instruction']}
    history_path = context.project_dir / 'runtime/reference_role_review_history.jsonl'
    if history_path.is_symlink() or history_path.parent.is_symlink():
        raise ValueError('Unsafe role review history.')
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    return {**context.metadata, 'review_requirements': requirements, 'requirement_resolutions': resolutions}
