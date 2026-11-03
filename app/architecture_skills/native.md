# 原生语义建模
原生文件工具的当前工作目录已经是本项目 runtime/agent_workspace；脚本路径写 scripts/文件名.rb，笔记写 notes/文件名.md，不要再加 agent_workspace/ 前缀。读取失败先列出实际目录并复用已存在文件，不凭猜测反复换路径。
只通过当前宿主列出的 SketchUp 写入工具提交模型。命名组/组件可选择、可编辑；stable ASCII 直接部件，如 Slabs、Walls、Glazing、Frames、Balconies、Braces、Entrance、Roof。Roof 保留独立顶层部件。
完整原生模式提供文件、脚本和受保护的 sketchup_run_workspace_ruby 时，可在项目 scripts/ 中编写可复现的 Ruby，表达真实踏步、曲线、构件定义与实例；使用宿主注入的 root/model、script_id=harness_building 和 .mm 单位。简化 typed 工具只是适合简单几何的选项，不能用斜盒代替要求明确的楼梯踏步。没有列出脚本写入工具的模式才只使用现有 typed 工具。终端可准备与检查项目脚本，不得绕过宿主直接连接 SU、操作其他文档或另启第二个模型写入器。
先 inspect/model_state 验证当前模型，再分系统构建：主要楼板/核心与围护 → 关键构架/负空间 → 立面与阳台 → 屋顶/入口。每次一到几个系统，避免超大回复截断。查看工具结果，失败不能当成功。根据错误修正参数，不重建已正确的整栋建筑。
重复定义使用 repeat/step，变形部件独立。模型内容不应包含未经请求的异地项目、复杂人物/车辆或巨量景观。场地只补足用户需求，建筑主体质量优先。
Ruby 样板先核对面法线与有符号高度：SketchUp 在地面上新建的水平面可能朝下，正 pushpull 距离可能向地下生成。向上拉伸前检查 face.normal.z，必要时 reverse!；倾斜构件按预期局部方向检查。第一件构件的实际 min/max Z 和高度必须与层表吻合，再复制。发生方向错误时只修对应已命名部件，使用 edit 与 exact allowed_mutation_paths，不用全楼 replace 重试。
局部重做内容时，clear_owned_contents.call(['Part']) 保留原容器并返回回执；随后找到原同名组，在它的 entities 中重建。不得再次向 root 添加同名容器，也不得删除原容器改变 PID。新建尚不存在的部件时才 add_group。不同系统的脚本应各自完整定义所需函数，不依赖前一 Ruby eval 的局部变量或临时方法。
保持既有模型文件、视图风格、材质和用户几何。宿主事务/模型身份/KEEP 校验是必需条件，不允许绕过。
