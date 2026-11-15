"""Media-local v8 starter. No network, model inference, asset discovery or publication."""
from pathlib import Path
import argparse,json,hashlib,math,re,shutil,subprocess,sys

SKILL=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def run(args,**kw):return subprocess.run([str(x) for x in args],check=True,**kw)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
def source(root,spec):
 p=Path(spec['path']);return p if p.is_absolute() else root/p
def load_job(p):
 p=Path(p).resolve();j=read(p)
 if (j.get('fps'),j.get('width'),j.get('height'),j.get('duration'))!=(30,1920,1080,60):raise ValueError('Starter profile is 60s/1080p30. Adapt timeline and QA explicitly for other formats.')
 return p.parent,j
def init(path):
 root=Path(path).resolve()
 if root.exists():raise ValueError('Use a new output directory; existing files are not overwritten.')
 shutil.copytree(SKILL/'assets/template',root/'film');(root/'media').mkdir();(root/'audio').mkdir();(root/'qa').mkdir()
 shutil.copy2(SKILL/'assets/example-job.json',root/'job.json')
 print('Created media-free job:',root)
def audit(path,quiet=False):
 root,j=load_job(path);errors=[];warnings=[];rows=[];info={}
 expected=read(SKILL/'assets/example-job.json')
 if set(j['assets'])!=set(expected['assets']):errors.append('Canonical asset slots must match this template; adapt code before changing slot names.')
 for name,spec in j['assets'].items():
  if spec.get('case')!=expected['assets'].get(name,{}).get('case'):errors.append('Wrong case for '+name)
 if not 1<=len(j['references'])<=16:errors.append('Reference count must be 1..16, or redesign the layout.')
 scenes=j['narration']
 if [(x['id'],x['start'],x['end']) for x in scenes]!=[(x['id'],x['start'],x['end']) for x in expected['narration']]:errors.append('Scene timing/profile mismatch.')
 specs=[(name,spec) for name,spec in j['assets'].items()]+[(f'ref-{i+1:02}',x) for i,x in enumerate(j['references'])]+[(f'voice-{i+1}',dict(x,kind='audio')) for i,x in enumerate(scenes)]
 if j.get('bgm'):specs.append(('bgm',dict(j['bgm'],kind='audio')))
 specs += [(f'sfx-{i}',dict(x,kind='audio')) for i,x in enumerate(j.get('sfx',[]))]
 ref_hashes=[]
 for name,spec in specs:
  p=source(root,spec)
  if not p.is_file():errors.append('Missing '+name+': '+spec['path']);continue
  try:
   meta=probe(p);info[name]=meta;digest=sha(p);duration=float(meta.get('format',{}).get('duration',0))
   rows.append({'slot':name,'path':str(p),'sha256':digest,'duration':duration,'kind':spec['kind'],'case':spec.get('case'),'rights':spec.get('rights','unverified')})
   if name.startswith('ref-'):ref_hashes.append(digest)
   if spec.get('rights','unverified')=='unverified':warnings.append('Rights unverified: '+name)
  except Exception as e:errors.append(name+': unreadable media '+str(e))
 if len(set(ref_hashes))!=len(ref_hashes):errors.append('Duplicate reference files; confirm duplicates rather than pretending unique sources.')
 for cue,c in j['clips'].items():
  name=cue.rsplit(':',1)[0]
  if name not in info:continue
  duration=float(info[name]['format']['duration']);end=float(c['start'])+float(c['rate'])*float(c['shown'])
  if c['start']<0 or c['rate']<=0 or end>duration+.04:errors.append(f'Clip too short: {cue} needs {end:.3f}s, has {duration:.3f}s')
 for i,s in enumerate(scenes):
  if not .7<=s['pace']<=1.45:errors.append('Voice pace outside explicit starter bounds: '+s['id'])
  if f'voice-{i+1}' in info:
   duration=float(info[f'voice-{i+1}']['format']['duration'])/s['pace']
   if duration>s['end']-s['start']-.4:errors.append('Voice does not fit scene: '+s['id'])
 if len(j['references'])!=8 and '八张' in ''.join(x['text'] for x in scenes):errors.append('Narration still says eight references; update it for the actual inputs.')
 result={'ok':not errors,'errors':errors,'warnings':warnings,'assets':rows,'source_materials_private':True}
 write(root/'qa/intake.json',result)
 if not quiet:print(json.dumps({'ok':result['ok'],'errors':errors,'warnings':len(warnings),'files':len(rows)},ensure_ascii=False))
 return result
def parse_captions(path):
 p=Path(path)
 if p.suffix.lower()=='.srt':
  def sec(x):
   a,b,c=x.replace(',','.').split(':');return int(a)*3600+int(b)*60+float(c)
  rows=[]
  for block in re.split(r'\n\s*\n',p.read_text(encoding='utf-8-sig').strip().replace('\r','')):
   lines=block.splitlines();idx=next((i for i,x in enumerate(lines) if '-->' in x),None)
   if idx is None:continue
   a,b=lines[idx].split('-->');rows.append({'start':sec(a.strip()),'end':sec(b.strip().split()[0]),'text':' '.join(lines[idx+1:])})
 else:
  data=read(p);rows=data if isinstance(data,list) else data.get('segments',data.get('word_segments',[]))
  rows=[{'start':x['start'],'end':x['end'],'text':x.get('text',x.get('word','')).strip()} for x in rows]
 if not rows:raise ValueError('No timed captions found.')
 previous=-1
 for x in rows:
  if not 0<=x['start']<x['end']<=60 or x['start']<previous or not x['text']:raise ValueError('Invalid/out-of-order caption interval.')
  previous=x['start']
 return rows
def audio_duration(p):return float(probe(p)['format']['duration'])
def prepare(path,captions=None):
 root,j=load_job(path);result=audit(path,True)
 if not result['ok']:raise ValueError('Intake failed: '+'; '.join(result['errors']))
 pub=root/'film/public';pub.mkdir(exist_ok=True);work=root/'audio/prepared';work.mkdir(exist_ok=True)
 for name,spec in j['assets'].items():shutil.copy2(source(root,spec),pub/name)
 refs=[]
 for i,spec in enumerate(j['references']):
  # Preserve actual encoding; do not rename JPEG bytes to PNG.
  name=f'ref-{i+1:02}'+source(root,spec).suffix.lower();shutil.copy2(source(root,spec),pub/name);refs.append(name)
 cfg=dict(j['labels'],references=refs,clips=j['clips']);write(pub/'job-config.json',cfg)
 timing=[];pieces=[]
 for i,s in enumerate(j['narration']):
  p=work/f'voice-{i}.wav';run(['ffmpeg','-y','-v','error','-i',source(root,s),'-af',f'atempo={s["pace"]}','-ar','48000','-ac','1',p])
  start=s['start']+.2;end=start+audio_duration(p)
  if end>s['end']-.18:raise ValueError('Paced voice overflows '+s['id'])
  timing.append({'start':start,'end':end,'scene_start':s['start'],'scene_end':s['end'],'id':s['id'],'text':s['text'],'pace':s['pace']});pieces.append(p)
 args=['ffmpeg','-y','-v','error'];filters=[]
 for p in pieces:args+=['-i',str(p)]
 for i,t in enumerate(timing):filters.append(f'[{i}:a]adelay={round(t["start"]*48000)}S:all=1[v{i}]')
 filters.append(''.join(f'[v{i}]' for i in range(6))+'amix=inputs=6:normalize=0,apad,atrim=duration=60,acompressor=threshold=0.125:ratio=2:attack=6:release=90:makeup=1.3,loudnorm=I=-13.5:TP=-1.8:LRA=7,aresample=48000,aformat=channel_layouts=stereo[voice]')
 run(args+['-filter_complex',';'.join(filters),'-map','[voice]',work/'voice.wav'])
 def mix(with_music,out):
  args=['ffmpeg','-y','-v','error','-i',str(work/'voice.wav')];filters=[];tracks=['[0:a]'];index=1
  for s in j.get('sfx',[]):
   if not 0<=s['at']<60:raise ValueError('SFX time out of range')
   args+=['-i',str(source(root,s))];filters.append(f'[{index}:a]atrim=duration=0.85,aresample=48000,aformat=channel_layouts=stereo,volume={s.get("gain",.13)},adelay={round(s["at"]*48000)}S:all=1[s{index}]');tracks.append(f'[s{index}]');index+=1
  if with_music and j.get('bgm'):
   args+=['-stream_loop','-1','-i',str(source(root,j['bgm']))]
   duck='1'
   for t in timing:duck=f'if(between(t,{max(0,t["start"]-.15):.4f},{t["end"]+.2:.4f}),0.52,{duck})'
   filters.append(f'[{index}:a]atrim=duration=60,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-24.5:TP=-9:LRA=9,volume=\'{duck}\':eval=frame,afade=t=in:d=0.8,afade=t=out:st=59:d=1[music]');tracks.append('[music]')
  filters.append(''.join(tracks)+f'amix=inputs={len(tracks)}:normalize=0,apad,atrim=duration=60,alimiter=limit=0.8:attack=5:release=75:level=false[a]')
  run(args+['-filter_complex',';'.join(filters),'-map','[a]','-ar','48000',str(out)])
 mix(False,pub/'audio-noBGM.wav');mix(True,pub/'audio-withBGM.wav');write(pub/'timing.json',timing)
 if captions:cap=parse_captions(captions);mode='provided-timestamps; human verification still required'
 else:
  cap=[];mode='approximate-sentence-timing'
  for t in timing:
   parts=[x for x in re.split(r'(?<=[，。？；])',t['text']) if x];step=(t['end']-t['start'])/len(parts)
   cap.extend({'start':t['start']+i*step,'end':t['start']+(i+1)*step,'text':x} for i,x in enumerate(parts))
 write(pub/'captions.json',cap);write(root/'qa/preparation.json',{'caption_mode':mode,'timing':timing,'voice_cloning_run':False,'has_bgm':bool(j.get('bgm')),'native_model_writes':0})
 print('Prepared local assets/audio/captions. Caption mode:',mode)
def render(path):
 root,j=load_job(path);film=root/'film';cli=film/'node_modules/@remotion/cli/remotion-cli.js'
 if not cli.is_file():raise ValueError('Install pinned dependencies in film, or link an approved matching node_modules runtime.')
 for name,extra in [('main',[]),('noBGM',['--props=props-nobgm.json'])]:
  with (root/'qa'/f'render-{name}.log').open('wb') as log:run(['node',cli,'render','src/index.tsx','KStudioLaunch',root/(name+'.mp4'),'--codec=h264','--crf=18','--concurrency=2','--x264-preset=fast',*extra],cwd=film,stdout=log,stderr=log)
 print('Rendered both input-prop versions.')
def stream(p,kind):return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map',f'0:{kind}:0','-c','copy','-f','hash','-hash','sha256','-'],text=True).strip()
def measure(p,log_path):
 # One bounded decode pass measures black intervals and true audio peak.
 result=subprocess.run(['ffmpeg','-hide_banner','-nostats','-threads','2','-filter_threads','2','-i',str(p),'-vf','blackdetect=d=0.15:pix_th=0.02','-af','ebur128=peak=true','-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True)
 log=result.stderr.decode('utf8',errors='replace');Path(log_path).write_text(log,encoding='utf8')
 summary=log.rsplit('Summary:',1)[-1]
 def number(pattern):
  match=re.search(pattern,summary)
  if not match:raise ValueError('Missing audio measurement: '+p.name)
  value=float(match.group(1))
  if not math.isfinite(value):raise ValueError('Silent/invalid audio measurement: '+p.name)
  return value
 loudness=number(r'I:\s*([-\d.]+)\s*LUFS');peak=number(r'Peak:\s*([-\d.]+)\s*dBFS')
 black=[{'start':float(a),'end':float(b),'duration':float(c)} for a,b,c in re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',log)]
 if peak>=0:raise ValueError('Audio reaches clipping threshold: '+p.name)
 return {'integrated_lufs':loudness,'true_peak_dbfs':peak,'black_intervals':black,'review_black_intervals':bool(black),'subjective_listening':'NOT_VERIFIED'}

def verify(path):
 root,j=load_job(path);paths=[root/'main.mp4',root/'noBGM.mp4'];rows=[]
 for p in paths:
  info=probe(p);v=next(x for x in info['streams'] if x['codec_type']=='video')
  if (int(v['width']),int(v['height']),v['r_frame_rate'],int(v['nb_frames']))!=(1920,1080,'30/1',1800):raise ValueError('Output spec mismatch')
  metrics=measure(p,root/'qa'/f'{p.stem}-decode.log')
  rows.append({'name':p.name,'sha256':sha(p),'video':stream(p,'v'),'audio':stream(p,'a'),'video_s':float(v['duration']),'container_s':float(info['format']['duration']),'metrics':metrics})
 if rows[0]['video']!=rows[1]['video']:
  original=root/'qa/noBGM-original-props-render.mp4'
  if original.exists():raise ValueError('Original noBGM render already preserved; inspect before normalization.')
  shutil.copy2(paths[1],original);tmp=root/'qa/normalized-noBGM.mp4'
  run(['ffmpeg','-y','-v','error','-i',paths[0],'-i',original,'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',tmp])
  assert stream(tmp,'v')==rows[0]['video'] and stream(tmp,'a')==rows[1]['audio'];tmp.replace(paths[1])
  rows[1].update(sha256=sha(paths[1]),video=stream(paths[1],'v'),normalization='lossless main video plus preserved noBGM audio')
 if j.get('bgm') and rows[0]['audio']==rows[1]['audio']:raise ValueError('Expected distinct BGM/noBGM audio tracks')
 frames=root/'qa/frames';frames.mkdir(exist_ok=True)
 for i,t in enumerate([.6,7.6,15.6,20.4,23,24.2,25.1,28.3,30,34.2,36.2,37.6,40.6,42.6,47.5,51,55,59.4]):run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',paths[0],'-frames:v','1',frames/f'{i:02}-{t:.1f}.png'])
 write(root/'qa/media-verification.json',{'videos':rows,'human_listening':'NOT_VERIFIED','visual_review':'REQUIRED','native_quality':'not assessed by media verification','public_rights':'see intake; not granted by render','has_bgm':bool(j.get('bgm'))})
 print('Technical media checks passed; inspect actual frames/motion and listen before final delivery.')
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['init','audit','prepare','render','verify']);p.add_argument('path');p.add_argument('--captions');a=p.parse_args()
 try:
  if a.command=='init':init(a.path)
  elif a.command=='audit':
   if not audit(a.path)['ok']:return 2
  elif a.command=='prepare':prepare(a.path,a.captions)
  elif a.command=='render':render(a.path)
  else:verify(a.path)
 except (ValueError,KeyError,subprocess.CalledProcessError,OSError) as e:print('ERROR:',e,file=sys.stderr);return 2
 return 0
if __name__=='__main__':raise SystemExit(main())
