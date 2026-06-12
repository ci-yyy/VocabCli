"""
从考研英语红宝书 PDF 中提取单词-释义对，保存为 JSON。
"""

import json
import re
from pathlib import Path

import fitz

# ---------- 常量 ----------

# 页眉/页脚关键词（子串匹配，排除误杀）
HEADER_FOOTER_KEYWORDS = [
    "2027考研英语红宝书",
    "共 6550 词",
    "扫码听单词",
    "纸上默写",
    "耳边复习",
    "不背单词 App",
    "单词不用背，融入语境自然会",
]

# 正则（模块级，避免每页重复编译）
WORD_LINE_RE = re.compile(r"^(\d+)\s+([A-Za-z][A-Za-z'’\- ]*)$")
PURE_NUM_RE = re.compile(r"^\d+$")
ENGLISH_WORD_RE = re.compile(r"^[A-Za-z][A-Za-z'’\- ]*$")
PAGE_FOOTER_RE = re.compile(r"\d+\s*/\s*\d+\s*页")


# ---------- 文本预处理 ----------

def clean_lines(text: str) -> list[str]:
    """拆分并去除空行。"""
    lines = [line.strip() for line in text.splitlines()]
    return [line for line in lines if line]


def is_header_footer(line: str) -> bool:
    """判断是否为页眉/页脚噪音行。"""
    if any(k in line for k in HEADER_FOOTER_KEYWORDS):
        return True
    # "Word" / "Meaning" 只匹配单独成行的列标题，避免误杀单词本身
    if line.strip() in ("Word", "Meaning"):
        return True
    if PAGE_FOOTER_RE.search(line):
        return True
    return False


def preprocess_lines(text: str) -> list[str]:
    return [line for line in clean_lines(text) if not is_header_footer(line)]


# ---------- 单页解析 ----------

def parse_page(text: str, page_num: int, debug: bool = False) -> list[dict]:
    """
    解析一页 PDF 文本。

    返回:
        [{page, index, word, meaning}, ...]
    """
    lines = preprocess_lines(text)

    words: list[dict] = []
    meanings: list[dict] = []

    i = 0
    in_meaning_section = False

    # ---- 阶段一：单词区 ----
    while i < len(lines):
        line = lines[i]

        # 一行模式: "1001 sensitive"
        m = WORD_LINE_RE.match(line)
        if not in_meaning_section and m:
            words.append({"index": int(m.group(1)), "word": m.group(2).strip()})
            i += 1
            continue

        # 两行模式: "999" + "sensation"
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

    # ---- 阶段二：释义区 ----
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

    # 调试输出（统一放到 debug/ 目录）
    if debug and (not words or not result):
        debug_dir = Path("debug")
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_path = debug_dir / f"page_{page_num:04d}.txt"
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write("===== lines =====\n")
            f.write("\n".join(lines))
            f.write("\n\n===== parsed_words =====\n")
            f.write(json.dumps(words, ensure_ascii=False, indent=2))
            f.write("\n\n===== parsed_meanings =====\n")
            f.write(json.dumps(meanings, ensure_ascii=False, indent=2))
            f.write("\n\n===== parsed_result =====\n")
            f.write(json.dumps(result, ensure_ascii=False, indent=2))

    return result


# ---------- 整个 PDF ----------

def extract_pdf(pdf_path: str, debug: bool = False) -> list[dict]:
    """提取 PDF 中所有单词-释义对。"""
    doc = fitz.open(pdf_path)
    total = len(doc)
    all_data: list[dict] = []

    for page_num in range(1, total + 1):
        text = doc[page_num - 1].get_text()
        page_data = parse_page(text, page_num, debug=debug)
        all_data.extend(page_data)
        # 行内更新进度，不刷屏
        print(f"\r  第 {page_num}/{total} 页，累计 {len(all_data)} 条", end="", flush=True)

    print()
    return all_data


# ---------- 入口 ----------

if __name__ == "__main__":
    pdf_dir = Path("words_pdf")
    out_dir = Path("words_json")
    out_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        print(f"\n处理: {pdf_path.name}")
        data = extract_pdf(str(pdf_path))
        out_path = out_dir / f"{pdf_path.stem}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存到 {out_path}，共 {len(data)} 条")

