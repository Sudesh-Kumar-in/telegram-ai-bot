# Telegram AI Chatbot (OpenAI Powered)

Ek production-ready Telegram chatbot jo OpenAI API use karke AI-generated
responses deta hai. Har user ki conversation history SQLite database mein
alag-alag store hoti hai, taaki bot context ke saath baat kar sake.

## Features

- `/start`, `/help`, `/clear` commands
- OpenAI API se AI-generated replies
- Per-user conversation memory (SQLite)
- Long response ka automatic multi-message split
- Typing indicator
- Poori tarah async code
- Proper error handling (OpenAI errors, Telegram errors, timeouts)
- Logging jisme API keys kabhi print nahi hoti
- `.env` se saari configuration (koi hardcoded secret nahi)

## Project Structure

```
telegram-ai-bot/
├── bot.py               # Entry point - app start karta hai
├── config.py             # .env se config load & validate karta hai
├── database.py            # SQLite conversation history (async wrapper)
├── openai_service.py       # OpenAI API calls
├── handlers.py             # Telegram command/message handlers
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Step-by-Step Setup

### 1. Python Install Karna

Python 3.10 ya usse naya version chahiye.

- **Windows/Mac**: [python.org/downloads](https://www.python.org/downloads/) se install karo.
- Install ke waqt "Add Python to PATH" checkbox zaroor select karo (Windows par).

Check karne ke liye terminal/command prompt mein:

```bash
python --version
```

(Kuch systems par `python3 --version` use karna pade.)

---

### 2. Telegram BotFather Se Bot Banana

1. Telegram app kholo aur search karo: `@BotFather`
2. `BotFather` ko `/start` bhejo.
3. `/newbot` command bhejo.
4. Bot ka ek naam do (display name) — jo bhi chaho.
5. Bot ka ek **username** do — ye `bot` se end hona chahiye (jaise `my_ai_chat_bot`).
6. BotFather aapko ek **token** dega, jaisa dikhta hai:
   ```
   123456789:AAExampleTokenXXXXXXXXXXXXXXXXXXXXX
   ```
   **Ye token kisi ke saath share mat karo.**

---

### 3. Telegram Bot Token Configure Karna

Ye token `.env` file mein `TELEGRAM_BOT_TOKEN` ke against daalna hoga
(neeche Step 7 mein batayenge).

---

### 4. OpenAI API Key Configure Karna

1. [platform.openai.com](https://platform.openai.com/) par account banao/login karo.
2. Left sidebar mein **API Keys** section mein jao (ya seedha
   [platform.openai.com/api-keys](https://platform.openai.com/api-keys)).
3. **Create new secret key** par click karo aur key copy kar lo (ye sirf ek
   baar dikhti hai, isliye turant kahin safe save kar lo).
4. Ye key `.env` file mein `OPENAI_API_KEY` ke against daalni hogi.

> **Note:** OpenAI API use karne ke liye aapke account mein billing/credits
> setup hona zaroori hai.

---

### 5. Virtual Environment Banana

Project folder ke andar jaake:

```bash
cd telegram-ai-bot
```

Virtual environment banao:

```bash
# Windows
python -m venv venv

# Mac/Linux
python3 -m venv venv
```

Activate karo:

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

Activate hone ke baad terminal ke start mein `(venv)` dikhega.

---

### 6. Dependencies Install Karna

```bash
pip install -r requirements.txt
```

Ye install karega:
- `python-telegram-bot` — Telegram Bot API library
- `openai` — official OpenAI Python SDK
- `python-dotenv` — `.env` file read karne ke liye

---

### 7. `.env` Configure Karna

`.env.example` ko copy karke `.env` naam ki nayi file banao:

```bash
# Mac/Linux
cp .env.example .env

# Windows
copy .env.example .env
```

Ab `.env` file ko kisi text editor mein kholo aur values fill karo:

```
TELEGRAM_BOT_TOKEN=123456789:AAExampleTokenXXXXXXXXXXXXXXXXXXXXX
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

> **Security reminder:** `.env` file kabhi Git/GitHub par push mat karna.
> Ye already `.gitignore` mein add hai isliye accidentally commit nahi hogi.

**Model ke baare mein:** `OPENAI_MODEL` variable se model easily change ho
sakta hai. Agar koi model name invalid/unavailable nikle, bas `.env` mein
`OPENAI_MODEL` value badal do (jaise `gpt-4o-mini`, `gpt-4o`, ya koi aur
account mein available model) — code mein kuch change karne ki zaroorat
nahi.

---

### 8. Bot Locally Run Karna

Virtual environment activate hone ke saath:

```bash
python bot.py
```

Agar sab sahi hai to terminal mein dikhega:

```
Starting Telegram AI bot...
Database initialized successfully.
Bot is running. Press Ctrl+C to stop.
```

Ab Telegram par apne bot ko open karo aur `/start` bhejo!

Bot band karne ke liye terminal mein `Ctrl + C` dabao.

---

### 9. Common Errors Aur Unke Solutions

| Error | Reason | Solution |
|---|---|---|
| `[CONFIG ERROR] Missing required environment variable(s): TELEGRAM_BOT_TOKEN` | `.env` file missing hai ya token empty hai | `.env` file check karo, token sahi se paste karo |
| `Unauthorized` (Telegram) | Bot token galat hai | BotFather se token dobara copy karo |
| `AuthenticationError` (OpenAI) | OpenAI API key galat hai ya expire ho gayi | Naya API key generate karo aur `.env` update karo |
| `RateLimitError` | OpenAI account mein credits khatam ya rate limit lag gaya | OpenAI billing/usage dashboard check karo |
| `ModuleNotFoundError: No module named 'telegram'` | Dependencies install nahi hui / venv activate nahi hai | Virtual environment activate karo, `pip install -r requirements.txt` chalao |
| Bot response nahi de raha / hang ho gaya | Internet issue ya OpenAI timeout | Kuch der baad try karo, `OPENAI_TIMEOUT` value `.env` mein badhao |
| `sqlite3.OperationalError: database is locked` | Bahut zyada simultaneous requests (rare, low-traffic bots mein nahi hota) | Bot restart karo; heavy traffic ke liye Postgres jaisa DB consider karo |

---

### 10. Production Deployment (Basic Process)

Ye bot **polling mode** mein chalta hai, jo simple VPS/server deployment ke
liye perfect hai (Telegram se webhook setup ki zaroorat nahi).

**General steps kisi bhi Linux server (jaise Ubuntu VPS, AWS EC2, DigitalOcean Droplet) par:**

1. Server par code upload karo (Git ya SCP se):
   ```bash
   git clone <your-repo-url>
   cd telegram-ai-bot
   ```

2. Python, venv, aur dependencies install karo (Steps 5-6 jaisa).

3. `.env` file server par banao (values ko kabhi Git mein commit mat karna,
   seedha server par create karo):
   ```bash
   nano .env
   # values paste karke save karo (Ctrl+O, Enter, Ctrl+X)
   ```

4. Bot ko background mein continuously chalane ke liye ek process manager
   use karo, jaise **systemd** (recommended):

   `/etc/systemd/system/telegram-ai-bot.service` file banao:
   ```ini
   [Unit]
   Description=Telegram AI Bot
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/telegram-ai-bot
   ExecStart=/path/to/telegram-ai-bot/venv/bin/python bot.py
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

   Fir enable aur start karo:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-ai-bot
   sudo systemctl start telegram-ai-bot
   ```

   Logs dekhne ke liye:
   ```bash
   sudo journalctl -u telegram-ai-bot -f
   ```

5. Alternative: `tmux`/`screen` session mein bhi chala sakte ho for quick
   testing, ya Docker container mein bhi deploy kar sakte ho — jo bhi aapke
   hosting setup ke liye suitable ho.

**Zaroori reminders:**
- `.env` file production server par bhi kabhi public repo mein commit mat
  karna.
- SQLite single-server deployments ke liye theek hai; agar aage multiple
  server instances chalane ho (horizontal scaling), to PostgreSQL jaisa DB
  consider karo.

---

## Quick Command Summary

```bash
cd telegram-ai-bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # phir .env mein values fill karo
python bot.py
```

Bot chal jaayega — Telegram par `/start` bhejo aur enjoy karo! 🚀
