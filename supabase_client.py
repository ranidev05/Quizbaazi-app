# supabase_client.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("https://nddygojvbhbekxwjhegj.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5kZHlnb2p2YmhiZWt4d2poZWdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM4NTE1ODIsImV4cCI6MjA1OTQyNzU4Mn0.CrwXQn0I7IIWv4uH5TfJCtyZqF8cb-4R4y7XQhAwp_4")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def initialize_database():
    """Initialize database tables if they don't exist"""
    # This would typically be done via migrations in a production app
    # Here we're providing an example of how to set up the tables programmatically
    
    try:
        # Create users table
        supabase.table("users").select("id").limit(1).execute()
        print("Users table exists")
    except Exception:
        print("Creating users table...")
        # SQL for creating users table would go here
        # In production, this would be handled through Supabase migrations
    
    # Similar checks for other tables...

def seed_sample_data():
    """Seed the database with sample data for testing"""
    # Create sample quiz categories
    categories = [
        {"name": "SSC", "description": "Staff Selection Commission Exams", "icon": "🏢"},
        {"name": "RRB", "description": "Railway Recruitment Board Exams", "icon": "🚂"},
        {"name": "Banking", "description": "Bank PO and Clerk Exams", "icon": "🏦"},
        {"name": "UPSC", "description": "Civil Services Exams", "icon": "🏛️"}
    ]
    
    for category in categories:
        # Check if category exists
        result = supabase.table("quiz_categories").select("*").eq("name", category["name"]).execute()
        if not result.data:
            # Insert category
            supabase.table("quiz_categories").insert(category).execute()
    
    # Create sample quiz subjects
    subjects = [
        {"name": "History", "description": "Indian and World History", "icon": "📜"},
        {"name": "Geography", "description": "Physical and Political Geography", "icon": "🌏"},
        {"name": "Economics", "description": "Micro and Macro Economics", "icon": "📊"},
        {"name": "Mathematics", "description": "Basic and Advanced Mathematics", "icon": "🔢"},
        {"name": "Reasoning", "description": "Logical and Analytical Reasoning", "icon": "🧠"}
    ]
    
    for subject in subjects:
        # Check if subject exists
        result = supabase.table("quiz_subjects").select("*").eq("name", subject["name"]).execute()
        if not result.data:
            # Insert subject
            supabase.table("quiz_subjects").insert(subject).execute()
    
    # Create sample quiz sets (more complex as it requires IDs from categories and subjects)
    # This would be expanded in a real application
