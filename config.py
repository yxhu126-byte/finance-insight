import os
from dotenv import load_dotenv

load_dotenv()

# ========== API 配置 ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# ========== 模型配置 ==========
LLM_MODEL = "deepseek-chat"

# ========== 分块参数 ==========
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 4

# ========== 提取配置 ==========
MAX_EXTRACTION_CHARS = 30000

# ========== 异常检测阈值 ==========
EXPENSE_GROWTH_OVER_REVENUE_THRESHOLD = 10
PROFIT_CF_DIVERGENCE_THRESHOLD = 0

# ========== UI 配置 ==========
PAGE_TITLE = "财报深析 · AI金融分析工作台"
PAGE_ICON = "📊"
