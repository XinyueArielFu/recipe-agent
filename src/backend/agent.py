import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from backend.llm_backend import get_backend
from backend.tools import tools, convert_temperature, query_recipe_sql, search_recipe_notes

TOOL_FUNCTIONS = {
    "convert_temperature": convert_temperature,
    "query_recipe_sql": query_recipe_sql,
    "search_recipe_notes": search_recipe_notes
}

