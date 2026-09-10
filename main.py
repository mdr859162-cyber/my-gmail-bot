import asyncio
import io
import json
import logging
import random
import sqlite3
import string
import urllib.parse
import urllib.request
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
BOT_TOKEN = "8845301572:AAEtl_D_p65aIWLeUVeFwLMsVJ_3Utlss58"      # আপনার বটের টোকেন দিন
ADMIN_ID = 8422485324                  # আপনার এডমিন আইডি
CHANNEL_USERNAME = "@gmailhubsaport"   # টেলিগ্রাম চ্যানেলের ইউজারনেম
SUPPORT_GROUP_LINK = "https://t.me/gmailhubsaport"
HELPLINE_USERNAME = "gmailhub_Helpline"

MIN_WITHDRAW = 100.0
GMAIL_PRICE = 18.0
REFERRAL_BONUS = 10.0
WORK_VIDEO_LINK = "https://t.me/gmailhubsaport/3"
MAX_FAKE_ATTEMPTS = 5

# --- DATABASE SETUP ---
DB_NAME = "gmail_bot_v5.db"

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
            referral_income REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 0,
            fake_attempts INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gmail_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            password TEXT,
            status TEXT DEFAULT 'pending',
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
        "SELECT user_id, balance, pending_balance, total_earned, today_tasks, total_tasks, referred_by, referrals_count, referral_income, is_active, fake_attempts FROM users WHERE user_id = ?",
        (user_id,),
    )
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(user_id, referred_by=None):
    conn = sqlite3.connect(DB_NAME, timeout=15)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, balance, pending_balance, total_earned, today_tasks, total_tasks, referred_by, referrals_count, referral_income, is_active, fake_attempts) VALUES (?, 0.0, 0.0, 0.0, 0, 0, ?, 0, 0.0, 0, 0)",
        (user_id, referred_by),
    )
    conn.commit()
    conn.close()

def generate_auto_credentials():
    first_names = ["Ethan", "Oliver", "Lucas", "Mason", "Logan", "Alexander", "James", "Benjamin", "Henry", "Daniel"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

    fn = random.choice(first_names)
    ln = random.choice(last_names)
    random_num = random.randint(1024, 9989)

    email = f"{fn.lower()}.{ln.lower()}{random_num}@gmail.com"

    upper = random.choice(string.ascii_uppercase)
    lower = "".join(random.choices(string.ascii_lowercase, k=4))
    digits = "".join(random.choices(string.digits, k=3))
    special = random.choice("@#$%&*")

    pass_list = list(upper + lower + digits + special)
    random.shuffle(pass_list)
    password = "".join(pass_list)

    return fn, ln, email, password

def get_gmail_by_id(gmail_id):
    conn = sqlite3.connect(DB_NAME, timeout=15)
    cursor = conn.cursor()
    cursor.execute("SELECT email, password, used_by FROM gmail_stock WHERE id = ?", (gmail_id,))
    gmail = cursor.fetchone()
    conn.close()
    return gmail

async def is_user_joined(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return False

def check_gmail_exists(email):
    try:
        url = "https://accounts.google.com/_/signin/v2/lookup"
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
        data = urllib.parse.urlencode({'f.req': json.dumps([email])}).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as response:
            res_text = response.read().decode('utf-8')
            if "NOT_FOUND" in res_text or "IdentifierNotFound" in res_text:
                return False
            return True
    except Exception:
        return False

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
        "✨ **আসসালামু আলাইকুম! GMAILHUB বটে আপনাকে স্বাগতম** 🌟\n\n"
        "💼 আমাদের বটে জিমেইল সেল দিয়ে আপনি খুব সহজেই প্রতিদিন চমৎকার ইনকাম করতে পারবেন।"
        " এটি একটি ১০০% অটোমেটেড ও বিশ্বাসযোগ্য প্ল্যাটফর্ম।\n\n"
        "👉 কাজ শুরু করতে নিচের **'▶️ Start'** বাটনে ক্লিক করুন! 🚀"
    )

    keyboard = [[InlineKeyboardButton("▶️ Start 🚀", callback_data="check_join")]]
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    menu_keyboard = [
        ["💼 কাজ শুরু করুন 🚀", "💰 ব্যালেন্স & উইথড্র 💳"],
        ["📊 কাজের রিপোর্ট 📈", "📜 কাজের নিয়ম ⚠️"],
        ["👥 রেফার করুন 🎁", "🎥 আমি নতুন (কাজের ভিডিও) 🎬"],
        ["🆘 হেল্পলাইন 📞"],
    ]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)

    join_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 আমাদের চ্যানেলে জয়েন হন 🚀", url=SUPPORT_GROUP_LINK)],
        [InlineKeyboardButton("✅ জয়েন সম্পন্ন করেছি ⚡", callback_data="show_main_menu")],
    ])

    if query.data == "check_join":
        await query.message.reply_text(
            "⚠️ **বটটি ব্যবহার করার আগে বাধ্যতামূলক আমাদের অফিশিয়াল চ্যানেলে যুক্ত হতে হবে!** 📢",
            parse_mode="Markdown",
            reply_markup=join_keyboard,
        )
    elif query.data == "show_main_menu":
        joined = await is_user_joined(user_id, context)
        if joined:
            await query.message.reply_text(
                "🎉 **স্বাগতম!** আপনার জয়েনিং সফল হয়েছে। নিচের মেনু থেকে আপনার কাঙ্ক্ষিত অপশনটি বেছে নিন। 👇",
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
        else:
            await query.message.reply_text(
                "❌ **আপনি এখনো চ্যানেলে জয়েন করেননি!**\n\nদয়া করে আগে চ্যানেলে জয়েন হয়ে তারপর '✅ জয়েন সম্পন্ন করেছি' বাটনে ক্লিক করুন। 🛑",
                parse_mode="Markdown",
                reply_markup=join_keyboard,
            )

# --- ADMIN COMMANDS ---
async def check_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    conn = sqlite3.connect(DB_NAME, timeout=15)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM gmail_stock WHERE status = 'approved'")
    approved_count = cursor.fetchone()[0]
    conn.close()

    msg = (
        "📊 **এডমিন জিমেইল স্টক রিপোর্ট:**\n\n"
        f"✅ **ডাউনলোড করার জন্য ফ্রেস জিমেইল জমা আছে:** `{approved_count}` টি 📦\n\n"
        "💡 *ডাউনলোড ও স্টক খালি করতে `/getused` কমান্ড দিন।*"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

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
        await update.message.reply_text("⚠️ **ডাউনলোড করার মতো কোনো নতুন জিমেইল স্টকে নেই!** 📭")
        return

    file_content = "=== APPROVED FRESH GMAILS ===\n\n"
    downloaded_ids = []

    for idx, row in enumerate(rows, 1):
        g_id, email, password, target_user_id = row
        file_content += f"{idx}. Email: {email} | Password: {password} | User ID: {target_user_id}\n"
        downloaded_ids.append(g_id)

    file_bytes = io.BytesIO(file_content.encode("utf-8"))
    file_bytes.name = f"fresh_gmails_{len(rows)}.txt"

    await update.message.reply_document(
        document=file_bytes,
        caption=f"📂 **মোট {len(rows)} টি ভেরিফাইড জিমেইল ফাইল আকারে পাঠানো হলো।** ✨\n\n🔥 স্টক থেকে এই ফাইলগুলো রিমুভ করা হয়েছে!",
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

    joined = await is_user_joined(user_id, context)
    if not joined and user_id != ADMIN_ID:
        join_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 আমাদের চ্যানেলে জয়েন হন 🚀", url=SUPPORT_GROUP_LINK)],
            [InlineKeyboardButton("✅ জয়েন সম্পন্ন করেছি ⚡", callback_data="show_main_menu")],
        ])
        await update.message.reply_text(
            "⚠️ **বটটি ব্যবহার করার আগে আপনাকে অবশ্যই আমাদের অফিশিয়াল চ্যানেলে জয়েন হতে হবে!** 🛑",
            parse_mode="Markdown",
            reply_markup=join_keyboard,
        )
        return

    if context.user_data.get("awaiting_withdraw_wallet"):
        method = context.user_data.get("withdraw_method")
        wallet = text
        user = get_user(user_id)
        balance = user[1] if user else 0.0

        if balance < MIN_WITHDRAW:
            await update.message.reply_text(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই। সর্বনিম্ন উইথড্র ৳{MIN_WITHDRAW:.0f} 🛑")
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
            "⏳ **আপনার উইথড্র রিকোয়েস্টটি সফলভাবে জমা হয়েছে!** 📩\n\n"
            f"💰 অ্যামাউন্ট: **৳{balance:.2f}**\n"
            f"📌 পেমেন্ট মাধ্যম: **{method}**\n"
            f"📱 প্রাপ্তির নম্বর: `{wallet}`\n\n"
            "👨‍💻 এডমিন দ্রুত আপনার নম্বরটি ভেরিফাই করে পেমেন্ট সম্পন্ন করে দেবেন।",
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
                    "💸 **নতুন উইথড্র রিকোয়েস্ট এসেছে!** 🔔\n\n"
                    f"👤 ইউজার আইডি: `{user_id}`\n"
                    f"💰 অ্যামাউন্ট: **৳{balance:.2f}**\n"
                    f"📌 মাধ্যম: **{method}**\n"
                    f"📱 ওয়ালেট নম্বর: `{wallet}`"
                ),
                parse_mode="Markdown",
                reply_markup=admin_keyboard,
            )
        except Exception:
            pass
        return

    add_user(user_id)
    user = get_user(user_id)

    if text == "💰 ব্যালেন্স & উইথড্র 💳":
        balance = user[1] if user else 0.0
        pending = user[2] if user else 0.0
        total = user[3] if user else 0.0

        balance_msg = (
            "💳 **আপনার ব্যালেন্স বিস্তারিত:** 📊\n\n"
            f"⏳ **পেন্ডিং/প্রসেস ব্যালেন্স:** ৳{pending:.2f}\n"
            f"💵 **বর্তমান মূল ব্যালেন্স:** ৳{balance:.2f}\n"
            f"💰 **সর্বমোট অর্জিত ইনকাম:** ৳{total:.2f}\n\n"
            f"⚠️ *সর্বনিম্ন উইথড্র সীমা: ৳{MIN_WITHDRAW:.0f}*"
        )
        await update.message.reply_text(
            balance_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 টাকা উইথড্র করুন 🏦", callback_data="request_withdraw")]]),
        )

    elif text == "💼 কাজ শুরু করুন 🚀":
        fn, ln, auto_email, auto_pass = generate_auto_credentials()
        conn = sqlite3.connect(DB_NAME, timeout=15)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO gmail_stock (email, password, status, used_by) VALUES (?, ?, 'pending', ?)", (auto_email, auto_pass, user_id))
        gmail_id = cursor.lastrowid
        conn.commit()
        conn.close()

        task_text = (
            "📧 **নতুন জিমেইল টাস্ক:** 🎯\n\n"
            f"👤 **First Name:** `{fn}`\n"
            f"👤 **Last Name:** `{ln}`\n"
            f"🔹 **User Name:** `{auto_email}`\n"
            f"🔑 **Password:** `{auto_pass}`\n\n"
            "👉 উপরের তথ্যগুলো দিয়ে জিমেইল তৈরি করুন এবং কাজ শেষ হলে **'✅ কাজ জমা দিন'** বাটনে চাপ দিন।"
        )
        task_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ কাজ জমা দিন 📥", callback_data=f"submit_task_{gmail_id}")],
            [InlineKeyboardButton("❌ কাজ বাতিল 🛑", callback_data=f"cancel_task_{gmail_id}")],
        ])
        await update.message.reply_text(task_text, parse_mode="Markdown", reply_markup=task_keyboard)

    elif text == "👥 রেফার করুন 🎁":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        ref_count = user[7] if user else 0
        ref_income = user[8] if user else 0.0

        ref_msg = (
            "👥 **আপনার রেফারেল লিংক ব্যবহার করে বন্ধুদের ইনভাইট করুন!** ✨\n\n"
            f"🔗 **রেফারেল লিংক:**\n`{ref_link}`\n\n"
            "🎁 **রেফারেল বোনাস অফার:**\n"
            f"আপনার রেফারেল লিংক ব্যবহার করে কেউ জয়েন করার পর, তার **প্রথম জিমেইলটি সফলভাবে অ্যাপ্রুভ হলেই** আপনি পেয়ে যাবেন **৳{REFERRAL_BONUS:.0f}.০০** ইনস্ট্যান্ট বোনাস! 💰\n\n"
            "📊 **আপনার রেফারেল পরিসংখ্যান (লাইভ):**\n"
            f"👥 **মোট রেফার করেছেন:** `{ref_count}` জন\n"
            f"💵 **রেফার থেকে মোট ইনকাম:** `৳{ref_income:.2f}`"
        )
        await update.message.reply_text(ref_msg, parse_mode="Markdown")

    elif text == "📊 কাজের রিপোর্ট 📈":
        today = user[4] if user else 0
        total = user[5] if user else 0
        await update.message.reply_text(
            f"📊 **আপনার কাজের পারফরম্যান্স রিপোর্ট:** 📈\n\n"
            f"📅 **আজকে সফলভাবে জমা হওয়া কাজ:** {today} টি 🎯\n"
            f"📈 **মোট সফলভাবে জমা দেওয়া কাজ:** {total} টি 🏆",
            parse_mode="Markdown",
        )

    elif text == "📜 কাজের নিয়ম ⚠️":
        rule_msg = (
            "📜 **কাজের নিয়মাবলী ও নির্দেশিকা:** ⚠️\n\n"
            "১. **দয়া করে বট থেকে সঠিক জিমেইল এবং পাসওয়ার্ড নিয়ে জিমেইল খুলে সঠিক নিয়মে জমা দিন।** 📧\n"
            "২. কাজ না করে ভুয়া/ফেক সাবমিট করার চেষ্টা করলে বটের অটোমেটিক সিস্টেমে ওয়ার্নিং যোগ হবে। 🚨\n"
            "৩. বারবার ভুয়া কাজ জমা দেওয়ার চেষ্টা করলে আপনার একাউন্ট স্থায়ীভাবে স্থগিত (Block) করা হবে। 🛑"
        )
        await update.message.reply_text(rule_msg, parse_mode="Markdown")

    elif text == "🎥 আমি নতুন (কাজের ভিডিও) 🎬":
        await update.message.reply_text(
            f"🎥 **সহজে কাজ শেখার নির্দেশিকা ভিডিও:** 🎬\n{WORK_VIDEO_LINK}",
            parse_mode="Markdown",
        )

    elif text == "🆘 হেল্পলাইন 📞":
        helpline_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 সরাসরি সাপোর্ট এডমিন 👨‍💻", url=f"https://t.me/{HELPLINE_USERNAME}")]
        ])
        await update.message.reply_text(
            "🆘 **যেকোনো প্রয়োজনে বা তথ্যের জন্য আমাদের এডমিনের সাথে যোগাযোগ করুন:** 📞",
            parse_mode="Markdown",
            reply_markup=helpline_keyboard,
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
            await query.message.reply_text(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই (কমপক্ষে ৳{MIN_WITHDRAW:.0f} প্রয়োজন)। 🛑")
            return

        method_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🩵 বিকাশ (Bkash)", callback_data="withdraw_Bkash")],
            [InlineKeyboardButton("🩷 নগদ (Nagad)", callback_data="withdraw_Nagad")],
        ])
        await query.message.reply_text("💳 **টাকা নেওয়ার মাধ্যম নির্বাচন করুন:** 🏦", parse_mode="Markdown", reply_markup=method_keyboard)

    elif data.startswith("withdraw_"):
        method = data.split("_")[1]
        context.user_data["awaiting_withdraw_wallet"] = True
        context.user_data["withdraw_method"] = method
        await query.message.reply_text(f"📱 আপনার **{method}** নম্বরটি লিখে আমাদের মেসেজ পাঠাও:", parse_mode="Markdown")

    elif data.startswith("submit_task_"):
        gmail_id = data.split("_")[2]
        gmail_info = get_gmail_by_id(gmail_id)

        if not gmail_info:
            await query.message.edit_text("⚠️ কাজের তথ্য পাওয়া যায়নি!")
            return

        email, password, _ = gmail_info

        await query.message.edit_text("⏳ **আপনার জিমেইলটি ভেরিফাই করা হচ্ছে, অনুগ্রহ করে ৫ সেকেন্ড অপেক্ষা করুন...** 🔍", parse_mode="Markdown")
        await asyncio.sleep(4)

        is_valid = check_gmail_exists(email)

        conn = sqlite3.connect(DB_NAME, timeout=15)
        cursor = conn.cursor()

        if is_valid:
            cursor.execute("UPDATE gmail_stock SET status = 'approved' WHERE id = ?", (gmail_id,))
            cursor.execute(
                "UPDATE users SET balance = balance + ?, total_earned = total_earned + ?, today_tasks = today_tasks + 1, total_tasks = total_tasks + 1 WHERE user_id = ?",
                (GMAIL_PRICE, GMAIL_PRICE, user_id),
            )

            cursor.execute("SELECT referred_by, is_active FROM users WHERE user_id = ?", (user_id,))
            user_info = cursor.fetchone()

            if user_info and user_info[0] and user_info[1] == 0:
                referred_by = user_info[0]
                cursor.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
                cursor.execute(
                    "UPDATE users SET balance = balance + ?, total_earned = total_earned + ?, referrals_count = referrals_count + 1, referral_income = referral_income + ? WHERE user_id = ?",
                    (REFERRAL_BONUS, REFERRAL_BONUS, REFERRAL_BONUS, referred_by),
                )
                try:
                    await context.bot.send_message(
                        chat_id=referred_by,
                        text=f"🎉 **রেফার বোনাস অর্জিত হয়েছে!** 🎁\n\nআপনার রেফার করা সদস্য ১ম কাজ সফলভাবে অ্যাপ্রুভ করায় আপনার ব্যালেন্সে **৳{REFERRAL_BONUS:.0f}.০০** বোনাস যোগ হয়েছে! 💰",
                        parse_mode="Markdown",
                    )
                except Exception:
                    pass

            conn.commit()
            conn.close()

            await query.message.edit_text(
                "✅ **আপনার জিমেইলটি সফলভাবে ভেরিফাইড এবং জমা নেওয়া হয়েছে!** 🎉\n\n"
                f"💰 আপনার মূল ব্যালেন্সে **৳{int(GMAIL_PRICE)}.০০** টাকা যোগ করা হয়েছে।",
                parse_mode="Markdown",
            )

        else:
            cursor.execute("DELETE FROM gmail_stock WHERE id = ?", (gmail_id,))
            cursor.execute("UPDATE users SET fake_attempts = fake_attempts + 1 WHERE user_id = ?", (user_id,))
            cursor.execute("SELECT fake_attempts FROM users WHERE user_id = ?", (user_id,))
            attempts = cursor.fetchone()[0]
            conn.commit()
            conn.close()

            warning_msg = ""
            if attempts >= MAX_FAKE_ATTEMPTS:
                warning_msg = (
                    "\n\n🚨 **কঠোর সতর্কতা:** 🛑\n"
                    f"আপনি বারবার ({attempts} বার) কাজ না করে জমা দেওয়ার চেষ্টা করছেন!\n"
                    "⚠️ *সঠিক নিয়ম না মানলে আপনার আইডি থেকে পেমেন্ট তোলা বন্ধ হয়ে যাবে।*"
                )

            await query.message.edit_text(
                "❌ **জিমেইলটি তৈরি করা হয়নি!** 🛑\n\n"
                "দয়া করে বট থেকে দেওয়া তথ্য অনুযায়ী সঠিকভাবে জিমেইল তৈরি করে তারপর জমা দিন।"
                f"{warning_msg}",
                parse_mode="Markdown"
            )

    elif data.startswith("cancel_task_"):
        gmail_id = data.split("_")[2]
        conn = sqlite3.connect(DB_NAME, timeout=15)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gmail_stock WHERE id = ?", (gmail_id,))
        conn.commit()
        conn.close()
        await query.message.edit_text("❌ **আপনার কাজটি বাতিল করা হয়েছে!** 🛑", parse_mode="Markdown")

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

        await query.message.edit_text(f"✅ ইউজার `{target_user_id}` এর ৳{amount} পেমেন্ট অ্যাপ্রুভ করা হয়েছে। 🎉")
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 **আপনার ৳{amount:.2f} টাকা পেমেন্ট সফলভাবে সম্পন্ন হয়েছে!** 💸\nআমাদের সার্ভিস ব্যবহারের জন্য ধন্যবাদ।",
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

        await query.message.edit_text(f"❌ ইউজার `{target_user_id}` এর পেমেন্ট বাতিল করে ব্যালেন্স ফেরত দেওয়া হয়েছে।")
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"❌ **আপনার উইথড্র রিকোয়েস্টটি বাতিল করা হয়েছে এবং ৳{amount:.2f} টাকা আপনার মূল ব্যালেন্সে ফেরত দেওয়া হয়েছে।** 🔄",
                parse_mode="Markdown",
            )
        except Exception:
            pass

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stock", check_stock))
    app.add_handler(CommandHandler("getused", get_used_gmails))

    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^(check_join|show_main_menu)$"))
    app.add_handler(CallbackQueryHandler(main_callbacks, pattern="^(request_withdraw|withdraw_|submit_task_|cancel_task_)"))
    app.add_handler(CallbackQueryHandler(admin_action_callback, pattern="^(w_approve_|w_reject_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is ready and running smoothly with full requested updates...")
    app.run_polling()

if __name__ == "__main__":
    main()
