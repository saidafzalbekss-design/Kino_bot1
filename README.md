# Kino Bot (aiogram 3, webhook)

Render'da ishga tushirish (Web Service):

- Build Command: `pip install -r requirements.txt`
- Start Command: `python main.py`
- Environment Variables:
  - `BOT_TOKEN` = BotFather tokeni
  - `WEBHOOK_URL` = (ixtiyoriy) o'z domeningiz; bo'lmasa Render'ning `RENDER_EXTERNAL_URL` ishlatiladi

## VIP bo'limi

Admin buyruqlari:
- `/addvip <user_id>` — muddatsiz VIP berish
- `/addvip <user_id> <kun>` — masalan `/addvip 123456789 30`
- `/delvip <user_id>` — VIP'ni olib tashlash
- `/vips` — VIP foydalanuvchilar ro'yxati
- `/movievip <kod>` — mavjud kinoni VIP <-> oddiy qilish

Foydalanuvchi `/id` yuborib o'z ID raqamini bilib oladi.
Ixtiyoriy: `VIP_CONTACT` (masalan `@admin_username`) — VIP so'ragan odamga ko'rsatiladi.
