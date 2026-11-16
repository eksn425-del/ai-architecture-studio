"""Conservative contextual defaults; no filename or visual-content inference."""
import json
import hashlib
import re
from pathlib import Path

TARGET = re.compile(r'目标(?:建筑|参考)?(?:图|照片)|原图|参考图|补充.{0,12}(?:视角|侧面|背面)|(?:同一|同一栋).{0,14}(?:建筑|视角)|多视角|新(?:的)?视角|(?:背面|侧面)照片|这是.{0,6}(?:背面|侧面)图|additional (?:view|reference)|source (?:image|photo)',re.I)
DEFECT = re.compile(r'这里.{0,8}(?:缝|错|问题|漏|重叠)|(?:模型|当前|建模|结果|渲染).{0,12}(?:截图|错位|裂缝|重叠|漏面|问题)|问题(?:定位|截图)|缺陷(?:图|截图)|截图.{0,12}(?:缝|错位|重叠|漏面)|(?:defect|issue) screenshot|this.{0,8}(?:gap|overlap|misalignment)',re.I)
MIXED = re.compile(r'分别|混合|其中|一张.{0,12}另一张|前.{0,4}后|第[一二三四五六七八12345678].{0,12}(?:图|张)|mixed',re.I)


def infer_reference_role(project: Path, content: bytes, references, *, has_model: bool,
                         context: str = '', batch_count: int = 1, exclude_source: str = '') -> tuple[str,str]:
    """Return (role, auditable reason), leaving ambiguity unknown."""
    text=(context or '')[:3000]
    if re.search(r'不是[^，。；\n]{0,16}(?:目标|建筑|要建|参考)|操作界面|界面截图|日志截图|报错截图|not.{0,12}(?:target|reference)',text,re.I):
        return 'unknown','explicit_non_target_or_interface'
    target=bool(TARGET.search(text));defect=bool(DEFECT.search(text))
    if (target and defect) or MIXED.search(text) or ((target or defect) and re.search(r"(?:不是|并非)[^，。；\n]{0,12}(?:问题|缺陷|目标|参考|原图|建筑|截图)|不要当",text)):
        return 'unknown','mixed_or_conflicting_context'
    digest=hashlib.sha256(content).hexdigest();known=set();versions=set();prior=[]
    for ref in references:
        if ref.type!='image' or ref.source==exclude_source:continue
        prior.append(ref)
        path=project/ref.source
        if not path.resolve().is_relative_to(project.resolve()) or path.is_symlink() or not path.is_file():continue
        if hashlib.sha256(path.read_bytes()).hexdigest()==digest:
            known.add(ref.evidence_role)
            if ref.evidence_role=='defect_location':versions.add(json.dumps(ref.evidence_model_revisions,sort_keys=True))
    if known:
        if len(known)!=1 or 'unknown' in known:return 'unknown','duplicate_role_uncertain'
        role=next(iter(known))
        if role=='defect_location' and len(versions)!=1:return 'unknown','duplicate_version_conflict'
        if (role=='defect_location' and target) or (role=='target_building' and defect):
            return 'unknown','duplicate_context_conflict'
        return role,'same_image_previous_role'
    if target:return 'target_building','explicit_current_target_context'
    if defect:
        return ('defect_location','current_problem_context') if has_model else ('unknown','problem_without_model_version')
    if not has_model and not prior and batch_count==1:
        return 'target_building','first_image_new_project'
    return 'unknown','needs_current_context'


def resolve_pending_reference_defaults(project, context, message, revisions):
    """Resolve only fresh auto uploads, never legacy or already-submitted evidence."""
    changed=False
    pending=[r for r in context.references if r.type=='image'
             and r.role_origin in ('awaiting_context','context_default') and not r.submitted_at]
    for ref in pending:
        if ref.role_origin=='context_default' and not (TARGET.search(message) or DEFECT.search(message) or MIXED.search(message) or re.search(r'不是|并非|不要当|操作界面|界面截图|日志截图|报错截图',message)):
            continue
        path=project/ref.source
        if path.is_symlink() or not path.resolve().is_relative_to(project.resolve()) or not path.is_file():continue
        # Other unresolved files from the same upload are not positive role evidence.
        prior=[r for r in context.references if r not in pending]
        role,reason=infer_reference_role(project,path.read_bytes(),prior,has_model=bool(ref.evidence_model_revisions),
            context=message,batch_count=max(ref.role_batch_count,len(pending)),exclude_source=ref.source)
        if role!=ref.evidence_role or reason!=ref.role_reason:
            ref.evidence_role=role;ref.role_origin='awaiting_context' if role=='unknown' else 'context_default';ref.role_reason=reason;changed=True
    return changed


def duplicate_defect_version(project,content,references):
    """Return historical version only when identical defect evidence agrees."""
    digest=hashlib.sha256(content).hexdigest();versions=[]
    for ref in references:
        if ref.type!='image' or ref.evidence_role!='defect_location':continue
        path=project/ref.source
        if path.is_symlink() or not path.resolve().is_relative_to(project.resolve()) or not path.is_file():continue
        if hashlib.sha256(path.read_bytes()).hexdigest()==digest:versions.append(ref.evidence_model_revisions)
    if versions:return dict(versions[0]) if all(v==versions[0] for v in versions) else {}
    return None
