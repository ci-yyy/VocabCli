"""
初始化工具：选择 PDF → 提取词条 → 生成词库 JSON → 配置学习入口。
运行方式：python init.py
"""

import json
import os
import re
import sys
from pathlib import Path

import fitz

# ---------- 路径 ----------

PDF_DIR = Path("words_pdf")
OUT_DIR = Path("words_json")
CONFIG_FILE = Path("data/config.json")


# ---------- PDF 解析（源自 script.py）----------

HEADER_FOOTER_KEYWORDS = [
    "2027考研英语红宝书",
    "共 6550 词",
    "扫码听单词",
    "纸上默写",
    "耳边复习",
    "不背单词 App",
    "单词不用背，融入语境自然会",
]

WORD_LINE_RE = re.compile(r"^(\d+)\s+([A-Za-z][A-Za-z'’\- ]*)$")
PURE_NUM_RE = re.compile(r"^\d+$")
ENGLISH_WORD_RE = re.compile(r"^[A-Za-z][A-Za-z'’\- ]*$")
PAGE_FOOTER_RE = re.compile(r"\d+\s*/\s*\d+\s*页")


def clean_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    return [line for line in lines if line]


def is_header_footer(line: str) -> bool:
    if any(k in line for k in HEADER_FOOTER_KEYWORDS):
        return True
    if line.strip() in ("Word", "Meaning"):
        return True
    if PAGE_FOOTER_RE.search(line):
        return True
    return False


def preprocess_lines(text: str) -> list[str]:
    return [line for line in clean_lines(text) if not is_header_footer(line)]


def parse_page(text: str, page_num: int) -> list[dict]:
    lines = preprocess_lines(text)
    words: list[dict] = []
    meanings: list[dict] = []
    i = 0
    in_meaning_section = False

    while i < len(lines):
        line = lines[i]
        m = WORD_LINE_RE.match(line)
        if not in_meaning_section and m:
            words.append({"index": int(m.group(1)), "word": m.group(2).strip()})
            i += 1
            continue
        if not in_meaning_section and PURE_NUM_RE.match(line):
            if i + 1 < len(lines) and ENGLISH_WORD_RE.match(lines[i + 1]):
                words.append({"index": int(line), "word": lines[i + 1].strip()})
                i += 2
                continue
            else:
                in_meaning_section = True
        if in_meaning_section:
            break
        i += 1

    while i < len(lines):
        line = lines[i]
        if PURE_NUM_RE.match(line):
            idx = int(line)
            i += 1
            parts: list[str] = []
            while i < len(lines) and not PURE_NUM_RE.match(lines[i]):
                parts.append(lines[i])
                i += 1
            meaning = " ".join(parts).strip()
            if meaning:
                meanings.append({"index": idx, "meaning": meaning})
        else:
            i += 1

    meaning_map = {m["index"]: m["meaning"] for m in meanings}
    result = []
    for w in words:
        idx = w["index"]
        if idx in meaning_map:
            result.append({
                "page": page_num,
                "index": idx,
                "word": w["word"],
                "meaning": meaning_map[idx],
            })
    return result


def extract_pdf(pdf_path: str) -> list[dict]:
    """提取 PDF 中所有单词-释义对，带进度条。"""
    doc = fitz.open(pdf_path)
    total = len(doc)
    all_data: list[dict] = []
    for page_num in range(1, total + 1):
        text = doc[page_num - 1].get_text()
        page_data = parse_page(text, page_num)
        all_data.extend(page_data)
        print(f"\r  第 {page_num}/{total} 页，累计 {len(all_data)} 条", end="", flush=True)
    print()
    return all_data


# ---------- 交互 ----------

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def list_pdf_files() -> list[Path]:
    """返回 words_pdf/ 下所有 .pdf 文件，按名称排序。"""
    pdf_dir = Path(PDF_DIR)
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True)
    return sorted(pdf_dir.glob("*.pdf"))


def choose_pdf(files: list[Path]) -> Path:
    """显示文件列表，让用户选择一个，返回路径。"""
    clear()
    print("=" * 50)
    print("        📚 考研英语红宝词 · 初始化")
    print("=" * 50)
    print()
    print(f"在 {PDF_DIR}/ 中找到以下 PDF 文件：")
    print()
    for i, f in enumerate(files, 1):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {i}. {f.name}  ({size_mb:.1f} MB)")
    print()
    print("-" * 50)

    while True:
        choice = input("请选择要转换的文件 [1-{}]: ".format(len(files))).strip()
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(files):
                return files[n - 1]
        print(f"无效输入，请输入 1 ~ {len(files)} 之间的数字。")


def convert_pdf(pdf_path: Path) -> Path:
    """转换 PDF 为 JSON，返回输出路径。"""
    clear()
    print(f"正在转换: {pdf_path.name}")
    print()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{pdf_path.stem}.json"

    data = extract_pdf(str(pdf_path))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已保存到 {out_path}，共 {len(data)} 条")
    return out_path


def save_config(word_file: Path, pdf_name: str, total: int):
    """保存配置文件，供 word_cli.py 读取。"""
    config = {
        "word_file": str(word_file),
        "source_pdf": pdf_name,
        "total_words": total,
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ---------- 入口 ----------

def main():
    pdf_files = list_pdf_files()

    if not pdf_files:
        clear()
        print("=" * 50)
        print("        📚 考研英语红宝词 · 初始化")
        print("=" * 50)
        print()
        print(f"⚠️  未在 {PDF_DIR}/ 目录下找到 PDF 文件。")
        print()
        print("请按以下步骤操作：")
        print(f"  1. 将红宝书 PDF 文件放入项目根目录下的 {PDF_DIR}/ 文件夹")
        print("  2. 重新运行 python init.py")
        print()
        input("按回车退出...")
        return

    pdf_path = choose_pdf(pdf_files)
    out_path = convert_pdf(pdf_path)

    # 读取总词数
    with open(out_path, "r", encoding="utf-8") as f:
        total = len(json.load(f))

    save_config(out_path, pdf_path.name, total)

    clear()
    print("=" * 50)
    print("        ✅  初始化完成！")
    print("=" * 50)
    print()
    print(f"  词库: {out_path.name}")
    print(f"  词数: {total} 条")
    print(f"  来源: {pdf_path.name}")
    print()
    print("  接下来请运行：")
    print()
    print("      python word_cli.py")
    print()
    print("  开始背词！")
    print()
    input("按回车退出...")


if __name__ == "__main__":
    main()
