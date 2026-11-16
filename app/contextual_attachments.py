"""Bound textual attachment intent to host-owned fresh image identities.

Model roles are suggestions, not visual truth or historical provenance.
"""
import hashlib
import re
from pathlib import Path
from .reference_defaults import duplicate_defect_version


def attachment_snapshot(project, context):
    result=[]
    for ref in context.references:
        if ref.type!='image':continue
        path=project/ref.source
        if path.is_symlink() or not path.resolve().is_relative_to(project.resolve()) or not path.is_file():
            raise ValueError('Image evidence must be a regular file within the project.')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        result.append({'attachment_id':hashlib.sha256((ref.source+'\0'+digest).encode()).hexdigest(),
            'source':ref.source,'sha256':digest,'role':ref.evidence_role,'role_origin':ref.role_origin,
            'source_turn':ref.evidence_turn_id,'model_revisions':ref.evidence_model_revisions,
            'editable':ref.role_origin in ('context_default','awaiting_context') and (not ref.submitted_at or (ref.role_clarification_pending and ref.evidence_role=='unknown'))})
    return result


def apply_attachment_intent(project, context, snapshot, decisions, message):
    if attachment_snapshot(project,context)!=snapshot:raise ValueError('Attachment evidence changed during interpretation.')
    if not isinstance(decisions,list):raise ValueError('Attachment decisions must be a list.')
    allowed={x['attachment_id']:x for x in snapshot if x['editable']}
    seen=set();updates=[]
    for decision in decisions:
        if not isinstance(decision,dict) or set(decision)!={'attachment_id','role','evidence_quote'}:raise ValueError('Invalid attachment decision.')
        ident=decision['attachment_id'];role=decision['role'];quote=decision['evidence_quote']
        if ident not in allowed or ident in seen:raise ValueError('Only fresh automatic attachment roles can be interpreted.')
        if role not in ('target_building','defect_location','supporting','unknown'):raise ValueError('Unknown attachment role.')
        if not isinstance(quote,str) or (role!='unknown' and (not quote.strip() or quote not in message)):raise ValueError('Role needs evidence from the actual current user message.')
        seen.add(ident);item=allowed[ident]
        ref=next(r for r in context.references if r.source==item['source'])
        same=[x for x in snapshot if x['sha256']==item['sha256'] and x['attachment_id']!=ident]
        historical_defects=[x for x in same if x['role']=='defect_location']
        role_words={'target_building':r'目标(?:建筑)?(?:图|照片)?|参考图|原图|target|reference','defect_location':r'问题(?:图|截图)?|缺陷(?:图|截图)?|defect|issue','supporting':r'辅助|补充资料'}.get(role)
        if role_words:
            denial=re.compile(r'(?:不是|并非|不要当(?:成)?|not\s+)[^，。；;\n]{0,12}(?:'+role_words+r')',re.I)
            if denial.search(quote) and not re.search(role_words,denial.sub('',quote),re.I):role='unknown'
        known={x['role'] for x in same if not x['editable'] and x['role']!='unknown'}
        if known and (len(known)>1 or role not in known):role='unknown'
        # A fresh source identity never launders old defect pixels into target truth.
        if historical_defects and role!='defect_location':role='unknown'
        revisions=ref.evidence_model_revisions
        if role=='defect_location':
            prior=duplicate_defect_version(project,(project/ref.source).read_bytes(),[r for r in context.references if r is not ref])
            if prior is not None:revisions=prior
            if not revisions:role='unknown'
        updates.append((ref,role,revisions))
    changed=False
    for ref,role,revisions in updates:
        if ref.evidence_role!=role or ref.evidence_model_revisions!=revisions:
            ref.evidence_role=role;ref.evidence_model_revisions=revisions
            if role!='unknown':ref.role_clarification_pending=False
            ref.role_reason='readonly_current_message_interpretation';ref.role_origin='awaiting_context' if role=='unknown' else 'context_default';changed=True
    return changed


def restore_defect_feedback_state(project, session, context):
    """Restore lifecycle only; independent current-user intent still grants the edit.

    Uploads initially invalidate approval while their purpose is unknown. A fresh
    current-model defect screenshot does not change the approved target building.
    Keep native identity, current geometry/view hashes and original-source proof.
    """
    if session.status != 'ready' or not session.model_path or session.reconstruction_state not in {'clarifying', 'planned'}:
        return False
    pending = [ref for ref in context.references if not ref.submitted_at]
    from .reference_roles import current_model_revisions
    revisions = current_model_revisions(project, session.ruby_state)
    if not revisions or not pending or any(ref.type != 'image' or ref.evidence_role != 'defect_location' or ref.evidence_model_revisions != revisions for ref in pending):
        return False
    submitted = {source for message in context.conversation for source in (message.metadata or {}).get('attachments', [])}
    if any(source not in submitted for source in [*context.brief.source_files, *context.site.source_files]):
        return False # New taskbook/site inputs still require replanning.
    from .contextual_turn import read_plan_card
    from .modeling_quality import load_current_independent_visual_review
    if not read_plan_card(project) or not load_current_independent_visual_review(project, session.ruby_state, include_accepted=True):
        return False
    session.reconstruction_state = 'building'
    session.thread_id = '' # Image/tool continuity is checked afresh by the runtime.
    session.plan_started_ns = 0
    session.plan_request_message = ''
    return True
