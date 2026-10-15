from pathlib import Path
import json,html
D=Path(__file__).resolve().parent;r=json.loads((D/'measured-relations.json').read_text(encoding='utf-8'));geo=json.loads((D/'geometry-topology.json').read_text(encoding='utf-8'))
out=['<svg xmlns="http://www.w3.org/2000/svg" width="1480" height="1210" viewBox="0 0 1480 1210"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 Z" fill="context-stroke"/></marker></defs><rect width="1480" height="1210" fill="#f5f6f8"/><g font-family="Microsoft YaHei,Arial,sans-serif">']
def text(x,y,s,size=18,color='#18212c'):out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(s)}</text>')
def line(a,b,color='#234',width=2,arrow=False,dash=False):out.append(f'<path d="M{a[0]:.3f},{a[1]:.3f} L{b[0]:.3f},{b[1]:.3f}" fill="none" stroke="{color}" stroke-width="{width}"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="7 6"' if dash else '')+'/>')
def rect(x,y,w,h,fill,stroke='none'):out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}"/>')
text(32,40,'r4 原生几何与原图方向核对｜零几何写入',26)
text(32,70,'坐标：从坡道短端 -X 朝 +X 看，画面左为 +Y，右为 -Y；非地理南北。模型尺寸为估算建筑的实测值。',17)
for px,py in [(24,95),(754,95),(24,625),(754,625)]:rect(px,py,700,500,'white','#dde2e7')
text(44,128,'A｜实测拉索：24 × 24 mm，不是厚三角实体',21)
rod=r['rods'][0];e=rod['endpoints_world_mm'];a=[90,535];b=[240,210];line(a,b,'#087f68',2,True)
line([90,535],[240,535],'#9aa6b0',1,False,True);line([240,535],[240,210],'#9aa6b0',1,False,True)
text(270,240,'22 根独立杆，每根 6 面 / 12 边')
text(270,275,'所有短边：24 mm；长边约 12.55 / 13.51 m')
text(270,310,'大轴向包围盒 ≠ 构件横截面')
text(270,345,'端点与屋顶边梁、环廊板几何接触：22/22')
rect(300,395,110,110,'#f3fbf8','#087f68');line([300,380],[410,380],'#087f68',2,True);text(319,372,'24 mm',16);text(430,455,'真实方截面示意（放大，非同图比例）',15)
text(44,575,'源图 1 / 2 / 5 / 6 / 8 为细杆表达；源图精确直径与结构节点未测绘。',15)
text(774,128,'B｜原生坡道端视投影：两段坡向反了',21)
text(805,165,'+Y / 画面左',16);text(1260,165,'-Y / 画面右',16)
def ramp_pt(p):return [825+(24000-p[1])/28000*520,540-p[2]/10800*310]
for f in r['ramps']:
 color='#b73532' if not f['direction_matches_source_projection'] else '#087f68';lo,hi=f['top_endpoints_world_mm'];line(ramp_pt(lo),ramp_pt(hi),color,4,True);q={'RAMP_1':[845,560],'RAMP_2':[1080,465],'RAMP_3':[845,312]}[f['path'][-1]];text(q[0],q[1],f['path'][-1]+f'  {lo[2]/1000:g}→{hi[2]/1000:g}m',15,color)
line([1310,196],[1140,196],'#087f68',2,True);text(794,205,'原图 1：三段均向左上升（方向观察，未测绘）',15)
text(774,575,'每段升高3.6m / 水平28m，端点与相应平台接触；源图绕行长边仍未知。',15)
text(44,658,'C｜L2 原生板面：当前挑空在 -Y 侧',21)
# Native actual top-face polygons, world XY; positive Y drawn up.
def plan(p):return [100+p[0]/50000*540,1065-p[1]/20000*260]
rect(100,805,540,260,'#fcebea','#b73532')
for f in r['floor_topology']:
 if abs(f['z_mm']-7200)>0.1:continue
 for loop in f['loops']:
  ps=[plan(p) for p in loop['points']];coords=' '.join(f'{p[0]:.3f},{p[1]:.3f}' for p in ps);out.append(f'<polygon points="{coords}" fill="'+('#c7dced' if loop['outer'] else '#fff')+'" stroke="#315a78" stroke-width="1"/>')
text(85,785,'+Y / 坡道端视左侧',16);text(100,1090,'-Y / 坡道端视右侧',16);text(100,1120,'+X → 远端；蓝=有板，粉=该层无板',16)
text(140,1015,'当前原生大挑空',18,'#a02a27');text(120,855,'(10m,16m,7.2m)：有板',16);text(120,1045,'(10m,5m,7.2m)：无板',16)
text(44,1155,'原图5/8剖面：左侧大挑空、右侧局部板。方向对应由不等高屋顶交叉核对。',14)
text(44,1180,'源图剖切位置与精确边界未测绘；当前板面数据已证实，完整源图对应仍未确认。',14,'#8a5b15')
text(774,658,'D｜X=10m 的原生子系统截面交线',21)
text(774,686,'由真实面环算出；不是新建的SketchUp剖切面，也不是完整结构剖面。',14)
def section(p):return [807+(28000-p[0])/36000*600,1118-p[1]/18000*390]
def walk(nodes):
 for n in nodes:yield n;yield from walk(n['children'])
colors={'FLOORS':'#245b89','ROOF_TIMBER':'#9d6822','ENVELOPE_OUTER':'#aab4bb'}
segments=[]
for g in walk(geo['groups']):
 color=colors.get(g['path'][0])
 if not color:continue
 for f in g['faces']:
  for loop in f['loops']:
   pts=loop['points'];cross=[]
   for a,b in zip(pts,pts[1:]+pts[:1]):
    da,db=a[0]-10000,b[0]-10000
    if abs(da)<0.001 and abs(db)<0.001:segments.append(([a[1],a[2]],[b[1],b[2]],color));continue
    if da*db<0 or abs(da)<0.001:
     t=0 if abs(da)<0.001 else da/(da-db);q=[a[k]+t*(b[k]-a[k]) for k in [1,2]]
     if q not in cross:cross.append(q)
   if len(cross)==2:segments.append((cross[0],cross[1],color))
for a,b,color in segments:line(section(a),section(b),color,1.4)
text(795,1120,'+Y 左',14);text(1320,1120,'-Y 右',14)
for z in [0,3600,7200,10800]:text(1370,1120-z/18000*390,f'{z/1000:g}m',13)
text(825,925,'L2 该侧有板',16,'#245b89');text(1150,970,'L2 该侧为空',16,'#a02a27')
text(774,1155,'全精度面环、孔洞、端点与PID均在 native/ 与 measured-relations.json。',14)
out+=['</g></svg>'];(D/'spatial-diagnosis.svg').write_text(''.join(out),encoding='utf-8')
(D/'section-segments.json').write_text(json.dumps({'plane':'X=10000mm','scope':list(colors),'segments_yz_mm':segments},ensure_ascii=False),encoding='utf-8')
print('Wrote source-direction/native-data SVG and exact section intersections')
