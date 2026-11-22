# Draft inquiry to Qt for Python and Qt Windows packaging maintainers

Proposed public channel for a packaging documentation issue: the [Qt for Python PYSIDE tracker](https://bugreports.qt.io/browse/PYSIDE), identified in the [project reporting guide](https://wiki.qt.io/Qt_for_Python/Reporting_Bugs). Submission requires confirmation of the destination and final text.

**Subject:** Corresponding build inputs for Qt for Python 6.12.0 Windows x64 wheel components

Hello,

We are preparing a Windows x64 desktop distribution and auditing which source packages and notices correspond to its Qt for Python binaries. Our baseline contains binary members matching the following official PyPI artifacts:

- `pyside6_essentials-6.12.0-cp310-abi3-win_amd64.whl`, SHA-256 `c9a95102aa23c1f86516a30d5a9be37552d324eee7e567eb7508973f1218cb42`.
- `shiboken6-6.12.0-cp310-abi3-win_amd64.whl`, SHA-256 `a1906cb8116869178c64b6bab52623bbc8b4ceed7b30bfc3c9aa0f6e67f6438e`.

We have downloaded the official Qt 6.12.0 QtBase, QtSvg and QtImageFormats source archives and the PySide 6.12.0 source archive. We found the COIN recipe files in the latter. We would appreciate official links or published attestations that identify the following for these exact wheels:

1. Which Qt for Python and Qt module revisions were used? Does the build correspond exactly to the published source archives, or were other changes applied? If there were extra changes, where can we obtain their patch series and the source inputs?
2. Is there a public COIN build ID or artifact with the effective configure/CMake options, generated binding steps, MSVC and Windows SDK versions, Clang/LLVM version, Qt dependency package IDs, and wheel assembly inputs?
3. For the shipped qjpeg, qtiff and qwebp plugins, which codec sources and revisions were selected, and were they linked statically or dynamically? Could you point us to the feature summaries and copyright materials for libjpeg-turbo, libtiff, libwebp, and any additional codecs or compression libraries built into those binaries?
4. Where can we find the full source, patch set, build recipe and applicable notice set for the wheel's software renderer `PySide6/opengl32sw.dll` (SHA-256 `18aedc7a4b610f53bcc7b7a5c5ed9293c7e86f030e3273ad54ed3bb1ebd36702`)? Its binary identifies Mesa 11.2.2. The signed SDK comparison file has SHA-256 `b04de4541863bc7d8879040a78889c4849c1b1da2784c4630f734c146c2998ce` and matching code/read-only data sections. We would like to confirm the Mesa and LLVM source revisions and patches for the wheel file specifically.
5. If full build logs are not public, is there a publicly accessible corresponding-source bundle or a release-specific component and license manifest that covers these binaries? Which team should we contact for any of the remaining components?

Thank you,  
IP Sentinel / 文东工作室

### Binary scope of the inquiry

PySide6/opengl32sw.dll, PySide6/plugins/generic/qtuiotouchplugin.dll, PySide6/plugins/iconengines/qsvgicon.dll, PySide6/plugins/imageformats/qgif.dll, PySide6/plugins/imageformats/qicns.dll, PySide6/plugins/imageformats/qico.dll, PySide6/plugins/imageformats/qjpeg.dll, PySide6/plugins/imageformats/qsvg.dll, PySide6/plugins/imageformats/qtga.dll, PySide6/plugins/imageformats/qtiff.dll, PySide6/plugins/imageformats/qwbmp.dll, PySide6/plugins/imageformats/qwebp.dll, PySide6/plugins/networkinformation/qnetworklistmanager.dll, PySide6/plugins/platforms/qdirect2d.dll, PySide6/plugins/platforms/qminimal.dll, PySide6/plugins/platforms/qoffscreen.dll, PySide6/plugins/platforms/qwindows.dll, PySide6/plugins/styles/qmodernwindowsstyle.dll, PySide6/plugins/tls/qcertonlybackend.dll, PySide6/plugins/tls/qopensslbackend.dll, PySide6/plugins/tls/qschannelbackend.dll, PySide6/pyside6.abi3.dll, PySide6/Qt6Core.dll, PySide6/Qt6Gui.dll, PySide6/Qt6Network.dll, PySide6/Qt6Svg.dll, PySide6/Qt6Widgets.dll, PySide6/QtCore.pyd, PySide6/QtGui.pyd, PySide6/QtNetwork.pyd, PySide6/QtWidgets.pyd, shiboken6/Shiboken.pyd, shiboken6/shiboken6.abi3.dll

Please identify LLVM linkage and the applicable license and notice files for every embedded dependency.

Submission channel: [Qt for Python bug reporting](https://wiki.qt.io/Qt_for_Python/Reporting_Bugs), PYSIDE project. Draft awaiting approval.
