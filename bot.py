import os
from google import genai
from google.genai import types
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"
MAX_HISTORY_TURNS = 10
HISTORY_KEY = "conversation_history"

BASE_DIR = Path(__file__).parent
RULES = (BASE_DIR / "prompt.txt").read_text(encoding="utf-8")
BUSINESS = (BASE_DIR / "business.txt").read_text(encoding="utf-8")
SYSTEM_PROMPT = f"{RULES}\n\nBUSINESS INFORMATION:\n{BUSINESS}"

def split_message(text, max_length=3500):
    parts = []
    while len(text) > max_length:
        cut = text.rfind("\n", 0, max_length)
        if cut == -1:
            cut = max_length
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")

    parts.append(text)
    return parts

async def safe_reply(message, text):
    try:
        await message.reply_text(text, parse_mode='Markdown')
    except BadRequest:
        await message.reply_text(text)

async def handle_message(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return

    user_message = update.message.text
    history = _context.user_data.setdefault(HISTORY_KEY, [])
    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )

    try:
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=[*history, user_content],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )

        bot_response = response.text
        if not bot_response:
            raise RuntimeError("Gemini returned an empty response")

        history.extend(
            [
                user_content,
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=bot_response)],
                ),
            ]
        )
        del history[: -(MAX_HISTORY_TURNS * 2)]

        message_parts = split_message(bot_response)

        for part in message_parts:
            await safe_reply(update.message, part)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Sorry, something went wrong. Please try again.")

async def reset_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(HISTORY_KEY, None)
    if update.message is not None:
        await update.message.reply_text("Conversation history cleared.")

async def close_genai_client(_application: Application) -> None:
    await client.aio.aclose()

def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_shutdown(close_genai_client)
        .build()
    )
    app.add_handler(CommandHandler("reset", reset_conversation))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()