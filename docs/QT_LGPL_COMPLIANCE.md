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

这验证了目录式冻结产物允许在部署目录内更换同一构建的 DLL。仍需用不同的 ABI 兼容构建验证运行行为，并在最终安装版和便携版重复测试。正式用户数据和配置未参与验证。

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

当前已确认独立 DLL 布局及同构建替换流程，源码交付和不同构建替换仍为阻塞。

- [Qt LGPL 使用义务](https://www.qt.io/development/open-source-lgpl-obligations)
- [Qt 源码官方下载](https://www.qt.io/development/download-open-source)
- [Qt 6.12.0 模块源码](https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/)
- [Qt for Python 6.12.0 源码](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.12.0-src/)
- [GNU LGPLv3 条文](https://www.gnu.org/licenses/lgpl-3.0.html)
