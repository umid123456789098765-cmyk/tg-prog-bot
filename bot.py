"""
Бот: генерирует пост про программирование через Claude API
и отправляет его в Telegram-канал.

Запускается по расписанию через GitHub Actions (см. .github/workflows/post.yml).

Нужны переменные окружения (задаются как GitHub Secrets):
  TELEGRAM_BOT_TOKEN   - токен бота от @BotFather
  TELEGRAM_CHANNEL_ID  - @username_канала или числовой chat_id
  ANTHROPIC_API_KEY    - ключ Anthropic API
"""

import os
import random
import sys
import requests

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

# Пул тем, чтобы посты не повторялись слишком часто.
# Каждый запуск случайно выбирает 1-2 темы и просит модель
# написать пост, слегка отталкиваясь от них (но не обязательно строго по теме).
TOPICS = [
    "полезная фича Python, о которой мало кто знает",
    "разница между двумя похожими концепциями (например, стек и очередь)",
    "хороший совет по чистому коду",
    "интересный факт из истории языков программирования",
    "распространённая ошибка джуниора и как её избежать",
    "объяснение алгоритма или структуры данных простыми словами",
    "полезная команда/трюк в Git",
    "разница между двумя похожими инструментами (REST vs GraphQL и т.п.)",
    "принцип SOLID или другой паттерн проектирования",
    "интересная деталь про то, как работает память/сеть/ОС",
    "лайфхак по продуктивности разработчика",
    "разбор частой ошибки в понимании асинхронности/многопоточности",
]

SYSTEM_PROMPT = """Ты ведёшь Telegram-канал про программирование.
Твоя задача — написать ОДИН короткий пост для канала.

Требования:
- Язык: русский
- Длина: 3-7 предложений (коротко и по делу, это Telegram, не лонгрид)
- Без markdown-разметки (**, ##, и т.п.) — только обычный текст, можно эмодзи по делу (1-2 шт, не переусердствуй)
- Можно короткий пример кода, если уместно — в тройных апострофах не нужно, просто впиши как есть
- Стиль: живой, конкретный, без воды и без вступлений в духе "Сегодня поговорим о..."
- В конце — необязательно, но можно короткий вопрос к читателям для вовлечения
- Не подписывай пост, не добавляй хэштеги, не пиши "Пост:" в начале — выдай только сам текст поста
"""


def generate_post() -> str:
    api_key = os.environ["ANTHROPIC_API_KEY"]
    topics = random.sample(TOPICS, k=2)
    user_prompt = (
        f"Оттолкнись (необязательно строго) от одной из этих тем: "
        f"«{topics[0]}» или «{topics[1]}». Напиши пост."
    )

    response = requests.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-5",
            "max_tokens": 500,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    text_parts = [block["text"] for block in data["content"] if block.get("type") == "text"]
    post_text = "\n".join(text_parts).strip()

    if not post_text:
        raise RuntimeError(f"Пустой ответ от Claude API: {data}")

    return post_text


def send_to_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    channel_id = os.environ["TELEGRAM_CHANNEL_ID"]

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
        post = generate_post()
        print("Сгенерированный пост:\n" + post)
        send_to_telegram(post)
        print("Пост успешно отправлен в канал.")
        return 0
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
