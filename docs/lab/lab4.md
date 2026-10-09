# Lab 4: Condvar & VirtIO Driver

建议用时：**1 周**。先完成条件变量练习，再完成块设备驱动的三个原有任务。

到目前为止，我们已经实现了内核的一些重要组件：内存分配、内核/用户进程、页表等。从这个 Lab 开始，我们将关注操作系统中的持久化问题，最终实现一个功能较为完善的文件系统。

## 1. 本地准备与条件变量

### 1.1 准备内核代码

本实验在已完成的 `lab3-dev` 基础上，引入课程 `lab4` 框架；需要保留自己的前序实现。 使用 [Lab0 中配置的 Ubuntu 环境](./lab0.md#_1-配置本地实验环境)，在 Linux 终端操作。

首次开始本实验时，先回到原有仓库，确认当前位于已完成的 `lab3-dev` 分支：

```shell
cd ~/os-course/OS-26Fall-FDU
git status
```

若 `git status` 显示有源码修改，先保存到当前分支；如果提示工作区干净（working tree clean），跳过这两条命令。执行前确认修改列表中只有需要保留的源码和配置。

```shell
git add -A
git commit -m "Save lab3 work"
```

确认工作区干净后，获取课程框架并创建本次工作分支：

```shell
git fetch upstream
git switch -c lab4-dev upstream/lab4
git merge lab3-dev --no-edit
```

如果提示合并冲突，运行 `git status` 查看文件；打开这些文件，处理 `<<<<<<<`、`=======`、`>>>>>>>` 标记间的内容，同时保留自己的实现和本次框架的新接口、初始化流程、测试。去掉冲突标记并保存后执行：

```shell
git add -A
git commit -m "Resolve lab4 merge conflicts"
```

没有冲突时无需执行以上两条命令。不要直接用一方文件覆盖所有冲突。

以上获取框架的步骤只执行一次。已经开始本实验时，在工作区干净的前提下用 `git switch lab4-dev` 返回本次分支，继续修改即可，无需重新创建或合并。

### 1.2 条件变量练习（沿用 Lab 4.1）

本部分沿用往年 Lab 4.1 的独立 [Condvar 练习仓库](https://github.com/Boreas618/Condvar)，在本地 Linux 环境中运行普通的 C/Pthreads 程序。该练习与内核代码放在两个并列目录中；内核 `lab4` 分支不包含本练习的 `main.c`，也没有它的 `make check` 目标。

在存放课程项目的目录中执行（与内核仓库并列）：

```shell
cd ~/os-course
git clone https://github.com/Boreas618/Condvar.git
cd Condvar
```

本实验主要用于帮助大家熟悉一类典型的同步互斥原语——条件变量。后续的实验中，我们将大量使用条件变量及其变体。

本实验中我们将利用条件变量实现一个极简的 Redis（一种用于存储键值对的内存数据库）。`server` 维护键为 `[0, 499]`、值为 email 地址的内存数据库；32 个 `client` 分别发起 2000 次随机查询，通过共享 buffer 交付请求并读取响应。这里的 `client` 和 `server` 是同一个本地程序内的 **Pthreads 线程**，不需要网络连接。源程序的共享 buffer 有 6 个槽位。

一次请求的流程与原练习一致：

1. `client` 在互斥锁保护下寻找 `status == 0` 的空槽，写入 key，将状态设为 `1`（请求等待处理）。
2. `server` 扫描共享 buffer，处理 `status == 1` 的请求，写入对应 value，将状态设为 `2`（响应完成），通知等待该槽位的 `client`。
3. `client` 等待响应完成后读取 value，按源码注释中的格式写入自己的 `out00.txt` 至 `out31.txt` 日志，再把槽位归还为 `status == 0`。

条件变量负责唤醒等待者，共享状态负责记录条件是否成立。以父线程等待子线程完成为例：

```c
#include <pthread.h>

int done = 0;
pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t c = PTHREAD_COND_INITIALIZER;

void thread_exit(void) {
    pthread_mutex_lock(&m);
    done = 1;
    pthread_cond_signal(&c);
    pthread_mutex_unlock(&m);
}

void thread_join(void) {
    pthread_mutex_lock(&m);
    while (done == 0)
        pthread_cond_wait(&c, &m);
    pthread_mutex_unlock(&m);
}
```

注意以下三点：

* **先检查条件，再决定是否等待。** `signal` 不为未来的等待者保存通知。如果子线程已经设置 `done = 1`，父线程应直接继续执行；不能不检查状态就进入等待。
* **用同一把锁保护条件。** `pthread_cond_wait` 在调用者持有互斥锁时，原子地释放锁并进入等待，返回前重新取得这把锁。不能把它简单拆成“解锁，再睡眠”两个无保护的步骤，否则通知可能落在二者之间，造成丢失唤醒。
* **使用 `while` 重新检查。** 被唤醒不代表条件仍然满足：线程重新取得锁之前，其他线程可能改变共享状态，也可能出现虚假唤醒。上例等待条件是 `done == 0`，能够继续执行的条件是 `done == 1`。这是对往年 PDF 中条件方向笔误的澄清。有关等待与通知的进一步说明见 [OSTEP 第 30 章](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-cv.pdf)。

> [!important]
> **条件变量任务（原 Lab 4.1）**：依照上述介绍与项目中的注释完成 `main.c` 的 todo 处内容。完成后 `make check` 验证程序正确性。

原练习的任务、请求规模和输出格式保持不变。完成 TODO 时，还需处理原骨架中与运行正确性直接相关的三处问题：

* 读取数据库时，确保传给 `getline` 的每个行缓冲区指针初始为 `NULL`，并正确初始化对应容量。不能将未初始化的指针交给 `getline`。
* `server` 总共处理 `NUM_THREADS * REQUESTS_PER_THREAD` 个请求；处理完后应退出，不应因原来的 `<=` 循环条件再等待一个不存在的请求。
* 主线程在销毁互斥锁和条件变量前，应等待 `server_thread` 结束；所有线程结束前不可销毁仍可能使用的同步对象。

这些是原有骨架的运行勘误，不增加查询操作或新的内核接口。练习使用本地 C 编译器、Make 和 Python 3；在 `Condvar` 目录中运行：

```shell
make check
wc -l out*.txt
```

未完成的骨架包含 `exit(1)`，此时 `make check` 失败是预期现象。完成后应看到检查脚本输出 `PASS`，并确认 **32 个日志文件各有 2000 行，共 64000 行**。原 `check.py` 只核对已有记录的查询结果，不检查记录总数，因此仅看到 `PASS` 不足以证明请求全部完成。在实验报告中保留检查输出和行数统计。

### 1.3 从条件变量到块设备等待

接下来回到内核仓库的 `lab4-dev` 分支。Pthreads 条件变量是宿主环境提供的接口，不能直接在本实验内核中调用。内核已有 `src/common/sem.h` 中的 `Semaphore`、`wait_sem` 与 `post_sem`，本实验继续沿用它们完成 I/O 等待与通知，不要求新增一套内核条件变量接口。

与条件变量不同，信号量可以保存一次提前到达的通知。仍需明确“哪个请求已经完成”、保护相应共享状态，并处理唤醒后的重新检查。当前 `src/common/buf.h` 已有 `Buf.sem`；`virtio_blk_rw` 已将其初始化为 0，继续使用即可。等待过程中要让中断处理函数能够取得 `disk.lk`，否则等待者与中断处理函数会互相阻塞。请结合 `sem.c` 理解 `wait_sem` 的返回值，不能把任意一次返回都当成设备完成。

## 2. I/O 框架

硬盘、SD卡等一类设备都是块设备。块设备的特点是数据的读写以块（block）为单位，一次性读取或写入固定大小的数据块。为了实现对块设备的高效管理和操作，操作系统通常会提供一个 I/O 框架，用于抽象和管理这些块设备的访问。

在现代操作系统中，I/O 框架主要分为同步 I/O 和异步 I/O 两种模式。同步 I/O 会阻塞调用的进程，直到 I/O 操作完成。而异步 I/O 则允许进程发起 I/O 操作后立即返回，不会阻塞进程的执行流，从而提高系统的并发度。在本实验中，我们将重点关注同步 I/O 的实现。

这里的 `virtio_blk_rw` 对调用者提供同步接口：调用者等待设备完成后才返回；设备与 CPU 之间则通过异步请求和中断协作，等待期间其他进程可以运行。这也是往年 PDF 使用“异步 I/O”标题而在线文档描述“同步 I/O”的原因，二者描述的是不同层次。

I/O 的基本逻辑如下：

* **读**：块设备驱动向设备发送读请求和目标地址，然后等待请求完成。此时发起请求的进程可以休眠，调度器可以调度其他进程（异步）。请求完成后，内核通知休眠进程读请求已完成，数据已准备好。
* **写**：块设备驱动向设备发送写请求、目标地址以及待写入的数据，等待直到设备完成写入。

> [!important]
> **思考**：对于写操作，你能设计出一种机制，让我们无需等待中断，且不会引发一致性问题吗？即 A 发起了写 DATA 到 ADDR 请求后立刻返回，不等待写操作完成，此时 B 读 DATA 可以读出 A 刚刚写入的内容。

### 2.1 本实验具体逻辑

本实验 I/O 的具体逻辑如下：

<figure><img src="/assets/lab4-1.png" alt=""><figcaption></figcaption></figure>

1. 进程调用 `virtio_blk_rw` 向块设备驱动发起读写请求。
2. 块设备驱动（即上述 `virtio_blk_rw`）通过相关接口控制设备。在我们的实验中，块设备驱动主要通过读写特殊寄存器的方式（memory-mapped I/O）来控制设备。
3. 块设备驱动发起请求后，进程休眠，等待请求的完成。我们的内核中并没有提供条件变量，需要我们使用 `Semaphore` 替代条件变量。
4. 经过一段时间后，设备完成读写请求。
5. 设备发起中断，块设备驱动中的中断处理函数处理此中断。
6. 块设备驱动中的中断处理函数**通知**进程请求已完成（即唤醒进程）。

## 3. 设备：`virtio-blk-device`

`virtio-blk-device` 是我们实现块设备驱动的核心。

> [!info]
> **实验平台**
>
> 本课程使用 QEMU 的 `virt` 平台和 VirtIO 块设备，以便聚焦 I/O 请求、等待与中断通知的核心逻辑。

VirtIO 是一种现代化的虚拟设备接口，它广泛用于虚拟机中，以提供高效的 I/O 设备模拟。本实验中，我们将利用 `virtio-blk-device` 作为我们的块设备。这意味着我们的块设备是一个虚拟的块设备，块设备内的数据由宿主机共同提供。

由于 VirtIO 是一种虚拟设备接口，前端/后端的概念由此引出：

* **前端**：即我们的块设备驱动。
* **后端**：QEMU、KVM 等宿主机组件的逻辑，负责处理内核（运行在 QEMU 虚拟环境中）中的块设备驱动发起的读写请求。

前端和后端通过共享内存交互，前端的块设备驱动向共享内存里写入读写请求，后端的逻辑从共享内存里读出读写请求并处理，将处理结果提供给前端。

前端与后端的共享内存被称为 `virtqueue`（虚拟队列）。对于块设备，VirtIO 使用一个或多个队列来管理请求。每个virtqueue都包含3张表， `Descriptor Table` 存放了 I/O 请求描述符，即I/O 请求的基本信息，`Available Ring` 记录了当前哪些描述符是可用的， `Used Ring` 记录了哪些描述符已经被后端使用了 \[1]。

```
                          +------------------------------------+
                          |       virtio  guest driver         |
                          +-----------------+------------------+
                            /               |              ^
                           /                |               \
                          put            update             get
                         /                  |                 \
                        V                   V                  \
                   +----------+      +------------+        +----------+
                   |          |      |            |        |          |
                   +----------+      +------------+        +----------+
                   | available|      | descriptor |        |   used   |
                   |   ring   |      |   table    |        |   ring   |
                   +----------+      +------------+        +----------+
                   |          |      |            |        |          |
                   +----------+      +------------+        +----------+
                   |          |      |            |        |          |
                   +----------+      +------------+        +----------+
                        \                   ^                   ^
                         \                  |                  /
                         get             update              put
                           \                |                /
                            V               |               /
                           +----------------+-------------------+
                           |	   virtio host backend          |
                           +------------------------------------+
```

在我们的实验中，`virtqueue` 定义如下：

```c
struct virtq {
    struct virtq_desc *desc;
    struct virtq_avail *avail;
    struct virtq_used *used;
    u16 free_head;
    u16 nfree;
    u16 last_used_idx;

    struct {
        volatile u8 status;
        volatile u8 done;
        u8 *buf;
    } info[NQUEUE];
};
```

## 4. 块设备驱动

块设备驱动中发起读写请求的函数是：

```c
int virtio_blk_rw(Buf *b);
```

其中，`Buf *b` 是一个缓冲区指针，表示要进行 I/O 操作的数据块缓冲区。`virtio_blk_rw` 将依据 `b` 的各字段（如 `data` 是块对应的数据，`block_no` 是该块在硬盘上的编号等，`b->flags & B_DIRTY` 非零表示是一个写请求），配置上述的 `Descriptor Table` 和 `Available Ring`，向设备发起请求。

块设备驱动中处理中断的函数是：

```c
static void virtio_blk_intr();
```

其负责读取 `Used Ring` 并通知相关进程 I/O 操作已完成，数据已准备好。

此外，我们需要利用好 `disk.virtq.info[d0]` 以进行块设备驱动与设备间的同步。

## 5. 制作启动盘

现代操作系统通常是作为一个硬盘镜像来发布的，我们的也不例外。但由于历史原因，我们的实验在制作镜像时遵循树莓派的规则，即第一个分区为启动分区 （boot partion），文件系统必须为 FAT32，剩下的分区可由我们自由分配。为了简便，我们采用主引导记录（[Master boot record, MBR](https://en.wikipedia.org/wiki/Master_boot_record)） 来进行分区，第一个分区和第二个分区均约为 64 MB，第二分区是根目录所在的文件系统（我们后续需要实现文件系统管理这个分区）。简言之，SD 卡上的布局如下

```
 512B            FAT32      后续实现的文件系统
+-----+-----+--------------+----------------+
| MBR | ... | boot partion | root partition |
+-----+-----+--------------+----------------+
 \   1MB   / \    64MB    / \     63MB     /
  +-------+   +----------+   +------------+
```

### 5.1 MBR

MBR 位于设备的前 512 Byte，有多种格式，不过大同小异，一种常见的格式如下表：

| Address | Description                              | Size (bytes) |
| ------- | ---------------------------------------- | ------------ |
| 0x0     | Bootstrap code area and disk information | 446          |
| 0x1BE   | Partition entry 1                        | 16           |
| 0x1CE   | Partition entry 2                        | 16           |
| 0x1DE   | Partition entry 3                        | 16           |
| 0x1EE   | Partition entry 4                        | 16           |
| 0x1FE   | 0x55                                     | 1            |
| 0x1FF   | 0xAA                                     | 1            |

但这里我们只需要获得第二个分区的信息，即上表中的 Partition entry 2，这 16B 中有该分区的具体信息，包括它的起始 LBA 和分区大小（共含多少块）如下：

| Offset (bytes) | Field length (bytes) | Description                                   |
| -------------- | -------------------- | --------------------------------------------- |
| ...            | ...                  | ...                                           |
| 0x8            | 4                    | LBA of first absolute sector in the partition |
| 0xC            | 4                    | Number of sectors in partition                |

## 6. 任务

> [!important]
> **任务 1**: 完成 `src/driver/virtio_blk.c:119` TODO 内容，通过 Semaphore 等待 I/O 请求完成。
>
> 提示：
>
> 1. 你可以自行为`Buf` 增加所需字段。
> 2. 本任务本质上是用 Semaphore 实现一个条件变量，需要注意条件变量的使用注意事项。

> [!important]
> **任务 2**: 完成 `src/driver/virtio_blk.c:143` TODO 内容，通知 `virtio_blk_rw` 请求已完成。

> [!important]
> **任务 3**: 在 `kernel_entry` 中调用 `virtio_blk_rw` 解析 MBR 获得第二分区起始块的 LBA 和分区大小以便后续使用。

### 6.1 代码位置与本地验证

行号可能随合并变化，请按 `LAB 4 TODO 1/2` 标记定位驱动任务，任务 3 的 `kernel_entry` 位于 `src/kernel/core.c`。`virtio_init()` 已在 `src/main.c` 中调用，初始化框架保持沿用。不要在缺少进程上下文的早期初始化代码中执行会休眠的块设备读写。

对 MBR 的读取使用整盘的绝对扇区号 **0**；第二分区起始 LBA 和分区扇区数分别来自分区项内偏移 `0x8` 与 `0xC` 的 4 字节小端整数。读取成功后输出解析结果，并核对 MBR 末尾的 `0x55 0xAA`。按当前镜像生成脚本的默认布局，第二分区起始 LBA 为 **133120**，共有 **129024** 个 512 字节扇区；这些值用于核对，不能代替实际解析。分区内的文件系统块号如何转换为整盘扇区号，参见 [Lab 5](./lab5.md)。

> [!warning]
> **先读取 MBR，再运行 `io_test()`。** 当前 `kernel_entry` 默认先调用 `io_test()`，但 `src/test/io_test.c` 的写性能测试会覆盖整盘第 0 至 2047 扇区，其中包含 MBR，且不恢复。完成任务 3 时，应将 MBR 读取与结果保存放在 `io_test()` 调用之前；I/O 测试仅使用可重新生成的实验镜像。启动下一次验证或继续后续实验前重新生成镜像，否则上次测试已经破坏的 MBR 会使解析失败。

在内核仓库根目录、退出 QEMU 后，按 [本地环境说明](./lab0.md#_1-配置本地实验环境) 配好构建依赖，并使用固定的 `build` 目录：

```shell
cmake -S . -B build
rm -f build/boot/sd.img
cmake --build build --target image
cmake --build build --target qemu
```

记录 MBR 解析输出和 `io_test PASS`，说明条件变量练习中的“发布请求—等待响应—唤醒”如何对应到驱动中的描述符、信号量和完成中断。`io_test` 校验数据读写并测量速度；吞吐量受个人环境影响，不以某个固定速度作为正确性标准。

## 7. 参考资料

**\[1]** 简单了解一下Virtio Spec协议 [https://www.openeuler.org/zh/blog/yorifang/virtio-spec-overview.html](https://www.openeuler.org/zh/blog/yorifang/virtio-spec-overview.html)

**\[2]** [OSTEP：Condition Variables](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-cv.pdf)

**\[3]** [原 Condvar 练习源码](https://github.com/Boreas618/Condvar/tree/16667bb83cb0631c8d598501630caa0d78828540)

## 8. 实验报告与提交

每位同学必须在 elearning 对应作业中提交 **`学号-lab4.pdf` 实验报告**。具体提交日期和迟交安排以本学期 elearning 作业说明为准。Condvar 与 VirtIO 两部分合写在同一份报告中。

报告必须包括：

* **实验思路**：共享 buffer 的状态转换、需要保护的条件、锁与条件变量的配合；驱动从提交请求、休眠到中断唤醒的完整过程。
* **实现方式**：两部分的修改文件与关键逻辑，如何避免丢失唤醒和死锁，如何处理唤醒后的条件检查，以及 MBR 的解析与分区边界。不要求粘贴大段代码，可使用伪代码或流程图说明。
* **实验结果**：本地环境、运行命令、Condvar 的 `make check` 输出及每个客户端的请求行数、驱动 `io_test PASS`、MBR 解析结果；失败现象、定位过程和已知问题也要如实说明。
* **问题回答**：为什么条件变量等待需要互斥锁和 `while`；条件变量与信号量如何处理提前到达的通知；为什么不能持有 `disk.lk` 等待中断取得同一把锁；对第 2 节写操作一致性问题的分析。

报告可以使用流程图、伪代码或少量关键代码，不需要粘贴大段源码，但必须清楚说明实验思路、实现方式和实验结果。未完成内容、未通过测试及已知问题应如实记录。
