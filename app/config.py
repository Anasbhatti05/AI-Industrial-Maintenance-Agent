import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv('APP_NAME', 'AI Industrial Maintenance Agent')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
MODEL_NAME = os.getenv('MODEL_NAME', 'openai/gpt-oss-20b')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
MANUALS_DIR = os.path.join(DATA_DIR, 'manuals')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
