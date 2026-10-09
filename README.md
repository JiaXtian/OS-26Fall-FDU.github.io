# 复旦大学操作系统（H）课程实验 · 2026 秋

本仓库维护课程实验文档。课程以 AArch64 为目标架构，使用 QEMU 运行教学内核，逐步完成内存管理、进程管理、设备驱动和文件系统，最终启动 shell。

- **在线实验文档**：[课程主页](https://jiaxtian.github.io/OS-26Fall-FDU.github.io/)
- **实验代码仓库**：[rfieldsy/OS-26Fall-FDU](https://github.com/rfieldsy/OS-26Fall-FDU)
- **开始实验**：[Lab0 · Booting](https://jiaxtian.github.io/OS-26Fall-FDU.github.io/lab/lab0)

## 实验安排

| 实验 | 内容 | 周期 |
| --- | --- | --- |
| Lab0 · Booting | 配置环境并启动内核 | 1 周 |
| Lab1 · Memory Allocator | 物理内存分配与管理 | 2 周 |
| Lab2 · Process (Kernel Part) | 内核态进程管理 | 2 周 |
| Lab3 · Process (User Part) | 用户态页表与上下文切换 | 2 周 |
| Lab4 · Condvar & VirtIO Driver | 条件变量与块设备驱动 | 1 周 |
| Lab5 · Logging File System | 磁盘管理与块缓存 | 1 周 |
| Lab6 · Inode-based FS | 基于 Inode 的文件系统 | 2 周 |
| LabFinal | Pipe、Console、ELF 加载与 shell | 2 周 |


## 文档维护

实验 Markdown 位于 `docs/lab/`，站点使用 VitePress。安装 Node.js 22 后，在本仓库根目录执行：

```shell
npm ci
npm run docs:dev
```

使用 `npm run docs:build` 构建静态站点。推送到 `main` 后，GitHub Actions 会自动部署到 GitHub Pages；
