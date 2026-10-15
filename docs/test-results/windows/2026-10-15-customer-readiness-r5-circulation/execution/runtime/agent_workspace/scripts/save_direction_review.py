import json, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

w = Path.cwd()
project = w.parent.parent
names = [
'9d05f4a6ae-codex-clipboard-1b4276a9-93d4-4833-95cb-c3b193c9c96d.png',
'ade9a9063c-codex-clipboard-273f5c39-ee57-4cd8-a0c0-d1113b742a27.png',
'8e8a3625d5-codex-clipboard-a04d023f-1044-423f-89db-4a0b51e92505.png',
'c55a28860e-codex-clipboard-fdf7fe7c-e5f1-47d4-b800-d4f5eaf99b52.png',
'da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png',
'4fdbe428b1-codex-clipboard-8856a1fd-12c2-44d9-a5af-868c4c8d4c2a.png',
'8328ae9aa4-codex-clipboard-538fb3e3-5783-461e-8458-b231bd90bd57.png',
'92fc9f3b50-codex-clipboard-10ea73cd-a751-4576-b174-295e6446a725.png']
refs = ['inputs/reference/'+n for n in names]
panels = [
['上：坡道短端外观，右屋顶边高于左边，中央下垂；三条坡道投影均向左上升。','下：实体模型同一短端，确认上述高低及坡道投影；外廊与内框架有深度。'],
['上：场地轴测，长条平面、短跨下垂屋顶沿长向延伸；近短端有坡道。','下：坡道端与相邻长边模型斜视，验证外廊、平台及多层玻璃；透视不改变端部高低。'],
['上：近地入口侧视，地面坡道接首个架空平台；此角度画面左右不能替代图1短端左右。','下：长边外廊底部，格栅、横梁、混凝土柱与内玻璃分离。'],
['上：顶层木色曲面顶棚、圆洞护栏、帘幕；圆洞不等同于中间层大挑空。','下：双层高工作空间、螺旋梯、局部中间楼板及梁柱；确有跨层空间。'],
['上：透视横剖，地面、完整下层、局部中间层、顶层；剖面左侧挑空、右侧中间楼板。其左右须经端部标志对齐。','下：底层平面；长条柱网、内部交通、远端楼梯与服务核；无可读尺寸。'],
['自上至下四幅：外钢架与玻璃缓冲区；木质加层与下垂屋顶；保留旧框架及局部楼板；旧构件再利用示意。文字是设计说明，不是实测或当前模型证明。'],
['上：开放顶层平面，圆洞与外环廊。','中：近坡道端半部大挑空，另一侧及远端保留局部楼板，远端螺旋梯与服务核。','下：较完整下层平面、分隔房间与梯核。上/中/下暂对应L3/L2/L1，图中无清晰层名。'],
['上：气候概念剖面，支持屋顶中垂、双层围护及大挑空；箭头非实体构件。','下：结构横剖，四个使用标高、局部中间楼板；右边屋顶较高。不能单凭此图断定真实方位。']]
sources=[]
for i,(name,ref) in enumerate(zip(names,refs)):
    p=project/ref
    assert p.is_file(), p
    with Image.open(p) as original:
        size=list(original.size)
    sources.append({'path':ref,'kind':['exterior_image','exterior_image','exterior_image','interior_image','floorplan_image','document','floorplan_image','document'][i], 'provenance':'observed','role':f'原图{i+1}，全部面板直接对照','notes':panels[i], 'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'image_size_px':size})

coordinate = '拟定观察者位于坡道短端X<0，朝+X看；+Z向上，画面左为+Y（Y=20000），画面右为-Y（Y=0）。X沿长向；没有真实北向。原平面图左端对应草图下端，原图上边对应草图左边。此为源图与草图约定，当前模型变换未重新原生核验。'
confirmed=['先不修改模型，先用八张原图做平面和剖面方向确认。','用户指出从坡道端看屋顶右边更高；保留现有曲面，坡道及其他部分先不动。']
constraints=['坡道端观察：屋顶右边高于左边，中央下垂，沿建筑长向延伸。','旧框架、上加木质空间、内外两层围护及深外廊分别表达。','L2为局部楼板，L1至L3之间保留大挑空；圆洞另行定位。','外坡道、转接平台、环廊和内楼梯不能互相替代。','本轮仅绘制草图与更新计划，不运行或修改SketchUp。']
assumptions=[coordinate,'层号L0/L1/L2/L3是工作命名，暂对应图5下图及图7下/中/上图；没有可读原层名。','地面起点在坡道端画面右侧，各段向左上升；完整连续通路拟由环廊回到右侧下一段起点，未有连续路径图证实具体绕行边。','50×20m及0/3.6/7.2/10.8m仅保留旧估值，不是用户提供或图纸测量。','未重新核验模型根、深层变换、下载及重开几何；历史修正是否提交、保存前屋顶状态均不能据本轮证明。']
evidence={'schema_version':1,'fidelity_mode':'multi_view_reconstruction','primary_source':refs[0],'sources':sources,'exterior_views':{},'floorplan':{'provided':True,'provenance':'observed','source_refs':[refs[4],refs[6]],'levels':['L0：图5下，暂定','L1/L2局部/L3：图7下/中/上，暂定'],'notes':['几何关系可见；层名、尺寸与精确端点不可读。']},'cad':{'provided':False,'provenance':'pending','source_refs':[],'notes':['无DWG或尺寸CAD。']},'interior':{'provided':True,'provenance':'observed','source_refs':[refs[3],refs[4],refs[6],refs[7]],'spaces':['曲面顶层大厅','下层双层高工作空间','局部中间层','圆洞及螺旋梯'],'notes':['挑空与圆洞分别表达，不能假定所有洞口都贯穿四层。']},'scale_anchors':[],'hard_constraints':constraints,'assumptions':assumptions,'user_confirmed':confirmed,'inference_policy':{'unseen_exterior':'infer_coherent','unseen_interior':'infer_plausible','preserve_circulation':True},'review_status':{'source_review':'eight_original_sheets_all_panels_compared','geometry_written':False,'native_model_identity':'NOT_VERIFIED_THIS_TURN','native_save_reopen':'BLOCKED_NO_NATIVE_EVIDENCE','historic_pre_save_geometry':'BLOCKED_MISSING_EVIDENCE'},'sketch':'notes/direction_sketch.png'}
mapping={'front':('observed',[0,1],['坡道短端，右高左低；以此定义左右。']),'rear':('inferred',[4,6],['远端服务核和端梯见平面，无独立正立面。']),'left':('inferred',[1,2,6],['长边外廊可见，但照片所示长边与+Y侧对应仍待原生相机/地标核验。']),'right':('inferred',[4,6,7],['另一长边关系由平剖面约束，不能直接镜像所有细节。']),'roof':('observed',[0,1,3,4,5,7],['横跨下垂，边缘不等高；实际曲率、最低点位置未量测。']),'oblique':('observed',[1],['相邻短长边及外廊深度可见。'])}
for v,(prov,ids,notes) in mapping.items(): evidence['exterior_views'][v]={'provenance':prov,'source_refs':[refs[i] for i in ids],'notes':notes}
facade={'schema_version':1,'source_mode':'multi_view_reconstruction','dimensions_mm':{'overall_width':58000,'overall_depth':28000,'level_height':3600,'floor_count':4},'views':{},'roof':{'provenance':'observed','type':'短跨中垂曲面，坡道端画面右高左低，沿长向延伸','parapet':'未见连续实心女儿墙的充分证据','divisions':['木色曲面顶棚/屋面','高低边支承与上部玻璃','外廊低位平檐，独立于主屋顶'],'notes':['外廊平檐不可当作主屋顶。','屋顶边缘绝对高度和曲率待测；不根据旧高边参数名决定左右。']},'global_features':['长条柱梁框架','退进下部与外扩上部','玻璃缓冲层及格栅外环廊','四个使用标高，其中中间层局部铺板','室内圆洞、螺旋梯、端部楼梯'],'user_confirmed':confirmed,'inferred':['dimensions_mm均为旧估值；4表示使用标高数，并非四层完整楼板。',coordinate]}
for v in ['front','rear','left','right']:
    facade['views'][v]={'provenance':mapping[v][0],'opening_count':None,'door_count':None,'features':mapping[v][2],'notes':['不凭材料分缝增加楼层；玻璃、框架、栏杆和步行面分别保留。']}

# Preserve existing method ownership and estimates without claiming execution or approval.
strategy=json.loads((w/'notes/construction_strategy.json').read_text(encoding='utf-8'))
strategy['current_stage']='pending'
params=strategy['shared_parameters']
for key,p in params.items():
    if p['units']!='text':
        p['provenance']='estimated'; p['source']='旧计划估值，图纸无可读尺寸；本轮仅比较方向与拓扑，未测量、未批准执行。'
params['scope']={'value':'本轮源图方向草图和计划确认；不修改既有模型，不重建。','units':'text','provenance':'user_confirmed','source':'2026-10-14最新用户请求。'}
params['roof_screen_relation']={'value':'从坡道短端朝+X看，右(Y=0)高于左(Y=20000)，中央下垂','units':'text','provenance':'observed','source':'图1上/下与用户说明；图2下及图5/8横剖支持屋顶形态。'}
params['coordinate_convention']={'value':coordinate,'units':'text','provenance':'inferred','source':'仅草图约定，尚未验证当前模型变换。'}
params['ramp_connection']={'value':'短端坡道向左上升，经平台接环廊；环廊返回下一段起点的精确路线待确认','units':'text','provenance':'inferred','source':'图1/2各段坡向可见，图3入口与图7环廊约束衔接。'}
params['floor_topology']={'value':'L0地面；L1较完整下层；L2局部板与大挑空；L3顶层含圆洞','units':'text','provenance':'inferred','source':'图5/8剖面与图7下/中/上平面，层名暂定。'}
for s in strategy['systems']:
    s['status']='pending'
    s['notes']=['历史构造方法仅保留为候选；本轮未调用，不代表已建或验证。','只在核验模型身份与实际命名路径后用于批准范围；先建空父组，再在其entities内建子项；兄弟元素语义ID唯一。']
    if s['id']=='roof':
        s['method']='custom_owned_ruby'; s['method_id']='kstudio.project_ruby.scoped_existing_roof_transform'
        s['selection_reason']='若以后只改左右高低，应先核验现有屋顶及支承变换并保留现有曲面；SAIE直墙或ADAI重新挤出不能保留该现有曲面。具体变换尚未选择，本轮不执行。'
        s['depends_on']+=['roof_screen_relation','coordinate_convention']
    if s['id']=='floors': s['depends_on']+=['floor_topology']
    if s['id']=='ramps': s['depends_on']+=['ramp_connection']; s['notes'].append('本轮及已提出的屋顶局部修正均不授权修改坡道。')
    s['depends_on']=list(dict.fromkeys(s['depends_on']))
strategy['notes']=['本轮仅计划草图；不以pending推断当前模型没有几何，不以旧记录宣称原生身份已验证。','主体/楼板/屋顶/坡道归primary_form；玻璃栏杆样件归representative_module；重复归replication；内梯隔墙归variants；地面家具归finish。该阶段划分不是重建指令。','ADAI合同记载0.5.39启用；只记录候选，不宣称本轮调用。','后续屋顶局部修正须冻结坡道、楼板、围护、室内及场地；关联支承是否需动须依据接缝另定，不能默认扩大范围。','深层原生保存/重开证据和历史保存前状态缺失：BLOCKED；不得用本草图代替原生交付证据。']
card='''# 八图方向复核卡｜2026-10-14｜待用户确认

本轮仅核对原图、画草图和更新计划。未修改SketchUp；不是全量重建请求。

## KNOWN：图中观察／用户确认
- 八张原图全部面板已对照：1端部外观/实体模型，2场地轴测/斜视模型，3入口/外廊，4顶层/双层高室内，5横剖/底层平面，6四层分解示意，7三张平面，8气候/结构剖面。图片内的实体模型仍是原始参考，不是当前SketchUp。
- 整体是长条柱梁框架，上加木质空间；上部外玻璃扩出，内部围护与外皮之间有深环廊。格栅、横梁和下部退进可见。
- 图1坡道端：屋顶右侧更高、左侧较低、中部下垂；图2与图5/8支持横跨曲面沿长向延伸。外廊平檐是另一系统。
- 图1三段坡道的端部投影都向左上升，图3首段接架空平台；不能画成逐层交替左右爬升的简单之字。
- 图5/8显示四个使用标高，局部中间楼板与大挑空；图7中图给出挑空平面范围，图4显示双层高空间。顶层圆洞与这一大挑空分别定位。
- 用户要求先不改模型；屋顶右高、保留曲面及其他部分的约束持续有效。

## ASSUMED：草图约定与待核实拓扑
观察者站坡道短端，朝建筑长向看：X沿长向，Z向上；左为+Y（Y=20000），右为-Y（Y=0）。不是实际北向，当前模型轴/变换尚未原生核验。
原平面图左端旋转到草图下端；图7上/中/下暂标L3/L2/L1，图5下暂标L0。L2近坡道端左侧留大挑空，右侧及远端保留楼板；顶层较完整，另有圆洞。剖面穿过近端挑空，仅为关系示意。
拟定连续路径：地面右侧→坡道向左上升→L1左侧平台→环廊回到右侧下一段起点→L2、L3。各段坡向有图像依据；环廊到底绕哪条长边及转接净宽尚无完整连续路径证据，草图虚线标示，不当作测绘结论。

## ESTIMATED：仅保留旧估值
内框架约50×20m，外皮约58×28m，层标高约0/3.6/7.2/10.8m。源图无可读尺寸；屋顶曲率、最低点偏位、边高差、坡道长度/坡度与准确洞口位置仍待确定。不把旧roof_edge_a/b名称当成左右依据。

## 后续范围与构造候选
确认方向后仍以同一模型局部核查为目标：先核验原生身份、根和变换，再核对屋顶/支承及接缝；任何修改另按确认范围进行，不自动重建或调整坡道。
主体及楼板、屋顶和交通关系先于重复立面细节。历史候选：ADAI闭合洞口板/截面，组件复用框架和玻璃栏杆，SAIE普通直墙；已有曲面局部修正优先保留现有几何，具体变换待原生读回。每个方法均未在本轮执行。

## 文件与证据边界
草图：notes/direction_sketch.png（平面、横剖、坡道投影）；非实测、不按比例。
四份计划文件本轮重新写入UTF-8并校验。没有新增设计任务书、场地要求、URL或CAD；源建筑复核，不做场地/功能改编。
本轮无SketchUp读写工具；模型身份、当前提交、深层变换、下载/重开差异无法原生确认。历史保存前证据缺失及原生交付诊断标记BLOCKED，不编造修正成功。
'''
(w/'notes/reconstruction_card.md').write_text(card,encoding='utf-8')
for file,data in [('reconstruction_evidence.json',evidence),('facade_schedule.json',facade),('construction_strategy.json',strategy)]:
    (w/'notes'/file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Draw a standalone schematic, not a reconstruction image or source measurement.
im=Image.new('RGB',(1500,1280),'#fafbf9'); d=ImageDraw.Draw(im)
font_path='C:/Windows/Fonts/msyh.ttc'
def text(x,y,s,size=23,fill='#23343b'):
    d.text((x,y),s,font=ImageFont.truetype(font_path,size),fill=fill)
def line(points,fill='#374b52',width=3): d.line(points,fill=fill,width=width)
def arrow(a,b,fill='#18778b',width=4):
    import math
    line([a,b],fill,width)
    ang=math.atan2(b[1]-a[1],b[0]-a[0]); length=12
    for delta in [-0.5,0.5]: line([b,(b[0]-length*math.cos(ang+delta),b[1]-length*math.sin(ang+delta))],fill,width)
def dashed(a,b,fill='#ba7536'):
    import math
    length=math.dist(a,b)
    for start in range(0,int(length),18):
        t=start/length; u=min((start+10)/length,1)
        line([(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t),(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)],fill,3)
text(45,25,'八张原图方向复核 · 草图供确认',34)
text(45,76,'同一观察方向：站在坡道短端，朝建筑长向看。非实测、不按比例；本轮不改模型。',23)
text(60,132,'平面示意：L2局部中间层',27)
d.rectangle((130,210,530,730),outline='#97b3b9',width=3)
d.rectangle((180,255,480,680),fill='#e4e9e8',outline='#374b52',width=3)
d.rectangle((180,370,330,680),fill='#fafbf9',outline='#ba7536',width=3)
for yy in range(385,680,25): line([(185,yy),(325,yy+8)],'#e1c09e',1)
d.rectangle((180,255,230,315),outline='#374b52',width=2)
text(183,261,'端梯',20)
d.rectangle((390,255,480,335),outline='#374b52',width=2)
text(399,280,'服务核',20)
d.ellipse((265,280,323,338),outline='#374b52',width=3)
text(237,340,'螺旋梯/洞口',18)
text(195,463,'大挑空',27, '#a36027'); text(194,505,'俯看L1',21)
text(351,485,'局部楼板',23); text(340,527,'近右侧保留',19)
text(209,173,'远端（原平面图右端）',21)
text(52,385,'环',23); text(52,420,'廊',23)
text(538,385,'环',23); text(538,420,'廊',23)
line([(110,610),(550,610)],'#677c87',2); text(82,585,'A',21);text(552,585,'A',21)
text(138,743,'左：低屋顶边',20);text(370,743,'右：高屋顶边',20)
arrow((495,815),(160,777)); text(203,817,'坡道向左上升',22)
text(440,785,'起点',19)
arrow((330,910),(330,847));text(183,927,'观察者：朝 +X 看',23)
text(115,876,'+Y（左）',19);text(417,876,'−Y（右）',19)
for a,b in [((145,725),(145,225)),((145,225),(515,225)),((515,225),(515,725))]: dashed(a,b)
text(110,984,'橙色虚线：环廊返回路线候选，绕行边待确认',19,'#a36027')
text(690,132,'A—A 横剖示意：穿过近端挑空',27)
text(698,173,'左右与坡道端正视一致；不代表精确剖切位置',20)
# Concave asymmetric roof, right edge higher.
roof=[]
for i in range(101):
    t=i/100; roof.append((845+450*t,(1-t)**2*246+2*t*(1-t)*375+t*t*211))
line(roof,'#a57749',8)
text(793,209,'左较低',21);text(1246,174,'右更高',25,'#18778b')
text(982,314,'中部下垂',23,'#a57749')
for x in [845,1295]: line([(x,250 if x==845 else 215),(x,780)],'#88969b',4)
for yy in [435,545,655]: line([(748,yy),(1390,yy)],'#91b4bb',3)
# L2 slab incomplete, remove the void portion of line.
line([(846,545),(1065,545)],'#fafbf9',8)
line([(845,435),(1295,435)],'#374b52',7)
line([(1065,545),(1295,545)],'#374b52',7)
line([(845,655),(1295,655)],'#374b52',7)
line([(845,765),(1295,765)],'#374b52',7)
for yy,label in [(435,'L3 顶层'),(545,'L2 局部'),(655,'L1 下层'),(765,'L0 地面')]: text(680,yy-30,label,22)
text(873,482,'挑空',25,'#a36027');text(874,562,'L1至L3',20);text(874,594,'双层高',20)
text(1092,552,'局部房间/楼板',20)
text(959,388,'顶层大厅；圆洞另行定位',20)
text(868,703,'地面层，上方为较完整L1楼板',19)
text(815,805,'外皮与内框架间为环廊/缓冲区',21)
text(690,861,'坡道端投影：三段均向左爬升',27)
for ya,label,start_label in [(920,'L3','L2起点'),(995,'L2','L1起点'),(1070,'L1','L0地面')]:
    line([(835,ya),(935,ya)],'#6a8189',3)
    arrow((1300,ya+75),(850,ya),'#18778b',4)
    text(760,ya-14,label,21)
    text(1310,ya+49,start_label,19)
text(832,1160,'段间通过平台、环廊返回下一起点（具体绕行待确认）',20,'#a36027')
text(45,1223,'实线：源图可见关系　｜　虚线/层号：推定　｜　尺寸、曲率、坡度及洞口精确位置未定',22)
im.save(w/'notes/direction_sketch.png')

for name in ['reconstruction_card.md','reconstruction_evidence.json','facade_schedule.json','construction_strategy.json']:
    p=w/'notes'/name; raw=p.read_text(encoding='utf-8'); assert '\ufffd' not in raw
    if p.suffix=='.json': json.loads(raw)
    print(name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
assert len(sources)==8
assert all(k in params for s in strategy['systems'] for k in s['depends_on'])
print('Verified: eight source hashes, four refreshed UTF-8 notes, direction sketch; no SketchUp operations.')
