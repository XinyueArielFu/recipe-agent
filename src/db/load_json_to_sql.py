###### 1. import & set directories ######
import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = BASE_DIR / "src" / "db" / "schema.sql"
JSON_PATH = BASE_DIR / "data" / "recipes.json"
DB_PATH = BASE_DIR / "data" / "recipes.db"

###### 2. Connect to db & read and execute schema.sql ######
# connect the entrance of the database
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;") # force to check foreign keys otherwise sqlite won't check
cur = conn.cursor()

schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
cur.executescript(schema_sql)
conn.commit() # have to safe the changes to db

###### 3.read json file ######
recipes_data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
print(f"Read total total of {len(recipes_data)} from {JSON_PATH}")

###### 4.0 DELETE ALL contents if run the script again ######
cur.execute("DELETE FROM ingredients;")
cur.execute("DELETE FROM recipe_tags;")
cur.execute("DELETE FROM recipe_composition;")
cur.execute("DELETE FROM cooking_stages;")
cur.execute("DELETE FROM recipes")
print(f"DELETE all tables")

###### 4. loop trough json and add each recipe data into recipes sql table ######
for recipe in recipes_data:
    cur.execute(
        """
        INSERT INTO recipes (
            recipe_id, source, name_zh, name_en, difficulty, servings, is_standalone_dish
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe["recipe_id"],
            recipe["source"],
            recipe["name_zh"],
            recipe["name_en"],
            recipe["difficulty"],
            recipe["servings"],
            recipe["is_standalone_dish"],
        )
    )

conn.commit()
print(f"Inserted {len(recipes_data)} rows into recipes table")

###### 5. insert data into ingredients (one-to-many) ######
for recipe in recipes_data:
    for ingredient in recipe["ingredients"]:
        cur.execute(
            """
            INSERT INTO ingredients (recipe_id, name_zh, name_en, amount, unit)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                recipe["recipe_id"],
                ingredient["name_zh"],
                ingredient["name_en"],
                ingredient["amount"],
                ingredient["unit"],
            )
        )

conn.commit()

cur.execute("SELECT COUNT(*) FROM ingredients")
ingredient_count = cur.fetchone()[0]
print(f"Inserted ingredients: Total ingredient rows: {ingredient_count}")

###### 6. insert zh & en tags into recipe_tags table ######
for recipe in recipes_data:
    for zh, en in zip(recipe["tags_zh"], recipe["tags_en"]):
        cur.execute(
            """
            INSERT INTO recipe_tags (recipe_id, tag_zh, tag_en)
            VALUES (?, ?, ?)
            """,
            (
                recipe["recipe_id"],
                zh,
                en,
            )
        )

conn.commit()

cur.execute("SELECT COUNT(*) FROM recipe_tags")
tags_count = cur.fetchone()[0]
print(f"Inserted recipe_tags: total {tags_count} rows")

###### 7. Insert components into recipe_composition table ######
for recipe in recipes_data:
    for component_id in recipe["components"]:
        cur.execute(
            """
            INSERT INTO recipe_composition (parent_recipe_id, component_recipe_id)
            VALUES (?, ?)
            """,
            (
                recipe["recipe_id"],
                component_id,
            )
        )

conn.commit()

cur.execute("SELECT COUNT(*) FROM recipe_composition")
component_count = cur.fetchone()[0]
print(f"Inserted recipe_composition: total {component_count} rows")

###### 8. Insert cooking stages into cooking_stages table ######
for recipe in recipes_data:
    for stage in recipe["cooking_stages"]:
         cur.execute(
            """
            INSERT INTO cooking_stages (recipe_id, stage_order, tool_zh, tool_en, temperature_F, heat_level_zh, heat_level_en, duration_minutes, notes_zh)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipe["recipe_id"],
                stage["stage_order"],
                stage["tool_zh"],
                stage["tool_en"],
                stage["temperature_F"], # JSON 的 null 会被自动转换成 Python 的 None
                stage["heat_level_zh"],
                stage["heat_level_en"],
                stage["duration_minutes"],
                stage["notes_zh"],
            )
        )
conn.commit()

cur.execute("SELECT COUNT(*) FROM cooking_stages")
count = cur.fetchone()[0]
print(f"Inserted cooking_stages: total {count} rows")

###### full recipie extract verification ######
# print("\n--- Verification: 芒果盒子 (R0800) ---")

# cur.execute("SELECT name_zh, name_en, source FROM recipes WHERE recipe_id = 'R0800'")
# print("Recipe:", cur.fetchone())

# cur.execute("SELECT name_zh, amount, unit FROM ingredients WHERE recipe_id = 'R0800'")
# print("Ingredients:", cur.fetchall())

# cur.execute("SELECT tag_zh, tag_en FROM recipe_tags WHERE recipe_id = 'R0800'")
# print("Tags:", cur.fetchall())

# cur.execute("SELECT component_recipe_id FROM recipe_composition WHERE parent_recipe_id = 'R0800'")
# print("Components:", cur.fetchall())

# cur.execute("SELECT stage_order, tool_zh, notes_zh FROM cooking_stages WHERE recipe_id = 'R0800' ORDER BY stage_order")
# print("Cooking stages:", cur.fetchall())

######  ######
######  ######
######  ######