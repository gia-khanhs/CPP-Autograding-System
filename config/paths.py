from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# region data
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
# ITERIM_DATA_DIR = DATA_DIR / 'interim'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
TEMP_DATA_DIR = DATA_DIR  / 'temp'
Path(RAW_DATA_DIR).mkdir(parents=True, exist_ok=True)
# Path(ITERIM_DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(PROCESSED_DATA_DIR).mkdir(parents=True, exist_ok=True)
# Path(TEMP_DATA_DIR).mkdir(parents=True, exist_ok=True)
# endregion

# region output
OUTPUT_DIR = PROJECT_ROOT / 'output'
CORRECTED_CODE_DIR = OUTPUT_DIR / 'corrected_code'
GRADE_DIR = OUTPUT_DIR / 'scores'
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(CORRECTED_CODE_DIR).mkdir(parents=True, exist_ok=True)
Path(GRADE_DIR).mkdir(parents=True, exist_ok=True)
# endregion

CONFIG_DIR = PROJECT_ROOT / 'config'

LOG_FILE = PROJECT_ROOT / 'logs' / 'func.log'

EXTRACTED_SUBMISSION_MASTER_FOLDER = "SUBMISSIONS"