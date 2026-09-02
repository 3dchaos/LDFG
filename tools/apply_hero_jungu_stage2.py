# -*- coding: utf-8 -*-
"""apply_hero_jungu_stage2.py
阶段2：为英雄军鼓落地"受击减伤"闭环。
1) 重建 @英雄军鼓_读取品质数值：按英雄军鼓职业(warrior/wizard/taoist)分发玩家同款品质数值，补全受击减伤所需字段。
2) 追加 @英雄军鼓_战斗确认 + @英雄军鼓_被打掉血前。
3) QFunction-0 末尾追加 @HeroStruckDamage 英雄回调。
命令确定依据：H.ChangeDamageValue(手册796英雄被攻击掉血前)、RANDOMEX/LARGE/EQUAL 条件命令放#IF、H.HumanHP 动作放#ACT。
"""
import io, re, sys, os

BUFF = 'Mir200/Envir/QuestDiary/系统功能/军鼓BUFF.txt'
QF = 'Mir200/Envir/Market_def/QFunction-0.txt'

def read(p): return io.open(p,'rb').read().decode('gbk')
def write(p,t): io.open(p,'wb').write(t.encode('gbk'))
def crlf(t): return t.count('\r\n') > t.count('\n')/2
def eol(t,s): return s.replace('\r\n','\n').replace('\n','\r\n') if crlf(t) else s.replace('\r\n','\n')

# ---------- 品质数值数据（与玩家各职业军鼓品质基础完全一致） ----------
# 字段顺序固定；每职业各6品质。变量名统一为 N$英雄军鼓<Field>。
WARRIOR = {
 1: dict(点=3,大点=6,血蓝=120,吸血=3,攻速=1,破防=2,准确=0,物伤减=2,魔伤减=1,暴抗=1,防冰=0,触发几率=12,切割=20,追风切割=10,铁头减伤=4,铁头回血=1),
 2: dict(点=4,大点=8,血蓝=200,吸血=4,攻速=2,破防=2,准确=1,物伤减=3,魔伤减=2,暴抗=2,防冰=1,触发几率=14,切割=30,追风切割=15,铁头减伤=5,铁头回血=1),
 3: dict(点=5,大点=10,血蓝=320,吸血=5,攻速=3,破防=3,准确=2,物伤减=5,魔伤减=3,暴抗=3,防冰=2,触发几率=16,切割=45,追风切割=20,铁头减伤=6,铁头回血=2),
 4: dict(点=6,大点=12,血蓝=460,吸血=6,攻速=4,破防=4,准确=3,物伤减=7,魔伤减=5,暴抗=4,防冰=3,触发几率=18,切割=60,追风切割=30,铁头减伤=8,铁头回血=2),
 5: dict(点=8,大点=15,血蓝=620,吸血=8,攻速=5,破防=5,准确=4,物伤减=9,魔伤减=7,暴抗=6,防冰=4,触发几率=21,切割=80,追风切割=40,铁头减伤=10,铁头回血=3),
 6: dict(点=10,大点=18,血蓝=850,吸血=10,攻速=6,破防=7,准确=5,物伤减=12,魔伤减=9,暴抗=8,防冰=5,触发几率=24,切割=100,追风切割=50,铁头减伤=12,铁头回血=4),
}
WIZARD = {
 1: dict(点=1,大点=2,血蓝=40,施法速度=1,元素=1,触发几率=8,吸蓝=1,范围=2,状态时间=2,爆伤=20,层数触发线=4),
 2: dict(点=1,大点=3,血蓝=60,施法速度=1,元素=1,触发几率=10,吸蓝=1,范围=2,状态时间=2,爆伤=30,层数触发线=4),
 3: dict(点=2,大点=4,血蓝=90,施法速度=1,元素=2,触发几率=12,吸蓝=2,范围=2,状态时间=2,爆伤=40,层数触发线=3),
 4: dict(点=2,大点=5,血蓝=120,施法速度=2,元素=2,触发几率=14,吸蓝=2,范围=3,状态时间=3,爆伤=50,层数触发线=3),
 5: dict(点=3,大点=6,血蓝=160,施法速度=2,元素=3,触发几率=16,吸蓝=3,范围=3,状态时间=3,爆伤=60,层数触发线=2),
 6: dict(点=3,大点=7,血蓝=220,施法速度=3,元素=3,触发几率=18,吸蓝=3,范围=3,状态时间=3,爆伤=80,层数触发线=2),
}
TAOIST = {
 1: dict(点=1,大点=2,血蓝=50,触发几率=8,元素=1,恢复=2,爆率=1,爆伤=10,状态时间=2),
 2: dict(点=1,大点=2,血蓝=70,触发几率=10,元素=1,恢复=3,爆率=1,爆伤=15,状态时间=2),
 3: dict(点=2,大点=3,血蓝=100,触发几率=12,元素=2,恢复=4,爆率=2,爆伤=20,状态时间=2),
 4: dict(点=2,大点=3,血蓝=130,触发几率=14,元素=2,恢复=5,爆率=2,爆伤=25,状态时间=3),
 5: dict(点=3,大点=4,血蓝=170,触发几率=16,元素=3,恢复=6,爆率=3,爆伤=30,状态时间=3),
 6: dict(点=3,大点=5,血蓝=220,触发几率=18,元素=3,恢复=8,爆率=3,爆伤=40,状态时间=3),
}

def gen_quality_block(prof, data):
    """生成 [@英雄军鼓_读取品质数值_<prof>] 块，data 为 {品质:{字段:值}}"""
    fields = list(sorted({k for q in data.values() for k in q}))
    # 注意保持施法速度/攻速区分，法师有施法速度，战士有攻速；点/大点/血蓝通用
    L = []
    L.append('[@英雄军鼓_读取品质数值_%s]' % prof)
    L.append('{')
    L.append('#IF')
    L.append('#ACT')
    L.append(';清空本职业品质数值桶')
    for f in fields:
        L.append('MOV N$英雄军鼓%s 0' % f)
    for q in range(1,7):
        L.append('')
        L.append('#IF')
        L.append('EQUAL N$英雄军鼓品质 %d' % q)
        L.append('CheckHeroJob %s' % {'warrior':'WARRIOR','wizard':'WIZARD','taoist':'TAOIST'}[prof])
        L.append('#ACT')
        for f in fields:
            L.append('MOV N$英雄军鼓%s %s' % (f, data[q][f]))
        L.append('BREAK')
    L.append('}')
    return '\n'.join(L)

# ---------- 1) 重建 @英雄军鼓_读取品质数值 ----------
def rebuild_quality():
    t = read(BUFF)
    # 找到 [@英雄军鼓_读取品质数值] 整段，替换为分发表
    start = t.find('[@英雄军鼓_读取品质数值]')
    if start < 0:
        sys.exit('!! 找不到 @英雄军鼓_读取品质数值')
    # 段结束：从 start 起找闭合 }（该标签用 { } 包裹，品质块内无嵌套花括号冲突——品质块每段没有额外 {）
    # 找段尾：定位到标签体的最后一个 '}' 之前的下一个 '[@'
    seg_end = t.find('[@', start+1)
    if seg_end < 0:
        sys.exit('!! 找不到段尾标签')
    # 回退到 seg_end 前的 '}'（标签体结束），即取 [start, seg_end) 替换
    old = t[start:seg_end]
    parts = []
    parts.append(';读取英雄军鼓品质数值：按英雄军鼓职业分发玩家同款品质(满足 复用玩家方向数值 取向，落 N$英雄军鼓* 变量域)')
    parts.append('[@英雄军鼓_读取品质数值]')
    parts.append('{')
    parts.append('#IF')
    parts.append('#ACT')
    parts.append(';按英雄军鼓职业分发对应职业品质基础')
    parts.append('')
    parts.append('#IF')
    parts.append('EQUAL <$STR(S$英雄军鼓职业)> warrior')
    parts.append('#ACT')
    parts.append('#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_读取品质数值_warrior')
    parts.append('BREAK')
    parts.append('')
    parts.append('#IF')
    parts.append('EQUAL <$STR(S$英雄军鼓职业)> wizard')
    parts.append('#ACT')
    parts.append('#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_读取品质数值_wizard')
    parts.append('BREAK')
    parts.append('')
    parts.append('#IF')
    parts.append('EQUAL <$STR(S$英雄军鼓职业)> taoist')
    parts.append('#ACT')
    parts.append('#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_读取品质数值_taoist')
    parts.append('BREAK')
    parts.append('}')
    new_qual = '\n'.join(parts)
    new_block = new_qual + '\n\n' + gen_quality_block('warrior', WARRIOR) + '\n\n' + gen_quality_block('wizard', WIZARD) + '\n\n' + gen_quality_block('taoist', TAOIST)
    new_block = eol(t, new_block)
    write(BUFF, t[:start] + new_block + t[seg_end:])
    print('重建 @英雄军鼓_读取品质数值 完成(含三职业分发表)')

# ---------- 2) 追加 战斗确认 + 被打掉血前 ----------
def append_to_eof(p, text):
    """把多行块 text 以文件实际行尾追加到文件末尾(带空行分隔)。"""
    t = read(p)
    newline = '\r\n' if crlf(t) else '\n'
    core = t.rstrip('\r\n')
    text = text.replace('\r\n', '\n').replace('\n', newline)
    out = core + newline + text
    if not out.endswith(newline):
        out += newline
    write(p, out)
    print('已追加到文件末尾: %s' % p)

def append_battle():
    block = '''

;============ 阶段2：英雄军鼓 受击减伤 战斗闭环 ============
;英雄军鼓战斗确认：英雄在线+在位+有效+名称一致。被 @HeroStruckDamage 调用。
[@英雄军鼓_战斗确认]
{
#IF
NOT CheckHeroOnline
#ACT
MOV N$英雄军鼓战斗确认 0
BREAK

#IF
NOT H.CHECKUSEITEM 14
#ACT
MOV N$英雄军鼓战斗确认 0
MOV N$英雄军鼓触发成功 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_清理
BREAK

#IF
NOT EQUAL N$英雄军鼓有效 1
#ACT
MOV N$英雄军鼓战斗确认 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新
BREAK

#IF
#ACT
H.GetItemFieldValue 14 name S$英雄军鼓确认名

#IF
NOT EQUAL <$STR(S$英雄军鼓确认名)> <$STR(S$英雄军鼓当前名称)>
#ACT
MOV N$英雄军鼓战斗确认 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新
BREAK

#IF
#ACT
MOV N$英雄军鼓战斗确认 1
BREAK
}

;英雄被攻击掉血前：按当前方向分发 受击减伤(H.ChangeDamageValue 1 - 值)。
;命令依据：@HeroStruckDamage + H.ChangeDamageValue 见手册796。
[@英雄军鼓_被打掉血前]
{
#IF
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_战斗确认
MOV N$英雄军鼓触发成功 0

#IF
NOT EQUAL N$英雄军鼓战斗确认 1
#ACT
BREAK

;---- 战士·铁头娃：被击按几率减伤，高品质追加回血 ----
#IF
EQUAL <$STR(S$英雄军鼓当前职业)> warrior
EQUAL <$STR(S$英雄军鼓当前方向)> 铁头娃
LARGE N$英雄军鼓品质 0
RANDOMEX <$STR(N$英雄军鼓触发几率)> 100
#ACT
H.ChangeDamageValue 1 - <$STR(N$英雄军鼓铁头减伤)>
MOV N$英雄军鼓触发成功 1

#IF
EQUAL <$STR(S$英雄军鼓当前职业)> warrior
EQUAL <$STR(S$英雄军鼓当前方向)> 铁头娃
EQUAL N$英雄军鼓触发成功 1
LARGE N$英雄军鼓品质 4
#ACT
H.HumanHP + <$STR(N$英雄军鼓铁头回血)> 0 1 0 0 1
BREAK

;---- 法师·小冰箱：被击按几率冰甲减伤(满层冰冻 RangeHarm 阶段3补) ----
#IF
EQUAL <$STR(S$英雄军鼓当前职业)> wizard
EQUAL <$STR(S$英雄军鼓当前方向)> 小冰箱
LARGE N$英雄军鼓品质 0
RANDOMEX <$STR(N$英雄军鼓触发几率)> 100
#ACT
H.ChangeDamageValue 1 - <$STR(N$英雄军鼓元素)>
MOV N$英雄军鼓触发成功 1
BREAK

;---- 道士·奶不死：被击按几率减伤，高品质追加救急回血 ----
#IF
EQUAL <$STR(S$英雄军鼓当前职业)> taoist
EQUAL <$STR(S$英雄军鼓当前方向)> 奶不死
LARGE N$英雄军鼓品质 0
RANDOMEX <$STR(N$英雄军鼓触发几率)> 100
#ACT
H.ChangeDamageValue 1 - <$STR(N$英雄军鼓元素)>
MOV N$英雄军鼓触发成功 1

#IF
EQUAL <$STR(S$英雄军鼓当前职业)> taoist
EQUAL <$STR(S$英雄军鼓当前方向)> 奶不死
EQUAL N$英雄军鼓触发成功 1
LARGE N$英雄军鼓品质 4
RANDOMEX <$STR(N$英雄军鼓触发几率)> 100
#ACT
H.HumanHP + <$STR(N$英雄军鼓恢复)> 100 1
MOV N$英雄军鼓触发成功 1
BREAK
}
'''
    append_to_eof(BUFF, block)

# ---------- 3) QF 新增 @HeroStruckDamage ----------
def append_qf():
    qf_block = '''

;========== 英雄军鼓 受击掉血前触发 ==========
[@HeroStruckDamage]
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_被打掉血前
'''
    append_to_eof(QF, qf_block)

if __name__ == '__main__':
    rebuild_quality()
    append_battle()
    append_qf()
    print('阶段2 受击减伤 落地脚本完成')
