# -*- coding: utf-8 -*-
"""fix_hero_jungu_getstringpos.py
修复英雄军鼓刷新中 GetStringPosEX 被错误放在 #ACT 区导致的脚本错误。
参照玩家侧 @军鼓配置_读取 结构：GetStringPosEX 是条件命令，须放 #IF 区。
"""
import io, re, sys

P = 'Mir200/Envir/QuestDiary/系统功能/军鼓BUFF.txt'

def read(p):
    return io.open(p, 'rb').read().decode('gbk')

def write(p, text):
    io.open(p, 'wb').write(text.encode('gbk'))

def crlf_style(t):
    return t.count('\r\n') > t.count('\n') / 2

def to_eol(t, s):
    # 将多行字符串 s 的行尾适配为文件实际行尾
    return s.replace('\r\n', '\n').replace('\n', '\r\n') if crlf_style(t) else s.replace('\r\n', '\n')

t = read(P)

OLD = '''#IF
#ACT
;英雄独立解析配置(不复用玩家侧读取，避免污染玩家 S$军鼓*/N$军鼓* 变量)
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
ExtractStringEx | <$STR(S$英雄军鼓配置文本)> S$英雄军鼓配置字段'''

NEW = '''#IF
#ACT
;英雄独立解析配置(不复用玩家侧读取，避免污染玩家 S$军鼓*/N$军鼓* 变量)
MOV N$英雄军鼓有效 0
MOV N$英雄军鼓配置行 0
MOV S$英雄军鼓配置文本

;GetStringPosEX 是条件命令，须放在 #IF 区(与玩家侧 @军鼓配置_读取 同构)
#IF
GetStringPosEX ..\\QuestDiary\\系统功能\\军鼓流派配置.txt <$STR(S$英雄军鼓名称)> N$英雄军鼓配置行 S$英雄军鼓配置文本 0
#ACT

#IF
EQUAL N$英雄军鼓配置行 0
#ACT
MOV N$英雄军鼓有效 0
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_清理
BREAK

#IF
#ACT
ExtractStringEx | <$STR(S$英雄军鼓配置文本)> S$英雄军鼓配置字段'''

oa, na = to_eol(t, OLD), to_eol(t, NEW)
n = t.count(oa)
print('anchor count:', n)
if n != 1:
    sys.exit('anchor not unique / missing')
write(P, t.replace(oa, na))
print('fixed OK')
