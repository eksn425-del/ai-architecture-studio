# Dream Coffee 原生编辑与空白重放补验：PARTIAL

此前[受保护修复报告](../2026-10-11-dream-coffee-protected-repair/README.md)锁屏阻塞后，用户解锁，本批补齐真实生命周期测试。没有新Builder或模型API调用，没有修改正式r4几何。

**原生编辑 PASS**：网页下载字节匹配的专用副本在SU2024打开，116组指纹与正式r4一致；鼠标进入根组选中PLANTERS，通过原生移动工具移动，Ctrl+S保存，Ctrl+O原生重新打开。只有PLANTERS变化，其余115组一致，保存前与重开后递归指纹完全一致。[实际重开模型截图](native/saved-reopen.png)、[凭据](model/native-reopen.json)。中文SU快捷键M实际为卷尺，第一次尝试没有移动，随后改用真实Move工具栏，失败过程保留。

**全新空白重放 FAIL**：读回初始entity_count=0，持久baseline受守护写入，生成116组/新根PID19/r1，写后验证成功，采集真实六方向：[front](views/front.png)、[rear](views/rear.png)、[left](views/left.png)、[right](views/right.png)、[roof](views/roof.png)、[oblique](views/oblique.png)。但三组 FRONT_SLOPED_GLAZING、FRONT_STORE_FRONT_GLAZING、UPPER_GLASS_PAVILION 的严格递归几何/面材质指纹不同；面/边/实例数相同，原因未确定，不能称重放完全一致。[实际receipt与差异](model/baseline-replay.json)。本批source-perspective文件明确为该新模型oblique，不冒称另一次源角度Critic；独立视觉复审NOT_RUN，原r4视觉PARTIAL仍有效。

## 外部能力吸收结果

重放实际方法以[账本](model/oss-method-ledger.json)与[采用读回](model/oss-method-adoption.json)为准。这是既有baseline重放，不把它当作新增雨棚ADAI修复成功，也不把helper执行当视觉PASS。

原生切换遇到保存提示：宿主定时open超时后仍有排队对话，人工工具清理实际提示，再用Ctrl+O打开专用空白。已恢复原项目state/strategy/progress并读回正式模型为r4；需修复宿主切换超时取消/串行化，避免残留open请求。无原图、私人SKP、APIKey或个人路径提交。新的SHA256清单独立生成，前批证据未改。

下一轮：对三组玻璃系统逐面定位baseline差异，修正已提交脚本的持久一致性；修复原生切换保存提示与超时遗留操作。再在正式r4白名单内定向修雨棚/木板，保留原110组，完成源图独立Critic，不全局重建。
