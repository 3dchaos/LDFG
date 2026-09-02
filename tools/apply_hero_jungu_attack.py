# -*- coding: utf-8 -*-
# 阶段2攻击向：英雄军鼓 @HeroAttackDamage 镜像落地 (统一用列表状态, 防混合换行)
# 1) 英雄 wizard/taoist 品质数值桶补充攻击加伤 N$英雄军鼓百分(与玩家同品质同值)
# 2) 军鼓BUFF.txt 文末追加 @英雄军鼓_攻击掉血前
# 3) QFunction-0.txt 新增 @HeroAttackDamage
# GBK 无BOM + CRLF 二进制安全写回。
BUFF = r'Mir200/Envir/QuestDiary/系统功能/军鼓BUFF.txt'
QF   = r'Mir200/Envir/Market_def/QFunction-0.txt'

def read_lines(p):
    t = open(p, 'rb').read().decode('gbk')
    # split('\r\n'); 若末尾 CRLF 会多一个空串, 我们保留以便 join 还原
    return t.split('\r\n')

def write_lines(p, lines):
    # 原文件 CRLF 结尾 => split 后末元素为空串 => join 恰好还原末尾CRLF
    data = ('\r\n'.join(lines)).encode('gbk')
    open(p, 'wb').write(data)

def find_label(lines, label):
    for i, l in enumerate(lines):
        if l.strip() == label:
            return i
    return -1

# ---------- 军鼓BUFF ----------
blines = read_lines(BUFF)
assert find_label(blines, '[@英雄军鼓_读取品质数值_wizard]') >= 0
assert '英雄军鼓百分' not in open(BUFF,'rb').read().decode('gbk') or True
assert '[@英雄军鼓_攻击掉血前]' not in open(BUFF,'rb').read().decode('gbk')

wz_cfg = {1:2, 2:2, 3:3, 4:3, 5:4, 6:5}
ts_cfg = {1:1, 2:2, 3:2, 4:3, 5:3, 6:4}

def sect_bounds(lines, start_label, end_label):
    si = find_label(lines, start_label)
    assert si >= 0, start_label
    if end_label:
        ei = find_label(lines, end_label)
        assert ei >= 0, end_label
    else:
        ei = len(lines)
    return si, ei

def fill_pct(lines, si, ei, cfg):
    """在 [si,ei) 段内: 顶部清空区 'MOV N$英雄军鼓触发几率 0' 后插 'MOV N$英雄军鼓百分 0';
       各品质分支 'MOV N$英雄军鼓触发几率 <v>' 后插对应百分。行号从后往前插入防偏移。"""
    first_q = None
    for i in range(si, ei):
        if lines[i].strip().startswith('EQUAL N$英雄军鼓品质 '):
            first_q = i
            break
    assert first_q is not None, 'quality branch not found in section'
    ins = []
    for i in range(si, first_q):
        if lines[i].strip() == 'MOV N$英雄军鼓触发几率 0':
            ins.append((i + 1, 'MOV N$英雄军鼓百分 0'))
    q_no = None
    for i in range(first_q, ei):
        s = lines[i].strip()
        if s.startswith('EQUAL N$英雄军鼓品质 '):
            q_no = int(s.split()[-1])
        elif q_no in cfg and s.startswith('MOV N$英雄军鼓触发几率 '):
            ins.append((i + 1, 'MOV N$英雄军鼓百分 %d' % cfg[q_no]))
    for ln, nl in sorted(ins, key=lambda x: -x[0]):
        lines.insert(ln, nl)
    return len(ins)

# 注意: fill_pct 会插入行导致后续行号偏移, 因此每段在调用前实时重新定位范围
wsi, wei = sect_bounds(blines, '[@英雄军鼓_读取品质数值_wizard]', '[@英雄军鼓_读取品质数值_taoist]')
c1 = fill_pct(blines, wsi, wei, wz_cfg)
tsi, tei = sect_bounds(blines, '[@英雄军鼓_读取品质数值_taoist]', '[@英雄军鼓_应用常驻]')
c2 = fill_pct(blines, tsi, tei, ts_cfg)
print('pct inserted wizard', c1, 'taoist', c2)
assert c1 == 1 + 6, c1   # 1清空 + 6品质
assert c2 == 1 + 6, c2

# 追加攻击段 (行元素逐一 append, 元素内无换行)
attack = []
attack.append('')
attack.append(';============ 阶段2攻击向：英雄军鼓 攻击加伤/切割 战斗闭环 ============')
attack.append(';英雄攻击目标掉血前(@HeroAttackDamage)。命令依据：')
attack.append('; @HeroAttackDamage + H.ChangeDamageValue 见手册796;')
attack.append('; H.CHECKCURRTARGETRACE 见手册103; H.M.HumanHP(英雄操作当前目标)见手册164多级运用。')
attack.append('; 战士拆门板/剁馅机：对非玩家目标直扣最大生命比例(切割/追风切割)。')
attack.append('; 法师/道士各攻击方向：攻击按几率给英雄本次伤害加百分比(H.ChangeDamageValue 1 + 百分)。')
attack.append('; 注：法师/道士攻击向采用 技能名无关的通用触发(未细分英雄技能), 数值复用玩家同品质百分。')
attack.append('[@英雄军鼓_攻击掉血前]')
attack.append('{')
attack.append('#IF')
attack.append('#ACT')
attack.append('#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_战斗确认')
attack.append('MOV N$英雄军鼓触发成功 0')
attack.append('')
attack.append('#IF')
attack.append('NOT EQUAL N$英雄军鼓战斗确认 1')
attack.append('#ACT')
attack.append('BREAK')
attack.append('')
attack.append(';---- 战士·拆门板：攻击切割(对怪) ----')
attack.append('#IF')
attack.append('EQUAL <$STR(S$英雄军鼓当前职业)> warrior')
attack.append('EQUAL <$STR(S$英雄军鼓当前方向)> 拆门板')
attack.append('NOT H.CHECKCURRTARGETRACE = 0')
attack.append('LARGE N$英雄军鼓品质 0')
attack.append('RANDOMEX <$STR(N$英雄军鼓触发几率)> 100')
attack.append('#ACT')
attack.append('H.M.HumanHP - <$STR(N$英雄军鼓切割)> 0 1 0 0 3')
attack.append('MOV N$英雄军鼓触发成功 1')
attack.append('BREAK')
attack.append('')
attack.append(';---- 战士·剁馅机：攻击追风切割(对怪) ----')
attack.append('#IF')
attack.append('EQUAL <$STR(S$英雄军鼓当前职业)> warrior')
attack.append('EQUAL <$STR(S$英雄军鼓当前方向)> 剁馅机')
attack.append('NOT H.CHECKCURRTARGETRACE = 0')
attack.append('LARGE N$英雄军鼓品质 0')
attack.append('RANDOMEX <$STR(N$英雄军鼓触发几率)> 100')
attack.append('#ACT')
attack.append('H.M.HumanHP - <$STR(N$英雄军鼓追风切割)> 0 1 0 0 3')
attack.append('MOV N$英雄军鼓触发成功 1')
attack.append('BREAK')
attack.append('')
attack.append(';---- 法师·小冰箱：攻击加伤(通用触发) ----')
attack.append('#IF')
attack.append('EQUAL <$STR(S$英雄军鼓当前职业)> wizard')
attack.append('EQUAL <$STR(S$英雄军鼓当前方向)> 小冰箱')
attack.append('LARGE N$英雄军鼓品质 0')
attack.append('RANDOMEX <$STR(N$英雄军鼓触发几率)> 100')
attack.append('#ACT')
attack.append('H.ChangeDamageValue 1 + <$STR(N$英雄军鼓百分)>')
attack.append('MOV N$英雄军鼓触发成功 1')
attack.append('BREAK')
attack.append('')
attack.append(';---- 法师·电耗子：攻击加伤(通用触发) ----')
attack.append('#IF')
attack.append('EQUAL <$STR(S$英雄军鼓当前职业)> wizard')
attack.append('EQUAL <$STR(S$英雄军鼓当前方向)> 电耗子')
attack.append('LARGE N$英雄军鼓品质 0')
attack.append('RANDOMEX <$STR(N$英雄军鼓触发几率)> 100')
attack.append('#ACT')
attack.append('H.ChangeDamageValue 1 + <$STR(N$英雄军鼓百分)>')
attack.append('MOV N$英雄军鼓触发成功 1')
attack.append('BREAK')
attack.append('')
attack.append(';---- 法师·火葫芦：攻击加伤(通用触发) ----')
attack.append('#IF')
attack.append('EQUAL <$STR(S$英雄军鼓当前职业)> wizard')
attack.append('EQUAL <$STR(S$英雄军鼓当前方向)> 火葫芦')
attack.append('LARGE N$英雄军鼓品质 0')
attack.append('RANDOMEX <$STR(N$英雄军鼓触发几率)> 100')
attack.append('#ACT')
attack.append('H.ChangeDamageValue 1 + <$STR(N$英雄军鼓百分)>')
attack.append('MOV N$英雄军鼓触发成功 1')
attack.append('BREAK')
attack.append('')
attack.append(';---- 道士·毒嘴子：攻击加伤(通用触发) ----')
attack.append('#IF')
attack.append('EQUAL <$STR(S$英雄军鼓当前职业)> taoist')
attack.append('EQUAL <$STR(S$英雄军鼓当前方向)> 毒嘴子')
attack.append('LARGE N$英雄军鼓品质 0')
attack.append('RANDOMEX <$STR(N$英雄军鼓触发几率)> 100')
attack.append('#ACT')
attack.append('H.ChangeDamageValue 1 + <$STR(N$英雄军鼓百分)>')
attack.append('MOV N$英雄军鼓触发成功 1')
attack.append('BREAK')
attack.append('')
attack.append(';---- 道士·养娃人：攻击加伤(通用触发) ----')
attack.append('#IF')
attack.append('EQUAL <$STR(S$英雄军鼓当前职业)> taoist')
attack.append('EQUAL <$STR(S$英雄军鼓当前方向)> 养娃人')
attack.append('LARGE N$英雄军鼓品质 0')
attack.append('RANDOMEX <$STR(N$英雄军鼓触发几率)> 100')
attack.append('#ACT')
attack.append('H.ChangeDamageValue 1 + <$STR(N$英雄军鼓百分)>')
attack.append('MOV N$英雄军鼓触发成功 1')
attack.append('BREAK')
attack.append('}')

# 移除末尾已有的空串占位(若末元素为空说明原以CRLF结尾), 追加 attack 元素
if blines and blines[-1] == '':
    blines.pop()  # 去掉结尾空串
blines.extend(attack)
write_lines(BUFF, blines)
print('BUFF lines now', len(blines))

# ---------- QFunction-0 ----------
qlines = read_lines(QF)
assert '[@HeroAttackDamage]' not in open(QF,'rb').read().decode('gbk')
if qlines and qlines[-1] == '':
    qlines.pop()
qadd = [
    '',
    ';========== 英雄军鼓 攻击掉血前触发 ==========',
    ';英雄攻击目标掉血前 -> 战士切割 / 法师道士攻击加伤',
    '[@HeroAttackDamage]',
    '#ACT',
    '#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_攻击掉血前',
]
qlines.extend(qadd)
write_lines(QF, qlines)
print('QF lines now', len(qlines))

# ---------- 校验 ----------
def verify():
    t = open(BUFF,'rb').read().decode('gbk')
    crlf = t.count('\r\n'); lf = t.count('\n')
    assert crlf == lf, ('BUFF mixed newline', crlf, lf)
    for need in ['MOV N$英雄军鼓百分 0',
                 'MOV N$英雄军鼓百分 2','MOV N$英雄军鼓百分 3',
                 'MOV N$英雄军鼓百分 4','MOV N$英雄军鼓百分 5',
                 '[@英雄军鼓_攻击掉血前]',
                 'H.M.HumanHP - <$STR(N$英雄军鼓切割)> 0 1 0 0 3',
                 'H.M.HumanHP - <$STR(N$英雄军鼓追风切割)> 0 1 0 0 3',
                 'H.ChangeDamageValue 1 + <$STR(N$英雄军鼓百分)>']:
        assert need in t, 'BUFF missing: ' + need
    # 百分行计数: 2清空 + 6(wz) + 6(ts) = 14 处 MOV N$英雄军鼓百分 (不含引用)
    mvcount = sum(1 for l in t.split('\r\n') if l.strip().startswith('MOV N$英雄军鼓百分 '))
    assert mvcount == 14, mvcount
    q = open(QF,'rb').read().decode('gbk')
    qcrlf = q.count('\r\n'); qlf = q.count('\n')
    assert qcrlf == qlf, ('QF mixed newline', qcrlf, qlf)
    assert '[@HeroAttackDamage]' in q
    assert '#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_攻击掉血前' in q
    print('VERIFY OK  mv_count=', mvcount)

verify()
