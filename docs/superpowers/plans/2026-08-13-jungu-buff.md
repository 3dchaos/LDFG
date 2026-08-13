# 军鼓位 54 件玩法 BUFF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给当前版本已写入数据库的 54 件 `StdMode=65` 军鼓位装备接入玩法 BUFF，做到装备仍在 14 位时持续生效，装备异常消失、死亡掉落、脚本回收或卸下后能自动取消。

**Architecture:** 使用“装备状态检测 + 短时刷新”的方案：每 2 秒读取 14 号装备位数据库名，匹配 54 件道具后写入 3 秒在线临时属性，并显示 3 秒图标。所有常驻属性都用短时 `ChangeHumAbility = ... 3`、`AddHumNewValue = ... 3` 和掉血前触发加码表达，停止刷新后自然过期；清理逻辑只清本系统变量和图标，不主动把人物属性归零，避免误清其他系统 BUFF。

**Tech Stack:** Mir200 / 翎风脚本、GBK/ANSI 文本、PowerShell 静态验证工具、现有 `tools/mir200-common.ps1` 编码辅助。

---

## Design Table

| 方向 | 职业 | 核心定位 | 常驻短时效果 | 顶级副效果 |
| --- | --- | --- | --- | --- |
| 拆门板 | 战士 | 破防爆发 | 攻击、暴击、忽视防御 | `压轴/封顶` 在 `@AttackDamage` 额外加伤 |
| 铁头娃 | 战士 | 肉盾抗揍 | 防御、魔御、HP、物魔减伤 | `压轴/封顶` 在 `@StruckDamage` 额外减伤和少量反伤 |
| 剁馅机 | 战士 | 快刀命中 | 攻击、准确、暴击、攻击伤害 | `压轴/封顶` 在 `@AttackDamage` 额外加伤 |
| 电耗子 | 法师 | 雷系爆发 | 魔法、魔法躲避、暴击、攻击伤害 | `压轴/封顶` 命中时短压目标魔御百分比 |
| 火葫芦 | 法师 | 火系烧怪 | 魔法、攻击伤害、杀怪爆率 | `压轴/封顶` 在 `@AttackDamage` 额外加伤 |
| 小冰箱 | 法师 | 冰盾生存 | 魔御、HP/MP、魔伤减、防冰冻 | `压轴/封顶` 在 `@StruckDamage` 额外减伤 |
| 养娃人 | 道士 | 召唤强化 | 道术、暴击抗性、宝宝伤害触发增强 | `压轴/封顶` 在 `@SlaveAttackDamage` 额外加宝宝伤害 |
| 奶不死 | 道士 | 辅助续航 | 防御、魔御、HP/MP、HP/MP 恢复、暴击抗性 | `压轴/封顶` 在 `@StruckDamage` 额外减伤 |
| 毒嘴子 | 道士 | 毒咒伤害 | 道术、毒恢复/毒躲避/魔法躲避、暴击 | `压轴/封顶` 命中时短压目标防御/魔御百分比 |

## Quality Scaling

| 品质 | 品质值 | 小点数 | 大点数 | 百分比 | 隐藏元素 | HP/MP | 顶级加码 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 粗坯 | 1 | 1 | 2 | 2 | 1 | 50 | 0 |
| 精制 | 2 | 2 | 3 | 3 | 2 | 80 | 0 |
| 淬火 | 3 | 3 | 5 | 4 | 3 | 120 | 0 |
| 成名 | 4 | 4 | 7 | 5 | 4 | 180 | 0 |
| 压轴 | 5 | 5 | 9 | 6 | 5 | 250 | 2 |
| 封顶 | 6 | 6 | 12 | 8 | 6 | 350 | 3 |

## Files

| 类型 | 路径 | 责任 |
| --- | --- | --- |
| Create | `Mir200/Envir/QuestDiary/系统功能/军鼓BUFF.txt` | 14 位检测、54 件名字映射、短时属性应用、战斗触发加码、清理逻辑 |
| Modify | `Mir200/Envir/Market_def/QFunction-0.txt` | 增加装备穿脱、死亡、掉血前、宝宝掉血前等 QF 钩子 |
| Modify | `Mir200/Envir/MapQuest_def/QManage.txt` | 登录刷新和 `@OnTimer87` 个人定时刷新 |
| Modify | `Mir200/Envir/QuestDiary/系统功能/老登辅助/攻击触发.txt` | 在现有攻击触发中调用军鼓状态轻刷新 |
| Modify | `Mir200/Envir/QuestDiary/系统功能/老登辅助/死亡触发.txt` | 死亡逻辑开头调用军鼓死亡检查 |
| Modify | `tools/check-jungu-buff.ps1` | 静态验证 54 件覆盖、钩子、定时器、清理入口 |
| Reference | `docs/军鼓位玩法StdItems.csv` | 54 件道具名字和职业方向来源 |

## Implementation Tasks

### Task 1: Strengthen Static Check

**Files:**
- Modify: `tools/check-jungu-buff.ps1`

- [x] **Step 1: Extend the checker to read `docs/军鼓位玩法StdItems.csv`.**

Implementation detail:

```powershell
$specRows = Import-Csv -LiteralPath $specPath -Encoding utf8
if ($specRows.Count -ne 54) {
    $fail += "expected 54 spec rows, got $($specRows.Count)"
}
foreach ($row in $specRows) {
    if ($row.StdMode -ne '65') {
        $fail += "non StdMode=65 item in spec: $($row.Name)"
    }
}
```

- [x] **Step 2: Verify every CSV name appears exactly once in `军鼓BUFF.txt`.**

Implementation detail:

```powershell
$buffText = Get-Content -LiteralPath $scriptPath -Encoding ansi -Raw
foreach ($row in $specRows) {
    $count = ([regex]::Matches($buffText, [regex]::Escape($row.Name))).Count
    if ($count -ne 1) {
        $fail += "item name coverage error: $($row.Name) appears $count times"
    }
}
```

- [x] **Step 3: Verify core labels and safety commands exist.**

Required labels/commands:

```text
[@军鼓BUFF_刷新]
[@军鼓BUFF_应用]
[@军鼓BUFF_战斗确认]
[@军鼓BUFF_攻击触发]
[@军鼓BUFF_攻击掉血前]
[@军鼓BUFF_被打掉血前]
[@军鼓BUFF_宝宝掉血前]
[@军鼓BUFF_死亡检查]
[@军鼓BUFF_清理]
CHECKUSEITEM 14
GetItemFieldValue 14 name S$军鼓名称
SetOnTimer 87 2
SETOFFTIMER 87
CloseArrBuff 1 87
```

- [x] **Step 4: Run checker and confirm RED state before production edits.**

Run:

```powershell
.\tools\check-jungu-buff.ps1
```

Expected: fails because `Mir200/Envir/QuestDiary/系统功能/军鼓BUFF.txt` does not exist yet and QFunction/QManage hooks are absent.

### Task 2: Create Main BUFF Script

**Files:**
- Create: `Mir200/Envir/QuestDiary/系统功能/军鼓BUFF.txt`

- [x] **Step 1: Create the file with GBK/ANSI encoding.**

Use `tools/mir200-common.ps1` or `[Text.Encoding]::GetEncoding(936)`; do not use UTF-8 patch for this file.

- [x] **Step 2: Add `@军鼓BUFF_刷新`.**

Behavior:

```text
1. If `NOT CHECKUSEITEM 14`, call `@军鼓BUFF_清理` and `BREAK`.
2. Read `GetItemFieldValue 14 name S$军鼓名称`.
3. Clear `N$军鼓有效`, `S$军鼓方向`, `N$军鼓品质`, `N$军鼓战斗确认`.
4. Exact-match all 54 item names from `docs/军鼓位玩法StdItems.csv`.
5. For each match, set:
   - `N$军鼓有效 1`
   - `N$军鼓品质 1..6`
   - `S$军鼓方向 拆门板/铁头娃/剁馅机/电耗子/火葫芦/小冰箱/养娃人/奶不死/毒嘴子`
   - `GOTO @军鼓BUFF_应用`
   - `BREAK`
6. If no match, call `@军鼓BUFF_清理`.
```

- [x] **Step 3: Add `@军鼓BUFF_应用`.**

Behavior:

```text
1. Map quality 1..6 to the numeric table in `Quality Scaling`.
2. Start `SetOnTimer 87 2`.
3. Display `SetArrBuff 1 87 1 1681 3 1 1682 1 [玩法印记]<$STR(S$军鼓名称)>`.
4. Apply only the current职业 + direction branch.
5. Use short 3-second effects only.
6. Use `LockUpdateAbil` / `UpdateAbil` around grouped `ChangeHumAbility` / `AddHumNewValue`.
7. Do not use high-frequency `ChangeSpeed` in the refresh loop; local history says speed changes can stack, so the safe version expresses speed schools through accuracy, hidden damage, and damage-before-hit bonuses.
8. Do not use high-frequency `ChangeSlaveAbilityEX` in the refresh loop; 养娃人的宝宝增幅 is applied through `@SlaveAttackDamage`, which is per-hit and cannot leave stale pet stats.
```

- [x] **Step 4: Add combat confirmation label.**

Behavior:

```text
[@军鼓BUFF_战斗确认]
If `N$军鼓有效` is not 1, set `N$军鼓战斗确认 0` and break.
If 14 slot is empty, call clear and break.
Read `GetItemFieldValue 14 name S$军鼓确认名`.
If `S$军鼓确认名` equals `S$军鼓名称`, set `N$军鼓战斗确认 1`.
Else set `N$军鼓战斗确认 0`, call refresh, and break.
```

- [x] **Step 5: Add combat bonus labels.**

Labels:

```text
[@军鼓BUFF_攻击触发]
[@军鼓BUFF_攻击掉血前]
[@军鼓BUFF_被打掉血前]
[@军鼓BUFF_宝宝掉血前]
```

Rules:

```text
攻击掉血前:
- 拆门板、剁馅机、电耗子、火葫芦、毒嘴子 can increase damage by the current quality percent.
- 压轴/封顶 add `N$军鼓顶级加码`.
- 电耗子 top tier may short-lower target magic defense percentage through `M.ChangeHumAbilityPercentage 3/4`.
- 毒嘴子 top tier may short-lower target defense/magic defense percentage through `M.ChangeHumAbilityPercentage 1/2/3/4`.

被打掉血前:
- 铁头娃、小冰箱、奶不死 reduce current damage by current quality element/percent.
- 压轴/封顶 add `N$军鼓顶级加码`.

宝宝掉血前:
- 养娃人 only, Taoist only, increases slave damage.
```

- [x] **Step 6: Add cleanup labels.**

Labels:

```text
[@军鼓BUFF_死亡检查]
[@军鼓BUFF_清理]
```

Rules:

```text
死亡检查:
- Clear active markers and close icon.
- Keep timer on for one more 2-second pass, so if a replacement/death-protection script keeps the equipment in slot 14, the buff is rebuilt automatically.

清理:
- Clear only `S$军鼓*` and `N$军鼓*` variables.
- `SETOFFTIMER 87`.
- `CloseArrBuff 1 87`.
- Do not reset ChangeHumAbility/AddHumNewValue/ChangeSpeed to zero.
```

### Task 3: Wire QFunction Callbacks

**Files:**
- Modify: `Mir200/Envir/Market_def/QFunction-0.txt`

- [x] **Step 1: Add slot 14 equip/unequip hooks near the top of QFunction.**

Add:

```text
;军鼓位装备触发
[@TakeOnEx]
#IF
EQUAL <$CurItemPos> 14
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_刷新
BREAK

[@TakeOffEx]
#IF
EQUAL <$CurItemPos> 14
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_清理
BREAK
```

- [x] **Step 2: Add optional drop cleanup hook.**

Add:

```text
[@HumDropItem]
#IF
EQUAL <$CurItemPos> 14
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_清理
BREAK
```

Note: official manual says `@HumDropItem` only fires for item-rule-enabled rows; this hook is a best-effort fast cleanup. The timer remains the real safety net.

- [x] **Step 3: Add damage callbacks.**

Add labels:

```text
[@AttackDamage]
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_攻击掉血前

[@StruckDamage]
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_被打掉血前
```

- [x] **Step 4: Extend existing `@SlaveAttackDamage`.**

Current file already has `[@SlaveAttackDamage]` calling old attack logic. Insert before the old call:

```text
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_宝宝掉血前
```

- [x] **Step 5: Extend existing `@PlayDie`.**

Insert before old death script call:

```text
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_死亡检查
```

### Task 4: Wire QManage Timer And Login

**Files:**
- Modify: `Mir200/Envir/MapQuest_def/QManage.txt`

- [x] **Step 1: Add timer 87 handler.**

Add near other timer labels:

```text
;军鼓位BUFF刷新
[@OnTimer87]
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_刷新
```

- [x] **Step 2: Add login refresh.**

Inside `[@Login]` first `#ACT` block, add:

```text
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_刷新
```

### Task 5: Wire Existing Helper Scripts

**Files:**
- Modify: `Mir200/Envir/QuestDiary/系统功能/老登辅助/攻击触发.txt`
- Modify: `Mir200/Envir/QuestDiary/系统功能/老登辅助/死亡触发.txt`

- [x] **Step 1: Add lightweight attack refresh.**

In `[@攻击触发]` at the start of `#ACT`, add:

```text
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_攻击触发
```

- [x] **Step 2: Add death cleanup to helper script.**

In `[@死亡触发]` at the start of the script body, add:

```text
#IF
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_死亡检查
```

This duplicates the QFunction death call intentionally; both call an idempotent cleanup/recheck label, protecting future edits if one path is moved.

### Task 6: Static Validation

**Files:**
- Validate: all modified files

- [x] **Step 1: Run the static buff checker.**

Run:

```powershell
.\tools\check-jungu-buff.ps1
```

Expected:

```text
jungu buff static check ok
```

- [x] **Step 2: Run project encoding check for touched Mir200 files and docs.**

Run:

```powershell
.\tools\mir200-encoding.ps1 -Path docs,tools,Mir200\Envir\Market_def\QFunction-0.txt,Mir200\Envir\MapQuest_def\QManage.txt,Mir200\Envir\QuestDiary\系统功能\军鼓BUFF.txt,Mir200\Envir\QuestDiary\系统功能\老登辅助\攻击触发.txt,Mir200\Envir\QuestDiary\系统功能\老登辅助\死亡触发.txt
```

Expected: docs/tools as UTF-8, Mir200 `.txt` as GBK/ANSI.

- [x] **Step 3: Run focused static searches.**

Run:

```powershell
rg -n "军鼓BUFF|OnTimer87|TakeOnEx|TakeOffEx|AttackDamage|StruckDamage|HumDropItem" "Mir200\Envir\Market_def\QFunction-0.txt" "Mir200\Envir\MapQuest_def\QManage.txt" "Mir200\Envir\QuestDiary\系统功能\军鼓BUFF.txt" "Mir200\Envir\QuestDiary\系统功能\老登辅助\攻击触发.txt" "Mir200\Envir\QuestDiary\系统功能\老登辅助\死亡触发.txt"
```

Expected: all planned labels and calls are visible, with no duplicated accidental blocks.

- [x] **Step 4: Check all 54 item names still exist in database spec.**

Run:

```powershell
.\tools\mir200-stditems.ps1 -Check
```

Expected: existing StdItems check succeeds. Do not compile or start server.

## Edge Case Matrix

| Case | Protection |
| --- | --- |
| Normal equip | `@TakeOnEx` immediately refreshes and starts timer |
| Normal unequip | `@TakeOffEx` clears marker, closes icon, stops timer |
| Durability consumed and equipment disappears | Next `@OnTimer87` sees no `CHECKUSEITEM 14`, clears and stops; 3-second effects expire |
| Death drops equipped item | `@PlayDie` and helper death script call death check; timer gets one more pass to rebuild only if item remains |
| Script recovery / `TakePosW 14` / forced removal | Timer detects missing slot within 2 seconds; effects expire after 3 seconds |
| Item renamed | `GetItemFieldValue 14 name` reads database name, so renamed display names do not break matching |
| Wrong profession wears item | The item is recognized and icon appears, but only matching职业 branch applies stats; this can be changed later by adding cross-class fallback |
| Damage callback fires after stale state | `@军鼓BUFF_战斗确认` rereads slot 14 before applying combat bonus |

## Self-Review Notes

- This plan does not require item-rule rows for correctness; `@HumDropItem` is only an optional fast cleanup hook.
- This plan avoids permanent `ChangeHumAbilityEX` and permanent item mutation.
- This plan avoids explicit zeroing of general temporary player attributes during cleanup to avoid removing unrelated buffs.
- Static validation is limited by project instruction: no compile, no server start, no runtime verification.
