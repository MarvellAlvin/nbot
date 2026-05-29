import os
import json
import requests
from dotenv import load_dotenv
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
INDO_API_KEY = os.getenv('INDO_API_KEY')
API_BASE = "https://indosmm.id/api/v2"

# ----------- FUNGSI PEMBANTU API -----------
def indo_api(action: str, **params) -> dict:
    """Panggil API IndoSMM dan kembalikan response JSON."""
    payload = {"key": INDO_API_KEY, "action": action}
    payload.update(params)
    try:
        r = requests.post(API_BASE, data=payload, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ----------- COMMAND BOT -----------
def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Halo! Selamat datang di bot SMM Panel.\n"
             "Gunakan perintah:\n"
             "/services - Lihat daftar layanan\n"
             "/balance - Cek saldo\n"
             "/add <service_id> <jumlah> <link> - Buat pesanan\n"
             "/status <order_id> - Cek status pesanan"
    )

def balance(update, context):
    data = indo_api("balance")
    if "balance" in data:
        bal = data["balance"]
        cur = data.get("currency", "USD")
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"💰 Saldo: {bal} {cur}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"❌ Gagal: {data.get('error', 'Unknown')}")

def services(update, context):
    data = indo_api("services")
    if isinstance(data, list) and len(data) > 0:
        # Tampilkan 10 layanan pertama agar tidak terlalu panjang
        text = "📋 *Daftar Layanan (10 pertama):*\n\n"
        for s in data[:10]:
            text += (
                f"ID: `{s['service']}`\n"
                f"Nama: {s['name']}\n"
                f"Kategori: {s.get('category','')}\n"
                f"Harga: ${s['rate']} | Min: {s['min']} – Max: {s['max']}\n"
                f"Refill: {'✅' if s.get('refill') else '❌'} | Cancel: {'✅' if s.get('cancel') else '❌'}\n\n"
            )
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=text, parse_mode="Markdown")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="❌ Gagal mengambil daftar layanan.")

def add_order(update, context):
    try:
        # Format: /add <service_id> <quantity> <link>
        args = context.args
        svc = int(args[0])
        qty = int(args[1])
        link = args[2]
    except (IndexError, ValueError):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="❌ Format salah. Gunakan:\n`/add <service_id> <jumlah> <link>`",
                                 parse_mode="Markdown")
        return

    data = indo_api("add", service=svc, quantity=qty, link=link)
    if "order" in data:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"✅ Pesanan berhasil!\nID Order: `{data['order']}`",
                                 parse_mode="Markdown")
    else:
        err = data.get("error", "Unknown error")
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"❌ Gagal membuat pesanan: {err}")

def status(update, context):
    if len(context.args) < 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="❌ Format: `/status <order_id>`", parse_mode="Markdown")
        return
    order_id = context.args[0]
    data = indo_api("status", order=order_id)
    if "error" in data:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"❌ Error: {data['error']}")
        return
    msg = (
        f"📊 *Status Order* #{order_id}\n"
        f"Status: `{data.get('status')}`\n"
        f"Sisa: {data.get('remains', '?')}\n"
        f"Biaya: ${data.get('charge', '?')}\n"
        f"Mata Uang: {data.get('currency', 'USD')}"
    )
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=msg, parse_mode="Markdown")

# Command tambahan yang Anda sudah punya (tidak dihapus)
def puisi(update, context):
    text_puisi = "bercahayalah jika kamu ingin dicintai setiap lawan jenis. 😉"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_puisi)

def pantun(update, context):
    text_pantun = "jalan-jalan ke jakarta barat, pulangnya beli sempolan. kalau kamu tidak ingin bersahabat, mari kita pacaran"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_pantun)

def echo(update, context):
    message = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

# ----------- MAIN -----------
def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handler perintah
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('balance', balance))
    dp.add_handler(CommandHandler('services', services))
    dp.add_handler(CommandHandler('add', add_order))
    dp.add_handler(CommandHandler('status', status))
    # Perintah lama Anda
    dp.add_handler(CommandHandler('puisi', puisi))
    dp.add_handler(CommandHandler('pantun', pantun))

    # Echo pesan biasa
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Mulai polling
    updater.start_polling()
    print("Bot berjalan...")
    updater.idle()

if __name__ == '__main__':
    main()