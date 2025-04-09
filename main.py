import telebot
import os

# Bot initialization with token from environment variable
TOKEN = os.getenv('7006338541:AAE2_y1jfT1iMEttOQzjM5XwfolW-VtoD8k')
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set. Please set it in Railway.app.")
bot = telebot.TeleBot(TOKEN)

# Bot states
START, CATEGORY, QUIZ, ANSWER, WALLET_DEPOSIT, WALLET_WITHDRAW = range(6)

# UPI ID from environment variable or default
UPI_ID = os.getenv('UPI_ID', 'yourupi@upi')

# Global users dictionary
users = {}
from supabase import create_client, Client
import os

# Supabase client setup
supabase_url = os.getenv('https://nddygojvbhbekxwjhegj.supabase.co')
supabase_key = os.getenv('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5kZHlnb2p2YmhiZWt4d2poZWdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM4NTE1ODIsImV4cCI6MjA1OTQyNzU4Mn0.CrwXQn0I7IIWv4uH5TfJCtyZqF8cb-4R4y7XQhAwp_4')
supabase: Client = create_client(supabase_url, supabase_key)

def load_questions():
    try:
        response = supabase.table('quiz_questions').select('*').execute()
        rows = response.data
        questions = {
            'Quiz Zone': {
                'Bihar Daroga': [[] for _ in range(20)],
                'Bihar Police': [[] for _ in range(20)],
                'Railway': [[] for _ in range(20)]
            },
            'Question Bank': {
                'Current Affairs': [],
                'Maths': [],
                'Reasoning': [],
                'English': [],
                'GK/GS': {
                    'History': [[] for _ in range(20)],
                    'Geography': [[] for _ in range(20)],
                    'Polity': [[] for _ in range(20)],
                    'Economics': [[] for _ in range(20)],
                    'Statistics': [[] for _ in range(20)],
                    'Physics': [[] for _ in range(20)],
                    'Chemistry': [[] for _ in range(20)],
                    'Biology': [[] for _ in range(20)]
                }
            }
        }
        for row in rows:
            section = row['section']
            category = row['category']
            set_num = row['set_number'] - 1  # Adjust to 0-based index
            ref_note = row['reference_note'] if row['reference_note'] else ''
            if section == 'Quiz Zone':
                questions['Quiz Zone'][category][set_num].append({
                    'q': row['question'],
                    'options': [row['option1'], row['option2'], row['option3'], row['option4']],
                    'ans': row['answer'],
                    'ref_note': ref_note
                })
            elif section == 'Question Bank':
                if category in ['Current Affairs', 'Maths', 'Reasoning', 'English']:
                    questions['Question Bank'][category].append({
                        'q': row['question'],
                        'options': [row['option1'], row['option2'], row['option3'], row['option4']],
                        'ans': row['answer'],
                        'ref_note': ref_note
                    })
                elif category == 'GK/GS':
                    subcategory = row['category']  # Assuming category holds subcategory for GK/GS
                    questions['Question Bank']['GK/GS'][subcategory][set_num].append({
                        'q': row['question'],
                        'options': [row['option1'], row['option2'], row['option3'], row['option4']],
                        'ans': row['answer'],
                        'ref_note': ref_note
                    })
        return questions
    except Exception as e:
        print(f"Error loading questions: {e}")
        # Fallback hardcoded data (same as before)
        return {
            'Quiz Zone': {
                'Bihar Daroga': [[{'q': 'What is Bihar Daroga role?', 'options': ['Police', 'Teacher', 'Clerk', 'Doctor'], 'ans': 'Police', 'ref_note': 'BPSC 2020'}] for _ in range(20)],
                # ... rest of fallback data
            },
            # ... rest of fallback data
        }

def load_users():
    global users
    try:
        response = supabase.table('users').select('*').execute()
        rows = response.data
        users = {}
        for row in rows:
            user_id = row['user_id']
            users[user_id] = {
                'name': row['name'],
                'username': row['username'] if row['username'] else '',
                'wallet': {
                    'balance': float(row['balance']),
                    'transactions': row['transactions'].split(';') if row['transactions'] else []
                },
                'pending_deposit': {
                    'amount': float(row['pending_deposit_amount']),
                    'ref_id': row['pending_deposit_ref_id'],
                    'status': row['pending_deposit_status']
                },
                'pending_withdrawal': {
                    'amount': float(row['pending_withdrawal_amount']),
                    'upi_id': row['pending_withdrawal_upi'],
                    'status': row['pending_withdrawal_status']
                },
                'quiz_progress': {
                    'Quiz Zone': {'Bihar Daroga': {'free': 0, 'paid': 3}, 'Bihar Police': {'free': 0, 'paid': 3}, 'Railway': {'free': 0, 'paid': 3}},
                    'Question Bank': {subject: 0 for subject in QUESTIONS['Question Bank'].keys()}
                }
            }
        return users
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users(users):
    try:
        # Clear existing data and insert updated data
        supabase.table('users').delete().neq('user_id', 'none').execute()  # Clear all
        for user_id, data in users.items():
            user_data = {
                'user_id': user_id,
                'name': data['name'],
                'username': data['username'],
                'balance': data['wallet']['balance'],
                'transactions': ';'.join(data['wallet']['transactions']),
                'pending_deposit_amount': data['pending_deposit']['amount'],
                'pending_deposit_ref_id': data['pending_deposit']['ref_id'],
                'pending_deposit_status': data['pending_deposit']['status'],
                'pending_withdrawal_amount': data['pending_withdrawal']['amount'],
                'pending_withdrawal_upi': data['pending_withdrawal']['upi_id'],
                'pending_withdrawal_status': data['pending_withdrawal']['status']
            }
            supabase.table('users').insert(user_data).execute()
    except Exception as e:
        print(f"Error saving users: {e}")

QUESTIONS = load_questions()
from bot_config import bot
from telebot import types

def show_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎯 Quiz Zone", callback_data="quiz_zone"),
               types.InlineKeyboardButton("📚 Question Bank", callback_data="question_bank"))
    markup.add(types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
               types.InlineKeyboardButton("💰 Wallet", callback_data="wallet"))
    markup.add(types.InlineKeyboardButton("🎁 Invite", callback_data="refer"))
    bot.send_message(chat_id, "🎉 Welcome to the Quiz Bot!\nChoose an option:", reply_markup=markup)

def show_quiz_categories(chat_id):
    markup = types.InlineKeyboardMarkup()
    categories = [
        ("🎓 Bihar Daroga", "Bihar Daroga"),
        ("👮 Bihar Police", "Bihar Police"),
        ("🚂 Railway", "Railway")
    ]
    for display, cat in categories:
        markup.add(types.InlineKeyboardButton(display, callback_data=f"qz_category_{cat}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main"))
    bot.send_message(chat_id, "🎯 Select a Category:", reply_markup=markup)

def show_question_bank_subjects(chat_id):
    markup = types.InlineKeyboardMarkup()
    subjects = ['Current Affairs', 'Maths', 'Reasoning', 'English', 'GK/GS']
    for subject in subjects:
        markup.add(types.InlineKeyboardButton(subject, callback_data=f"qb_subject_{subject}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main"))
    bot.send_message(chat_id, "📚 Select a Subject:", reply_markup=markup)

def show_wallet_menu(chat_id, message_id=None):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💰 Deposit", callback_data="wallet_deposit"),
               types.InlineKeyboardButton("💵 Withdraw", callback_data="wallet_withdraw"))
    markup.add(types.InlineKeyboardButton("📊 Balance", callback_data="wallet_balance"),
               types.InlineKeyboardButton("📜 History", callback_data="wallet_history"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main"))
    if message_id:
        bot.edit_message_text("💰 Wallet Options:", chat_id=chat_id, message_id=message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, "💰 Wallet Options:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    show_main_menu(call.message.chat.id)
    bot.answer_callback_query(call.id)
    from bot_config import bot, users
from database import load_users, save_users
from menus import show_main_menu, show_quiz_categories

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        users[user_id] = {
            'name': message.from_user.first_name,
            'username': message.from_user.username if message.from_user.username else '',
            'wallet': {'balance': 0, 'transactions': []},
            'pending_deposit': {'amount': 0, 'ref_id': '', 'status': 'Pending'},
            'pending_withdrawal': {'amount': 0, 'upi_id': '', 'status': 'Pending'},
            'quiz_progress': {
                'Quiz Zone': {'Bihar Daroga': {'free': 0, 'paid': 3}, 'Bihar Police': {'free': 0, 'paid': 3}, 'Railway': {'free': 0, 'paid': 3}},
                'Question Bank': {subject: 0 for subject in QUESTIONS['Question Bank'].keys()}
            }
        }
        save_users(users)
    bot.send_message(message.chat.id, f"🎉 Welcome, {users[user_id]['name']}! Use /help for instructions.")
    show_main_menu(message.chat.id)

@bot.message_handler(commands=['startquiz'])
def start_quiz_command(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        users[user_id] = {
            'name': message.from_user.first_name,
            'username': message.from_user.username if message.from_user.username else '',
            'wallet': {'balance': 0, 'transactions': []},
            'pending_deposit': {'amount': 0, 'ref_id': '', 'status': 'Pending'},
            'pending_withdrawal': {'amount': 0, 'upi_id': '', 'status': 'Pending'},
            'quiz_progress': {
                'Quiz Zone': {'Bihar Daroga': {'free': 0, 'paid': 3}, 'Bihar Police': {'free': 0, 'paid': 3}, 'Railway': {'free': 0, 'paid': 3}},
                'Question Bank': {subject: 0 for subject in QUESTIONS['Question Bank'].keys()}
            }
        }
        save_users(users)
    show_quiz_categories(message.chat.id)

@bot.message_handler(commands=['invite'])
def invite_command(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        users[user_id] = {
            'name': message.from_user.first_name,
            'username': message.from_user.username if message.from_user.username else '',
            'wallet': {'balance': 0, 'transactions': []},
            'pending_deposit': {'amount': 0, 'ref_id': '', 'status': 'Pending'},
            'pending_withdrawal': {'amount': 0, 'upi_id': '', 'status': 'Pending'},
            'quiz_progress': {
                'Quiz Zone': {'Bihar Daroga': {'free': 0, 'paid': 3}, 'Bihar Police': {'free': 0, 'paid': 3}, 'Railway': {'free': 0, 'paid': 3}},
                'Question Bank': {subject: 0 for subject in QUESTIONS['Question Bank'].keys()}
            }
        }
        save_users(users)
    ref_link = f"https://t.me/YourBotName?start={user_id}"
    bot.send_message(message.chat.id, f"🎁 Invite friends with this link to earn 100 bonus points:\n{ref_link}")

@bot.message_handler(commands=['about'])
def about_command(message):
    about_text = (
        "ℹ️ **About Quiz Bot**\n"
        "Practice and test your skills:\n"
        "- 🎯 Quiz Zone: Job-wise quizzes (some paid)\n"
        "- 📚 Question Bank: Free subject-wise tests\n"
        "Manage funds via /wallet. Start with /startquiz!"
    )
    bot.send_message(message.chat.id, about_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "📋 **Quiz Bot Commands**\n"
        "/start - Start the bot and view the welcome message\n"
        "/startquiz - Begin a quiz from Quiz Zone\n"
        "/invite - Get your referral link and earn bonus points\n"
        "/about - Learn about the bot and how to play\n"
        "/help - Get instructions on using the bot\n"
        "/exit - Exit the quiz at any time\n"
        "/profile - View your profile details\n"
        "\n**How to Play**: Choose Quiz Zone or Question Bank!"
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['exit'])
def exit_command(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id in users and 'quiz' in users[user_id]:
        del users[user_id]['quiz']
        bot.send_message(message.chat.id, "🏃 Quiz session exited!")
    else:
        bot.send_message(message.chat.id, "ℹ️ No active session to exit.")
    show_main_menu(message.chat.id)

@bot.message_handler(commands=['profile'])
def profile_command(message):
    user_id = str(message.from_user.id)
    users = load_users()
    if user_id not in users:
        bot.send_message(message.chat.id, "❌ Please start the bot with /start first!")
        return
    user = users[user_id]
    profile_text = (
        f"👤 Profile\n"
        f"Name: {user['name']}\n"
        f"Username: @{user['username'] if user['username'] else 'Not set'}\n"
        f"Wallet Balance: ₹{user['wallet']['balance']}"
    )
    bot.send_message(message.chat.id, profile_text)
    from bot_config import bot, users
from database import save_users, QUESTIONS
from menus import show_quiz_categories, show_main_menu
from quiz_logic import ask_question

@bot.callback_query_handler(func=lambda call: call.data == "quiz_zone")
def quiz_zone(call):
    show_quiz_categories(call.message.chat.id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qz_category_"))
def show_quiz_type(call):
    user_id = str(call.from_user.id)
    category = call.data.split("_")[2]
    if user_id not in users:
        users[user_id] = {
            'name': call.from_user.first_name,
            'username': call.from_user.username if call.from_user.username else '',
            'wallet': {'balance': 0, 'transactions': []},
            'pending_deposit': {'amount': 0, 'ref_id': '', 'status': 'Pending'},
            'pending_withdrawal': {'amount': 0, 'upi_id': '', 'status': 'Pending'},
            'quiz_progress': {
                'Quiz Zone': {'Bihar Daroga': {'free': 0, 'paid': 3}, 'Bihar Police': {'free': 0, 'paid': 3}, 'Railway': {'free': 0, 'paid': 3}},
                'Question Bank': {subject: 0 for subject in QUESTIONS['Question Bank'].keys()}
            }
        }
        save_users(users)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🆓 Free Quiz Set", callback_data=f"qz_free_{category}"),
               telebot.types.InlineKeyboardButton("💸 Paid Quiz Set", callback_data=f"qz_paid_{category}"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="quiz_zone"))
    bot.edit_message_text(f"🎯 Choose Quiz Type for {category}:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qz_free_") or call.data.startswith("qz_paid_"))
def start_quiz_zone(call):
    user_id = str(call.from_user.id)
    parts = call.data.split("_")
    quiz_type, category = parts[1], parts[2]
    progress = users[user_id]['quiz_progress']['Quiz Zone'][category]
    current_set = progress['free'] if quiz_type == 'free' else progress['paid']
    max_set = 2 if quiz_type == 'free' else 19
    if current_set > max_set:
        bot.send_message(call.message.chat.id, f"✅ You've completed all {quiz_type} sets for {category}!")
        show_main_menu(call.message.chat.id)
        return
    cost = 0 if quiz_type == 'free' else 5
    if cost > 0 and users[user_id]['wallet']['balance'] < cost:
        bot.send_message(call.message.chat.id, "❌ Insufficient balance! Deposit via Wallet.")
        show_main_menu(call.message.chat.id)
        return
    if cost > 0:
        users[user_id]['wallet']['balance'] -= cost
        users[user_id]['wallet']['transactions'].append(f"Quiz Set {current_set + 1} ({category}): -₹{cost} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    questions = random.sample(QUESTIONS['Quiz Zone'][category][current_set], min(25, len(QUESTIONS['Quiz Zone'][category][current_set])))
    users[user_id]['quiz'] = {
        'section': 'Quiz Zone',
        'category': category,
        'quiz_type': quiz_type,
        'current_set': current_set,
        'questions': questions,
        'current': 0,
        'attempted': 0,
        'correct': 0,
        'wrong': 0,
        'start_time': time.time(),
        'timer_active': True
    }
    ask_question(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)
    from bot_config import bot, users
from database import QUESTIONS
from menus import show_question_bank_subjects, show_main_menu
from quiz_logic import ask_question

@bot.callback_query_handler(func=lambda call: call.data == "question_bank")
def question_bank(call):
    show_question_bank_subjects(call.message.chat.id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qb_subject_"))
def handle_subject_selection(call):
    user_id = str(call.from_user.id)
    subject = call.data.split("_")[2]
    if user_id not in users:
        users[user_id] = {
            'name': call.from_user.first_name,
            'username': call.from_user.username if call.from_user.username else '',
            'wallet': {'balance': 0, 'transactions': []},
            'pending_deposit': {'amount': 0, 'ref_id': '', 'status': 'Pending'},
            'pending_withdrawal': {'amount': 0, 'upi_id': '', 'status': 'Pending'},
            'quiz_progress': {
                'Quiz Zone': {'Bihar Daroga': {'free': 0, 'paid': 3}, 'Bihar Police': {'free': 0, 'paid': 3}, 'Railway': {'free': 0, 'paid': 3}},
                'Question Bank': {subject: 0 for subject in QUESTIONS['Question Bank'].keys()}
            }
        }
        save_users(users)
    markup = telebot.types.InlineKeyboardMarkup()
    if subject == 'GK/GS':
        for subcat in QUESTIONS['Question Bank']['GK/GS'].keys():
            markup.add(telebot.types.InlineKeyboardButton(subcat, callback_data=f"qb_subcat_{subject}_{subcat}"))
    else:
        current_set = users[user_id]['quiz_progress']['Question Bank'][subject]
        if current_set < 20:
            markup.add(telebot.types.InlineKeyboardButton(f"Question Set {current_set + 1}", callback_data=f"qb_set_{subject}_{current_set + 1}"))
        else:
            bot.send_message(call.message.chat.id, f"✅ You've completed all sets for {subject}!")
            show_main_menu(call.message.chat.id)
            return
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="question_bank"))
    bot.edit_message_text(f"📚 Select an option for {subject}:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qb_subcat_"))
def show_question_sets(call):
    user_id = str(call.from_user.id)
    parts = call.data.split("_")
    subject, subcategory = parts[2], parts[3]
    current_set = users[user_id]['quiz_progress']['Question Bank'][subject]
    markup = telebot.types.InlineKeyboardMarkup()
    if current_set < 20:
        markup.add(telebot.types.InlineKeyboardButton(f"Question Set {current_set + 1}", callback_data=f"qb_set_{subject}_{subcategory}_{current_set + 1}"))
    else:
        bot.send_message(call.message.chat.id, f"✅ You've completed all sets for {subcategory}!")
        show_main_menu(call.message.chat.id)
        return
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data=f"qb_subject_{subject}"))
    bot.edit_message_text(f"📚 Select a Question Set for {subcategory}:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("qb_set_"))
def start_question_bank(call):
    user_id = str(call.from_user.id)
    parts = call.data.split("_")
    subject = parts[2]
    if subject == 'GK/GS':
        subcategory, set_num = parts[3], int(parts[4]) - 1
        questions = random.sample(QUESTIONS['Question Bank'][subject][subcategory][set_num], min(100, len(QUESTIONS['Question Bank'][subject][subcategory][set_num])))
    else:
        set_num = int(parts[3]) - 1
        questions = random.sample(QUESTIONS['Question Bank'][subject], min(100, len(QUESTIONS['Question Bank'][subject])))
    users[user_id]['quiz'] = {
        'section': 'Question Bank',
        'subject': subject,
        'subcategory': subcategory if subject == 'GK/GS' else None,
        'current_set': set_num,
        'questions': questions,
        'current': 0,
        'attempted': 0,
        'correct': 0,
        'wrong': 0,
        'start_time': time.time(),
        'timer_active': True
    }
    ask_question(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)
    from bot_config import bot, users
from database import save_users, QUESTIONS
from menus import show_main_menu
from threading import Timer
from datetime import datetime
import time

def ask_question(chat_id, user_id):
    if user_id not in users or 'quiz' not in users[user_id]:
        show_main_menu(chat_id)
        return
    q_data = users[user_id]['quiz']['questions'][users[user_id]['quiz']['current']]
    question_text = f"❓ Q{users[user_id]['quiz']['current'] + 1}/{len(users[user_id]['quiz']['questions'])}: {q_data['q']}"
    if q_data['ref_note']:
        question_text += f"\n<b><font color=\"red\">Reference: {q_data['ref_note']}</font></b>"
    markup = telebot.types.InlineKeyboardMarkup()
    for opt in q_data['options']:
        markup.add(telebot.types.InlineKeyboardButton(opt, callback_data=f"answer_{opt}"))
    time_limit = 30 if users[user_id]['quiz']['section'] == 'Quiz Zone' else 60
    bot.send_message(chat_id, question_text, reply_markup=markup, parse_mode="HTML")
    timer_msg = bot.send_message(chat_id, f"⏳ Timer: {time_limit} seconds left")
    Timer(time_limit, lambda: update_timer(chat_id, timer_msg.message_id, user_id, 0)).start()

def update_timer(chat_id, message_id, user_id, time_left):
    if user_id not in users or 'quiz' not in users[user_id] or not users[user_id]['quiz']['timer_active']:
        return
    if time_left <= 0:
        bot.edit_message_text("⏰ Time's up!", chat_id, message_id)
        next_question(chat_id, user_id, None)
    else:
        time_limit = 30 if users[user_id]['quiz']['section'] == 'Quiz Zone' else 60
        bot.edit_message_text(f"⏳ Timer: {time_left} seconds left", chat_id, message_id)
        Timer(1, lambda: update_timer(chat_id, message_id, user_id, time_left - 1)).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def check_answer(call):
    user_id = str(call.from_user.id)
    if user_id not in users or 'quiz' not in users[user_id]:
        show_main_menu(call.message.chat.id)
        return
    users[user_id]['quiz']['timer_active'] = False
    answer = call.data.split("_")[1]
    q_data = users[user_id]['quiz']['questions'][users[user_id]['quiz']['current']]
    users[user_id]['quiz']['attempted'] += 1
    if answer == q_data['ans']:
        users[user_id]['quiz']['correct'] += 1
    else:
        users[user_id]['quiz']['wrong'] += 1
    if users[user_id]['quiz']['section'] == 'Question Bank':
        bot.send_message(call.message.chat.id, "✅ Correct!" if answer == q_data['ans'] else f"❌ Wrong! Correct answer: {q_data['ans']}")
    next_question(call.message.chat.id, user_id, call.message.message_id)
    bot.answer_callback_query(call.id)

def next_question(chat_id, user_id, message_id):
    users[user_id]['quiz']['current'] += 1
    if users[user_id]['quiz']['current'] >= len(users[user_id]['quiz']['questions']):
        finish_quiz(chat_id, user_id)
    else:
        ask_question(chat_id, user_id)

def finish_quiz(chat_id, user_id):
    total_time = int(time.time() - users[user_id]['quiz']['start_time']) // 60  # Minutes
    review = (
        f"📋 Quiz Review\n"
        f"Total Questions: {len(users[user_id]['quiz']['questions'])}\n"
        f"Attempted: {users[user_id]['quiz']['attempted']}\n"
        f"Correct: {users[user_id]['quiz']['correct']}\n"
        f"Wrong: {users[user_id]['quiz']['wrong']}\n"
        f"Total Time Taken: {total_time} min"
    )
    bot.send_message(chat_id, review)
    if users[user_id]['quiz']['section'] == 'Quiz Zone':
        quiz_type = users[user_id]['quiz']['quiz_type']
        category = users[user_id]['quiz']['category']
        users[user_id]['quiz_progress']['Quiz Zone'][category][quiz_type] += 1
        next_set = users[user_id]['quiz_progress']['Quiz Zone'][category][quiz_type]
        max_set = 3 if quiz_type == 'free' else 20
        if next_set < max_set:
            cost = "Free" if quiz_type == 'free' else "₹5"
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(f"Start Quiz Set {next_set + 1} ({cost})", callback_data=f"qz_{quiz_type}_{category}"))
            markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="quiz_zone"))
            bot.send_message(chat_id, f"✅ Ready for the next set?", reply_markup=markup)
        else:
            bot.send_message(chat_id, f"✅ All {quiz_type} sets for {category} completed!")
            show_main_menu(chat_id)
    elif users[user_id]['quiz']['section'] == 'Question Bank':
        subject = users[user_id]['quiz']['subject']
        if subject == 'GK/GS':
            subject = 'GK/GS'
        users[user_id]['quiz_progress']['Question Bank'][subject] += 1
        next_set = users[user_id]['quiz_progress']['Question Bank'][subject]
        if next_set < 20:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(f"Start Question Set {next_set + 1}", callback_data=f"qb_set_{subject}_{next_set + 1}" if subject != 'GK/GS' else f"qb_subcat_{subject}_{users[user_id]['quiz']['subcategory']}"))
            markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="question_bank"))
            bot.send_message(chat_id, f"✅ Ready for the next set?", reply_markup=markup)
        else:
            bot.send_message(chat_id, f"✅ All sets for {subject} completed!")
            show_main_menu(chat_id)
    save_users(users)
    del users[user_id]['quiz']

def check_db_updates():
    while True:
        users = load_users()
        for user_id, data in users.items():
            if data['pending_deposit']['status'] == 'Success':
                amount = data['pending_deposit']['amount']
                ref_id = data['pending_deposit']['ref_id']
                users[user_id]['wallet']['balance'] += amount
                users[user_id]['wallet']['transactions'].append(f"Deposit Success: +₹{amount} (Ref: {ref_id}) on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                bot.send_message(int(user_id), f"✅ Your deposit of ₹{amount} (Ref: {ref_id}) has been successfully verified!")
                users[user_id]['pending_deposit'] = {'amount': 0, 'ref_id': '', 'status': 'Pending'}
            if data['pending_withdrawal']['status'] == 'Success':
                amount = data['pending_withdrawal']['amount']
                upi_id = data['pending_withdrawal']['upi_id']
                users[user_id]['wallet']['balance'] -= amount
                users[user_id]['wallet']['transactions'].append(f"Withdrawal Success: -₹{amount} to {upi_id} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                bot.send_message(int(user_id), f"✅ Your withdrawal of ₹{amount} to {upi_id} has been successfully processed!")
                users[user_id]['pending_withdrawal'] = {'amount': 0, 'upi_id': '', 'status': 'Pending'}
        save_users(users)
        time.sleep(60)
        from bot_config import bot, users
from database import load_users, QUESTIONS
from quiz_logic import check_db_updates
from threading import Thread

if __name__ == "__main__":
    users = load_users()
    Thread(target=check_db_updates).start()
    bot.polling(none_stop=True)
