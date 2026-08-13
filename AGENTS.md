# Codex 阅读说明书

## 目标

这份仓库是一个翎风 / Mir200 系列传奇服务端工程。这个文件只给 Codex 和其他自动化代理阅读，用来快速理解工程结构、脚本分工、修改边界和静态检查重点。

## 总规则

- 只做静态阅读、静态分析和文本修改。
- 不要编译、不要启动服务端、不要尝试运行验证。
- 修改脚本时尽量只碰目标文件，别顺手重构无关目录。
- 保留原始编码、原始注释风格和原始缩进习惯。
- 这个工程里有很多中文脚本和配置，读写时要注意编码，不要把文件存坏。

## 编码处理规则

- 读取工程文本时默认按 ANSI 编码处理，优先使用 PowerShell 的 `-Encoding ansi`。
- 如果读取结果出现乱码，再对同一个文件尝试 UTF-8；不要因为文件包含中文就直接批量转换编码。
- 写回文件前先确认原文件编码；写回时必须保留原始编码、BOM 状态、换行风格和原有缩进。
- 如果无法确认编码，不要覆盖原文件；先保留原文并在说明中标记为待确认。
- `AGENTS.md`、`docs/` 和知识库 Markdown 当前按 UTF-8 维护；这不代表 `Mir200/Envir/` 下的脚本和配置也都是 UTF-8。

## 仓库总览

根目录下是典型的四合一服务端结构：

- `DBServer/`：数据库服务相关文件
- `LoginGate/`、`SelGate/`、`RunGate/`：登录与网关服务
- `LoginSrv/`：登录服务
- `LogServer/`：日志服务
- `Mir200/`：核心游戏服务器与脚本主目录
- `Mud2/`：数据库与部分底层数据
- `登录器/`：客户端启动器相关文件
- `Config.ini`：整套服务端的总配置入口，包含端口、启动方式、数据库路径等

## 关键入口

优先从这些文件看起：

- `Config.ini`：服务器各组件端口、启动参数、数据库路径
- `Mir200/!Setup.txt`：Mir200 主配置，体量很大，常作为核心运行参数参考
- `Mir200/Envir/MapInfo.txt`：地图属性、传送连接、禁用项、战斗/安全标记
- `Mir200/Envir/MerChant.txt`：NPC / 商人摆放表
- `Mir200/Envir/MonGen.txt`：怪物刷怪表
- `Mir200/Envir/MonItems/`、`MonUseItems/`：怪物掉落与使用物品配置
- `Mir200/Envir/Npc_def/`：NPC 定义脚本
- `Mir200/Envir/Market_def/`：商店、对话、功能 NPC 脚本
- `Mir200/Envir/QuestDiary/`：功能脚本与任务脚本主区域
- `Mir200/Envir/Robot_def/`：自动定时与机器人脚本
- `Mir200/Envir/MapQuest_def/`：地图触发类脚本
- `Mir200/Envir/UserData/`：用户自定义数据和自定义技能数据

## 这个工程的脚本分层

### 1. `Market_def/`

这里通常放“可交互 NPC / 商城 / 功能入口”类脚本，很多内容是菜单、兑换、传送、回收、仓库、商店、辅助功能。

从现有内容看，常见区域包括：

- 各主城分类目录，例如 `比奇城`、`盟重城`、`魔龙城`、`白日门` 等
- 功能分类目录，例如 `洗装备`
- 特殊区域目录，例如 `其它区域`、`幻境-影之道`

这类脚本常会直接调用 `GIVE`、`TAKE`、`GAMEGOLD`、`MAPMOVE`、`CreateNPC`、`GetListString`、`GetStringPosEX` 之类动作。

### 2. `Npc_def/`

这里是 NPC 定义脚本，偏“入口绑定”和“NPC 行为总脚本”。

当前仓库里能直接看到的例子有：

- `公告牌-GM001.txt`
- `比奇国王-0122.txt`
- `沙城总管-0150.txt`
- `红娘-M101.txt`
- `月老-M101.txt`

### 3. `QuestDiary/`

这里是最重要的功能脚本区，通常按“系统功能 / 活动 / 数据文件 / 专题功能”组织。

你这套工程里已经很明显地分成了：

- `系统功能/`：通用功能主脚本
- `系统功能/老登辅助/`：本服定制辅助功能
- `系统功能/装备回收/`：装备分类回收脚本
- `数据文件/`：名单、秘钥、检测、记录等持久文本
- `新爆率/`：爆率或怪物掉落相关脚本
- `荣誉勋章/`、`典狱长功能/`、`天下第一/` 等专题模块

这里很适合先找入口，再顺着 `#CALL`、`GOTO`、`GetListString`、`DelTextListLine` 一层层追。

### 4. `Robot_def/`

这里是自动执行脚本，和时间、活动、轮询、挂机管理相关。

例如：

- `AutoRunRobot.txt`
- `RobotManage.txt`

### 5. `MapInfo.txt`

这是地图规则和地图连通关系的总表，包含：

- 地图属性
- 禁止回城、禁止随机、战斗地图、安全地图等标记
- 坐标传送连接
- 部分地图限制项

改地图传送、限制、地图状态时，先看这个文件。

## 这套工程的常见写法

- 脚本基本按 `[@标签]` 分段，常见结构是 `#IF`、`#ACT`、`#SAY`、`#ELSEACT`
- 条件判断经常和动作写在同一段里
- 功能脚本常把“界面、判断、执行、反馈”写在一个文件里
- 数据常落到 `QuestDiary/数据文件/` 或各类名单文本里
- 自动化常依赖全局变量、列表文件和定时触发

## 杀怪触发规则

- `[@OnKillMob]` 必须配合地图参数 `ONKILLMON` 才能触发。
- `[@KillMon]` 不需要地图参数 `ONKILLMON`；不要把两种触发入口混为一谈。
- `[@HeroKillMon]` 是英雄独立击杀触发入口，是否独立触发还要结合英雄设置判断。
- 地图开放、首杀或 Boss 推进必须使用完整怪物名匹配，名称必须和 `MonGen.txt` 中的实际名称完全一致。
- 不得用模糊包含、前缀匹配或自动忽略数字/括号后缀替代完整匹配。`牛魔王`、`牛魔王8`、`赤月恶魔`、`赤月恶魔8` 应视为不同名称，除非设计明确把它们分别列为允许目标。
- 同名 Boss 可能出现在多个地图；完整怪物名之外，还必须校验当前地图和当前开放阶段，避免其他地图的同名怪物提前推进世界阶段。

## Codex 修改时要注意的点

- 不要把样本文件当成单纯示例；很多就是现网逻辑。
- `Config.ini` 里有些路径是旧机器绝对路径，迁移或阅读时要特别小心。
- `Mir200` 下很多文本是中文编码文件，直接改写时要避免乱码。
- `MapInfo.txt`、`MerChant.txt`、`MonGen.txt`、`Npcs.txt` 这类文件通常牵一发而动全身。
- `QuestDiary/数据文件/` 下的名单类文本经常是运行时依赖，不要随手清空。
- 二进制文件如 `.exe`、`.dat`、`.mdb`、`.lic` 不要编辑。

## 工具化与 Skill 升级

- 遇到重复、批量或跨文件的 Mir200 文本修改时，优先沉淀为项目工具脚本，而不是每次临时拼大段 PowerShell。
- 工具脚本建议放在 `tools/` 下，命名要说明用途，例如 `mir200-maplinks.ps1`、`mir200-stagecheck.ps1`、`mir200-encoding.ps1`。
- 工具脚本必须默认保护 GBK / ANSI 文本：读取前识别编码，写回时保留原编码、BOM、换行风格和缩进习惯。
- `Mir200/Envir/**/*.txt` 的批量编辑优先走这些项目工具；`AGENTS.md`、`docs/`、`.vscode/*.json` 等 UTF-8 文档和配置可用普通补丁方式修改。
- 如果一次任务中总结出稳定规则，例如 `MapInfo.txt` 链接解析、动态地图门生成、防偷渡验证、Boss 完整名校验，应同步更新 `lf-mir200-knowledge` skill 或其参考文档。
- 当用户要求“沉淀到 skill”“更新 skill”“写进知识库”这类持久化经验时，必须同时更新 skill 源仓库 `D:\wangsiProject\LF知识库搭建\codex-skills\lf-mir200-knowledge\`，再按需要同步本机安装版 `C:\Users\admin\.codex\skills\lf-mir200-knowledge\`，避免只改运行副本导致源仓库遗漏。
- 更新 skill 时不要只记录本次操作流水账，要提炼成可复用规则：触发条件、读取顺序、命令语法依据、编辑边界、静态验证方法。
- 本仓库的 `AGENTS.md` 和 `docs/*.md` 是项目知识源；Mir200 相关 skill 在处理本仓库前应优先读取这些 Markdown，再结合本地手册和样本脚本判断。

当前可用项目工具：

- `tools/mir200-common.ps1`：公共 GBK / UTF-8 读写、换行识别、`MapInfo.txt` 链接解析、地图阶段表解析函数。
- `tools/mir200-encoding.ps1`：按项目规则列出文件应使用的编码；默认 `.txt` 走 GBK，`AGENTS.md`、`docs/`、`.vscode/*.json` 等走 UTF-8。
- `tools/mir200-maplinks.ps1`：导出 `MapInfo.txt` 中的自然地图链接，支持按源地图或目标地图过滤。
- `tools/mir200-stagecheck.ps1`：结合 `地图开放.txt` 阶段表检查 `MapInfo.txt` 是否仍有低阶段直达高阶段的静态链接。
- `tools/mir200-stditems.ps1`：离线维护 `Mud2/DB/GEEM2.db` 的 `StdItems`；默认预览，`-Apply` 写入前自动备份，支持 `-SpecPath` 读取 UTF-8 CSV 规格。

常用静态验证命令：

```powershell
.\tools\mir200-maplinks.ps1 -SourceMap 0
.\tools\mir200-stagecheck.ps1
.\tools\mir200-encoding.ps1 -Path AGENTS.md,docs,.vscode,Mir200\Envir\MapInfo.txt
.\tools\mir200-stditems.ps1 -Check
```

## 地图阶段与防偷渡

- 地图开放阶段由全局变量 `G0` 表示时，必须明确每个阶段对应的地图清单、推进 Boss、Boss 完整名称、Boss 地图和下一阶段值。
- 阶段推进只能从当前阶段进入紧邻的下一阶段；不得因为击杀同名怪、脚本重复触发或异常变量值跳过阶段。
- 任何进入地图的路径都必须经过同一套目的地阶段检查，不能只封 NPC 按钮。
- 静态排查至少覆盖：
  - `MapInfo.txt` 的坐标直连、地图门和自然传送；
  - NPC / 商人脚本中的 `MAPMOVE`、`MAP`、`GROUPMAPMOVE`、`MAPS`；
  - `RECALL`、`RECALLMAP`、`ExchangeMap`、组队/行会/夫妻/师徒/英雄召回；
  - 动态地图、副本、镜像地图、`MONGEN`、`MONGENEX`、`CreateNPC`；
  - 回城卷、随机传送、地牢逃脱、行会回城、传送符及其礼包/绑定版本；
  - 重连回地图、死亡/复活、活动/任务/机器人脚本和 GM 命令；
  - 随机移动、地图事件、挂机辅助和其他自动传送逻辑。
- 所有目标地图都要归属一个开放阶段；允许退出到已开放安全地图的回城逻辑，也必须确认不会把玩家带入未开放地图。
- 对已在高级地图中的玩家，设计必须明确“正常推进后保留”与“异常越境后的纠正”两种情况；纠正动作和触发点必须以本地手册和现有脚本支持为准，不得臆造命令。
- 普通玩家不得通过组队、召回、活动、副本、重连或道具绕过阶段限制；管理员例外必须显式、单独判断。

## 建议的阅读顺序

1. `Config.ini`
2. `Mir200/!Setup.txt`
3. `Mir200/Envir/MapInfo.txt`
4. `Mir200/Envir/MerChant.txt`
5. `Mir200/Envir/MonGen.txt`
6. `Mir200/Envir/Npc_def/`
7. `Mir200/Envir/Market_def/`
8. `Mir200/Envir/QuestDiary/`
9. `Mir200/Envir/Robot_def/`

## 静态检查建议

改完脚本后，至少人工核对这些点：

- 文件路径是否写对
- `#CALL`、`GetListString`、`GetStringPosEX` 等引用路径是否仍然存在
- 新增或修改的标签名是否和跳转目标一致
- 菜单文本和动作是否仍然匹配
- 数据文件的读写格式是否被破坏
- 是否误改了共享配置或二进制文件

## 本仓库里的参考知识库

Mir200 相关本地知识库和样本脚本位于：

- `C:\Users\admin\.codex\skills\lf-mir200-knowledge\references\mir200-thinking.md`
- `C:\Users\admin\.codex\skills\lf-mir200-knowledge\references\local-layout.md`

当需要判断脚本风格、目录职责或常见写法时，优先以这些本地知识和样本脚本为准。
