"""Package only reviewed cloud/website sources; no .env, runtime or credentials.

Run in the cloud acceptance environment to record its exact dependency closure.
This produces SOURCE, never a built container image or deployment claim.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata as metadata
import json
import platform
import subprocess
import sys
import zipfile
from pathlib import Path
from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def dependency_snapshot(requirements):
    queue=[Requirement(line.strip()) for line in requirements.splitlines() if line.strip() and not line.startswith('#')]
    seen=set();installed={};environment=default_environment()
    while queue:
        req=queue.pop(0);key=(canonicalize_name(req.name),tuple(sorted(req.extras)))
        if key in seen:continue
        seen.add(key);dist=metadata.distribution(req.name)
        if req.specifier and not req.specifier.contains(dist.version):
            raise ValueError(f'Acceptance environment does not satisfy {req}: {dist.version}')
        installed[canonicalize_name(dist.metadata['Name'])]=dist.version
        for text in dist.requires or []:
            child=Requirement(text)
            if child.marker and not any(child.marker.evaluate({**environment,'extra':extra}) for extra in (req.extras or {''})):continue
            queue.append(child)
    return {'python':platform.python_version(),'platform':platform.platform(),'marker_environment':environment,
            'scope':'Exact runtime dependency closure of tested host; NOT a Linux/container lock or image acceptance',
            'packages':[{'name':n,'version':v} for n,v in sorted(installed.items())]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='New project-drive artifact directory')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True,exist_ok=True)
    archive=args.output/'KStudio-R3-cloud-website-source.zip'
    if archive.exists():raise ValueError('Refuse to overwrite an existing archive; choose a new output directory')
    paths=list((root/'cloud').glob('*.py'))
    paths.extend(p for p in (root/'website').rglob('*') if p.is_file() and p.suffix in {'.html','.css','.js','.svg'})
    paths.extend(root/'deploy'/n for n in ['Dockerfile','Dockerfile.dockerignore','compose.yml','Caddyfile','backup.sh','restore.sh','ops.py','verify_restore.py','environment.template','README.md','ENVIRONMENT.md'])
    paths.extend(root/n for n in ['requirements-cloud.txt','THIRD_PARTY_NOTICES.md','docs/USER_GUIDE_R2.md'])
    if (root/'LICENSE').is_file():paths.append(root/'LICENSE')
    files={p.relative_to(root).as_posix():p.read_bytes() for p in paths}
    assert not any('.env' in Path(n).name or any(x in Path(n).parts for x in ('runtime','__pycache__','fixtures','.git')) for n in files)
    snapshot=dependency_snapshot(files['requirements-cloud.txt'].decode('utf-8-sig'))
    files['DEPENDENCIES.tested-host.json']=(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n').encode()
    files['requirements-cloud.tested-windows.lock.txt']=('# Tested Windows runtime closure only. Do not use this as a Linux lock.\n'+''.join(p['name']+'=='+p['version']+'\n' for p in snapshot['packages'])).encode()
    files['SOURCE_ARTIFACT_README.md']=('''# K Studio R3 cloud + website SOURCE candidate

Start with deploy/ENVIRONMENT.md, deploy/environment.template and deploy/README.md. This archive contains the
independent cloud service, public website, pinned direct requirements and deployment
configuration. It does not contain the local SketchUp writer, desktop installation,
runtime data, private tests, .env files, credentials, or prebuilt containers.

IMAGE_STATUS=NOT_BUILT; PUBLIC_DEPLOYMENT=NOT_RUN. Docker was unavailable in the
acceptance environment. Python/PostgreSQL/Caddy image tags are not immutable image
digests. Resolve and freeze target Linux dependencies/images on the staging builder,
record SBOM/digests, and run the actual staging gates before production promotion.
requirements-cloud.txt pins direct dependencies. The tested Windows dependency
snapshot records the exact runtime closure, including platform markers. It is not
a cross-platform lock, Linux build claim or vulnerability certification.

MANIFEST.json hashes every payload file; SHA256SUMS is the human-readable form.
Neither is a publisher signature. Verify the outer ZIP hash through a trusted channel.
No private .env or identity/payment/provider credentials are included. Configure
real external services according to ENVIRONMENT.md; unset services remain closed.
restore_drill.py referenced in the repository's historical README is a separate
test fixture and intentionally not shipped in this deployment source artifact.
The repository has no root LICENSE file at packaging time. This private owner
delivery does not invent a public redistribution license. Confirm first-party
source/design rights and publish the operator-approved terms before redistribution;
THIRD_PARTY_NOTICES is attribution, not a substitute for those permissions.
''').encode()
    rows=[{'path':n,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for n,data in sorted(files.items())]
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    manifest={'schema':1,'artifact_type':'cloud-website-source','base_git_head':head,'working_tree_changes_included':True,
              'image_status':'NOT_BUILT','public_deployment':'NOT_RUN','credentials_included':False,
              'file_count':len(rows),'files':rows}
    files['MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    files['SHA256SUMS']=(''.join(r['sha256']+'  '+r['path']+'\n' for r in rows)).encode()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zipped:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,11,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if name.endswith('.sh') else 0o100644)<<16
            zipped.writestr(info,data)
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        for row in rows:assert hashlib.sha256(zipped.read(row['path'])).hexdigest()==row['sha256']
        assert not any('.env' in Path(n).name or '__pycache__' in n for n in zipped.namelist())
    receipt={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
             'payload_files':len(rows),'archive_files':len(files),'all_member_hashes_verified':True,
             'image_status':'NOT_BUILT','public_deployment':'NOT_RUN'}
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    (args.output/'SHA256SUMS').write_text(receipt['sha256']+'  '+archive.name+'\n',encoding='utf-8')
    print(json.dumps(receipt))


if __name__=='__main__':main()
