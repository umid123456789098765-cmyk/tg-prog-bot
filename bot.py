"""
Бот: берёт готовый пост про программирование из posts.py
и отправляет его в Telegram-канал.

Никакого AI, никаких платных API — только Telegram, который бесплатен.

Запускается по расписанию через GitHub Actions (см. .github/workflows/post.yml).

Нужны переменные окружения (задаются как GitHub Secrets):
  TELEGRAM_BOT_TOKEN   - токен бота от @BotFather
  TELEGRAM_CHANNEL_ID  - @username_канала или числовой chat_id
"""

import os
import sys
from datetime import datetime, timezone

import requests

from posts import POSTS

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

SLOT_HOURS = [4, 9, 14]


def pick_post() -> str:
    now = datetime.now(timezone.utc)
    day_of_year = now.timetuple().tm_yday

    slot = min(range(len(SLOT_HOURS)), key=lambda i: abs(SLOT_HOURS[i] - now.hour))

    index = (day_of_year * len(SLOT_HOURS) + slot) % len(POSTS)
    return POSTS[index]


def send_to_telegram(text: str) -> None:
    token = os.environ["8941079708:AAGL_hHy3bbw5kNc3votICVV74u_Hnze4Mc"]
    channel_id = os.environ["https://t.me/dasturchi_log"]

    response = requests.post(
        TELEGRAM_API_URL.format(token=token),
        json={
            "chat_id": channel_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(f"Ошибка Telegram API: {response.status_code} {response.text}")


def main() -> int:
    try:
        post = pick_post()
        print("Отправляемый пост:\n" + post)
        send_to_telegram(post)
        print("Пост успешно отправлен в канал.")
        return 0
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
