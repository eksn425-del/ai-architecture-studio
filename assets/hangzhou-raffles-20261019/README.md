# 杭州来福士：街景与江景 Blender 素材包

本包在已有 R3 最终双塔/裙房模型基础上，新增城市街景与滨江环境，供 K Studio 宣传素材制作和本地 Codex 编辑使用。

## 打开和使用

- `Hangzhou-Raffles-Environment-Final.blend`：主文件，Blender 4.3.2 制作，原生可编辑，材质全部程序化，无外链贴图。
- `01-hero-aerial.png`：城市到江面的鸟瞰主视角，1920×1440。
- `02-street-arrival.png`：街道到双塔的接近视角，1920×1440。
- `03-river-promenade.png`：从江面方向回看城市的场景视角，1920×1440。
- `04-atrium-skylight.png`：新增加的钢格构玻璃采光顶近景，1920×1440。
- 相机 `04 ANIMATION | 250 frame orbit`：250 帧、25 fps 的可编辑镜头运动，未输出完整视频。
- `source-architecture.zip`：未改动的原始 R3 `.blend` 文件，用于从基线重新生成；不包含用户参考照片。
- `build_environment.py`、`finalize_scene.py`、`refine_atrium.py`、`refine_far_bank.py`、`render_saved_scene.py`：完整场景构建、打磨和重新渲染脚本。
- `REFERENCES_AND_CONTEXT.md`：参考出处与城市空间假设。
- `QA_FINAL.json`、`MANIFEST.json`：本次实际文件、场景检查和哈希记录。

本地 Codex 建议先读取本文件，然后打开主 `.blend`。不要再用源模型覆盖环境版本。可直接使用四张图做剪辑，也可调整相机重新渲染。

## 重建

解压 `source-architecture.zip` 后，在本目录运行（将 blender 换成你本机 Blender 可执行文件路径）：

```bash
blender -b R3-final-Hangzhou-Raffles.blend -t 8 --python build_environment.py -- --out . --preview
blender -b Hangzhou-Raffles-Environment.blend -t 8 --python finalize_scene.py -- --preview
blender -b Hangzhou-Raffles-Environment-Final.blend -t 8 --python render_saved_scene.py
```

只重新渲染最终模型：

```bash
blender -b Hangzhou-Raffles-Environment-Final.blend -t 8 --python render_saved_scene.py
```

## 增加内容

道路、车道线、斑马线、人行道、广场种植、街树、城市绿地、长椅、路灯、路桩、简化车辆与行人、周边建筑体量和幕墙分格、江面、滨江步道/台阶及对岸天际线。原有双塔/裙房网格保留，材质和展示光照调整。根据业主反馈及 UNStudio 官方实景补上中央中庭的玻璃采光顶、钢格构、内衬及楼层边缘；对岸增加分层楼群、沿江道路、步道及绿化。构造尺寸与室内层数仍为示意推定。

## 使用边界

这是基于既有模型的建筑可视化素材，不是杭州来福士实测模型。双塔本体继承旧版本的精度限制；道路、周边建筑、绿化和江岸为有参考依据的示意补全，并未使用测绘/GIS定位。

本场景将 +Y 方向作为画面中的滨江方向；它不是实测真北。江岸距模型原点约 560 米，是为构图压缩的艺术假设，不能解释成真实距离。参考资料中的 750–1000 米也是未测量的估计，不能作为设计依据。

这些成果通过云端 Blender 脚本实际生成并渲染。本轮属于宣传场景后期制作，不构成 K Studio 网站自主建模或自然语言全流程通过的证明。宣传中不要把推测环境表述为实景扫描，也不要宣称模型一比一复原。

第三方网页照片仅提供链接，未打包分发。品牌名称和建筑设计归各自权利人；本包不代表获得建筑师或项目业主背书。未附加任何开源许可或第三方素材再许可承诺。
