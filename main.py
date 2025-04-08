import telebot
import random
import time
from datetime import datetime
import pandas as pd
import threading
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Initialize bot
bot = telebot.TeleBot("7651135048:AAFHdEopM7pwsQxBeHfdgxplT9d5x1hsD1U")

# Bot states
START, CATEGORY, QUIZ, ANSWER, WALLET_DEPOSIT, WALLET_WITHDRAW = range(6)

# UPI ID for deposits
UPI_ID = "yourupi@upi"

# Global data
users = {}

# Google Drive Setup
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FILE_IDS = {
    'quiz_questions': '10XQ8Un9NSNUpmYgXo8Q_eqfkxi3FW7OBc6MvRrocZIc',  # Replace with actual file ID
    'users': '1HqoO_GHfsHr8XKyfyduwVjutzpp_3fJ7myLnXsD5pOE'                     # Replace with actual file ID
}

def get_drive_service():
    creds = None
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    except FileNotFoundError:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def download_file_from_drive(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh

# Load questions from Google Drive
def load_questions():
    try:
        file = download_file_from_drive(FILE_IDS['quiz_questions'])
        df = pd.read_excel(file)
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
        for _, row in df.iterrows():
            section = row['Section']
            ref_note = row['ReferenceNote'] if pd.notna(row['ReferenceNote']) else ''
            if section == 'Quiz Zone':
                category = row['Category']
                set_num = int(row['SetNumber']) - 1
                questions['Quiz Zone'][category][set_num].append({
                    'q': row['Question'],
                    'options': [row['Option1'], row['Option2'], row['Option3'], row['Option4']],
                    'ans': row['Answer'],
                    'ref_note': ref_note
                })
            elif section == 'Question Bank':
                subject = row['Subject']
                if subject in ['Current Affairs', 'Maths', 'Reasoning', 'English']:
                    questions['Question Bank'][subject].append({
                        'q': row['Question'],
                        'options': [row['Option1'], row['Option2'], row['Option3'], row['Option4']],
                        'ans': row['Answer'],
                        'ref_note': ref_note
                    })
                elif subject == 'GK/GS':
                    subcategory = row['SubCategory']
                    set_num = int(row['SetNumber']) - 1
                    questions['Question Bank']['GK/GS'][subcategory][set_num].append({
                        'q': row['Question'],
                        'options': [row['Option1'], row['Option2'], row['Option3'], row['Option4']],
                        'ans': row['Answer'],
                        'ref_note': ref_note
                    })
        return questions
    except Exception as e:
        print(f"Error loading questions: {e}")
        return {
            'Quiz Zone': {
                'Bihar Daroga': [[{'q': 'What is Bihar Daroga role?', 'options': ['Police', 'Teacher', 'Clerk', 'Doctor'], 'ans': 'Police', 'ref_note': 'BPSC 2020'}] for _ in range(20)],
                'Bihar Police': [[{'q': 'Bihar Police HQ?', 'options': ['Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur'], 'ans': 'Patna', 'ref_note': 'Bihar SI 2019'}] for _ in range(20)],
                'Railway': [[{'q': 'Indian Railway founded?', 'options': ['1853', '1863', '1873', '1883'], 'ans': '1853', 'ref_note': 'RRB 2021'}] for _ in range(20)]
            },
            'Question Bank': {
                'Current Affairs': [{'q': 'Latest tech?', 'options': ['AI', 'VR', 'AR', 'IoT'], 'ans': 'AI', 'ref_note': 'UPSC 2022'}],
                'Maths': [{'q': 'What is 2+2?', 'options': ['4', '5', '6', '3'], 'ans': '4', 'ref_note': 'SSC 2019'}],
                'Reasoning': [{'q': 'If A is B, B is C, then?', 'options': ['A=C', 'B=C', 'A=B', 'C=A'], 'ans': 'A=C', 'ref_note': 'Bank PO 2020'}],
                'English': [{'q': 'Synonym of Happy?', 'options': ['Sad', 'Joy', 'Angry', 'Tired'], 'ans': 'Joy', 'ref_note': 'CLAT 2021'}],
                'GK/GS': {
                    'History': [[{'q': 'Who was Akbar?', 'options': ['King', 'Poet', 'Scientist', 'Trader'], 'ans': 'King', 'ref_note': 'UPSC 2018'}] for _ in range(20)],
                    'Geography': [[{'q': 'Largest desert?', 'options': ['Sahara', 'Gobi', 'Kalahari', 'Antarctic'], 'ans': 'Antarctic', 'ref_note': 'SSC 2020'}] for _ in range(20)],
                    'Polity': [[{'q': 'Constitution year?', 'options': ['1947', '1950', '1949', '1951'], 'ans': '1950', 'ref_note': 'BPSC 2021'}] for _ in range(20)],
                    'Economics': [[{'q': 'What is GDP?', 'options': ['Growth', 'Income', 'Value', 'Debt'], 'ans': 'Value', 'ref_note': 'IBPS 2019'}] for _ in range(20)],
                    'Statistics': [[{'q': 'What is mean?', 'options': ['Average', 'Median', 'Mode', 'Sum'], 'ans': 'Average', 'ref_note': 'SSC 2022'}] for _ in range(20)],
                    'Physics': [[{'q': 'Speed of light?', 'options': ['3x10^8', '3x10^6', '3x10^7', '3x10^9'], 'ans': '3x10^8', 'ref_note': 'JEE 2020'}] for _ in range(20)],
                    'Chemistry': [[{'q': 'What is H2O?', 'options': ['Water', 'Salt', 'Sugar', 'Acid'], 'ans': 'Water', 'ref_note': 'NEET 2021'}] for _ in range(20)],
                    'Biology': [[{'q': 'Human cell count?', 'options': ['Trillions', 'Billions', 'Millions', 'Thousands'], 'ans': 'Trillions', 'ref_note': 'NEET 2022'}] for _ in range(20)]
                }
            }
        }

QUESTIONS = load_questions()

# Load users from Google Drive
def load_users():
    global users
    try:
        file = download_file_from_drive(FILE_IDS['users'])
        df = pd.read_excel(file)
        users = {}
        for _, row in df.iterrows():
            user_id = str(row['UserID'])
            users[user_id] = {
                'name': row['Name'],
                'username': row['Username'] if pd.notna(row['Username']) else '',
                'wallet': {
                    'balance': row['Balance'],
                    'transactions': row['Transactions'].split(';') if pd.notna(row['Transactions']) else []
                },
                'pending_deposit': {
                    'amount': row['PendingDepositAmount'] if pd.notna(row['PendingDepositAmount']) else 0,
                    'ref_id': row['PendingDepositRefID'] if pd.notna(row['PendingDepositRefID']) else '',
                    'status': row['PendingDepositStatus'] if pd.notna(row['PendingDepositStatus']) else 'Pending'
                },
                'pending_withdrawal': {
                    'amount': row['PendingWithdrawalAmount'] if pd.notna(row['PendingWithdrawalAmount']) else 0,
                    'upi_id': row['PendingWithdrawalUPI'] if pd.notna(row['PendingWithdrawalUPI']) else '',
                    'status': row['PendingWithdrawalStatus'] if pd.notna(row['PendingWithdrawalStatus']) else 'Pending'
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

# Save users to Google Drive (local save for now)
def save_users(users):
    df = pd.DataFrame(columns=['UserID', 'Name', 'Username', 'Balance', 'Transactions', 
                               'PendingDepositAmount', 'PendingDepositRefID', 'PendingDepositStatus',
                               'PendingWithdrawalAmount', 'PendingWithdrawalUPI', 'PendingWithdrawalStatus'])
    for user_id, data in users.items():
        row = {
            'UserID': user_id,
            'Name': data['name'],
            'Username': data['username'],
            'Balance': data['wallet']['balance'],
            'Transactions': ';'.join(data['wallet']['transactions']),
            'PendingDepositAmount': data['pending_deposit']['amount'],
            'PendingDepositRefID': data['pending_deposit']['ref_id'],
            'PendingDepositStatus': data['pending_deposit']['status'],
            'PendingWithdrawalAmount': data['pending_withdrawal']['amount'],
            'PendingWithdrawalUPI': data['pending_withdrawal']['upi_id'],
            'PendingWithdrawalStatus': data['pending_withdrawal']['status']
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_excel('users_local.xlsx', index=False)

# Main menu
def show_main_menu(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎯 Quiz Zone", callback_data="quiz_zone"),
               telebot.types.InlineKeyboardButton("📚 Question Bank", callback_data="question_bank"))
    markup.add(telebot.types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
               telebot.types.InlineKeyboardButton("💰 Wallet", callback_data="wallet"))
    markup.add(telebot.types.InlineKeyboardButton("🎁 Invite", callback_data="refer"))
    bot.send_message(chat_id, "🎉 Welcome to the Quiz Bot!\nChoose an option:", reply_markup=markup)

# Command Handlers
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
        bot.send_message(message.chat.id, f"🎉 Welcome, {message.from_user.first_name}! Use /help for instructions.")
    else:
        bot.send_message(message.chat.id, f"🎉 Welcome back, {users[user_id]['name']}! Use /help for instructions.")
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
    ref_link = f"https://t.me/QuizBaaziZone?start={user_id}"
    bot.send_message(message.chat.id, f"🎁 Invite friends with this link to earn get bonus points:\n{ref_link}")

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
    user = users[user1711_id]
    profile_text = (
        f"👤 Profile\n"
        f"Name: {user['name']}\n"
        f"Username: @{user['username'] if user['username'] else 'Not set'}\n"
        f"Wallet Balance: ₹{user['wallet']['balance']}"
    )
    bot.send_message(message.chat.id, profile_text)

# Quiz Zone
def show_quiz_categories(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    categories = [
        ("🎓 Bihar Daroga", "Bihar Daroga"),
        ("👮 Bihar Police", "Bihar Police"),
        ("🚂 Railway", "Railway")
    ]
    for display, cat in categories:
        markup.add(telebot.types.InlineKeyboardButton(display, callback_data=f"qz_category_{cat}"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main"))
    bot.send_message(chat_id, "🎯 Select a Category:", reply_markup=markup)

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

# Question Bank
def show_question_bank_subjects(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    subjects = ['Current Affairs', 'Maths', 'Reasoning', 'English', 'GK/GS']
    for subject in subjects:
        markup.add(telebot.types.InlineKeyboardButton(subject, callback_data=f"qb_subject_{subject}"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main"))
    bot.send_message(chat_id, "📚 Select a Subject:", reply_markup=markup)

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
    current_set = users[user_id]['quiz_progress']['Question Bank']['GK/GS']
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

# Quiz Logic
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
    threading.Timer(time_limit, lambda: update_timer(chat_id, timer_msg.message_id, user_id, 0)).start()

def update_timer(chat_id, message_id, user_id, time_left):
    if user_id not in users or 'quiz' not in users[user_id] or not users[user_id]['quiz']['timer_active']:
        return
    if time_left <= 0:
        bot.edit_message_text("⏰ Time's up!", chat_id, message_id)
        next_question(chat_id, user_id, None)
    else:
        time_limit = 30 if users[user_id]['quiz']['section'] == 'Quiz Zone' else 60
        bot.edit_message_text(f"⏳ Timer: {time_left} seconds left", chat_id, message_id)
        threading.Timer(1, lambda: update_timer(chat_id, message_id, user_id, time_left - 1)).start()

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

# Wallet Handlers
@bot.callback_query_handler(func=lambda call: call.data == "wallet")
def wallet_menu(call):
    show_wallet_menu(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

def show_wallet_menu(chat_id, message_id=None):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("💰 Deposit", callback_data="wallet_deposit"),
               telebot.types.InlineKeyboardButton("💵 Withdraw", callback_data="wallet_withdraw"))
    markup.add(telebot.types.InlineKeyboardButton("📊 Balance", callback_data="wallet_balance"),
               telebot.types.InlineKeyboardButton("📜 History", callback_data="wallet_history"))
    markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main"))
    if message_id:
        bot.edit_message_text("💰 Wallet Options:", chat_id=chat_id, message_id=message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, "💰 Wallet Options:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "wallet_deposit")
def wallet_deposit(call):
    user_id = str(call.from_user.id)
    users = load_users()
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
    bot.send_message(
        call.message.chat.id,
        f"💰 Deposit:\n1. Send money to {UPI_ID}\n2. Reply with 'Amount RefID' (e.g., 100 Ref12345)."
    )
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_deposit, user_id)
    bot.answer_callback_query(call.id)

def process_deposit(message, user_id):
    users = load_users()
    try:
        amount, ref_id = message.text.strip().split()
        amount = float(amount)
        users[user_id]['pending_deposit'] = {'amount': amount, 'ref_id': ref_id, 'status': 'Pending'}
        bot.send_message(message.chat.id, f"✅ Deposit request (₹{amount}) with Ref: {ref_id} submitted. Awaiting admin verification.")
        save_users(users)
    except:
        bot.send_message(message.chat.id, "❌ Format: Amount RefID (e.g., 100 Ref12345)")
    show_wallet_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "wallet_withdraw")
def wallet_withdraw(call):
    user_id = str(call.from_user.id)
    users = load_users()
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
    bot.send_message(call.message.chat.id, "💵 Enter amount to withdraw (e.g., 50):")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_withdraw_amount, user_id)
    bot.answer_callback_query(call.id)

def process_withdraw_amount(message, user_id):
    users = load_users()
    try:
        amount = float(message.text)
        if amount <= 0 or amount > users[user_id]['wallet']['balance']:
            bot.send_message(message.chat.id, "❌ Invalid or insufficient amount!")
            show_wallet_menu(message.chat.id)
            return
        bot.send_message(message.chat.id, "💵 Enter your UPI ID (e.g., yourid@upi):")
        bot.register_next_step_handler_by_chat_id(message.chat.id, process_withdraw_upi, user_id, amount)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Enter a valid number!")
        show_wallet_menu(message.chat.id)

def process_withdraw_upi(message, user_id, amount):
    users = load_users()
    upi_id = message.text.strip()
    if "@" not in upi_id:
        bot.send_message(message.chat.id, "❌ Invalid UPI ID!")
        show_wallet_menu(message.chat.id)
        return
    users[user_id]['pending_withdrawal'] = {'amount': amount, 'upi_id': upi_id, 'status': 'Pending'}
    bot.send_message(message.chat.id, f"✅ Withdrawal request (₹{amount}) to {upi_id} submitted. Awaiting admin verification.")
    save_users(users)
    show_wallet_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "wallet_balance")
def wallet_balance(call):
    user_id = str(call.from_user.id)
    users = load_users()
    bot.edit_message_text(f"📊 Wallet Balance: ₹{users[user_id]['wallet']['balance']}", chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "wallet_history")
def wallet_history(call):
    user_id = str(call.from_user.id)
    users = load_users()
    history = users[user_id]['wallet']['transactions'][-10:]
    msg = "📜 Transaction History:\n" + "\n".join(history) if history else "📜 No transactions yet."
    bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)

# Profile Handler
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_callback(call):
    user_id = str(call.from_user.id)
    users = load_users()
    if user_id not in users:
        bot.send_message(call.message.chat.id, "❌ Please start the bot with /start first!")
        return
    user = users[user_id]
    profile_text = (
        f"👤 Profile\n"
        f"Name: {user['name']}\n"
        f"Username: @{user['username'] if user['username'] else 'Not set'}\n"
        f"Wallet Balance: ₹{user['wallet']['balance']}"
    )
    bot.edit_message_text(profile_text, chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)

# Back to Main Menu
@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    show_main_menu(call.message.chat.id)
    bot.answer_callback_query(call.id)

# Check Excel for updates
def check_excel_updates():
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

# Run bot
if __name__ == "__main__":
    users = load_users()
    threading.Thread(target=check_excel_updates).start()
    bot.polling(none_stop=True)
