# r9 原生可靠性继续修复：真实竞争恢复与精确新增保护

同八图、同项目、生产r9未改。上一轮[真实格栅结果](../2026-10-16-customer-readiness-r9-grating/README.md)保留；本轮不把安全工具通过冒充建模质量通过。

1. **实际SU2024 GUID竞争恢复PASS。** 在独立副本上仅写测试元数据并保存，真实GUID改变，使已排队的旧GUID读取确实失败。host核对相同路径、root、项目、版本后，只重试读取一次并成功；原生几何按明确精度契约未变。[原生结果](native/r9-guid-race-fixed/result.json)。初次注入用过大的纳秒整数导致原生RangeError，改存字符串后重测，初次日志保留；没有重跑几何writer。
2. **正式保护分派器的原生副本测试PASS。** graph模式只由host明确scope_contract开启，旧v2保持原契约。精确缺失叶组可创建，已有父组、兄弟、共享原型、文档松散几何全保护，巨大格栅也不截断；强制deepKEEP覆盖整个环廊、屋顶、楼板。[一次新增/清理、7类越界拒绝/全回滚、3类图检测](native/native-r9-production-graph-guard/result.json)。代码已接入，真正网站新增护栏仍待下一操作。
3. **声明数值契约的三阶段一致性PASS，原始全双精度严格FAIL仍保留。** 新KStudioNativeStableGeometry/1仅对无量纲法线和仿射线性系数取12位小数，顶点毫米坐标、平移、拓扑、材质及其他字段完全不舍入。完整原生图重新验证，所有引用与原型都参与哈希，原始图摘要与每一处量化调整保留；不是增加epsilon跳过比较，也不是仅比数量。[两种结果并列](native/r9-stable-native-delivery.json)。1e-9线性变化、镜像、材质、1e-16平移、1e-9毫米顶点变化的回归都仍拒绝。严格两次空白程序重放NOT_RUN。

下一处实际质量修复已核实：真实路径是FLOORS/L3，历史提及L3_DECK并不存在；顶层原生有两个48段小洞，中心(12000,10500,10800)/(22500,10500,10800)mm，半径1100mm。现有42段护栏只围绕大螺旋梯洞。源图04确有细白圆筒网护栏；不移动任何洞口，只准备在CIRCULATION_INTERNAL/SMALL_CIRCULAR_VOID_GUARDS这一准确缺失叶组新增两处护栏。[登记](native/r10-small-guards-preparation/registration.json)、[计划与校验](native/r10-small-guards-preparation/validation.json)。护栏高度/网距/杆径为估计，不是规范或结构认证；此报告尚未在网站执行。

不调用付费API，Builder0，外层用量未知null，未设置流量上限。独立客户安装/服务商推理、源图整体质量、重放仍未通过，客户NOT_READY。Codex继续，非交付结案。
