SYNTAX_PATH = "agents/tutor/c_tutor_all_vectorstores/c_tutor_syntax"
CONTROL_FLOW_PATH = "agents/tutor/c_tutor_all_vectorstores/c_tutor_control_flow"
DATA_STRUCTURES_PATH = "agents/tutor/c_tutor_all_vectorstores/c_tutor_data_structures"
FUNCTIONS_PATH = "agents/tutor/c_tutor_all_vectorstores/c_tutor_functions"
MEMORY_FILES_PATH = "agents/tutor/c_tutor_all_vectorstores/c_tutor_memory_files"

# Модель DeepSeek
MODEL_NAME = "deepseek-chat"
TEMPERATURE = 0.8
MAX_TOKENS = 2000

# API ключ DeepSeek
from config import Config

DEEPSEEK_API_KEY = Config.DEEPSEEK_API_KEY
