---
prev: false
---

# Lab 0: Booting

**实验周期：1 周。** 请在本地完成实验，具体提交日期以本学期 elearning 作业为准。

本学期，我们将实现一个简单的操作系统内核。在 Lab 0 中，我们将配置好实验环境并完成 3 个实验任务。

## 1. 配置本地实验环境

先按照[本地环境配置](../guide/environment.md)准备 Linux 实验环境、AArch64 GNU 工具链、CMake、Make、Git 和 QEMU。Windows 可以使用 WSL2，macOS 可以使用本地 Linux 虚拟机；请在该 Linux 环境的终端中执行下文命令。

本课程使用 QEMU 模拟 AArch64 四核机器，无需购买开发板。记录操作系统、CPU 架构和各工具版本，后续实验沿用同一环境。构建系统默认模拟 4 个 CPU、4 GiB 内存，请为本地环境预留相应资源，并保持课程的 QEMU 配置不变。

## 2. 配置代码仓库

代码仓库为 [rfieldsy/OS-26Fall-FDU](https://github.com/rfieldsy/OS-26Fall-FDU)。完整的个人仓库、身份设置、SSH/HTTPS 认证、冲突处理及后续实验衔接步骤见 [Git 实验流程](../guide/workflow.md)。以下命令均在本地执行。

### 克隆实验代码并记录基线

在自己存放课程项目的目录中执行；Git 的姓名和邮箱按 [Git 实验流程](../guide/workflow.md)配置为本人的信息。

```shell
git clone -o upstream -b lab0 https://github.com/rfieldsy/OS-26Fall-FDU.git
cd OS-26Fall-FDU
git switch -c lab0-dev
git tag lab0-start
git rev-parse lab0-start
```

`upstream` 指向课程框架，`lab0-dev` 用于自己的开发，`lab0-start` 记录开始实验时的代码。后续使用个人 Git 仓库时，将自己的仓库设为 `origin`，保留课程框架远端 `upstream`。

### 构建并运行内核

在仓库根目录执行：

```shell
cmake -S . -B build
cmake --build build --target qemu
```

首次运行时，三个任务尚未实现，未出现四核的 `Hello, world!` 输出属于正常现象。完成任务后，再次执行上述命令检查结果。使用默认 Makefile 生成器时，也可以在 `build` 目录中执行原有的 `cmake ..` 和 `make qemu`。

### 后续实验如何衔接

先提交本次实验并记录 `lab0-submit`。Lab 1 框架已包含 BSS 清零和新的多核初始化流程，因此直接从 `upstream/lab1` 开始；Lab 2 及以后再从本次课程框架建立新分支，并合并上一实验提交。**完成框架合并并解决冲突后，先记录下一实验的 `labN-start`，再开始本次任务。** 每个实验页给出对应命令；不要直接覆盖自己的历史实现，合并和提交规则见 [Git 实验流程](../guide/workflow.md)。

## 3. QEMU

本学期的实验将在 QEMU 模拟的 [virt 通用虚拟平台](https://www.qemu.org/docs/master/system/arm/virt.html) 上运行我们编写的内核。完成本地环境配置后，在仓库根目录执行 `cmake --build build --target qemu` 即可构建并运行内核。

> [!info]
>
> **QEMU 命令解析（不要求掌握）**
>
> 以下命令对应代码仓库的 QEMU 配置，需在已经构建成功的 `build` 目录中执行；通常直接使用上面的构建目标即可：
>
> ```shell
> qemu-system-aarch64 -machine virt,gic-version=3 \
>     -cpu cortex-a72 \
>     -smp 4 \
>     -m 4096 \
>     -nographic \
>     -monitor none \
>     -serial mon:stdio \
>     -global virtio-mmio.force-legacy=false \
>     -kernel src/kernel8.elf
> ```
>
> * `-machine virt,gic-version=3` 指定模拟的机器类型为 `virt`（QEMU 中用于模拟虚拟的 ARM 系统的标准平台）。 `gic-version=3` 指定要使用的全局中断控制器 (GIC) 的版本为 3，用于支持更现代的中断处理功能。
> * `-cpu cortex-a72` 指定模拟的 CPU 类型为 Cortex-A72（一款高性能的 ARMv8 处理器）。
> * `-smp 4` 表示要模拟 4 个 CPU 核心（即 4 个对称多处理单元），后续我们的实验将涉及 SMP 的内容。
> * `-nographic` 配置 QEMU 运行在无图形输出模式下，即所有的输入输出都通过命令行界面进行，而不是通过 GUI 窗口。
> * `-monitor none` 禁用 QEMU 的监控控制台（QEMU monitor），避免了干扰正常的输出流。
> * `-serial mon:stdio` 将虚拟机的串行端口绑定到标准输入输出（stdio），这意味着虚拟机的输出会显示在当前的终端窗口中，输入也来自终端。
> * `-global virtio-mmio.force-legacy=false` 配置 QEMU 中的 VirtIO 设备（VirtIO 是一种用于加速虚拟化设备的标准）。`virtio-mmio.force-legacy=false` 禁用 VirtIO MMIO 设备的传统模式，确保这些设备使用现代化的接口。
> * `-kernel src/kernel8.elf` 指定要加载的内核镜像文件 `build/src/kernel8.elf`。QEMU 会在虚拟机中启动这个内核，模拟其运行环境。



**`qemu` 的退出方法为： `Ctrl+A`，松开后按 `x`。**

## 4. AArch64

> AArch64 等价于 ARMv8 的 64 位指令集。

本学期的教学 OS 将运行在 AArch64 架构下。

绝大多数代码都使用 C 语言完成，部分代码需要使用汇编语言编写，建议简要了解（当然暂时用不到）：

* 指令手册：[Arm Architecture Reference Manual for A-profile architecture](https://developer.arm.com/documentation/ddi0487/latest/)。
* 各通用寄存器及其别名、函数调用约定、栈结构。
* 算术、访存、跳转等基本汇编指令。

## 5. 操作系统

本课程的先修课程包括但不限于**程序设计**，**计算机系统基础**，**计算机组成与体系结构**。

* **程序设计**中，我们学习了用 C 语言编写**用户态**程序。**用户态**这一概念是相较于操作系统的**内核态**而言的，本课程实验的重心即为内核态编程。在后续的实验中，我们将逐步理解（1）用户态/内核态的定义；（2）划分用户态/内核态的意义；（3）用户态与内核态的交互等问题。
* **计算机系统基础**与 **计算机组成与体系结构**中，我们初步认识了计算机系统中的各类硬件组成，如 CPU，内存，缓存，外设等等。操作系统内核的作用在于**管理并虚拟化（或者说抽象）这些资源** \[1]。在后续的实验中，我们将逐步理解虚拟化这一概念。
* 除此以外，一系列软件开发实践中的重要问题，如并发和持久化，也将由操作系统中的特定的机制或策略解决。

换而言之，操作系统是「硬件资源」与「用户态程序」的中间层，负责管理用户态程序对于硬件资源的访问（随着学习的深入，我们将对这一命题做出补充）。

## 6. Booting

在 `build` 目录中执行 `make qemu` 后，构建系统将自动编译操作系统内核并启动 QEMU 运行内核。下面我们将介绍本实验操作系统内核的启动流程。

### 入口：梦开始的地方

我们通过链接器脚本（请见第7节）指定内核的入口为 `_start` 函数（位于 `src/start.S`）。

> [!note]
>
> **为什么入口函数不是 `main` 函数？**
>
> 在学习用户态 C 语言编程时，我们认为 `main` 函数是程序的入口。然而，这一说法省略了编译层面的一些重要细节，编译器会在 `main` 函数插入一系列初始化代码，因而 `main` 函数不是函数严格意义上的入口（相关背景知识请自行回顾**计算机系统基础**）。同样，尽管我们的内核定义了 `main` 函数，我们仍需要将入口设为 `_start` 函数并完成一些必要的准备动作。
>
> 目前，我们无需深究 `_start` 函数中的细节，具体内容我们会在合适的时机提供解读文档。

### `main`：内核，启动！

`_start` 函数最终会跳转到 `main` 函数。在 `main` 函数中，我们将完成内核的初始化工作。至此，我们已经成功启动了我们的内核。

目前，`main` 函数中的主要内容是一个分支判断，其作用是区分 CPU 0 和其余核心的初始化逻辑。下面我们具体介绍之。

### 对称多处理器（SMP）

现代计算机广泛采用多处理器架构，感兴趣的同学可以在本地 Linux 环境中通过 `lscpu` 命令查看该环境的处理器信息。同样地，我们的内核运行在 QEMU 虚拟出来的 4 核机器上。这 4 个核心可以并发（或者说并行，在这里我们暂不严格区分这两个概念）地执行不同的指令流。

> [!warning]
>
> **注意**：以下内容可能理解难度较高，因此为了完成实验任务，请着重注意加粗字体。此外，欢迎在 Github Issues 区提出问题。随着本课程实验的进行，同学们将逐步加深对这些问题的理解。

在我们的实验平台上，机器启动时仅有一个核（CPU 0）处于唤醒状态。作为唯一一个唤醒的核心，其主要负责：

* 内核相关服务的初始化，例如 `uart_init` 用于初始化通信串口，UART 可用于输出数据，前面我们提到串行端口被绑定到了标准输入输出，**也就是说 `uart_*` 函数类似于过去所学的 `putchar` 等标准输入输出函数（相关函数请见`src/driver/uart.c`）**。`printk_init` 则用于初始化 `printk` 服务，**`printk` 更加类似于用户态编程中 `printf`，语法与效果也基本一致**。
* 唤醒其他核心，即 `smp_init`。

`main` 函数中的分支判断用于：

* CPU 0 启动核心，并完成一系列初始化动作，最后放行其他核心。
* 其余核心被 CPU 0 唤醒后，等待 CPU 0 完成初始化动作并放行。

> [!important]
> **任务 1**
>
> CPU 0 完成内核服务初始化后，打印 "Hello, world! (Core 0)" （提示：上面介绍了如何打印字符串）。
>
> **任务 2**
>
> 其余 CPU 被放行后，各自打印 "Hello, world! (Core \<cpuid>)" （提示：上面介绍了如何打印字符串）。
>
> [!info]
>
> **预期输出**（后面三行的顺序可变）
>
> ```shell
> Hello, world! (Core 0)
> Hello, world! (Core 2)
> Hello, world! (Core 3)
> Hello, world! (Core 1)
> ```

## 7. 链接器脚本

链接器脚本位于 `src/linker.ld`。

我们执行 `make qemu` 编译内核并启动QEMU，编译内核得到的产物是一个 ELF 文件。此 ELF 文件同我们之前用户态程序的 ELF 文件一样，具有 `text`，`rodata`，`bss` 等段，而链接器脚本规定了这些段在内存中的位置。

> [!caution]
>
> **复习**
>
> 如果对 ELF 文件的结构及上述 `text`，`rodata`，`bss` 等段的性质不熟悉，请复习 **计算机系统基础** 所学相关内容。

此外，链接器脚本还暴露了一系列符号，用于描述内存地址。举例如下：

```linker-script
PROVIDE(data = .);
.data : AT(ADDR(.data) - 0xFFFF000000000000) {
    *(.data)
    *(.data.*)
}
PROVIDE(edata = .);
```

这一段链接器脚本的含义是：

* 暴露一个 `data` 符号，标识当前地址（`.`），即此时内存布局中 `.data` 段的起始地址。
* 定义一个 `.data` 段，其中包含所有 `.data` 和以 `.data.` 开头的子段。这个段放置在内存中的特定位置，并且其起始地址由 `AT` 子句指定。 `AT` 子句的含义暂不要求掌握。
* 在 `.data` 段的内容被分配后，再暴露一个 `edata` 符号，标识 `.data` 段结束时的地址。

**也就是说，`data` 标志了 `data` 段 的开始，`edata` 标志了 `data` 段 的结束。** 在 `main` 函数中，我们可以通过以下方式获得 `data` 和 `edata` 的地址：

```c
extern char data[], edata[];
printk("data is %p; edata is %p", (void*)data, (void*)edata);
```

> [!important]
>
> **任务 3**
>
> 按照惯例 BSS 段应当置零（为什么？请复习计算机系统基础或咨询助教）。然而，当操作系统内核被装载到内存中时，BSS 段对应的内存无法保证是置零状态（因为很多时候没有比操作系统更高一级的有关方面来负责“打扫”内存，此时操作系统内核本身就是内存的管理者）。因此，请在CPU 0 进行内核初始化前增加**清零 BSS 段**的逻辑。
>
> **提示 1**: 清零 BSS 段首先需要获取 BSS 段起始和终止的地址，上面已经演示了如何获取某段的起始和终止地址。
>
> **提示 2**: 查找 `memset` 函数，使用此函数清零一段连续的内存空间。

## 参考资料

1. Arpaci-Dusseau, R. H., & Arpaci-Dusseau, A. C. (2018). Operating systems: Three easy pieces.

## 8. 实验报告与提交

本实验必须提交实验报告。在 elearning 对应作业中上传 `学号-lab0.pdf`，本次只交 PDF 报告，无需上传代码；沿用原安排，Lab 0 报告不单独计分。请保留本地代码和 Git 记录，后续实验需要继续使用。具体日期和迟交安排以本学期 elearning 作业说明为准。

报告必须包括：

1. **实验环境与版本**：本地系统和架构、工具版本、`lab0-start` 与最终提交的完整 commit hash。
2. **实验思路**：分别说明任务 1、2、3 的实现思路，以及 CPU 0 初始化、放行其他核心和清零 BSS 的顺序。
3. **实现方式**：列出修改过的文件、关键函数和使用的链接器符号，解释 BSS 地址范围及清零原因。可以用少量关键代码或流程图，不需要粘贴大段代码。
4. **实验结果与测试**：给出构建和运行命令、四个核心的实际输出与截图/日志，说明为什么后三个核心的输出顺序可以不同；如有失败，记录现象、定位过程和修复结果。
5. **问题回答与总结**：回答本页任务和提示中的问题，说明遇到的困难、解决方法和仍存在的问题。

在仓库根目录检查修改后记录完成版本：

```shell
git status --short
git add -A
git diff --cached --stat
git commit -m "Complete Lab 0"
git tag lab0-submit
git rev-parse lab0-start
git rev-parse lab0-submit
```

只暂存实验源码及必要配置；不要加入构建产物、磁盘镜像或个人凭据。若已经提交了全部修改，跳过 `git commit`。标签只在首次完成时创建，重新提交的版本记录方法见[统一提交规范](../guide/submission.md)。
