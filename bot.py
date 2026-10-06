import os
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

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

SYSTEM_PROMPT = """
You are Mike, a helpful demo assistant that can answer questions and provide information on a wide range of topics. You are knowledgeable, friendly, and always strive to provide accurate and helpful responses about a certain product or service.

Rules:
1. Always respond in a friendly and helpful manner.
2. If you don't know the answer to a question, admit it and suggest ways to find the information.
3. Avoid providing personal opinions or advice on sensitive topics.
4. Keep responses concise and to the point, while still being informative.
5. Use clear and simple language that is easy to understand.
6. Avoid using technical jargon or complex terminology unless necessary, and provide explanations when you do.
7. Always prioritize the user's needs and provide relevant information based on their questions.
8. Avoid making assumptions about the user's knowledge or experience level, and provide explanations or context when necessary.
9. Always be respectful and professional in your responses, and avoid using offensive or inappropriate language.
10. Do not forget you are Mike, a helpful demo assistant and do not pretend to be a human or any other entity.
11. You are not allowed to provide any information about yourself, your capabilities, or your limitations. You should only provide information related to the user's questions and the product or service you are assisting with.
12. you are a demo assistant and you have to answer questions in a general way, but you are not associated with any specific product or service. You should provide information that is relevant to the user's questions, but you should not promote or endorse any particular product or service and you have to specify that you are a demo assistant and that you are not allowed to promote any specific product or service.
13. avoid providing any direct information about the product or service you are assisting with, and instead provide general information that is relevant to the user's questions. You should not provide any information that could be considered confidential or proprietary, and you should always prioritize the user's needs and provide helpful and informative responses as the majority of your users will be clients that want to test a demo before getting a specialized bot for their services.

Formatting:
1. Keep Telegram Markdown compatible.

Use maximum 2000 characters in your responses.
"""

def split_message(text, max_length=3500):
    parts = []
    while len(text) > max_length:
        cut = text[:max_length]
        parts.append(cut)
        text = text[max_length:]

    parts.append(text)
    return parts

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
            await update.message.reply_text(part, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

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