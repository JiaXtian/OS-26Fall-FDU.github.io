---
next: false
---

# 操作系统课程实验

复旦大学 **2026 年秋季学期《操作系统（H）》**课程配套实验。我们将从内核启动开始，逐步完成内存管理、内核态与用户态进程、同步互斥、块设备驱动和文件系统，最终启动 shell。

**当前已发布： [Lab0 · Booting](./lab/lab0.md)。** 其余实验将按课程进度开放。

## 开始实验

1. 按[本地实验环境](./guide/environment.md)准备 Linux、GNU 工具链与 QEMU。
2. 按[Git 工作流](./guide/workflow.md)获取 [2026 实验代码](https://github.com/rfieldsy/OS-26Fall-FDU)，进入对应实验分支。
3. 阅读 [Lab0](./lab/lab0.md)，完成任务并按[提交规范](./guide/submission.md)提交报告。

所有实验在本地完成。每次实验都必须提交报告，具体提交时间以本学期 eLearning 作业公告为准。

## 实验安排

下表为 13 周的相对进度安排，具体教学周由课程公告确定。

| 实验 | 内容 | 周期 | 相对进度 | 状态 |
| --- | --- | --- | --- | --- |
| [Lab0 · Booting](./lab/lab0.md) | 配置并启动操作系统内核 | 1 周 | 第 1 周 | 已发布 |
| Lab1 · Memory Allocator | 实现物理内存的分配管理 | 2 周 | 第 2–3 周 | 待发布 |
| Lab2 · Process (Kernel Part) | 实现内核态的进程管理 | 2 周 | 第 4–5 周 | 待发布 |
| Lab3 · Process (User Part) | 实现用户态页表和上下文切换机制 | 2 周 | 第 6–7 周 | 待发布 |
| Lab4 · Condvar & VirtIO Driver | 理解同步互斥原语与初始化块设备驱动 | 1 周 | 第 8 周 | 待发布 |
| Lab5 · Logging File System | 实现磁盘管理与块缓存 | 1 周 | 第 9 周 | 待发布 |
| Lab6 · Inode-based FS | 实现基于 Inode 的文件系统 | 2 周 | 第 10–11 周 | 待发布 |
| LabFinal | 实现 Pipe、Console、ELF 加载等功能，最终启动 shell | 2 周 | 第 12–13 周 | 待发布 |

课程实验按上述顺序推进，后续实验依赖前序实现。请及时保存工作分支、完成版本与测试记录。
