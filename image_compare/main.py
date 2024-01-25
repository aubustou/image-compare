from __future__ import annotations

import argparse
import logging
import os
import random
from pathlib import Path

import chromadb  # Remplacez ceci par la bibliothèque client correcte pour ChromaDB
import numpy as np
import torch
from PIL import Image
from torchvision import models, transforms

logger = logging.getLogger(__name__)

CHROMADB_HOST = "pyramides.flu"
CHROMADB_PORT = 8000


def extract_features(model, preprocess, image_path: Path) -> np.ndarray:
    # Charger l'image
    image = Image.open(image_path).convert("RGB")
    image = preprocess(image)
    image = image.unsqueeze(0)  # Ajouter une dimension de batch

    # Pas de calcul de gradient nécessaire
    with torch.no_grad():
        # Obtenir les caractéristiques de l'image
        features = model(image)

    return features


def search(
    image_path: Path, model, preprocess, collection: chromadb.Collection, k: int
):
    # Extrait les caractéristiques de l'image cible dans A
    features_A = extract_features(model, preprocess, image_path)

    results = collection.query(
        query_embeddings=features_A.numpy().tolist(),
        n_results=k,
    )
    for id_ in results["ids"]:
        logger.info("Found %s", id_[0])


def push_to_chromadb(collection, features_list):
    for image_path, feature in features_list:
        feature_vector = feature.numpy().tolist()  # Convertir en liste (si nécessaire)

        # Insérer dans ChromaDB
        collection.add(image_path.name, feature_vector)


def get_features(model, preprocess, folder: Path, collection) -> None:
    features_list = []

    for index, filename in enumerate(folder.rglob("*.jpg")):
        if index % 100 == 0:
            logger.info("Extracted features for %s images", index)
            push_to_chromadb(collection, features_list)

            features_list = []

        try:
            features = extract_features(model, preprocess, filename)
        except Exception as e:
            logger.debug("Error while extracting features for %s: %s", filename, e)
            continue
        else:
            features_list.append((filename, features))

    push_to_chromadb(collection, features_list)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory", type=Path, help="Directory containing images to be inserted"
    )

    args = parser.parse_args()

    folder = args.directory

    logging.basicConfig(level=logging.INFO)

    # Charger le modèle pré-entraîné (ResNet dans cet exemple)
    model = models.resnet50(pretrained=True)
    model.eval()

    # Transformer pour prétraiter les images
    preprocess = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # Configuration de la connexion à ChromaDB
    client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT, ssl=False)
    try:
        collection = client.create_collection("bd-images")
    except Exception:
        collection = client.get_collection("bd-images")

    get_features(model, preprocess, folder, collection)

    # Recherche
    image_path = random.choice(list(folder.rglob("*.jpg")))
    search(image_path, model, preprocess, collection, 1)


if __name__ == "__main__":
    main()
