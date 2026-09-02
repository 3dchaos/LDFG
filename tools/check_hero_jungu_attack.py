# -*- coding: utf-8 -*-
# 静态回归：阶段2攻击向 英雄军鼓 @HeroAttackDamage 闭环
BUFF=r'Mir200/Envir/QuestDiary/系统功能/军鼓BUFF.txt'
QF=r'Mir200/Envir/Market_def/QFunction-0.txt'
def L(p): return open(p,'rb').read().decode('gbk').split('\r\n')
fail=[]
def ok(cond,msg):
    print(('OK   ' if cond else 'FAIL ')+msg)
    if not cond: fail.append(msg)
blines=L(BUFF); qlines=L(QF)
def find(lab,ls):
    for i,l in enumerate(ls):
        if l.strip()==lab: return i
    return -1

# 1. 攻击段存在且为文件最后一段(其后无其它 [@ 标签)
asi=find('[@英雄军鼓_攻击掉血前]',blines)
ok(asi>=0,'BUFF 有 @英雄军鼓_攻击掉血前')
if asi>=0:
    after=[l for l in blines[asi+1:] if l.strip().startswith('[@')]
    ok(not after,'@英雄军鼓_攻击掉血前 是文件最后一段(其后无其它[@标签), 实际:%s'%after)
    # 段闭合
    ok(blines[-1].strip()=='}' and blines[-2].strip()=='BREAK' and blines[-3].strip().startswith('MOV N$英雄军鼓触发成功 1'),
       '攻击段以 BREAK+} 正确收尾')

# 2. 段内命令落区: 在 @英雄军鼓_攻击掉血前 段内扫描
if asi>=0:
    # 截到段结束 '}' (最后一行)
    seg=blines[asi+1:len(blines)]  # 从 { 到 } (段在文件末尾)
    # 简化: 从 { 后 到 段尾 }
    body=seg
    zone=None
    cond_ok=act_ok=True
    for l in body:
        s=l.strip()
        if s=='#IF': zone='IF'; continue
        if s=='#ACT': zone='ACT'; continue
        if s.startswith('#ELSE'): zone='IF'; continue
        if s=='{': continue
        if s=='}': break
        if not s or s.startswith(';'): continue
        if s=='BREAK': continue
        if s.startswith('#CALL'): 
            if zone!='ACT': act_ok=False; print('  [落区错]#CALL在',zone,':',s)
            continue
        # 条件命令
        if s.startswith(('EQUAL','NOT EQUAL','LARGE','NOT LARGE','RANDOMEX','NOT RANDOMEX','H.CHECKCURRTARGETRACE','NOT H.CHECKCURRTARGETRACE','CHECK')):
            if zone!='IF': cond_ok=False; print('  [落区错]条件命令在',zone,':',s)
        elif s.startswith(('MOV','H.M.HumanHP','H.ChangeDamageValue','SetOnTimer','SetOffTimer','INC')):
            if zone!='ACT': act_ok=False; print('  [落区错]动作命令在',zone,':',s)
    ok(cond_ok,'攻击段条件命令均落 #IF 区')
    ok(act_ok,'攻击段动作命令均落 #ACT 区')

# 3. 攻击段用到的方向数值桶字段存在(MOV定义)与引用一致
used={'N$英雄军鼓切割','N$英雄军鼓追风切割','N$英雄军鼓百分','N$英雄军鼓触发几率','N$英雄军鼓品质',
      'S$英雄军鼓当前职业','S$英雄军鼓当前方向'}
for u in used:
    ok(u.replace('$','\$') in '\n'.join(blines) or u in '\n'.join(blines), '字段存在: '+u)

# 4. 战斗确认标签存在(攻击段依赖)
ok(find('[@英雄军鼓_战斗确认]',blines)>=0,'BUFF 有 @英雄军鼓_战斗确认')

# 5. QF @HeroAttackDamage
hadi=find('[@HeroAttackDamage]',qlines)
ok(hadi>=0,'QF 有 @HeroAttackDamage')
uniq=sum(1 for l in qlines if l.strip()=='[@HeroAttackDamage]')
ok(uniq==1,'QF @HeroAttackDamage 唯一')
if hadi>=0:
    ok(any('#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_攻击掉血前'==l.strip() for l in qlines[hadi:hadi+3]),
       'QF @HeroAttackDamage -> #CALL @英雄军鼓_攻击掉血前')

# 6. 百分完整: 2清空+6wizard+6taoist=14 MOV
mv=sum(1 for l in blines if l.strip().startswith('MOV N$英雄军鼓百分 '))
ok(mv==14,'MOV N$英雄军鼓百分 共14处(实际%d)'%mv)

# 7. 无混合换行 / 编码仍GBK
for p in (BUFF,QF):
    raw=open(p,'rb').read()
    try: raw.decode('gbk')
    except: ok(False,'仍GBK可解码: '+p); continue
    t=raw.decode('gbk')
    ok(t.count('\r\n')==t.count('\n'),'纯CRLF: '+p)

print('==== 结论: %d 项失败 ===='%len(fail))
