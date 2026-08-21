"""
Бот: берёт готовый пост про программирование из posts.py
и отправляет его в Telegram-канал. Если у поста указана картинка —
отправляет фото с подписью, если нет — просто текст.

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

TELEGRAM_SEND_MESSAGE_URL = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_SEND_PHOTO_URL = "https://api.telegram.org/bot{token}/sendPhoto"

# Telegram ограничивает подпись к фото 1024 символами (текст без фото — до 4096).
PHOTO_CAPTION_LIMIT = 1024

SLOT_HOURS = [4, 9, 14]


def pick_post() -> dict:
    now = datetime.now(timezone.utc)
    day_of_year = now.timetuple().tm_yday
    slot = min(range(len(SLOT_HOURS)), key=lambda i: abs(SLOT_HOURS[i] - now.hour))
    index = (day_of_year * len(SLOT_HOURS) + slot) % len(POSTS)
    return POSTS[index]


def send_to_telegram(post: dict) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")

    if not token:
        raise RuntimeError("Секрет TELEGRAM_BOT_TOKEN не задан или пустой.")
    if not channel_id:
        raise RuntimeError("Секрет TELEGRAM_CHANNEL_ID не задан или пустой.")

    text = post["text"]
    image_url = post.get("image")

    print(f"Длина токена: {len(token)} символов")
    print(f"Есть картинка: {'да' if image_url else 'нет'}")

    if image_url:
        caption = text if len(text) <= PHOTO_CAPTION_LIMIT else text[:PHOTO_CAPTION_LIMIT - 1] + "…"
        response = requests.post(
            TELEGRAM_SEND_PHOTO_URL.format(token=token),
            json={
                "chat_id": channel_id,
                "photo": image_url,
                "caption": caption,
            },
            timeout=30,
        )
    else:
        response = requests.post(
            TELEGRAM_SEND_MESSAGE_URL.format(token=token),
            json={
                "chat_id": channel_id,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=30,
        )

    if not response.ok:
        raise RuntimeError(
            f"Telegram API вернул ошибку. HTTP статус: {response.status_code}. "
            f"Тело ответа: {response.text}"
        )


def main() -> int:
    try:
        post = pick_post()
        print("Отправляемый пост:\n" + post["text"])
        send_to_telegram(post)
        print("Пост успешно отправлен в канал.")
        return 0
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
