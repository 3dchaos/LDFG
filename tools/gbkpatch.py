# -*- coding: utf-8 -*-
"""gbkpatch.py - 按 GBK 编码对工程文本做精确替换/追加。

用途：Mir200/Envir 下大量 .txt 为 GBK(无BOM) 编码。用 Python 以 gbk
严格解码-替换-编码写回，可避免 PowerShell/通用文本工具破坏编码。

用法（CLI）:
  前置替换类：
    python gbkpatch.py <文件路径> <旧串文件|-> <新串>  -- 逐个精确替换
  为避免命令行中文转义问题，推荐用 Python 内直接 import 本模块调用
  patch_file / append_file。

约定：
  - 源 .py 以 UTF-8 书写中文，读入文件按 GBK 解码。
  - 保留原换行风格(LF/CRLF)、无 BOM。
"""
import io
import os
import sys


def read_gbk(path):
    with io.open(path, 'rb') as f:
        raw = f.read()
    # 原文件无 BOM；若带 BOM 也应能处理（只读内容）。
    text = raw.decode('gbk')
    return text, raw


def write_gbk(path, text):
    # 一律按无 BOM GBK 写回，行尾统一为 CRLF 或按原样？—— 保留原文件中换行，故不重排。
    raw = text.encode('gbk', errors='strict')
    with io.open(path, 'wb') as f:
        f.write(raw)


def patch_file(path, old, new, count=1):
    """将 path 中首次出现的 old 精确替换为 new。返回替换次数。"""
    text, _ = read_gbk(path)
    n = text.count(old)
    if n == 0:
        raise ValueError('NOT_FOUND in %s: %r' % (path, old[:60]))
    if count == 1:
        if n > 1:
            # 默认只替换第一次；如需全部请显式传 count=0
            text = text.replace(old, new, 1)
            replaced = 1
        else:
            text = text.replace(old, new)
            replaced = 1
    else:
        text = text.replace(old, new)
        replaced = n
    write_gbk(path, text)
    return replaced


def patch_all(path, old, new):
    text, _ = read_gbk(path)
    n = text.count(old)
    text = text.replace(old, new)
    write_gbk(path, text)
    return n


def append_file(path, block):
    """在文件末尾追加 block（block 自带结尾换行规范）。"""
    text, _ = read_gbk(path)
    if not text.endswith('\n'):
        text += '\n'
    text += block
    write_gbk(path, text)


def append_before_label(path, block, label):
    """在指定 [@label] 之前插入 block（保持段顺序）。"""
    text, _ = read_gbk(path)
    marker = '[@' + label + ']'
    idx = text.find(marker)
    if idx < 0:
        raise ValueError('LABEL_NOT_FOUND %s' % marker)
    text = text[:idx] + block + text[idx:]
    write_gbk(path, text)


def read_only(path):
    text, _ = read_gbk(path)
    return text


if __name__ == '__main__':
    # 命令行形式简单演示/基本替换：python gbkpatch.py file oldfile newfile
    # old 从临时文件读取以避免转义。
    path, oldf, newf = sys.argv[1], sys.argv[2], sys.argv[3]
    with io.open(oldf, encoding='utf-8') as f:
        old = f.read()
    with io.open(newf, encoding='utf-8') as f:
        new = f.read()
    print(patch_file(path, old, new))
