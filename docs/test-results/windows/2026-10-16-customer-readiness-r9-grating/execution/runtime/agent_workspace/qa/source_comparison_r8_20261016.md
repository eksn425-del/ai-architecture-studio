# 第8版只读复核，2026-10-16

本轮未运行几何写入、未改构件。原始八张拼图的所有分面均直接查看。当前同一独立模型根20606、版本8。新拍六个标准视角、10个原图对应视角及四处坡道转接的双向近景，路径记录在 readonly_r8_audit_20261016.json。

| 原图 | 当前对照结果与限制 |
|---|---|
| 1 上下短端外观/模型 | 上两段已在固定短端玻璃内侧，三段上升方向一致；下段外置未变。平台比上一版缩小，精确外挑量和转接尺寸仍属估值。护栏粗横杆明显不同于原图细网。 |
| 2 鸟瞰/斜视模型 | 长条体量、内退上厅与凹曲屋顶可识别。端部上两段收回，平台仍有侧向外挑；尚不能认定与原图轮廓完全一致。 |
| 3 入口/廊下 | 原图为格栅板与离散细梁，当前外廊为不透空平板，视觉偏厚重；下层内退柱线保留。 |
| 4 顶厅/双层高工作区 | 曲面木顶保留；当前地板深木色、空场及简化家具不同于浅色丰富室内。圆洞缺圆筒细网护栏；螺旋梯踏步及支承、护栏不完整。当前低平连续顶板未还原原图双层高大厅。 |
| 5 剖透视/底层平面 | 层间大挑空、局部楼板、房间分隔与交通细节未充分还原。当前未剖切外观不能充当剖面一致证明；近地室内图补充证明空间差异。 |
| 6 四层构造分解 | 混凝土框架、木质上厅、外玻璃缓冲层可区分；当前不作构造拆解，细杆、板、格栅和围护关系仍简化。未据图中文字执行任何操作。 |
| 7 三层平面 | 原图局部中间层、房间边界、圆洞和环廊可见；当前屋顶遮挡俯视，不能完整核对平面。已结合室内、构件路径及源剖面记录不一致，不把遮挡解释为缺失。 |
| 8 气候/结构剖面 | 屋顶右高左低且中部下垂的方向保留；精确曲率、净高和局部楼板关系未达到原图一致证明，气候箭头不建成实体。 |

## 穿板、挡路与误改

上两段原生范围 X=-3900..-1700，固定短端玻璃 X=-4000，主体确在玻璃后；Y=-3000..23000，端点标高依次3600/7200/10800。第8版提交时沿两段中心线每1m检查2.2m头顶范围通过；同槽上下坡道理论底面净距3440mm。这仅证明已检查样本，不是人体扫掠或完整路线合格。

新双向近景中，朝内侧转接方向可见平段及环廊；朝外看见短端玻璃，不能仅据该远端围护就断言转弯必被玻璃阻挡。环廊有斜拉杆、边框、栏杆等，整体通行仍待独立复核结论；没有执行新碰撞探测写入。不得标为全部走通。

上次46路径保护与15路径修改范围核查通过。此次重查相同46路径的标识、子组数和包围盒，对比结果另存JSON；历史深几何保护与本次简单读回区别记录。未重新运算全模型深几何哈希。

## 下载边界

软件记录已有第8版 agent-checkpoint-df810517c351.skp，908100字节；本轮核对其SHA256与软件保存记录一致。native_delivery_checkpoint.json 状态为 UNVERIFIED_NATIVE_REOPEN：保存成功不等于下载重开后的可编辑几何一致。当前工具未提供原生保存/重开接口，不伪造新保存或重开成功。

独立复核：等待本轮当前图像结果；完成后追加。


本轮独立只读复核已返回：NEEDS_FIX。以下为独立观察，不视为写入指令：

- Repeated diagonal rods visibly terminate in circulation space below the soffit, with exposed ends above the deck. SOURCE sections and model photographs show diagonals continuing between structural attachment points; these are not intended shadow gaps.

- Heavy stacked horizontal rails and opaque grey circulation decks dominate CURRENT. SOURCE 1–3 show slender pale frames, fine mesh guards and visibly permeable grating with exposed supporting beams. The current assembly obscures the glazing and changes the building’s defining lightness.

- A circular floor opening in the foreground has no raised guard, while SOURCE 4 upper shows prominent cylindrical mesh guards around the visible circular openings. The existing guarded stair opening does not resolve this separate exposed opening.

138项标识/子组数/包围盒比较全部一致，覆盖46个受保护路径；未发现这些受保护部分误改。当前仍为第8版，无几何写入。
