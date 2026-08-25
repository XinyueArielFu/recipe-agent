import json
from pathlib import Path
from tqdm import tqdm

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JSON_PATH = BASE_DIR / "data" / "recipes.json"
CHROMA_DIR = BASE_DIR / "chroma_db"

###### Testing retrieval ######
def search_recipe_notes(query, collection, model, n_results=3):
    query_with_instruction = "为这个句子生成表示以用于检索相关文章：" + query # library recomended prompt
    query_embedding = model.encode(query_with_instruction).tolist() # from np ndarry to python list

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    output = []
    for i in range(len(results["ids"][0])):
        output.append({
            "recipe_id": results["ids"][0][i],
            "name_zh": results["metadatas"][0][i]["name_zh"],
            "name_en": results["metadatas"][0][i]["name_en"],
            "document": results["documents"][0][i],
            "distance": results["distances"][0][i],
        })

    return output

if __name__ == "__main__":
    ###### 1. load embedding model ######
    print("Loading embedding model...")
    # model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
    print("Model loaded")

    ###### 2. read json & create chromadb and connection and collection ######
    recipes_data = json.loads(JSON_PATH.read_text(encoding='utf-8'))
    print(f"Read total of {len(recipes_data)} recipes")

    # create a "connection" with chromadb --> in order to interact with this database
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        client.delete_collection("mom_recipe_notes")
        print("Deleted old collection")
    except Exception:
        print("No existing collection to delete")

    collection = client.get_or_create_collection(
        name="mom_recipe_notes",
        metadata={"hnsw:space": "cosine"}
        )

    ###### 3. loop over json, filter out source == "mom" recipes only ######
    count = 0
    for recipe in tqdm(recipes_data, desc="Embedding recipes"):
        if recipe["source"] != "mom":
            continue

        text = recipe["name_zh"] + " " + recipe["name_en"] + " " + recipe["steps_description"] + " " + (recipe["notes"] or "")
        embedding = model.encode(text).tolist()

        collection.add(
            ids=[recipe["recipe_id"]],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "name_zh": recipe["name_zh"],
                "name_en": recipe["name_en"],
            }],
        )
        count += 1

    print(f"Embedded and stored {count} mom recipes")

    print("\n--- Testing retrieval ---")
    results = search_recipe_notes("小酥肉怎么做", collection, model)
    for r in results:
        print(f"{r['recipe_id']} - {r['name_zh']} (distance: {r['distance']:.4f})")
