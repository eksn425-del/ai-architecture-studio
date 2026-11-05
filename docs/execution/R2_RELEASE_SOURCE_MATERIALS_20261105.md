# 2026-11-05：对应源码与 Microsoft 分发材料

此次对实际 build04 依赖做工程追溯，没有修改旧工件、购买许可、执行下载的源码或宣布公开分发合法性。所有归档放在项目 E 盘 `jobs/kstudio-r2-live-20261105/source-materials/`；归档 URL、实际字节数及 SHA256 在 `archives/*manifest.json`。`license-source-kit/` 和 `windows-redistribution-matched.json` 保存 Microsoft 精确发行包的来源和匹配证据。源码材料需要与获准二进制一起通过实际发布渠道提供；本机保存不是已经履行公开源码提供义务。

## 已实际完成

| 实际组件 | 对应材料与验证 |
| --- | --- |
| LibreOffice Kit 0.1.5 / LibreOffice 26.8.0.3 | 从随包 `prebuilds.json` 取得 core commit `bce0998afefdbc355585ca324285661a2170ba77`；复制96个源码/补丁/构建脚本/许可材料，存在上游 manifest 摘要的逐项一致。取得该 commit 完整 core 归档353,665,929字节，SHA256 `c046d25748ff3cd0c31e226f45ba47eb328aeba3f8d4d844b9d9db78cf1f85eb`。 |
| sharp / @img/sharp-win32-x64 0.35.5 | 从准确 npm 版本的 gitHead 取得 `51a990faa26ade5586a4934ac9673c98d8893326`；完整源码41,802,569字节，SHA256 `d600bcbdd550ea096a384391a474907e6aa8138f97ea472bf5228b07ae75f779`。 |
| libvips 8.18.7 Windows | 实际 `libvips-42.dll` 与上游 `vips-dev-x64-web-8.18.7-static.zip` 对应文件逐字节相同，SHA256 `06dab07cc386748513337a31672b1d5269fbc770a14ff403080575665bf0813f`。取 build-win64-mxe v8.18.7 构建脚本、补丁及基线 MXE recipes，不拿当前 main 的较新依赖冒充。 |
| LGPL/MPL 库 | vips8.18.7、glib2.90.0、pango1.58.2、cairo1.18.6、librsvg2.63.2、fribidi1.0.17、libexif0.6.26、libheif1.23.5、proxy-libintl0.5 九个源码包全部通过对应上游构建 recipe/wrap 的 SHA256；原始许可证/版权通知另行提取保留。 |
| WebView2 1.0.3856.49 | 官方 NuGet 包9,025,251字节。实际5个 .NET/Loader DLL 全部精确匹配包内文件；保留该版本原始 LICENSE、NOTICE、nuspec，不能仅引用最新版网页。该 SDK 证据不代替终端 WebView2 Runtime 安装验证。 |
| ConPTY 1.25.260303002-preview | 官方 NuGet 包1,728,475字节，实际8个 ConPTY/OpenConsole 文件全部匹配。nuspec 明确 MIT；保留官方许可页面及 Microsoft 版权声明，不把 node-pty 父包许可当厂商许可。 |
| Microsoft PE 检查 | 60个真实文件的版本、原文件名、SHA256、证书/时间戳信息已收集，当前 Windows 验证签名全部 Valid；这只证明签名检查结果。44个 UCRT/API-set 文件是10.0.26100.4654；两个 VC runtime 是14.38.33126.1，NumPy 的 MSVCP 是14.40.33810.0。 |
| 无关示例 | 新构建仅从新 `harness-stage` 删除 fast-uri3.1.9/benchmark 的6个非运行文件，记录原 SHA；原依赖和旧工件不动。实际 Node 执行 URI parse 通过；全部 Harness skill/template保留。版本变化、导出变化、重解析点、越界目标必须停止删减重新审核。 |

## 尚不能宣布完成的准确边界

1. LibreOffice Kit 公开仓库 `master` 当前 commit `b19bb73c74ed893b8a5d1716d32df32a113ed31b` 的 entry/package.json 是0.1.3，仓库 tags 查询为空。不能把该源码称为实际0.1.5适配器的精确首选修改形式。随包 JavaScript 和96份引擎材料已保留；继续发布前需要准确0.1.5适配器源码定位/上游确认或经过验证的可对应版本。未向上游发消息，不虚构回复。
2. libvips 的九份互惠库完整源码与构建补丁已到位，但未在此 Windows 开发机重建整套 MXE、验证替换/重新链接，也未镜像其全部编译工具链和所有非互惠传递依赖。LibreOffice 外部静态依赖同样需要沿 `core.json`/第三方清单核对。不能写“完整可复现构建已通过”。上游脚本足以指示工程下一步，不要求用户安装所有工具。
3. 其余47个 Microsoft CRT/UCRT 文件尚未全部与独立官方发行包逐字节匹配。TOC 显示 VCRUNTIME 来自实际 CPython安装，MSVCP来自NumPy wheel，UCRT/API-set 来自构建环境原生依赖。保留 CPython 原始 Microsoft Distributable Code 通知（含继续分发的条件），不把从系统或开发环境找到文件视为任意复制许可。下一发行应核准正式取得的 redist/SDK来源和终端条款，而不是用有效签名代替条件。
4. 本产品终端条款不能禁止法律/组件许可允许的库调试、替换或逆向范围；需要选定实际提供源码的发布地址、保留期和发行人身份。测试签名、当前本地素材目录不构成正式书面源码承诺。

以上缺口是精确技术/运营决定，不是统一的“找律师审批”。仍未给出法律结论。

## 免费部署验证的补齐

此前 PostgreSQL 参数测试在未设置 `KSTUDIO_TEST_POSTGRES_URL` 的 CI 中跳过。`r2-cloud-container.yml` 现新增临时 postgres:17 service，跑实际并发预留、幂等、租户隔离、退款与未知usage恢复，且解析JUnit强制 PostgreSQL 参数存在、无跳过、无错误；测试账号只存在于临时runner。新增 `tests/cloud/**` 路径触发。此改动待真实 GitHub runner 结果，不能用本机 SQLite 23PASS/17PGskip 冒充已跑。现有无网络容器HTTP验收继续保留，不推镜像、不接真实支付、不公开部署。

## 可复用命令

```powershell
python scripts/collect_corresponding_source_materials.py $ActualBundle $FreshSourceMaterials
./scripts/collect_windows_redistribution_evidence.ps1 -Bundle $ActualBundle -BinaryMap $ActualBinaryMap -Output $FreshVendorEvidence
# build_desktop.ps1 自动调用，仅可作用于其新建harness-stage
python scripts/prepare_release_dependency_stage.py $FreshHarnessStage
```

官方来源：[Sharp精确源码](https://github.com/lovell/sharp/tree/51a990faa26ade5586a4934ac9673c98d8893326)、[libvips Windows 8.18.7](https://github.com/libvips/build-win64-mxe/releases/tag/v8.18.7)、[LibreOffice精确core](https://github.com/LibreOffice/core/tree/bce0998afefdbc355585ca324285661a2170ba77)、[Kit公开仓库](https://github.com/deepseek-ai/dsh-libreoffice-kit)、[WebView2精确版本](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.3856.49)、[ConPTY精确版本](https://www.nuget.org/packages/Microsoft.Windows.Console.ConPTY/1.25.260303002-preview)。
