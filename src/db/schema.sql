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