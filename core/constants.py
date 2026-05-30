import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

RECENT_FILES_PATH = os.path.join(DATA_DIR, "recent_files.json")
SETTINGS_PATH = os.path.join(DATA_DIR, "user_settings.json")
SESSION_PATH = os.path.join(DATA_DIR, "last_session.json")
BATCH_RESULTS_PATH = os.path.join(DATA_DIR, "batch_test_results.txt")
