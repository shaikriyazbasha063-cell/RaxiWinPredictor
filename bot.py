import logging
import threading
import os
import asyncio
import requests
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ==========================================
# CONFIGURATION
# ==========================================
# ⚠️ PASTE YOUR NEW PREDICTOR BOT TOKEN HERE
TOKEN = "PASTE_YOUR_NEW_PREDICTOR_BOT_TOKEN_HERE"

# Your numeric Telegram ID (admin)
ADMIN_NUMERIC_ID = 6081001025

# Your prediction channel for auto-posting
# Leave empty ("") if you don't want auto-posting yet
# Example: "@RaxiWinPredictions" or "-1001234567890"
PREDICTION_CHANNEL = ""

# Auto-post interval in seconds (300 = 5 minutes)
AUTO_POST_INTERVAL = 300
# ==========================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home():
    return "RaxiWin Predictor is running 24/7!"
def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# API ENDPOINTS (Multiple fallbacks)
# ==========================================
API_ENDPOINTS = [
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
    "https://api.raxiwin.com/api/webapi/GetNoaverageEmerdList?typeId=1",
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
]

def fetch_latest_results():
    """Fetch last 100 Wingo results with retry logic"""
    for endpoint in API_ENDPOINTS:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
            response = requests.get(endpoint, headers=headers, timeout=10)
            data = response.json()
            
            results = []
            if 'data' in data and 'list' in data['data']:
                for item in data['data']['list'][:100]:
                    num = item.get('number')
                    if num is not None:
                        results.append(int(num))
            
            if len(results) >= 20:
                return results
        except Exception as e:
            logging.error(f"API {endpoint} error: {e}")
            continue
    return []

# ==========================================
# ANALYSIS ENGINE
# ==========================================
def analyze_numbers(results):
    """Analyze last 100 results and predict top 3 numbers"""
    if len(results) < 20:
        return None
    
    freq = {i: 0 for i in range(10)}
    missing = {i: len(results) for i in range(10)}
    
    for num in results:
        freq[num] += 1
    
    for i, num in enumerate(results):
        if missing[num] == len(results):
            missing[num] = i
    
    avg_missing = {i: 10 for i in range(10)}
    for num in range(10):
        last_seen = -1
        gaps = []
        for i, n in enumerate(results):
            if n == num:
                if last_seen != -1:
                    gaps.append(i - last_seen)
                last_seen = i
        if gaps:
            avg_missing[num] = round(sum(gaps) / len(gaps), 1)
    
    scores = {}
    for num in range(10):
        miss = missing[num]
        avg = avg_missing[num]
        f = freq[num]
        score = (miss - avg) * 2 + (15 - f)
        scores[num] = round(score, 1)
    
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_predictions = [num for num, score in ranked[:3]]
    
    cold_numbers = sorted(missing.items(), key=lambda x: x[1], reverse=True)[:3]
    hot_numbers = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:3]
    
    latest = results[0]
    latest_size = "SMALL" if latest < 5 else "BIG"
    
    return {
        "latest": latest,
        "latest_size": latest_size,
        "total": len(results),
        "predictions": top_predictions,
        "cold": cold_numbers,
        "hot": hot_numbers,
        "freq": freq,
        "missing": missing,
        "avg_missing": avg_missing,
    }

# ==========================================
# PREDICT COMMAND
# ==========================================
async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        msg = await update.message.reply_text("📡 Fetching real-time results...")
    else:
        msg = await update.callback_query.edit_message_text("📡 Fetching real-time results...")
        await update.callback_query.answer()
    
    results = fetch_latest_results()
    if not results:
        await msg.edit_text("❌ API is offline right now. Try again in a few minutes.")
        return
    
    analysis = analyze_numbers(results)
    if not analysis:
        await msg.edit_text("❌ Not enough data. Try again soon.")
        return
    
    preds = " | ".join([f"`{n}`" for n in analysis['predictions']])
    cold_str = " | ".join([f"`{n}` (miss {m})" for n, m in analysis['cold']])
    hot_str = " | ".join([f"`{n}` ({f}x)" for n, f in analysis['hot']])
    
    text = (
        f"🎯 *RaxiWin Number Predictor*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *Latest Result:* `{analysis['latest']}` ({analysis['latest_size']})\n"
        f"🔢 *Analyzed:* Last {analysis['total']} rounds\n\n"
        f"🎯 *TOP 3 PREDICTIONS:*\n"
        f"{preds}\n\n"
        f"🧊 *Cold Numbers:*\n{cold_str}\n\n"
        f"🔥 *Hot Numbers:*\n{hot_str}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Disclaimer:* Random game. Play responsibly.\n"
        f"🔄 Real-time API data"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data='refresh'),
         InlineKeyboardButton("📊 Full Stats", callback_data='stats')]
    ]
    await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ==========================================
# STATS COMMAND
# ==========================================
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()
        msg = await update.callback_query.edit_message_text("📡 Loading stats...")
    else:
        msg = await update.message.reply_text("📡 Loading stats...")
    
    results = fetch_latest_results()
    if not results:
        await msg.edit_text("❌ API offline. Try again.")
        return
    
    analysis = analyze_numbers(results)
    
    lines = ["📊 *Number Statistics (Last 100)*\n━━━━━━━━━━━━━━━━━━━━\n"]
    lines.append("`Num | Freq | Miss | Avg | Status`")
    lines.append("`━━━━━━━━━━━━━━━━━━━━━━━━━`")
    
    for num in range(10):
        f = analysis['freq'][num]
        m = analysis['missing'][num]
        a = analysis['avg_missing'][num]
        if m == 0:
            status = "🔥"
        elif m > a:
            status = "🧊"
        else:
            status = "  "
        lines.append(f"`{num}   | {f:>3}  | {m:>3}  | {a:>3} | {status}`")
    
    preds_str = ", ".join(map(str, analysis['predictions']))
    lines.append(f"\n🎯 *Top Predictions:* `{preds_str}`")
    lines.append(f"⚠️ Play responsibly. No guarantee.")
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data='back')]]
    await msg.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ==========================================
# BUTTON HANDLER
# ==========================================
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    if data == 'refresh':
        await predict_command(update, context)
    elif data == 'stats':
        await stats_handler(update, context)
    elif data == 'back':
        await predict_command(update, context)

# ==========================================
# START
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🎯 Get Prediction", callback_data='refresh')],
        [InlineKeyboardButton("📊 Full Statistics", callback_data='stats')]
    ]
    text = (
        "🎯 *Welcome to RaxiWin Predictor!*\n\n"
        "I analyze the last 100 real-time results and predict the most likely numbers.\n\n"
        "👇 Tap below to get started:"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ==========================================
# AUTO-POST TO CHANNEL
# ==========================================
async def auto_post_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not PREDICTION_CHANNEL:
        return
    try:
        results = fetch_latest_results()
        if not results:
            return
        analysis = analyze_numbers(results)
        if not analysis:
            return
        
        preds = " | ".join([f"`{n}`" for n in analysis['predictions']])
        text = (
            f"🎯 *RaxiWin Prediction*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Last Result: `{analysis['latest']}` ({analysis['latest_size']})\n\n"
            f"🎯 *Target Numbers:*\n{preds}\n\n"
            f"🧊 Cold: `{analysis['cold'][0][0]}` (miss {analysis['cold'][0][1]})\n"
            f"🔥 Hot: `{analysis['hot'][0][0]}` ({analysis['hot'][0][1]}x)\n\n"
            f"⚠️ Play responsibly."
        )
        await context.bot.send_message(chat_id=PREDICTION_CHANNEL, text=text, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Auto-post error: {e}")

async def start_autopost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        await update.message.reply_text("❌ Admin only.")
        return
    if not PREDICTION_CHANNEL:
        await update.message.reply_text(
            "⚠️ No channel set.\n\nEdit line 24 in bot.py:\n`PREDICTION_CHANNEL = \"@yourchannel\"`\n\nThen redeploy.",
            parse_mode='Markdown'
        )
        return
    
    # Remove existing jobs
    for job in context.application.job_queue.jobs():
        job.schedule_removal()
    
    context.application.job_queue.run_repeating(auto_post_job, interval=AUTO_POST_INTERVAL, first=5)
    await update.message.reply_text(
        f"✅ Auto-post started!\n📢 Channel: `{PREDICTION_CHANNEL}`\n⏱️ Every {AUTO_POST_INTERVAL} seconds",
        parse_mode='Markdown'
    )

async def stop_autopost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        await update.message.reply_text("❌ Admin only.")
        return
    for job in context.application.job_queue.jobs():
        job.schedule_removal()
    await update.message.reply_text("🛑 Auto-post stopped.")

async def test_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_NUMERIC_ID:
        return
    if not PREDICTION_CHANNEL:
        await update.message.reply_text("⚠️ No channel set.")
        return
    try:
        await context.bot.send_message(chat_id=PREDICTION_CHANNEL, text="✅ Test message from Predictor Bot!")
        await update.message.reply_text("✅ Test sent! Check your channel.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ==========================================
# MAIN
# ==========================================
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("predict", predict_command))
    app_bot.add_handler(CommandHandler("stats", stats_handler))
    app_bot.add_handler(CommandHandler("start_autopost", start_autopost))
    app_bot.add_handler(CommandHandler("stop_autopost", stop_autopost))
    app_bot.add_handler(CommandHandler("test_channel", test_channel))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    
    print("Predictor Bot running 24/7...")
    app_bot.run_polling()
