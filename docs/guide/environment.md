# 本地实验环境

所有实验在自己的电脑上完成。内核运行于 QEMU 模拟的 AArch64 `virt` 平台，宿主机可以是 x86-64 或 ARM64；宿主架构与被模拟的架构不必相同。

## 推荐环境

统一使用 **Ubuntu 24.04 LTS 的 Linux 环境**。Linux 用户可直接使用；Windows 用户可使用 WSL2 中的 Ubuntu；macOS 用户可使用本地 Ubuntu 虚拟机，Apple Silicon 对应 ARM64 Ubuntu，Intel 对应 x86-64 Ubuntu。原框架使用 GNU 编译器、链接器以及 Linux 磁盘工具，macOS 自带的 Clang 和磁盘命令不能直接替代。

建议为 Linux 环境保留 4 个可用逻辑核、8 GiB 内存和 20 GiB 可用磁盘空间。框架的 QEMU 参数是 4 核、4 GiB 内存；这些是运行建议，不是评分要求。WSL2 中将项目放在 Linux 家目录，例如 `~/os-course`，避免 `/mnt/c` 的文件权限和性能差异。项目绝对路径请勿包含空格：原镜像生成脚本没有为所有路径添加引号。

在该 Linux 环境中安装依赖：

```sh
sudo apt update
sudo apt install -y build-essential git cmake python3 zip unzip \
  gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu \
  qemu-system-arm gdb gdb-multiarch dosfstools mtools fdisk
```

- `build-essential` 提供宿主 GNU C/C++ 编译器和 Make。Condvar 和 Lab5/6 的文件系统单元测试使用宿主编译器。
- x86-64 Linux 下，内核使用 `aarch64-linux-gnu-*` 交叉工具链；ARM64 Linux 下，框架会使用原生 GNU 工具链。
- `qemu-system-arm` 提供 `qemu-system-aarch64`。
- 框架的镜像生成还使用 `mkfs.vfat`、`mcopy`、`sfdisk`、`dd`，分别由 `dosfstools`、`mtools`、`fdisk`、系统基础工具提供。不要把镜像路径替换为真实磁盘设备。

完成安装后检查：

```sh
uname -m
git --version
cmake --version
gcc --version
g++ --version
qemu-system-aarch64 --version
command -v aarch64-linux-gnu-gcc aarch64-linux-gnu-ld
command -v mkfs.vfat mcopy sfdisk python3
```

报告记录实际版本。上面的 Ubuntu 版本是文档统一支持的操作路径；不要求追逐工具的最新发行版。

## 获取代码与首次构建

按[Git 工作流](./workflow.md)取得 `lab0` 分支，在**代码仓库根目录**运行：

```sh
cmake -S . -B build -G "Unix Makefiles"
cmake --build build --target qemu
```

`build` 必须使用这一名称并位于仓库根目录下：后续镜像和 musl 构建脚本中存在 `../build` 相对路径。进入 `build` 后执行 `make qemu` 与上述命令等价。QEMU 退出方式是先按 `Ctrl+A`，松开后按 `x`。Lab0 最初运行的是待补全的实验框架，请以本页任务要求检查你完成后的输出。

切换实验分支后，在确认只含构建产物的情况下清理旧的 `build` 目录，再重新配置：

```sh
# 在仓库根目录执行；不要删除 src、boot 或 musl 源码目录
rm -rf build
cmake -S . -B build -G "Unix Makefiles"
cmake --build build --target qemu
```

不需要使用 `sudo` 编译或运行 QEMU。本框架使用软件模拟，不依赖 KVM 或实体 ARM 开发板。

## 调试与分层测试

在两个本地终端中，分别进入同一代码仓库：

```sh
# 终端一：启动内核并等待调试器
cmake --build build --target qemu-debug
```

```sh
# 终端二：连接本机调试端口
cmake --build build --target debug
```

同时只运行一个使用端口 1234 的 QEMU 实例。`qemu-debug` 刚启动时停住是预期行为，在 GDB 中设置断点后执行 `continue`。

测试按各 Lab 页面选择。内核测试在 QEMU 中运行；Condvar 的 `make check`、Lab5 的 `cache_test` 和 Lab6 的 `inode_test` 在宿主 Linux 中运行。单元测试通过不等于 QEMU 集成通过。Lab4 的 `io_test` 会改写磁盘镜像，运行前阅读该页的镜像重建说明；Final 还需要初始化 musl 子模块并先构建 libc。

## 常见问题

| 现象 | 检查方法 |
| --- | --- |
| 找不到 `aarch64-linux-gnu-gcc` | 确认命令运行在 Linux 环境中，并完成依赖安装。 |
| `cc` 不认识 GNU 参数或汇编失败 | 确认没有混用 macOS 的 Clang 或旧构建缓存。 |
| 找不到 `mkfs.vfat`、`mcopy`、`sfdisk` | 安装镜像工具，使用 `command -v` 检查 PATH。 |
| 镜像生成找不到源码/用户程序 | 使用仓库根目录下的 `build`，检查项目路径是否含空格。 |
| QEMU 停住或没有通过输出 | 先区分调试等待、尚未实现的 TODO、以及实际死锁；保留日志和复现步骤。 |
| 换分支后出现重复定义或旧结果 | 先检查合并冲突，再清理该分支的构建目录并重新配置。 |
