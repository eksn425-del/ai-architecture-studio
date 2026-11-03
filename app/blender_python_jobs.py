"""Thin candidate lifecycle. Untrusted Python runs ONLY in the native agent sandbox.

This host prepares a disposable working copy and independently validates the saved
result. It never invokes a model-authored script as an unrestricted host process.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid
from .runtime_safety import LocalRuntimeLease


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def save(path,value):
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(path)


class BlenderPythonJobs:
    """Disabled until execution AND validation share a verified OS boundary."""
    def __init__(self, *args, **kwargs):
        raise RuntimeError("Blender Python candidate mode is disabled: OS-isolated execution/inspection/render, frozen safe staging, and complete supported-asset KEEP validation are not verified. The existing declarative backend remains available.")


class _TrustedFixturePrototype:
    """Development fixture only. Never register this as a product/Agent tool."""
    def __init__(self,project,executable):
        self.project=Path(project).resolve();self.executable=str(Path(executable).resolve())
        self.root=self.project/'runtime/blender-python';self.state=self.root/'head.json'
        self.workspace=self.project/'runtime/agent_workspace'
        for path in (self.root,self.workspace):
            path.mkdir(parents=True,exist_ok=True)
            if path.is_symlink() or path.resolve()!=path:raise ValueError('Unsafe job directory')
        self.collector=Path(__file__).with_name('blender_python_inspect.py')

    def _trusted(self,operation,model,*args):
        cmd=[self.executable,'--background','--factory-startup','--disable-autoexec',
             '--python-exit-code','1','--python',str(self.collector),'--',operation,str(model),*map(str,args)]
        run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        log=self.root/(operation+'-'+uuid.uuid4().hex+'.log');log.write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
        if run.returncode:raise ValueError('Trusted Blender '+operation+' failed; see '+str(log))

    def initialize(self):
        with LocalRuntimeLease(self.root):
            if self.state.exists():return read(self.state)
            base=self.root/'initial.blend'
            if base.exists():raise ValueError('Unclaimed initial file; inspect before recovery')
            self._trusted('bootstrap',base,self.project.name)
            head={'project':self.project.name,'revision':0,'model':str(base),'sha256':sha(base)}
            save(self.state,head);return head

    def prepare(self,*,expected_revision,allowed_names,keep_names):
        with LocalRuntimeLease(self.root):
            head=read(self.state)
            if head['revision']!=expected_revision:raise ValueError('Stale revision')
            base=Path(head['model'])
            if not base.is_relative_to(self.root) or base.is_symlink() or sha(base)!=head['sha256']:raise ValueError('Saved source changed')
            allowed=set(allowed_names);keep=set(keep_names)
            if not allowed or allowed & keep or any(not isinstance(n,str) or not n or len(n)>100 for n in allowed|keep):raise ValueError('Invalid host scope/KEEP')
            job=uuid.uuid4().hex;folder=self.workspace/'blender-jobs'/job;folder.mkdir(parents=True)
            shutil.copyfile(base,folder/'input.blend')
            before=self.root/(job+'-before.json');self._trusted('inspect',base,before)
            baseline=read(before)
            if set(baseline['objects'])-allowed-keep:raise ValueError('Every existing object needs an explicit allowed or KEEP binding')
            if keep-set(baseline['objects']):raise ValueError('KEEP object missing')
            contract={'job':job,'head':head,'allowed':sorted(allowed),'keep':sorted(keep),
                      'baseline':baseline,'folder':str(folder),'source_sha256':sha(folder/'input.blend')}
            save(self.root/(job+'.json'),contract)
            # The model sees only instructions and working files, never the host contract.
            return {'job':job,'workspace':str(folder),'input':str(folder/'input.blend'),
                    'script':str(folder/'model.py'),'candidate':str(folder/'candidate.blend'),
                    'command':[self.executable,'--background','--disable-autoexec',str(folder/'input.blend'),
                               '--python-exit-code','1','--python',str(folder/'model.py')],
                    'execution':'Run command through the native agent shell with workspace-write and network disabled. Never request unrestricted execution.'}

    def commit(self,job):
        if len(job)!=32 or any(c not in '0123456789abcdef' for c in job):raise ValueError('Invalid job identity')
        with LocalRuntimeLease(self.root):
            contract=read(self.root/(job+'.json'));head=read(self.state)
            if head!=contract['head']:raise ValueError('Stale job; current scene unchanged')
            folder=Path(contract['folder']);candidate=folder/'candidate.blend'
            if folder.resolve()!=self.workspace/'blender-jobs'/job or candidate.is_symlink() or not candidate.is_file():raise ValueError('Invalid candidate path')
            if sha(folder/'input.blend')!=contract['source_sha256']:raise ValueError('Job input changed')
            # Snapshot first: native workspace writes can never mutate the accepted file.
            accepted=self.root/(job+'.blend')
            if accepted.exists():raise ValueError('Immutable candidate already exists; inspect recovery')
            shutil.copyfile(candidate,accepted)
            reopened=self.root/(job+'-reopened.json');self._trusted('inspect',accepted,reopened)
            after=read(reopened);before=contract['baseline']
            changed={n for n in set(before['objects'])|set(after['objects']) if before['objects'].get(n)!=after['objects'].get(n)}
            if not changed or changed-set(contract['allowed']):raise ValueError('Candidate mutated outside the host scope or made no progress')
            if before['world']!=after['world']:raise ValueError('Candidate changed global world settings')
            if any(before['objects'][n]!=after['objects'].get(n) for n in contract['keep']):raise ValueError('KEEP changed')
            # Independently reopen a second time; saved native data must be stable.
            second=self.root/(job+'-reopened-again.json');self._trusted('inspect',accepted,second)
            if read(second)!=after:raise ValueError('Native reopen instability')
            image=self.root/(job+'.png');self._trusted('render',accepted,image)
            if read(self.state)!=head:raise ValueError('Host scene changed during verification')
            result={'project':self.project.name,'revision':head['revision']+1,'model':str(accepted),
                    'sha256':sha(accepted),'native_reopen':'PASS','keep':'PASS','changed':sorted(changed),
                    'geometry':after,'image':str(image),'quality':'UNVERIFIED_SOURCE_FIDELITY'}
            save(self.root/(job+'-receipt.json'),result);save(self.state,result)
            return result
