import json
import os
import sys
from pathlib import Path

# ---------- 文件路径 ----------

CONFIG_FILE = Path("data/config.json")
HARD_WORDS_FILE = "data/hard_words.json"


# ---------- 配置与加载 ----------

def load_config() -> dict:
    """读取初始化时生成的配置文件，返回 {word_file, source_pdf, total_words}。"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  尚未初始化词库。")
        print()
        print("请先运行以下命令选择并转换词库：")
        print()
        print("    python init.py")
        print()
        sys.exit(1)
    except Exception as e:
        print(f"读取配置失败: {e}")
        sys.exit(1)


def load_word_file(path: str) -> list[dict]:
    """加载词库文件——必须存在，否则报错退出。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"词库文件不存在: {path}")
        print("请重新运行 python init.py 初始化。")
        sys.exit(1)
    except Exception as e:
        print(f"读取 {path} 失败: {e}")
        sys.exit(1)


def load_hard_words() -> list[dict]:
    """加载生词本——不存在时返回空列表。"""
    try:
        with open(HARD_WORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"读取生词本失败: {e}")
        sys.exit(1)


def save_json(path: str, data: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clear():
    os.system("cls" if os.name == "nt" else "clear")


# ---------- 模式一：刷词 ----------

def run_review_mode(words: list[dict]):
    """刷词模式：浏览全部单词，按 s 将不会的词存入生词本。"""
    total = len(words)
    idx = 0
    show_mean = False
    hard_words = load_hard_words()
    hard_set = {w["index"] for w in hard_words}

    while True:
        clear()
        entry = words[idx]
        marked = " [已标记]" if entry["index"] in hard_set else ""
        print(f"📖 刷词模式  进度: {idx+1}/{total}  页码: {entry['page']}{marked}")
        print("-" * 50)
        print(f"单词: {entry['word']}")

        if show_mean:
            print(f"释义: {entry['meaning']}")

        print()
        print("[ 回车显示/下一个 | s 标记生词 | 数字跳转 | q 退出 ]")

        key = input().strip().lower()

        if key == "q":
            clear()
            return

        if key == "s":
            if entry["index"] not in hard_set:
                hard_words.append(entry)
                hard_set.add(entry["index"])
                save_json(HARD_WORDS_FILE, hard_words)
                print(f"\n✅ 已加入生词本！（当前共 {len(hard_words)} 个生词）")
            else:
                print(f"\n⏳ 该单词已在生词本中")
            if not show_mean:
                show_mean = True
            input("按回车继续...")
            continue

        if key.isdigit():
            target = int(key)
            if 1 <= target <= total:
                idx = target - 1
                show_mean = False
            else:
                print(f"请输入 1 ~ {total} 之间的数字！")
                input("按回车继续...")
            continue

        # 回车：先显示释义，再进下一个
        if not show_mean:
            show_mean = True
        else:
            idx = (idx + 1) % total
            show_mean = False


# ---------- 模式二：复习生词 ----------

def run_hard_mode():
    """生词模式：复习已标记的生词，按 d 移出（表示掌握了）。"""
    hard_words = load_hard_words()

    if not hard_words:
        clear()
        print("🎉 生词本为空！快去刷词模式下按 s 标记生词吧。")
        print()
        input("按回车返回主菜单...")
        return

    total = len(hard_words)
    idx = 0
    show_mean = False

    while True:
        clear()
        entry = hard_words[idx]
        print(f"🔁 生词复习  进度: {idx+1}/{total}  页码: {entry['page']}")
        print("-" * 50)
        print(f"单词: {entry['word']}")

        if show_mean:
            print(f"释义: {entry['meaning']}")

        print()
        print("[ 回车显示/下一个 | d 移出（掌握了）| 数字跳转 | q 退出 ]")

        key = input().strip().lower()

        if key == "q":
            clear()
            return

        if key == "d":
            removed = hard_words.pop(idx)
            save_json(HARD_WORDS_FILE, hard_words)
            total = len(hard_words)
            print(f"\n✅ 已将「{removed['word']}」移出生词本！（剩余 {total} 个）")
            if total == 0:
                print("\n🎉 所有生词已掌握！")
                input("按回车返回主菜单...")
                return
            if idx >= total:
                idx = total - 1
            show_mean = False
            input("按回车继续...")
            continue

        if key.isdigit():
            target = int(key)
            if 1 <= target <= total:
                idx = target - 1
                show_mean = False
            else:
                print(f"请输入 1 ~ {total} 之间的数字！")
                input("按回车继续...")
            continue

        # 回车逻辑
        if not show_mean:
            show_mean = True
        else:
            idx = (idx + 1) % total
            show_mean = False


# ---------- 主菜单 ----------

def main():
    config = load_config()
    word_file = config["word_file"]
    total_words = config.get("total_words", "?")
    source_pdf = config.get("source_pdf", "未知")

    words = load_word_file(word_file)

    while True:
        clear()
        hard_count = len(load_hard_words())

        print("=" * 50)
        print("        📚 考研英语红宝词 · 背词助手")
        print("=" * 50)
        print()
        print(f"  当前词库: {source_pdf}")
        print(f"  总词库: {len(words)} 词")
        print(f"  生词本: {hard_count} 词")
        print()
        print("  1. 刷词模式  — 浏览全部单词，按 s 标记生词")
        print("  2. 生词模式  — 复习已标记的生词，按 d 移出")
        print("  q. 退出")
        print()
        print("-" * 50)

        choice = input("请选择 [1/2/q]: ").strip().lower()

        if choice == "1":
            run_review_mode(words)
        elif choice == "2":
            run_hard_mode()
        elif choice == "q":
            clear()
            print("👋 再见！")
            break
        else:
            print("无效输入，请重新选择")
            input("按回车继续...")


if __name__ == "__main__":
    main()
