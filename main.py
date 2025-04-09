# main.py
import os
import logging
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    Poll
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("https://nddygojvbhbekxwjhegj.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5kZHlnb2p2YmhiZWt4d2poZWdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM4NTE1ODIsImV4cCI6MjA1OTQyNzU4Mn0.CrwXQn0I7IIWv4uH5TfJCtyZqF8cb-4R4y7XQhAwp_4v")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Conversation states
MAIN_MENU, QUIZ_ZONE, QUESTION_BANK, PROFILE, WALLET, QUIZ_SET, TAKING_QUIZ = range(7)

# Define callback data patterns
QUIZ_ZONE_CALLBACK = "quiz_zone"
QUESTION_BANK_CALLBACK = "question_bank"
PROFILE_CALLBACK = "profile"
WALLET_CALLBACK = "wallet"
INVITE_CALLBACK = "invite"
CATEGORY_CALLBACK = "category_"
SUBJECT_CALLBACK = "subject_"
SET_CALLBACK = "set_"
WALLET_DEPOSIT_CALLBACK = "wallet_deposit"
WALLET_WITHDRAW_CALLBACK = "wallet_withdraw"
WALLET_TRANSACTIONS_CALLBACK = "wallet_transactions"
WALLET_BALANCE_CALLBACK = "wallet_balance"
BACK_CALLBACK = "back_to_"

# Helper functions for database operations
async def get_or_create_user(user_data):
    """Create user if not exists and return user data"""
    telegram_id = str(user_data.id)
    
    # Check if user exists
    user = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    
    if not user.data:
        # Generate unique invite code
        import uuid
        invite_code = str(uuid.uuid4())[:8]
        
        # Create new user
        new_user = {
            "telegram_id": telegram_id,
            "username": user_data.username,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "invite_code": invite_code
        }
        result = supabase.table("users").insert(new_user).execute()
        return result.data[0]
    
    return user.data[0]

async def get_quiz_categories():
    """Get all quiz categories from database"""
    result = supabase.table("quiz_categories").select("*").execute()
    return result.data

async def get_quiz_subjects():
    """Get all quiz subjects from database"""
    result = supabase.table("quiz_subjects").select("*").execute()
    return result.data

async def get_quiz_sets(category_id=None, subject_id=None):
    """Get quiz sets based on category or subject"""
    query = supabase.table("quiz_sets").select("*")
    
    if category_id:
        query = query.eq("category_id", category_id)
    if subject_id:
        query = query.eq("subject_id", subject_id)
        
    result = query.execute()
    return result.data

async def get_questions_for_set(set_id):
    """Get questions for a specific quiz set"""
    result = supabase.table("questions").select("*").eq("quiz_set_id", set_id).execute()
    return result.data

async def save_quiz_attempt(user_id, quiz_set_id, total_questions, correct_answers, wrong_answers, total_time):
    """Save the results of a quiz attempt"""
    unattempted = total_questions - (correct_answers + wrong_answers)
    
    attempt_data = {
        "user_id": user_id,
        "quiz_set_id": quiz_set_id,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "unattempted": unattempted,
        "total_time": total_time
    }
    
    result = supabase.table("user_attempts").insert(attempt_data).execute()
    return result.data[0]

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    
    # Store user data in database
    db_user = await get_or_create_user(user)
    
    # Create main menu keyboard
    keyboard = [
        [InlineKeyboardButton("Quiz Zone", callback_data=QUIZ_ZONE_CALLBACK)],
        [InlineKeyboardButton("Question Bank", callback_data=QUESTION_BANK_CALLBACK)],
        [InlineKeyboardButton("Profile", callback_data=PROFILE_CALLBACK)],
        [InlineKeyboardButton("Wallet", callback_data=WALLET_CALLBACK)],
        [InlineKeyboardButton("Invite", callback_data=INVITE_CALLBACK)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Welcome {user.first_name} to the Government Exam Quiz Bot!\n\n"
        "Please select an option from the menu below:",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

# Callback query handlers
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == QUIZ_ZONE_CALLBACK:
        return await quiz_zone_handler(update, context)
    elif query.data == QUESTION_BANK_CALLBACK:
        return await question_bank_handler(update, context)
    elif query.data == PROFILE_CALLBACK:
        return await profile_handler(update, context)
    elif query.data == WALLET_CALLBACK:
        return await wallet_handler(update, context)
    elif query.data == INVITE_CALLBACK:
        return await invite_handler(update, context)
    
    return MAIN_MENU

async def quiz_zone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz zone - show job categories"""
    query = update.callback_query
    
    # Get all categories from database
    categories = await get_quiz_categories()
    
    # Create keyboard with categories
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(
            category["name"], 
            callback_data=f"{CATEGORY_CALLBACK}{category['id']}"
        )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data=f"{BACK_CALLBACK}main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="Please select a job category:",
        reply_markup=reply_markup
    )
    
    return QUIZ_ZONE

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection - show quiz sets"""
    query = update.callback_query
    await query.answer()
    
    # Extract category ID from callback data
    category_id = int(query.data.replace(CATEGORY_CALLBACK, ""))
    context.user_data["selected_category_id"] = category_id
    
    # Get quiz sets for this category
    quiz_sets = await get_quiz_sets(category_id=category_id)
    
    # Create keyboard with sets
    keyboard = []
    for i, quiz_set in enumerate(quiz_sets):
        if i % 2 == 0:
            row = [InlineKeyboardButton(
                quiz_set["name"], 
                callback_data=f"{SET_CALLBACK}{quiz_set['id']}"
            )]
            if i + 1 < len(quiz_sets):
                row.append(InlineKeyboardButton(
                    quiz_sets[i+1]["name"], 
                    callback_data=f"{SET_CALLBACK}{quiz_sets[i+1]['id']}"
                ))
            keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("Back to Categories", callback_data=f"{BACK_CALLBACK}categories")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="Please select a quiz set:",
        reply_markup=reply_markup
    )
    
    return QUIZ_SET

async def question_bank_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle question bank - show subject categories"""
    query = update.callback_query
    await query.answer()
    
    # Get all subjects from database
    subjects = await get_quiz_subjects()
    
    # Create keyboard with subjects
    keyboard = []
    for subject in subjects:
        keyboard.append([InlineKeyboardButton(
            subject["name"], 
            callback_data=f"{SUBJECT_CALLBACK}{subject['id']}"
        )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data=f"{BACK_CALLBACK}main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="Please select a subject:",
        reply_markup=reply_markup
    )
    
    return QUESTION_BANK

async def subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subject selection - show quiz sets"""
    query = update.callback_query
    await query.answer()
    
    # Extract subject ID from callback data
    subject_id = int(query.data.replace(SUBJECT_CALLBACK, ""))
    context.user_data["selected_subject_id"] = subject_id
    
    # Get quiz sets for this subject
    quiz_sets = await get_quiz_sets(subject_id=subject_id)
    
    # Create keyboard with sets
    keyboard = []
    for i, quiz_set in enumerate(quiz_sets):
        if i % 2 == 0:
            row = [InlineKeyboardButton(
                quiz_set["name"], 
                callback_data=f"{SET_CALLBACK}{quiz_set['id']}"
            )]
            if i + 1 < len(quiz_sets):
                row.append(InlineKeyboardButton(
                    quiz_sets[i+1]["name"], 
                    callback_data=f"{SET_CALLBACK}{quiz_sets[i+1]['id']}"
                ))
            keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("Back to Subjects", callback_data=f"{BACK_CALLBACK}subjects")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="Please select a quiz set:",
        reply_markup=reply_markup
    )
    
    return QUIZ_SET

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile button - show user profile"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Get user data from database
    result = supabase.table("users").select("*").eq("telegram_id", str(user.id)).execute()
    db_user = result.data[0] if result.data else None
    
    if not db_user:
        await query.edit_message_text(
            text="Error: User profile not found. Please restart the bot with /start."
        )
        return MAIN_MENU
    
    # Get user's quiz stats
    attempts_result = supabase.table("user_attempts").select("*").eq("user_id", db_user["id"]).execute()
    total_attempts = len(attempts_result.data)
    total_correct = sum(attempt["correct_answers"] for attempt in attempts_result.data) if attempts_result.data else 0
    total_questions = sum(attempt["total_questions"] for attempt in attempts_result.data) if attempts_result.data else 0
    
    # Calculate accuracy
    accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    # Create profile text
    profile_text = f"📊 *User Profile*\n\n"
    profile_text += f"*Name:* {db_user['first_name']} {db_user['last_name'] or ''}\n"
    profile_text += f"*Username:* @{db_user['username'] or 'Not set'}\n"
    profile_text += f"*Wallet Balance:* ₹{db_user['wallet_balance'] or 0:.2f}\n\n"
    profile_text += f"*Quiz Statistics:*\n"
    profile_text += f"• Total Attempts: {total_attempts}\n"
    profile_text += f"• Questions Answered: {total_questions}\n"
    profile_text += f"• Correct Answers: {total_correct}\n"
    profile_text += f"• Accuracy: {accuracy:.1f}%\n"
    
    # Back button
    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data=f"{BACK_CALLBACK}main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=profile_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return MAIN_MENU

async def wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet button - show wallet options"""
    query = update.callback_query
    await query.answer()
    
    # Get user's wallet balance
    user = update.effective_user
    result = supabase.table("users").select("wallet_balance").eq("telegram_id", str(user.id)).execute()
    wallet_balance = result.data[0]["wallet_balance"] if result.data else 0
    
    # Create wallet menu
    keyboard = [
        [InlineKeyboardButton("Deposit", callback_data=WALLET_DEPOSIT_CALLBACK)],
        [InlineKeyboardButton("Withdraw", callback_data=WALLET_WITHDRAW_CALLBACK)],
        [InlineKeyboardButton("Transactions", callback_data=WALLET_TRANSACTIONS_CALLBACK)],
        [InlineKeyboardButton("Balance", callback_data=WALLET_BALANCE_CALLBACK)],
        [InlineKeyboardButton("Back to Main Menu", callback_data=f"{BACK_CALLBACK}main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"💰 *Wallet*\n\nCurrent Balance: ₹{wallet_balance:.2f}\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return WALLET

async def invite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle invite button - show invite link"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Get user's invite code
    result = supabase.table("users").select("invite_code").eq("telegram_id", str(user.id)).execute()
    invite_code = result.data[0]["invite_code"] if result.data else None
    
    if not invite_code:
        await query.edit_message_text(
            text="Error: Invite code not found. Please restart the bot with /start."
        )
        return MAIN_MENU
    
    # Create invite link
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={invite_code}"
    
    # Back button
    keyboard = [[InlineKeyboardButton("Back to Main Menu", callback_data=f"{BACK_CALLBACK}main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"🔗 *Invite Friends*\n\nShare this link with your friends:\n\n`{invite_link}`\n\n"
             f"When they join using your link, both of you will receive rewards!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return MAIN_MENU

async def quiz_set_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz set selection and start the quiz"""
    query = update.callback_query
    await query.answer()
    
    # Extract quiz set ID from callback data
    quiz_set_id = int(query.data.replace(SET_CALLBACK, ""))
    context.user_data["selected_quiz_set_id"] = quiz_set_id
    
    # Get questions for this quiz set
    questions = await get_questions_for_set(quiz_set_id)
    
    if not questions:
        # No questions found
        await query.edit_message_text(
            text="No questions found for this quiz set. Please select another set."
        )
        return QUIZ_SET
    
    # Store questions in context
    context.user_data["questions"] = questions
    context.user_data["current_question_index"] = 0
    context.user_data["correct_answers"] = 0
    context.user_data["wrong_answers"] = 0
    context.user_data["start_time"] = datetime.now()
    context.user_data["answered_questions"] = []
    
    # Start the quiz
    return await send_next_question(update, context)

async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the next question to the user"""
    # Check if this is a callback query or a direct call
    if hasattr(update, 'callback_query'):
        query = update.callback_query
        message = query.message
    else:
        message = update.message
    
    questions = context.user_data["questions"]
    current_index = context.user_data["current_question_index"]
    
    # Check if we're done with all questions
    if current_index >= len(questions):
        return await finish_quiz(update, context)
    
    # Get current question
    question = questions[current_index]
    
    # Create options
    options = [
        question["option_a"],
        question["option_b"],
        question["option_c"],
        question["option_d"]
    ]
    
    # Create answer mapping (for checking correct answer later)
    correct_option_map = {
        "A": 0, "B": 1, "C": 2, "D": 3
    }
    context.user_data["correct_option_index"] = correct_option_map[question["correct_option"]]
    
    # Create keyboard with options
    keyboard = [
        [InlineKeyboardButton("A", callback_data="answer_0"), 
         InlineKeyboardButton("B", callback_data="answer_1")],
        [InlineKeyboardButton("C", callback_data="answer_2"), 
         InlineKeyboardButton("D", callback_data="answer_3")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send question with options
    question_text = f"Question {current_index + 1}/{len(questions)}\n\n{question['question_text']}\n\n"
    question_text += f"A. {question['option_a']}\n"
    question_text += f"B. {question['option_b']}\n"
    question_text += f"C. {question['option_c']}\n"
    question_text += f"D. {question['option_d']}\n\n"
    question_text += "⏱️ You have 30 seconds to answer."
    
    # Store the question's start time
    context.user_data["question_start_time"] = datetime.now()
    
    # Create timer for 30 seconds
    async def question_timer(context: ContextTypes.DEFAULT_TYPE, chat_id, message_id):
        await asyncio.sleep(30)
        # Check if user has already answered
        if "current_question_answered" not in context.user_data or not context.user_data["current_question_answered"]:
            # Time's up, mark as unanswered
            context.user_data["unanswered"] = context.user_data.get("unanswered", 0) + 1
            
            # Move to next question
            context.user_data["current_question_index"] += 1
            context.user_data["current_question_answered"] = False
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{question_text}\n\n⏱️ Time's up! Moving to the next question."
            )
            
            # Send next question
            await send_next_question(update, context)
    
    if hasattr(update, 'callback_query'):
        # Edit existing message
        await query.edit_message_text(text=question_text, reply_markup=reply_markup)
        
        # Schedule timer
        asyncio.create_task(question_timer(context, query.message.chat_id, query.message.message_id))
    else:
        # Send new message
        sent_message = await message.reply_text(text=question_text, reply_markup=reply_markup)
        
        # Schedule timer
        asyncio.create_task(question_timer(context, message.chat_id, sent_message.message_id))
    
    # Reset current question answered flag
    context.user_data["current_question_answered"] = False
    
    return TAKING_QUIZ

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's answer to a quiz question"""
    query = update.callback_query
    await query.answer()
    
    # Mark question as answered to prevent timer from processing it again
    context.user_data["current_question_answered"] = True
    
    # Get selected option and correct option
    selected_option = int(query.data.replace("answer_", ""))
    correct_option = context.user_data["correct_option_index"]
    
    # Calculate time taken to answer
    question_start_time = context.user_data["question_start_time"]
    answer_time = datetime.now()
    time_taken = (answer_time - question_start_time).total_seconds()
    
    # Check if answer is correct
    is_correct = selected_option == correct_option
    
    if is_correct:
        context.user_data["correct_answers"] += 1
        result_text = "✅ Correct!"
    else:
        context.user_data["wrong_answers"] += 1
        result_text = f"❌ Wrong! The correct answer was {['A', 'B', 'C', 'D'][correct_option]}."
    
    # Get current question
    questions = context.user_data["questions"]
    current_index = context.user_data["current_question_index"]
    question = questions[current_index]
    
    # Add answer details to list
    context.user_data["answered_questions"].append({
        "question": question["question_text"],
        "user_answer": selected_option,
        "correct_answer": correct_option,
        "is_correct": is_correct,
        "time_taken": time_taken
    })
    
    # Update question index
    context.user_data["current_question_index"] += 1
    
    # Create question text with result
    question_text = f"Question {current_index + 1}/{len(questions)}\n\n{question['question_text']}\n\n"
    question_text += f"A. {question['option_a']}\n"
    question_text += f"B. {question['option_b']}\n"
    question_text += f"C. {question['option_c']}\n"
    question_text += f"D. {question['option_d']}\n\n"
    question_text += f"{result_text}\n"
    question_text += f"Time taken: {time_taken:.1f} seconds"
    
    if question["explanation"]:
        question_text += f"\n\nExplanation: {question['explanation']}"
    
    # Show result for 2 seconds then move to next question
    await query.edit_message_text(text=question_text)
    
    # Wait 2 seconds before showing next question
    await asyncio.sleep(2)
    
    # Send next question
    return await send_next_question(update, context)

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish the quiz and show results"""
    if hasattr(update, 'callback_query'):
        query = update.callback_query
        chat_id = query.message.chat_id
    else:
        chat_id = update.message.chat_id
    
    # Calculate quiz statistics
    start_time = context.user_data["start_time"]
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    correct_answers = context.user_data["correct_answers"]
    wrong_answers = context.user_data["wrong_answers"]
    unanswered = context.user_data.get("unanswered", 0)
    
    total_questions = len(context.user_data["questions"])
    accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Get user ID from database
    user = update.effective_user
    result = supabase.table("users").select("id").eq("telegram_id", str(user.id)).execute()
    user_id = result.data[0]["id"] if result.data else None
    
    if user_id:
        # Save quiz attempt to database
        quiz_set_id = context.user_data["selected_quiz_set_id"]
        await save_quiz_attempt(
            user_id=user_id,
            quiz_set_id=quiz_set_id,
            total_questions=total_questions,
            correct_answers=correct_answers,
            wrong_answers=wrong_answers,
            total_time=total_time
        )
    
    # Create result text
    result_text = "📊 *Quiz Results*\n\n"
    result_text += f"Total Questions: {total_questions}\n"
    result_text += f"Correct Answers: {correct_answers}\n"
    result_text += f"Wrong Answers: {wrong_answers}\n"
    result_text += f"Unanswered: {unanswered}\n"
    result_text += f"Accuracy: {accuracy:.1f}%\n"
    result_text += f"Total Time: {total_time:.1f} seconds\n\n"
    
    if accuracy >= 80:
        result_text += "🌟 Excellent performance! Keep it up!"
    elif accuracy >= 60:
        result_text += "👍 Good job! There's still room for improvement."
    else:
        result_text += "📚 Keep practicing! You'll improve with time."
    
    # Create detailed review of answers
    answer_review = "\n\n*Detailed Review:*\n\n"
    for i, answer in enumerate(context.user_data["answered_questions"]):
        answer_review += f"Q{i+1}: {'✅' if answer['is_correct'] else '❌'} "
        answer_review += f"({answer['time_taken']:.1f}s)\n"
    
    result_text += answer_review
    
    # Create keyboard with options to go back to main menu
    keyboard = [
        [InlineKeyboardButton("Return to Main Menu", callback_data=f"{BACK_CALLBACK}main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query'):
        await query.edit_message_text(
            text=result_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=result_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Clear user data
    for key in ["questions", "current_question_index", "correct_answers", 
                "wrong_answers", "start_time", "answered_questions"]:
        if key in context.user_data:
            del context.user_data[key]
    
    return MAIN_MENU

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button callbacks"""
    query = update.callback_query
    await query.answer()
    
    destination = query.data.replace(f"{BACK_CALLBACK}", "")
    
    if destination == "main":
        # Go back to main menu
        keyboard = [
            [InlineKeyboardButton("Quiz Zone", callback_data=QUIZ_ZONE_CALLBACK)],
            [InlineKeyboardButton("Question Bank", callback_data=QUESTION_BANK_CALLBACK)],
            [InlineKeyboardButton("Profile", callback_data=PROFILE_CALLBACK)],
            [InlineKeyboardButton("Wallet", callback_data=WALLET_CALLBACK)],
            [InlineKeyboardButton("Invite", callback_data=INVITE_CALLBACK)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="Please select an option from the menu below:",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU
        
    elif destination == "categories":
        # Go back to quiz categories
        return await quiz_zone_handler(update, context)
        
    elif destination == "subjects":
        # Go back to subjects
        return await question_bank_handler(update, context)
    
    # Default - go back to main menu
    return await start(update, context)

# Wallet-specific handlers
async def wallet_deposit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet deposit option"""
    query = update.callback_query
    await query.answer()
    
    # Here you would implement your payment gateway integration
    # For this example, we'll just show a message
    
    keyboard = [[InlineKeyboardButton("Back to Wallet", callback_data=WALLET_CALLBACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="💳 *Deposit Money*\n\n"
             "To add money to your wallet, please use one of the following methods:\n\n"
             "1. UPI: example@upi\n"
             "2. Bank Transfer: Account details in next message\n\n"
             "After payment, please share the transaction ID with us.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return WALLET

async def wallet_withdraw_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet withdraw option"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("Back to Wallet", callback_data=WALLET_CALLBACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="💸 *Withdraw Money*\n\n"
             "To withdraw money from your wallet, please provide your:\n\n"
             "1. UPI ID or Bank Account details\n"
             "2. Amount to withdraw\n\n"
             "We process withdrawals within 24-48 hours.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return WALLET

async def wallet_transactions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet transactions option"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Get user ID from database
    user_result = supabase.table("users").select("id").eq("telegram_id", str(user.id)).execute()
    user_id = user_result.data[0]["id"] if user_result.data else None
    
    if not user_id:
        await query.edit_message_text(
            text="Error: User not found. Please restart the bot with /start."
        )
        return WALLET
    
    # Get transactions from database
    transactions_result = supabase.table("transactions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
    transactions = transactions_result.data
    
    # Create transactions list
    if not transactions:
        transactions_text = "No transactions found."
    else:
        transactions_text = ""
        for i, tx in enumerate(transactions, 1):
            tx_date = datetime.fromisoformat(tx["created_at"].replace("Z", "+00:00")).strftime("%d-%m-%Y %H:%M")
            transactions_text += f"{i}. {tx_date} - ₹{tx['amount']:.2f} - {tx['transaction_type'].capitalize()} - {tx['status'].capitalize()}\n"
    
    keyboard = [[InlineKeyboardButton("Back to Wallet", callback_data=WALLET_CALLBACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"📝 *Recent Transactions*\n\n{transactions_text}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return WALLET

async def wallet_balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet balance option"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Get user's wallet balance
    result = supabase.table("users").select("wallet_balance").eq("telegram_id", str(user.id)).execute()
    wallet_balance = result.data[0]["wallet_balance"] if result.data else 0
    
    keyboard = [[InlineKeyboardButton("Back to Wallet", callback_data=WALLET_CALLBACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"💰 *Wallet Balance*\n\nYour current balance is: ₹{wallet_balance:.2f}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return WALLET

def main():
    """Run the bot."""
    # Get token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Create conversation handler for main menu
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_handler, pattern=f"^({QUIZ_ZONE_CALLBACK}|{QUESTION_BANK_CALLBACK}|{PROFILE_CALLBACK}|{WALLET_CALLBACK}|{INVITE_CALLBACK})$")
            ],
            QUIZ_ZONE: [
                CallbackQueryHandler(category_handler, pattern=f"^{CATEGORY_CALLBACK}"),
                CallbackQueryHandler(back_handler, pattern=f"^{BACK_CALLBACK}")
            ],
            QUESTION_BANK: [
                CallbackQueryHandler(subject_handler, pattern=f"^{SUBJECT_CALLBACK}"),
                CallbackQueryHandler(back_handler, pattern=f"^{BACK_CALLBACK}")
            ],
            QUIZ_SET: [
                CallbackQueryHandler(quiz_set_handler, pattern=f"^{SET_CALLBACK}"),
                CallbackQueryHandler(back_handler, pattern=f"^{BACK_CALLBACK}")
            ],
            TAKING_QUIZ: [
                CallbackQueryHandler(handle_quiz_answer, pattern="^answer_")
            ],
            WALLET: [
                CallbackQueryHandler(wallet_deposit_handler, pattern=f"^{WALLET_DEPOSIT_CALLBACK}$"),
                CallbackQueryHandler(wallet_withdraw_handler, pattern=f"^{WALLET_WITHDRAW_CALLBACK}$"),
                CallbackQueryHandler(wallet_transactions_handler, pattern=f"^{WALLET_TRANSACTIONS_CALLBACK}$"),
                CallbackQueryHandler(wallet_balance_handler, pattern=f"^{WALLET_BALANCE_CALLBACK}$"),
                CallbackQueryHandler(back_handler, pattern=f"^{BACK_CALLBACK}"),
                CallbackQueryHandler(wallet_handler, pattern=f"^{WALLET_CALLBACK}$")
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    # Add conversation handler to application
    application.add_handler(conv_handler)
    
    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
