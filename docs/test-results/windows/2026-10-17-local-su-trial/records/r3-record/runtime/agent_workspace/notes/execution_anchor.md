# 执行依据
2026-10-17：已直接查看唯一原图，已获用户建模批准。当前模型 blank-disposable-20261017-114606，写入前实体数 0。
原图为正面及左侧斜视：两层连续白色方盒、平屋顶薄压顶；首层一组宽玻璃门、二层两组门；左侧每层一窄竖窗；阳台外挑且左边短回折，右端通高木条。无可见楼梯、其他附楼或坡屋顶。
坐标 x=0..8000，前立面 y=0，进深 y=0..7000，层高 3000。门窗是穿墙开口；楼板与阳台顶在 z=3000，阳台不加支柱。未见背面/右侧按确认的封闭墙；不加室内隔墙、楼梯、家具、环境。
当前工具已提供可核验 SAIE 适配器，替代规划时“未验证签名”的判断：墙用 saie.wall，开洞墙用 saie.wall_with_openings。屋顶、阳台、门框、玻璃及木条用 kstudio.custom_owned_ruby，因为现有适配器仅支持直墙及矩形洞口，不提供这些型材系统。ADAI 禁用。
先生成连续围护、楼板、平屋顶和阳台实体，后验证一个双扇门型，再生成尺寸变体、木条、栏板和饰面；全部在同一持久脚本、同一 owned root 内。
尺寸沿用批准计划：阳台 7200×1200×300，栏高1100，木条12根。单图不能测定进深、背面及精确洞口尺寸；不把推断当成测量。
`n复核修正：阳台右端由 x7800 收至7350，右回折同步内移450；左窗以原中心4300保持上下对齐，改850×1600，单块主玻璃。保留正面三门、木格栅及压顶。外铺地被复核列出，但用户已明确不做周边环境，按原范围省略。局部左墙使用原生面环开洞挤出：现有 SAIE 适配器只能在根下生成新墙，不能在既有目标容器内替换且保留该容器ID，因此本次局部修正改用 custom_owned_ruby。

Revision3: upper front heads lowered to5100; balcony fascia deepened downward to450. Threshold/floor remains3000 under confirmed storey dimension and flush-door relationship. Critic suggestion to raise floor is not adopted because it conflicts with this explicit anchor. Root/target IDs retained, unrelated geometry protected.

Final read-only handoff: committed model remains revision3. Proposed fourth write was rejected by host mutation budget before any model operation; script restored to revision3 content. Remaining in-scope visual issue: 150mm wall band between ground door head2400 and balcony underside2550 appears tighter than source. Proposed future scoped change: head2250 would give300mm; not executed. Current six-view and source-angle independent review are revision3. Do not rerun cumulative patch transformations without revision checks.
