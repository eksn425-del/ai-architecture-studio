import json
import hashlib
from pathlib import Path

workspace = Path.cwd()
project = workspace.parent.parent
files = [
 '9d05f4a6ae-codex-clipboard-1b4276a9-93d4-4833-95cb-c3b193c9c96d.png',
 'ade9a9063c-codex-clipboard-273f5c39-ee57-4cd8-a0c0-d1113b742a27.png',
 '8e8a3625d5-codex-clipboard-a04d023f-1044-423f-89db-4a0b51e92505.png',
 'c55a28860e-codex-clipboard-fdf7fe7c-e5f1-47d4-b800-d4f5eaf99b52.png',
 'da5324e1c5-codex-clipboard-1ed05c14-1674-4910-bc05-ccb2c03aec93.png',
 '4fdbe428b1-codex-clipboard-8856a1fd-12c2-44d9-a5af-868c4c8d4c2a.png',
 '8328ae9aa4-codex-clipboard-538fb3e3-5783-461e-8458-b231bd90bd57.png',
 '92fc9f3b50-codex-clipboard-10ea73cd-a751-4576-b174-295e6446a725.png']
refs = ['inputs/reference/' + f for f in files]
panels = [
 ['上：短端外观，玻璃上部外扩、下部退进、斜拉杆与连续坡道。下：同短端模型，曲面屋顶中部低、两侧高且不等高。'],
 ['上：鸟瞰线图，长条平面、短跨下垂的屋顶沿长向延伸。下：短端和长侧模型斜视，坡道平台接侧廊，外皮与内框架之间有深度。'],
 ['上：近地入口，首段坡道接架空平台，底层玻璃内退。下：长侧廊近景，混凝土柱、外挑钢梁、格栅平台与网栏。'],
 ['上：木色曲面顶棚、圆形楼板洞口及护栏、帘幕。下：双层高工作空间、螺旋梯、局部上层楼板及柱梁。'],
 ['上：透视剖面，地面层、完整下层、局部中间层、木构顶层；外侧缓冲廊。下：地面层平面，长条柱网、圆形梯位、图右端交通服务区。'],
 ['从上至下四个分解图：玻璃与轻钢拉索外层；木构加层及曲面屋顶；原混凝土框架；旧构件再利用示意。文字属于方案说明，不是尺寸或施工验证。'],
 ['上：开放顶层平面，圆形洞口与环廊。中：左部大挑空、右部局部楼板，圆形梯位与图右端服务区。下：较完整下层、分隔房间、圆形梯位；三图无清晰楼层标注。'],
 ['上：气候剖面，确认内外双层围护和贯通空间；箭头与设备符号不是实体建模指令。下：结构剖面，四个使用标高、局部中间楼板、下垂屋顶、不等高边缘及原框架。']]
scope = ['用于课程汇报的可修改SketchUp模型','室内保留主要结构、挑空、主要隔墙和楼梯，家具简化','周边只做紧邻建筑的地面','无准确尺寸可合理估算，优先整体形状、曲面屋顶和坡道']
constraints = ['原框架、木构加层与外玻璃缓冲层分开，不合并成单层玻璃盒子','屋顶沿短跨下垂、两侧不等高，沿长向延伸；不得改成平屋顶或普通拱顶','中间层保留大挑空，不做四层满铺楼板','坡道、转折平台与环廊连续连接，首段落地；后端不可直接镜像前端','圆形洞口与螺旋梯共享定位；玻璃、框、梁、栏杆和楼板分别可编辑']
assumptions = ['X为长向、Y为短向、Z向上；图1短端为front/X=0，rear/X=50000；left/Y=0、right/Y=20000，仅为模型坐标，不代表南北','图5下暂对应L0；图7下/中/上暂对应L1/L2局部/L3，属于推断','外皮最大范围58×28m、内框架50×20m；约十个长向结构跨，玻璃分格另行核对','真实尺度、构件截面、屋顶函数、隐藏端细节和坡道精确坡度均未知；没有已确认的跨图几何矛盾']
evidence = {'schema_version':1,'fidelity_mode':'multi_view_reconstruction','primary_source':refs[0],
 'sources':[{'path':r,'kind':k,'provenance':'observed','role':f'原始图{i+1}；已直接检查全部分面','notes':p,'sha256':hashlib.sha256((project/r).read_bytes()).hexdigest()} for i,(r,k,p) in enumerate(zip(refs,['exterior_image','exterior_image','exterior_image','interior_image','floorplan_image','document','floorplan_image','document'],panels))],
 'exterior_views':{},
 'floorplan':{'provided':True,'provenance':'observed','source_refs':[refs[4],refs[6]],'levels':['L0暂对应图5下','L1/L2局部/L3暂对应图7下/中/上'],'notes':['形状与洞口有图像证据；楼层映射和尺寸为推断，非测量。']},
 'cad':{'provided':False,'provenance':'pending','source_refs':[],'notes':['未提供DWG或尺寸CAD。']},
 'interior':{'provided':True,'provenance':'observed','source_refs':[refs[3],refs[4],refs[6]],'spaces':['顶层开放空间','双层高工作空间'],'notes':['主要柱梁、圆形洞口、螺旋梯、局部楼板可见。']},
 'scale_anchors':[{'name':'人物身高假定；非实测','value_mm':1700,'provenance':'inferred','source_ref':refs[2]}],
 'hard_constraints':constraints,'assumptions':assumptions,'user_confirmed':scope,
 'inference_policy':{'unseen_exterior':'infer_coherent','unseen_interior':'infer_plausible','preserve_circulation':True},
 'inspection_note':'八个原始文件包含18个分面；效果图、模型照、图纸是同方案不同表达，均非当前SketchUp模型。没有场地适配任务。'}
for view,prov,indices,note in [('front','observed',[0,1],'短端坡道立面'),('rear','inferred',[6],'仅图纸约束隐藏端；没有正对后端照片'),('left','observed',[1,2],'可见长侧；Y侧映射暂定'),('right','inferred',[4,6,7],'剖面及平面约束另一侧，无完整正立面'),('roof','observed',[0,1,3,4,5,7],'短跨下垂曲面及不等高边缘'),('oblique','observed',[1],'长短向比例、外皮厚度与坡道平台')]:
 evidence['exterior_views'][view]={'provenance':prov,'source_refs':[refs[i] for i in indices],'notes':[note]}
params={}
for key,value in {'body_length':50000,'body_depth':20000,'envelope_length':58000,'envelope_depth':28000,'buffer_depth':4000,'bay_length':5000,'level_0':0,'level_1':3600,'level_2':7200,'level_3':10800,'roof_low':13800,'roof_edge_a':15500,'roof_edge_b':16500,'ramp_width':2200,'rail_height':1100,'slab_thickness':250}.items():
 params[key]={'value':value,'units':'mm','provenance':'estimated','source':'平面内框架约2.5:1、剖面层间关系及人物比例共同约束；仅初始可调估值'}
params['scope']={'value':'；'.join(scope),'units':'text','provenance':'user_confirmed','source':'本轮用户确认范围不变'}
specs=[
 ('frame','primary_form','shell','prototype_instance','sketchup.component_definition_and_instances','柱梁是重复框架而非墙开洞；复用原生组件，不需墙体辅助方法',['body_length','body_depth','bay_length','level_3'],[['STRUCTURE_EXISTING']],['front','oblique']),
 ('floors','primary_form','shell','profile_extrusion','adai_geometry.profile_with_holes','本地合同明确已启用；用于闭合圆洞楼板，边界相接大挑空改用分段profile，避免无效孔环',['body_length','body_depth','level_0','level_1','level_2','level_3','slab_thickness'],[['FLOORS','L0'],['FLOORS','L1'],['FLOORS','L2_PARTIAL'],['FLOORS','L3']],['roof','oblique']),
 ('roof','primary_form','roof','profile_extrusion','adai_geometry.profile','已启用yz截面沿X挤出可表达短跨下垂；目前无需要双曲面的可靠证据',['body_length','body_depth','roof_low','roof_edge_a','roof_edge_b'],[['ROOF_TIMBER','CURVED_SHELL']],['front','roof','oblique']),
 ('envelope_bounds','primary_form','shell','custom_owned_ruby','sketchup.entities.add_face','透明外皮的上部外扩和底部退进不适合实墙开洞辅助方法；用最小面片作界线，后续同组替换为真实构件',['envelope_length','envelope_depth','buffer_depth','level_1','level_3'],[['ENVELOPE_OUTER']],['front','left','oblique']),
 ('ramps','primary_form','balcony','profile_extrusion','adai_geometry.profile','已启用profile适合坡道侧截面与平台；先用独立节点记录标高和连接，不能以栏杆线替代可走实体',['ramp_width','level_0','level_1','level_2','level_3','buffer_depth'],[['CIRCULATION_EXTERNAL','RAMPS'],['CIRCULATION_EXTERNAL','LANDINGS'],['CIRCULATION_EXTERNAL','GALLERIES']],['front','roof','oblique']),
 ('module','representative_module','opening_system','prototype_instance','sketchup.component_definition_and_instances','玻璃幕墙与网栏应分部件组件，不适用实墙开洞；先验证一跨及一段护栏',['bay_length','buffer_depth','rail_height'],[['ENVELOPE_OUTER','MODULE'],['CIRCULATION_EXTERNAL','RAIL_MODULE']],['front','oblique']),
 ('repeat','replication','repetition','prototype_instance','sketchup.component_definition_and_instances','复用已验证玻璃、框、格栅与栏杆组件；结构跨不等同玻璃分格',['envelope_length','envelope_depth','bay_length'],[['ENVELOPE_OUTER','FRONT'],['ENVELOPE_OUTER','REAR'],['ENVELOPE_OUTER','LEFT'],['ENVELOPE_OUTER','RIGHT']],['front','rear','left','right','oblique']),
 ('stairs_partitions','variants','interior_detail','custom_owned_ruby','sketchup.entities.add_face_and_component_instances','当前已验证ADAI合同仅profile；螺旋梯的扇形踏步和共轴洞口需最小原生组件组合，SAIE墙开洞不适合旋转梯；普通隔墙采用简单独立板件',['level_0','level_1','level_2','level_3','scope'],[['CIRCULATION_INTERNAL','SPIRAL_STAIRS'],['CIRCULATION_INTERNAL','END_STAIRS'],['INTERIOR','PARTITIONS']],['roof','oblique']),
 ('finish','finish','site','prototype_instance','sketchup.component_definition_and_instances','家具用可隐藏简化组件，地面仅紧邻区域，不需要新的场地工具',['scope','envelope_length','envelope_depth'],[['SITE_GROUND'],['INTERIOR','FURNITURE_SIMPLIFIED']],['front','roof','oblique'])]
strategy={'schema_version':1,'current_stage':'pending','stage_order':['primary_form','representative_module','replication','variants','finish'],'shared_parameters':params,'systems':[],
 'notes':['所有方法仅为选择计划，尚未执行或证明OSS使用成功。','开始前须核验空白可丢弃模型身份；仅在提供的所属根内单一受保护写入；兄弟元素使用唯一语义ID。','每阶段由所列系统独占目标组；所有层高、坡道平台与洞口共用参数，避免多个脚本重复创建。','每次实际写入后做原图角度和六标准视图的独立审查，再决定后续；本轮没有几何写入。','坡道坡度按各段实际水平长度和层差计算，不宣称满足无障碍规范；隐藏端不复制前端。','原型临时件验证后替换或转作实例，避免与正式立面重叠。']}
for sid,stage,role,method,mid,reason,deps,paths,views in specs:
 strategy['systems'].append({'id':sid,'stage':stage,'role':role,'method':method,'method_id':mid,'selection_reason':reason,'status':'pending','depends_on':deps,'target_paths':paths,'verification_views':views,'notes':['唯一实例ID采用系统/侧面/层/序号；共享定义与实例ID分开。']})
facade={'schema_version':1,'source_mode':'multi_view_reconstruction','dimensions_mm':{'overall_width':58000,'overall_depth':28000,'level_height':3600,'floor_count':4},'views':{},
 'roof':{'provenance':'mixed','type':'短跨下垂、两侧不等高、沿长向延伸的木色曲面屋顶','parapet':'未证实独立实体女儿墙','divisions':['木构曲面壳体','高边支承框架','与外层玻璃相邻的低位水平边带'],'notes':['低点13.8m、两边15.5/16.5m为估值；曲率和低点偏移可调。']},
 'global_features':['内混凝土框架/内玻璃—缓冲廊—外轻钢玻璃三层关系','底层退进、上部玻璃外扩、格栅平台、细网栏与斜拉杆','浅灰混凝土、白钢、透明玻璃、木色顶棚、局部绿色板'],
 'user_confirmed':scope,'inferred':assumptions+['dimensions_mm全部为估算；四个使用标高含局部层，不代表四层满铺。']}
features={'front':['折返坡道、逐层平台、白色玻璃框','底部退进、斜拉杆'], 'rear':['依据图右端服务交通区安排端部直梯及开口，细节待核'], 'left':['深缓冲廊、挑出格栅平台、连续细框玻璃','局部绿色板'], 'right':['按剖面保留另一侧缓冲廊与结构，不强制镜像']}
for v in ['front','rear','left','right']:
 facade['views'][v]={'provenance':'mixed' if v in ['front','left'] else 'inferred','opening_count':None,'door_count':None,'features':features[v],'notes':['玻璃分格按原图另核；遮挡区开口数量不伪造。']}
card='''# 玻璃与曲面屋顶建筑：已核对的建模计划

## KNOWN：用户确认与可见事实
用户确认：八图同栋、用于课程汇报；主要结构、挑空、隔墙和楼梯保留，家具简化，场地只做紧邻地面；尺寸允许估算。属于原图还原，不作场地或功能改设计。
已直接检查八张原图全部18个分面：图1外观/短端模型；图2鸟瞰/长短侧模型；图3入口/长廊；图4曲面顶层/双层高室内；图5剖面/地面平面；图6四层分解；图7三层平面；图8气候/结构剖面。
共同关系：长条混凝土旧框架上加木构顶层；外玻璃与内框架之间有深缓冲廊，上部外扩、底部退进。屋顶沿短跨中部下垂、两侧不等高，沿长向延伸。短端连续坡道接平台与侧廊。内部有局部中间楼板、大挑空、圆洞与螺旋梯，不能满铺四层。

## ESTIMATED：可调整的初始参数
- 内框架50×20m，外皮最大58×28m，侧廊约4m；平面内框架约2.5:1、约十个长向跨及人物比例为估算锚点，不是实测尺寸。
- L0/L1/L2局部/L3标高0/3.6/7.2/10.8m；屋顶谷底13.8m、两侧15.5/16.5m。屋顶曲率与最低点可调，不采用固定圆弧或强制对称。
- 坡道暂宽2.2m、栏杆高1.1m、楼板厚0.25m。逐段计算水平长度、标高与坡度，不以统一坡度硬套，不声称规范验证。

## ASSUMED：仍需视觉核对
X长向、Y短向、Z向上；图1短端为front/X=0，仅模型命名，不代表真实方位。图5下暂为L0，图7下/中/上暂为L1/L2局部/L3。图7中左部大挑空、右部局部板优先于通用楼板假设。隐藏后端、准确尺度、坡道转折细节和楼层标注未知；未发现已确认的跨图矛盾。图中功能箭头和设备符号不生成实体。

## 整体形状、屋顶与坡道安排
1. 先建原柱梁框架、完整下层和局部中间层/洞口，再建立木构顶层及短跨下垂屋顶。用图1短端轮廓、图2长侧比例、图5/8剖面核对高度和外扩/退进。
2. 外皮与内玻璃分开，廊道有实体宽度；低位水平边带与主曲面屋顶分组，避免把外廊屋面当作另一层主屋顶。
3. 首段坡道从紧邻地面到L1平台，其后按图1/2短端上下折返关系接L2、L3平台和侧廊。每段记录起终点、标高、宽度、接驳平台；图示连续路线为依据，具体坡度及转折位置为待校正估值。隐藏端按平面安排服务交通，不镜像坡道。
4. 圆洞和螺旋梯共用中心定位，局部层按剖面留空；端部直梯与服务区按图7安排，不把所有圆洞都当作贯穿每层的同一楼梯。

## 阶段与可编辑组织
顺序：主体/屋顶/坡道拓扑 → 一跨幕墙和一段护栏验证 → 组件重复 → 主要隔墙、楼梯及端部差异 → 简化家具、地面和汇报视图。
根下分组：STRUCTURE_EXISTING、FLOORS、ROOF_TIMBER、ENVELOPE_OUTER、CIRCULATION_EXTERNAL、CIRCULATION_INTERNAL、INTERIOR、SITE_GROUND；层、侧面、坡道段有独立名称及唯一实例ID。玻璃/框/拉杆、屋顶/支承、坡道/平台/栏杆分开。
方法：原生组件复用柱梁、玻璃框和栏杆；本地已启用ADAI profile用于曲面截面和坡道，profile_with_holes用于闭合洞口楼板，边界挑空用分段轮廓。螺旋踏步采用最小原生组件组合。所有方法仅为计划，尚未调用。
实际开工前核验空白可丢弃模型及所属根。每次写入后先对原图角度及六标准视图做独立审查；主体形状与交通关系正确后才细化重复构件。

## 当前状态
四份计划本轮已重新保存；范围已确认，具体计划等待用户批准。没有SketchUp几何写入，不声称模型已完成。
'''
notes=workspace/'notes'
notes.mkdir(exist_ok=True)
(notes/'reconstruction_card.md').write_text(card,encoding='utf-8')
for name,data in [('reconstruction_evidence.json',evidence),('facade_schedule.json',facade),('construction_strategy.json',strategy)]:
 (notes/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['reconstruction_card.md','reconstruction_evidence.json','facade_schedule.json','construction_strategy.json']:
 path=notes/name
 contents=path.read_text(encoding='utf-8')
 assert '\ufffd' not in contents
 if path.suffix=='.json': json.loads(contents)
 print(name, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
assert all(d in params for s in strategy['systems'] for d in s['depends_on'])
assert len(evidence['sources'])==8
print('VERIFIED: 4 UTF-8 notes saved; 8 original source hashes; no geometry writes.')
