import json
from pathlib import Path
from tqdm import tqdm

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent.parent
JSON_PATH = BASE_DIR / "data" / "recipes.json"
CHROMA_DIR = BASE_DIR / "chroma_db"

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
    print("\n--- Testing retrieval ---")
    results = search_recipe_notes("小酥肉怎么做", collection, model)
    for r in results:
        print(f"{r['recipe_id']} - {r['name_zh']} (distance: {r['distance']:.4f})")

#################### DEBUG #####################
# import numpy as np

# def cosine_sim(a, b):
#     a, b = np.array(a), np.array(b)
#     return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# name_query = model.encode("小酥肉").tolist()
# pork_song_text = model.encode("肉松小贝 pork song cake 将烤好的戚风纸杯蛋糕冷却后取出. 取两片纸杯蛋糕, 中间用蛋黄酱粘合, 再在表面均匀涂抹蛋黄酱沾满肉松即可 四寸戚风蛋糕配方放在cupcake大小的模具里, 烤制步骤和时间不变").tolist()
# crispy_pork_text = model.encode("小酥肉 crispy pork strips 1.猪肉洗干净切条, 加入适量蚝油, 五香粉, 盐, 腌制20分钟. 2.混合面粉和玉米淀粉加入鸡蛋搅拌至无颗粒面糊. 3.面糊中加入微微碾碎的花椒粒和白芝麻,搅拌均匀. 4.把腌制好的猪肉条裹上面糊. 5.分批次放入七成热的油锅中, 防止粘连 6.炸制表面微微金黄, 捞出控油, 再次放入油锅中炸至金黄酥脆即可").tolist()

# print("query'小酥肉' vs 小酥肉原文:", cosine_sim(name_query, crispy_pork_text))
# print("query'小酥肉' vs 肉松小贝原文:", cosine_sim(name_query, pork_song_text))
# print("小酥肉原文 vs 肉松小贝原文 (两段文字彼此的相似度):", cosine_sim(crispy_pork_text, pork_song_text))
######################

######  ######