import logging
import threading
import os
import asyncio
from datetime import datetime
from flask import Flask
from supabase import create_client, Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ==========================================
# CONFIGURATION - BDG GAME
# ==========================================
# ⚠️ PASTE YOUR BOT TOKEN HERE
TOKEN ="8994009994:AAGCaAptekIIGheR2yHOarKRgJlypnH_PVk"

ADMIN_ID = "@proearner0"
REGISTER_LINK = "https://bdg4.vip/#/register?invitationCode=x5Vcp861092"
INVITE_CODE = "x5Vcp861092"
TELEGRAM_CHANNEL = "https://t.me/+H8f_nP-zUCZhMzll"
TODAY_GIFT_CODE = "4346F170B0051BD21B95EE9DECBAC10C"
ADMIN_NUMERIC_ID = 6081001025
LOG_CHANNEL_ID = ADMIN_NUMERIC_ID

SUPABASE_URL = "https://izxzdcvymipyvxcrgbee.supabase.co"
SUPABASE_KEY = "sb_publishable_KYwqH8JMDCk9utMYyP9Eyg_WFAjUuZS"
# ==========================================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CHOOSE_LANG, ASK_GAME_ID, ASK_TEAM_STATUS, DEPOSIT_MENU, DEPOSIT_HELP, WITHDRAW_HELP, HUMAN_AGENT, BROADCAST_MSG = range(8)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home():
    return "BDG Game Support Bot is running 24/7!"
def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# SUPABASE DATABASE
# ==========================================
def save_user(user_id, username, first_name):
    try:
        response = supabase.table('users').select('user_id').eq('user_id', user_id).execute()
        if len(response.data) == 0:
            supabase.table('users').insert({
                "user_id": user_id,
                "username": username or "",
                "first_name": first_name or "",
                "language": "en",
                "joined_at": datetime.now().isoformat()
            }).execute()
            return True
        return False
    except Exception as e:
        logging.error(f"Supabase save_user error: {e}")
        return False

def get_user_lang(user_id):
    try:
        response = supabase.table('users').select('language').eq('user_id', user_id).execute()
        if len(response.data) > 0:
            return response.data[0]['language']
        return "en"
    except Exception as e:
        logging.error(f"Supabase get_user_lang error: {e}")
        return "en"

def set_user_lang(user_id, lang):
    try:
        supabase.table('users').update({"language": lang}).eq('user_id', user_id).execute()
    except Exception as e:
        logging.error(f"Supabase set_user_lang error: {e}")

def get_all_user_ids():
    try:
        response = supabase.table('users').select('user_id').execute()
        return [row['user_id'] for row in response.data]
    except Exception as e:
        logging.error(f"Supabase get_all_user_ids error: {e}")
        return []

def count_users():
    try:
        response = supabase.table('users').select('user_id').execute()
        return len(response.data)
    except Exception as e:
        logging.error(f"Supabase count_users error: {e}")
        return 0

# ==========================================
# TRANSLATIONS - BDG GAME
# ==========================================
TEXTS = {
    "lang_set": {"en": "✅ Language set to English!", "hi": "✅ भाषा हिंदी में सेट हो गई!", "te": "✅ భాష తెలుగులో సెట్ చేయబడింది!"},
    "welcome": {
        "en": "👋 Welcome to BDG Game Support! How can we help you today?",
        "hi": "👋 BDG Game सपोर्ट में आपका स्वागत है! हम आपकी कैसे मदद कर सकते हैं?",
        "te": "👋 BDG Game సపోర్ట్‌కు స్వాగతం! మేము మీకు ఎలా సహాయం చేయగలము?"
    },
    "btn_gift": {"en": "🎁 Daily Gift Code", "hi": "🎁 डेली गिफ्ट कोड", "te": "🎁 డైలీ గిఫ్ట్ కోడ్"},
    "btn_referral": {"en": "🔗 My Referral Link", "hi": "🔗 मेरा रेफरल लिंक", "te": "🔗 నా రెఫరల్ లింక్"},
    "btn_deposit": {"en": "💳 Deposit / Withdraw Help", "hi": "💳 डिपॉजिट / विड्रॉ हेल्प", "te": "💳 డిపాజిట్ / విత్‌డ్రా సహాయం"},
    "btn_faq": {"en": "❓ FAQ", "hi": "❓ सामान्य प्रश्न", "te": "❓ తరచుగా అడిగే ప్రశ్నలు"},
    "btn_human": {"en": "💬 Talk to Human Agent", "hi": "💬 ह्यूमन एजेंट से बात करें", "te": "💬 మానవ ఏజెంట్‌తో మాట్లాడండి"},
    "btn_changelang": {"en": "🌐 Change Language", "hi": "🌐 भाषा बदलें", "te": "🌐 భాష మార్చండి"},
    "btn_back": {"en": "⬅️ Back to Menu", "hi": "⬅️ मेनू पर वापस", "te": "⬅️ మెనూకు తిరిగి"},
    "btn_contact": {"en": "💬 Contact Admin", "hi": "💬 एडमिन से संपर्क करें", "te": "💬 అడ్మిన్‌ను సంప్రదించండి"},
    "btn_channel": {"en": "📢 Join Channel", "hi": "📢 चैनल जॉइन करें", "te": "📢 ఛానెల్ జాయిన్ అవ్వండి"},
    "btn_yes_reg": {"en": "✅ Yes, I'm registered", "hi": "✅ हाँ, मैं रजिस्टर्ड हूँ", "te": "✅ అవును, నేను రిజిస్టర్ అయ్యాను"},
    "btn_no_new": {"en": "❌ No, I'm new", "hi": "❌ नहीं, मैं नया हूँ", "te": "❌ కాదు, నేను కొత్తవాడిని"},
    "btn_dep_issue": {"en": "💵 Deposit Issue", "hi": "💵 डिपॉजिट समस्या", "te": "💵 డిపాజిట్ సమస్య"},
    "btn_with_issue": {"en": "🏧 Withdrawal Issue", "hi": "🏧 विड्रॉ समस्या", "te": "🏧 విత్‌డ్రా సమస్య"},
    "btn_solved": {"en": "✅ Yes, solved", "hi": "✅ हाँ, हल हो गया", "te": "✅ అవును, పరిష్కరించబడింది"},
    "btn_human_contact": {"en": "❌ No, contact Human", "hi": "❌ नहीं, ह्यूमन से संपर्क करें", "te": "❌ కాదు, మానవుడిని సంప్రదించండి"},
    "gift_prompt": {
        "en": "🎁 *Daily Gift Code*\n\nSend me your *BDG Game ID*.",
        "hi": "🎁 *डेली गिफ्ट कोड*\n\nअपनी *BDG Game ID* भेजें।",
        "te": "🎁 *డైలీ గిఫ్ట్ కోడ్*\n\nమీ *BDG Game ID* పంపండి."
    },
    "gift_received": {
        "en": "Thank you! Received: `{data}`\n\nIs this ID registered under our team?",
        "hi": "धन्यवाद! मिला: `{data}`\n\nक्या यह आईडी हमारी टीम में है?",
        "te": "ధన్యవాదాలు! అందింది: `{data}`\n\nఈ ID మా టీమ్‌లో ఉందా?"
    },
    "gift_verified": {
        "en": "✅ *Verified Team Member!*\n\nContact admin: {admin}\n🆔 `{id}`",
        "hi": "✅ *सत्यापित सदस्य!*\n\nएडमिन: {admin}\n🆔 `{id}`",
        "te": "✅ *ధృవీకరించబడిన సభ్యుడు!*\n\nఅడ్మిన్: {admin}\n🆔 `{id}`"
    },
    "gift_not_reg": {
        "en": "❌ *Not Registered*\n\nRegister on BDG Game: {link}",
        "hi": "❌ *रजिस्टर्ड नहीं*\n\nBDG Game पर रजिस्टर: {link}",
        "te": "❌ *రిజిస్టర్ కాలేదు*\n\nBDG Game లో రిజిస్టర్: {link}"
    },
    "referral": {
        "en": f"🔗 *Your BDG Game Referral Link:*\n\n{{link}}\n\nInvite Code: `{INVITE_CODE}`",
        "hi": f"🔗 *आपका BDG Game रेफरल लिंक:*\n\n{{link}}\n\nइनविटेशन कोड: `{INVITE_CODE}`",
        "te": f"🔗 *మీ BDG Game రెఫరల్ లింక్:*\n\n{{link}}\n\nఇన్విటేషన్ కోడ్: `{INVITE_CODE}`"
    },
    "faq": {
        "en": f"❓ *BDG Game FAQ:*\n\n1. *Login?* - Use phone/email\n2. *Password?* - Letters & numbers only\n3. *Withdraw?* - Wallet > Payout\n4. *Invite Code:* `{INVITE_CODE}`",
        "hi": f"❓ *BDG Game सामान्य प्रश्न:*\n\n1. *लॉगिन?* - फ़ोन/ईमेल\n2. *पासवर्ड?* - अक्षर और नंबर\n3. *विड्रॉ?* - वॉलेट > पेआउट\n4. *इनविटेशन कोड:* `{INVITE_CODE}`",
        "te": f"❓ *BDG Game FAQ:*\n\n1. *లాగిన్?* - ఫోన్/ఇమెయిల్\n2. *పాస్‌వర్డ్?* - అక్షరాలు & నంబర్లు\n3. *విత్‌డ్రా?* - వాలెట్ > పేఅవుట్\n4. *ఇన్విటేషన్ కోడ్:* `{INVITE_CODE}`"
    },
    "dep_menu": {"en": "💳 *BDG Deposit / Withdraw Help*\n\nChoose:", "hi": "💳 *BDG डिपॉजिट / विड्रॉ*\n\nचुनें:", "te": "💳 *BDG డిపాజిట్ / విత్‌డ్రా*\n\nఎంచుకోండి:"},
    "dep_trouble": {"en": "💵 *Deposit:*\n1. Wallet\n2. UPI/Bank\n3. Min ₹100\n4. Wait 5-10 mins\n\nSolved?", "hi": "💵 *डिपॉजिट:*\n1. वॉलेट\n2. UPI/बैंक\n3. न्यूनतम ₹100\n4. 5-10 मिनट\n\nहल हुई?", "te": "💵 *డిపాజిట్:*\n1. వాలెట్\n2. UPI/బ్యాంక్\n3. కనీసం ₹100\n4. 5-10 నిమిషాలు\n\nపరిష్కారమైందా?"},
    "with_trouble": {"en": "🏧 *Withdrawal:*\n1. Wallet > Payout\n2. Bank/UPI\n3. Min ₹200\n4. Wait 30 mins\n\nSolved?", "hi": "🏧 *विड्रॉ:*\n1. वॉलेट > पेआउट\n2. बैंक/UPI\n3. न्यूनतम ₹200\n4. 30 मिनट\n\nहल हुई?", "te": "🏧 *విత్‌డ్రా:*\n1. వాలెట్ > పేఅవుట్\n2. బ్యాంక్/UPI\n3. కనీసం ₹200\n4. 30 నిమిషాలు\n\nపరిష్కారమైందా?"},
    "solved": {"en": "🎉 Great! /start for more.", "hi": "🎉 बढ़िया! /start करें।", "te": "🎉 అద్భుతం! /start చేయండి."},
    "human_required": {"en": "💬 *Human Support*\n\nContact: {admin}", "hi": "💬 *ह्यूमन सपोर्ट*\n\nसंपर्क: {admin}", "te": "💬 *మానవ సహాయం*\n\nసంప్రదించండి: {admin}"},
    "human_prompt": {"en": "💬 *Talk to Human Agent*\n\nDescribe your issue below.", "hi": "💬 *ह्यूमन एजेंट*\n\nसमस्या बताएं।", "te": "💬 *మానవ ఏజెంట్*\n\nమీ సమస్యను వివరించండి."},
    "human_received": {"en": "✅ *Received*\n\n`{data}`\n\nContact: {admin}", "hi": "✅ *मिला*\n\n`{data}`\n\nसंपर्क: {admin}", "te": "✅ *అందింది*\n\n`{data}`\n\nసంప్రదించండి: {admin}"},
    "kw_unknown": {"en": "🤔 Try keywords:\n\n• otp\n• password\n• withdraw\n• deposit\n• login\n• register\n• bonus", "hi": "🤔 कीवर्ड आज़माएं:\n\n• otp\n• password\n• withdraw\n• deposit\n• login\n• register\n• bonus", "te": "🤔 కీవర్డ్‌లు:\n\n• otp\n• password\n• withdraw\n• deposit\n• login\n• register\n• bonus"},
    "kw_otp_title": {"en": "📩 OTP Not Received?", "hi": "📩 OTP नहीं आया?", "te": "📩 OTP రాలేదా?"},
    "kw_otp_body": {"en": "1️⃣ Wait 60 sec\n2️⃣ Check network\n3️⃣ Restart phone\n\nStill? {admin}", "hi": "1️⃣ 60 सेकंड\n2️⃣ नेटवर्क\n3️⃣ रीस्टार्ट\n\nफिर भी? {admin}", "te": "1️⃣ 60 సెకన్లు\n2️⃣ నెట్‌వర్క్\n3️⃣ రీస్టార్ట్\n\nఇంకా? {admin}"},
    "kw_pwd_title": {"en": "🔑 Password Help", "hi": "🔑 पासवर्ड", "te": "🔑 పాస్‌వర్డ్"},
    "kw_pwd_body": {"en": "✅ Capital (A-Z)\n✅ Small (a-z)\n✅ Numbers (0-9)\n❌ NO symbols", "hi": "✅ बड़े (A-Z)\n✅ छोटे (a-z)\n✅ नंबर (0-9)\n❌ चिन्ह नहीं", "te": "✅ పెద్ద (A-Z)\n✅ చిన్న (a-z)\n✅ నంబర్లు (0-9)\n❌ చిహ్నాలు వద్దు"},
    "kw_with_title": {"en": "🏧 Withdrawal", "hi": "🏧 विड्रॉ", "te": "🏧 విత్‌డ్రా"},
    "kw_with_body": {"en": "1. Login\n2. Wallet > Payout\n3. Bank/UPI\n4. Min ₹200\n5. Submit", "hi": "1. लॉगिन\n2. वॉलेट > पेआउट\n3. बैंक/UPI\n4. ₹200\n5. सबमिट", "te": "1. లాగిన్\n2. వాలెట్ > పేఅవుట్\n3. బ్యాంక్/UPI\n4. ₹200\n5. సబ్మిట్"},
    "kw_dep_title": {"en": "💵 Deposit", "hi": "💵 डिपॉजिट", "te": "💵 డిపాజిట్"},
    "kw_dep_body": {"en": "1. Login\n2. Wallet > Deposit\n3. UPI/Bank\n4. Min ₹100", "hi": "1. लॉगिन\n2. वॉलेट > डिपॉजिट\n3. UPI/बैंक\n4. ₹100", "te": "1. లాగిన్\n2. వాలెట్ > డిపాజిట్\n3. UPI/బ్యాంక్\n4. ₹100"},
    "kw_login_title": {"en": "🔓 Login", "hi": "🔓 लॉगिन", "te": "🔓 లాగిన్"},
    "kw_login_body": {"en": "1. Open app\n2. Login\n3. Phone/email\n4. Password\n5. OTP", "hi": "1. ऐप\n2. लॉगिन\n3. फ़ोन\n4. पासवर्ड\n5. OTP", "te": "1. యాప్\n2. లాగిన్\n3. ఫోన్\n4. పాస్‌వర్డ్\n5. OTP"},
    "kw_reg_title": {"en": "📝 Register on BDG Game", "hi": "📝 BDG Game पर रजिस्टर", "te": "📝 BDG Game లో రిజిస్టర్"},
    "kw_reg_body": {"en": f"1. {{link}}\n2. Phone\n3. Password\n4. Invite Code: `{INVITE_CODE}`", "hi": f"1. {{link}}\n2. फ़ोन\n3. पासवर्ड\n4. इनविटेशन कोड: `{INVITE_CODE}`", "te": f"1. {{link}}\n2. ఫోన్\n3. పాస్‌వర్డ్\n4. ఇన్విటేషన్ కోడ్: `{INVITE_CODE}`"},
    "kw_bonus_title": {"en": "🎁 BDG Bonus", "hi": "🎁 BDG बोनस", "te": "🎁 BDG బోనస్"},
    "kw_bonus_body": {"en": "Code:\n`{code}`\n\n24 hours only.", "hi": "कोड:\n`{code}`\n\n24 घंटे।", "te": "కోడ్:\n`{code}`\n\n24 గంటలు."},
    "kw_help_title": {"en": "🆘 BDG Help", "hi": "🆘 BDG मदद", "te": "🆘 BDG సహాయం"},
    "kw_help_body": {"en": "Login, Deposit, Withdraw, OTP, Password, Gift codes.", "hi": "लॉगिन, डिपॉजिट, विड्रॉ, OTP, पासवर्ड, गिफ्ट।", "te": "లాగిన్, డిపాజిట్, విత్‌డ్రా, OTP, పాస్‌వర్డ్, గిఫ్ట్."},
}

def t(key, lang, **kwargs):
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("en", ""))
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

async def log_to_channel(bot, message: str):
    try:
        await bot.send_message(chat_id=LOG_CHANNEL_ID, text=message, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Log error: {e}")

def get_cached_lang(context, user_id):
    lang = context.user_data.get('lang')
    if not lang:
        lang = get_user_lang(user_id)
        context.user_data['lang'] = lang
    return lang

# ==========================================
# LANGUAGE SELECTION
# ==========================================
async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇮🇳 हिंदी", callback_data='lang_hi')],
        [InlineKeyboardButton("🇮🇳 తెలుగు", callback_data='lang_te')]
    ]
    text = "🌐 *Please choose your language:*\n🌐 *कृपया अपनी भाषा चुनें:*\n🌐 *దయచేసి మీ భాషను ఎంచుకోండి:*"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        except:
            await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return CHOOSE_LANG

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    user_id = query.from_user.id
    set_user_lang(user_id, lang)
    context.user_data['lang'] = lang
    try:
        await query.edit_message_text(t("lang_set", lang), parse_mode='Markdown')
    except:
        pass
    keyboard = [
        [InlineKeyboardButton(t("btn_gift", lang), callback_data='gift')],
        [InlineKeyboardButton(t("btn_referral", lang), callback_data='referral')],
        [InlineKeyboardButton(t("btn_deposit", lang), callback_data='deposit')],
        [InlineKeyboardButton(t("btn_faq", lang), callback_data='faq')],
        [InlineKeyboardButton(t("btn_human", lang), callback_data='human')],
        [InlineKeyboardButton(t("btn_channel", lang), url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton(t("btn_changelang", lang), callback_data='changelang')]
    ]
    await query.message.reply_text(t("welcome", lang), reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_GAME_ID

# ==========================================
# MAIN MENU
# ==========================================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    lang = get_cached_lang(context, user_id)
    keyboard = [
        [InlineKeyboardButton(t("btn_gift", lang), callback_data='gift')],
        [InlineKeyboardButton(t("btn_referral", lang), callback_data='referral')],
        [InlineKeyboardButton(t("btn_deposit", lang), callback_data='deposit')],
        [InlineKeyboardButton(t("btn_faq", lang), callback_data='faq')],
        [InlineKeyboardButton(t("btn_human", lang), callback_data='human')],
        [InlineKeyboardButton(t("btn_channel", lang), url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton(t("btn_changelang", lang), callback_data='changelang')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = t("welcome", lang)
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
        except:
            await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup)
    return ASK_GAME_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    is_new = save_user(user.id, user.username, user.first_name)
    context.user_data['lang'] = get_user_lang(user.id)
    if is_new:
        await log_to_channel(context.bot,
            f"🆕 *NEW BDG USER*\n\n👤 {user.first_name}\n📛 @{user.username if user.username else 'N/A'}\n🆔 `{user.id}`\n👥 Total: `{count_users()}`")
        return await language_selection(update, context)
    return await main_menu(update, context)

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await language_selection(update, context)

# ==========================================
# KEYWORDS
# ==========================================
async def keyword_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    user = update.effective_user
    lang = get_cached_lang(context, user.id)
    save_user(user.id, user.username, user.first_name)
    admin = ADMIN_ID
    if "otp" in text:
        reply = f"📩 *{t('kw_otp_title', lang)}*\n\n{t('kw_otp_body', lang, admin=admin)}"
    elif "password" in text:
        reply = f"🔑 *{t('kw_pwd_title', lang)}*\n\n{t('kw_pwd_body', lang)}"
    elif "withdraw" in text:
        reply = f"🏧 *{t('kw_with_title', lang)}*\n\n{t('kw_with_body', lang)}"
    elif "deposit" in text:
        reply = f"💵 *{t('kw_dep_title', lang)}*\n\n{t('kw_dep_body', lang)}"
    elif "login" in text:
        reply = f"🔓 *{t('kw_login_title', lang)}*\n\n{t('kw_login_body', lang)}"
    elif "register" in text:
        reply = f"📝 *{t('kw_reg_title', lang)}*\n\n{t('kw_reg_body', lang, link=REGISTER_LINK)}"
    elif "bonus" in text or "gift" in text:
        reply = f"🎁 *{t('kw_bonus_title', lang)}*\n\n{t('kw_bonus_body', lang, code=TODAY_GIFT_CODE)}"
    elif "help" in text:
        reply = f"🆘 *{t('kw_help_title', lang)}*\n\n{t('kw_help_body', lang)}"
    else:
        keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
        await update.message.reply_text(t("kw_unknown", lang), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return
    keyboard = [
        [InlineKeyboardButton(t("btn_contact", lang), url=f"https://t.me/{admin.replace('@', '')}")],
        [InlineKeyboardButton(t("btn_channel", lang), url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton(t("btn_back", lang), callback_data='back')]
    ]
    await update.message.reply_text(reply, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ==========================================
# ADMIN
# ==========================================
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        return ConversationHandler.END
    await update.message.reply_text(f"📢 Broadcast Mode\n👥 Total: `{count_users()}`\n\nSend the message.", parse_mode='Markdown')
    return BROADCAST_MSG

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        return ConversationHandler.END
    message = update.message
    user_ids = get_all_user_ids()
    total = len(user_ids)
    if total == 0:
        await message.reply_text("❌ No users yet.")
        return ConversationHandler.END
    status_msg = await message.reply_text(f"📡 Broadcasting to {total} users...")
    success, failed = 0, 0
    for uid in user_ids:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=message.chat_id, message_id=message.message_id)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await status_msg.edit_text(f"✅ Broadcast done!\n📤 Sent: {success}\n❌ Failed: {failed}")
    return ConversationHandler.END

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    text = (f"📊 *BDG Game Bot Statistics*\n\n"
            f"👥 Total Users: `{count_users()}`\n"
            f"🎁 Gift Code: `{TODAY_GIFT_CODE}`\n"
            f"🔑 Invite Code: `{INVITE_CODE}`\n"
            f"💾 Database: Supabase (Permanent)\n"
            f"🌍 Languages: EN / HI / TE\n"
            f"⚡ Status: Online 24/7")
    await update.message.reply_text(text, parse_mode='Markdown')

# ==========================================
# FLOWS
# ==========================================
async def gift_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_cached_lang(context, query.from_user.id)
    await query.edit_message_text(t("gift_prompt", lang), parse_mode='Markdown')
    return ASK_GAME_ID

async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = "Screenshot" if update.message.photo else update.message.text
    context.user_data['game_id'] = user_data
    lang = get_cached_lang(context, update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton(t("btn_yes_reg", lang), callback_data='team_yes')],
        [InlineKeyboardButton(t("btn_no_new", lang), callback_data='team_no')],
        [InlineKeyboardButton(t("btn_back", lang), callback_data='back')]
    ]
    await update.message.reply_text(t("gift_received", lang, data=user_data), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ASK_TEAM_STATUS

async def receive_team_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_cached_lang(context, user.id)
    game_id = context.user_data.get('game_id', '?')
    if query.data == 'team_yes':
        text = t("gift_verified", lang, admin=ADMIN_ID, id=game_id)
        await log_to_channel(context.bot, f"✅ BDG Gift Claim\n👤 {user.first_name}\n🆔 `{game_id}`")
    else:
        text = t("gift_not_reg", lang, link=REGISTER_LINK)
        await log_to_channel(context.bot, f"❌ BDG Unregistered\n👤 {user.first_name}")
    keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_cached_lang(context, query.from_user.id)
    keyboard = [
        [InlineKeyboardButton(t("btn_dep_issue", lang), callback_data='dep_issue')],
        [InlineKeyboardButton(t("btn_with_issue", lang), callback_data='with_issue')],
        [InlineKeyboardButton(t("btn_back", lang), callback_data='back')]
    ]
    await query.edit_message_text(t("dep_menu", lang), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return DEPOSIT_MENU

async def deposit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_cached_lang(context, query.from_user.id)
    if query.data == 'dep_issue':
        text = t("dep_trouble", lang)
        state = DEPOSIT_HELP
    else:
        text = t("with_trouble", lang)
        state = WITHDRAW_HELP
    keyboard = [
        [InlineKeyboardButton(t("btn_solved", lang), callback_data='solved')],
        [InlineKeyboardButton(t("btn_human_contact", lang), callback_data='human_contact')],
        [InlineKeyboardButton(t("btn_back", lang), callback_data='back')]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return state

async def issue_resolution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_cached_lang(context, query.from_user.id)
    if query.data == 'solved':
        text = t("solved", lang)
    else:
        text = t("human_required", lang, admin=ADMIN_ID)
        await log_to_channel(context.bot, f"🆘 ESCALATED\n👤 {query.from_user.first_name}")
    keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

async def human_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_cached_lang(context, query.from_user.id)
    await query.edit_message_text(t("human_prompt", lang), parse_mode='Markdown')
    return HUMAN_AGENT

async def receive_human_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = "Screenshot" if update.message.photo else update.message.text
    user = update.effective_user
    lang = get_cached_lang(context, user.id)
    text = t("human_received", lang, data=user_data, admin=ADMIN_ID)
    keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    await log_to_channel(context.bot, f"💬 HUMAN REQUEST\n👤 {user.first_name}\n📝 {user_data}")
    return ConversationHandler.END

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = get_cached_lang(context, user_id)
    data = query.data
    if data == 'changelang':
        return await language_selection(update, context)
    elif data == 'referral':
        text = t("referral", lang, link=REGISTER_LINK)
        keyboard = [
            [InlineKeyboardButton(t("btn_channel", lang), url=TELEGRAM_CHANNEL)],
            [InlineKeyboardButton(t("btn_back", lang), callback_data='back')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return ASK_GAME_ID
    elif data == 'faq':
        text = t("faq", lang)
        keyboard = [[InlineKeyboardButton(t("btn_back", lang), callback_data='back')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return ASK_GAME_ID
    elif data == 'back':
        return await main_menu(update, context)
    return ASK_GAME_ID

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await main_menu(update, context)

# ==========================================
# MAIN
# ==========================================
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler('broadcast', broadcast_command)],
        states={BROADCAST_MSG: [MessageHandler(filters.ALL & ~filters.COMMAND, send_broadcast)]},
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    main_conv = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('language', language_command),
            CallbackQueryHandler(gift_code_start, pattern='^gift$'),
            CallbackQueryHandler(deposit_start, pattern='^deposit$'),
            CallbackQueryHandler(human_start, pattern='^human$'),
            CallbackQueryHandler(set_language, pattern='^lang_(en|hi|te)$'),
        ],
        states={
            CHOOSE_LANG: [
                CallbackQueryHandler(set_language, pattern='^lang_(en|hi|te)$'),
                CallbackQueryHandler(button_click),
            ],
            ASK_GAME_ID: [
                CallbackQueryHandler(gift_code_start, pattern='^gift$'),
                CallbackQueryHandler(deposit_start, pattern='^deposit$'),
                CallbackQueryHandler(human_start, pattern='^human$'),
                CallbackQueryHandler(button_click),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_id),
            ],
            ASK_TEAM_STATUS: [CallbackQueryHandler(receive_team_status, pattern='^(team_yes|team_no)$')],
            DEPOSIT_MENU: [CallbackQueryHandler(deposit_choice, pattern='^(dep_issue|with_issue)$')],
            DEPOSIT_HELP: [CallbackQueryHandler(issue_resolution, pattern='^(solved|human_contact)$')],
            WITHDRAW_HELP: [CallbackQueryHandler(issue_resolution, pattern='^(solved|human_contact)$')],
            HUMAN_AGENT: [MessageHandler(filters.TEXT | filters.PHOTO, receive_human_issue)],
        },
        fallbacks=[
            CommandHandler('start', start),
            CommandHandler('language', language_command),
            CallbackQueryHandler(button_click),
        ],
    )
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("language", language_command))
    app_bot.add_handler(CommandHandler("stats", stats_command))
    app_bot.add_handler(broadcast_conv)
    app_bot.add_handler(main_conv)
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_auto_reply))
    print("BDG Game Bot running 24/7...")
    app_bot.run_polling()
