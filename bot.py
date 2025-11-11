import os, base64, requests, logging, json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

chat_start_times = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone(timedelta(hours=-3))).isoformat()
    chat_start_times[chat_id] = now
    await update.message.reply_text(
        "Olá! 👋\nEnvie um print do seu depósito.\n"
        "A IA vai validar se o depósito foi feito **após o início da conversa**."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_started_at_iso = chat_start_times.get(chat_id)

    if not chat_started_at_iso:
        await update.message.reply_text("Por favor, envie /start antes de mandar o print.")
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    img_bytes = requests.get(file_url).content
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    prompt = f"""
Analise o print enviado e extraia apenas o depósito que está expandido (seta para cima).
Verifique se o depósito foi concluído e se a data/hora do depósito é posterior a {chat_started_at_iso}.
Retorne um resumo curto em português:
- Valor
- Data/hora
- Resultado: "Aprovado" ou "Reprovado"
    """

    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url}
                ]
            }]
        )
        result = response.output_text.strip()
        await update.message.reply_text(result[:4096])

    except Exception as e:
        logging.exception(e)
        await update.message.reply_text("⚠️ Ocorreu um erro ao analisar a imagem.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
