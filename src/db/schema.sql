-- schema.sql
-- 数据库结构定义：五张表 + 一个视图
-- 由 load_json_to_sql.py 读取并执行

CREATE TABLE IF NOT EXISTS recipes (
    recipe_id TEXT PRIMARY KEY,
    source TEXT NOT NULL CHECK (
        source IN ('mom', 'ai_generated', 'user_submitted')
    ),
    name_zh TEXT NOT NULL,
    name_en TEXT NOT NULL,
    difficulty TEXT,
    servings INTEGER,
    is_standalone_dish BOOLEAN NOT NULL DEFAULT 1
);

CREATE VIEW IF NOT EXISTS verified_recipes AS 
    SELECT * FROM recipes
    WHERE source = 'mom';

CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id TEXT NOT NULL,
    name_zh TEXT NOT NULL,
    name_en TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id)
);

CREATE TABLE IF NOT EXISTS recipe_composition (
    parent_recipe_id TEXT NOT NULL,
    component_recipe_id TEXT NOT NULL,
    PRIMARY KEY (parent_recipe_id, component_recipe_id),
    FOREIGN KEY (parent_recipe_id) REFERENCES recipes(recipe_id),
    FOREIGN KEY (component_recipe_id) REFERENCES recipes(recipe_id)
);

CREATE TABLE IF NOT EXISTS recipe_tags (
    recipe_id TEXT NOT NULL,
    tag_zh TEXT NOT NULL,
    tag_en TEXT NOT NULL,
    PRIMARY KEY (recipe_id, tag_zh),
    FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id)
);

CREATE TABLE IF NOT EXISTS cooking_stages (
    recipe_id TEXT NOT NULL,
    stage_order INTEGER NOT NULL,
    tool_zh TEXT NOT NULL,
    tool_en TEXT NOT NULL,
    temperature_F INTEGER,
    heat_level_zh TEXT,
    heat_level_en  TEXT,
    duration_minutes INTEGER,
    notes_zh TEXT,
    PRIMARY KEY (recipe_id, stage_order),
    FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id)
);