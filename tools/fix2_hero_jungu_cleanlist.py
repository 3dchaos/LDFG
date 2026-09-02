# -*- coding: utf-8 -*-
"""fix2 补齐刷新清空列表变量（互斥组/模块/配置行/配置文本）。GBK安全。"""
import io, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUFF = os.path.join(ROOT, 'Mir200', 'Envir', 'QuestDiary', '系统功能', '军鼓BUFF.txt')
def read_gbk(p): return io.open(p,'rb').read().decode('gbk')
def write_gbk(p,t): io.open(p,'wb').write(t.encode('gbk'))
def adapt(s,t):
    crlf = t.count('\r\n') > t.count('\n')/2
    return s.replace('\r\n','\n').replace('\n','\r\n') if crlf else s.replace('\r\n','\n')

t = read_gbk(BUFF)
old = """MOV S$英雄军鼓名称
MOV S$英雄军鼓方向
MOV S$英雄军鼓职业
MOV S$英雄军鼓校验职业"""
new = """MOV S$英雄军鼓名称
MOV S$英雄军鼓方向
MOV S$英雄军鼓职业
MOV S$英雄军鼓校验职业
MOV S$英雄军鼓互斥组
MOV S$英雄军鼓模块
MOV N$英雄军鼓配置行 0
MOV S$英雄军鼓配置文本"""
oa, na = adapt(old,t), adapt(new,t)
n = t.count(oa)
if n != 1: raise SystemExit('!! anchor=%d' % n)
write_gbk(BUFF, t.replace(oa, na))
print('ok 补齐刷新清空变量')
