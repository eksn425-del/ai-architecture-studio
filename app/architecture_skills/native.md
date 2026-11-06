# 原生语义建模
新建筑必须采用真实分段搭建：先只提交楼板、柱和必要核心的骨架，读回层高和整体比例，再做围护/开口、一个立面样板、验证后的重复、楼梯栏杆与收尾。按该建筑实际逻辑调整次序，不能第一笔就把所有系统做完。每个阶段独立提交保存、观察原生变化，主要阶段取一张斜视图；不靠整楼显隐、不插入假进度或人为等待。写入工具 construction_stage 使用 structure/enclosure/sample/repetition/circulation/finish/correction；它只是阶段标签，不证明系统完工。用户已批准整体计划时连续完成各阶段，不每阶段反复要求批准。继续时先核对当前原生 revision 和 runtime/construction_steps.jsonl 的成功记录，已提交阶段不得重新执行；未知提交先恢复核对。
原生文件工具的当前工作目录已经是本项目 runtime/agent_workspace；脚本路径写 scripts/文件名.rb，笔记写 notes/文件名.md，不要再加 agent_workspace/ 前缀。读取失败先列出实际目录并复用已存在文件，不凭猜测反复换路径。
只通过当前宿主列出的 SketchUp 写入工具提交模型。命名组/组件可选择、可编辑；stable ASCII 直接部件，如 Slabs、Walls、Glazing、Frames、Balconies、Braces、Entrance、Roof。Roof 保留独立顶层部件。
完整原生模式提供文件、脚本和受保护的 sketchup_run_workspace_ruby 时，可在项目 scripts/ 中编写可复现的 Ruby，表达真实踏步、曲线、构件定义与实例；使用宿主注入的 root/model、script_id=harness_building 和 .mm 单位。简化 typed 工具只是适合简单几何的选项，不能用斜盒代替要求明确的楼梯踏步。没有列出脚本写入工具的模式才只使用现有 typed 工具。终端可准备与检查项目脚本，不得绕过宿主直接连接 SU、操作其他文档或另启第二个模型写入器。
先 inspect/model_state 验证当前模型，再分系统构建：主要楼板/核心与围护 → 关键构架/负空间 → 立面与阳台 → 屋顶/入口。每次一到几个系统，避免超大回复截断。查看工具结果，失败不能当成功。根据错误修正参数，不重建已正确的整栋建筑。
重复定义使用 repeat/step，变形部件独立。模型内容不应包含未经请求的异地项目、复杂人物/车辆或巨量景观。场地只补足用户需求，建筑主体质量优先。
Ruby 样板先核对面法线与有符号高度：SketchUp 在地面上新建的水平面可能朝下，正 pushpull 距离可能向地下生成。向上拉伸前检查 face.normal.z，必要时 reverse!；倾斜构件按预期局部方向检查。第一件构件的实际 min/max Z 和高度必须与层表吻合，再复制。发生方向错误时只修对应已命名部件，使用 edit 与 exact allowed_mutation_paths，不用全楼 replace 重试。
局部重做内容时，clear_owned_contents.call(['Part']) 保留原容器并返回回执；随后找到原同名组，在它的 entities 中重建。不得再次向 root 添加同名容器，也不得删除原容器改变 PID。新建尚不存在的部件时才 add_group。不同系统的脚本应各自完整定义所需函数，不依赖前一 Ruby eval 的局部变量或临时方法。
Ruby 的 `def` 不会捕获宿主局部变量。`root`、`model`、`clear_owned_contents` 是注入的局部变量，并非全局方法；不能在 `def helper` 内直接引用它们。优先使用捕获当前绑定的 lambda；若用 def，必须把需要的对象作为参数传入。不要使用 class/module 包装、反射或重新获取 active_model。例：`find_part = lambda { |name| root.entities.grep(Sketchup::Group).find { |g| g.name == name } }`，随后 `part = find_part.call('Frames')`。清理授权内容应在顶层调用 `clear_owned_contents.call(['Frames'])` 后复用 part，而不是隐藏在不能访问该局部变量的方法内。
所有阶段均使用同一个 `script_id=harness_building`。第一阶段成功返回 root/revision 后，后续阶段必须 `update_mode=edit` 并列出精确 `allowed_mutation_paths`；不设置 `allow_full_rebuild`，也不重新执行第一阶段。斜梁/扶手先在自身局部坐标建模，组合变换为“局部旋转后平移到端点”；用实际两个端点回读检查，不把已经在世界坐标的点再次整体平移。示例和计划不是实测结果，仍需检查原生工具回执。
保持既有模型文件、视图风格、材质和用户几何。宿主事务/模型身份/KEEP 校验是必需条件，不允许绕过。
