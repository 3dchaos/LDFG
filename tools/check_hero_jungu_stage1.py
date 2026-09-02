# -*- coding: utf-8 -*-
"""check_hero_jungu_stage1.py 阶段1静态回归校验。"""
import io, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUFF = os.path.join(ROOT, 'Mir200', 'Envir', 'QuestDiary', '系统功能', '军鼓BUFF.txt')
CONF = os.path.join(ROOT, 'Mir200', 'Envir', 'QuestDiary', '系统功能', '军鼓流派配置.txt')
QF   = os.path.join(ROOT, 'Mir200', 'Envir', 'Market_def', 'QFunction-0.txt')
QM   = os.path.join(ROOT, 'Mir200', 'Envir', 'MapQuest_def', 'QManage.txt')

def read(p):
    with io.open(p, 'rb') as f:
        raw = f.read()
    try:
        return raw.decode('gbk')
    except UnicodeDecodeError:
        sys.exit('!! GBK解码失败: ' + p)

errs = []

def check(cond, msg):
    print(('OK  ' if cond else 'FAIL') + '  ' + msg)
    if not cond:
        errs.append(msg)

# ---- 编码与行尾 ----
for p in (BUFF, CONF, QF, QM):
    raw = io.open(p, 'rb').read()
    t = raw.decode('gbk', errors='replace')
    check('�' not in t, '%s 无乱码' % os.path.basename(p))
    crlf = raw.count(b'\r\n'); lf = raw.count(b'\n')
    check(crlf == lf, '%s 纯CRLF(crlf=%d lf=%d)' % (os.path.basename(p), crlf, lf))

# ---- 标签唯一性 ----
def labelset(p):
    return set(re.findall(r'\[@([^\]]+)\]', read(p)))

def label_count(p, lab):
    return read(p).count('[@' + lab + ']')

lb = labelset(BUFF)
hero_labs = ['英雄军鼓_刷新','英雄军鼓_职业确认','英雄军鼓_读取品质数值','英雄军鼓_应用常驻',
             '英雄军鼓_定时检查','英雄军鼓_清理','英雄军鼓_死亡检查','英雄军鼓_关闭当前表现',
             '英雄军鼓_刷新战士基础攻速','英雄军鼓_刷新战士攻速',
             '英雄军鼓_刷新法师基础施法速度','英雄军鼓_刷新法师施法速度']
for l in hero_labs:
    check(l in lb and label_count(BUFF, l) == 1, '军鼓BUFF 标签 @%s 唯一存在' % l)

# 玩家侧攻速标签应保留唯一(兼容转发)
for l in ['军鼓BUFF_刷新战士英雄攻速']:
    check(label_count(BUFF, l) == 1, '军鼓BUFF 兼容标签 @%s 保留' % l)

# ---- 花括号配对(整文件) ----
for p in (BUFF,):
    t = read(p)
    check(t.count('{') == t.count('}'), '%s 花括号配对' % os.path.basename(p))

# ---- #CALL 目标存在性：军鼓BUFF 内部引用 ----
t = read(BUFF)
for m in re.finditer(r'#CALL\s+\[([^\]]+)\]\s+@([^\s]+)', t):
    f, lab = m.group(1), m.group(2)
    if f == '系统功能\\军鼓BUFF.txt':
        check(lab in lb, '本文件#CALL @%s 存在' % lab)
    elif f == '系统功能\\军鼓流派配置.txt':
        cl = labelset(CONF)
        check(lab in cl, '跨文件#CALL 配置@%s 存在' % lab)
    elif f.startswith('系统功能\\军鼓流派\\'):
        # 军鼓流派子目录方向脚本
        fn = os.path.join(ROOT, 'Mir200', 'Envir', 'QuestDiary', os.path.normpath(f))
        if os.path.exists(fn):
            dl = labelset(fn)
            check(lab in dl, '跨文件#CALL [%s]@%s 存在' % (os.path.basename(fn), lab))
        else:
            errs.append('跨文件路径不存在 %s' % fn)
    else:
        errs.append('未知#CALL路径 %s @%s' % (f, lab))

# ---- QF 引用军鼓BUFF ----
tqf = read(QF)
for m in re.finditer(r'#CALL\s+\[([^\]]+)\]\s+@([^\s]+)', tqf):
    f, lab = m.group(1), m.group(2)
    if '军鼓BUFF' in f:
        check(lab in lb, 'QF#CALL 军鼓BUFF@%s 存在' % lab)
for l in ['HeroTakeOnEx','HeroTakeOffEx','HeroDie']:
    check(label_count(QF, l) == 1, 'QF 标签 @%s 唯一' % l)
# 玩家侧军鼓原标签不被破坏
for l in ['TakeOnEx','TakeOffEx','HumDropItem','AttackDamage','StruckDamage','SlaveAttackDamage','PlayDie']:
    check(label_count(QF, l) == 1, 'QF 玩家回调 @%s 保留' % l)

# ---- QM 引用军鼓BUFF ----
tqm = read(QM)
for m in re.finditer(r'#CALL\s+\[([^\]]+)\]\s+@([^\s]+)', tqm):
    f, lab = m.group(1), m.group(2)
    if '军鼓BUFF' in f:
        check(lab in lb, 'QM#CALL 军鼓BUFF@%s 存在' % lab)

# ---- 关键锚点落盘确认 ----
check('CheckHeroOnline' in t, '军鼓BUFF 含 CheckHeroOnline 守卫')
check('H.CHECKUSEITEM 14' in t, '军鼓BUFF 含 H.CHECKUSEITEM 14')
check('H.GetItemFieldValue 14 name S$英雄军鼓名称' in t, '军鼓BUFF 含 H.GetItemFieldValue')
check('CheckHeroJob WARRIOR\n#ACT\n#CALL [系统功能\\军鼓BUFF.txt] @军鼓BUFF_刷新战士英雄攻速' not in read(QM),
      'QM 已移除旧固定攻速调用')

print('\n==== 结论：%d 项失败 ====' % len(errs))
for e in errs:
    print('  - ' + e)
sys.exit(1 if errs else 0)
