# 同八张原图：原版 Codex 实际局部对照（2026-10-14）

总体 PARTIAL：原版一次屋顶方向局部修改 PASS，119 个保护路径深层几何/材质和 PID 不变，原生保存与两份安全副本重开 PASS；整栋源图相似度仍 FAIL。

所有者明确允许后，只给本次进程的单个 guarded MCP 工具设置 approve。CLI 仍 workspace-write、approval_policy never，原始写工具禁用，既有 ProjectRuby 身份/范围/KEEP/一次写入限制保持。八张原图 SHA 和顺序及 r2 起点已实际核对，网站 r4、原始 r1 和私人资源先备份。

原版输入与网站 r2→r3 相同：『从坡道这一端看，屋顶还是左边偏高。请按原图改成右边高、左边低，保留曲面，坡道和其他部分别动。』实际 gpt-6.1-sol / medium，没有换模型、重建整栋或付费 API。

实际完整文档几何指纹为 `2f9c218c4a15dc20ad39bac7fe8cdf90234847f880a135db0e7efd5f95ce8719`，与网站 r3 **完全相同**。两边都反射既有屋顶并对随附 TENSION_BRACING 做对应局部转换；不是全楼翻转。不能据此说原版提高了空间理解或整栋源图质量。

成功 CLI 耗时393951ms，input1265869 / output7282，cached1171968；网站原方向修改实际536656ms，Builder input3431345 / output7112，52聚合工具调用，另有两次 Critic input131156 / output1437。两者上下文、工具包装、Critic调用位置不同，时间和 Token 是本次观测值，不能解释为公平的模型速度/价格排名。

保留前两次失败：第一次78146ms账户配额报错，无最终Token记录；第二次495262ms只读MCP超时，无写入，input982531 / output1649。查明子进程继承 MCP 会话 stdin；stdout改文件的假设测试失败，最终仅加 stdin=DEVNULL，真实 SDK inspect1.33s返回。没有修改模型权限或产品几何后端。

仓库历史开发 AGENTS 还污染了 CLI 工作目录，触发无关 Git/CURRENT 查找。隔离根标记后实际原版执行正常；产品 Native Agent 已加入 .kstudio-agent-root/project_root_markers，沙箱/授权/联网/写目录不变。436 passed、2 skipped。网站新边界真实复测 NOT_RUN，不可拿代码测试当建模质量 PASS。

独立只读 Sol Medium Critic 91422ms、input47588 / output874、0工具，NEEDS_FIX YES：曲顶两侧斜撑成为厚实三角带，遮住通道，与原图细拉索不符；未剖切截图不能证明室内洞口或真实连接。保留曲顶轮廓和折返坡道总体组织，不应整栋重试。下一步应先只读核对同项目 r4 的斜撑拓扑/截面，再制定最小局部修复，不以原版成功替代网站验收。

原版交付候选是真实保存副本，原生 guarded lifecycle API 打开；不是浏览器下载。审计脚本字段 clean_download 在本对照中仅指该干净候选；原版浏览器下载、单独鼠标编辑和最终严格空白 replay NOT_RUN。网站 r4 的实际浏览器下载与 native reopen 已由上一报告证明。

六张图与 sidecar 均为本次真实控制 r3。私人八张图片、SKP、原始执行日志、账号及密钥未上传。保留完整失败及实际用量；未知 Token 为 null，所有本地成本上限为0，未重置历史用量。

交接时网站r4原文件和状态保留，但活跃SketchUp仍为控制候选r3。跨文件夹恢复被原生守卫拒绝，前台切换失败后未执行路径输入；网站r4活跃文档恢复PENDING。后续需原生对话框稳定打开、深层SHA核对后才更新GUID。
