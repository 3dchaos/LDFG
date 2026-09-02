# -*- coding: utf-8 -*-
"""fix_hero_jungu_renew2.py — 按行号区间精确修改，避免多段三连文本歧义。

目标文件：军鼓BUFF.txt、QManage.txt (GBK 无BOM + CRLF)

改动：
 [军鼓BUFF.txt]
  A) @英雄军鼓_刷新 应用成功末尾(刷新法师施法速度 #CALL 之后)插入 SetOnTimer 89 2
  B) @英雄军鼓_定时检查 整段(1676-1712 原状)替换为纯续期版(去掉 H.CHECKUSEITEM/
     H.GetItemFieldValue 玩家作用域探测)
  C) @英雄军鼓_清理 段内 刷新法师施法速度 #CALL 之后插入 SetOffTimer 89
 [QManage.txt]
  D) 在 [@OnTimer88] 前新增 [@OnTimer89] -> #CALL @英雄军鼓_定时检查

按行索引修改 + \r\n 重建写回，保证 GBK/CRLF 不变。
"""
import io
import sys

BUFF = r'Mir200/Envir/QuestDiary/系统功能/军鼓BUFF.txt'
QMANAGE = r'Mir200/Envir/MapQuest_def/QManage.txt'
NL = '\r\n'


def read_lines(path):
    raw = open(path, 'rb').read()
    t = raw.decode('gbk', errors='strict')
    return t.split('\r\n')  # CRLF -> 行数组(每行不含行尾)


def write_lines(path, lines):
    t = NL.join(lines)
    # 原文件以 \r\n 结尾；join 后末尾无多余行尾,补一个以保持结构
    open(path, 'wb').write(t.encode('gbk', errors='strict'))


def find_label(lines, label):
    """返回以 [@label] 开头的行索引,且该行无其它前缀。"""
    for i, l in enumerate(lines):
        if l.strip() == '[@%s]' % label:
            return i
    raise SystemExit('LABEL NOT FOUND: [@%s]' % label)


# ========== 军鼓BUFF.txt ==========
L = read_lines(BUFF)

# --- A) _刷新 末尾插 SetOnTimer 89 2 ---
si = find_label(L, '英雄军鼓_刷新')
# 该段内最后一个以 #CALL 刷新法师施法速度 的行
last_magic = None
j = si + 1
while j < len(L) and not L[j].strip().startswith('[@') :
    if L[j].strip().startswith('#CALL') and '刷新法师施法速度' in L[j]:
        last_magic = j
    j += 1
assert last_magic is not None, 'A: no magic CALL in _刷新'
L.insert(last_magic + 1,
    ';英雄军鼓专属续期定时器：独立于玩家军鼓/87(玩家可不带军鼓)。ChangeHumAbility 3秒限时,需周期重施。')
L.insert(last_magic + 2, 'SetOnTimer 89 2')
print('[OK] A  _刷新 SetOnTimer 89 2 @line', last_magic + 2)

# --- B) 重构 _定时检查 整段 ---
ti = find_label(L, '英雄军鼓_定时检查')
# 段范围: ti .. 该段闭合 '}' 行
end = ti
while end < len(L) and L[end].strip() != '}':
    end += 1
assert L[end].strip() == '}', 'B: 定时检查段未找到闭合 }'
# 重建段
new_seg = [
    '[@英雄军鼓_定时检查]',
    '{',
    ';英雄军鼓专属续期(QManage @OnTimer89)与玩家87共同入口。装备在位由穿戴/卸下事件维护,',
    ';这里不用 H.CHECKUSEITEM/H.GetItemFieldValue 在玩家作用域探测英雄装备(引擎无H.版,不可靠)。',
    '#IF',
    'NOT CheckHeroOnline',
    '#ACT',
    'BREAK',
    '',
    '#IF',
    'NOT EQUAL N$英雄军鼓有效 1',
    '#ACT',
    ';有效状态丢失：停止续期定时器,等待穿戴/登录事件重开',
    'SetOffTimer 89',
    'BREAK',
    '',
    '#IF',
    '#ACT',
    ';有效=1：周期重施3秒限时常驻,顶住引擎英雄属性重算',
    '#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_应用常驻',
    '#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新战士攻速',
    '#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新法师施法速度',
    'BREAK',
    '}',
]
L[ti:end + 1] = new_seg
print('[OK] B  重构 _定时检查 段(行', ti + 1, '起', len(new_seg), '行)')

# --- C) _清理 段内 刷新法师施法速度 CALL 后插 SetOffTimer 89 ---
ci = find_label(L, '英雄军鼓_清理')
last_magic_c = None
j = ci + 1
while j < len(L) and not L[j].strip().startswith('[@'):
    if L[j].strip().startswith('#CALL') and '刷新法师施法速度' in L[j]:
        last_magic_c = j
    j += 1
assert last_magic_c is not None, 'C: no magic CALL in _清理'
L.insert(last_magic_c + 1, ';停掉英雄军鼓专属续期定时器')
L.insert(last_magic_c + 2, 'SetOffTimer 89')
print('[OK] C  _清理 SetOffTimer 89 @line', last_magic_c + 2)

write_lines(BUFF, L)
print('[OK] 军鼓BUFF.txt written')

# ========== QManage.txt ==========
Q = read_lines(QMANAGE)
o88 = find_label(Q, 'OnTimer88')
on89 = [
    ';英雄军鼓专属续期定时器(89)：玩家无需带军鼓也可为英雄军鼓持续重施3秒限时属性。',
    '[@OnTimer89]',
    '#ACT',
    '#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_定时检查',
    '',
]
Q[o88:o88] = on89
print('[OK] D  QManage 新增 [@OnTimer89] @line', o88)
write_lines(QMANAGE, Q)
print('[OK] QManage.txt written')
print('DONE')
