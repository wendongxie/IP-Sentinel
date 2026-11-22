# IP Sentinel v1.2.0 发布合规人工复核材料

**状态：BLOCKED。** 本材料针对基线提交 `e653227ffa8b5f7850f6ca10aa4f40c812e4886b` 的 115 个旧冻结原生文件。待发布构建尚不存在。复核时以最终 EXE 的隔离安装结果及最终 ZIP 解压结果为准。

## 发行形态与证据

| 项目 | 工程事实 |
| --- | --- |
| 安装版 | Inno Setup 按用户安装，默认位于 `%LOCALAPPDATA%\Programs\IP Sentinel`。程序、Qt DLL、Python 绑定和插件按文件写入部署树。 |
| 便携版 | 目录式 PyInstaller 载荷打包为 ZIP，解压到可写目录后运行。动态库位置与安装版一致。 |
| 组件清单 | [原生文件清单](../release-compliance/inventory.json) 包含相对路径、哈希、分组、版本、来源线索、许可依据、上游源码、补丁证据和交付事项。原始收集记录来自旧隔离运行的 PyInstaller `COLLECT-00.toc`。 |
| 工程替换 | Windows 10 经独立 Qt SDK 6.12.0 动态库实测。SDK 的 Qt Core DLL 与旧包文件 SHA-256 不同。安装测试副本及已解压便携版替换后启动、托盘和单实例唤醒通过，均恢复原文件。 |
| 已集中交付材料 | [合规目录](../release-compliance/README.md) 含 LGPLv3/GPLv3 全文、源码哈希索引、提取的第三方许可、替换说明和审核状态。 |

### 分组解释

基线 115 个文件全部与原 PyInstaller 收集记录指向的磁盘输入逐字节比对一致。对官方发行物的独立核对结果为 **43 个官方 wheel 精确匹配、30 个已定位来源系列、42 个精确发行来源待确认**。43 个中，35 个来自 PySide6 或 shiboken6 wheel，另 8 个来自 SQLAlchemy 官方 Windows wheel。

- `WHEEL_EXACT` 表示基线文件和指定官方 wheel 成员哈希一致。文件的 wheel 来源已经确认，其上游有效构建参数仍取决于该 wheel 的构建证据。
- `SDK_EXACT` 单列官方 SDK 对照文件。独立替换测试用的 Qt Core DLL 来自该组；它没有随旧包分发。基线 Qt Core 归于 wheel。
- `SOURCE_FAMILY` 表示原始构建记录、文件指纹或版本能指向来源系列，仍缺精确可再分发的发行包、构建输入或构建记录。
- `EMBEDDED_CANDIDATE` 以父文件路径和 SHA-256 记录可能静态链接或嵌入的组件。这些条目不重复计入 115 个落盘原生文件。没有独立 PE 导入不等于已经证明静态编入；须用链接记录、构建配置或足以确定版本的二进制证据核实。
- `UNRESOLVED` 表示精确发行来源未确定。即使能指出收集路径，仍可能无法证明原始发行物与交付权利。

## 缺口、所需文件与可获取渠道

| 范围 | 已掌握 | 取得以下证据即可收敛 |
| --- | --- | --- |
| PySide6 Essentials、shiboken6 和 Qt 6.12.0 | 官方 Windows wheels；QtBase、QtSvg、QtImageFormats、PySide 源码归档及摘要；PySide 源码中的 COIN 构建配方；运行时构建信息。 | 需要这两个具体 wheel 的 COIN 任务标识或公开日志、Qt 与 PySide 精确提交、实际构建参数或 `CMakeCache.txt`／配置摘要、工具链和 Windows SDK 版本、补丁及生成绑定步骤。配方只证明上游具备这些构建步骤。 |
| Mesa/LLVM | `opengl32sw.dll` 与 PySide6 wheel 一致，内嵌 Mesa 11.2.2；Qt SDK 对照的代码段相同，整文件哈希不同；Mesa 基础源码已取得。 | 要求匹配旧 DLL 指纹的 Mesa/LLVM 精确源码修订、补丁、链接组件清单、Windows 构建脚本和完整版权文件。两份 DLL 的整文件不同原因仍未证明。 |
| 编解码器和 Qt 嵌入库 | Qt 源码有 libjpeg-turbo、libtiff、libwebp 等版本归属和许可文本。旧包 qjpeg、qtiff、qwebp 没有直接导入对应独立 DLL。 | 需要各插件的 CMake 特性摘要或链接清单，明确静态、动态或未选，尤其是 TIFF 对 JPEG、WebP、zlib 等选项。根据实物补齐 libpng、PCRE2、FreeType、HarfBuzz 等的传递声明。 |
| CPython 与原生依赖 | 旧包的原始构建记录和版本。 | 核对最终 CPython 发行包及其捆绑声明、SQLite 及 libffi 源码版本、CFFI wheel 来源和依赖。 |
| MSVC/UCRT | 旧包 42 个 UCRT/API Set 文件的直接收集位置是本机另一软件的 libheif 目录。文件版本和哈希已记录，原始 Microsoft 发行物未确认。 | 明确实际来自哪个 Microsoft 可再分发包或 Windows SDK。下一次工程构建应使用审核通过的 SDK/Redistributable 输入，或验证在支持的 Windows 版本上使用系统组件后排除相应文件。 |

已公开的来源集中在 Qt 模块下载目录、PySide wheel 的 PyPI 文件详情、源码内 COIN 配方及 Qt Windows 构建文档。剩余的**实际构建任务与补丁证据**应向上游询问。若上游无法提供，下一次评估应限定为复现受控源码构建或剔除可选组件并回归测试。没有新证据时停止重复搜索。

- [Qt for Python Windows 构建文档](https://doc.qt.io/qtforpython-6/building_from_source/windows.html)
- [Qt for Python 6.12.0 源码目录](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.12.0-src/)
- [Qt 6.12.0 分模块源码](https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/)
- [Qt 的 Mesa 归属说明](https://doc.qt.io/qt-6/qt-attribution-llvmpipe.html)
- [微软 C++ 运行库再分发说明](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170)

## 两种交付布局

| 维度 | 保留 PyInstaller 目录式 | 单独维护第三方可替换运行时目录 |
| --- | --- | --- |
| LGPL 可验证性 | 已有 Qt Core 的两种交付实测。增加刻意修改的兼容构建与其他绑定的证据。 | 能集中列出 Qt 库和插件，仍需证明运行路径、源版本与替换有效。 |
| 用户替换 | 写权限明确，用户按相对路径替换。分散的插件需使用说明。 | 更容易定位；加载器或插件路径重设若错误，会加载到另一份库。 |
| 构建复杂度 | 沿用 spec、安装器及便携 ZIP，收敛来源白名单即可。 | 需校验 DLL 搜索顺序、Qt 插件定位、更新行为、签名、异常恢复及两个系统的部署方式。 |
| 包体积 | 分包或过滤可选功能可减少体积，需实测。 | 搬移文件的体积接近原方案。保留多个运行时副本会增加体积，当前未测。 |
| 维护成本 | 较低，有现成流水线及验证记录。 | 需长期同步 ABI、插件与安装器布局并维护额外回归。 |
| 功能影响 | 影响较小。任何移除可选插件或系统库都需回归。 | 改变 Windows 加载路径，需验证托盘、字体图标、代理、启动和卸载。 |

推荐保留当前目录式布局，先固定第三方 DLL 来源并对最终载荷验证。仅当复核认定实际替换障碍、加载路径无法可靠控制，或需要外置运行时才能维护来源时，再试验第二种布局。

## 请专业审核人员明确回答

1. **LGPLv3 §4、§4(a)–(c)**。可否按实际安装 EXE 和 ZIP 的告知方式分发组合应用。关于 Qt 许可及版权的告知应加在哪里，是否必须在应用内附带相应提示？安装和使用条款是否明确允许修改 LGPL 库及为调试该修改而逆向工程？
2. **LGPLv3 §4(d)(1)**。目录式布局、可写权限、现有不同构建 Qt Core 实测和最终复测计划，是否足以证明实际采用并运行接口兼容的修改库？需针对 Qt 插件、PySide6 或 shiboken6 分别提供哪些运行或 ABI 证据？
3. **LGPLv3 §4(d)(0)**。若某组件无法走共享库机制，需要提供哪些最小对应源码、可重组的应用材料、构建工具与许可条件？基线 PyInstaller bootloader、冻结应用和其余库应如何分别处理？
4. **LGPLv3 §4(e)、GPLv3 §6**。两种下载形态是否涉及适用的 User Product 交易条款？若适用，运行修改后的组合应用需要提供哪些安装信息、权限说明或签名资料？
5. **GPLv3 §6(d) 与独立第三方条款**。在同一个正式下载页提供带摘要的对应源码 ZIP 是否符合实际交付方式？需要保证源码可获取多久，源码 ZIP 还需哪些修改、配置、许可与构建资料？MSVC/UCRT、Mesa/LLVM 和各编解码器是否有额外义务？

- [GNU LGPLv3 条文](https://www.gnu.org/licenses/lgpl-3.0.html)
- [GNU GPLv3 条文](https://www.gnu.org/licenses/gpl-3.0.html)
- [Qt 官方 LGPL 义务说明](https://www.qt.io/development/open-source-lgpl-obligations)

## 下一次正式构建前

1. 取得可信的 Windows x64 CPython 运行时，验证已修复门槛内的 CVE、正式发行出处、哈希、实际加载 DLL、HTTPS 证书负例与代理路径。
2. 固定原生组件来源，解决来自无关应用目录的 UCRT/API Set 文件和其他来源缺口。补齐上游证据或经审查的替代方案。
3. 完成最终二进制的源码、许可证、版权和修改记录比对，取得有证据的工程和专业法律结论，更新发布前置检查中的签核。
4. 用现有版本及 wheel 哈希锁构建隔离候选包。对最终安装、便携包的文件清单、动态库替换、许可资料、链接、SHA-256 和 Win10/11 行为进行复核。

英文技术问题见 [上游询问草稿](QT_UPSTREAM_INQUIRY_EN.md)。

内部验证载荷的 10 份 VC 运行库及其授权缺口见 [MSVC 再分发审查](MSVC_REDISTRIBUTION_AUDIT.md)。最终载荷须重新核对来源、加载路径和部署权限。
