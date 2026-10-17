# 主体与附属体对应表
唯一来源：inputs/reference/2fc62f9b95-villa-single-view.png；已查看完整单幅正面+左侧斜视，无第二独立角度。以下为待建路径，均相对宿主验证的所属根。
| ID | 可见实体/关系 | 比例锚定与不确定性 | 目标路径 | 状态 |
|---|---|---|---|---|
| main | 两层白色盒体，正面三组洞、左侧两窄窗 | 宽8米深7米层高3米为用户尺度；墙厚估200 | SHELL_FRONT / SHELL_LEFT / SHELL_REAR / SHELL_RIGHT | 未建 |
| floors | 层面与二层门槛、阳台齐平 | z=0/3000；内部楼板按外壳需要推定，楼梯不做 | SLAB_GROUND / SLAB_LEVEL_2 | 未建 |
| roof | 主盒体连续薄压顶，无可见屋面设备 | z=6000；厚180估算，顶面未知 | ROOF_FLAT / ROOF_CAP | 未建 |
| balcony | 正面二层悬挑白板；无柱，前栏及左回折 | 接近全宽，估宽7200挑1200厚300 | BALCONY_SLAB / BALCONY_GUARD_FRONT / BALCONY_GUARD_LEFT / BALCONY_GUARD_RIGHT | 未建；右回折推定 |
| screen | 正面最右侧通高木条带 | 约主体九分之一宽；根数初估12 | SCREEN_FRONT_RIGHT | 未建 |
| plinth | 外墙底部浅灰窄基脚 | 非新楼层，精确高度未知 | FINISH_PLINTH | 未建 |

轮廓优先检查：左前竖角、两段屋顶边、阳台左右端及板底、木带顶底。图中没有已证实的附属侧翼或其他屋顶。水平边在图像中的倾斜由透视解释。
原生面挤出与组件为拟用方法；可调用 SAIE 签名未核验，ADAI 禁用。无几何、无源图匹配验收。


Revision 3 built readback: all listed primary/attached building volumes exist under their named paths (19 assemblies). Balcony x600..7350, top3000, bottom2550; upper doors heads5100; left windows850x1600. No stairs/interior/site. Roof/back/right remain inferred. See qa/visual_review.json for current independent visual verdict.
