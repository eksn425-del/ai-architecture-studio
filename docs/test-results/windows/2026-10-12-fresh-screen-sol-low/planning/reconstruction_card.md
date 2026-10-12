# 白色遮阳屏露台建筑：重建参数方案

## 状态与证据
规划待确认；本轮无SketchUp几何编辑。多视角重建（multi_view_reconstruction），三张七面板；没有CAD、平面图、完整室内或背立面。
KNOWN：用户确认同一栋建筑，允许估算尺寸和背面补全，要求可编辑主体、玻璃、白色遮阳屏、露台、楼梯。
上传顺序按用户修正：第一张e8b29b2975…上正面/下右前斜视；第二张4745639df3…上俯视/中露台/下左短立面；第三张ca2fcc34f6…上楼梯/下遮阳屏。此前图号按展示顺序，现改为实际上传顺序。

## 五项源图约束
1. 两层主体＋屋顶玻璃房，右侧长条屏幕和左侧退台构成不对称外形；第一张两面板→FLOORS/ROOF/ROOF_ROOM；正面、右前斜视检查。
2. 长面白色密孔屏及右侧转角，细框分板、后方玻璃可透见；第一张及第三张下部→SCREENS；正面/右侧检查。常规板暂辨12块＋窄收口，孔形与准确数量需代表模块复核。
3. 左侧二层露台与屋顶露台上下叠置、主体后退；第二张中/下部→TERRACES/RAILINGS；左侧检查。
4. 正面两跑同向外楼梯带中间平台、玻璃斜栏杆，木色墙在后；第三张上部→STAIR/WALLS；正面近景检查。
5. 落地玻璃、深色框、屋顶玻璃房及左侧六组伞桌；第二张上部/第一张下部→GLAZING/ROOF_ROOM/FURNITURE；俯视/斜视检查。

## 统一尺寸与坐标
ESTIMATED（用户接受，仍非实测）：总长24000mm、进深12000mm；两层各3600mm，屋顶玻璃房高2600mm，总高约9800mm。
原点：建筑外包络正面左角地面。+X向正面右侧，+Y向背面，+Z向上；正面Y=0，背面Y=12000。地面Z=0，二层完成面3600，屋顶露台完成面7200。楼板250mm向完成面下方，层内名义净高3350mm，局部梁另计。
ASSUMED：墙厚200mm；玻璃8mm，框嵌接10mm；栏杆1100mm；屏幕与玻璃450mm净距，屏高3600mm。右侧屏幕范围X约10800–24000，Z约3950–7550，转角延续至Y约10000；均按图比例估算，不能改变可见外形。
玻璃房暂估X=13000–21500、Y=3500–9500；屋顶通道连续。二层左露台与主体退距约2500mm；外楼梯宽1500mm，24级×150mm，两跑各12级、平台Z=1800mm，踏步300mm，平台长约1500mm。准确分级为推定，形态和接层为硬约束。
门窗逐立面按facade_schedule.json；未知开启扇/门数保持null，不把幕墙格数当洞口数。背面用相同框架及材料补全，不镜像正面楼梯或屏幕。

## 建模结构与方法
独立命名：WALLS、FLOORS、ROOF、TERRACES、ROOF_ROOM、GLAZING、SCREENS、STAIR、RAILINGS、MATERIAL_ZONES、PLANTERS、FURNITURE、SITE；子构件独立语义ID，重复板、框格和栏板用组件实例。
直墙洞口优先SAIE（执行前验证实际接口）；板壳和网板穿孔优先已启用ADAI轮廓方法；楼梯、组件层级与重复采用项目原生几何。当前没有调用、建成或质量合格记录。具体选择/依赖见construction_strategy.json。
连接检查：板墙、墙洞、楼梯平台接层≤5mm；玻璃嵌框10mm；屏玻璃450mm为有意净距。模型读回和近景均须验证，包围盒接触不算连接合格。
材料：白色屏及板边、深灰框、半透明玻璃、木色墙面及板底。密孔保留可见细密效果及真实板厚，先检验一个模块的几何与性能；不改成稀疏百叶。

## 顺序与所有权
审批后：主形（同时包含退台、屋顶房、主要开口、楼梯与屏轮廓）→代表模块（屏、玻璃框、栏板）→检验后重复→转角及特殊门→花池/简化伞桌/材质。
构建者负责唯一写入；检查者只读，进度在真实模型读回后更新。脚本计划scripts/reconstruct_white_screen.rb，尚未创建。后续修正另存候选脚本，保护已接受部分。
对照七面板中的正面、右前斜视、俯视、左侧和楼梯近景；六个标准检查视图另存。主要比例不符先修主体，不靠装饰掩盖；一次主要构建最多两次有依据修正。尺寸/接口/拓扑须先验一个真实代表段；通过后才能重复。

## 推定边界与审批
室内只补必要楼板、空间和屋顶交通，不设计完整装修；花池、桌椅伞简化。场地铺装仅作展示底座，未提供用地或功能改造要求。
方案审批：待用户确认。用户已接受整体估算与背面补全，但尚未确认此完整方案。未建模；视觉质量未评。

## 2026-10-12 scoped user correction
Only add STAIR_WHITE_SIDEBOARD and ROOF_ROOM_CLERESTORY. Keep every existing root child unchanged. Stair fascia: continuous XZ outline, 180 mm thick, ~550 mm vertical depth, outside stair under existing glass railing. adai.profile is suitable for constant section; straight SAIE wall cannot follow both slopes. Roof room: 55 mm dark horizontal transoms at Z9350 leave ~395 mm top lights below existing head; existing glass and roof remain unchanged. Custom owned Ruby for frame bars because wall/opening helpers are unsuitable for additive curtain-wall members. All values estimated from source detail; user explicitly constrains scope to these two corrections.
