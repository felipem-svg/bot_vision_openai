
import os, base64, requests, logging, json, io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from PIL import Image

# (Opcional, útil para desenvolvimento local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN não definido.")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY não definido.")

client = OpenAI(api_key=OPENAI_API_KEY)

# Guarda quando o usuário iniciou a conversa
chat_start_times = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    from datetime import datetime, timezone, timedelta
    # Salva o horário de início da conversa em ISO (UTC-3 por padrão)
    now = datetime.now(timezone(timedelta(hours=-3))).isoformat()
    chat_start_times[chat_id] = now
    await update.message.reply_text(
        "Olá! 👋\nEnvie um print do seu depósito.\n"
        "A IA vai validar se o depósito foi feito **após o início da conversa**."
    )

def _bytes_to_png_data_url(raw: bytes) -> str:
    """Abre bytes com Pillow e converte para PNG (RGB), retornando data URL."""
    img = Image.open(io.BytesIO(raw))
    if img.mode in ("P", "RGBA"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def _analyze_image_data_url(data_url: str, chat_started_at_iso: str) -> str:
    prompt = f"""
    Analise o print e considere APENAS o depósito que está expandido (seta para cima).
    Verifique se está Concluído, extraia Valor e Data/Hora e confirme se a data/hora é posterior a {chat_started_at_iso}.
    Responda curto em PT-BR:
    - Valor
    - Data/hora
    - Resultado: "Aprovado" ou "Reprovado"
    Se não achar o depósito expandido, diga isso.
    """

    response = client.responses.create(
        model="gpt-4o",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": data_url}
            ]
        }],
        temperature=0
    )
    return response.output_text.strip()

async def _download_telegram_file(context: ContextTypes.DEFAULT_TYPE, file_id: str) -> bytes:
    file = await context.bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    resp = requests.get(file_url, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Download falhou (HTTP {resp.status_code})")
    logging.info("Telegram download: Content-Type=%s bytes=%d", resp.headers.get("Content-Type",""), len(resp.content))
    return resp.content

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_started_at_iso = chat_start_times.get(chat_id)
    if not chat_started_at_iso:
        await update.message.reply_text("Por favor, envie /start antes de mandar o print.")
        return

    try:
        # pega a melhor resolução
        photo = update.message.photo[-1]
        raw = await _download_telegram_file(context, photo.file_id)

        # normaliza para PNG data URL
        data_url = _bytes_to_png_data_url(raw)

        result = _analyze_image_data_url(data_url, chat_started_at_iso)
        await update.message.reply_text(result[:4096])
    except Exception as e:
        logging.exception(e)
        await update.message.reply_text("⚠️ Ocorreu um erro ao analisar a imagem. Tente reenviar como *foto* (não como arquivo).")

async def handle_image_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_started_at_iso = chat_start_times.get(chat_id)
    if not chat_started_at_iso:
        await update.message.reply_text("Por favor, envie /start antes de mandar o print.")
        return

    doc = update.message.document
    if not doc or not (doc.mime_type or "").startswith("image/"):
        return

    try:
        raw = await _download_telegram_file(context, doc.file_id)
        data_url = _bytes_to_png_data_url(raw)
        result = _analyze_image_data_url(data_url, chat_started_at_iso)
        await update.message.reply_text(result[:4096])
    except Exception as e:
        logging.exception(e)
        await update.message.reply_text("⚠️ Não consegui processar esse arquivo de imagem. Envie como *foto* ou faça uma nova captura.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_image_document))
    app.run_polling()

if __name__ == "__main__":
    main()
