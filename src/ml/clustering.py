import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from sklearn.decomposition import PCA
from sklearn.metrics import davies_bouldin_score

###### 1. Load directories ######
BASE_DIR = Path(__file__).resolve().parent.parent.parent
JSON_PATH = BASE_DIR / "data" / "recipes.json"

recipes_data = json.loads(JSON_PATH.read_text(encoding='utf-8'))
print(f"Read total of {len(recipes_data)} recipes")

###### 2. ingredients features - TF-IDF ######
# TF := term frequency
# IDF := inverse document frequency

ingredient_texts = [
    " ".join(ingre["name_en"] for ingre in recipe["ingredients"])
        for recipe in recipes_data
]

vectorizer = TfidfVectorizer(max_features=40) # Create a TF-IDF vectorizer
X_ingredients = vectorizer.fit_transform(ingredient_texts).toarray()

print("Ingredient feature shape:", X_ingredients.shape)
print("Selected ingredient words:", vectorizer.get_feature_names_out())

###### 3. tags features ######
tags_lists = [recipe["tags_en"] for recipe in recipes_data]
mlb = MultiLabelBinarizer()
X_tags = mlb.fit_transform(tags_lists)

print("Tags feature shape:", X_tags.shape)
print("Selected tags:", mlb.classes_)

###### 4. stack ingredients feature and tags feature into one maxtrix ######
# X_ingredients (32×20)
# X_tags (32×55)
# --> became (32×75) horizontal stack
X = np.hstack([X_ingredients, X_tags])
print("Combined feature shape:", X.shape)

# KMeans training
kmeans = KMeans(n_clusters=2, random_state=123)
labels = kmeans.fit_predict(X)

# print("Cluster labels:", labels)

###### 5. recipe <--> KNN label ######
recipe_names = [recipe["name_zh"] for recipe in recipes_data]

clusters = {}
for name, label in zip(recipe_names, labels):
    clusters.setdefault(label, []).append(name)

for cluster_id in sorted(clusters.keys()):
    print(f"\nCluster {cluster_id}")
    for name in clusters[cluster_id]:
        print(f" - {name}")

###### 6. silhouette score ######
score = silhouette_score(X, labels=labels)
print(f"Silhouette score (n_clusters=2, max_features=40): {score:.4f}")

###### 7. PCA ######
pca = PCA(n_components=10)
X_reduced = pca.fit_transform(X)

kmeans_pca = KMeans(n_clusters=2, random_state=123)
labels_pca = kmeans_pca.fit_predict(X_reduced)

print("Full Dim — silhouette:", silhouette_score(X, labels))
print("Full Dim — Davies-Bouldin:", davies_bouldin_score(X, labels))
print("PCA — silhouette:", silhouette_score(X_reduced, labels_pca))
print("PCA — Davies-Bouldin:", davies_bouldin_score(X_reduced, labels_pca))

recipe_names = [recipe["name_zh"] for recipe in recipes_data]

clusters = {}
for name, label in zip(recipe_names, labels_pca):
    clusters.setdefault(label, []).append(name)

for cluster_id in sorted(clusters.keys()):
    print(f"\nCluster {cluster_id}")
    for name in clusters[cluster_id]:
        print(f" - {name}")
######  ######