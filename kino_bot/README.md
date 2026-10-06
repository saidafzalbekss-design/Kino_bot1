# Kino Bot (aiogram 3)

Telegram kino bot. Foydalanuvchi kino kodini yozadi yoki ro'yxatdan tanlaydi, bot kinoni yuboradi.
Adminlar bot ichida kino qo'shadi va o'chiradi.

## Struktura

```
kino_bot/
├── main.py              # Botni ishga tushirish
├── config.py            # TOKEN, ADMIN_IDS, sozlamalar
├── requirements.txt
├── database/
│   ├── __init__.py
│   └── db.py            # SQLite so'rovlari (aiosqlite)
├── handlers/
│   ├── start.py         # /start, bosh menyu
│   ├── user.py          # Kinolar ro'yxati, kod bilan kino olish
│   └── admin.py         # Kino qo'shish / o'chirish (faqat adminlar)
├── keyboards/
│   └── inline.py        # Inline tugmalar
├── states/
│   └── admin.py         # FSM holatlari
├── filters/
│   └── admin.py         # IsAdmin filtri
└── utils/
    └── helpers.py       # send_movie, safe_edit
```

## Ishga tushirish

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`config.py` ni oching va to'ldiring:

- `BOT_TOKEN` — @BotFather'dan olingan token
- `ADMIN_IDS` — adminlar Telegram ID'lari (@userinfobot orqali bilasiz)

Keyin:

```bash
python main.py
```

## Foydalanish

- Hamma: `/start` → "Kinolar ro'yxati" yoki kod yozish
- Admin: bosh menyuda "➕ Kino qo'shish" va "🗑 Kino o'chirish" tugmalari chiqadi
- Admin buyruqlari: `/addmovie`, `/cancel`

Yangi admin qo'shish: `config.py` dagi `ADMIN_IDS` ga ID qo'shib, botni qayta ishga tushiring.
# tg-bot-
# tg-bot-
# kino_bot
