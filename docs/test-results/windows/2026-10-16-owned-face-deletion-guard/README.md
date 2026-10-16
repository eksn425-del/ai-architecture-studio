# 修复带叹号删除方法漏判，提供限定叶组删面入口

实际第17版源码中的hole.erase!暴露旧正则末尾word-boundary不能匹配以!结尾的方法；静态复现root.erase!、face.erase!、clear!意外接受，erase_entities已拒绝。第17版原生全图范围保护实际通过，不把源码过滤器当Ruby沙盒。修复为明确方法名后不接标识字符，保留历史成功源码与SHA，不能改写旧证据或把严格重放写成通过。

注入erase_owned_faces.call(准确路径,[face.persistent_id])，只允许批准叶直接拥有的实际Face，根路径/外部面/非Face/重复或空ID拒绝；共享定义复用完整38出现位置审批与原生proof。完整范围fence和原生交付collector保持，不放宽父组。88相关Python回归通过，另有实际SU2024[正例与六负例](native/actual-native-results3.json)，每个负例全图回滚相等。生产17三次恢复均验证一致，原案例未改，测试没有建新客户模型或调用推理。

两次真实原生fixture失败全保留：[第一次](native/actual-failure.json)、[第二次](native/actual-failure2.json)。从已有洞的边界重新add_face不能假定得到正确填洞面，第一次删除返回面后目标几何不同；第二次实际面积前置检查先拒绝。第三次在批准共享叶内新建外面/内面并核对内面面积，再通过限定helper删除，得到正确真孔，完整几何/材料SHA与原模型相同；该叶内部FacePID重建，不能把几何SHA相等说成所有Face身份相同。原生产文件始终未写入。

此报告只证明原生安全方法，真实网站对新helper的使用NOT_RUN，源图保真未评估；真实第17版质量见[外檐报告](../2026-10-16-customer-readiness-r17-outer-vents/README.md)。当前仍继续补缺失转角竖框和其他支持明确的源图问题。
