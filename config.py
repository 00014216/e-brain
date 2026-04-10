import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL         = os.getenv('SUPABASE_URL', '')
SUPABASE_ANON_KEY    = os.getenv('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
ANTHROPIC_API_KEY    = os.getenv('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY       = os.getenv('OPENAI_API_KEY', '')
SECRET_KEY           = os.getenv('SECRET_KEY', 'dev-secret-key')

UPLOAD_FOLDER        = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS   = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_CONTENT_LENGTH   = 20 * 1024 * 1024
