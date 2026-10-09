# Lab 5: Logging File System


本次实验的目的是熟悉日志文件系统和块设备缓存的实现。

> _操作系统的本质：虚拟化、并发、**持久化**_

## 1. 实验准备（1周）

本实验在已完成的 `lab4-dev` 基础上，引入课程 `lab5` 框架；需要保留自己的前序实现。 使用 [Lab0 中配置的 Ubuntu 环境](./lab0.md#_1-配置本地实验环境)，在 Linux 终端操作。

首次开始本实验时，先回到原有仓库，确认当前位于已完成的 `lab4-dev` 分支：

```shell
cd ~/os-course/OS-26Fall-FDU
git status
```

若 `git status` 显示有源码修改，先保存到当前分支；如果提示工作区干净（working tree clean），跳过这两条命令。执行前确认修改列表中只有需要保留的源码和配置。

```shell
git add -A
git commit -m "Save lab4 work"
```

确认工作区干净后，获取课程框架并创建本次工作分支：

```shell
git fetch upstream
git switch -c lab5-dev upstream/lab5
git merge lab4-dev --no-edit
```

如果提示合并冲突，运行 `git status` 查看文件；打开这些文件，处理 `<<<<<<<`、`=======`、`>>>>>>>` 标记间的内容，同时保留自己的实现和本次框架的新接口、初始化流程、测试。去掉冲突标记并保存后执行：

```shell
git add -A
git commit -m "Resolve lab5 merge conflicts"
```

没有冲突时无需执行以上两条命令。不要直接用一方文件覆盖所有冲突。

以上获取框架的步骤只执行一次。已经开始本实验时，在工作区干净的前提下用 `git switch lab5-dev` 返回本次分支，继续修改即可，无需重新创建或合并。

## 2. Unalertable Waiting 机制的更新

*   为 `wait_sem` 等一系列函数（所有在声明时带有WARN RESULT的函数）添加了编译检查，未处理返回值将编译失败。

    ```C
    #define WARN_RESULT __attribute__((warn_unused_result))
    ```
*   添加了一套以 `unalertable_wait_sem` 为代表的函数，unalertable wait 不会被 signal（kill）打断，也没有返回值，**但请严格限制使用，保证 unalertable wait 能够在可预见的短时间内被唤醒，不会使得signal操作时效性过差。**

    > 在我们的Lab中，可能并没有明显的使用的作用区别，这里主要解释清楚，便于大家理解
* 为实现 unalertable wait，我们参考了 Linux 的 `uninterruptable wait` 的实现，为 `procstate` 添加了一项 `DEEPSLEEPING`，`DEEPSLEEPING` 与 `SLEEPING` 基本相同，区别仅在于 alert 操作对 `DEEPSLEEPING` 无效。**你需要在调度器相关代码中将 `DEEPSLEEPING` 纳入考虑。** 除 activate 操作外，一般可以将 `DEEPSLEEPING` 视为 `SLEEPING` 处理。
* 将原先的 `activate_proc` 重命名为 `_activate_proc`，添加了参数 `onalert`，以指出是正常唤醒还是被动打断，并用宏定义 `activate_proc` 为 `onalert = false` 的 `_activate_proc`，`alert_proc` 为 `onalert=true` 的`_activate_proc`。**你需要修改 `_activate_proc` 的代码，并在 `kill` 中换用 `alert_proc` 唤醒进程**

## 3. 文件系统

### 3.1. 从磁盘到块设备抽象

在计算机中，我们基本把除了 CPU 和内存以外的所有东西当作外设，与这些外设进行交互的过程称为输入/输出（I/O）。

Linux 系统中，我们将所有外设抽象成**设备**（Device），设备分为三种：

1. 字符设备（Character Device）：以字符（二进制流）为单位进行 I/O 的设备，比如键盘、鼠标、串口等；
2. 块设备（Block Device）：以块（Block）为单位进行 I/O 的设备，比如硬盘；
3. 网络设备（Network Device）：以数据包（Packet）为单位进行 I/O 的设备，比如网卡。

在 Linux 中，设备进一步被抽象成了特殊的设备文件（File），因此我们可以通过文件系统的接口来访问设备。设备文件的路径常常为`/dev/<device_name>`，比如 `/dev/sda` 就是第一个 SATA 硬盘。

块设备的本质是**实现了以下两个接口的任何对象**：

```c
// 块大小
#define BLOCK_SIZE 512
// 从设备读取数据
int block_read(int block_no, uint8_t buf[BLOCK_SIZE]);
// 将数据写入设备
int block_write(int block_no, const uint8_t buf[BLOCK_SIZE]);
```

### 3.2. 从缓存到块缓存

计算机学科中处理重复的、低速的任务的办法是什么？**缓存**。它是最简单的空间换时间办法，在不同领域还有很多其他名字：动态规划、记忆化搜索……

与 DRAM 相比，磁盘的访问时延很高。因此，理所当然地，我们需要在内存中维护一个**块缓存**（Block Cache），用于加速对块设备的访问。

块缓存是**写回**（Write Back）的，因此我们需要一个**脏位**（Dirty Bit）来标记块缓存中的数据是否已经被修改过。不过，由于我们无法追踪块缓存中的数据是否被修改过，因此我们需要让用户在使用块缓存的时候**手动**标记脏位。这个过程称为**同步**（Sync）；另一方面，由于对同一块的写是互斥的，应该有个类似锁的机制来实现「不让同一块落入两个人手里」。

因此，块缓存的接口如下：

```c
// 从设备读取一块
Block *block_acquire(int block_no);
// 标记一块为脏
void block_sync(Block *block);
// 释放一块
void block_release(Block *block);
```

从另一个角度来看，也可以把前两者看成一组：它们的作用其实和块设备的两个函数类似：一个负责读，一个负责写。最后一个函数则是释放块缓存。

### 3.3. 从内存布局到磁盘布局

内存和磁盘都是存储设备，然而由于其本身的特性，两者的布局方式有很大的不同。

我们的文件系统布局如下（以 0 为文件系统起点）：

> [!danger]
> **注意**
>
> 本表块号相对文件系统分区起点。当前仓库的 `src/user/mkfs/main.c` 保留相对块 0，将超级块写在相对块 1（`wsect(1, buf)`），并设 `log_start = 2`。这是对旧文档超级块位置的勘误；不要把文件系统相对块号直接当成整盘 LBA。分区布局请参考 [Lab 4](./lab4.md)。

| 起始块号           | 长度                                             | 用途       |
| -------------- | ---------------------------------------------- | -------- |
| 0              | 1                                              | 保留块      |
| 1              | 1                                              | 超级块      |
| `log_start`    | `num_log_blocks`                               | 日志区域     |
| `inode_start`  | `num_inodes * sizeof(InodeEntry) / BLOCK_SIZE` | inode 区域 |
| `bitmap_start` | `num_bitmap_blocks`                            | 位图区域     |
| `data_start`   | `num_data_blocks`                              | 数据区域     |

内存擅长小块随机读写，而硬盘只能大块整读整写，因此位图的效率反而比其他内存中使用过的动态分配器（例如 SLAB）要高。

表中的 `num_bitmap_blocks` 和 `data_start` 是布局说明用的名称，当前 `SuperBlock` 中没有这两个字段；应依据超级块已有字段及 `mkfs` 的布局确定范围，不要直接按示意表访问不存在的成员。

硬盘和内存的分配器的接口是类似的：

```c
// 内存
void *kalloc(size_t size);
void kfree(void *ptr);

// 硬盘
int block_alloc();
void block_free(int block_no);
```

### 3.4. 日志文件系统是干什么的？

位于磁盘上的文件系统需要面临的一个问题是：当系统崩溃或者意外掉电的时候，如何维持**数据的一致性**。

比如现在为了完成某项功能，需要同时更新文件系统中的两个数据结构 A 和 B，因为磁盘每次只能响应一次读写请求，势必造成 A 和 B 其中一者的更新先被磁盘接收处理。如果正好在其中一个更新完成后发生了掉电或者 crash，那么就会造成不一致的状态。

因此，日志作为一种**写入协议**，基本思想是这样的：**在真正更新磁盘上的数据之前，先往磁盘上写入一些信息，这些信息主要是描述接下来要更新什么**。

一个典型的写入过程如下：（Checkpoint）

1. 将要写入的数据先写入磁盘的日志区域
2. 将日志区域的数据写入磁盘的数据区域
3. 将日志区域的数据删除

对于多个事务的提交，时间序列图如下：

<figure><img src="/assets/lab5-1.png" alt=""><figcaption></figcaption></figure>

一个典型的系统启动中的初始化过程如下：（`recover_from_log`）

1. 检查日志区域是否有数据
2. 如果有，说明上次系统非正常终止，将日志区域的数据写入磁盘的数据区域
3. 将日志区域的数据删除

这个过程中任意时刻发生崩溃都是安全的，顶多是丢数据，但不会导致一致性问题。

> [!important]
> **思考**
>
> 为什么不会导致一致性问题？

日志协议的思想核心是：**持久化脏块本身**。

### 3.5. 事务：文件系统上的操作抽象

在日志文件系统中，我们将**一次文件系统操作**称为一个**事务**（Transaction）。一个事务中可能包含多个写块的操作，但是这些操作要么全部成功，要么全部失败。

> [!important]
> **思考**
>
> 你能够举出“操作要么全部成功，要么全部失败”的例子吗？

先看接口：

```c
// 开始事务
void begin_op(OpContext *ctx);
// 结束事务
void end_op(OpContext *ctx);
```

这两个函数的作用请参考代码注释。我们的设计中已经有很多这样的「对称」方法，这种设计下我们往往更关注的是其中区域（Scope）的含义。

**事务的 Scope 中进行的是对块缓存的操作。** 当所有人都离开 Scope 后，事务才会真正生效（即，按照日志协议读写块缓存）。

> [!info]
> **注意**
>
> 本实验为简单起见，按照日志协议时块缓存总表现为写直达，不使用写回，以确保数据真正落盘。

### 3.6 对外接口的使用示例

以下示例沿用接口说明；当前 `cache.h` 声明的是全局对象 `extern BlockCache bcache`，在实际代码中应写 `bcache.acquire(...)` 等点号调用；只有持有 `BlockCache *` 时才使用箭头。

读块：

```c
Block *block = bcache->acquire(block_no);

// ... Read block->data here ...

bcache->release(block);
```

写块：

```c
// Define an atomic operation context
OpContext ctx;

// Begin an atomic operation
bcache->begin_op(&ctx);
Block *block = bcache->acquire(block_no);

// ... Modify block->data here ...

// Notify the block cache that "I have modified block->data"
bcache->sync(&ctx, block);
bcache->release(block);

// End the atomic operation
bcache->end_op(&ctx);
```

## 4. 任务

> [!important]
> **任务 1**
>
> 由于为 `_wait_sem` 等一系列函数添加了编译检查，未处理返回值将编译失败；对于这一系列函数，确保起返回值被使用。
>
> 特别的，对于`_wait_sem`函数，若起返回为`false`后，不应当继续`wait`，应当立即返回（返回一个布尔值 `false` 表示当前进程未被唤醒，而是因为其他信号（例如进程被`kill`）而中断了等待状态，具体可见`sem.c`的`_wait_sem`函数实现）

> [!important]
> **任务 2**
>
> 补充完成`sched.c`中`bool _activate_proc(Proc *p, bool onalert)`函数。
>
> 对于**DEEPSLEEPING**状态：
>
> * `on alert = true`时表示主动请求唤醒，`DEEPSLEEPING`状态下主动请求唤醒将被忽略，返回false；
> * `on alert = false`时表示被动唤醒，这时 `DEEPSLEEPING` 状态下的进程会被唤醒，需要将其加入调度队列并设置为`RUNNABLE`，返回`true`。
>
> 其余状态不需要更改。

> [!important]
> **思考**
>
> 我们为什么需要`DEEPSLEEPING`状态？

> [!important]
> **任务 3**
>
> 在`kill`函数中，使用`alert_proc`来唤醒进程
>
> * `kill` 使用 `onalert=true` 表示它尝试以一种“安全”方式来唤醒进程。这意味着如果进程在 `DEEPSLEEPING` 中，系统默认不打断它。
> * `kill` 并非总是意味着立即终止，我们此处希望进程在自然状态下处理完成，而不是强制唤醒一个不稳定的进程。
> * 若在之前使用过`_wait_sem`函数（即非直接调用`wait_sem`，而是出现过以`_lock_sem` 与 `_wait_sem`调用函数时），需要指定`alertable`参数

> [!important]
> **任务 4**
>
> 阅读`cache.h`中的数据结构，理解其含义，并完成`cache.c`中的下列函数，最后在`src/fs/test`下通过相关`mock`测试。

```c
Part 1:

/*
 * 返回当前cache中块的个数（可以使用一个全局变量，但需要注意加减的原子性能否保证）。
 */
static usize get_num_cached_blocks()

/* 
 * 我们拥有一个链表记录了所有在cache的块，其软上限是EVICTION_THRESHOLD
 * 首先判断acquire的块在不在cache中，如果在应该如何操作？如果不在如何操作？
 * 如果当我们再插入一个块进入cache就要超过上界时，我们需要uncache一块？（如何选择这
 * 删除的一块？这一块还需要满足哪些条件？）使用device_read从设备读块的内容acquire
 * 返回时，需要保证调用者已获得了该block的锁。
 */
static Block *cache_acquire(usize block_no)

/* 
 * 如何表示这一块不再被acquire，处于可用状态？返回后，需要保证调用者释放了该block锁。
 * 提示：若希望一个信号量post时可以通知所有等待它的信号量，可以使用post_all_sem函数。
 */
static void cache_release(Block *block)

Part 2:

/*
 * 当拥有特别多的操作时，我们需要等待（原因在于一个事务提交的log数量有上限），如何判断
 * 当前是否依然支持更多操作，判断条件是什么？（考虑log的数量限制）如果在进行checkpoint
 * 的过程中，我们是否可以继续begin_op? 上述情况我们都需要等待，如何实现？初始化ctx->rm
 * 为OP_MAX_NUM_BLOCKS，表示其剩余的可用操作数。
 */
static void cache_begin_op(OpContext *ctx)

/*
 * 若ctx为NULL，直接使用device_writex写入块
 * （在调用函数前，调用者必须保证已经通过acquire持有该块的锁）
 * 标记该块为脏块，在log_header中记录该块（如果该块已经被标记为脏块呢？）
 */
static void cache_sync(OpContext *ctx, Block *block)

/*
 * 什么时候进行checkpoint写入操作？（checkpoint详细过程见3.4）
 * 注意：返回该函数时必须保证该事务内的所有写入全部完成。
 */
static void cache_end_op(OpContext *ctx)

/* 
 * 初始化你一切想要初始化的（如锁，信号量，一些赋值变量...）同时根据log完成断电恢复操作。
 */
void init_bcache(const SuperBlock *_sblock, const BlockDevice *_device)  
    

/* 
 * 提示：此部分建议善用bitmap_get,bitmap_set,bitmap_clear函数，见bitmap.h。
 */
Part 3:

/* 
 * 根据位图分配一个可用块，返回其块号，同时请注意：返回的块需要保证数据已经被memset，为干净块。
 */
static usize cache_alloc(OpContext *ctx)

/*
 * 根据位图恢复一个可用块，此时无需完全清除块的内容。
 */
static void cache_free(OpContext *ctx, usize block_no)
```

> [!important]
> **思考**
>
> 若存在一个事务在begin\_op阶段需要等待checkpoint完成的信号才能继续，但若其还未运行至`wait_sem`时，checkpoint完成的信号已经发送，这样的并发问题是否存在？如何解决？

## 5. 测试方式

**测试环境：使用 Linux 中的 GNU GCC/G++。** 测试项目使用 C11、C++17、pthread 和 UndefinedBehaviorSanitizer，且包含 GCC 参数 `-ftree-pre`；macOS 的 `gcc` 通常实际为 Apple Clang，请在 [Linux 实验环境](./lab0.md#_1-配置本地实验环境)中执行以下命令。Mock 测试无需 QEMU 或磁盘镜像。

有趣的是，文件系统本身作为一个抽象实现，理论上只要提供了正确的接口（例如块设备、内存分配器、锁等），本身应当是具有良好跨平台性的。因此，本次实验我们使用了基于 Mock 的评测方法，离开 QEMU 环境来测试你的文件系统。相关 C/C++ 代码在 `src/fs/test` 目录下。

我们仅 mock 了以下方法，因此请保证你只调用了在前面实验中出现的这些方法（理论上你也不该用到其他方法，否则说明你的实现不具有跨平台性）：

```c
void *kalloc(isize x);
void kfree(void *ptr);
void printk(const char *fmt, ...);
void yield();

// list.c 宏/方法集
// SpinLock 方法集
// Semaphore 方法集
// PANIC、assert 宏
// RefCount 方法集
```

在仓库根目录配置并运行（切换到本实验分支后重新配置）：

```sh
cmake -S src/fs/test -B src/fs/test/build -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++
cmake --build src/fs/test/build --target cache_test
./src/fs/test/build/cache_test
```

如果构建目录曾使用其他编译器，请先备份需要保留的测试日志，删除 `src/fs/test/build` 后重新配置。普通源码改动只需重新构建，无需反复清理。

通过标准：最后一行出现 `(info) OK: 23 tests passed.`。必须保留完整输出。`overflow`、`alloc` 等用例会故意触发并捕获异常，参考日志中的 `(fatal)` 不应单独判为失败；应结合每个用例的 `passed` 和最终 23 项通过汇总判断。测试框架在失败时也可能以 0 退出，因此仅看退出码不够。

助教的测试结果样例输出：（仅供参考，无需完全一致）

```shell
(info) "init" passed.
(info) "read_write" passed.
(info) "loop_read" passed.
(info) "reuse" passed.
(debug) #cached = 20, #read = 154
(info) "lru" passed.
(info) "atomic_op" passed.
(fatal) 
(info) "overflow" passed.
(info) "resident" passed.
(info) "local_absorption" passed.
(info) "global_absorption" passed.
(info) "replay" passed.
(fatal) 
(info) "alloc" passed.
(info) "alloc_free" passed.
(info) "concurrent_acquire" passed.
(info) "concurrent_sync" passed.
(info) "concurrent_alloc" passed.
(info) "simple_crash" passed.
(trace) running: 1000/1000 (296 replayed)
(info) "single" passed.
(trace) running: 1000/1000 (334 replayed)
(info) "parallel_1" passed.
(trace) running: 1000/1000 (291 replayed)
(info) "parallel_2" passed.
(trace) running: 500/500 (115 replayed)
(info) "parallel_3" passed.
(trace) running: 500/500 (125 replayed)
(info) "parallel_4" passed.
(trace) throughput = 71764.50 txn/s
(trace) throughput = 67016.50 txn/s
(trace) throughput = 66486.50 txn/s
(trace) throughput = 62407.00 txn/s
(trace) throughput = 60668.50 txn/s
(trace) throughput = 75762.00 txn/s
(trace) throughput = 64034.00 txn/s
(trace) throughput = 75834.50 txn/s
(trace) throughput = 58649.00 txn/s
(trace) throughput = 67872.00 txn/s
(trace) throughput = 51930.50 txn/s
(trace) throughput = 54758.00 txn/s
(trace) throughput = 62521.00 txn/s
(trace) throughput = 72498.50 txn/s
(trace) throughput = 66931.00 txn/s
(trace) throughput = 59653.50 txn/s
(trace) throughput = 63922.50 txn/s
(trace) throughput = 57582.00 txn/s
(trace) throughput = 71582.50 txn/s
(trace) throughput = 64026.50 txn/s
(trace) throughput = 56911.50 txn/s
(trace) throughput = 62170.50 txn/s
(trace) throughput = 51186.50 txn/s
(trace) throughput = 61406.50 txn/s
(trace) throughput = 66081.00 txn/s
(trace) throughput = 68124.50 txn/s
(trace) throughput = 64132.50 txn/s
(trace) throughput = 69123.50 txn/s
(trace) throughput = 62546.00 txn/s
(trace) throughput = 73620.50 txn/s
(trace) running: 30/30 (3 replayed)
(info) "banker" passed.
(info) OK: 23 tests passed.
```

> [!danger]
>
> **注意**
>
> 上述测试只用于检测`cache.c`中内容是否正确运行， 任务 1-3 的内容是否正确完成至少需要确保在 `build/`运行`make qemu`时能正确跑通（可以打开`core.c`中`proc_test()`和`user_proc_test`尝试运行）

### 5.1. QEMU 回归与磁盘接口衔接

Mock 只覆盖文件系统接口；任务 1—3 还需使用自己的累计实现，在根目录的 `build` 中分别运行 Lab 2、Lab 3 回归，确认等待、正常唤醒、被 `kill` 打断和 `DEEPSLEEPING` 的处理。`onalert=true` 对应 `alert_proc` 的打断请求，`onalert=false` 对应 `activate_proc` 的正常唤醒；它们不是是否主动调用函数的区别。

```sh
cmake -S . -B build
cmake --build build --target qemu
```

`boot/generate-image.py` 会使用仓库内的 `src/user/mkfs/main.c` 在本地生成镜像，依赖 Python 3、主机 C 编译器、`mkfs.vfat`、`mcopy`、`sfdisk` 和 `dd`，无需下载预制镜像。脚本使用固定的 `../build` 相对路径，请保持根目录构建目录名为 `build`。

后续将 Mock 实现接入真实块设备时，沿用 Lab 4 解析的第二分区起始 LBA，在块设备封装层统一换算 `整盘 LBA = 分区起始 LBA + 文件系统相对块号`，并在文件系统初始化之前读取相对块 1 的超级块。当前 `block_device.c` 仅保留接口骨架，`sblock_data` 尚未装载磁盘数据；仅调用 `init_block_device()` 不会自动完成这一步。不要在 `cache.c` 中硬编码分区偏移或绕过传入的 `BlockDevice`，否则会破坏 Mock 测试的抽象边界。这一说明用于衔接既有 Lab 4 和文件系统接口，不新增块缓存功能。

## 6. 评分标准

本次实验的评分标准如下：

- **核心实现**：70%
- **前序 Lab2、Lab3 功能正确**：20%
- **思考题**：30%

> [!warning]
> 原文列出的比例合计为 120%，存在口径冲突；具体计分权重以本学期 eLearning 评分细则为准，本页不作自行归一化。


| Test              | Score |
| ----------------- | ----- |
| init              | 2     |
| read_write        | 4     |
| loop_read         | 2     |
| reuse             | 2     |
| lru               | 2     |
| atomic_op         | 2     |
| overflow          | 3     |
| resident          | 3     |
| local_absorption  | 3     |
| global_absorption | 3     |
| replay            | 3     |
| alloc             | 3     |
| alloc_free        | 3     |
| concurrent_acquire | 5     |
| concurrent_sync    | 5     |
| concurrent_alloc   | 5     |
| simple_crash | 3     |
| single       | 4     |
| parallel_1   | 4     |
| parallel_2   | 4     |
| parallel_3   | 2     |
| parallel_4   | 2     |
| banker       | 1     |



## 7. 参考资料

1. xv6 文件系统补充讲义：https://github.com/FDUCSLG/OS-2022Fall-Fudan/blob/lab10/doc/filesystem-v4.pdf （可阅读其中关于本次实验(P. 26-P. 33)的部分，其中还包含了下次实验(inode等)的内容）
2. 聊聊 xv6 中的文件系统：https://www.cnblogs.com/KatyuMarisaBlog/p/14366115.html
3. xv6 中文文档：https://th0ar.gitbooks.io/xv6-chinese/content/content/chapter6.html


## 8. 实验报告与提交

每位同学必须在 elearning 对应作业中提交 **`学号-lab5.pdf` 实验报告**。具体提交日期和迟交安排以本学期 elearning 作业说明为准。

报告必须包括：

1. **实验环境**：操作系统、CPU 架构、编译器、CMake 和 QEMU 版本，以及实际使用的运行环境（原生 Ubuntu、WSL2 或虚拟机）。
2. **实验思路**：按本页各任务说明目标、数据结构、关键不变量、同步关系与设计理由，不能仅给出运行截图。
3. **实现方式**：列出本次修改的文件及对应功能，说明主要流程、边界处理、失败处理与调试过程。可以使用简短伪代码、流程图或关键片段，不要求粘贴大段完整代码。
4. **实验结果**：给出可复现的构建和测试命令、完整测试日志或其附件、关键结果截图；如有未通过项目，写清实际现象、原因分析与当前完成程度。
5. **本实验分析**：回答本页全部思考题，重点讨论事务开始、日志记录、提交及写回等阶段崩溃时的一致性，以及并发事务、日志吸收和丢失唤醒的处理；说明为了支持文件系统，对调度器、`kill` 与信号量调用作了哪些修改。
6. **验证范围**：分别列出 23 项 `cache_test` 的结果与 QEMU 中 Lab 2/Lab 3 回归结果，不用 Mock 通过代替调度验证。

报告可以使用流程图、伪代码或少量关键代码，不需要粘贴大段源码，但必须清楚说明实验思路、实现方式和实验结果。未完成内容、未通过测试及已知问题应如实记录。
