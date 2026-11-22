# IP Sentinel v1.2.0 第三方组件审查

本清单基于提交 `e653227ffa8b5f7850f6ca10aa4f40c812e4886b` 的旧冻结产物，用于发布审查。新产物需要重新核对。项目自身的许可状态沿用仓库现状。

| 组件 | 旧产物版本或文件 | 许可证及核对依据 |
| --- | --- | --- |
| CPython | 3.12.14，含 Windows Python 运行时及标准库 | PSF 许可证及 CPython 随附的第三方声明。发布时使用实际运行时对应的文本。 |
| OpenSSL | 3.5.8，由 Python 的 `ssl.OPENSSL_VERSION` 报告 | Apache License 2.0。发布时核对 SSL 实际加载的组件，随附对应版本的许可和声明。 |
| PySide6 Essentials 与 shiboken6 | 6.12.0，含 Python Qt 绑定及 ABI DLL | 按 Qt for Python 社区发行的 LGPLv3 路径评估。分发前核对实际源文件、二进制构建选项和许可文本。 |
| Qt | 6.12.0，含 Core、Gui、Network、Widgets、Svg 及插件 | 已核对冻结产物的插件清单及对应官方源码的 SPDX 标记。归档摘要、已提取许可文本的位置和待验证项见 [Qt LGPL 再分发审查](QT_LGPL_COMPLIANCE.md)。 |
| 软件 OpenGL 组件 | `_internal/PySide6/opengl32sw.dll`，内嵌 Mesa 11.2.2 字符串 | 与官方 PySide6 wheel 完全相同。与 Qt SDK 签名归档中 DLL 的 PE 时间戳、代码段及只读数据段相同，但整文件哈希不同。Qt 的许可归属包含 MIT、Boost 1.0 和 LLVM 单独告知。精确补丁、LLVM 补丁版本与构建配方仍待核实。 |
| Microsoft 原生运行库 | `MSVCP140*.dll`、`VCRUNTIME140*.dll` 为 14.44.35211.0，`ucrtbase.dll` 及 API Set 转发 DLL 显示 10.0.26100.4654 | 旧构建有 42 个 UCRT/API Set 文件来自本机的 libheif 软件目录。原始 Microsoft 可再分发包未确认。下一次候选构建应验证受支持系统上的依赖，并固定批准的运行库输入与适用分发条款。 |

这份清单仅覆盖本次两个发布阻塞涉及的组件。正式交付前需从新构建的文件清单补齐应用依赖、编译器运行库和各组件嵌入的第三方代码声明。

逐文件基线、已提取的完整 GPLv3 与 LGPLv3 正文及独立源码交付索引见仓库的 `release-compliance/`。清单以旧冻结产物的相对路径和 SHA-256 为依据，其中待确认证据不会由自动化脚本判为通过。

## 编解码器和原生传递依赖

已将官方源码归属记录和相关许可证文本提取到 `release-compliance/licenses/upstream-qt/`，索引见 `release-compliance/qt-attributions.json`。QtBase 归档声明 qjpeg 的候选为 libjpeg-turbo 3.2.0，QtImageFormats 声明 qtiff 和 qwebp 的候选分别为 libtiff 4.7.2 与 libwebp 1.6.0。三者的旧包普通 PE 导入表未见独立的对应编解码器 DLL。该证据支持进一步检查静态链接，但不能单独锁定编译选项、所有传递库或源补丁。归属索引也记录 QtBase 的 libpng、zlib、FreeType、HarfBuzz、PCRE2 与 MD4C 的上游版本及许可，具体启用项须与实际构建记录对照。

Mesa 的旧包及 wheel 哈希为 `18aedc7a4b610f53bcc7b7a5c5ed9293c7e86f030e3273ad54ed3bb1ebd36702`。Qt SDK 对照 DLL 的哈希为 `b04de4541863bc7d8879040a78889c4849c1b1da2784c4630f734c146c2998ce`。其共同代码段 SHA-256 为 `39880e8a7f5ca7e58e7aa0a635508842dace554d77f62267cb2927e48d951307`。Qt 的历史构建说明将 Mesa 11.2.2 与 LLVM 3.6 系列关联。实际 PE 导入表未显示独立 LLVM DLL，精确 LLVM 版本、配置、补丁及内嵌许可仍需上游确认。

另从 Mesa 官方归档获取了上游基础源码 `mesa-11.2.2.tar.xz`，本地 SHA-256 为 `40e148812388ec7c6d7b6657d5a16e2e8dabba8b97ddfceea5197947647bdfb4`，未验证其分离签名。该归档用于源码审查，尚未证明包含 Qt 交付 DLL 的完整对应源码与补丁，因此未加入正式源码交付索引。

按原始打包收集记录分组的核对结论及人工复核问题见 [发布合规人工复核材料](RELEASE_COMPLIANCE_REVIEW.md)。

- [CPython 许可证](https://docs.python.org/3/license.html)
- [OpenSSL 许可证](https://openssl-library.org/source/license/)
- [Qt 模块许可](https://doc.qt.io/qt-6/licensing.html)
- [Qt for Python 许可证说明](https://doc.qt.io/qtforpython-6/licenses.html)
- [Qt Mesa llvmpipe 归属声明](https://doc.qt.io/qt-6/qt-attribution-llvmpipe.html)
- [Qt Windows Mesa 构建资料](https://wiki.qt.io/MesaLlvmpipe)
- [Mesa 11.x 官方源码归档](https://archive.mesa3d.org/older-versions/11.x/)

内部验证载荷的 10 份 VC 运行库及其授权缺口见 [MSVC 再分发审查](MSVC_REDISTRIBUTION_AUDIT.md)。最终载荷须重新核对来源、加载路径和部署权限。
