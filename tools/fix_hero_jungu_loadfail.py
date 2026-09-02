# -*- coding: utf-8 -*-
"""fix_hero_jungu_loadfail.py - 修复 @英雄军鼓_应用常驻 load fail。

根因：
  1. H.LockUpdateAbil / H.UpdateAbil 为非法命令（引擎/知识库均无 H. 前缀版本），
     正确命令是无前缀 LockUpdateAbil / UpdateAbil（同玩家侧先例）。
  2. }[@英雄军鼓_应用常驻] 合并段边界写法异常，改为标准 } 换行 [@...]。

保留 GBK(无BOM)+CRLF，仅做字节级精确替换。
"""
import io
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r'Mir200/Envir/QuestDiary/系统功能/军鼓BUFF.txt'
BAK = r'.workbuddy/backup-英雄军鼓-20260902/军鼓BUFF.txt.pre-loadfail.bak'

# 1) 备份
import os
os.makedirs(os.path.dirname(BAK), exist_ok=True)
shutil.copyfile(P, BAK)
print('backup ->', BAK)

raw = open(P, 'rb').read()

def do_replace(raw, old_bytes, new_bytes, label, expect_any=True):
    n = raw.count(old_bytes)
    if n == 0 and expect_any:
        print('[WARN] NOT_FOUND', label)
        return raw
    if n == 0 and not expect_any:
        print('[SKIP] already replaced', label)
        return raw
    raw = raw.replace(old_bytes, new_bytes)
    print('replaced', label, 'x', n)
    return raw

# 2) H.LockUpdateAbil -> LockUpdateAbil  (行内独立命令，整词，前后为空白/换行)
for pre in (b'\r\n', b'\n'):
    pass
# 更稳妥：仅当该串作为整命令令牌出现（前一个字节是换行），我们的段内它都在行首（缩进可能无）
# 直接做全替换 H.LockUpdateAbil -> LockUpdateAbil
raw = do_replace(raw, b'H.LockUpdateAbil', b'LockUpdateAbil', 'H.LockUpdateAbil->LockUpdateAbil')
raw = do_replace(raw, b'H.UpdateAbil', b'UpdateAbil', 'H.UpdateAbil->UpdateAbil')

# 3) }[@英雄军鼓_应用常驻] -> }\r\n[@英雄军鼓_应用常驻]  (合并段边界拆成标准两行)
# 实际合并文本为 '}[@英雄军鼓_应用常驻]'
old3 = ('}[@英雄军鼓_应用常驻]').encode('gbk')
new3 = ('}\r\n[@英雄军鼓_应用常驻]').encode('gbk')
n3 = raw.count(old3)
if n3:
    raw = raw.replace(old3, new3)
    print('split }@ label x', n3)
else:
    print('[INFO] merged }@ not found (may already be standard)')

open(P, 'wb').write(raw)
print('written OK. bytes', len(raw))
