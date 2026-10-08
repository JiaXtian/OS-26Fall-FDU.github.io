---
prev: false
---

# Lab 0: Booting

**实验周期：1 周。** 请在本地完成实验，最晚提交日期：10月16日 23:59:59。

本学期，我们将实现一个简单的操作系统内核。在 Lab 0 中，我们将配置好实验环境并完成 3 个实验任务。

## 1. 配置本地实验环境

本实验使用 **Ubuntu 24.04 LTS**，通过 QEMU 模拟 AArch64 四核机器。按自己的操作系统选择下面一种方式，完成后统一进入 Ubuntu 终端安装实验工具。

建议为 Ubuntu 环境分配 4 个可用逻辑核、8 GiB 内存、40 GiB 磁盘，并为宿主系统保留足够资源。课程 QEMU 配置使用 4 核、4 GiB 内存，保持代码中的配置即可；不需要 ARM 开发板或嵌套虚拟化。

### 1.1 Linux

已安装 Ubuntu 24.04 LTS 的同学可以直接打开终端，进入第 1.4 节。使用其他发行版的同学可自行安装等价依赖，也可安装 VMware Workstation 并创建 Ubuntu 虚拟机，以便采用本页相同的命令。VMware 的下载入口和 Ubuntu 安装步骤见下一节。

### 1.2 Windows

**方式一：WSL2（推荐）**

适用于 Windows 11，或 Windows 10 2004（内部版本 19041）及以上版本。按以下步骤安装：

1. 以管理员身份打开 PowerShell，执行：

   ```powershell
   wsl --install -d Ubuntu-24.04
   ```

2. 根据提示重启电脑，打开开始菜单中的 Ubuntu，设置 Linux 用户名和密码。输入密码时终端不显示字符，这是正常现象。
3. 在 PowerShell 中确认 Ubuntu 使用 WSL2：

   ```powershell
   wsl -l -v
   ```

   对应发行版的 `VERSION` 应为 `2`。如果为 `1`，执行 `wsl --set-version Ubuntu-24.04 2`；若发行版名称不同，以列表中的实际名称为准。
4. 此后从开始菜单打开 Ubuntu，在 **Ubuntu 终端**中执行第 1.4 节及实验命令。把项目放在 `~/os-course`，避免放在 `/mnt/c` 下。

安装遇到问题时，参考 [Microsoft 官方 WSL 中文安装教程](https://learn.microsoft.com/zh-cn/windows/wsl/install)。如提示不支持虚拟化，按该教程检查系统组件及 BIOS/UEFI 的硬件虚拟化设置。

**方式二：VMware Workstation + Ubuntu**

适用于 Intel/AMD 的 x86-64 Windows 电脑。希望使用完整 Ubuntu 桌面的同学可以选择此方式，无需同时安装 WSL2。

1. 按 [VMware 官方下载说明](https://knowledge.broadcom.com/external/article/368667/download-and-license-information-for-vmw.html)注册或登录 Broadcom 账户，下载适用于 Windows 的 Workstation Pro，运行安装程序。
2. 从 [Ubuntu 24.04 LTS 官方镜像目录](https://releases.ubuntu.com/24.04/)下载文件名包含 `desktop-amd64.iso` 的桌面镜像；这里的 AMD64 同时适用于 Intel 和 AMD 的 x86-64 处理器。
3. 在 Workstation 中新建虚拟机，选择下载的 ISO，操作系统选择 Ubuntu 64-bit。按本节开头的建议分配 CPU、内存和虚拟磁盘，网络选择 NAT。
4. 启动虚拟机，按安装向导安装 Ubuntu、创建用户名和密码。安装器中的磁盘选项作用于新建的虚拟磁盘。完成后重启，按提示断开安装 ISO，进入已安装的 Ubuntu。
5. 打开 Ubuntu 的终端，继续第 1.4 节。项目保存在虚拟机的 Linux 家目录中。

图文操作可参考 [CSDN：VMware 安装 Ubuntu 24.04 桌面版](https://openeuler.csdn.net/6a154719662f9a54cb7724ab.html)。

### 1.3 macOS：VMware Fusion + Ubuntu

macOS 用户也需要在 **Ubuntu 虚拟机内**完成实验。确认芯片类型，再选择对应镜像：

| Mac 类型 | Ubuntu 镜像 | 官方下载 |
| --- | --- | --- |
| Apple Silicon（M 系列芯片） | ARM64 桌面镜像，文件名包含 `desktop-arm64.iso` | [Ubuntu 24.04 LTS ARM64](https://cdimage.ubuntu.com/ubuntu/releases/24.04/release/) |
| Intel Mac | AMD64 桌面镜像，文件名包含 `desktop-amd64.iso` | [Ubuntu 24.04 LTS AMD64](https://releases.ubuntu.com/24.04/) |

Apple Silicon 上的 Fusion 需要 ARM64 客户机，不能使用 AMD64 镜像，详见 [VMware 官方架构说明](https://knowledge.broadcom.com/external/article/315602)。

1. 按 [VMware 官方下载教程](https://knowledge.broadcom.com/external/article/368667/download-and-license-information-for-vmw.html)登录 Broadcom，下载支持自己 macOS 版本的 **Fusion Pro**。打开下载的安装包，按提示安装并允许必要的系统权限；当前免费版本无需购买许可证。
2. 下载上表中与 Mac 芯片匹配的 Ubuntu ISO。打开 Fusion，新建虚拟机，选择“从光盘或镜像安装”（Install from disc or image），选中该 ISO。
3. 确认系统类型为相应架构的 Ubuntu。保存前自定义设置，按本节开头的建议分配 CPU、内存和虚拟磁盘；网络使用“与我的 Mac 共享”（NAT）。Apple Silicon 保持默认 UEFI 固件。
4. 启动虚拟机，按照 Ubuntu 安装向导安装到新建的虚拟磁盘，并设置用户名和密码。安装完成后重启，按提示断开 ISO，进入 Ubuntu 桌面。
5. 在 **Ubuntu 的终端**中执行第 1.4 节和后面的实验命令，不要在 macOS 的 Terminal 中执行这些命令。项目放在 Ubuntu 家目录，不放在 macOS 共享文件夹中。

### 1.4 在 Ubuntu 中安装工具

以下命令对上面三种系统入口相同。在 Ubuntu 终端执行：

```shell
sudo apt update
sudo apt install -y build-essential git cmake python3 \
  gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu \
  qemu-system-arm gdb gdb-multiarch dosfstools mtools fdisk
```

`build-essential` 提供 GNU 编译器和 Make，`qemu-system-arm` 提供 `qemu-system-aarch64`。在 x86-64 Ubuntu 中，框架使用 `aarch64-linux-gnu-*` 交叉工具链；在 ARM64 Ubuntu 中，框架使用原生 GNU 工具链。Lab0 的构建目标还会生成镜像，因此需要 `dosfstools`、`mtools`、`fdisk` 提供的 `mkfs.vfat`、`mcopy`、`sfdisk`。

安装完成后检查：

```shell
uname -m
git --version
cmake --version
gcc --version
qemu-system-aarch64 --version
command -v aarch64-linux-gnu-gcc aarch64-linux-gnu-ld
command -v mkfs.vfat mcopy sfdisk python3
```

版本命令应正常输出版本号，`command -v` 应输出对应工具路径。记录自己的系统架构和工具版本，用于实验报告。

## 2. 获取 Lab0 代码并运行

在 Ubuntu 终端执行以下命令，下载 [课程实验代码](https://github.com/rfieldsy/OS-26Fall-FDU) 的 `lab0` 分支，并创建自己的本地工作分支：

```shell
mkdir -p ~/os-course
cd ~/os-course
git clone -o upstream -b lab0 https://github.com/rfieldsy/OS-26Fall-FDU.git
cd OS-26Fall-FDU
git switch -c lab0-dev
```

`upstream` 为课程代码仓库本地名称；`lab0-dev` 是自己修改 Lab0 的分支。再次开始实验时，进入已有目录即可：

```shell
cd ~/os-course/OS-26Fall-FDU
git status
```

确认当前分支是 `lab0-dev`。如果已创建该分支但当前不在其上，先保存当前分支的修改，再执行 `git switch lab0-dev`，不要重复克隆或创建分支。

### 构建并运行内核

在上述代码仓库根目录执行：

```shell
cmake -S . -B build -G "Unix Makefiles"
cmake --build build --target qemu
```

构建目录固定为仓库根目录下的 `build`，因为镜像脚本使用这一相对路径；项目路径不要包含空格。构建和运行 QEMU 不需要 `sudo`。

首次运行时，三个任务尚未实现，未出现四核的 `Hello, world!` 输出属于正常现象。完成任务后，再次执行构建和运行命令检查结果。退出 QEMU 时，先按 `Ctrl+A`，松开后按 `x`。使用上述 Makefile 生成器时，在 `build` 目录运行 `make qemu` 也可启动内核。

如果出现 `command not found`，先确认正在 Ubuntu 中操作，并重新检查第 1.4 节对应工具；如果镜像生成时找不到文件，确认当前位于仓库根目录、构建目录名为 `build`，且项目路径不含空格。

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

### 入口：

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
> 按照惯例 BSS 段应当置零（为什么？请尝试查询资料回答该问题）。然而，当操作系统内核被装载到内存中时，BSS 段对应的内存无法保证是置零状态（因为很多时候没有比操作系统更高一级的有关方面来负责“打扫”内存，此时操作系统内核本身就是内存的管理者）。因此，请在CPU 0 进行内核初始化前增加**清零 BSS 段**的逻辑。
>
> **提示 1**: 清零 BSS 段首先需要获取 BSS 段起始和终止的地址，上面已经演示了如何获取某段的起始和终止地址。
>
> **提示 2**: 查找 `memset` 函数，使用此函数清零一段连续的内存空间。


## 8. 实验报告与提交

每位同学必须在 elearning 对应作业中提交 **`学号-lab0.pdf` 实验报告**。具体提交日期和迟交安排以本学期 elearning 作业说明为准。沿用原安排，Lab0 报告不单独计分。

报告必须包括：

1. **实验环境**：操作系统、CPU 架构、编译器、CMake 和 QEMU 版本，以及实际使用的运行环境（原生 Ubuntu、WSL2 或虚拟机）。
2. **实验思路**：分别说明任务 1、2、3 的实现思路，以及 CPU 0 初始化、放行其他核心和清零 BSS 的顺序。
3. **实现方式**：列出修改过的文件、关键函数和使用的链接器符号，解释 BSS 地址范围及清零原因。
4. **实验结果与测试**：给出构建和运行命令、四个核心的实际输出与截图/日志，说明为什么后三个核心的输出顺序可以不同；如有失败，记录现象、定位过程和修复结果。
5. **问题回答与总结**：回答本页任务和提示中的问题，可说明遇到的困难、解决方法和仍存在的问题。

报告可以使用流程图、伪代码或少量关键代码，不需要粘贴大段源码，但必须清楚说明实验思路、实现方式和实验结果。未完成内容、未通过测试及已知问题应如实记录。

## 参考资料

1. Arpaci-Dusseau, R. H., & Arpaci-Dusseau, A. C. (2018). Operating systems: Three easy pieces.