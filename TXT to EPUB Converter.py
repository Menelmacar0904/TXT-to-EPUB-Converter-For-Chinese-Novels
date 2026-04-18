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
root.attributes('-alpha', 0)      # 把主窗口变为透明，但仍能保持任务栏图标

title_layer = 1         # 标题层级记录

# 打开目标txt文件
while True:
    txt_file = filedialog.askopenfilename(title='请选择要转换的txt文本文件', filetypes=[('文本文件', '*.txt')])
    if txt_file == '':
        messagebox.showwarning(title='未选取文件', message='未选取文件！\n程序将自动退出。')
        sys.exit()
    else: break

# 检测目标文件编码
target_encoding = 'utf-8'
target_errors = 'strict'
try:
    with open(txt_file, encoding=target_encoding) as test:
        for i in test: pass
except UnicodeDecodeError:          # 如果 utf-8 报错，尝试用 gbk 读取
    target_encoding = 'gbk'
    target_errors = 'ignore'
    

# 正则表达式预编译
p_section = re.compile('[【\\[]?第 *[零一二三四五六七八九十百千\\d]+\\s*卷[\\s$]')
p_intro = re.compile('[【\\[]?简介[]】]?[:：]?$')
p_chapter = re.compile('[【\\[]?第 *[零一二三四五六七八九十百千\\d]+\\s*[章回节集][\\s$]')
p_easter =  re.compile('[\\[【]?彩蛋')
p_spinoff = re.compile('[\\[【]?番外')
p_brief_chap = re.compile('[【\\[]? *[零一二三四五六七八九十百千\\d]+\\s*$')
p_author = re.compile('\\s*作者')
p_get_author = re.compile('[^作者:：\\s].+')

book_stem = Path(txt_file).stem
book_author = ''
md_file = Path(txt_file).parent / f'{book_stem}.md'

with (open(txt_file, 'r', encoding=target_encoding, errors=target_errors) as f_in,
      open(md_file, 'w', encoding='utf-8-sig') as f_out):
    mark = 0            # 正文标记
    for line in f_in:
        if not line.strip(): continue
        line = line.rstrip() + '\n\n'       # 添加两个换行，在Markdown中分段
        # 寻找作者
        if mark == 0:
            if re.match(p_author, line):
                try:
                    book_author = re.findall(p_get_author, line.strip())[0]
                except IndexError:
                    pass
        # 添加标题
        if re.match(p_section, line) or re.match(p_intro, line):  # 给简介与整卷添加大标题
            line = '# ' + line
            title_layer = 2
            mark = 1
        elif (re.search(p_chapter, line) or re.match(p_easter, line) or re.match(p_spinoff, line)
              or re.match(p_brief_chap, line)):  # 检测章节标题
            line = title_layer * '#' + ' ' + line
            mark = 1
        if mark: f_out.write(line)

epub_file = Path(txt_file).parent / f'{book_stem}.epub'         # 输出文件转换
# EPUB文件转换
pypandoc.convert_file(
    source_file = str(md_file),
    to = 'epub',
    format = 'md',
    outputfile = str(epub_file),
    extra_args = ['--metadata', f'title={book_stem}',
                  '--metadata', f'author={book_author}',
                  '--toc', '--toc-depth=2', '--split-level=2',
                  '--metadata', 'toc-title=目录']
)

md_file.unlink()         # 移除中间步骤产生的.md文件
messagebox.showinfo(title='转换成功', message=f'恭喜！《{book_stem}》已成功转换为 EPUB 电子书！\n文件已保存为：\n{epub_file}')
