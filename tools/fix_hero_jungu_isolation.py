# -*- coding: utf-8 -*-
"""fix_hero_jungu_isolation.py
修正英雄军鼓刷新：不再复用玩家侧 @军鼓配置_读取（避免污染玩家 S$军鼓*/N$军鼓* 变量），
改为英雄独立解析配置(GetStringPosEX + ExtractStringEx，全落英雄变量)。GBK安全。
"""
import io, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUFF = os.path.join(ROOT, 'Mir200', 'Envir', 'QuestDiary', '系统功能', '军鼓BUFF.txt')

def read_gbk(p):
    return io.open(p,'rb').read().decode('gbk')
def write_gbk(p,t):
    io.open(p,'wb').write(t.encode('gbk'))
def adapt(s,t):
    crlf = t.count('\r\n') > t.count('\n')/2
    return s.replace('\r\n','\n').replace('\n','\r\n') if crlf else s.replace('\r\n','\n')

t = read_gbk(BUFF)

old = """;复用玩家配置表按名称匹配(先写玩家侧通用变量，读后转存英雄变量)
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
MOV N$英雄军鼓有效 1"""

new = """;英雄独立解析配置(不复用玩家侧读取，避免污染玩家 S$军鼓*/N$军鼓* 变量)
MOV N$英雄军鼓配置行 0
MOV S$英雄军鼓配置文本
MOV N$英雄军鼓有效 0
GetStringPosEX ..\\QuestDiary\\系统功能\\军鼓流派配置.txt <$STR(S$英雄军鼓名称)> N$英雄军鼓配置行 S$英雄军鼓配置文本 0

#IF
EQUAL N$英雄军鼓配置行 0
#ACT
MOV N$英雄军鼓有效 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_清理
BREAK

#IF
#ACT
ExtractStringEx | <$STR(S$英雄军鼓配置文本)> S$英雄军鼓配置字段
MOV S$英雄军鼓名称 <$STR(S$英雄军鼓配置字段1)>
MOV S$英雄军鼓职业 <$STR(S$英雄军鼓配置字段2)>
MOV S$英雄军鼓方向 <$STR(S$英雄军鼓配置字段3)>
MOV N$英雄军鼓品质 <$STR(S$英雄军鼓配置字段4)>
MOV N$英雄军鼓阶段 <$STR(S$英雄军鼓配置字段5)>
MOV S$英雄军鼓互斥组 <$STR(S$英雄军鼓配置字段6)>
MOV S$英雄军鼓模块 <$STR(S$英雄军鼓配置字段7)>
MOV S$英雄军鼓校验职业 <$STR(S$英雄军鼓配置字段2)>
MOV N$英雄军鼓有效 1"""

oa = adapt(old, t)
na = adapt(new, t)
n = t.count(oa)
if n != 1:
    raise SystemExit('!! isolation anchor count=%d' % n)
write_gbk(BUFF, t.replace(oa, na))
print('ok 英雄军鼓刷新改为独立解析配置')
