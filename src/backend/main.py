
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

###### 1. FastAPI ######
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")
ADMIN_SECRET = os.environ["ADMIN_SECRET"]

from backend.agent import handle_query
from backend.tools import convert_temperature

from db.queries import get_connection, get_full_ingredients, get_cooking_stages

app = FastAPI()

###### 2. POST / query ######
class QueryRequest(BaseModel):
    question: str
    backend: str = "llama"

@app.post("/query")
def query(req: QueryRequest):
    answer = handle_query(req.question, backend_name=req.backend)
    return {"answer": answer}

class ConvertRequest(BaseModel):
    value: float
    from_unit: str

###### 3. Post / convert ######
@app.post("/convert")
def convert(req: ConvertRequest):
    result = convert_temperature(value=req.value, from_unit=req.from_unit)
    return {"result": result}

###### 4. GET / recipe ######
@app.get("/recipes")
def list_recipe():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT recipe_id, name_zh, name_en, difficulty, servings FROM verified_recipes")
    rows = cur.fetchall()

    recipes = []
    for r in rows:
        recipes.append({
            "recipe_id": r[0],
            "name_zh": r[1],
            "name_en": r[2],
            "difficulty": r[3],
            "servings": r[4],
        })

    return recipes

###### 5. GET / recipes / {id} ######
@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT name_zh, name_en, difficulty, servings FROM verified_recipes WHERE recipe_id = ?",
        (recipe_id, )
    )

    row = cur.fetchone()

    if row is None:
        return {"error": f"Recipe '{recipe_id}' not found"}

    ingredients = get_full_ingredients(conn=conn, recipe_id=recipe_id)
    cooking_stages = get_cooking_stages(conn=conn, recipe_id=recipe_id)

    return {
        "recipe_id": recipe_id,
        "name_zh": row[0],
        "name_en": row[1],
        "difficulty": row[2],
        "servings": row[3],
        "ingredients": ingredients,
        "cooking_stages": cooking_stages,
    }

###### 6. Post / recipes (admin key) ######
class RecipeInput(BaseModel):
    name_zh: str
    name_en: str
    difficulty: str = "easy"
    servings: int = 1
    
@app.post("/recipes")
def add_recipe(recipe: RecipeInput, x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="No permission. Only administrators are allowed to add recipes")

    return {"status": "recieved", "name_zh": recipe.name_zh}