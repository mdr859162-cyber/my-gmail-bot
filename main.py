import io
import logging
import random
import re
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

# --- YOUR CONFIGURATION DATA ---
BOT_TOKEN = "8845301572:AAHcAaiv3Hj1pCmWZ8OEbTcvfqI50tfMb3c"
ADMIN_ID = 8422485324  # আপনার অ্যাডমিন আইডি
SUPPORT_GROUP_LINK = "https://t.me/gmailhubbdsaort"
HELPLINE_USERNAME = "gmailhub_Helpline"
MIN_WITHDRAW = 10.0  # সর্বনিম্ন উইথড্র অ্যামাউন্ট

GMAIL_PRICE = 18.0  # প্রতি জিমেইলের দাম ১৮ টাকা

WORK_VIDEO_LINK = ""


# --- HIGH QUALITY REALISTIC CREDENTIALS GENERATOR ---
def generate_auto_credentials():
  # রিয়েল ও ন্যাচারাল ফার্স্ট নেম এবং লাস্ট নেম
  first_names = [
      "Ethan",
      "Oliver",
      "Lucas",
      "Mason",
      "Logan",
      "Alexander",
      "James",
      "Benjamin",
      "Henry",
      "Daniel",
      "Samuel",
      "David",
      "Joseph",
      "Carter",
      "Owen",
      "Wyatt",
      "John",
      "Jack",
      "Luke",
      "Asher",
  ]
  last_names = [
      "Smith",
      "Johnson",
      "Williams",
      "Brown",
      "Jones",
      "Garcia",
      "Miller",
      "Davis",
      "Rodriguez",
      "Martinez",
      "Hernandez",
      "Lopez",
      "Gonzalez",
      "Wilson",
      "Anderson",
      "Thomas",
      "Taylor",
      "Moore",
      "Jackson",
      "Martin",
  ]

  fn = random.choice(first_names)
  ln = random.choice(last_names)
  random_num = random.randint(1024, 9989)

  # নামের সাথে হুবহু মিল রেখে প্রফেশনাল ইউজারনেম (যেমন: ethan.smith8492@gmail.com)
  email = f"{fn.lower()}.{ln.lower()}{random_num}@gmail.com"

  # স্ট্রং ও ইউনিক পাসওয়ার্ড তৈরি (Upper + Lower + Digit + Special Char)
  upper = random.choice(string.ascii_uppercase)
  lower = "".join(random.choices(string.ascii_lowercase, k=4))
  digits = "".join(random.choices(string.digits, k=3))
  special = random.choice("@#$%&*")

  pass_list = list(upper + lower + digits + special)
  random.shuffle(pass_list)
  password = "".join(pass_list)

  return fn, ln, email, password


# --- DATABASE SETUP ---
DB_NAME = "gmail_bot_v2.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
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
            status TEXT DEFAULT 'available',
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

  try:
    cursor.execute(
        "ALTER TABLE gmail_stock ADD COLUMN used_by INTEGER DEFAULT NULL"
    )
  except sqlite3.OperationalError:
    pass

  conn.commit()
  conn.close()


init_db()


# --- HELPER FUNCTIONS ---
def get_user(user_id):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT user_id, balance, today_tasks, total_tasks, referred_by,"
      " referrals_count, is_active FROM users WHERE user_id = ?",
      (user_id,),
  )
  user = cursor.fetchone()
  conn.close()
  return user


def add_user(user_id, referred_by=None):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR IGNORE INTO users (user_id, balance, today_tasks, total_tasks,"
      " referred_by, referrals_count, is_active) VALUES (?, 0.0, 0, 0, ?, 0,"
      " 0)",
      (user_id, referred_by),
  )
  conn.commit()
  conn.close()


def get_available_gmail():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, email, password FROM gmail_stock WHERE status = 'available'"
      " LIMIT 1"
  )
  gmail = cursor.fetchone()
  conn.close()
  return gmail


def get_gmail_by_id(gmail_id):
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT email, password FROM gmail_stock WHERE id = ?", (gmail_id,)
  )
  gmail = cursor.fetchone()
  conn.close()
  return gmail


# --- HANDLERS ---


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  await update.message.reply_text(
      f"🆔 **আপনার টেলিগ্রাম আইডি হলো:** `{user_id}`", parse_mode="Markdown"
  )


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
      "💼 আমাদের বটে জিমেইল সেল দিয়ে আপনি খুব সহজেই আকর্ষণীয় ইনকাম করতে পারবেন।"
      " এটি সম্পূর্ণ বাংলাদেশ থেকে চালিত একটি বিশ্বস্ত প্ল্যাটফর্ম।\n\n"
      "⚡ **আমাদের বিশেষত্ব:**\n"
      "► ২৪ ঘণ্টা পেমেন্ট সেবা চালু থাকে 🕒\n"
      "► বাজারে আমরাই দিচ্ছি জিমেইলের সর্বোচ্চ রেট 💰\n\n"
      "👉 বটটি চালু করতে নিচের **'▶️ Start'** বাটনে ক্লিক করুন।"
  )

  keyboard = [[InlineKeyboardButton("▶️ Start", callback_data="check_join")]]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await update.message.reply_text(
      welcome_text, parse_mode="Markdown", reply_markup=reply_markup
  )


async def check_join_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  query = update.callback_query
  await query.answer()
  user_id = query.from_user.id

  menu_keyboard = [
      ["💼 কাজ শুরু করুন", "💰 ব্যালেন্স & উইথড্র"],
      ["📊 কাজের রিপোর্ট", "📜 কাজের নিয়ম"],
      ["👥 রেফার করুন", "🎥 আমি নতুন (কাজের ভিডিও)"],
      ["🆘 হেল্পলাইন"],
  ]
  reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)

  join_keyboard = InlineKeyboardMarkup([
      [InlineKeyboardButton("📢 সাপোর্ট গ্রুপে জয়েন করুন", url=SUPPORT_GROUP_LINK)],
      [
          InlineKeyboardButton(
              "✅ জয়েন সম্পন্ন করেছি", callback_data="show_main_menu"
          )
      ],
  ])

  chat_username = "@" + SUPPORT_GROUP_LINK.split("/")[-1]

  if query.data == "check_join":
    await query.message.reply_text(
        "⚠️ **বটটি ব্যবহার করার আগে দয়া করে আমাদের সাপোর্ট গ্রুপে জয়েন করুন!**\n\n"
        "জয়েন করার পর নিচের **'✅ জয়েন সম্পন্ন করেছি'** বাটনে চাপ দিন।",
        parse_mode="Markdown",
        reply_markup=join_keyboard,
    )
  elif query.data == "show_main_menu":
    try:
      member = await context.bot.get_chat_member(
          chat_id=chat_username, user_id=user_id
      )
      if member.status in ["member", "administrator", "creator"]:
        await query.message.reply_text(
            "🎉 **ধন্যবাদ আমাদের সাথে যুক্ত হওয়ার জন্য!**\n\n"
            "এখন আপনি কাজ শুরু করতে পারেন। নিচের মেনু থেকে অপশন বেছে নিন।",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
      else:
        await query.message.reply_text(
            "❌ **আপনি এখনো আমাদের সাপোর্ট গ্রুপে জয়েন করেননি!**\n\n"
            "দয়া করে আগে গ্রুপে জয়েন করুন, তারপর **'✅ জয়েন সম্পন্ন করেছি'**"
            " বাটনে চাপ দিন।",
            parse_mode="Markdown",
            reply_markup=join_keyboard,
        )
    except Exception:
      await query.message.reply_text(
          "⚠️ **ভেরিফাই করতে সমস্যা হচ্ছে!**\n\n"
          "নিশ্চিত করুন বটটিকে আপনার সাপোর্ট গ্রুপে **অ্যাডমিন (Admin)** হিসেবে"
          " যুক্ত করা আছে।",
          parse_mode="Markdown",
          reply_markup=join_keyboard,
      )


# --- ADMIN COMMANDS ---


async def clear_gmail_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  user_id = update.effective_user.id
  if user_id != ADMIN_ID:
    await update.message.reply_text("⛔ আপনার অ্যাডমিন অ্যাক্সেস নেই।")
    return

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("DELETE FROM gmail_stock")
  conn.commit()
  conn.close()

  await update.message.reply_text(
      "🗑️ **জিমেইল স্টকের সমস্ত ডাটা সফলভাবে ক্লিয়ার করা হয়েছে!**",
      parse_mode="Markdown",
  )


async def stock_status_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  user_id = update.effective_user.id
  if user_id != ADMIN_ID:
    await update.message.reply_text("⛔ আপনার অ্যাডমিন অ্যাক্সেস নেই।")
    return

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT COUNT(*) FROM gmail_stock WHERE status = 'available'"
  )
  available = cursor.fetchone()[0]

  cursor.execute(
      "SELECT COUNT(*) FROM gmail_stock WHERE status = 'used' OR status ="
      " 'approved'"
  )
  used = cursor.fetchone()[0]

  total = available + used
  conn.close()

  await update.message.reply_text(
      f"📦 **জিমেইল স্টক এর বিস্তারিত রিপোর্ট:**\n\n"
      f"🔹 **মোট আপলোড করা জিমেইল:** `{total}` টি\n"
      f"🟢 **বর্তমানে এভেলেবল (খালি):** `{available}` টি\n"
      f"🔴 **ইউজাররা কাজ করেছে (ব্যবহৃত):** `{used}` টি\n\n"
      f"💡 *ব্যবহৃত জিমেইল ডাউনলোড করতে লিখুন:* `/getused`",
      parse_mode="Markdown",
  )


async def get_used_gmails(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  if user_id != ADMIN_ID:
    await update.message.reply_text("⛔ আপনার অ্যাডমিন অ্যাক্সেস নেই।")
    return

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT email, password, used_by FROM gmail_stock WHERE status = 'used'"
      " OR status = 'approved'"
  )
  rows = cursor.fetchall()
  conn.close()

  if not rows:
    await update.message.reply_text(
        "⚠️ **কোনো ব্যবহৃত জিমেইল পাওয়া যায়নি!**"
    )
    return

  file_content = "=== USER COMPLETED GMAILS ===\n\n"
  for idx, row in enumerate(rows, 1):
    email, password, used_by = row
    file_content += (
        f"{idx}. Email: {email} | Password: {password} | User ID: {used_by}\n"
    )

  file_bytes = io.BytesIO(file_content.encode("utf-8"))
  file_bytes.name = "used_gmails.txt"

  await update.message.reply_document(
      document=file_bytes,
      caption=(
          f"📂 **ইউজারদের সম্পন্ন করা {len(rows)} টি জিমেইল এর ফাইল।**"
      ),
      parse_mode="Markdown",
  )


# --- MAIN MESSAGE HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  text = update.message.text.strip()
  user_id = update.effective_user.id

  # উইথড্র প্রসেস
  if context.user_data.get("awaiting_withdraw_wallet"):
    method = context.user_data.get("withdraw_method")
    wallet = text

    user = get_user(user_id)
    balance = user[1]

    if balance < MIN_WITHDRAW:
      await update.message.reply_text(
          f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই। সর্বনিম্ন উইথড্র"
          f" ৳{MIN_WITHDRAW}"
      )
      context.user_data.clear()
      return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE user_id = ?",
        (balance, user_id),
    )
    cursor.execute(
        "INSERT INTO withdrawals (user_id, amount, method, wallet, status)"
        " VALUES (?, ?, ?, ?, 'pending')",
        (user_id, balance, method, wallet),
    )
    w_id = cursor.lastrowid
    conn.commit()
    conn.close()

    context.user_data.clear()

    await update.message.reply_text(
        "⏳ **আপনার উইথড্র রিকোয়েস্টটি সফলভাবে জমা হয়েছে!**\n\n"
        f"💰 **অ্যামাউন্ট:** ৳{balance:.2f}\n"
        f"📌 **মাধ্যম:** {method}\n"
        f"📬 **ওয়ালেট/নম্বর:** `{wallet}`\n\n"
        "আপনার পেমেন্টটি বর্তমানে প্রসেসিং-এ আছে, ২৪ ঘণ্টার মধ্যে পেমেন্টটি পেয়ে"
        " যাবেন।",
        parse_mode="Markdown",
    )

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ পেমেন্ট সম্পন্ন (Approve)",
                callback_data=f"w_approve_{w_id}_{user_id}_{balance}",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ পেমেন্ট বাতিল (Refund)",
                callback_data=f"w_reject_{w_id}_{user_id}_{balance}",
            )
        ],
    ])
    try:
      await context.bot.send_message(
          chat_id=ADMIN_ID,
          text=(
              "💸 **নতুন উইথড্র রিকোয়েস্ট এসেছে!**\n\n"
              f"👤 **ইউজার আইডি:** `{user_id}`\n"
              f"💰 **অ্যামাউন্ট:** ৳{balance:.2f}\n"
              f"📌 **মাধ্যম:** {method}\n"
              "📱 **বিকাশ/নম্বর (কপি করতে টাচ করুন):**\n"
              f"`{wallet}`\n\n"
              "⚠️ *আগে ইউজারকে টাকা পাঠান, তারপর 'Approve' চাপুন।*"
          ),
          parse_mode="Markdown",
          reply_markup=admin_keyboard,
      )
    except Exception:
      pass
    return

  # অ্যাডমিন জিমেইল আপলোড
  if user_id == ADMIN_ID and (
      "@gmail.com" in text or text.startswith("/bulkadd")
  ):
    clean_text = re.sub(r"^/bulkadd", "", text, flags=re.IGNORECASE).strip()
    tokens = clean_text.split()

    added_count = 0
    failed_count = 0

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    i = 0
    while i < len(tokens):
      if "@" in tokens[i]:
        email = tokens[i].strip()
        if i + 1 < len(tokens) and "@" not in tokens[i + 1]:
          password = tokens[i + 1].strip()
          i += 2
        else:
          password = "NoPassword"
          i += 1

        try:
          cursor.execute(
              "INSERT INTO gmail_stock (email, password) VALUES (?, ?)",
              (email, password),
          )
          added_count += 1
        except Exception:
          failed_count += 1
      else:
        i += 1

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ **বুল্ক আপলোড সম্পন্ন হয়েছে!**\n\n"
        f"🟢 **সফলভাবে স্টকে যোগ হয়েছে:** {added_count} টি\n"
        f"⚠️ **ব্যর্থ/ভুল ফরম্যাট:** {failed_count} টি",
        parse_mode="Markdown",
    )
    return

  # ইউজার মেনু
  add_user(user_id)
  user = get_user(user_id)

  if "ব্যালেন্স & উইথড্র" in text or "ব্যালেন্স" in text:
    balance = user[1]
    today_tasks = user[2]
    total_tasks = user[3]

    balance_text = (
        "💳 **আপনার অ্যাকাউন্ট ব্যালেন্স বিবরণী:**\n\n"
        f"🔹 **বর্তমান ব্যালেন্স:** ৳{balance:.2f}\n"
        f"🔹 **আজকের জমা দেওয়া কাজ:** {today_tasks} টি\n"
        f"🔹 **সর্বমোট সফল কাজ:** {total_tasks} টি\n\n"
        f"⚠️ *সর্বনিম্ন উইথড্র অ্যামাউন্ট: ৳{MIN_WITHDRAW}*"
    )

    withdraw_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "💸 টাকা উইথড্র করুন", callback_data="request_withdraw"
        )
    ]])
    await update.message.reply_text(
        balance_text, parse_mode="Markdown", reply_markup=withdraw_keyboard
    )

  elif "কাজ শুরু করুন" in text:
    gmail = get_available_gmail()

    if gmail:
      gmail_id, email, password = gmail
      fn = email.split(".")[0].capitalize() if "." in email else "John"
      ln = "Smith"
    else:
      fn, ln, auto_email, auto_pass = generate_auto_credentials()
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO gmail_stock (email, password) VALUES (?, ?)",
          (auto_email, auto_pass),
      )
      gmail_id = cursor.lastrowid
      conn.commit()
      conn.close()
      email, password = auto_email, auto_pass

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE gmail_stock SET status = 'used', used_by = ? WHERE id = ?",
        (user_id, gmail_id),
    )
    conn.commit()
    conn.close()

    task_text = (
        "📧 **নতুন জিমেইল টাস্ক (প্রফেশনাল ফরম্যাট):**\n\n"
        f"👤 **First Name:** `{fn}`\n"
        f"👤 **Last Name:** `{ln}`\n"
        f"🔹 **User Name:** `{email}`\n"
        f"🔑 **Password:** `{password}`\n\n"
        "👉 *প্রতিটি তথ্যের ওপর টাচ করলেই তা সাথে সাথে কপি হয়ে যাবে।*\n\n"
        "ধাপ ১: জিমেইল অ্যাপ/ব্রাউজারে গিয়ে First & Last Name এবং এই ইমেইল-পাসওয়ার্ড দিয়ে অ্যাকাউন্ট তৈরি করুন।\n"
        "ধাপ ২: কাজ শেষ হলে নিচে **'✅ কাজ জমা দিন'** বাটনে চাপ দিন।"
    )
    task_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ কাজ জমা দিন", callback_data=f"submit_task_{gmail_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ কাজ বাতিল", callback_data=f"cancel_task_{gmail_id}"
            )
        ],
    ])
    await update.message.reply_text(
        task_text, parse_mode="Markdown", reply_markup=task_keyboard
    )

  elif "কাজের রিপোর্ট" in text:
    today_tasks = user[2]
    total_tasks = user[3]
    report_text = (
        "📊 **আপনার কাজের নিখুঁত রিপোর্ট:**\n\n"
        f"📅 **আজকের মোট কাজ:** {today_tasks} টি\n"
        f"📈 **সর্বমোট কাজ:** {total_tasks} টি\n\n"
        "✨ *সঠিকভাবে কাজ করতে থাকুন এবং প্রতিদিন বেশি বেশি ইনকাম করুন!*"
    )
    await update.message.reply_text(report_text, parse_mode="Markdown")

  elif "কাজের নিয়ম" in text:
    rules_text = (
        "📜 **জিমেইল ক্রিয়েট করার নিয়মাবলী:**\n\n"
        "১. দয়া করে বট থেকে দেওয়া First Name, Last Name, জিমেইল এবং পাসওয়ার্ড নিয়ে সঠিক নিয়মে জিমেইল একাউন্ট ক্রিয়েট করুন।\n\n"
        "⚠️ **বিশেষ নোটিশ (অবশ্যই পালনীয়):**\n"
        "📌 **জিমেইল খোলার পরই ফোন থেকে অ্যাকাউন্টটি Log Out / Remove করে"
        " দিবেন।** অন্যথায় পেমент পাবেন না।\n"
        "🚫 কোনো প্রকার প্রতারণামূলক কাজ করলে আইডি ব্যান করা হবে।"
    )
    await update.message.reply_text(rules_text, parse_mode="Markdown")

  elif "রেফার করুন" in text:
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    ref_text = (
        "👥 **রেফার করে ইনকাম করুন!**\n\n"
        "আপনার রেফারেল লিংকের মাধ্যমে বন্ধুকে ইনভাইট করুন। আপনার রেফারে আইডি"
        " এক্টিভ হলে পাবেন **১০ টাকা** বোনাস!\n\n"
        f"🔗 **আপনার রেফার লিংক:**\n`{ref_link}`"
    )
    await update.message.reply_text(ref_text, parse_mode="Markdown")

  elif "আমি নতুন" in text:
    if WORK_VIDEO_LINK.strip():
      video_keyboard = InlineKeyboardMarkup([[
          InlineKeyboardButton(
              "▶️ ভিডিওটি দেখতে এখানে ক্লিক করুন", url=WORK_VIDEO_LINK
          )
      ]])
      await update.message.reply_text(
          "🎥 **আপনি কি কাজে নতুন?**\n\nনিচের লিংকে ক্লিক করে কাজের ভিডিও দেখে নিন:",
          parse_mode="Markdown",
          reply_markup=video_keyboard,
      )
    else:
      await update.message.reply_text(
          "🎥 **খুব শীঘ্রই কাজের ভিডিও আসছে!**\n\nভিডিও আপলোড হওয়া মাত্রই"
          " আপনারা এখানে দেখতে পাবেন। আপাতত নিয়ম পড়ে কাজ চালু রাখুন।",
          parse_mode="Markdown",
      )

  elif "হেল্পলাইন" in text:
    help_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "💬 এডমিন সাপোর্ট", url=f"https://t.me/{HELPLINE_USERNAME}"
        )
    ]])
    help_text = (
        "🆘 **এডমিন হেল্পলাইন:**\n\n"
        "যে কোনো প্রয়োজনে বা সমস্যার কারণে আমাদের এডমিনের সঙ্গে যোগাযোগ"
        " করুন।\n\n"
        "⚠️ **বিশেষ নোটিশ:** অযথা কেউ মেসেজ দিবেন না।"
    )
    await update.message.reply_text(
        help_text, parse_mode="Markdown", reply_markup=help_keyboard
    )


# --- CALLBACKS & WITHDRAW SYSTEM ---
async def main_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  user_id = query.from_user.id
  data = query.data

  if data == "request_withdraw":
    user = get_user(user_id)
    balance = user[1]

    if balance < MIN_WITHDRAW:
      await query.message.reply_text(
          f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই। উইথড্র করতে কমপক্ষে"
          f" **৳{MIN_WITHDRAW}** প্রয়োজন। আপনার বর্তমান ব্যালেন্স: ৳{balance:.2f}"
      )
      return

    method_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🩵 বিকাশ (Bkash)", callback_data="withdraw_Bkash"
            )
        ],
        [InlineKeyboardButton("🩷 নগদ (Nagad)", callback_data="withdraw_Nagad")],
        [
            InlineKeyboardButton(
                "💲 USDT (BEP20)", callback_data="withdraw_USDT"
            )
        ],
    ])
    await query.message.reply_text(
        f"💳 **আপনার বর্তমান ব্যালেন্স: ৳{balance:.2f}**\n\nপেমেন্ট নেওয়ার জন্য নিচের"
        " যেকোনো একটি মাধ্যম সিলেক্ট করুন:",
        parse_mode="Markdown",
        reply_markup=method_keyboard,
    )

  elif data.startswith("withdraw_"):
    method = data.split("_")[1]
    context.user_data["awaiting_withdraw_wallet"] = True
    context.user_data["withdraw_method"] = method

    prompt_text = (
        f"📱 আপনার **{method}** নম্বরটি বা ওয়ালেট অ্যাড্রেসটি লিখে পাঠান:"
    )
    if method == "USDT":
      prompt_text = "🌐 আপনার **USDT (BEP20)** ওয়ালেট অ্যাড্রেসটি লিখে পাঠান:"

    await query.message.reply_text(prompt_text, parse_mode="Markdown")

  elif data.startswith("submit_task_"):
    gmail_id = data.split("_")[2]
    gmail_info = get_gmail_by_id(gmail_id)

    await query.message.edit_text(
        "📥 **আপনার কাজ সফলভাবে জমা হয়েছে!**\n\n"
        f"আপনার জিমেইলের **{int(GMAIL_PRICE)} টাকা** ২৪ ঘন্টার মধ্যে পেয়ে যাবেন"
        " এবং জিমেইলটি বর্তমানে প্রসেসিং এ দেওয়া হয়েছে।",
        parse_mode="Markdown",
    )

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"✅ কাজ অ্যাপ্রুভ ({int(GMAIL_PRICE)} টাকা যোগ)",
                callback_data=f"approve_{user_id}_{gmail_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ বাতিল করুন", callback_data=f"reject_{user_id}_{gmail_id}"
            )
        ],
    ])

    if gmail_info:
      email, password = gmail_info
      admin_msg = (
          "📥 **নতুন টাস্ক জমা পড়েছে!**\n\n"
          f"👤 **ইউজার আইডি:** `{user_id}`\n\n"
          "🔍 **চেক করার জন্য তথ্য (কপি করতে টাচ করুন):**\n"
          f"📧 **ইমেইল:**\n`{email}`\n"
          f"🔑 **পাসওয়ার্ড:**\n`{password}`\n\n"
          "⚠️ *আগে ফায়ারফক্স ফোকাস ব্রাউজারে সাইন-ইন করে চেক করুন। ঠিক থাকলে"
          " অ্যাপ্রুভ করুন।*"
      )
    else:
      admin_msg = (
          "📥 **নতুন টাস্ক জমা পড়েছে!**\n\n**ইউজার আইডি:**"
          f" `{user_id}`\n**জিমেইল আইডি:** `{gmail_id}`"
      )

    try:
      await context.bot.send_message(
          chat_id=ADMIN_ID,
          text=admin_msg,
          parse_mode="Markdown",
          reply_markup=admin_keyboard,
      )
    except Exception:
      pass

  elif data.startswith("cancel_task_"):
    gmail_id = data.split("_")[2]
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE gmail_stock SET status = 'available', used_by = NULL WHERE id ="
        " ?",
        (gmail_id,),
    )
    conn.commit()
    conn.close()
    await query.message.edit_text(
        "❌ **আপনার কাজটি বাতিল করা হয়েছে!**", parse_mode="Markdown"
    )


# --- ADMIN ACTIONS ---
async def admin_action_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  query = update.callback_query
  await query.answer()
  data = query.data

  if data.startswith("approve_"):
    parts = data.split("_")
    target_user_id = int(parts[1])
    gmail_id = int(parts[2])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE gmail_stock SET status = 'approved' WHERE id = ?", (gmail_id,)
    )
    cursor.execute(
        "SELECT referred_by, is_active FROM users WHERE user_id = ?",
        (target_user_id,),
    )
    res = cursor.fetchone()

    cursor.execute(
        "UPDATE users SET balance = balance + ?, today_tasks = today_tasks +"
        " 1, total_tasks = total_tasks + 1 WHERE user_id = ?",
        (GMAIL_PRICE, target_user_id),
    )

    if res and res[0] and res[1] == 0:
      referred_by = res[0]
      cursor.execute(
          "UPDATE users SET is_active = 1 WHERE user_id = ?", (target_user_id,)
      )
      cursor.execute(
          "UPDATE users SET balance = balance + 10, referrals_count ="
          " referrals_count + 1 WHERE user_id = ?",
          (referred_by,),
      )
      try:
        await context.bot.send_message(
            chat_id=referred_by,
            text=(
                "🎉 **আপনার রেফারকৃত ইউজার কাজ শেষ করায় আপনার একাউন্টে ১০ টাকা"
                " কমিশন যোগ হয়েছে!**"
            ),
            parse_mode="Markdown",
        )
      except Exception:
        pass

    conn.commit()
    conn.close()

    await query.message.edit_text(
        f"✅ User `{target_user_id}` এর কাজ সফলভাবে অ্যাপ্রুভ করা হয়েছে এবং"
        f" {int(GMAIL_PRICE)} টাকা ব্যালেন্সে যোগ হয়েছে।"
    )
    try:
      await context.bot.send_message(
          chat_id=target_user_id,
          text=(
              "🎉 **আপনার জমা দেওয়া জিমেইলটি অ্যাপ্রুভ করা হয়েছে!**\nআপনার"
              f" ব্যালেন্সে {int(GMAIL_PRICE)} টাকা যোগ করা হয়েছে।"
          ),
          parse_mode="Markdown",
      )
    except Exception:
      pass

  elif data.startswith("reject_"):
    parts = data.split("_")
    target_user_id = int(parts[1])
    gmail_id = int(parts[2])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE gmail_stock SET status = 'available', used_by = NULL WHERE id ="
        " ?",
        (gmail_id,),
    )
    conn.commit()
    conn.close()

    await query.message.edit_text(
        f"❌ User `{target_user_id}` এর কাজ রিজেক্ট করা হয়েছে।"
    )
    try:
      await context.bot.send_message(
          chat_id=target_user_id,
          text="❌ **আপনার জমা দেওয়া কাজটি বাতিল করা হয়েছে।**",
          parse_mode="Markdown",
      )
    except Exception:
      pass

  elif data.startswith("w_approve_"):
    parts = data.split("_")
    target_user_id = int(parts[3])
    amount = float(parts[4])

    await query.message.edit_text(
        f"✅ ইউজার `{target_user_id}` এর ৳{amount} পেমেন্ট অ্যাপ্রুভ করা হয়েছে।"
    )
    try:
      payment_success_msg = (
          "🎉 **আপনার পেমেন্টটি করা হয়েছে!**\n\n"
          f"💰 **অ্যামাউন্ট:** ৳{amount:.2f}\n\n"
          "🙏 *পেমেন্টটি করতে কিছুটা দেরি করার জন্য আমরা আন্তরিকভাবে দুঃখিত।"
          " আমাদের সাথে থাকার জন্য আপনাকে ধন্যবাদ!*"
      )
      await context.bot.send_message(
          chat_id=target_user_id,
          text=payment_success_msg,
          parse_mode="Markdown",
      )
    except Exception:
      pass

  elif data.startswith("w_reject_"):
    parts = data.split("_")
    target_user_id = int(parts[3])
    amount = float(parts[4])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, target_user_id),
    )
    conn.commit()
    conn.close()

    await query.message.edit_text(
        f"❌ ইউজার `{target_user_id}` এর উইথড্র রিজেক্ট করা হয়েছে এবং ব্যালেন্স"
        " রিফান্ড করা হয়েছে।"
    )
    try:
      await context.bot.send_message(
          chat_id=target_user_id,
          text=(
              f"❌ **আপনার উইথড্র রিকোয়েস্টটি বাতিল করা হয়েছে এবং ৳{amount:.2f}"
              " আপনার ব্যালেন্সে ফিরিয়ে দেওয়া হয়েছে।**"
          ),
          parse_mode="Markdown",
      )
    except Exception:
      pass


# --- MAIN FUNCTION ---
def main():
  app = ApplicationBuilder().token(BOT_TOKEN).build()

  # Commands
  app.add_handler(CommandHandler("myid", myid_command))
  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("cleargmail", clear_gmail_command))
  app.add_handler(CommandHandler("stock", stock_status_command))
  app.add_handler(CommandHandler("getused", get_used_gmails))

  # Callbacks & Messages
  app.add_handler(
      CallbackQueryHandler(
          check_join_callback, pattern="^(check_join|show_main_menu)$"
      )
  )
  app.add_handler(
      CallbackQueryHandler(
          main_callbacks,
          pattern="^(request_withdraw|withdraw_|submit_task_|cancel_task_)",
      )
  )
  app.add_handler(
      CallbackQueryHandler(
          admin_action_callback, pattern="^(approve_|reject_|w_approve_|w_reject_)"
      )
  )
  app.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )

  print("Bot is successfully running...")
  app.run_polling()


if __name__ == "__main__":
  main()
