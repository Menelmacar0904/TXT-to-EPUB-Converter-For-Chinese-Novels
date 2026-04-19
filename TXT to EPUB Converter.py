import re
import pypandoc
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import ctypes

# 高DPI适配
try:
    # 针对 Windows 8.1 及以上版本
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        # 针对 Windows Vista/7
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# 创建弹窗
root = tk.Tk()
root.title('TXT转EPUB工具')
root.geometry('0x0')
root.attributes('-alpha', 0)  # 把主窗口变为透明，但仍能保持任务栏图标

# 打开目标txt文件
while True:
    txt_file = filedialog.askopenfilename(title='请选择要转换的txt文本文件', filetypes=[('文本文件', '*.txt')])
    if txt_file == '':
        messagebox.showwarning(title='未选取文件', message='未选取文件！\n程序将自动退出。')
        sys.exit()
    else:
        break

# 检测目标文件编码
target_encoding = 'utf-8'
target_errors = 'strict'
try:
    with open(txt_file, encoding=target_encoding) as test:
        test.read(8192)
except UnicodeDecodeError:  # 如果 utf-8 报错，尝试用 gbk 读取
    target_encoding = 'gbk'
    target_errors = 'ignore'

# 正则表达式预编译
p_h1 = re.compile('[【\\[]?第\\s*[零一二两三四五六七八九十百千\\d]+\\s*卷(\\s|$)')
p_intro = re.compile('[【\\[]?简介[]】]?[:：\\s]')
p_h2 = re.compile('[【\\[]?第\\s*[零一二两三四五六七八九十百千\\d]+\\s*[章回节集](\\s|$)|'
                  '[\\[【]?彩蛋[：\\s]|'
                  '[\\[【]?番外[：\\s]|'
                  '[【\\[]?[零一二两三四五六七八九十百千\\d]+(.|，|、|\\s|$)')
p_author_extract = re.compile('作者[:：\\s]*(.*)')

title_chars = set('第简彩番''0123456789''零一二两三四五六七八九十')  # 标题开头元组，不匹配则直接跳过
book_stem = Path(txt_file).stem
book_author = ''
markdown_lines = []
mark = 0  # 正文标记
intro = 0  # 简介标记
title_layer = 1  # 标题层级记录

with open(txt_file, 'r', encoding=target_encoding, errors=target_errors) as f_in:
    for line in f_in:
        clean_line = line.strip()
        if not clean_line: continue
        # 寻找作者
        if mark == 0:
            match = p_author_extract.search(line)
            if match: book_author = match.group(1).strip()
        # 添加标题
        if clean_line[0] not in title_chars or len(clean_line) > 40:
            pass
        elif intro == 0 and p_intro.match(clean_line):  # 为简介添加大标题
            clean_line = '# ' + clean_line
            mark = 1
            intro = 1
        elif p_h1.match(clean_line):  # 给整卷添加大标题
            clean_line = '# ' + clean_line
            title_layer = 2
            mark = 1
        elif p_h2.match(clean_line):  # 检测章节标题
            clean_line = title_layer * '#' + ' ' + clean_line
            mark = 1
        if mark:
            markdown_lines.append(f"{clean_line}\n\n")

markdown_text = ''.join(markdown_lines)

epub_file = Path(txt_file).parent / f'{book_stem}.epub'  # 输出文件转换

css_file = Path(txt_file).parent / "style.css"
with open(css_file, "w", encoding="utf-8") as css:
    # 通用书名与正文样式
    base_css = """
        p {
            text-indent: 2em !important;
            margin-top: 0.5em !important;
            margin-bottom: 0.5em !important;
            line-height: 1.6 !important;
            text-align: justify !important;
        }
        p.noindent {
            text-indent: 2em !important;
        }
        h1.title {
            text-indent: 0 !important;
            text-align: center !important;
            padding-top: 35vh !important;
            font-size: 2.8em !important;
            border-bottom: none !important; 
        }
        """

    # 标题样式
    if title_layer == 2:
        heading_css = """
            h1 {
                text-indent: 0; text-align: center;
                padding-top: 35vh; margin-bottom: 2em; font-size: 2.2em;
            }
            h2 {
                text-indent: 0; text-align: center;
                padding-top: 5vh; margin-bottom: 1em; font-size: 1.6em;
            }
            """
    else:
        heading_css = """
            h1 {
                text-indent: 0; text-align: center;
                padding-top: 5vh; margin-bottom: 1em; font-size: 1.6em;
            }
            """
    css.write(base_css + heading_css)

# EPUB文件转换
pypandoc.convert_text(
    source=markdown_text,
    to='epub',
    format='commonmark',
    outputfile=str(epub_file),
    extra_args=['--metadata', f'title={book_stem}',
                '--metadata', f'author={book_author}',
                '--toc', '--toc-depth=2', '--split-level=2',
                '--metadata', 'toc-title=目录',
                f'--css={css_file}']
)

css_file.unlink()
messagebox.showinfo(title='转换成功', message=f'恭喜！《{book_stem}》已成功转换为 EPUB 电子书！\n文件已保存为：\n{epub_file}')
