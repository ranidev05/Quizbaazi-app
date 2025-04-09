# database_schema.py

"""
Supabase Database Schema for Quiz Bot

Tables:
1. users - Stores user information and wallet details
2. quiz_categories - Stores job categories like SSC, RRB
3. quiz_subjects - Stores subject categories like History, Geography
4. quiz_sets - Stores sets of questions
5. questions - Stores individual MCQ questions
6. user_attempts - Stores user quiz attempts
7. transactions - Stores wallet transactions
"""

# Users Table
"""
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR NOT NULL UNIQUE,
    username VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    wallet_balance DECIMAL(10,2) DEFAULT 0.0,
    invite_code VARCHAR UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

# Quiz Categories Table (for job-wise categories)
"""
CREATE TABLE quiz_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    icon VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

# Quiz Subjects Table (for subject-wise categories)
"""
CREATE TABLE quiz_subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    icon VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

# Quiz Sets Table
"""
CREATE TABLE quiz_sets (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES quiz_categories(id),
    subject_id INTEGER REFERENCES quiz_subjects(id),
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

# Questions Table
"""
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    quiz_set_id INTEGER REFERENCES quiz_sets(id),
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option CHAR(1) NOT NULL,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

# User Attempts Table
"""
CREATE TABLE user_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    quiz_set_id INTEGER REFERENCES quiz_sets(id),
    total_questions INTEGER,
    correct_answers INTEGER,
    wrong_answers INTEGER,
    unattempted INTEGER,
    total_time INTEGER, -- in seconds
    created_at TIMESTAMP DEFAULT NOW()
);
"""

# Transactions Table
"""
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL(10,2) NOT NULL,
    transaction_type VARCHAR NOT NULL, -- 'deposit', 'withdrawal'
    status VARCHAR NOT NULL, -- 'pending', 'completed', 'failed'
    reference_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);
"""
