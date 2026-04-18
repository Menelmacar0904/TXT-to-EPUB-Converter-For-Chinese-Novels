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
root.title("请手动选择文件")
root.geometry("0x0")
root.attributes("-alpha", 0.0)      # 把主窗口变为透明，但仍能保持任务栏图标

# 打开目标txt文件
while True:
    filepath = filedialog.askopenfilename()
    if filepath == "":
        messagebox.showwarning(title="未选取文件", message="未选取文件！\n程序将自动退出。")
        sys.exit()
    elif not filepath.endswith(".txt"):
        messagebox.showwarning(title="格式错误", message="选中的不是.txt文件！\n请重新选取.txt格式文件。")
        continue
    else:
        try:
            with open(filepath, encoding="utf-8") as novel:
                lines = novel.readlines()
                break
        except UnicodeDecodeError:          # 如果 utf-8 报错，尝试用 gbk 读取
            with open(filepath, encoding="gbk", errors="ignore") as novel:
                lines = novel.readlines()
            break

title_layer = 1         # 标题层级记录
# 转化为.md文件
for i, line in enumerate(lines):
    clean_line = line.strip()           # 清理空格
    lines[i] = line.rstrip()+"\n\n"            # 添加两个换行，Markdown需要两个换行来进行段落区分，同时保留段前缩进
    if not clean_line: continue     # 跳过空行
    if (re.match("[【\\[]?第 *[零一二三四五六七八九十百千0123456789]+\\s*卷", clean_line)
            or re.match("[【\\[]?简介[]】]?[:：]?$", clean_line)):         # 给简介与整卷添加大标题
        lines[i] = "# "+lines[i]
        title_layer = 2
    elif (re.match("[【\\[]?第 *[零一二三四五六七八九十百千0123456789]+\\s*[章回节]", clean_line)
          or re.match("[\\[【]?彩蛋", clean_line) or re.match("[\\[【]?番外", clean_line)
          or re.match("[【\\[]? *[零一二三四五六七八九十百千0123456789]+\\s*$", clean_line)):           # 检测章节标题
        lines[i] = title_layer * "#" + " " + lines[i]

book_stem = Path(filepath).stem
book_author = ""

mdfile = Path(filepath).parent / f"{book_stem}.md"       # 输出的md文件与输入文件放入同一文件夹
# md文件写入
with open(mdfile, "w", encoding="utf-8-sig") as novel:
    # 删除章卷前冗余文字
    mark = 0
    for line in lines:
        if mark == 0:
            if re.match("\\s*作者", line):
                try:
                    book_author = re.findall("[^作者:：\\s].+", line.strip())[0]
                except IndexError:
                    pass
            if line.startswith("#"):
                mark = 1
                novel.write(line)
        else:
            novel.write(line)

ofile = Path(filepath).parent / f"{book_stem}.epub"         # 输出文件转换
# EPUB文件转换
pypandoc.convert_file(
    source_file = str(mdfile),
    to = "epub",
    format = "md",
    outputfile = str(ofile),
    extra_args = ["--metadata", f"title={book_stem}", "--metadata", f"author={book_author}",
                "--toc", "--toc-depth=2", "--split-level=2"]
)
mdfile.unlink()         # 移除中间步骤产生的.md文件
messagebox.showinfo(title="转换成功", message=f"恭喜！《{book_stem}》已成功转换为 EPUB 电子书！\n文件已保存为：\n{ofile}")
