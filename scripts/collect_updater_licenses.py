"""Preserve shipped dependency license texts; no private runtime/config files."""
import importlib.metadata as metadata,json,shutil,sys
from pathlib import Path
destination=Path(sys.argv[1])/'licenses';destination.mkdir(parents=True,exist_ok=True)
python_license=Path(sys.base_prefix)/'LICENSE.txt'
if not python_license.is_file():raise SystemExit('Python runtime license missing')
shutil.copyfile(python_license,destination/'Python-LICENSE.txt')
components=[]
for name in ('cryptography','cffi','pyinstaller'):
    distribution=metadata.distribution(name);target=destination/name;target.mkdir(exist_ok=True);copied=[]
    for relative in distribution.files or []:
        if 'license' in str(relative).lower() or Path(relative).name.lower().startswith(('copying','notice')):
            source=Path(distribution.locate_file(relative))
            if source.is_file():
                output=target/Path(relative).name;shutil.copyfile(source,output);copied.append(output.name)
    if not copied:raise SystemExit('License text missing: '+name)
    components.append({'name':name,'version':distribution.version,'texts':copied,'project_url':distribution.metadata.get('Home-page')})
(destination/'components.json').write_text(json.dumps({'python':sys.version.split()[0],'components':components,'formal_publisher_signing':'not_provided','scope':'runtime license text inventory; separate binary/vendor distribution review still required'},indent=2),encoding='utf-8')
