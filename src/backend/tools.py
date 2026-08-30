import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
CHROMA_DIR = BASE_DIR / "chroma_db"

from db.queries import get_connection, get_full_ingredients, get_cooking_stages

from vector_store.build_vector_db import search_recipe_notes as _search_recipe_notes
from sentence_transformers import SentenceTransformer
import chromadb

_model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _client.get_collection("mom_recipe_notes")

####### 1. convert temperature F <--> C ############
def convert_temperature(value: float, from_unit: str) -> float:
    value = float(value)
    if from_unit.upper() == "F":
        return round((value - 32) * 5 / 9, 0) 
    elif from_unit.upper() == "C":
        return round(value * 9 / 5 + 32, 0)
    else:
        raise ValueError(f"Unknown unit: {from_unit}. Use 'F' or 'C'.")

# print(convert_temperature(212, "f"))

####### 2. query_recipe_sql ############
def query_recipe_sql(recipe_name: str, field: str) -> str:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT recipe_id FROM verified_recipes WHERE name_zh = ? OR name_en = ?",
        (recipe_name, recipe_name))
    row = cur.fetchone()
    if row is None:
        return f"Recipe '{recipe_name}' not found."

    recipe_id = row[0]
    if field == "ingredients":
        result = get_full_ingredients(recipe_id, conn)
        return str(result)
    elif field == "cooking_stages":
        result = get_cooking_stages(recipe_id, conn)
        return str(result)
    else:
        return f"Unknown field: {field}. Use 'ingredients' or 'cooking_stages'."

####### 3. search_recipe_notes ############
def search_recipe_notes(query: str, n_results: int = 3) -> str:
    results = _search_recipe_notes(query, _collection, _model, n_results)
    output = []
    for r in results:
        output.append(f"{r['name_zh']} ({r['name_en']}): {r['document']}")
    return "\n".join(output)


####### 4. tool schemas (manual for LLM) ############
### Anthropic Claude API format
tools = [
    {
        "name": "convert_temperature",
        "description": "convert temperature between Celsius and Fahrenheit",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {"type": "number", "description": "value of temperature to convert"},
                "from_unit": {"type": "string", "description": "Original units: 'F' represents Fahrenheit, 'C' represents Celsius"}
            },
            "required": ["value", "from_unit"]
        }
    },
    {
        "name": "query_recipe_sql",
        "description": "Query exact structured data about a recipe, such as ingredient amounts or cooking stage temperature/duration. Use this when the user asks for precise numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recipe_name": {"type": "string", "description": "Name of the recipe, in Chinese or English"},
                "field": {"type": "string", "description": "Either 'ingredients' or 'cooking_stages'"}
            },
            "required": ["recipe_name", "field"]
        }
    },
    {
        "name": "search_recipe_notes",
        "description": "Semantically search recipe step-by-step instructions and notes. Use this when the user asks how to make a dish or wants detailed cooking steps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The user's question, used for semantic search"}
            },
            "required": ["query"]
        }
    },
]

if __name__ == "__main__":
    print(query_recipe_sql("椰子冻", "cooking_stages"))
    print(search_recipe_notes("椰子冻怎么做"))





