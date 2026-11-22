# Qt LGPL 再分发审查

审查对象为提交 `e653227ffa8b5f7850f6ca10aa4f40c812e4886b` 的旧 Windows 候选包。仓库公开可见性与项目本身的许可是两项独立事实。本记录用于核实社区版 LGPLv3 分发条件。

## 冻结产物清单

| 范围 | 实际发现 |
| --- | --- |
| Qt 原生库 | `Qt6Core.dll`、`Qt6Gui.dll`、`Qt6Network.dll`、`Qt6Svg.dll`、`Qt6Widgets.dll` |
| Python 绑定 | `QtCore.pyd`、`QtGui.pyd`、`QtNetwork.pyd`、`QtWidgets.pyd`、`pyside6.abi3.dll`、`shiboken6.abi3.dll` |
| 通用及图标插件 | `qtuiotouchplugin.dll`、`qsvgicon.dll` |
| 图像格式 | `qgif.dll`、`qicns.dll`、`qico.dll`、`qjpeg.dll`、`qsvg.dll`、`qtga.dll`、`qtiff.dll`、`qwbmp.dll`、`qwebp.dll` |
| 网络信息与 TLS | `qnetworklistmanager.dll`、`qcertonlybackend.dll`、`qopensslbackend.dll`、`qschannelbackend.dll` |
| 平台及样式 | `qdirect2d.dll`、`qminimal.dll`、`qoffscreen.dll`、`qwindows.dll`、`qmodernwindowsstyle.dll` |

Qt 官方模块页面的 GPL 专用名单中未见上述五个 Qt 模块。下表依据已校验的 Qt 6.12.0 源码归档，列出每个已收录插件 DLL 对应的源码目录。所检查的插件入口或实现文件均在 SPDX 标记中列出 `LGPL-3.0-only` 选项。这个结论仍需与编译选项、全部传递依赖及嵌入的第三方代码核对。

| 源码归档 | 源码位置（相对 `src/plugins/`）及 DLL |
| --- | --- |
| qtbase | `generic/tuiotouch` → `qtuiotouchplugin.dll` |
| qtbase | `imageformats/gif` → `qgif.dll`，`imageformats/ico` → `qico.dll`，`imageformats/jpeg` → `qjpeg.dll` |
| qtbase | `networkinformation/networklistmanager` → `qnetworklistmanager.dll` |
| qtbase | `platforms/direct2d` → `qdirect2d.dll`，`platforms/minimal` → `qminimal.dll`，`platforms/offscreen` → `qoffscreen.dll`，`platforms/windows` → `qwindows.dll` |
| qtbase | `styles/modernwindows` → `qmodernwindowsstyle.dll` |
| qtbase | `tls/certonly` → `qcertonlybackend.dll`，`tls/openssl` → `qopensslbackend.dll`，`tls/schannel` → `qschannelbackend.dll` |
| qtsvg | `iconengines/svgiconengine` → `qsvgicon.dll`，`imageformats/svg` → `qsvg.dll` |
| qtimageformats | `imageformats/icns` → `qicns.dll`，`imageformats/tga` → `qtga.dll`，`imageformats/tiff` → `qtiff.dll`，`imageformats/wbmp` → `qwbmp.dll`，`imageformats/webp` → `qwebp.dll` |

## 交付所需证据

- PyInstaller 采用目录式冻结，Qt 原生库及插件以独立文件交付。须在全新构建的安装版与便携版副本中分别替换 ABI 兼容库，验证 Windows 加载了替换后的库，并验证界面启动。独立 DLL 的存在只证明物理布局。
- 随二进制提供适用的 LGPLv3、GPLv3 正文、版权声明和第三方组件说明。按实物版本核对 Qt、PySide6、shiboken6 的源码、构建脚本和任何改动。发布方应保有对应源码并提供可验证的获取方式，上游页面作为来源记录。
- 根据替换测试提供用户可执行的步骤，包括安装路径、需要写入权限的位置、备份恢复以及所需的 ABI 版本。若交付方式是否需要额外安装信息存在争议，交由人工专业复核。

## Windows 动态库替换验证

在 Windows 10 专业版 19045 上，把旧冻结产物复制到独立测试目录。通过 PyPI 官方发行元数据校验 `pyside6_essentials-6.12.0-cp310-abi3-win_amd64.whl`，归档 SHA-256 为 `c9a95102aa23c1f86516a30d5a9be37552d324eee7e567eb7508973f1218cb42`。

退出测试副本后，将 `_internal/Qt6Core.dll` 移到备份文件，从 wheel 的 `PySide6/Qt6Core.dll` 复制替换文件到原路径。两个 DLL 的 SHA-256 均为 `f57ed38afd95d0306cca9d88d997f639f70c7628a4f1f064eae291d579487121`。以 Windows 平台插件运行 `IP Sentinel.exe --smoke-test`，返回码为 0。测试入口检查主窗口、两个页签、图标、托盘及单实例唤醒，并使用临时 SQLite 数据库。测试后恢复原 DLL，已复核恢复后的 SHA-256。

随后使用 Qt 官方 SDK 的 6.12.0 Windows x64 MSVC2022 QtBase 归档，归档 SHA-1 与官方索引的 `bf35f8916164c6f313af8347dd0e91efe18178f0` 一致，实测 SHA-256 为 `219d1b86def3be418e31d704572bc4acc91b2ec373c65595c9fb12b42bf098dc`。提取的 `Qt6Core.dll` Authenticode 检查为有效，SHA-256 为 `39175459c4837c8cc0f709a637fb6eadb25d696785109c8393559ec876f02703`，与原 DLL 不同。替换后窗口测试通过，恢复哈希与原始文件一致。证据覆盖该 DLL、Windows 10 和已测试的界面功能。正式用户数据和配置未参与验证。

独立 AppId 的旧隔离安装器和旧便携 ZIP 也分别通过同一替换流程。安装、两种交付形态的窗口测试及隔离卸载返回码均为 0，两份 DLL 恢复后均通过原始 SHA-256 比对。旧包中的 `pyside6.abi3.dll`、`shiboken6.abi3.dll` 与 `PySide6/QtNetwork.pyd` 分别和本地固定 6.12.0 依赖目录中的对应文件进行 SHA-256 比对，三个文件均一致。

## 对应源码交付计划

Qt 官方目录已确认提供 6.12.0 的 `qtbase`、`qtsvg`、`qtimageformats` 分模块归档，Qt for Python 官方目录提供同版本的 `pyside-setup` 归档，覆盖 PySide6 与 shiboken6。版本匹配是第一步，还需核对 wheel 和最终冻结产物对应的构建配置、补丁、第三方许可文本和任何额外原生依赖。

以下归档已下载至本地审查目录 `.build-tools/strict-v1.2.0/qt-sources/`，并与 Qt 官方同路径的 `.sha256` 文件核对一致。
四个归档内的 LGPLv3 和 GPLv3 完整文本已提取至该目录下的 `license-review/`，按归档名称分目录保留，供交付审查使用。最终包还需纳入适用的组件版权与独立第三方声明。

| 归档 | SHA-256 |
| --- | --- |
| `qtbase-everywhere-src-6.12.0.tar.xz` | `a951bd163c7b80fc6b8c88d7668fb56abf91c152373e13c10666763238131307` |
| `qtsvg-everywhere-src-6.12.0.tar.xz` | `e4ab39534ec97987b1b9b60ef7f4d3253d5912a69f8c713a01753174a4029331` |
| `qtimageformats-everywhere-src-6.12.0.tar.xz` | `0943132b5db8de6b6a7f1d162682173e8763c7ed94e80fd39113292845f67762` |
| `pyside-setup-everywhere-src-6.12.0.tar.xz` | `099c1a597cf33c1b000e11cf68a0b82d216fb802bf81726efc720394f10c7751` |

计划将经过校验的对应源码、构建信息、补丁记录、适用的完整许可证和版权声明与实际二进制版本绑定，并从与二进制同等可访问的位置提供源码。按 LGPLv3 第 4(d)(1) 条验证合适的共享库机制，包括可使用接口兼容的修改版。若采用第 4(d)(0) 条的重新组合路径，另行确认最小对应源码、可重新组合的应用代码及 GNU GPLv3 第 6 条交付条件。安装信息仅在第 4(e) 条适用时判定仍需提供哪些内容。最终许可条款、安装信息和源码覆盖须人工专业复核。

## 合规收尾清单

| 事项 | 工程结果 |
| --- | --- |
| 用户自行更换、运行修改版 | Qt 库在 PyInstaller 输出的 `_internal/` 中独立交付。Inno Setup 默认按用户身份安装到 `%LOCALAPPDATA%\Programs\IP Sentinel`。便携副本应放在用户有写权限的位置。 |
| 用户操作 | 退出软件，将目标 DLL 备份到部署树外，复制可信 Windows x64、同 ABI 的构建到原路径，再启动并检查窗口、托盘与实际使用功能。失败时退出并恢复备份。升级后检查修改是否被安装程序覆盖。 |
| LGPLv3 §4(d)(1) | 已验证一个来自独立构建的 Qt DLL 能替换并运行。最终交付需复核更多相关组件、适用的运行条件及发行条款。 |
| LGPLv3 §4(d)(0) | 作为替代分发路径评估。若改用该条，需要提供对应源码和可重新组合的应用材料，当前未按此路径准备。 |
| LGPLv3 §4(e) | 安装信息在 GPLv3 §6 要求且运行修改后的组合应用需要时适用。需专业复核产品分发形态是否满足适用条件，并明确实际需要的资料。 |
| 源码及版权 | 建议正式附件和二进制下载页提供同版本源码归档、构建说明、补丁及摘要，并在 EXE 安装目录和 ZIP 内包含告知、完整许可和定位源码的说明。需确认最终发行条款没有妨碍为调试库修改而进行的逆向工程。 |
| 第三方原生组件 | 旧包另含 `PySide6/opengl32sw.dll`，需要把真实二进制对应到构建来源、许可和源码。图像插件所含第三方编解码器以及原生运行库的版本、构建选项和声明仍需逐项锁定。 |

Qt 官方 SDK 归档仅用于工程替换测试。交付时仍须为实际发布的 PySide6 wheel 二进制建立对应源码、构建配置和传递许可清单。

仓库 `release-compliance/` 集中保留替换步骤、审查状态、逐文件基线、四份源码的摘要及 GPLv3 与 LGPLv3 全文。发布检查需要工程和法律审核结论，并核对相关清单的摘要。未补全的版权和独立许可、实际 wheel 编译配置和补丁、Mesa/OpenGL 与编解码器对应关系，以及 GPLv3 §6 和 LGPLv3 §4 的具体适用方式仍是阻塞。既有用户软件许可沿用原状态。

## wheel 和源码对应证据

- 用官方 Windows x64 wheel 重新比对旧冻结包的原生清单。115 个原生文件中，35 个可与 PySide6 Essentials 6.12.0 或 shiboken6 6.12.0 wheel 成员逐字节对应，具体成员路径见 `release-compliance/inventory.json`。其余文件包含 CPython、编译器运行库和本应用 EXE 等，应分别核对来源。
- wheel 的 `PySide6/_config.py` 报告构建时间为 2026-10-05T13:28:34Z，`shiboken6/_config.py` 为 2026-10-05T13:28:25Z。实际导入报告三个组件均为 6.12.0，Qt 为 x86_64、MSVC 2022、动态链接的 Release 构建。Python limited API 输出显示绑定以 3.14.3 构建，在隔离的 3.12.16 运行。
- 官方 `pyside-setup` 归档包含 `dependencies.yaml`、`coin/product_dependencies.yaml`、`coin/instructions/execute_build_instructions.yaml` 和 `coin/instructions/execute_desktop_instructions.yaml`。这些是上游构建配方。仍缺实际构建任务日志及源提交、各 Qt 模块的生效配置或 CMake 缓存、所用 Windows SDK 与 Clang/LLVM 版本，以及 wheel 生成时应用的所有补丁或上游确认无额外补丁的证据。wheel 中的版本文件给出发行版本，未据此认定准确的 Git 提交。
- 四份已核验归档覆盖 QtBase、QtSvg、QtImageFormats、PySide6 和 shiboken6 的已辨明上游源码。软件 OpenGL 为单独输入。具体编解码器选择及编译配置仍需结合构建证据核实。已保存从源码归档原样提取的对应版权归属与许可文件。

## 需要人工法律复核的问题

1. 核对 LGPLv3 §4(d)(1) 的共享库机制是否适用于最终交付的全部 LGPL 组件，包括 PySide6、shiboken6、Qt 插件及其 ABI 配套文件。若某组件需走 §4(d)(0)，明确提供哪些可重新组合材料。
2. 核定 LGPLv3 §4(e) 与 GPLv3 §6 的安装信息适用范围，确认最终安装和运行的权限、签名策略及文档是否允许用户实际运行修改版。
3. 核对安装条款和使用说明是否允许为调试 LGPL 组件修改而进行的逆向工程。检查告知位置、版权署名、许可证正文和第三方许可条件。
4. 核定源码 ZIP 与二进制同位置交付的持续可用性、对应源码的覆盖范围，以及编解码器、Mesa/LLVM 和 Microsoft 运行库的独立条款。待取得实际构建结果后按版本逐项签核。

- [Qt LGPL 使用义务](https://www.qt.io/development/open-source-lgpl-obligations)
- [Qt 6.12.0 官方 Windows x64 SDK](https://download.qt.io/online/qtsdkrepository/windows_x86/desktop/qt6_6120/qt6_6120_msvc2022_64/qt.qt6.6120.win64_msvc2022_64/)
- [Qt 源码官方下载](https://www.qt.io/development/download-open-source)
- [Qt 6.12.0 模块源码](https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/)
- [Qt for Python 6.12.0 源码](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.12.0-src/)
- [GNU LGPLv3 条文](https://www.gnu.org/licenses/lgpl-3.0.html)

内部验证载荷的 10 份 VC 运行库及其授权缺口见 [MSVC 再分发审查](MSVC_REDISTRIBUTION_AUDIT.md)。最终载荷须重新核对来源、加载路径和部署权限。
