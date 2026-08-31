英雄引路人的出现逻辑是：

入口在 [AutoRunRobot.txt](D:/wangsiProject/老登四合一GitHub/Mir200/Envir/Robot_def/AutoRunRobot.txt:20)：

```txt
#AutoRun NPC HOUR 1 @英雄偶遇
```

也就是机器人脚本每 1 小时触发一次 `@英雄偶遇`，再由 [RobotManage.txt](D:/wangsiProject/老登四合一GitHub/Mir200/Envir/Robot_def/RobotManage.txt:229) 转调：

```txt
#CALL [系统功能\随机英雄NPC.txt] @英雄偶遇
```

真正条件在 [随机英雄NPC.txt](D:/wangsiProject/老登四合一GitHub/Mir200/Envir/QuestDiary/系统功能/随机英雄NPC.txt:1)：

```txt
LARGE G0 3
EQUAL G3 0
RANDOM 50
```

所以出现情况是：

- `G0 > 3`，也就是世界进度至少到 `4` 及以后。
- `G3 = 0`，也就是英雄功能还没正式开放。
- 每小时检测一次，每次 `RANDOM 50`，按 Mir 脚本常见规则是 `1/50` 概率触发。

换成人话：世界进度到第 4 阶段以后，并且全服还没开启英雄功能时，系统每小时抽一次，约 `1/50` 几率刷出英雄引路人。期望大概 50 小时出一次，但随机不是保底。

刷出后会先删除旧的英雄引路人，然后在这 8 张地图里随机选一张，随机坐标创建：

```txt
0      比奇省
1      沃玛森林
2      毒蛇山谷
11     白日门
12     丛林迷宫
D1002  赤月峡谷广场
D1004  抉择之地
4      封魔谷
```

玩家点英雄引路人后，支付 `2个金砖`，再走 [英雄引路人.txt](D:/wangsiProject/老登四合一GitHub/Mir200/Envir/Market_def/英雄引路人.txt:14) 的 `RANDOM 3`：成功约 `1/3`，成功后 `MOV G3 1`，全服英雄功能正式开放；失败则删除这个 NPC，下次继续等每小时抽。