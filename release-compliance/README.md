# IP Sentinel v1.2.0 第三方许可交付资料

`inventory.json` 按相对路径记录旧 Windows 冻结包的 EXE、DLL 和 PYD 及 SHA-256。更新为实际提交审批的构建清单时，逐项核对版本、来源、许可、版权和哈希。GPLv3 和 LGPLv3 正文来自已校验的 QtBase 6.12.0 源码。实际组件对应的版权声明与独立第三方许可仍须补齐。

## 对应源码

`sources.json` 列出已校验的四份官方 Qt 归档。正式交付前还需确认 wheel 的构建配置与补丁、软件 OpenGL 和编解码器的对应源码及所需声明。将补齐的归档放在独立源码目录，核对来源、版本和 SHA-256。流水线会生成 `IPSentinel_Sources_v1.2.0.zip`。发布时在同一下载位置提供源码与二进制并测试等效访问。源码归档不进入 Git。源码范围、访问条件和 GPLv3 第 6 条适用性须专业复核。

`qt-attributions.json` 对应从 Qt 源码中提取的编解码器及其他嵌入依赖的版权和许可证。收录上游文本供审查，实际纳入发行的最终范围依赖二进制与生效构建配置的对应结果。

## Windows 替换步骤

1. 从托盘退出 IP Sentinel。打开快捷方式的目标位置，或打开便携版中包含 `IP Sentinel.exe` 的目录。
2. 在 `_internal` 定位目标库。Qt 插件位于 `_internal/PySide6/plugins`。安装版默认位于当前用户的 `%LOCALAPPDATA%\Programs\IP Sentinel`。便携版应解压到可写目录。
3. 备份要替换的文件到部署目录之外。用可信的 Windows x64、ABI 兼容版本替换同名文件。插件或 Python 绑定可能需要配套的 Qt 构建。
4. 启动并检查所需功能。失败时退出并恢复备份。升级后重新确认替换状态。

Windows 10 实测涵盖不同哈希的 Qt 6.12.0 QtCore DLL。其他库的兼容性和分发条款见 `review.json`、`THIRD_PARTY_NOTICES.md` 与 `QT_LGPL_COMPLIANCE.md`。
