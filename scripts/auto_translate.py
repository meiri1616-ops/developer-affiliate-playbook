import os
import re
import requests

TARGET_LANGS = {
    "zh-TW": {
        "filename": "README_zh-TW.md",
        "name": "繁體中文",
        "current_label": "🇭🇰/🇹🇼 繁體中文 (目前)",
        "prompt": "Translate this Markdown document into Traditional Chinese (Taiwan/Hong Kong convention). Use local terms: 聯盟行銷 instead of 联盟营销, 分潤 instead of 分成, 網路 instead of 网络, 伺服器 instead of 服务器, 提現/出金 instead of 提现."
    },
    "en": {
        "filename": "README_en.md",
        "name": "English",
        "current_label": "🇺🇸 English (Current)",
        "prompt": "Translate this Markdown document into fluent, professional English tailored for indie hackers, software engineers, and affiliate marketers. Emphasize terms like 'Recurring Commission', 'DevTools', 'Indie Hacker', and 'Payout Rails'."
    },
    "ja": {
        "filename": "README_ja.md",
        "name": "日本語",
        "current_label": "🇯🇵 日本語 (現在)",
        "prompt": "Translate this Markdown document into natural Japanese tailored for software developers and tech entrepreneurs (e.g., アフィリエイト, 継続報酬, 不労所得, SaaS, 個人開発)."
    },
    "de": {
        "filename": "README_de.md",
        "name": "Deutsch",
        "current_label": "🇩🇪 Deutsch (Aktuell)",
        "prompt": "Translate this Markdown document into precise, professional German, emphasizing B2B SaaS, recurring commissions (Wiederkehrende Provisionen), and tax compliance (W-8BEN)."
    },
    "es": {
        "filename": "README_es.md",
        "name": "Español",
        "current_label": "🇪🇸 Español (Actual)",
        "prompt": "Translate this Markdown document into neutral, professional Spanish (Español neutro) suitable for Latin America and Spain, focusing on digital nomads and indie developers."
    }
}

def build_lang_bar(current_code):
    links = [
        "[ 🇨🇳 简体中文 ](./README.md)" if current_code != "zh-CN" else "[ 🇨🇳 简体中文 (当前) ](./README.md)",
        "[ 🇭🇰/🇹🇼 繁體中文 ](./README_zh-TW.md)" if current_code != "zh-TW" else "[ 🇭🇰/🇹🇼 繁體中文 (目前) ](./README_zh-TW.md)",
        "[ 🇺🇸 English ](./README_en.md)" if current_code != "en" else "[ 🇺🇸 English (Current) ](./README_en.md)",
        "[ 🇯🇵 日本語 ](./README_ja.md)" if current_code != "ja" else "[ 🇯🇵 日本語 (現在) ](./README_ja.md)",
        "[ 🇩🇪 Deutsch ](./README_de.md)" if current_code != "de" else "[ 🇩🇪 Deutsch (Aktuell) ](./README_de.md)",
        "[ 🇪🇸 Español ](./README_es.md)" if current_code != "es" else "[ 🇪🇸 Español (Actual) ](./README_es.md)"
    ]
    return f"<!-- 多语言切换栏 -->\n**Language / 语言切换**:\n" + " · ".join(links)

def translate_with_gemini(text, target_conf):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("未检测到 GEMINI_API_KEY")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    system_instruction = (
        f"{target_conf['prompt']}\n"
        "CRITICAL RULES:\n"
        "1. Do NOT translate or modify any URLs, affiliate links, image links, or badges.\n"
        "2. Keep the exact Markdown table structure, pipes '|', and spacing.\n"
        "3. Keep code blocks, backticks `...`, and tags untouched.\n"
        "4. Output ONLY the translated Markdown directly, with NO conversational filler."
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": system_instruction},
                {"text": text}
            ]
        }],
        "generationConfig": {"temperature": 0.2}
    }

    res = requests.post(url, json=payload, headers=headers, timeout=60)
    if res.status_code == 200:
        data = res.json()
        candidates = data.get("candidates", [])
        if candidates:
            return candidates[0]["content"]["parts"][0]["text"].strip()
    
    raise Exception(f"Gemini 翻译失败: {res.text}")

def main():
    if not os.path.exists("README.md"):
        print("未找到 README.md，退出。")
        return

    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # 清理已有的语言栏，避免重复叠加
    content_clean = re.sub(r"<!-- 多语言切换栏 -->.*?\*\*Language / 语言切换\*\*.*?(?=\n\n|\r\n\r\n)", "", content, flags=re.DOTALL)

    for lang_code, conf in TARGET_LANGS.items():
        print(f"⏳ 正在自动化生成 {conf['name']} ({conf['filename']})...")
        try:
            translated_body = translate_with_gemini(content_clean, conf)
            lang_bar = build_lang_bar(lang_code)
            
            # 将多语言栏优雅插入到主标题下方
            if "# 🛠️" in translated_body:
                parts = translated_body.split("# 🛠️", 1)
                final_content = parts[0] + "# 🛠️" + parts[1].split("\n", 1)[0] + f"\n\n{lang_bar}\n" + parts[1].split("\n", 1)[1]
            else:
                final_content = f"{lang_bar}\n\n" + translated_body

            with open(conf["filename"], "w", encoding="utf-8") as out_f:
                out_f.write(final_content)
                
            print(f"✅ {conf['filename']} 生成成功！")
        except Exception as e:
            print(f"❌ 翻译 {lang_code} 出错: {e}")

if __name__ == "__main__":
    main()
