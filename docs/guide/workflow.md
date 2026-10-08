# Git 工作流

实验代码仓库是 [rfieldsy/OS-26Fall-FDU](https://github.com/rfieldsy/OS-26Fall-FDU)。`main` 只有课程介绍，**不能直接在 main 上构建内核**。对应框架分支为 `lab0`、`lab1`、`lab2`、`lab3`、`lab4`、`lab5`、`lab6`、`final`。

`upstream` 表示课程框架仓库，`origin` 表示你自己的代码仓库。所有命令在本地 Linux 环境执行。

## 1. 获取框架

```sh
git clone -o upstream -b lab0 https://github.com/rfieldsy/OS-26Fall-FDU.git
cd OS-26Fall-FDU
git config user.name "你的姓名"
git config user.email "你的邮箱"
git switch -c lab0-dev
git tag lab0-start
```

`user.name`、`user.email` 是提交署名，不是登录信息。克隆公开框架无需 GitHub 账号；向个人仓库推送则使用 GitHub 支持的 HTTPS 凭据或 SSH 身份验证，不能使用账号密码代替访问令牌。

## 2. 开始下一次实验

先提交当前实验、记录完成标签，再切换。工作区中有尚未提交的文件时，不要执行新实验的合并。

Lab1 的框架已提供 Lab0 的启动支持和 BSS 初始化，Lab0 的演示输出不作为后续依赖。因此 Lab1 从官方框架开始：

```sh
git fetch upstream --tags
git switch -c lab1-dev upstream/lab1
git tag lab1-start
```

Lab2 及以后需要继承自己此前的实现。以下以 Lab2 为例：

```sh
git status --short          # 应为空；否则先提交上一实验的改动
git fetch upstream --tags
git switch -c lab2-dev upstream/lab2
git merge lab1-submit
# 如有冲突，按下节处理并完成合并，再创建标签
git tag lab2-start
git rev-parse upstream/lab2 lab1-submit lab2-start
```

| 当前实验 | 框架分支 | 上次完成标签 | 本次工作分支 | 本次起点标签 | 本次完成标签 |
| --- | --- | --- | --- | --- | --- |
| Lab0 | `upstream/lab0` | 无 | `lab0-dev` | `lab0-start` | `lab0-submit` |
| Lab1 | `upstream/lab1` | 无（框架已含启动支持） | `lab1-dev` | `lab1-start` | `lab1-submit` |
| Lab2 | `upstream/lab2` | `lab1-submit` | `lab2-dev` | `lab2-start` | `lab2-submit` |
| Lab3 | `upstream/lab3` | `lab2-submit` | `lab3-dev` | `lab3-start` | `lab3-submit` |
| Lab4 | `upstream/lab4` | `lab3-submit` | `lab4-dev` | `lab4-start` | `lab4-submit` |
| Lab5 | `upstream/lab5` | `lab4-submit` | `lab5-dev` | `lab5-start` | `lab5-submit` |
| Lab6 | `upstream/lab6` | `lab5-submit` | `lab6-dev` | `lab6-start` | `lab6-submit` |
| Final | `upstream/final` | `lab6-submit` | `final-dev` | `final-start` | `final-submit` |

每个标签创建一次。不要移动或覆盖已提交标签；重新提交时使用 `lab2-submit-v2` 等新标签，同时更新报告及 eLearning 附件。若下一实验已经开始，应明确它继承的是哪一版上次提交。

## 3. 处理合并冲突

```sh
git status
git diff --name-only --diff-filter=U
```

逐一打开冲突文件，理解框架新增内容与自己的实现，编辑后删除 `<<<<<<<`、`=======`、`>>>>>>>` 标记。不要用整个文件的“全部采用一方”覆盖已有实现。

```sh
git add path/to/resolved-file.c   # 替换为实际已解决的文件，逐一添加
git diff --cached
git diff --name-only --diff-filter=U  # 应为空
git commit                       # 完成合并
```

如果尚未完成合并且需要重新开始，可以执行 `git merge --abort` 回到合并前。不要使用 `git reset --hard` 来丢弃未备份的实验实现。完成合并后再创建本次 `*-start` 标签；本次合并冲突的解决同样属于本 Lab 的修改，ZIP 打包工具会将其纳入。

## 4. 保存与固定提交

以 Lab2 为例：

```sh
git status --short
git diff
# 把实际修改过的源码/配置文件逐一加入，不加入 build、镜像或日志
git add src/kernel/proc.c src/kernel/sched.c
git diff --cached
git commit -m "Complete lab2 process management"
git tag lab2-submit
git rev-parse lab2-start lab2-submit
```

上面的文件只是示例；以实际修改清单为准。包括新建文件在内的所有实现必须先提交，打包和评分针对固定 commit。不要把代码粘贴到报告中替代代码提交。

## 5. 使用自己的 Git 仓库

在 GitHub 或可供助教访问的 Git 平台创建一个**空仓库**（不要初始化 README）。将下面 URL 中的账户和仓库名替换为你自己的值：

```sh
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_OS_REPO.git
git remote -v
git push -u origin lab2-dev
git push origin lab2-start lab2-submit
```

后续实验推送对应分支和标签即可。提交的是个人仓库地址、完整 commit SHA、起点与完成标签；不是向课程 `upstream` 推送代码。私有仓库需按 eLearning 提供的助教账号授予只读所需的访问权限，并确保截止后仍可读取。不要在报告、代码或 ZIP 中放访问令牌、私钥等凭据。

Lab4 的 Condvar 使用独立练习仓库，按 Lab4 页面单独操作，不能将它作为内核源码合并。其起点/完成标签为 `condvar-start`、`condvar-submit`。

继续阅读[报告与代码提交规范](./submission.md)。
