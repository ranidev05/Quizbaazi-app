# error_handler.py
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error: {context.error}")
    
    # Get the error message
    error_message = str(context.error)
    
    # Send a message to the user
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"An error occurred: {error_message}\n\nPlease try again later or contact support."
        )
