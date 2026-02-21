"""
Jarvis Telegram Bot
Polls Telegram for messages, forwards them to FastAPI /orchestrate,
and sends the reply back to the user.
"""
import os
import logging
import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ── Config ───────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://jarvis-fastapi:8000")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("jarvis-telegram")

# ── Handlers ─────────────────────────────────────────────────────────


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "👋 Hi! I'm Jarvis, your AI assistant.\n\n"
        "Send me any message and I'll process it through the Jarvis pipeline.\n\n"
        "Commands:\n"
        "/start — Show this message\n"
        "/health — Check system health\n"
        "/help — Show help"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "🤖 *Jarvis AI Assistant*\n\n"
        "Just send me a message and I'll:\n"
        "1. Classify your intent\n"
        "2. Retrieve relevant context\n"
        "3. Plan a response\n"
        "4. Execute and critique it\n\n"
        "Try things like:\n"
        '• "Remind me to check logs at 5pm"\n'
        '• "What did we discuss yesterday?"\n'
        '• "Save a note: meeting at 3pm"\n',
        parse_mode="Markdown",
    )


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /health command — checks FastAPI system health."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{FASTAPI_URL}/diagnostics")
            data = resp.json()

        services = data.get("services", {})
        lines = [f"🏥 *System Health:* {data.get('status', 'unknown').upper()}\n"]
        for name, info in services.items():
            icon = "✅" if info.get("status") == "up" else "❌"
            lines.append(f"{icon} {name}: {info.get('status', '?')}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        logger.error("Health check failed: %s", e)
        await update.message.reply_text(f"❌ Health check failed: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any text message — forward to FastAPI orchestrate."""
    user = update.effective_user
    text = update.message.text
    user_id = f"telegram_{user.id}"

    logger.info("Message from %s (%s): %s", user.first_name, user_id, text[:80])

    # Show typing indicator
    await update.message.chat.send_action("typing")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{FASTAPI_URL}/orchestrate",
                json={"user_id": user_id, "text": text},
            )
            data = resp.json()

        reply = data.get("reply", "Sorry, I couldn't process that.")
        intent = data.get("intent", "unknown")

        logger.info("Reply to %s [intent=%s]: %s", user.first_name, intent, reply[:80])
        await update.message.reply_text(reply)

    except httpx.TimeoutException:
        logger.error("Timeout calling FastAPI for user %s", user_id)
        await update.message.reply_text(
            "⏳ Sorry, the request timed out. The AI might be busy — try again in a moment."
        )
    except Exception as e:
        logger.error("Error processing message from %s: %s", user_id, e)
        await update.message.reply_text(
            f"❌ Sorry, something went wrong: {e}"
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error("Exception while handling an update:", exc_info=context.error)


# ── Main ─────────────────────────────────────────────────────────────


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return

    logger.info("🤖 Starting Jarvis Telegram bot (polling mode)...")
    logger.info("   FastAPI URL: %s", FASTAPI_URL)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    # Start polling (no HTTPS needed!)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
