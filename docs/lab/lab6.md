# Lab 6: Inode-based File System

本次实验将实现基于 Inode 的文件系统的基础底层操作。**本实验工作量较大，请大家尽早开始。**

## 1. 实验准备（2周）

本实验在已完成的 `lab5-dev` 基础上，引入课程 `lab6` 框架；需要保留自己的前序实现。 使用 [Lab0 中配置的 Ubuntu 环境](./lab0.md#_1-配置本地实验环境)，在 Linux 终端操作。

首次开始本实验时，先回到原有仓库，确认当前位于已完成的 `lab5-dev` 分支：

```shell
cd ~/os-course/OS-26Fall-FDU
git status
```

若 `git status` 显示有源码修改，先保存到当前分支；如果提示工作区干净（working tree clean），跳过这两条命令。执行前确认修改列表中只有需要保留的源码和配置。

```shell
git add -A
git commit -m "Save lab5 work"
```

确认工作区干净后，获取课程框架并创建本次工作分支：

```shell
git fetch upstream
git switch -c lab6-dev upstream/lab6
git merge lab5-dev --no-edit
```

如果提示合并冲突，运行 `git status` 查看文件；打开这些文件，处理 `<<<<<<<`、`=======`、`>>>>>>>` 标记间的内容，同时保留自己的实现和本次框架的新接口、初始化流程、测试。去掉冲突标记并保存后执行：

```shell
git add -A
git commit -m "Resolve lab6 merge conflicts"
```

没有冲突时无需执行以上两条命令。不要直接用一方文件覆盖所有冲突。

以上获取框架的步骤只执行一次。已经开始本实验时，在工作区干净的前提下用 `git switch lab6-dev` 返回本次分支，继续修改即可，无需重新创建或合并。

## 2. 文件和目录

### 2.1. Inode：文件和目录的统一抽象

在上一次实验中，我们实现了一个简单的文件系统的基层操作，我们现在可以：

* 随意地读取或写入一个块；
* 利用事务一次性写入多个块，而且保证写入的一致性；
* 任意分配或释放一个块。

但是，和我们平时使用的文件系统相比，我们还缺少了一些核心的组件。毕竟，我们口中所说的文件系统一般不是以块（Block）为单位的，而是以文件（File）和目录（Directory）为单位的。我们需要一种能够把块组织成文件和目录的方法，这就是 Inode。

Inode 的名称是 **I**ndex **node** 的缩写，它是文件系统中的一个重要的概念，这里的 Index 指它具有索引的用途。

简单来说，一个 inode 就是一个硬盘上的文件或目录的抽象，它包含了文件或目录的元信息（metadata），比如文件大小、文件名，以及文件内容所在的块号等等。

在 Inode 中，目录其实也是一种特殊的文件：它的内容是一系列的文件名和对应的 inode 号。这样，我们就可以通过读取目录的内容来得到它所包含的所有文件和目录的信息。

> [!info]
> 实际上，可以把 Inode 类比为一棵树中的各个节点，叶节点是我们所说的「文件」，非叶节点就是我们所说的「目录」。

Inode 在文件系统中的位置如下：

> [!warning]
> **注意：**本表块号相对文件系统分区起点，不是整盘 LBA。当前仓库 `mkfs` 保留相对块 0，并在相对块 1 写入超级块，日志从相对块 2 开始；分区偏移及超级块装载见 [Lab 5 的接口衔接说明](./lab5.md#_5-1-qemu-回归与磁盘接口衔接)。

| 起始块号           | 长度                                             | 用途           |
| -------------- | ---------------------------------------------- | ------------ |
| 0              | 1                                              | 保留块          |
| 1              | 1                                              | 超级块          |
| `log_start`    | `num_log_blocks`                               | 日志区域         |
| `inode_start`  | `num_inodes * sizeof(InodeEntry) / BLOCK_SIZE` | **inode 区域** |
| `bitmap_start` | `num_bitmap_blocks`                            | 位图区域         |
| `data_start`   | `num_data_blocks`                              | 数据区域         |

本表的 `num_bitmap_blocks`、`data_start` 是布局示意名称，并非 `SuperBlock` 的成员；实现时以 `src/fs/defines.h` 和 `src/user/mkfs/main.c` 为准。

为了便于管理，我们的每个 Inode 都具有一个编号。这个编号就是 Inode 在 Inode 区域中的偏移量，第一个 Inode 的编号为 1，第二个 Inode 的编号为 2，以此类推。

当然，由于一个 inode 不会占用整个块（在我们的实验中一个 `InodeEntry` 是 64 字节），所以我们可以把多个 inode 放在一个块中。这样，我们就需要通过块号和块内偏移量来定位一个 inode。

> [!info]
> **你知道吗？**
>
> 由于设计原因，我们不使用 0 作为 Inode 的编号的开始：0 将会在一些函数中用于表示「没有 Inode」的意思。
>
> 延伸阅读：[https://stackoverflow.com/questions/2099121/why-do-inode-numbers-start-from-1-and-not-0](https://stackoverflow.com/questions/2099121/why-do-inode-numbers-start-from-1-and-not-0)

回想一下，实际文件系统中对文件和目录的操作是繁多的：读取、写入、新建、删除文件/目录，列出目录内容……等等。我们需要实现哪些接口才能完成这些操作呢？

#### 2.1.1. 作为文件的操作

让我们先从简单的情况开始：只考虑 inode 是文件（毕竟目录只是一种特殊的文件）。

最简单的接口如下所示：

a. 用于读写 inode 中元数据（例如文件大小、修改日期等）：

```c
// 读入一个 inode，返回一个可以用于读写的 Inode 指针
Inode *acquire(int inode_no);
// 标记为脏
void sync(Inode *inode);
// 释放一个 inode
void release(Inode *inode);
```

b. 用于读写 inode 对应的文件内容：

```c
// 将长度为 len 的 buf 写入 inode 的 offset 处
void write(Inode *inode, void *buf, int offset, int len);
// 将 inode 的 offset 处的 len 字节读入 buf
void read(Inode *inode, void *buf, int offset, int len);
// 清空 inode 的内容（使文件变成长度为 0 的空文件）
void clear(Inode *inode);
```

c. 用于分配 inode：

```c
// 新建一个 inode
int alloc();
```

你可能要问了：怎么没有 **删除一个文件（inode）** 的接口？因为它更复杂。

让我们先考虑一个问题：**一个文件可以同时被多个进程访问吗？**

这种需求显然是存在的。比如，我们平时运行一个程序的时候可能会去看它的日志文件。这时，我们的程序和我们的文本编辑器都会去打开这个文件，一个读取、一个写入。如果两边反复地 acquire 和 release inode，那么效率会很低。更好的想法是：能不能仅仅在读写操作上互斥（也就是说，虽然可以同时打开，如果一个进程正在读写文件，那么其他进程就不能读取或写入这个文件）？

这里其实就是对一个操作的拆解。在块缓存中，我们的 acquire 其实完成了三件事：

1. 建立（或者从链表中找到）一个块（可以称为 `get`）；
2. 如果块不在内存中，从硬盘上**读取**块（可以称为 `read_block`）；
3. 获取这个块上的读写锁（可以称为 `lock`）。

仔细想想，其实我们可以把这三件事分开来做。比如，三个进程其实都希望 `get` 一个 inode，但未必都需要 `read_inode`，也未必马上就要 `lock`。

让我们细分出一套接口来替代上面的 a. 类接口：

```c
// 获得一个 inode
Inode *get(int inode_no);
// 获取 inode 的读写锁
void lock(Inode *inode);
// 读取或标记一个 inode 为脏。sync(inode, true) 等价于原来的 sync，sync(inode, false) 等价于 read_inode
void sync(Inode *inode, bool do_write);
// 释放 inode 的读写锁
void unlock(Inode *inode);
// 释放 inode
void put(Inode *inode);
```

这样 `acquire = get + lock + sync(false)`，`sync = sync(true)`，`release = unlock + put`。

由于同一个 inode 引用可以同时被多个进程 `get/put` 了，所以我们需要一个计数器来记录当前有多少进程正在使用这个 inode，这样才知道什么时候可以把 inode 从链表中删除。这个计数器就是 `Inode` 结构体中的 `rc` 字段

回到删除文件的问题上来。让我们从头开始考虑文件可被实际从硬盘上删除的条件：

1. 文件没有被任何进程**打开**（或者说，所有之前打开文件的进程都已经 `put` 这个文件）；
2. 文件不再在文件系统中被需要（即，它已经不是叶节点）。

我们平时所说的「删除文件」其实是想完成第二件事：删除文件的目录项，使得文件从 Inode 树中脱离，用 `ls` 命令不再能看到它。但是，这并不意味着文件就真的被删除了：如果还有进程在使用它，它仍然占用着硬盘上的空间。

怎么知道文件不再被文件系统需要呢？我们需要另一个计数器来记录当前有多少位置引用了这个文件（例如目录项、硬连接等）。这个计数器就是我们的 `InodeEntry` 结构体中维护的 `num_links` 字段。

当两个计数器的值都降到 0 时，我们就可以真正删除这个文件了。

**所以，删除之所以没有列出来，是因为实际的删除逻辑是一个自然发生的过程**：我们只需要在所有可能导致上面两个条件满足的地方，检查两个计数器的值，如果都是 0 就调用释放 inode 的方法即可。

在本实验中，我们暂时还不涉及修改 `num_links` 的逻辑，而唯一减少 `rc` 的地方只有 `put`，所以我们只需要在 `put` 的时候检查 `rc` 和 `num_links` 即可。

此外，我们还添加了一个接口，用于一些进程显式地表示自己需要 `get` 两次（例如可能它要把自己的 inode 指针交给两个方法，两个方法都会调用 `put` 来释放这个 inode）：

```c
// 让 inode 的引用计数加一
Inode *share(Inode *inode);
```

总结一下，我们的接口包括：

```c
// === 和块缓存差不多的读写操作 ===
// 获得一个 inode（依然在inode中维护一个链表，）
Inode *get(int inode_no);
// 获取 inode 的读写锁，若valid项为false，需要读入inodeentry
void lock(Inode *inode);
// 读取或标记一个 inode 为脏
void sync(Inode *inode, bool do_write);
// 释放 inode 的读写锁
void unlock(Inode *inode);
// 释放 inode，判断是否清空inode内容
void put(Inode *inode);

// === 读写 inode 对应文件的内容 ===

// 获取inode在offset位置的块号，同时若ctx!=NULL且offset超过当前文件大小，会allocate新的一块并标记modified为true
usize map(OpContext *ctx, Inode *inode, usize offset, bool *modified)
// 将长度为 len 的 buf 写入 inode 的 offset 处
void write(Inode *inode, void *buf, int offset, int len);
// 将 inode 的 offset 处的 len 字节读入 buf
void read(Inode *inode, void *buf, int offset, int len);
// 清空 inode 的内容（使文件变成长度为 0 的空文件）
void clear(Inode *inode);

// === inode 本身的分配 ===
// 分配一个 inode
Inode *alloc();

// === inode 辅助操作 ===
// 让 inode 的引用计数加一
Inode *share(Inode *inode);
```

#### 2.1.2. inode 储存文件详解

我们的 inode 中用于指向数据区域的字段是 `addrs`。这个字段的类型是 `u32 addrs[INODE_NUM_DIRECT]`，其中 `INODE_NUM_DIRECT` 是一个常量，表示直接指向数据块的指针的个数。

例如，一个文件有 4.5 \* 512 = 2304 字节，则它占用 5 个块的空间。那么，这个文件的 inode 的 `inode.addrs` 字段的前 5 个元素就是这 5 个块的块号，而 `inode.num_bytes == 2304`。

我们的 `INODE_NUM_DIRECT` 为 12，也就是说，最多可以直接指向 12 个块。如果一个文件占用的空间超过了 12 个块（即超过 6 KB），我们就需要使用**间接块**来指向更多的块。

间接块的块号是 `inode.indirect`。当文件小于 6KB 时，可以用 0 表示没有间接块。`inode.indirect` 指向一个块，这个块中的内容是一系列块号，这些块号指向文件的后续块。

举个例子，如果一个文件占用了以下块：

```
1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014,1015,1016,1017,1018,1019,1020
```

那么，这个文件的 inode 为（假设间接块的块号为 6666）：

```
inode.addrs = [1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012]

inode.indirect = 6666
```

而 6666 号块的内容为：

```
[1013,1014,1015,1016,1017,1018,1019,1020]
```

为了根据在文件中的位置获得对应的块，便于 `read` 和 `write` 的实现，我们建议实现一个工具方法 `inode_map`，它用于在给定字节位置的情况下找到对应的块。

仍以上面的文件为例，有：

```c
inode_map(inode, 0) == 1001 // 第 0 字节在 1001 号块
inode_map(inode, 1023) == 1002 // 第 1023 字节在 1002 号块
inode_map(inode, 10239) == 1020 // 第 10239 字节在 1020 号块
inode_map(inode, 10240) == ??? // 第 10240 字节已经超过了文件的大小，用 block_alloc 分配一个新块，加入到 6666 块中，然后返回新块的块号
```

#### 2.1.3. 作为目录的操作

我们的文件系统中，目录也是一种特殊的文件。目录的内容是一系列的 `DirEntry`，每个 `DirEntry` 由一个 `inode_no` 和一个 `name` 组成。`inode_no` 是这个文件的 inode 的编号，`name` 是这个文件的名字。

例如，一个目录的内容是：

```
DirEntry[0] = {inode_no: 1, name: "a"}
DirEntry[1] = {inode_no: 2, name: "b"}
DirEntry[2] = {inode_no: 3, name: "c"}
```

为了方便后续实现，我们要求大家实现三个有用的接口：

```c
// 向目录增加一项 {inode_no, name}
void insert(Inode *dir_inode, int inode_no, const char *name);
// 从目录中删除第 index 项
void remove(Inode *dir_inode, int index);
// 从目录中查找名字为 name 的文件，返回它的 inode 编号
int lookup(Inode *dir_inode, const char *name);
```

因为目录只是文件的一种，你可以直接用 `read/write` 等方法来实现这三个接口。

## 3. 任务

> [!important]
> **任务**
>
> 完成inode.c中所有函数（函数需要实现的具体功能见上）
>
> ```c
> static Inode* inode_get(usize inode_no)
> static void inode_lock(Inode* inode)
> static void inode_sync(OpContext* ctx, Inode* inode, bool do_write)
> static void inode_unlock(Inode* inode)
> static void inode_put(OpContext* ctx, Inode* inode)
>
> static usize inode_map(OpContext *ctx, Inode *inode, usize offset, bool *modified)
> static usize inode_read(Inode* inode, u8* dest, usize offset, usize count)
> static usize inode_write(OpContext* ctx, Inode* inode, u8* src, usize offset, usize count)
> static void inode_clear(OpContext* ctx, Inode* inode)
>
>
> static Inode* inode_share(Inode* inode)
> static usize inode_alloc(OpContext* ctx, InodeType type)
>
>
> static usize inode_lookup(Inode* inode, const char* name, usize* index)
> static usize inode_insert(OpContext* ctx, Inode* inode, const char* name, usize inode_no)
> static void inode_remove(OpContext* ctx, Inode* inode, usize index)
> ```

## 4. 思考题

请在实验报告中回答以下问题（30% 分值）：

**问题1：** 在我们的 Inode 实现中，使用了 `get/lock/sync/unlock/put` 的分离式接口设计。请分析这种设计的优势和潜在问题。如果采用传统的 `acquire/sync/release` 组合接口，你认为在什么场景下会出现性能瓶颈？

**问题2：** 在 `inode_put` 函数中，我们需要检查 `rc` 和 `num_links` 两个计数器来决定是否删除 inode。请解释为什么需要这两个计数器，它们分别代表什么含义？如果只使用其中一个计数器会产生什么问题？

**问题3：** 目录作为特殊文件的实现方式带来了哪些优势？如果采用专门的目录块结构（不作为普通文件），你认为优缺点分别是什么？

**问题4：** 在实现 `inode_insert` 和 `inode_remove` 时，需要考虑目录文件大小的变化。请分析当目录项频繁增删时，可能出现哪些性能问题？如何优化？

**问题5：** `inode_lookup`的时间复杂度是多少？如果目录中的文件数量很大，这种线性查找方式是否高效？有哪些可能的优化策略？

## 5. 评测

本次实验我们继续使用基于 Mock 的评测方法，离开 QEMU/VirtIO 环境来测试你的文件系统。相关 C/C++ 代码在 `src/fs/test` 目录下。

使用与 Lab 5 相同的 Linux GNU GCC/G++ 环境，从仓库根目录运行：

```sh
cmake -S src/fs/test -B src/fs/test/build -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++
cmake --build src/fs/test/build --target inode_test
./src/fs/test/build/inode_test
```

切换分支后需要重新运行 CMake，才能获得本实验新增的 `inode_test` 目标。若之前使用其他编译器配置过该目录，请保留日志后删除 `src/fs/test/build` 并重新配置。

**通过标准**：应出现 `init`、`alloc`、`sync`、`touch`、`share`、`small_file`、`large_file`、`dir` 共 8 项 `passed`，且没有 `(error)` 和 `(fatal)` 输出。该测试不会输出 Lab 5 的“23 tests passed”汇总；测试运行器可能在失败时仍返回退出码 0，不能仅凭进程退出码判断通过。保存完整输出供审阅。

`inode_test` 为块缓存提供了 Mock，因此它通过并不自动证明 Lab 5 块缓存正确；合并后也应重新运行 `cache_test`。真实磁盘镜像仍由仓库脚本在本地生成，衔接方式见 [Lab 5](./lab5.md)。

## 6. 评分标准

本次实验的评分标准如下：

- **核心实现**：90%
- **思考题**：30%（AI率超过80%的答案将不得分）

> [!warning]
> 原文列出的比例合计为 120%，存在口径冲突；具体计分权重以本学期 eLearning 评分细则为准，本页不作自行归一化。

## 7. 参考资料

\[1] 聊聊 xv6 中的文件系统：https://www.cnblogs.com/KatyuMarisaBlog/p/14366115.html

\[2] xv6 中文文档：https://th0ar.gitbooks.io/xv6-chinese/content/content/chapter6.html


## 8. 实验报告与提交

每位同学必须在 elearning 对应作业中提交 **`学号-lab6.pdf` 实验报告**。具体提交日期和迟交安排以本学期 elearning 作业说明为准。

报告必须包括：

1. **实验环境**：操作系统、CPU 架构、编译器、CMake 和 QEMU 版本，以及实际使用的运行环境（原生 Ubuntu、WSL2 或虚拟机）。
2. **实验思路**：按本页各任务说明目标、数据结构、关键不变量、同步关系与设计理由，不能仅给出运行截图。
3. **实现方式**：列出本次修改的文件及对应功能，说明主要流程、边界处理、失败处理与调试过程。可以使用简短伪代码、流程图或关键片段，不要求粘贴大段完整代码。
4. **实验结果**：给出可复现的构建和测试命令、完整测试日志或其附件、关键结果截图；如有未通过项目，写清实际现象、原因分析与当前完成程度。
5. **思考题**：逐项回答第 4 节的 5 个问题，结合自己的实现说明接口拆分、`rc` 与 `num_links`、目录增删及查找复杂度。
6. **本实验重点**：说明直接块/间接块的映射与释放、inode 生命周期和锁/引用计数、目录项更新，以及边界情况；给出 8 项 `inode_test` 与 Lab 5 `cache_test` 回归记录。

报告可以使用流程图、伪代码或少量关键代码，不需要粘贴大段源码，但必须清楚说明实验思路、实现方式和实验结果。未完成内容、未通过测试及已知问题应如实记录。
