import json
import os
import sys

# 你的单词文件路径
WORD_FILE = "words_json/2027考研英语红宝书-不背单词乱序版.json"

def load_words():
    try:
        with open(WORD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        sys.exit()

def clear():
    os.system("cls")

def main():
    words = load_words()
    total = len(words)
    idx = 0
    show_mean = False

    while True:
        clear()
        print(f"进度: {idx+1}/{total}  页码: {words[idx]['page']}")
        print("-" * 40)
        print(f"单词: {words[idx]['word']}")

        if show_mean:
            print(f"释义: {words[idx]['meaning']}")

        print("\n[ 回车下一个 | 输入数字跳转 | q 退出 ]")
        key = input().strip().lower()

        if key == "q":
            clear()
            return

        # 新增：判断是否输入数字，跳转指定位置
        if key.isdigit():
            target = int(key)
            if 1 <= target <= total:
                idx = target - 1
                show_mean = False
            else:
                print(f"请输入 1 ~ {total} 之间的数字！")
                input("按回车继续...")
            continue

        # 原有回车逻辑
        if not show_mean:
            show_mean = True
        else:
            idx = (idx + 1) % total
            show_mean = False

if __name__ == "__main__":
    main()