#!/usr/bin/env python3
"""
MEXC Twitter/X Giveaway Parser + Telegram уведомления
Мониторит 25 аккаунтов MEXC и фильтрует посты по ключевым словам
"""

import time
import json
import requests
from datetime import datetime

# ─── НАСТРОЙКИ ────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN = "8926816082:AAEPfsToGr4Gvpmf2kiqMPU6bYHSj0GPlZw"
TELEGRAM_CHAT_ID = "8926816082"

ACCOUNTS = [
    "MEXC", "MEXCZH", "MEXC_Thailand", "MEXCRussian", "MEXCUKR",
    "MEXC_Japan", "mexc_mena", "MEXCespanol", "mexc_portuguese",
    "MEXC_Poland", "MEXC_PAK", "MEXCVietnam", "MEXC_Romania",
    "MEXCOceania", "MEXC_AfricaBU", "MEXC_SouthAsia", "MEXC_SEA",
    "MEXC_SriLanka", "MEXC_DE", "MEXCFrancophone", "MEXC_BD",
    "MEXCTrueNorth", "Jamie_MEXC", "MEXC_Predict", "MEXCPioneer",
]

KEYWORDS = [
    # UID
    "uid", "~uid~",
    # English
    "giveaway", "give away", "raffle", "contest", "prize",
    "winner", "reward", "airdrop",
    # Russian
    "розыгрыш", "приз", "победитель", "выиграй", "конкурс",
    # Spanish
    "sorteo", "rifa", "premio", "ganador", "concurso", "regalar",
    # Portuguese
    "sorteio", "prêmio", "premio", "concurso", "vencedor", "brinde", "oferta",
    # Urdu (Pakistan)
    "انعام", "قرعہ اندازی", "مقابلہ", "فاتح", "تحفہ",
    # Arabic
    "هبة", "مسابقة", "جائزة", "فائز", "سحب", "هدية",
]

CHECK_INTERVAL_SECONDS = 300  # Каждые 5 минут

# ─── TELEGRAM ─────────────────────────────────────────────────────────────────

def send_telegram(message: str):
    """Отправляет сообщение в Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }, timeout=10)
        if not resp.ok:
            print(f"  ⚠️  Telegram ошибка: {resp.text}")
    except Exception as e:
        print(f"  ⚠️  Telegram недоступен: {e}")

# ─── ПАРСЕР ───────────────────────────────────────────────────────────────────

def contains_keyword(text: str) -> list:
    text_lower = text.lower()
    return [kw for kw in KEYWORDS if kw.lower() in text_lower]


def save_to_file(tweet: dict, account: str, matched_keywords: list) -> bool:
    filename = "found_giveaways.json"
    entry = {
        "account": account,
        "date": tweet.get("date", ""),
        "text": tweet.get("text", ""),
        "link": tweet.get("link", ""),
        "matched_keywords": matched_keywords,
        "found_at": datetime.now().isoformat(),
    }
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    existing_links = {e.get("link") for e in data}
    if entry["link"] not in existing_links:
        data.append(entry)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    return False


def check_account(scraper, account: str, seen_links: set) -> int:
    found_count = 0
    try:
        print(f"  🔍 @{account}...")
        tweets = scraper.get_tweets(account, mode="user", number=20)
        tweet_list = tweets.get("tweets", [])

        for tweet in tweet_list:
            text = tweet.get("text", "")
            link = tweet.get("link", "")

            if link in seen_links:
                continue
            seen_links.add(link)

            matched = contains_keyword(text)
            if matched:
                is_new = save_to_file(tweet, account, matched)
                if is_new:
                    found_count += 1
                    # Отправка в Telegram
                    short_text = text[:400] + ("..." if len(text) > 400 else "")
                    msg = (
                        f"🎁 <b>Розыгрыш найден!</b>\n\n"
                        f"📌 Аккаунт: <b>@{account}</b>\n"
                        f"🔑 Слова: <b>{', '.join(matched)}</b>\n\n"
                        f"📝 {short_text}\n\n"
                        f"🔗 {link}"
                    )
                    send_telegram(msg)
                    print(f"  ✅ Найдено и отправлено в Telegram: @{account}")

    except Exception as e:
        print(f"  ⚠️  Ошибка @{account}: {e}")

    return found_count


def run():
    try:
        from ntscraper import Nitter
    except ImportError:
        print("❌ Установи: pip install ntscraper requests")
        return

    print("🚀 MEXC Giveaway Parser запущен")
    print(f"📋 Аккаунтов: {len(ACCOUNTS)}")
    print(f"🔑 Ключевых слов: {len(KEYWORDS)}")
    print(f"📬 Telegram Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"⏱  Интервал: {CHECK_INTERVAL_SECONDS} сек\n")

    # Тестовое сообщение
    send_telegram("✅ <b>MEXC Parser запущен!</b>\nМониторинг 25 аккаунтов начат.")

    scraper = Nitter(log_level=1, skip_instance_check=False)
    seen_links = set()
    iteration = 0

    while True:
        iteration += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Итерация #{iteration}")

        total_found = 0
        for account in ACCOUNTS:
            found = check_account(scraper, account, seen_links)
            total_found += found
            time.sleep(2)

        if total_found == 0:
            print("  ℹ️  Новых розыгрышей не найдено")
        else:
            print(f"  🎉 Всего найдено: {total_found}")

        print(f"  ⏳ Следующая проверка через {CHECK_INTERVAL_SECONDS} сек...")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
