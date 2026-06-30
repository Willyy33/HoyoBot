# HoYo Daily Check-in Bot
Get your Stellar Jade and Polychrome every month

A Playwright-based automation bot that automatically performs daily check-ins for HoYoLAB games:
- Honkai: Star Rail (HSR)
- Zenless Zone Zero (ZZZ)

The bot handles login sessions, popup handling, and daily reward claiming automatically.

---

## Setup Instructions

### 1. Install dependencies
```
pip install playwright python-dotenv
playwright install
```

### 2. Create .env
```
HOYO_EMAIL=your_email@example.com
HOYO_PASSWORD=your_password
```

### 3. Run manually
```
python bot.py
```