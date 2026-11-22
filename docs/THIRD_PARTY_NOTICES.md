# IP Sentinel v1.2.0 第三方组件审查

本清单基于提交 `e653227ffa8b5f7850f6ca10aa4f40c812e4886b` 的旧冻结产物，用于发布审查。新产物需要重新核对。项目自身的许可状态沿用仓库现状。

| 组件 | 旧产物版本或文件 | 许可证及核对依据 |
| --- | --- | --- |
| CPython | 3.12.14，含 Windows Python 运行时及标准库 | PSF 许可证及 CPython 随附的第三方声明。发布时使用实际运行时对应的文本。 |
| OpenSSL | 3.5.8，由 Python 的 `ssl.OPENSSL_VERSION` 报告 | Apache License 2.0。发布时核对 SSL 实际加载的组件，随附对应版本的许可和声明。 |
| PySide6 Essentials 与 shiboken6 | 6.12.0，含 Python Qt 绑定及 ABI DLL | 按 Qt for Python 社区发行的 LGPLv3 路径评估。分发前核对实际源文件、二进制构建选项和许可文本。 |
| Qt | 6.12.0，含 Core、Gui、Network、Widgets、Svg 及插件 | 已核对冻结产物的插件清单及对应官方源码的 SPDX 标记。归档摘要、已提取许可文本的位置和待验证项见 [Qt LGPL 再分发审查](QT_LGPL_COMPLIANCE.md)。 |

这份清单仅覆盖本次两个发布阻塞涉及的组件。正式交付前需从新构建的文件清单补齐应用依赖、编译器运行库和各组件嵌入的第三方代码声明。

- [CPython 许可证](https://docs.python.org/3/license.html)
- [OpenSSL 许可证](https://openssl-library.org/source/license/)
- [Qt 模块许可](https://doc.qt.io/qt-6/licensing.html)
- [Qt for Python 许可证说明](https://doc.qt.io/qtforpython-6/licenses.html)
