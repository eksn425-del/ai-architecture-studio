"""Map observed native files to collected component notices, without legal clearance."""
import argparse,json,re
from collections import Counter
from pathlib import Path

def classify(inventory):
    components=inventory['components'];owned={};npm=[]
    for c in components:
        for evidence in c['evidence']:
            if evidence['kind']=='analysis_toc_exact_distribution_file_match':
                for name in evidence['matched_files']:owned.setdefault(name.replace('\\','/').lower(),[]).append(c)
            if c['ecosystem']=='npm' and evidence['kind']=='bundle_metadata':
                npm.append((evidence['path'].removesuffix('package.json'),c))
    npm.sort(key=lambda x:len(x[0]),reverse=True)
    python=next(c for c in components if c['ecosystem']=='runtime' and c['name']=='Python')
    node=next(c for c in components if c['ecosystem']=='runtime' and c['name']=='Node.js')
    python_dll='python'+''.join(python['version'].split('.')[:2])+'.dll'
    rows=[]
    for binary in inventory['native_binaries_requiring_vendor_notice_review']:
        path=binary['path'];local=path.removeprefix('_internal/');base=Path(path).name.lower();owner=None;basis='';extra=[]
        if path in ('KStudio.exe','KStudioConnector.exe'):
            category='FIRST_PARTY_PUBLISHER_SIGNING_REQUIRED';basis='First-party frozen application entry'
        elif base.startswith(('api-ms-win-','vcruntime','ucrtbase','msvcp')) or '/webview/lib/Microsoft.Web.WebView2.' in path or base=='webview2loader.dll':
            category='MICROSOFT_RUNTIME_OR_WEBVIEW_REDISTRIBUTION_TERMS_REVIEW';basis='Identified Windows CRT/UCRT/WebView SDK family; filename/origin mapping is not a redistribution grant'
            owner=next((c for c in owned.get(local.lower(),[]) if c['license_texts']),None)
        elif path=='_internal/harness/node.exe':
            owner=node;category='NODE_RUNTIME_VENDOR_NOTICES_COLLECTED';basis='Official version-specific Node license with bundled third-party notices'
        else:
            owner=next((c for prefix,c in npm if path.startswith(prefix)),None)
            if owner:
                category='NPM_COMPONENT_NOTICES_MAPPED';basis='Actual deepest bundled package metadata and collected license text'
                if re.search(r'(?i)LGPL|AGPL|MPL|CPAL',owner['declared_license']):
                    category='RECIPROCAL_BINARY_SOURCE_OBLIGATION_REVIEW'
                if '/conpty/' in path:extra.append('ConPTY/OpenConsole vendor terms also require exact bundled upstream notice scope; parent node-pty license alone is not a grant for every binary')
            else:
                matches=owned.get(local.lower(),[])
                owner=next((c for c in matches if c['license_texts']),matches[0] if matches else None)
                if owner:
                    category='PYTHON_DISTRIBUTION_NOTICES_MAPPED';basis='Exact Analysis TOC source file matched to distribution RECORD ownership'
                elif '/' not in local and (base.endswith('.pyd') or base in ('python3.dll',python_dll,'libcrypto-3.dll','libssl-3.dll','libffi-8.dll','sqlite3.dll')):
                    owner=python;category='CPYTHON_RUNTIME_NOTICES_COLLECTED';basis='Bundled CPython standard-library/runtime dependency; CPython license includes third-party notices'
                else:category='UNMAPPED_BINARY_ENGINEERING_REVIEW';basis='No reliable source-to-component match found'
        row={**binary,'category':category,'mapping_basis':basis,'additional_notes':extra}
        if owner:row.update(component={'ecosystem':owner['ecosystem'],'name':owner['name'],'version':owner['version'],'declared_license':owner['declared_license']},license_texts=[{k:t[k] for k in ('path','sha256','bytes')} for t in owner['license_texts']])
        rows.append(row)
    return {'schema':1,'scope':'Per-file source/license-evidence mapping; not blanket legal approval or independent publisher signature verification',
            'summary':dict(Counter(r['category'] for r in rows)),'binaries':rows,'license_clearance':'REVIEW_REQUIRED'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('inventory',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve prior binary map')
    result=classify(json.loads(a.inventory.read_text(encoding='utf-8')))
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result['summary']))
