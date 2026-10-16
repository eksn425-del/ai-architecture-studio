# 当前外部连续补建卡｜r12→交通连接｜2026-10-16

同八整图、原项目/root20606，原r4/r10/r12版本不覆盖。所有者授权完成外部并合理推断未见细节，不等待旧草图选择。围护四组在r11已提交、r12已修正西端中层门扇：40上厅窗跨及16真实敞开入口；已完成保护、保存下载重开，构造细分为源图约束估计，非测绘。继续外部交通，后续细网/长侧门窗/轻框，不是补一处后结案。

当前准确范围见local-edit-scope.json/exterior-circulation-registration.json：L2/L3两个实际平台容器、远端三层GALLERY_Z*_SIDE3板件，新增CIRCULATION_INTERNAL/END_STAIR_COMPLETION与CIRCULATION_EXTERNAL/REMOTE_END_EDGE_GUARDS。保持目标容器PID；已有72踏步、坡道本体、屋顶、楼板、刚补围护和其他构件均保护。不要把范围扩大到父组。

把外挑上层余段收回矩形外玻璃内，同时保留当前坡道端和环廊连接的内侧平段。端梯实际世界变换和每踏步顶面须读回，补离散支承/侧防护/落脚平台与地面接顺；三块远端格栅仅局部留需要的梯口/支承连接，保持槽外透空格栅与通路，不用实板替代。接入r12远端入口y7600..9600和上层15200..17400，平台要有真实支承/净空。未见细部参照原图5/7与相邻细白构造推断，不复制坡道端，不删拉索换取画面干净。

上一步进度程序只列根目录造成深层楼板/屋顶假缺失，真实14目标原生读回都存在；新代码补准确路径批量读取。历史错误收据保留。built只表示实际几何存在，不能当视觉通过。按当前八图与真实几何执行，勿因旧pending/needs_fix再重建受保护结构。

执行后做当前六视图、八原图及端梯/梯口/平台细部独立复核，原生通路/净空/支承控制、作用域审计、保存下载重开。本轮同时完成批准范围内所有长环廊、坡道两侧、平台及槽边细白网护栏；准确33目标是一个协调的外部交通系统，不要只补一个栏杆后停止。先验证一个真实细网组件，使用重复实例，避免每根丝都创建全新定义而超出原生物理实体上限。保留真实门口/栏杆开口、坡道当前世界方向，按实际局部/世界矩阵构造，不二次镜像。提交时使用完整登记的协调范围，所有已有目标容器PID保持。后续为实墙/玻璃、不透明带、长侧入口和进退关系。


Host native coordinate proof: notes/native-circulation-coordinate-readback.json now contains actual31target matrices/world bounds/post bounds and72protected end tread bounds at r12. Matrices are column-major native inches; bounds explicitlymm. Preserve actual mirrored ramp-rail transforms; map world through target inverse rather than building world coordinates inside mirrored local groups. No geometry changed by this probe.
