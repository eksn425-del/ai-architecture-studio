"""Export only public dependency notices; retain build source/file maps privately."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


def export(evidence:Path,destination:Path):
    evidence=evidence.resolve();destination=destination.resolve()
    if destination.exists():raise ValueError('Preserve existing notices; use a fresh destination')
    inventory=json.loads((evidence/'license-inventory.json').read_text(encoding='utf-8'))
    bom=json.loads((evidence/'sbom.cdx.json').read_text(encoding='utf-8'))
    destination.mkdir(parents=True)
    rows=[]
    for c in inventory['components']:
        row={k:c[k] for k in ('ecosystem','name','version','declared_license','review_flags')}
        row['license_texts']=[]
        for text in c['license_texts']:
            source=(evidence/text['path']).resolve()
            if not source.is_relative_to(evidence):raise ValueError('License evidence escapes input directory')
            raw=source.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=text['sha256']:raise ValueError('License evidence bytes changed')
            target=destination/text['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            row['license_texts'].append({k:text[k] for k in ('path','sha256','bytes')})
        row['official_source_evidence']=[{k:entry[k] for k in ('source_url','sha256','version_binding','git_commit','verified_package_url') if entry.get(k)}
            for entry in c['evidence'] if entry['kind']=='official_source_license_supplement']
        rows.append(row)
    public={'schema':1,'generated_at':inventory['generated_at'],'scope':'Observed bundled dependencies and license text evidence; not legal clearance.',
            'license_clearance':'REVIEW_REQUIRED','components':rows,
            'limitations':inventory['limitations'],'native_binaries_requiring_vendor_notice_review':inventory['native_binaries_requiring_vendor_notice_review']}
    lookup={f"{c['ecosystem']}:{c['name']}@{c['version']}":c for c in rows}
    for component in bom['components']:
        original=lookup[component['bom-ref']]
        component['properties']=[{'name':'kstudio:license-texts','value':json.dumps(original['license_texts'],ensure_ascii=False)},
            {'name':'kstudio:declared-license-unverified','value':original['declared_license']},
            {'name':'kstudio:review-flags','value':','.join(original['review_flags'])},
            {'name':'kstudio:official-source-evidence','value':json.dumps(original['official_source_evidence'],ensure_ascii=False)}]
    for filename,value in [('dependency-notices.json',public),('sbom.cdx.json',bom)]:
        content=json.dumps(value,ensure_ascii=False,indent=2)
        if re.search(r'(?i)[a-z]:[\\/]+users[\\/]',content):raise ValueError('Private Windows user path in public metadata')
        (destination/filename).write_text(content,encoding='utf-8')
    shutil.copyfile(evidence/'requirements-bundled.lock',destination/'requirements-bundled.lock')
    missing=[c for c in rows if not c['license_texts']]
    notice='''# Third-party dependency evidence

This folder preserves original license/notice text bytes and their SHA256 hashes.
The inventory describes the actual packaged dependency files. Declared license names
and collected text are evidence, not a determination that all distribution obligations
have been fulfilled. Native binaries can contain additional vendored components.

The private build-source map and complete build-environment snapshot are excluded.
The bundled Python version list records observed versions; it is not a source hash lock.
Public upstream license supplements identify their exact commit or verified release tag.

License clearance: REVIEW_REQUIRED. Missing texts are explicitly listed below and are
not replaced with generic license templates. Nested example manifests describe source
files redistributed inside upstream packages, not separately activated applications.

## Components without a collected license text

'''
    notice+='\n'.join(f"- {c['ecosystem']} `{c['name']}@{c['version']}` — declared: {c['declared_license']}" for c in missing)+'\n'
    (destination/'README.md').write_text(notice,encoding='utf-8')
    return {'components':len(rows),'missing_text_components':len(missing),'license_clearance':'REVIEW_REQUIRED'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('evidence',type=Path);parser.add_argument('destination',type=Path)
    args=parser.parse_args();print(json.dumps(export(args.evidence,args.destination)))
