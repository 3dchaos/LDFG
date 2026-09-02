# -*- coding: utf-8 -*-
"""apply_hero_jungu_stage1.py   v2
阶段1：英雄军鼓最小常驻闭环 —— GBK 安全落盘。

改动：
  1) 军鼓BUFF.txt    : 收敛英雄固定攻速3 -> 完整攻速/施法速度汇总；末尾追加 @英雄军鼓_* 主段
                       (英雄军鼓复用玩家 87 定时器续期，不独占新定时器号)
  2) QFunction-0.txt : 新增 @HeroTakeOnEx/@HeroTakeOffEx/@HeroDie 英雄军鼓回调
  3) QManage.txt     : @HeroLogin 改调英雄军鼓刷新；@OnTimer87 追加英雄在线续期

注意：本 .py 以 UTF-8 保存。字符串用普通引号，引擎单反斜杠写为 \\ 。
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUFF = os.path.join(ROOT, 'Mir200', 'Envir', 'QuestDiary', '系统功能', '军鼓BUFF.txt')
QF   = os.path.join(ROOT, 'Mir200', 'Envir', 'Market_def', 'QFunction-0.txt')
QM   = os.path.join(ROOT, 'Mir200', 'Envir', 'MapQuest_def', 'QManage.txt')


def _adapt_newlines(text, t):
    """把外部传入文本的换行适配成与目标文件 t 一致的行尾风格。"""
    # 判断目标文件主行尾
    crlf = t.count('\r\n') > t.count('\n') / 2  # 大多数行为 CRLF
    if crlf:
        # 外部文本以 \n 换行 -> 转 \r\n
        return text.replace('\r\n', '\n').replace('\n', '\r\n')
    return text.replace('\r\n', '\n')


def read_gbk(p):
    with io.open(p, 'rb') as f:
        return f.read().decode('gbk')


def write_gbk(p, text):
    with io.open(p, 'wb') as f:
        f.write(text.encode('gbk'))


def replace_once(p, old, new, tag):
    t = read_gbk(p)
    old_a = _adapt_newlines(old, t)
    new_a = _adapt_newlines(new, t)
    n = t.count(old_a)
    if n != 1:
        raise SystemExit('!! [%s] anchor count=%d in %s' % (tag, n, p))
    write_gbk(p, t.replace(old_a, new_a))
    print('ok replace [%s]' % tag)


def append(p, block, tag):
    t = read_gbk(p)
    block_a = _adapt_newlines(block, t)
    if not t.endswith('\r\n') and not t.endswith('\n'):
        t += '\r\n' if '\r\n' in t else '\n'
    write_gbk(p, t + block_a)
    print('ok append [%s]' % tag)


# ===========================================================================
# 1) 军鼓BUFF.txt —— 收敛英雄固定攻速3 为 统一汇总
# ===========================================================================
old_speed = """[@军鼓BUFF_刷新战士英雄攻速]
{
#IF
CheckHeroJob WARRIOR
#ACT
MOV N$战士英雄基础攻速 3
MOV N$战士英雄最终攻速 <$STR(N$战士英雄基础攻速)>
H.CHANGESPEED 2 <$STR(N$战士英雄最终攻速)> 3
BREAK
}"""

new_speed = """;====== 英雄军鼓：战士攻速 / 法师施法速度 统一汇总 ======
;战士英雄攻速 = 基础3(与玩家基础对齐) + 追风流(剁馅机)贡献；未穿剁馅机路线贡献为0。
[@英雄军鼓_刷新战士基础攻速]
{
#IF
NOT CheckHeroJob WARRIOR
#ACT
MOV N$战士英雄基础攻速 0
BREAK

#IF
#ACT
MOV N$战士英雄基础攻速 3
BREAK
}

[@英雄军鼓_刷新战士攻速]
{
#IF
NOT CheckHeroJob WARRIOR
#ACT
BREAK

#IF
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新战士基础攻速
MOV N$战士英雄路线攻速 0
MOV N$战士英雄最终攻速 0

#IF
EQUAL <$STR(S$英雄军鼓当前方向)> 剁馅机
#ACT
MOV N$战士英雄路线攻速 <$STR(N$英雄军鼓攻速)>

#IF
#ACT
FORMULATION <$STR(N$战士英雄基础攻速)>+<$STR(N$战士英雄路线攻速)> N$战士英雄最终攻速
H.CHANGESPEED 2 <$STR(N$战士英雄最终攻速)> 3
BREAK
}

;法师英雄施法速度：基础0，仅穿法师军鼓(wizard)时取军鼓施法速度贡献。
[@英雄军鼓_刷新法师基础施法速度]
{
#IF
NOT CheckHeroJob WIZARD
#ACT
MOV N$法师英雄基础施法速度 0
BREAK

#IF
#ACT
MOV N$法师英雄基础施法速度 0
BREAK
}

[@英雄军鼓_刷新法师施法速度]
{
#IF
NOT CheckHeroJob WIZARD
#ACT
BREAK

#IF
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新法师基础施法速度
MOV N$法师英雄路线施法速度 0
MOV N$法师英雄最终施法速度 0

#IF
EQUAL <$STR(S$英雄军鼓当前职业)> wizard
#ACT
MOV N$法师英雄路线施法速度 <$STR(N$英雄军鼓施法速度)>

#IF
#ACT
FORMULATION <$STR(N$法师英雄基础施法速度)>+<$STR(N$法师英雄路线施法速度)> N$法师英雄最终施法速度
H.CHANGESPEED 3 <$STR(N$法师英雄最终施法速度)> 3
BREAK
}

;兼容旧入口转发(@HeroLogin 历史调用)，统一走上方汇总。
[@军鼓BUFF_刷新战士英雄攻速]
{
#IF
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新战士攻速
BREAK
}"""
replace_once(BUFF, old_speed, new_speed, '军鼓BUFF收敛攻速')

# ===========================================================================
# 2) 军鼓BUFF.txt —— 末尾追加英雄军鼓主段
# ===========================================================================
hero_block = """

;============================================================================
; 英雄军鼓模块：英雄在14号位独立穿戴军鼓，获得与玩家同方向同品质一致的常驻流派。
; 主体命令加 H.(英雄)，目标(怪物)命令加 M.；英雄军鼓状态用"英雄军鼓"变量前缀与玩家隔离。
; 本阶段(阶段1)：穿戴/刷新/定时续期(复用玩家87定时器)/清理/登录/死亡 + 攻速施法速度收敛。
; 方向隐藏专精层(破防/减伤/暴抗/元素/吸血/准确等 H.AddHumNewValue)与战斗触发属阶段2，
; 需实机验证 H.AddHumNewValue/H.ChangeState/H.CHECKCURRTARGETRACE 等后补齐。
; 实机验证点：H.CHECKUSEITEM / H.GetItemFieldValue 英雄前缀；若不可用将走清理(安全降级)。
;============================================================================

;刷新统一入口：英雄穿军鼓(@HeroTakeOnEx) / 英雄登录(@HeroLogin)
[@英雄军鼓_刷新]
{
#IF
NOT CheckHeroOnline
#ACT
BREAK

#IF
#ACT
;关闭上一个英雄军鼓方向表现并清空旧状态
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_关闭当前表现
MOV N$英雄军鼓需要刷新 0
MOV N$英雄军鼓有效 0
MOV N$英雄军鼓品质 0
MOV N$英雄军鼓阶段 0
MOV N$英雄军鼓职业确认 0
MOV N$英雄军鼓在位 0
MOV N$英雄军鼓点 0
MOV N$英雄军鼓大点 0
MOV N$英雄军鼓血蓝 0
MOV N$英雄军鼓攻速 0
MOV N$英雄军鼓施法速度 0
MOV S$英雄军鼓当前名称
MOV S$英雄军鼓当前方向
MOV S$英雄军鼓当前职业
MOV S$英雄军鼓名称
MOV S$英雄军鼓方向
MOV S$英雄军鼓职业
MOV S$英雄军鼓校验职业

;检查英雄14号位是否佩戴军鼓
#IF
NOT H.CHECKUSEITEM 14
#ACT
MOV N$英雄军鼓有效 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_清理
BREAK

#IF
#ACT
;读取英雄军鼓当前改名后名称
H.GetItemFieldValue 14 name S$英雄军鼓名称

#IF
EQUAL <$STR(S$英雄军鼓名称)>
#ACT
MOV N$英雄军鼓有效 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_清理
BREAK

#IF
#ACT
;复用玩家配置表按名称匹配(先写玩家侧通用变量，读后转存英雄变量)
MOV S$军鼓名称 <$STR(S$英雄军鼓名称)>
#CALL [系统功能\\军鼓流派配置.txt] @军鼓配置_读取

#IF
NOT EQUAL N$军鼓有效 1
#ACT
MOV N$英雄军鼓有效 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_清理
BREAK

#IF
#ACT
;配置命中：转存到英雄军鼓变量
MOV S$英雄军鼓名称 <$STR(S$军鼓名称)>
MOV S$英雄军鼓职业 <$STR(S$军鼓职业)>
MOV S$英雄军鼓方向 <$STR(S$军鼓方向)>
MOV N$英雄军鼓品质 <$STR(N$军鼓品质)>
MOV N$英雄军鼓阶段 <$STR(N$军鼓阶段)>
MOV S$英雄军鼓校验职业 <$STR(S$军鼓职业)>
MOV N$英雄军鼓有效 1

;职业确认：英雄职业须与军鼓职业一致
MOV N$英雄军鼓职业确认 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_职业确认

#IF
NOT EQUAL N$英雄军鼓职业确认 1
#ACT
MOV N$英雄军鼓有效 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_清理
BREAK

#IF
#ACT
;读取英雄品质对应数值桶(与玩家同品质同值)
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_读取品质数值

;写入当前英雄军鼓快照
MOV S$英雄军鼓当前名称 <$STR(S$英雄军鼓名称)>
MOV S$英雄军鼓当前方向 <$STR(S$英雄军鼓方向)>
MOV S$英雄军鼓当前职业 <$STR(S$英雄军鼓职业)>

;应用英雄军鼓常驻(按职业底座)
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_应用常驻

;刷新英雄攻速/施法速度(统一汇总)
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新战士攻速
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新法师施法速度
BREAK
}

;英雄军鼓职业确认
[@英雄军鼓_职业确认]
{
#IF
EQUAL <$STR(S$英雄军鼓校验职业)> warrior
CheckHeroJob WARRIOR
#ACT
MOV N$英雄军鼓职业确认 1
BREAK

#IF
EQUAL <$STR(S$英雄军鼓校验职业)> wizard
CheckHeroJob WIZARD
#ACT
MOV N$英雄军鼓职业确认 1
BREAK

#IF
EQUAL <$STR(S$英雄军鼓校验职业)> taoist
CheckHeroJob TAOIST
#ACT
MOV N$英雄军鼓职业确认 1
BREAK

#IF
#ACT
MOV N$英雄军鼓职业确认 0
BREAK
}

;读取英雄军鼓品质数值桶(与玩家同品质同值，写英雄军鼓变量域)
[@英雄军鼓_读取品质数值]
{
#IF
#ACT
MOV N$英雄军鼓点 0
MOV N$英雄军鼓大点 0
MOV N$英雄军鼓血蓝 0
MOV N$英雄军鼓攻速 0
MOV N$英雄军鼓施法速度 0

#IF
EQUAL N$英雄军鼓品质 1
#ACT
MOV N$英雄军鼓点 3
MOV N$英雄军鼓大点 6
MOV N$英雄军鼓血蓝 120
MOV N$英雄军鼓攻速 1
MOV N$英雄军鼓施法速度 1
BREAK

#IF
EQUAL N$英雄军鼓品质 2
#ACT
MOV N$英雄军鼓点 4
MOV N$英雄军鼓大点 8
MOV N$英雄军鼓血蓝 200
MOV N$英雄军鼓攻速 2
MOV N$英雄军鼓施法速度 1
BREAK

#IF
EQUAL N$英雄军鼓品质 3
#ACT
MOV N$英雄军鼓点 5
MOV N$英雄军鼓大点 10
MOV N$英雄军鼓血蓝 320
MOV N$英雄军鼓攻速 3
MOV N$英雄军鼓施法速度 1
BREAK

#IF
EQUAL N$英雄军鼓品质 4
#ACT
MOV N$英雄军鼓点 6
MOV N$英雄军鼓大点 12
MOV N$英雄军鼓血蓝 460
MOV N$英雄军鼓攻速 4
MOV N$英雄军鼓施法速度 2
BREAK

#IF
EQUAL N$英雄军鼓品质 5
#ACT
MOV N$英雄军鼓点 8
MOV N$英雄军鼓大点 15
MOV N$英雄军鼓血蓝 620
MOV N$英雄军鼓攻速 5
MOV N$英雄军鼓施法速度 2
BREAK

#IF
EQUAL N$英雄军鼓品质 6
#ACT
MOV N$英雄军鼓点 10
MOV N$英雄军鼓大点 18
MOV N$英雄军鼓血蓝 850
MOV N$英雄军鼓攻速 6
MOV N$英雄军鼓施法速度 3
BREAK
}

;应用英雄军鼓常驻：按英雄职业下发职业核心属性(3秒短窗口，由玩家87定时器续期)
[@英雄军鼓_应用常驻]
{
#IF
NOT CheckHeroOnline
#ACT
BREAK

#IF
EQUAL <$STR(S$英雄军鼓当前职业)> warrior
#ACT
H.LockUpdateAbil
H.ChangeHumAbility 1 = <$STR(N$英雄军鼓点)> 3
H.ChangeHumAbility 2 = <$STR(N$英雄军鼓大点)> 3
H.ChangeHumAbility 11 = <$STR(N$英雄军鼓血蓝)> 3
H.UpdateAbil
BREAK

#IF
EQUAL <$STR(S$英雄军鼓当前职业)> wizard
#ACT
H.LockUpdateAbil
H.ChangeHumAbility 7 = <$STR(N$英雄军鼓点)> 3
H.ChangeHumAbility 8 = <$STR(N$英雄军鼓大点)> 3
H.ChangeHumAbility 12 = <$STR(N$英雄军鼓血蓝)> 3
H.UpdateAbil
BREAK

#IF
EQUAL <$STR(S$英雄军鼓当前职业)> taoist
#ACT
H.LockUpdateAbil
H.ChangeHumAbility 9 = <$STR(N$英雄军鼓点)> 3
H.ChangeHumAbility 10 = <$STR(N$英雄军鼓大点)> 3
H.ChangeHumAbility 11 = <$STR(N$英雄军鼓血蓝)> 3
H.ChangeHumAbility 12 = <$STR(N$英雄军鼓血蓝)> 3
H.UpdateAbil
BREAK
}

;关闭当前英雄军鼓常驻表现(属性清零)
[@英雄军鼓_关闭当前表现]
{
#IF
NOT CheckHeroOnline
#ACT
BREAK

#IF
EQUAL <$STR(S$英雄军鼓当前职业)> warrior
#ACT
H.LockUpdateAbil
H.ChangeHumAbility 1 = 0
H.ChangeHumAbility 2 = 0
H.ChangeHumAbility 11 = 0
H.UpdateAbil
BREAK

#IF
EQUAL <$STR(S$英雄军鼓当前职业)> wizard
#ACT
H.LockUpdateAbil
H.ChangeHumAbility 7 = 0
H.ChangeHumAbility 8 = 0
H.ChangeHumAbility 12 = 0
H.UpdateAbil
BREAK

#IF
EQUAL <$STR(S$英雄军鼓当前职业)> taoist
#ACT
H.LockUpdateAbil
H.ChangeHumAbility 9 = 0
H.ChangeHumAbility 10 = 0
H.ChangeHumAbility 11 = 0
H.ChangeHumAbility 12 = 0
H.UpdateAbil
BREAK
}

;英雄军鼓定时续期：玩家87定时器在英雄在线时调用，重发3秒窗口
[@英雄军鼓_定时检查]
{
#IF
NOT CheckHeroOnline
#ACT
BREAK

#IF
NOT H.CHECKUSEITEM 14
#ACT
MOV N$英雄军鼓有效 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_清理
BREAK

#IF
NOT EQUAL N$英雄军鼓有效 1
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新
BREAK

#IF
#ACT
H.GetItemFieldValue 14 name S$英雄军鼓确认名

#IF
NOT EQUAL <$STR(S$英雄军鼓确认名)> <$STR(S$英雄军鼓当前名称)>
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新
BREAK

#IF
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_应用常驻
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新战士攻速
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新法师施法速度
BREAK
}

;英雄军鼓清理：卸下/掉落/失效 统一入口
[@英雄军鼓_清理]
{
#IF
#ACT
MOV N$英雄军鼓需要刷新 0
MOV N$英雄军鼓有效 0
MOV N$英雄军鼓品质 0
MOV N$英雄军鼓阶段 0
MOV N$英雄军鼓职业确认 0
MOV N$英雄军鼓在位 0
MOV N$英雄军鼓点 0
MOV N$英雄军鼓大点 0
MOV N$英雄军鼓血蓝 0
MOV N$英雄军鼓攻速 0
MOV N$英雄军鼓施法速度 0
MOV S$英雄军鼓名称
MOV S$英雄军鼓方向
MOV S$英雄军鼓职业
MOV S$英雄军鼓校验职业
MOV S$英雄军鼓确认名
MOV S$英雄军鼓当前名称
MOV S$英雄军鼓当前方向
MOV S$英雄军鼓当前职业
;清英雄军鼓常驻表现(属性归零)并收敛攻速/施法速度(未穿追风流/法师军鼓时为0)
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_关闭当前表现
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新战士攻速
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新法师施法速度
BREAK
}

;英雄军鼓死亡检查(@HeroDie)：停战斗态与定时刷新标记
[@英雄军鼓_死亡检查]
{
#IF
#ACT
MOV N$英雄军鼓需要刷新 1
MOV N$英雄军鼓触发成功 0
BREAK
}
"""
append(BUFF, hero_block, '军鼓BUFF追加英雄主段')

print('STAGE1 军鼓BUFF 完成')
