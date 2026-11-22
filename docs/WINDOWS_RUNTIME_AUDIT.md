# v1.2.0 Windows 运行时安全审查

核对日期为 2026 年 11 月 22 日。基线为 `e653227ffa8b5f7850f6ca10aa4f40c812e4886b`。

OpenSSL 官方公告将高危 CVE-2026-84782 的 3.5 分支修复边界列为 3.5.9，并将 CVE-2026-107493、CVE-2026-88822、CVE-2026-88823 和 CVE-2026-95691 等后续问题的修复边界列为 3.5.10。官方安全索引和下载页的更新状态不同，本次查询官方 GitHub 的 `openssl-3.5.10` 发布及标签均返回 404。安全公告中的修复版本号不能用作源码归档的完整性证明。

| Windows x64 运行时 | 实际 OpenSSL | 归档 SHA-256 |
| --- | --- | --- |
| 当前 Python 3.12.14 | 3.5.8 | 沿用旧候选包证据 |
| Astral Python 3.12.16，20261110 | 3.5.9 | `e23fe5b16926de1d81661b1a97352e89fb167549c55a6825796ccd0f32ec7f1b`，与官方发行元数据一致 |
| Python.org 3.14.10 Windows 嵌入包 | 3.5.9 | `90905e64a840557d8c1bc4f5b74db3d7ee85e3ffb217611cac1c7813acea4159`，其中 `python.exe` 的 PSF 签名验证为有效 |
| Python.org 3.15.2 Windows 嵌入包 | 3.5.9 | `d012f3aa29cf07436dae8aea1fec0fd195c2612a0b059b1f915ae0afb9ad1f62`，其中 `python.exe` 的 PSF 签名验证为有效 |

复核方法为从官方发行页获取相同架构的归档，校验归档摘要，在隔离目录解压，运行 `python.exe -c "import ssl, _ssl; print(ssl.OPENSSL_VERSION); print(_ssl.__file__)"`。PSF 二进制可用 PowerShell 的 `Get-AuthenticodeSignature` 核验签名。上表记录的是解压后实际运行结果。

## 方案比较

| 方案 | 维护和供应链成本 | 本轮结果 |
| --- | --- | --- |
| 保持 3.12，采用 Astral 完整运行时 | 依赖变更较少；可用发行摘要固定输入 | 已验证的最新发行仍加载 3.5.9 |
| 升级到 Python.org 3.14 或 3.15 | PSF 官方签名；仍需重新验证 PyInstaller、PySide6 和所有原生依赖 | 两个最新稳定嵌入包实际均为 3.5.9，未进入应用兼容验证 |
| 使用官方源码自建 CPython 和 OpenSSL | 需维护源码锁定、工具链、构建参数和后续安全更新 | 未找到可核验的 3.5.10 发行归档，现场也未发现可直接使用的完整 MSVC、Perl、NASM 工具链。本轮未构建 |

自建路径的待验证步骤为固定 CPython 与 OpenSSL 官方源码的签名和摘要，记录 MSVC/Windows SDK、Perl 和 NASM 版本，构建 Windows x64 OpenSSL，通过 CPython `PCbuild` 把同一构建的头文件、导入库与 DLL 一起用于重新编译 `_ssl` 和 `_hashlib`。先验证解释器，再验证冻结产物中对应 DLL 的 PE 导入、文件摘要和实际加载路径。验证矩阵包括可信 HTTPS、拒绝不可信证书、经过代理的 HTTPS，以及现有自动化测试。该路径尚未执行，不能当作已验证的构建配方。

## 其他 OpenSSL 分支复核

按 2026-11-22 的官方发行列表，受支持的 4.1 与 4.0 发布线分别列出 4.1.0 与 4.0.3。后续公告对本项目跟踪的修复给出了 4.1.1 与 4.0.4 边界，官方 GitHub 这两个版本的 Release 查询均返回 404。3.0 开源支持已结束，且 3.0.24 的同类查询亦返回 404。3.4 与 3.6 已结束常规支持。未发现同时满足公告所列修复、正式发行、可信 Windows CPython 分发且兼容现有打包方式的替代版本。本轮没有重复下载 3.5.9 运行时，也没有用未发行的提交开展替换实验。

下一次优先检查 CPython Windows 发行和 Astral 的正式 3.5 LTS 更新，验证归档签名或官方摘要、实际加载路径、Python/OpenSSL ABI、旧 DLL 排除、证书拒绝与代理请求，再审核 `approved_runtimes`。若考虑 OpenSSL 4.x，需先取得可信的完整 Windows 运行时，单独审计 Qt OpenSSL 插件与 CPython SSL 模块的兼容性。当前流水线只识别 3.x 动态 DLL 布局，采用 4.x 前须新增并实测相应加载路径和产物校验。安全门槛与审批状态保持原样。

本轮只复查发布元数据。OpenSSL 3.5.10、4.0.4、4.1.1 和 3.0.24 的官方 GitHub Release 查询仍返回 404，Astral 官方最新标签仍为 `20261110`。未发现可供试验的可信且已修复的 Windows 运行时，未下载旧运行时，也未替换任何 DLL。下次以出现正式发行归档和 Windows 构建记录作为恢复验证的条件。

- [OpenSSL 3.5 安全公告](https://openssl-library.org/news/vulnerabilities-3.5/index.html)
- [OpenSSL 官方下载](https://openssl-library.org/source/)
- [OpenSSL 支持周期](https://openssl-library.org/roadmap/)
- [Python 3.14.10](https://www.python.org/downloads/release/python-31410/)
- [Python 3.15.2](https://www.python.org/downloads/release/python-3152/)
- [Astral 20261110 构建](https://github.com/astral-sh/python-build-standalone/releases/tag/20261110)
