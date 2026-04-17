import re
import pypandoc
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox

while True:
    root = tk.Tk()
    root.title("请手动选择文件")
    root.withdraw()
    filepath = filedialog.askopenfilename()
    if not filepath.endswith(".txt"):
        if filepath == '':
            messagebox.showwarning(title="未选取文件", message="未选取文件！\n程序将自动退出。")
            sys.exit()
        messagebox.showwarning(title="格式错误", message="选中的不是.txt文件！\n请重新选取.txt格式文件。")
        continue
    with open(filepath,  encoding="utf-8") as novel:
        lines = novel.readlines()
        break

book_stem = Path(filepath).stem
while lines:
    first_line = lines[0].strip()
    # 如果第一行是空行，或者第一行就是书名本身，就把它从列表中删掉
    if not first_line or first_line == book_stem or first_line in book_stem:
        lines.pop(0)
    else:
        break # 直到遇到真正的内容（比如简介或第一卷），停止清理

title_layer = 1
for i, line in enumerate(lines):
    clean_line = line.strip()
    lines[i] = line.rstrip()+'\n\n'            #添加两个换行，Markdown需要两个换行来进行段落区分
    if not clean_line: continue
    if (re.match("[【\\[]?第[零一二三四五六七八九十百千0123456789]+卷", clean_line)
            or re.match("[【\\[]?简介[]】]?[:：]", clean_line) or clean_line == "简介"):         #给作品相关与整卷添加标题
        lines[i] = '# '+lines[i]
        title_layer = 2
    elif (re.match("[【\\[]?第[零一二三四五六七八九十百千0123456789]+[章回节]", clean_line)
          or re.match("[\\[【]?彩蛋", clean_line) or re.match("[\\[【]?番外", clean_line)
          or re.match("[【\\[]?[零一二三四五六七八九十百千0123456789]+$", clean_line)):           #检测章节标题
        lines[i] = title_layer * '#' + ' ' + lines[i]

book_author = simpledialog.askstring(title="输入信息", prompt="请输入作者名称（可选），不填请直接点确定：", parent=root)
if not book_author: book_author = ''

mdfile = Path(filepath).parent / f"{book_stem}.md"       #输出的md文件与输入文件放入同一文件夹
with open(mdfile, 'w', encoding="utf-8") as novel:    #md文件写入
    mark = 0        #删除章卷前冗余文字
    for i, line in enumerate(lines):
        if mark == 0 and '#' not in line : continue
        elif '#' in line :
            mark = 1
            novel.writelines(line)
        elif mark == 1: novel.writelines(line)

ofile = Path(filepath).parent / f"{book_stem}.epub"
pypandoc.convert_file(
    source_file = str(mdfile),
    to = 'epub',
    format = 'md',
    outputfile = str(ofile),
    extra_args = ['--metadata', f'title={book_stem}', '--metadata', f'author={book_author}',
                '--toc', '--toc-depth=2', '--split-level=2']
)

messagebox.showinfo(title="转换成功", message=f"恭喜！《{book_stem}》已成功转换为 EPUB 电子书！\n文件已保存为：\n{ofile}")
