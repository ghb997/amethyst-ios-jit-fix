# Amethyst 5.1.0 JIT 启动修复构建

此仓库为 Amethyst iOS 5.1.0 的候选 JIT 修复提供公开补丁和 GitHub Actions IPA 构建流程。
流程会下载固定版本的上游源码，校验并应用补丁，再构建含 Java 8、17、21、25 的完整标准 IPA。

## 获取 IPA

1. 打开 [Actions](https://github.com/ghb997/amethyst-ios-jit-fix/actions/workflows/build-ipa.yml)。
2. 选择成功的构建，下载 **Amethyst-5.1.0-JIT-fix** artifact。
3. 解压 artifact，取出 `Amethyst-5.1.0-JIT-fix.ipa`，使用自己的侧载工具签名安装。

IPA 只有构建所需的临时签名，不含个人开发者证书。安装后仍需通过 StikDebug 开启 JIT。
产物保留 30 天；可以在 Actions 页面使用 **Run workflow** 重新构建。
`SHA256SUMS.txt` 和 `verification.json` 用于核对下载完整性与打包内容。

## 修复的问题

在需要调试器辅助 JIT 映射的设备上，进程的 `CS_DEBUGGED` 标记并不保证 JIT 脚本仍在线。
上游启动前的重连判断额外要求 `JIT_FLAG_HAS_TXM`，与 JVM 实际使用的
`DeviceNeedsDebugJITMapping()` 条件不一致。因此部分非 TXM 设备可能跳过脚本重连，
随后出现 `JIT26CreateRegionLegacy returned NULL` / `debugger not servicing brk`。

补丁修改 4 个 Objective-C 文件：

- 7 个启动检查统一使用 JVM 的映射能力判断，覆盖非 TXM 设备。
- 启动前及等待 JIT 后刷新能力缓存。
- JIT 状态显示覆盖同一组设备；日志不再把置位的 JIT 标记直接称为在线调试器。
- 保留脚本禁用偏好、原有 StikDebug 脚本请求以及最终 JVM 断点握手检查。

这是一项针对已确认条件漏判的候选修复。上游的 `JIT26IsLikelyDebuggerKeepAttached()`
仍是启发式检测，可能把已附加但没有正确脚本的调试器识别为在线。
编译与打包通过不等于 StikDebug 真机行为已验证。

## 真机验证

每次测试前彻底关闭 Amethyst，使用新进程分别测试：

1. 先从 StikDebug 启动 Amethyst，再启动游戏。
2. 先打开 Amethyst，让启动器自动跳转 StikDebug，返回后启动游戏。
3. 检查 JAR 与 Forge/NeoForge 安装入口是否仍可正常运行。

若第一种顺序仍失败，应结合新日志和 StikDebug 脚本日志进一步判断实际握手结果。
已知可用的临时方式是第二种启动顺序。

## 来源与构建

- 上游：[herbrine8403/Amethyst-iOS-MyRemastered](https://github.com/herbrine8403/Amethyst-iOS-MyRemastered)
- 基础版本：`5.1.0`
- 固定提交：[`70b8bea76a0ac97483b3e86b54330dfef948cb07`](https://github.com/herbrine8403/Amethyst-iOS-MyRemastered/tree/70b8bea76a0ac97483b3e86b54330dfef948cb07)
- 补丁：[jit-startup-order.patch](jit-startup-order.patch)
- 原始及修改后文件校验值：[manifest.json](manifest.json)
- 构建配置：[build-ipa.yml](.github/workflows/build-ipa.yml)

macOS 14、Xcode 15.4、GNU Make、Java 8 和 ldid 与上游已成功的构建配置一致。
`BUILD_MOBILEGL=0` 使用上游提交中已有的两个 MobileGL 渲染器二进制。
Git LFS 下载被跳过：上游缺失的 trace replay 图片属于测试资料，iOS 构建不使用它。
两个失效的子模块 URL 分别映射到 `immago/DBNumberedSlider` 和 `facebook/fishhook`。
镜像中已核实存在相同的固定提交；依赖版本不变，详情记录在 `manifest.json`。
Java 运行时仍从上游 Makefile 指定的网址下载；因此固定源提交并不保证逐字节可复现。

Actions 会检查补丁前后 SHA-256、IPA ZIP 完整性、主程序中的新诊断字符串、JIT 脚本、
Java 启动器和 4 个 Java 运行时，并上传 dSYM 与构建日志用于排查问题。
上游源代码及补丁沿用 [GNU GPL v3](LICENSE)，第三方组件保留各自许可证。
