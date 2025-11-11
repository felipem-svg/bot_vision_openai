
# Telegram Deposit Validator Bot 🤖💰 (Patch: imagens robustas)

Este bot valida prints de depósito com IA (OpenAI). Este patch adiciona:
- Conversão automática de qualquer imagem para PNG com Pillow
- Suporte a fotos (`photo`) e documentos de imagem (`document`)
- Logs úteis (content-type/tamanho)
- Carregamento opcional de `.env` no desenvolvimento

## Setup local

```bash
pip install -r requirements.txt
cp .env.example .env  # preencha os valores
python bot.py
```

## Railway
- Configure as variáveis: `TELEGRAM_BOT_TOKEN` e `OPENAI_API_KEY`
- Deploy como Worker (Procfile incluso)
