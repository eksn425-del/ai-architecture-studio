"""Fetch missing npm license texts from the exact registry gitHead, no packages run.

Only public registry and raw GitHub endpoints are requested. Unresolvable licenses
remain missing. Results are evidence supplements, never automatic license clearance.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import quote, urlsplit


def fetch(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.hostname not in {'registry.npmjs.org','raw.githubusercontent.com'} or p.username or p.password:
        raise ValueError('Only public license sources are supported')
    # Public source retrieval follows the host's configured network proxy.
    # No provider credentials, cookies or registry authentication are attached.
    opener=urllib.request.build_opener()
    with opener.open(urllib.request.Request(url,headers={'User-Agent':'KStudio-license-evidence/1'}),timeout=15) as response:
        if urlsplit(response.url).hostname not in {'registry.npmjs.org','raw.githubusercontent.com'}:raise ValueError('Unexpected license redirect')
        data=response.read(8*1024*1024+1)
        if len(data)>8*1024*1024:raise ValueError('Oversized license source')
        return data


def main(inventory,output):
    if output.exists():raise ValueError('Use fresh evidence output')
    output.mkdir(parents=True)
    data=json.loads(inventory.read_text(encoding='utf-8'))
    missing=[c for c in data['components'] if not c['license_texts'] and c['ecosystem']=='npm' and not c['name'].startswith('@local/') and c['name']!='benchmark']
    def collect(c):
        row={'ecosystem':c['ecosystem'],'name':c['name'],'version':c['version'],'status':'MISSING','attempted':[]}
        try:
            metaurl='https://registry.npmjs.org/'+quote(c['name'],safe='')+'/'+quote(c['version'],safe='')
            info=json.loads(fetch(metaurl));head=info.get('gitHead','');repo=info.get('repository',{})
            if isinstance(repo,str):repo={'url':repo}
            match=re.search(r'github\.com[/:]([^/]+/[^/#]+)',repo.get('url',''))
            if not match:
                row['reason']='Registry does not identify a GitHub repository';return row
            repository=match[1].removesuffix('.git');directory=repo.get('directory','').strip('/')
            binding='FETCHED_EXACT_REGISTRY_COMMIT'
            if not re.fullmatch('[a-fA-F0-9]{40}',head):
                head=None
                for tag in ('v'+c['version'],c['version'],c['name']+'@'+c['version']):
                    package_url=f'https://raw.githubusercontent.com/{repository}/{quote(tag,safe="")}/'+(directory+'/' if directory else '')+'package.json'
                    try:package=json.loads(fetch(package_url))
                    except Exception:continue
                    if package.get('name')==c['name'] and package.get('version')==c['version']:
                        head=quote(tag,safe='');row['verified_package_url']=package_url;binding='FETCHED_OFFICIAL_VERSION_TAG';break
                if not head:
                    row['reason']='No registry gitHead or exact name/version release tag verified';return row
            candidates=[]
            for parent in ([directory,''] if directory else ['']):
                for filename in ('LICENSE','LICENSE.md','LICENSE.txt','COPYING','LICENCE','license','license.md','license.txt','LICENSE-MIT','LICENSE.MIT'):
                    candidates.append((parent+'/' if parent else '')+filename)
            for relative in candidates:
                url=f'https://raw.githubusercontent.com/{repository}/{head}/{relative}'
                row['attempted'].append(url)
                try:raw=fetch(url)
                except Exception:continue
                if b'\x00' in raw or len(raw)<40:continue
                name=re.sub('[^a-zA-Z0-9._-]','_',c['name']+'-'+c['version'])+'-'+Path(relative).name
                (output/name).write_bytes(raw)
                row.update(status=binding,path=name,sha256=hashlib.sha256(raw).hexdigest(),source_url=url,registry_metadata_url=metaurl,git_commit=head if binding=='FETCHED_EXACT_REGISTRY_COMMIT' else None)
                return row
            row['reason']='No recognizable license text found at exact package commit'
        except Exception as exc:row['reason']=type(exc).__name__
        return row
    with ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(collect,missing))
    # Explicit official version-tag sources for Python wheels omitting LICENSE.
    python_sources={('tokenizers','0.23.2'):'https://raw.githubusercontent.com/huggingface/tokenizers/v0.23.2/LICENSE',
                    ('vosk','0.3.45'):'https://raw.githubusercontent.com/alphacep/vosk-api/v0.3.45/COPYING'}
    for c in data['components']:
        url=python_sources.get((c['name'],c['version']))
        if c['license_texts'] or not url:continue
        row={'ecosystem':'pypi','name':c['name'],'version':c['version'],'status':'MISSING'}
        try:
            raw=fetch(url);name=c['name']+'-'+c['version']+'-LICENSE.txt';(output/name).write_bytes(raw)
            row.update(status='FETCHED_OFFICIAL_VERSION_TAG',path=name,sha256=hashlib.sha256(raw).hexdigest(),source_url=url,version_tag_match=True)
        except Exception as exc:row['reason']=type(exc).__name__
        rows.append(row)
    (output/'supplements.json').write_text(json.dumps({'schema':1,'components':rows,'license_clearance':'REVIEW_REQUIRED'},indent=2),encoding='utf-8')
    print(json.dumps({'fetched':sum(r['status'].startswith('FETCHED') for r in rows),'unresolved':sum(r['status']=='MISSING' for r in rows)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('inventory',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();main(args.inventory,args.output)
