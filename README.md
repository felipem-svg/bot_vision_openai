# Telegram Deposit Validator Bot 🤖💰

Bot do Telegram que valida prints de depósitos (ex: BetBoom) com ajuda da IA da OpenAI.

## 🔧 Como funciona
1. Usuário envia `/start`
2. Bot salva o horário da conversa
3. Usuário manda o print
4. IA analisa o print e verifica:
   - Se é um depósito concluído
   - Se o horário é posterior ao início da conversa

## 🛠️ Setup local

```bash
git clone https://github.com/seuusuario/telegram-deposit-validator.git
cd telegram-deposit-validator
pip install -r requirements.txt
cp .env.example .env
# preencha TELEGRAM_BOT_TOKEN e OPENAI_API_KEY
python bot.py
```

## ☁️ Deploy no Railway

1. Crie um novo projeto no [Railway](https://railway.app)
2. Faça upload deste repositório
3. Configure as variáveis de ambiente:
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
4. Deploy como **Worker**
5. Seu bot estará online 🎉

---

Feito com ❤️ usando [python-telegram-bot](https://python-telegram-bot.org) + [OpenAI GPT-4o](https://platform.openai.com/docs/guides/vision)
