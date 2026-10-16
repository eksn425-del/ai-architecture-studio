from pathlib import Path
import json,collections,math
D=Path('runtime/customer-readiness-20261015')
a=json.loads((D/'r9-graph-before-site-final-save.json').read_text(encoding='utf8'));b=json.loads((D/'r9-graph-bound-reopened.json').read_text(encoding='utf8'))
def pool(x):
 out=collections.defaultdict(list)
 for h,v in x['definitions'].items():
  p=json.loads(v['canonical_payload_json']);out[p['definition_name']].append((h,p))
 return out
aa,bb=pool(a),pool(b);rows=[]
def diff(x,y,path='',out=None):
 if out is None:out=[]
 if type(x)!=type(y):out.append({'path':path,'before':x,'after':y})
 elif isinstance(x,dict):
  for k in x.keys()|y.keys():
   if k not in x or k not in y:out.append({'path':path+'/'+k,'before':x.get(k),'after':y.get(k)})
   elif k!='definition_ref':diff(x[k],y[k],path+'/'+k,out)
 elif isinstance(x,list):
  if len(x)!=len(y):out.append({'path':path+'/length','before':len(x),'after':len(y)})
  else:
   for i,(u,v) in enumerate(zip(x,y)):diff(u,v,path+'/'+str(i),out)
 elif x!=y:out.append({'path':path,'before':x,'after':y,'numeric_delta':y-x if isinstance(x,(int,float)) and isinstance(y,(int,float)) else None})
 return out
for n in aa.keys()|bb.keys():
 if len(aa[n])!=1 or len(bb[n])!=1:
  if aa[n]!=bb[n]:rows.append({'definition':n,'ambiguous_or_missing':True,'counts':[len(aa[n]),len(bb[n])]})
 elif aa[n][0][0]!=bb[n][0][0]:
  ds=diff(aa[n][0][1],bb[n][0][1]);rows.append({'definition':n,'differences_excluding_reference_hashes':ds,'difference_count':len(ds)})
out={'status':'DIAGNOSIS_ONLY','before_document_sha':a['document_geometry_material_sha256'],'reopened_document_sha':b['document_geometry_material_sha256'],'changed_definition_records':len(rows),'rows':rows}
(D/'r9-native-reopen-definition-differences.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'changed_definition_records':len(rows),'direct_non_hash_differences':sum(r.get('difference_count',0) for r in rows),'first_differences':[r for r in rows if r.get('difference_count',0)][:5]},ensure_ascii=False)[:10000])
