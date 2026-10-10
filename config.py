"""Bot sozlamalari. Maxfiy qiymatlar muhit o'zgaruvchilaridan olinadi."""
import os

# Token kodda YOZILMAYDI. Render'da Environment Variables ga BOT_TOKEN qo'shing.
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

_admins = os.getenv("ADMIN_IDS", "8748576232,8137244603,8949654147")
ADMIN_IDS = [int(x) for x in _admins.replace(" ", "").split(",") if x]

DB_PATH = os.getenv("DB_PATH", "kino.db")

PAGE_SIZE = 1

# VIP so'ragan odam shu username'ga yozadi. Pastga o'zingizning username'ingizni yozing.
VIP_CONTACT = os.getenv("VIP_CONTACT", "@abdrxmvv13,@someone10110101101")
