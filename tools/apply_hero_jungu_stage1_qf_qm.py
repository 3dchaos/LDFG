# -*- coding: utf-8 -*-
"""apply_hero_jungu_stage1_qf_qm.py
阶段1 QF/QM 接入：英雄军鼓回调 + 登录/定时续期。GBK安全。
"""
import io, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QF = os.path.join(ROOT, 'Mir200', 'Envir', 'Market_def', 'QFunction-0.txt')
QM = os.path.join(ROOT, 'Mir200', 'Envir', 'MapQuest_def', 'QManage.txt')

def read_gbk(p): return io.open(p,'rb').read().decode('gbk')
def write_gbk(p,t): io.open(p,'wb').write(t.encode('gbk'))
def adapt(s,t):
    crlf = t.count('\r\n') > t.count('\n')/2
    return s.replace('\r\n','\n').replace('\n','\r\n') if crlf else s.replace('\r\n','\n')

def replace_once(p, old, new, tag):
    t = read_gbk(p); oa,na = adapt(old,t),adapt(new,t)
    n = t.count(oa)
    if n != 1: raise SystemExit('!! [%s] anchor=%d in %s' % (tag,n,p))
    write_gbk(p, t.replace(oa,na)); print('ok replace [%s]' % tag)

def append(p, block, tag):
    t = read_gbk(p); ba = adapt(block,t)
    if not (t.endswith('\r\n') or t.endswith('\n')):
        t += '\r\n' if '\r\n' in t else '\n'
    write_gbk(p, t+ba); print('ok append [%s]' % tag)

# ---------------------------------------------------------------
# 1) QFunction-0.txt 末尾追加英雄军鼓回调
# ---------------------------------------------------------------
qf_block = """
;========== 英雄军鼓位触发（14号位） ==========
;英雄穿装备 -> 刷新英雄军鼓
[@HeroTakeOnEx]
#IF
EQUAL <$H.CurItemPos> 14
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新
BREAK

;英雄卸装备 -> 清理英雄军鼓
[@HeroTakeOffEx]
#IF
EQUAL <$H.CurItemPos> 14
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_清理
BREAK

;英雄死亡 -> 英雄军鼓死亡检查(复位战斗态/标记刷新)
[@HeroDie]
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_死亡检查
"""
append(QF, qf_block, 'QF追加英雄军鼓回调')

# ---------------------------------------------------------------
# 2) QManage.txt @HeroLogin：战士固定攻速补偿 -> 英雄军鼓统一刷新
# ---------------------------------------------------------------
old_login = """#IF
CheckHeroJob WARRIOR
#ACT
#CALL [系统功能\\军鼓BUFF.txt] @军鼓BUFF_刷新战士英雄攻速
SENDMSG 6 战士英雄攻速，准确补偿开启
"""
new_login = """#IF
#ACT
;英雄登录：按英雄当前14号位军鼓结算常驻(含攻速/施法速度统一收敛到新链路)
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_刷新
"""
replace_once(QM, old_login, new_login, 'QM HeroLogin收敛为英雄军鼓刷新')

# ---------------------------------------------------------------
# 3) QManage.txt @OnTimer87：追加英雄军鼓在线续期
# ---------------------------------------------------------------
old_timer = """[@OnTimer87]
#ACT
MOV N$军鼓定时刷新中 1
#CALL [系统功能\\军鼓BUFF.txt] @军鼓BUFF_定时检查
MOV N$军鼓定时刷新中 0"""
new_timer = """[@OnTimer87]
#ACT
MOV N$军鼓定时刷新中 1
#CALL [系统功能\\军鼓BUFF.txt] @军鼓BUFF_定时检查
MOV N$军鼓定时刷新中 0
;英雄军鼓在线续期(英雄不在场时由 @英雄军鼓_定时检查 内部 CheckHeroOnline 守卫跳过)
#CALL [系统功能\\军鼓BUFF.txt] @英雄军鼓_定时检查"""
replace_once(QM, old_timer, new_timer, 'QM OnTimer87追加英雄续期')

print('QF/QM 完成')
