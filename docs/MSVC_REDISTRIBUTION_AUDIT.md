# Microsoft VC++ x64 运行库再分发审查

对象为 Windows 10 内部验证载荷。以下数据来自重新读取文件、计算摘要及 Windows Authenticode 验证。

| 部署路径 | SHA-256 | 文件版本 | 签名结果与主体 | 构建输入 |
|---|---|---|---|---|
| _internal/PySide6/MSVCP140.dll | f6f1d55bfd64027820ddce48f9cd8cf46d53bfa34047e6acf4ef348d492a05cb | 14.44.35211.0 | Valid / The QT Company Oy | isolated-venv/Lib/site-packages/PySide6/MSVCP140.dll |
| _internal/PySide6/MSVCP140_1.dll | 2be87527c41e1ba8aff48e326e0adcd4743516e0bbcc9304986c726e27de6aca | 14.44.35211.0 | Valid / The QT Company Oy | isolated-venv/Lib/site-packages/PySide6/MSVCP140_1.dll |
| _internal/PySide6/MSVCP140_2.dll | 6a72ed8a87eae1671640bd1ca98eccb989f1772ae46ab84594e385bf6d4ac4fb | 14.44.35211.0 | Valid / The QT Company Oy | isolated-venv/Lib/site-packages/PySide6/MSVCP140_2.dll |
| _internal/PySide6/VCRUNTIME140.dll | a36e0cb185eb89533ed96d4568138f86a1315756a8b2644c5963a8ce23e32101 | 14.44.35211.0 | Valid / The QT Company Oy | isolated-venv/Lib/site-packages/PySide6/VCRUNTIME140.dll |
| _internal/PySide6/VCRUNTIME140_1.dll | 302b1e160e858602490a55e32ae2e29ddfc0bec2a188e19550cb655cdaa58f9c | 14.44.35211.0 | Valid / The QT Company Oy | isolated-venv/Lib/site-packages/PySide6/VCRUNTIME140_1.dll |
| _internal/shiboken6/MSVCP140.dll | 1ba4d7c0a95d375da138a057a57593b33510ad5bda6c5e2686afd68faa5b4231 | 14.44.35211.0 | Valid / The QT Company Oy | isolated-venv/Lib/site-packages/shiboken6/MSVCP140.dll |
| _internal/shiboken6/VCRUNTIME140.dll | e7be9112ee9a5b9f44b44bff24cb761cca9b1ed7550b612f77b70edfcf5fdabf | 14.44.35211.0 | Valid / The QT Company Oy | isolated-venv/Lib/site-packages/shiboken6/VCRUNTIME140.dll |
| _internal/shiboken6/VCRUNTIME140_1.dll | f02cd4a862b85a9a3153d27e15e5a213f5df8e3d77004ed2e87b8a7e8873d97c | 14.44.35211.0 | Valid / The QT Company Oy | isolated-venv/Lib/site-packages/shiboken6/VCRUNTIME140_1.dll |
| _internal/VCRUNTIME140.dll | d5e4d9a3e835fa679450145d6a7d94e36573a509317111904d9b3712c30d9066 | 14.44.35211.0 | Valid / Microsoft Windows Software Compatibility Publisher | base-python/VCRUNTIME140.dll |
| _internal/VCRUNTIME140_1.dll | 1f2d41c4aa5db0bc33ebf7b66d72943a817d7ce6cbe880502a9403823633093f | 14.44.35211.0 | Valid / Microsoft Windows Software Compatibility Publisher | base-python/VCRUNTIME140_1.dll |

## 授权与部署决定

五个文件名均属于 VC v14 x64 CRT 家族。八个 Qt 目录副本可追溯至锁定 wheel，另外两个来自基础 Python。尚未建立这些副本与获得授权的 Microsoft.VC143.CRT REDIST 目录之间逐字节相同的证据。wheel 成员匹配、版本资源、有效签名分别证明不同事实，均不能单独证明本项目取得再分发权。

安装版优先评估微软集中部署。由已获授权的发布方采用官方签名的 vc_redist.x64.exe，或指导用户直接从微软安装。发布工程师须验证最低版本、已有更新版本、权限、重启及离线安装；检查进程实际加载路径，避免私有副本优先加载而错过集中更新。便携版可要求目标机预装受支持的 x64 Redistributable；若承诺解压即用，应从获授权 Visual Studio 工具集列出的 x64 REDIST 目录取得应用本地文件，记录工具集、版本、签名和逐文件摘要，并承担更新责任。两条路线均应在纯净系统重新验证 Qt、Python、插件及 TLS。当前仅记录方案，原内部测试包保持原样。

责任方：发布工程师提供可追溯官方输入及最终载荷对照；发行主体与许可审核人员确认适用 Visual Studio 条款、分发资格及产品条款。结论为待复核。

[微软部署说明](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files) · [VS 2022 可再分发清单](https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution) · [官方运行库](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) · [许可条款](https://visualstudio.microsoft.com/license-terms/)
