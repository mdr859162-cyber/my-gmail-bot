import io
import logging
import random
import sqlite3
import string
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# --- CONFIGURATION DATA ---
BOT_TOKEN = "8845301572:AAFyieYesphBdY5jGMro07dD1C5QfQ5Q7iU"
ADMIN_ID = 8422485324
SUPPORT_GROUP_LINK = "https://t.me/gmailhubsaport"
HELPLINE_USERNAME = "gmailhub_Helpline"

MIN_WITHDRAW = 100.0
GMAIL_PRICE = 18.0
REFERRAL_BONUS = 10.0
WORK_VIDEO_LINK = "https://t.me/gmailhubsaport/3"

# --- DATABASE SETUP ---
DB_NAME = "gmail_bot_v2.db"

def init_db():
  conn = sqlite3.connect(DB_NAME, timeout=15)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            pending_balance REAL DEFAULT 0.0,
            total_earned REAL DEFAULT 0.0,
            today_tasks INTEGER DEFAULT 0,
            total_tasks INTEGER DEFAULT 0,
            referred_by INTEGER,
            referrals_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS gmail_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            password TEXT,
            status TEXT DEFAULT 'pending_submit',
            used_by INTEGER DEFAULT NULL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            method TEXT,
            wallet TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

  conn.commit()
  conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def get_user(user_id):
  conn = sqlite3.connect(DB_NAME, timeout=15)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT user_id, balance, pending_balance, total_earned, today_tasks, total_tasks, referred_by, referrals_count, is_active FROM users WHERE user_id = ?",
      (user_id,),
  )
  user = cursor.fetchone()
  conn.close()
  return user

def add_user(user_id, referred_by=None):
  conn = sqlite3.connect(DB_NAME, timeout=15)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR IGNORE INTO users (user_id, balance, pending_balance, total_earned, today_tasks, total_tasks, referred_by, referrals_count, is_active) VALUES (?, 0.0, 0.0, 0.0, 0, 0, ?, 0, 0)",
      (user_id, referred_by),
  )
  conn.commit()
  conn.close()

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  args = context.args

  referred_by = None
  if args and args[0].isdigit():
    referred_by = int(args[0])
    if referred_by == user_id:
      referred_by = None

  add_user(user_id, referred_by)

  welcome_text = (
      "✨ **আসসালামু আলাইকুম! GMAILHUB বটে আপনাকে স্বাগতম** ✨\n\n"
      "💼 আমাদের বটে জিমেইল সেল দিয়ে আপনি খুব সহজেই ইনকাম করতে পারবেন।"
      " এটি ১০০% অটোমেটেড ও বিশ্বাসযোগ্য প্ল্যাটফর্ম।\n\n"
      "👉 কাজ শুরু করতে নিচের **'▶️ Start'** বাটনে ক্লিক করুন।"
  )

  keyboard = [[InlineKeyboardButton("▶️ Start", callback_data="check_join")]]
  await update.message.reply_text(
      welcome_text,
      parse_mode="Markdown",
      reply_markup=InlineKeyboardMarkup(keyboard),
  )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  menu_keyboard = [
      ["💼 কাজ শুরু করুন", "💰 ব্যালেন্স & উইথড্র"],
      ["📊 কাজের রিপোর্ট", "📜 কাজের নিয়ম"],
      ["👥 রেফার করুন", "🎥 আমি নতুন (কাজের ভিডিও)"],
      ["🆘 হেল্পলাইন"],
  ]
  reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)

  join_keyboard = InlineKeyboardMarkup([
      [InlineKeyboardButton("📢 আমাদের চ্যানেলে জয়েন হন", url=SUPPORT_GROUP_LINK)],
      [InlineKeyboardButton("✅ জয়েন সম্পন্ন করেছি", callback_data="show_main_menu")],
  ])

  if query.data == "check_join":
    await query.message.reply_text(
        "⚠️ **বটটি ব্যবহার করার আগে আমাদের চ্যানেলে যুক্ত হন!**",
        parse_mode="Markdown",
        reply_markup=join_keyboard,
    )
  elif query.data == "show_main_menu":
    await query.message.reply_text(
        "🎉 **স্বাগতম!** নিচের মেনু থেকে অপশন বেছে নিন।",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )

# --- ADMIN COMMAND (/getused) ---
async def get_used_gmails(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  if user_id != ADMIN_ID:
    return

  conn = sqlite3.connect(DB_NAME, timeout=15)
  cursor = conn.cursor()
  cursor.execute("SELECT id, email, password, used_by FROM gmail_stock WHERE status = 'approved'")
  rows = cursor.fetchall()

  if not rows:
    conn.close()
    await update.message.reply_text("⚠️ **ডাউনলোড করার মতো কোনো নতুন অ্যাপ্রুভড জিমেইল নেই!**")
    return

  file_content = "=== SUBMITTED GMAILS ===\n\n"
  downloaded_ids = []

  for idx, row in enumerate(rows, 1):
    g_id, email, password, used_by = row
    file_content += f"{idx}. Email: {email} | Password: {password} | User ID: {used_by}\n"
    downloaded_ids.append(g_id)

  file_bytes = io.BytesIO(file_content.encode("utf-8"))
  file_bytes.name = f"approved_gmails_{len(rows)}.txt"

  await update.message.reply_document(
      document=file_bytes,
      caption=f"📂 **মোট {len(rows)} টি জিমেইলের ফাইল।**",
      parse_mode="Markdown",
  )

  cursor.executemany("DELETE FROM gmail_stock WHERE id = ?", [(gid,) for gid in downloaded_ids])
  conn.commit()
  conn.close()

# --- MESSAGE HANDLING ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message or not update.message.text:
    return

  text = update.message.text.strip()
  user_id = update.effective_user.id

  # জিমেইল সাবমিট প্রসেসিং
  if context.user_data.get("awaiting_gmail_submit"):
    if ":" not in text and " " not in text:
      await update.message.reply_text("❌ **ভুল ফরম্যাট!** অনুগ্রহ করে `email:password` এভাবে লিখে পাঠান।")
      return

    try:
      if ":" in text:
        email, password = text.split(":", 1)
      else:
        email, password = text.split(" ", 1)
      
      email = email.strip()
      password = password.strip()
    except Exception:
      await update.message.reply_text("❌ ফরম্যাট সঠিক নয়! উদাহরণ: `example@gmail.com:pass123`")
      return

    conn = sqlite3.connect(DB_NAME, timeout=15)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gmail_stock (email, password, status, used_by) VALUES (?, ?, 'approved', ?)", (email, password, user_id))
    cursor.execute(
        "UPDATE users SET balance = balance + ?, total_earned = total_earned + ?, today_tasks = today_tasks + 1, total_tasks = total_tasks + 1 WHERE user_id = ?",
        (GMAIL_PRICE, GMAIL_PRICE, user_id),
    )

    # রেফার বোনাস
    cursor.execute("SELECT referred_by, is_active FROM users WHERE user_id = ?", (user_id,))
    user_info = cursor.fetchone()

    if user_info and user_info[0] and user_info[1] == 0:
      referred_by = user_info[0]
      cursor.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
      cursor.execute(
          "UPDATE users SET balance = balance + ?, total_earned = total_earned + ?, referrals_count = referrals_count + 1 WHERE user_id = ?",
          (REFERRAL_BONUS, REFERRAL_BONUS, referred_by),
      )
      try:
        await context.bot.send_message(
            chat_id=referred_by,
            text=f"🎉 **রেফার বোনাস!**\nআপনার রেফার করা ইউজার ১ম কাজ সম্পূর্ণ করায় সরাসরি অ্যাকাউন্টে **৳{REFERRAL_BONUS:.0f}.০০** বোনাস যোগ হয়েছে।",
            parse_mode="Markdown",
        )
      except Exception:
        pass

    conn.commit()
    conn.close()
    context.user_data.clear()

    await update.message.reply_text(
        "✅ **আপনার কাজ সফলভাবে জমা হয়েছে!**\n\n"
        f"📩 জিমেইল: `{email}`\n"
        f"💰 আপনার ব্যালেন্সে **৳{int(GMAIL_PRICE)}.০০** যোগ করা হয়েছে।",
        parse_mode="Markdown",
    )
    return

  # উইথড্র ওয়ালেট প্রসেসিং
  if context.user_data.get("awaiting_withdraw_wallet"):
    method = context.user_data.get("withdraw_method")
    wallet = text
    user = get_user(user_id)
    balance = user[1] if user else 0.0

    if balance < MIN_WITHDRAW:
      await update.message.reply_text(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই। সর্বনিম্ন উইথড্র ৳{MIN_WITHDRAW:.0f}")
      context.user_data.clear()
      return

    conn = sqlite3.connect(DB_NAME, timeout=15)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET balance = balance - ?, pending_balance = pending_balance + ? WHERE user_id = ?",
        (balance, balance, user_id),
    )
    cursor.execute(
        "INSERT INTO withdrawals (user_id, amount, method, wallet, status) VALUES (?, ?, ?, ?, 'pending')",
        (user_id, balance, method, wallet),
    )
    w_id = cursor.lastrowid
    conn.commit()
    conn.close()

    context.user_data.clear()

    await update.message.reply_text(
        "⏳ **উইথড্র রিকোয়েস্ট জমা হয়েছে!**\n\n"
        f"💰 অ্যামাউন্ট: ৳{balance:.2f}\n"
        f"📌 মাধ্যম: {method}\n"
        f"📬 নম্বর: `{wallet}`",
        parse_mode="Markdown",
    )

    admin_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ পেমেন্ট সম্পন্ন (Approve)", callback_data=f"w_approve_{w_id}_{user_id}_{balance}")],
        [InlineKeyboardButton("❌ পেমেন্ট বাতিল (Refund)", callback_data=f"w_reject_{w_id}_{user_id}_{balance}")],
    ])
    try:
      await context.bot.send_message(
          chat_id=ADMIN_ID,
          text=(
              "💸 **নতুন উইথড্র রিকোয়েস্ট এসেছে!**\n\n"
              f"👤 ইউজার: `{user_id}`\n"
              f"💰 অ্যামাউন্ট: ৳{balance:.2f}\n"
              f"📌 মাধ্যম: {method}\n"
              f"📱 নম্বর: `{wallet}`"
          ),
          parse_mode="Markdown",
          reply_markup=admin_keyboard,
      )
    except Exception:
      pass
    return

  add_user(user_id)
  user = get_user(user_id)

  # সাধারণ বাটন হ্যান্ডলিং
  if "ব্যালেন্স" in text:
    balance = user[1] if user else 0.0
    pending = user[2] if user else 0.0
    total = user[3] if user else 0.0

    balance_msg = (
        "💳 **আপনার ব্যালেন্স বিস্তারিত:**\n\n"
        f"⏳ **পেন্ডিং/প্রসেস ব্যালেন্স:** ৳{pending:.2f}\n"
        f"💵 **বর্তমান ব্যালেন্স:** ৳{balance:.2f}\n"
        f"💰 **মোট অর্জিত ব্যালেন্স:** ৳{total:.2f}\n\n"
        f"⚠️ *সর্বনিম্ন উইথড্র: ৳{MIN_WITHDRAW:.0f}*"
    )
    await update.message.reply_text(
        balance_msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 টাকা উইথড্র করুন", callback_data="request_withdraw")]]),
    )

  elif "কাজ শুরু করুন" in text:
    task_text = (
        "📧 **নতুন জিমেইল টাস্ক:**\n\n"
        "ধাপ ১: একটি নতুন জিমেইল অ্যাকাউন্ট তৈরি করুন।\n"
        "ধাপ ২: অ্যাকাউন্ট তৈরি শেষ হলে **'✅ কাজ জমা দিন'** বাটনে চাপ দিন।"
    )
    task_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ কাজ জমা দিন", callback_data="start_submit_process")],
        [InlineKeyboardButton("❌ কাজ বাতিল", callback_data="cancel_task_process")],
    ])
    await update.message.reply_text(task_text, parse_mode="Markdown", reply_markup=task_keyboard)

  elif "রেফার" in text:
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    await update.message.reply_text(
        f"👥 **রেফার লিংক:**\n`{ref_link}`\n\n"
        f"আপনার রেফার করা ইউজার ১ম সফল কাজ করলেই সরাসরি আপনার ব্যালেন্সে **৳{REFERRAL_BONUS:.0f}** বোনাস যোগ হয়ে যাবে!",
        parse_mode="Markdown",
    )

  elif "রিপোর্ট" in text:
    today = user[4] if user else 0
    total = user[5] if user else 0
    await update.message.reply_text(
        f"📊 **আপনার কাজের রিপোর্ট:**\n\n"
        f"📅 **আজকে জমা দেওয়া কাজ:** {today} টি\n"
        f"📈 **মোট জমা দেওয়া কাজ:** {total} টি",
        parse_mode="Markdown",
    )

  elif "নিয়ম" in text:
    await update.message.reply_text(
        "📜 **কাজের নিয়মাবলী ও নোটিশ:**\n\n"
        "১. সঠিকভাবে জিমেইল খুলে তথ্য জমা দিন।\n"
        "২. জিমেইল ভেরিফাই হলে টাকা সরাসরি আপনার বর্তমান ব্যালেন্সে যোগ হবে।\n"
        "৩. কোনো প্রকার ভুল তথ্য বা ফেক অ্যাকাউন্ট দিলে তা বাতিল করা হবে।",
        parse_mode="Markdown",
    )

  elif "ভিডিও" in text:
    await update.message.reply_text(
        f"🎥 **কাজ কিভাবে করবেন দেখতে নিচের লিংকে যান:**\n{WORK_VIDEO_LINK}",
        parse_mode="Markdown",
    )

  elif "হেল্পলাইন" in text:
    helpline_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 সরাসরি সাপোর্ট এডমিন", url=f"https://t.me/{HELPLINE_USERNAME}")]
    ])
    await update.message.reply_text(
        f"🆘 **যেকোনো প্রয়োজনে আমাদের এডমিন সাপোর্টে কথা বলুন:**",
        parse_mode="Markdown",
        reply_markup=helpline_keyboard
    )

# --- CALLBACK ACTIONS ---
async def main_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  user_id = query.from_user.id
  data = query.data

  if data == "request_withdraw":
    user = get_user(user_id)
    balance = user[1] if user else 0.0

    if balance < MIN_WITHDRAW:
      await query.message.reply_text(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই (কমপক্ষে ৳{MIN_WITHDRAW:.0f} প্রয়োজন)।")
      return

    method_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🩵 বিকাশ (Bkash)", callback_data="withdraw_Bkash")],
        [InlineKeyboardButton("🩷 নগদ (Nagad)", callback_data="withdraw_Nagad")],
    ])
    await query.message.reply_text("💳 পেমেন্ট নেওয়ার মাধ্যম সিলেক্ট করুন:", parse_mode="Markdown", reply_markup=method_keyboard)

  elif data.startswith("withdraw_"):
    method = data.split("_")[1]
    context.user_data["awaiting_withdraw_wallet"] = True
    context.user_data["withdraw_method"] = method
    await query.message.reply_text(f"📱 আপনার **{method}** নম্বরটি লিখে পাঠান:", parse_mode="Markdown")

  elif data == "start_submit_process":
    context.user_data["awaiting_gmail_submit"] = True
    await query.message.reply_text(
        "📥 **আপনার তৈরি করা জিমেইলটি পাঠান:**\n\n"
        "ফরম্যাট: `email:password`\n"
        "উদাহরণ: `gmailhub12@gmail.com:Pass1234`",
        parse_mode="Markdown"
    )

  elif data == "cancel_task_process":
    context.user_data.clear()
    await query.message.edit_text("❌ **আপনার কাজটি বাতিল করা হয়েছে!**", parse_mode="Markdown")

# --- ADMIN CALLBACK ACTIONS ---
async def admin_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  data = query.data

  if data.startswith("w_approve_"):
    parts = data.split("_")
    w_id, target_user_id, amount = int(parts[2]), int(parts[3]), float(parts[4])

    conn = sqlite3.connect(DB_NAME, timeout=15)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET pending_balance = pending_balance - ? WHERE user_id = ?", (amount, target_user_id))
    cursor.execute("UPDATE withdrawals SET status = 'approved' WHERE id = ?", (w_id,))
    conn.commit()
    conn.close()

    await query.message.edit_text(f"✅ ইউজার `{target_user_id}` এর ৳{amount} পেমেন্ট অ্যাপ্রুভ হয়েছে।")
    try:
      await context.bot.send_message(
          chat_id=target_user_id,
          text=f"🎉 **আপনার ৳{amount:.2f} পেমেন্টটি সফলভাবে সম্পন্ন হয়েছে!**",
          parse_mode="Markdown",
      )
    except Exception:
      pass

  elif data.startswith("w_reject_"):
    parts = data.split("_")
    w_id, target_user_id, amount = int(parts[2]), int(parts[3]), float(parts[4])

    conn = sqlite3.connect(DB_NAME, timeout=15)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET balance = balance + ?, pending_balance = pending_balance - ? WHERE user_id = ?",
        (amount, amount, target_user_id),
    )
    cursor.execute("UPDATE withdrawals SET status = 'rejected' WHERE id = ?", (w_id,))
    conn.commit()
    conn.close()

    await query.message.edit_text(f"❌ ইউজার `{target_user_id}` এর পেমেন্ট বাতিল করে টাকা ফেরত দেওয়া হয়েছে।")
    try:
      await context.bot.send_message(
          chat_id=target_user_id,
          text=f"❌ **আপনার উইথড্র বাতিল হয়েছে এবং ৳{amount:.2f} ব্যালেন্সে ফেরত এসেছে।**",
          parse_mode="Markdown",
      )
    except Exception:
      pass

def main():
  app = ApplicationBuilder().token(BOT_TOKEN).build()

  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("getused", get_used_gmails))

  app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^(check_join|show_main_menu)$"))
  app.add_handler(CallbackQueryHandler(main_callbacks, pattern="^(request_withdraw|withdraw_|start_submit_process|cancel_task_process)"))
  app.add_handler(CallbackQueryHandler(admin_action_callback, pattern="^(w_approve_|w_reject_)"))
  app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

  print("Bot is ready and running smoothly...")
  app.run_polling()

if __name__ == "__main__":
  main()
