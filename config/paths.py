from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
ITERIM_DATA_DIR = DATA_DIR / 'interim'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'

CONFIG_DIR = PROJECT_ROOT / 'config'

LOG_FILE = PROJECT_ROOT / 'logs' / 'func.log'

EXTRACTED_SUBMISSION_FOLDER = "Submissions"