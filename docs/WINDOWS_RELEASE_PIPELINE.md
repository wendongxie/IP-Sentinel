# Windows v1.2.0 发布流水线

当前 OpenSSL 最低门槛为 3.5.10。对于其他受支持系列，须核对同一批安全修复，并记录该系列的支持状态。项目目前没有已批准的 Windows 运行时。规则和 CVE 清单在 `packaging/release-policy.json`。更新规则须通过代码审查，依据官方公告和正式发行材料，不以修复提交或 DLL 显示版本号单独作为批准依据。

## 准备

1. 验证官方发行归档与签名或校验记录。在隔离 Windows 环境核对证书拒绝、代理 HTTPS 及真实加载的 SSL/crypto DLL。经审核后，在 `approved_runtimes` 记录 Python 版本 `python`、三个整数的 `openssl`、官方 `source`、`archive_sha256`、`verified_fixes`、审核证据 `evidence` 和 `files`。文件摘要必须覆盖 `_ssl.pyd`、`_hashlib.pyd`、两份 OpenSSL DLL 及 Python 运行库 DLL。当前实现支持使用这组动态 OpenSSL DLL 的 Windows x64 CPython；其他布局需要经过审查的验证机制。
2. 用通过运行时检查的解释器在一次性审查工作区做 PyInstaller 工程构建，逐项更新 `release-compliance/inventory.json`。按安装版与便携版的实际载荷完成原生依赖、版权、wheel 构建选项、源码和补丁核对，并补齐正式许可文本。将实际对应源码归档放在独立目录，更新 `sources.json`。专门的工程构建用于取证，正式入口在审核完成前停止。
3. 由相应审核人给出四项明确结论。在 `review.json` 为每项记录 `reviewer`、`date`、`evidence`、`inventory_sha256`、`source_index_sha256` 和 `status`。需要专业法律复核的项目仍须取得明确结论。提交通过审核的变更。构建从 Git HEAD 导出快照。

## 执行

在仓库根目录，使用 PowerShell 7、Git、Inno Setup 和本地 Gitleaks。

```powershell
pwsh -NoProfile -File .\packaging\build.ps1 `
  -Python 'C:\VerifiedPython\python.exe' `
  -Iscc 'C:\Tools\Inno Setup 6\ISCC.exe' `
  -Gitleaks 'C:\Tools\gitleaks.exe' `
  -Sources 'D:\ReleaseSources\IP-Sentinel-v1.2.0'
```

脚本使用独立目录和虚拟环境，按 `release-lock.txt` 安装固定版本的 Windows wheel，并执行 pip 一致性检查。依赖锁固定版本，尚未固定每个 wheel 的摘要。对于跨主机的完全可重现构建，仍需提供经审核的 wheelhouse 和逐 wheel 哈希。

每次运行会打印独立目录，默认在 `.build-tools/release-runs/`。JSON 和 Markdown 报告位于该目录的 `reports/`；通过的产物位于 `source/release/`。运行时或任一必需阶段失败会返回非零。Gitleaks 加上自查规则可发现常见凭据和数据库特征，不能替代对最终安装内容的解包、安装与人工核对。源码 ZIP 校验基于已核对的输入归档及最终 SHA-256；现有扫描不递归检查内部 tar.xz。流水线不执行 GitHub 操作。

## 正式发布前的剩余实测

在 Windows 10/11 对最终安装包做隔离安装、验证已安装文件和 SHA-256、运行应用、替换允许替换的 Qt 库，再卸载；对便携版重复验证。用配置隔离的环境验证有效 HTTPS、拒绝不受信证书和代理连接。检查源码交付位置和用户可访问性。核对与本次运行相符的审核记录后另行决定是否发布。

- [OpenSSL 3.5 安全公告](https://openssl-library.org/news/vulnerabilities-3.5/)
- [OpenSSL 官方下载](https://openssl-library.org/source/)
