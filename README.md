# Pizzeria Assistant — Telegram AI Chatbot (Demo)

A Telegram chatbot that answers customer questions for a small business
using the Google Gemini API. This demo uses a **fictional** pizzeria
("Da Marco"), but the bot is configured entirely through two text files,
so it can be adapted to another business without changing the code.

![Demo conversation](docs/demo.png)

## What it does

- Answers questions about the menu, prices, opening hours and delivery
- Says politely when it doesn't know something and gives the phone number
  instead of making up an answer
- Refuses off-topic questions (poems, news, general knowledge)
- Replies in the customer's language
- Remembers the last 10 exchanges of each conversation; `/reset` clears it

## How it works

- `bot.py` receives Telegram messages (python-telegram-bot) and sends
  them, with the recent history, to Gemini.
- `prompt.txt` holds the fixed rules (stay on topic, never invent
  information, how to format replies).
- `business.txt` holds the business data (menu, hours, delivery, phone).
  Edit this file to change the business.

The bot only knows what is in `business.txt`. That is how it avoids
inventing answers.

## Setup

Requires Python 3.10 or newer.

```bash
git clone https://github.com/ALEX323jh/Demo-Telegram-Bot.git
cd Demo-Telegram-Bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
   and copy the token.
2. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/).
3. Copy `.env.example` to `.env` and fill in both values.
4. Run the bot:

```bash
python bot.py
```

Send your bot a message on Telegram to try it.

## Adapting it to another business

1. Replace the contents of `business.txt` with the new business data.
2. Keep the rules in `prompt.txt` (change the wording only if needed).
3. Restart the bot.

The model is set by `MODEL_NAME` in `bot.py`.

## Commands

| Command  | Description                          |
|----------|--------------------------------------|
| `/reset` | Clears the conversation history      |

## Limitations

- Conversation history is stored in memory and is lost when the bot
  restarts.
- The bot cannot take orders or reservations; it directs customers to
  the phone number.
- It was tested on the Gemini free tier, which has rate limits and
  should not be used with real customer data.
- LLMs can still make mistakes. Test the bot with tricky questions
  before using it with real customers.

## Tech stack

Python, python-telegram-bot, Google Gemini API (google-genai), python-dotenv