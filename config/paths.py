from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
ITERIM_DATA_DIR = DATA_DIR / 'interim'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
TEMP_DATA_DIR = DATA_DIR  / 'temp'
Path(RAW_DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(ITERIM_DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(PROCESSED_DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(TEMP_DATA_DIR).mkdir(parents=True, exist_ok=True)

CONFIG_DIR = PROJECT_ROOT / 'config'

LOG_FILE = PROJECT_ROOT / 'logs' / 'func.log'

EXTRACTED_SUBMISSION_MASTER_FOLDER = "SUBMISSIONS"