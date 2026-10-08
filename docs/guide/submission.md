# 报告与代码提交规范

**每次实验都必须在 eLearning 提交 PDF 报告，包括 Lab0 和 Final。** 具体截止时间、迟交规则和评分口径以本学期 eLearning 对应实验公告为准。报告与代码版本应一致；更换代码版本时必须重新提交报告和相应附件。

## 报告内容

文件名为 `学号-lab0.pdf` 至 `学号-lab6.pdf`，最终实验为 `学号-final.pdf`。Lab4 的 Condvar 与 VirtIO 写在同一份报告中。

1. **基本信息与环境**：姓名、学号、Lab 名称、Linux/工具版本、实际使用的框架完整 commit SHA，以及测试运行环境。
2. **实验思路**：逐任务解释要解决的问题、关键数据结构、不变量、算法和设计取舍。同步相关任务需说明锁保护的状态、睡眠与唤醒条件及并发正确性。
3. **实现方式**：列出修改文件及主要函数，说明模块如何协作、控制流程及边界情况。可给关键伪代码，不需要大段粘贴实现代码。
4. **实验结果**：提供实际测试命令、输出或截图、通过与未通过的项目、必要的重复运行结果。说明输出为什么符合任务要求；不要只写“全部通过”。
5. **问题回答与分析**：完成本 Lab 的思考题、分析题，记录遇到的问题、定位过程、修复方式及已知限制。区分必做、选做和未完成部分。
6. **版本与改动清单**：起点标签/完整 SHA、完成标签/完整 SHA；Lab2 起再给出所继承的上次实验 SHA。说明代码提交方式和可复现步骤。

每个 Lab 页末还有该实验特有的报告要点，须一并完成。Lab0 沿用原说明中报告不计分的安排，但报告仍为必交材料。

## 代码提交方式

| 实验 | 建议方式 | 必要材料 |
| --- | --- | --- |
| Lab0 | 只交报告 | 本地启动结果、原任务问题回答；可在报告记录代码版本以便自查。 |
| Lab1–Lab2 | 增量 ZIP，也可个人 Git | PDF + 本 Lab 修改文件或可访问的固定 Git 提交。 |
| Lab3–Lab6、Final | 个人 Git，也可增量 ZIP | 累计实验依赖较多，Git 便于直接取得完整可运行版本及比较本 Lab 差异。 |
| Lab4 Condvar | 独立 ZIP 或独立 Git | 与内核分别记录版本，报告合并为 `学号-lab4.pdf`。 |

两种代码方式等效，任选一种，不要求重复提交。没有修改的框架文件、`.git`、构建产物、磁盘镜像和大体积日志不放入 ZIP。新增源码属于本次改动，必须提交；删除和重命名也必须明确记录。

## 方式 A：个人 Git 仓库

按[Git 工作流](./workflow.md)推送分支、起点标签和完成标签，然后在报告末尾写明：

```text
仓库 URL：自己的仓库地址
框架版本：本次 upstream/labN 的完整 SHA（在开始实验时记录）
上次实验版本：上一实验完成的完整 SHA（Lab1、Condvar 无需此项）
本次起点：labN-start + 完整 SHA
评分版本：labN-submit + 完整 SHA
改动清单：文件路径、对应任务、主要变化
构建和测试：具体命令、预期输出、已知限制
```

只给分支名或仓库首页不足以固定评分版本。确认助教可读取该 commit；私有库按课程公告配置访问，不能在报告内提供密码或令牌。评分针对报告中的 SHA；后续新 commit 不会自动替换已经提交的版本。

## 方式 B：仅本 Lab 修改文件的 ZIP

ZIP 是**增量提交**：Lab1 从官方 `lab1` 框架恢复；Lab2 起依赖上次已提交的代码和本次官方框架。助教应保留历次提交，按顺序还原。无法取得上一实验代码时，单独的本次 ZIP 不能构建，应改用可读取完整历史的个人 Git 仓库。Lab0 的演示改动不作为 Lab1 依赖，因此无需补交整份 Lab0 工程。

先按工作流完成提交并创建 `*-submit` 标签。推荐使用课程提供的增量打包工具（网站上的下载地址见下方）。把工具保存到**实验仓库之外**，例如 `~/os-course/package_submission.py`。

<a :href="withBase('/tools/package_submission.py')" download>下载 package_submission.py</a>

<script setup>
import { withBase } from 'vitepress'
</script>

工具要求 Python 3 和 Git 2.38 或更高版本，Ubuntu 24.04 自带 Git 满足要求。它只读取 Git 中已提交的版本，不代替 `git add` / `git commit`，且拒绝覆盖已有 ZIP。以下在内核代码仓库根目录运行，替换学号和开始实验时记录的框架 SHA：

```sh
# Lab1：不依赖学生的Lab0代码
python3 ../package_submission.py --lab lab1 --student YOUR_ID \
  --framework FRAMEWORK_SHA --start lab1-start --submit lab1-submit \
  --output ../YOUR_ID-lab1-code.zip

# Lab2 示例；以后替换相应Lab、上一完成标签和框架SHA
python3 ../package_submission.py --lab lab2 --student YOUR_ID \
  --framework FRAMEWORK_SHA --previous lab1-submit \
  --start lab2-start --submit lab2-submit \
  --output ../YOUR_ID-lab2-code.zip
```

`FRAMEWORK_SHA` 必须是本次合并的**实际框架提交**，不是“提交时最新的分支头”。开始实验时用 `git rev-parse upstream/lab2` 等命令记录。仓库不干净时先整理并提交源码；构建产物按已有 `.gitignore` 忽略，不要为通过打包检查而加入 Git。

Lab4 Condvar 在其独立目录中打包：

```sh
python3 ../package_submission.py --lab lab4-condvar --student YOUR_ID \
  --framework condvar-start --start condvar-start --submit condvar-submit \
  --output ../YOUR_ID-lab4-condvar-code.zip
```

ZIP 内包含：

- `files/`：保持仓库相对路径的本次新增/修改文件，也包含本次框架合并中解决冲突的文件。
- `submission.json`：框架、上次提交、起点和完成 SHA，文件清单、权限、最终源码树 SHA。
- `deleted.txt`：应删除的路径；重命名按删除旧路径并加入新路径表示。
- `README.txt`：还原提示。

工具相对于“本次框架与上次提交的自动合并结果”计算差异，因此不会遗漏创建 `*-start` 标签前解决的冲突，也不会把未修改的历次源码重新打包。提交前打开 ZIP 检查文件清单，并在报告解释每个修改文件。代码中如果修改了符号链接或子模块，请选择 Git 提交方式。

## 增量 ZIP 的审阅与还原

助教在独立目录取得本次框架与上一份已还原的提交。以下是 Lab2 起的审阅步骤；`FRAMEWORK_SHA`、`PREVIOUS_SHA` 都从 `submission.json` 读取：

```sh
git switch -c review-lab2 FRAMEWORK_SHA
git merge --no-commit --no-ff PREVIOUS_SHA
# 即使有冲突，也先保留现场；用已检查的ZIP中files/覆盖相应路径
# 按deleted.txt删除指定源码；按file_modes恢复可执行位
# 在独立审阅目录中暂存所有已还原源码，不包括ZIP或构建产物
git add -A
git diff --name-only --diff-filter=U  # 必须为空
git write-tree                     # 必须等于submission.json的submission_tree
```

Lab1 和 Condvar 只检出记录的框架 SHA，再覆盖对应 ZIP。压缩包解压到仓库以外，核对路径后再复制；不要将 `submission.json` 等元数据一起复制进源码。模式 `100755` 的文件应具有执行权限。

源码树相符后完成本地审阅提交、执行各 Lab 测试。通过 ZIP 重建的 commit SHA 与学生原 SHA 可能不同（作者与提交时间不同），应验证 **tree SHA**。继续还原下一 Lab 时，使用与学生上次提交 tree 相同的本地审阅提交作为上一版本，并保留框架祖先关系和审阅记录。若自动合并结果因历史差异不能重现，或最终 tree 不匹配，应要求提供能获取原始历史的 Git 提交，不应凭猜测给出测试结论。
