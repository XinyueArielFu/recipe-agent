import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "recipes.db"

# get connection to db
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_full_ingredients(recipe_id, conn):
    """
    Get all ingradients of the current recipe
    Then get all sub-components' recipe's ingradients
    """
    cur = conn.cursor()

    cur.execute("SELECT name_zh, name_en, amount, unit FROM ingredients WHERE recipe_id = ?",
                (recipe_id, ))
    result = cur.fetchall()

    # sub-components
    cur.execute("SELECT component_recipe_id FROM recipe_composition WHERE parent_recipe_id = ?",
                (recipe_id, ))

    components = cur.fetchall()

    for (component_id, ) in components:
        cur.execute("SELECT name_zh, name_en, amount, unit FROM ingredients WHERE recipe_id = ?",
                    (component_id, ))
        result += cur.fetchall()
    return result

if __name__ == "__main__":
    conn = get_connection()
    ingredients = get_full_ingredients("R0800", conn)
    for row in ingredients:
        print(row)
