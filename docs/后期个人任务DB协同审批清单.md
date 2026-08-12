# 后期个人任务 DB 协同审批清单

本文记录 `Mud2/DB/GEEM2.db` 入库审批与执行结果。本次已通过工具写入 `StdItems`，并保留写库前备份。

配套工具：

```powershell
.\tools\mir200-stditems.ps1
.\tools\mir200-stditems.ps1 -Apply
.\tools\mir200-stditems.ps1 -Check
.\tools\mir200-stditems.ps1 -SpecPath docs\后期个人任务StdItems.csv
```

默认不带 `-Apply` 时只预览；带 `-Apply` 时会先备份数据库。

## 当前执行结果

- 已入库 `雪域魂器残片`、`狐月引路符`、`雪域寻魂`、`火龙余烬`、`狐月问道`。
- 已备份：`Mud2/DB/GEEM2.db.bak-before-stditems-20260812-181512`。
- 任务脚本已切换为正式发放 `雪域魂器残片`、`狐月引路符` 和三个称号。
- 已同步 `ItemDescList.txt`、`FilterItemList.txt`、`ItemRuleList.txt`。

## 已确认可引用项

这些名称已在 `StdItems` 中存在，当前脚本可直接使用：

| 名称 | 用途 |
| --- | --- |
| `火龙凭证` | 雪域奖励 / 火龙前置 |
| `冰核` | 雪域交付材料 |
| `先驱者遗骸` | 王大娘交付材料 |
| `焰魂龙纹` | 火龙章节证明 |
| `避寒神丹` | 雪域奖励 |
| `狐火` | 狐月材料 / 临时引路凭据 |
| `皓月晶石` | 狐月材料和奖励 |
| `装备转移宝盒` | 终章奖励 |
| `火龙勇士` | 既有称号模板 |
| `登峰造极` | 既有称号模板 |

## 已新增项

| 名称 | 推荐模板 | 用途 |
| --- | --- | --- |
| `雪域魂器残片` | 复制 `冰核` | 雪域章节剧情凭据 |
| `狐月引路符` | 复制 `火龙凭证` | 火龙章节完成后的狐月引路凭据 |
| `雪域寻魂` | 复制 `火龙勇士` | 雪域章节完成称号 |
| `火龙余烬` | 复制 `火龙勇士` | 火龙章节完成称号 |
| `狐月问道` | 复制 `登峰造极` | 后期个人奇遇终章称号 |

## SQL 草案参考

入库前静态读取 `StdItems` 最大 `Idx=1060`，本次实际使用 `1061` 到 `1065`。

以后优先使用 `tools/mir200-stditems.ps1`，下面 SQL 仅作为人工复核参考。

```sql
BEGIN TRANSACTION;

INSERT INTO StdItems
SELECT 1061, '雪域魂器残片', StdMode, Shape, Weight, Anicount, Source, Reserved, Looks, DuraMax,
       Ac, AC2, Mac, Mac2, Dc, Dc2, Mc, Mc2, Sc, Sc2, Need, NeedLevel, Price, Stock, Color,
       OverLap, HP, MP, Light, element, element1, element2, element3, element4, element5,
       element6, element7, element8, element9, element10, element11, element12, element13,
       element14, element15, element16, element17, element18, element19, element20, element21,
       element22, element23, element24, Value26, Value27, Value28, Value29, Value30,
       InsuranceGold, InsuranceCurrency, Expand1, Expand2, Expand3, Expand4, Expand5, Horse,
       Element25, Asc, Asc2, Arc, Arc2, Mpc, Mpc2, Job, Element26, CustomItem
FROM StdItems WHERE Name='冰核';

INSERT INTO StdItems
SELECT 1062, '狐月引路符', StdMode, Shape, Weight, Anicount, Source, Reserved, Looks, DuraMax,
       Ac, AC2, Mac, Mac2, Dc, Dc2, Mc, Mc2, Sc, Sc2, Need, NeedLevel, Price, Stock, Color,
       OverLap, HP, MP, Light, element, element1, element2, element3, element4, element5,
       element6, element7, element8, element9, element10, element11, element12, element13,
       element14, element15, element16, element17, element18, element19, element20, element21,
       element22, element23, element24, Value26, Value27, Value28, Value29, Value30,
       InsuranceGold, InsuranceCurrency, Expand1, Expand2, Expand3, Expand4, Expand5, Horse,
       Element25, Asc, Asc2, Arc, Arc2, Mpc, Mpc2, Job, Element26, CustomItem
FROM StdItems WHERE Name='火龙凭证';

INSERT INTO StdItems
SELECT 1063, '雪域寻魂', StdMode, Shape, Weight, Anicount, Source, Reserved, Looks, DuraMax,
       Ac, AC2, Mac, Mac2, Dc, Dc2, Mc, Mc2, Sc, Sc2, Need, NeedLevel, Price, Stock, Color,
       OverLap, HP, MP, Light, element, element1, element2, element3, element4, element5,
       element6, element7, element8, element9, element10, element11, element12, element13,
       element14, element15, element16, element17, element18, element19, element20, element21,
       element22, element23, element24, Value26, Value27, Value28, Value29, Value30,
       InsuranceGold, InsuranceCurrency, Expand1, Expand2, Expand3, Expand4, Expand5, Horse,
       Element25, Asc, Asc2, Arc, Arc2, Mpc, Mpc2, Job, Element26, CustomItem
FROM StdItems WHERE Name='火龙勇士';

INSERT INTO StdItems
SELECT 1064, '火龙余烬', StdMode, Shape, Weight, Anicount, Source, Reserved, Looks, DuraMax,
       Ac, AC2, Mac, Mac2, Dc, Dc2, Mc, Mc2, Sc, Sc2, Need, NeedLevel, Price, Stock, Color,
       OverLap, HP, MP, Light, element, element1, element2, element3, element4, element5,
       element6, element7, element8, element9, element10, element11, element12, element13,
       element14, element15, element16, element17, element18, element19, element20, element21,
       element22, element23, element24, Value26, Value27, Value28, Value29, Value30,
       InsuranceGold, InsuranceCurrency, Expand1, Expand2, Expand3, Expand4, Expand5, Horse,
       Element25, Asc, Asc2, Arc, Arc2, Mpc, Mpc2, Job, Element26, CustomItem
FROM StdItems WHERE Name='火龙勇士';

INSERT INTO StdItems
SELECT 1065, '狐月问道', StdMode, Shape, Weight, Anicount, Source, Reserved, Looks, DuraMax,
       Ac, AC2, Mac, Mac2, Dc, Dc2, Mc, Mc2, Sc, Sc2, Need, NeedLevel, Price, Stock, Color,
       OverLap, HP, MP, Light, element, element1, element2, element3, element4, element5,
       element6, element7, element8, element9, element10, element11, element12, element13,
       element14, element15, element16, element17, element18, element19, element20, element21,
       element22, element23, element24, Value26, Value27, Value28, Value29, Value30,
       InsuranceGold, InsuranceCurrency, Expand1, Expand2, Expand3, Expand4, Expand5, Horse,
       Element25, Asc, Asc2, Arc, Arc2, Mpc, Mpc2, Job, Element26, CustomItem
FROM StdItems WHERE Name='登峰造极';

COMMIT;
```

## 脚本切换点

DB 入库并静态确认后，已切换以下脚本：

- 雪域魂器交付：发放 `雪域魂器残片`。
- 穆家店收束雪域：追加 `GIVEFENGHAO 雪域寻魂`。
- 云隐宗师收束火龙：发放 `狐月引路符`，追加 `GIVEFENGHAO 火龙余烬`。
- 狐月终章：追加 `GIVEFENGHAO 狐月问道`。
- `ItemDescList.txt`、`FilterItemList.txt`、`ItemRuleList.txt`：已补说明、拾取过滤、任务物品规则。
