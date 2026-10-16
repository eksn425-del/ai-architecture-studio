# 当前施工：第18版后，补真实室内顶棚与细支承、纠正饰面/查看明暗

持久script_id为glass_curved_roof；只读分页limit为1..100，别猜脚本名或请求超范围页。

原八张整图/原顺序/原项目architecture-project-4f0e4/root20606，实际18已网站保存下载/SU2024三阶段声明精度通过，rawdoubleFAIL和严格空白重放NOT_RUN保留，原r4/r18不可覆盖。实际网站Sol6.1Medium、外层不变，本地Token/工具/总时间0无限、累计历史完整。上轮外檐末跨竖框已补，152/152连接、228开孔、152保留玻璃、6横框接触全部通过，本轮外部完整KEEP。

31准确路径在local-edit-scope.json/interior-finish-registration.json：六个已有螺旋梯中心柱/底座叶(非整个SPIRAL父组)、24受严格表面保护的已有楼板/木顶/桌面叶、唯一新增INTERIOR/CEILING_TENSION_MEMBERS。所有目标原容器PID保持。全部旧72踏步、原径向支承、平台板/旧支承、细网、圆洞、梁柱、外部与帘幕保护；不能切梁板或整体移楼。主机actual native capture列出每个对象PID/25FaceID/158EdgeID，给新writer提交前surfaceguard使用。

中心柱原R370确偏粗，按原图04和现有直径3.4m楼梯推断新柱直径300mm、同心37000/6500mm、各段原3600mm高度，底座直径450mm/原35mm高。只清空/重建各自CORE/COLLAR已有叶，保持其PID。每级踏步旧径向支承从R360开始，现需在新CORE组内部补短支承，R145到R390左右、实际原支承中心高度/方向，嵌入新柱及旧杆且顶面接踏步底，绝不能只缩柱留空悬挑。实际S{k}_LANDING_SUPPORT_0/1由R390到2350、中心Zbase3450、宽65，实际顶base3482.5与平台底base3500有17.5mm空隙；在CORE组内补两条约R145..425的根连接，中心Zbase3467.5、宽65，顶base3500接真实平台底，同时与旧杆体重叠。角度用真实旧杆变换/原生读回(20/45deg)，不要猜位。不修改旧平台/支承/tread/mesh。原生216净空及实际新柱-短支承-旧杆/踏步/平台接触必须复测。

原图04确有木质天花饰面和浅V形细构件，需补。上层原梁底真实10320mm；新叶中15组浅V位置已在native_verification.actual_approved_v_members列出，另5组经过L3真实洞口而排除，禁止加回被排除的杆。断面35mm、端点10330(嵌梁底10mm)、中点10050，x按实际5m梁跨中点，Y段150..9850或10150..19850，按图推断位置/断面和隐蔽接头，不声称源图精确尺寸。两端接原LONG_BEAM_Z10800_Y0/1/2实体，低点在局部7200楼板上方2850，不穿洞/楼梯路线。使用真实共享杆件原型，别重建大量独立细线实体。

表面规则不是放宽几何保护：24叶内只能改constrained_surface_edits列出的25个Face正背材质和158个低夹角木顶Edge.soft/smooth，其余Face/Edge/VertexPID、坐标、环拓扑、法线、变换、隐藏、图层、所有其他材质都在原生提交前严格不变。下部L0/L1顶面、两个L2partial顶面调浅矿物地面；两个L2partial及L3底面给浅木天花饰面；18桌只改直接水平顶Face为浅白面，不动支架/腿及桌面几何。L3顶Face已经225/224/216，保持；屋顶164Face已经浅木233/216/183，保持其材质，不能再误称木顶根本没浅色。只把158条真实二面夹角<5deg的内部木顶曲面接缝soft/smooth=true，边界/侧边不软化，不隐藏Edge，不动任何曲率/厚度/顶点。新材质用独立名称，别改共享KS原材质。Surface硬保护已在安全副本实际正例+7负例(移坐标/翻面/添边/越权材质/隐藏边/越权柔化/非法ID)提交前回滚验证，不能去掉它。

主机只读明暗实验说明大面积发黑也来自查看设置：原Dark45/Light80/UseSunfalse，同机位、同几何/材质改成Dark80/Light15/UseSunForAllShadingtrue、DisplayShadowsfalse就恢复浅木/浅地面且保留细节。第一组85/90会过曝，已拒绝；测试后均恢复原设置。这轮可在原生document中采用中性80/15方案，其他显示参数保持，单独记录这是查看明暗变化而非修好了材质/几何，不开发新渲染功能。保存下载重新打开需另验这四项设置。actual source4更宽真实截图outputs/renders/host-r18-source4-{lower-void-wide,lower-long-wide,lower-reverse-wide,upper-hall-wide}.png，以及host-r18-neutral-lighting-...图片/sidecar可读，均是原生捕获；不是源图，不要当源图事实。遮挡的房间关系可根据原八图和实模合理推断，不需再让所有者选择。

八源事实reconstruction_evidence.json不写本轮施工计划/时间戳，避免复核反复失效；本轮记录放notes/interior_finish_plan.json及qa。可复用主机验证的同18修订独立评审，先完成这一次协调修复，不要再花整轮重复拍同修订六视图。新19之后必须新六视图/全部8原图对应，加实际source4上下厅/细柱支承/新天花V近景交独立只读Critic。完整KEEP+surfaceguard+净空/支承/接头/材质/接缝原生检查，网站保存下载SU24重开；本轮完成仍非整项客户交付完成，继续严格重放和其他支持明确的缺项。
