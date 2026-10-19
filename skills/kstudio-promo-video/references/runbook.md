# 快速复用

```powershell
python <skill>/scripts/promo.py init <new-job>
# 填入job.json，本地media/、audio/中放自己的素材
python <skill>/scripts/promo.py audit <new-job>/job.json
python <skill>/scripts/promo.py prepare <new-job>/job.json
# 可选：prepare ... --captions <已核实的captions.srt或JSON>
# 首次在该film目录安装依赖：npm install；遵守所用Remotion许可
python <skill>/scripts/promo.py render <new-job>/job.json
python <skill>/scripts/promo.py verify <new-job>/job.json
```

骨架是v8的60秒风格，不是所有项目的唯一结构。用户改时长/画幅先改时间线和QA。缺素材不隐式复用旧片。

声音参数、原生窗口录屏、效果/分析/封面提示词及性能处理见[关键工艺](production-details.md)。

1. **索引/文案**：文件角色、案例、来源、授权、SHA、时长/尺寸/入点；核对所有原参考。六段自然口播，每镜一个信息。时间不足先缩CTA、重复品牌和回闪，不挤压参考/生成/修改。
2. **声音**：本次本人授权本地VoxCPM2，干声→裁无声→atempo保音高→压缩与响度→独立BGM避让→短SFX→限幅。新的真实录音够好就直接剪，不强制生成口型。脚本只处理已提供干声，不运行TTS/付费API/下载权重。试听后再整片。
3. **同步**：优先最终配音的真实SRT/JSON，支持WhisperX等工具导出的时间段。未提供则approximate句子字幕并听辨，不宣称逐字。音轨有偏移必须先实测；v8的+2048采样不是所有片子应固定提前的值。
4. **真实拍摄**：按素材文档拍网页/原生SU；模型问题先诊断/按授权处理再录。同相机前后对比，后期图独立标注。人物、原生空间、参考优先，字卡/粒子服从主信息。
5. **装配**：prepare复制到新film/public稳定别名，保留源文件。人物说明、案例标题、参考数量、片段入点/倍速可配置。先看楼梯、材质、B参考、工作区四帧，再导出。分镜时长仍沿用v8，可人工改模板。
6. **双版本**：同SCENES/bgms开关出带乐/无乐，均保留人声/SFX。视频流不同就保留原无乐、无损封装统一视频并验证原音轨未变；不要重新编码再谎称相同。v8双渲染已一致，无需此处理。
7. **QA**：ffprobe尺寸/fps/帧数，完整解码，黑帧、响度、削波，参考去重、素材时长，双版视频/音轨。实际看连续地面、楼梯、参考→网页→模型；试听人声/BGM、字幕落点。不能以无削波推出音画卡点。声称≤3帧需测源峰值与成片。独立审查有界修必须项、保留未验证项。
8. **交付**：新目录存主片/无乐/源工程/本地索引/QA/SHA/提示词。工作台/剪映工程只有实际做出才称可用。方法包不含媒体。

Windows聊天文件夹/ZIP打不开：确认文件存在和ZIP完整性，复制明确桌面子目录，按需做只绑定127.0.0.1且仅服务交付目录的HTTP页。浏览器实际下载与HEAD状态分别记录，连接中断不能掩盖为成功。原文件不删。
