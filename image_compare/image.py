from __future__ import annotations

import argparse
import json
import logging
import zipfile
from pathlib import Path
from typing import TypedDict

import chromadb
import numpy as np
import requests
import torch
from PIL import Image
from torchvision import models, transforms

from bedetheque_scraper.main import add_file_to_zip
from bedetheque_scraper.scraper import get_album_info, get_albums

from .wishlist import add_to_wishlist, get_series

logger = logging.getLogger(__name__)

CHROMADB_HOST = "pyramides.flu"
CHROMADB_PORT = 8000


def extract_features(model, preprocess, image_path: Path) -> np.ndarray:
    # Charger l'image
    if image_path.suffix == ".zip":
        image = open_zip_file(image_path)
    else:
        image = Image.open(image_path).convert("RGB")
    image = preprocess(image)
    image = image.unsqueeze(0)  # Ajouter une dimension de batch

    # Pas de calcul de gradient nécessaire
    with torch.no_grad():
        # Obtenir les caractéristiques de l'image
        features = model(image)

    return features


class SearchResults(TypedDict):
    ids: list[list[str]]
    distances: list[list[float]]
    embeddings: list[list[float]]
    metadata: list[list[str]]


def search(
    image_path: Path, model, preprocess, collection: chromadb.Collection, k: int
) -> SearchResults:
    logger.info("Searching for %s", image_path)

    # Extrait les caractéristiques de l'image cible dans A
    features_A = extract_features(model, preprocess, image_path)

    results = collection.query(
        query_embeddings=features_A.numpy().tolist(),
        n_results=k,
    )
    for id_ in results["ids"][0]:
        logger.info("Found %s", id_[0])

    return results


def push_to_chromadb(collection, features_list):
    for image_path, feature in features_list:
        feature_vector = feature.numpy().tolist()  # Convertir en liste (si nécessaire)

        # Insérer dans ChromaDB
        collection.add(image_path.name, feature_vector)


def get_features(model, preprocess, folder: Path, collection) -> None:
    features_list: list[tuple[Path, torch.Tensor]] = []

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


def open_zip_file(zip_file: Path) -> Image.Image:
    """Get the cover image from a zip file."""
    with zipfile.ZipFile(zip_file) as z:
        for filename in z.namelist():
            if filename.endswith(".jpg"):
                with z.open(filename) as f:
                    return Image.open(f).convert("RGB")

    raise ValueError("No image found in zip file")


def login_to_bedetheque(session: requests.Session) -> None:
    """Login to bedetheque.com."""
    with Path("credentials.json").open() as f:
        credentials = json.load(f)

    data = {
        "redirect": "https://www.bdgest.com/preview-4012-BD-la-guerre-des-amazones-recit-complet.html",
        "autologin": 1,
        "login": "Connexion",
        "username": credentials["login"],
        "password": credentials["password"],
    }
    response = session.post(
        "https://www.bdgest.com/forum/ucp.php?mode=login", data=data
    )
    response.raise_for_status()

    logger.info("Logged in bedetheque")


def login_to_bdgest(session: requests.Session) -> None:
    """Login to bedetheque.com."""
    with Path("credentials.json").open() as f:
        credentials = json.load(f)

    breakpoint()

    data = {
        "csrf_token_bdg": session.cookies["csrf_cookie_bdg"],
        "li1": "username",
        "li2": "password",
        "source": "",
        "username": credentials["login"],
        "password": credentials["password"],
        "auto_connect": "on",
    }
    response = session.post(
        "https://online.bdgest.com/login", data=data, headers=BDGEST_HEADERS
    )

    response.raise_for_status()

    logger.info("Logged in bdgest")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory", type=Path, help="Directory containing images to be inserted"
    )
    parser.add_argument(
        "--generate", action="store_true", help="Generate features for images"
    )
    parser.add_argument("input", type=Path, help="Image to search for")
    parser.add_argument("-k", type=int, help="Number of results to return", default=1)
    parser.add_argument(
        "--distance-cutoff",
        type=int,
        help="Maximum distance between image and result",
        default=2000,
    )
    parser.add_argument("--show", action="store_true", help="Show results in a window")
    parser.add_argument("--recursive", action="store_true", help="Search recursively")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    folder = args.directory
    distance_cutoff = args.distance_cutoff

    if (inputs := args.input).is_file():
        input_files = [inputs]
    elif args.recursive:
        input_files = list(inputs.rglob("*.zip"))
    else:
        input_files = list(inputs.glob("*.zip"))

    model, preprocess = init_model()
    collection = get_collection()

    if args.generate:
        get_features(model, preprocess, folder, collection)

    for input_file in input_files:
        try:
            do(
                input_file=input_file,
                model=model,
                preprocess=preprocess,
                collection=collection,
                folder=folder,
                k=args.k,
                distance_cutoff=distance_cutoff,
                show=args.show,
            )
        except Exception as e:
            logger.error("Error while processing %s: %s", input_file, e)
            continue


def do(
    input_file: Path,
    model: torch.nn.Module,
    preprocess: transforms.Compose,
    collection: chromadb.Collection,
    folder: Path,
    k: int,
    distance_cutoff: int,
    show: bool = False,
):
    results = execute_search(
        model=model,
        preprocess=preprocess,
        collection=collection,
        folder=folder,
        image_path=input_file,
        k=k,
        distance_cutoff=distance_cutoff,
        show=show,
    )

    if not results:
        logger.warning("No results found for %s", input_file)
        return

    bd_id = int(results[0]["id"].removesuffix(".jpg").zfill(6))
    logger.info("Found BD %s", bd_id)

    with requests.Session() as session:
        # session.headers = BDGEST_HEADERS
        # login_to_bedetheque(session)
        # login_to_bdgest(session)

        add_to_wishlist(session, bd_id)
        series = get_series(session, bd_id)
        logger.info("Found BD %s from series %s", bd_id, series)

        albums = get_albums(series, session, bd_id)
        logger.info("Found albums %s", albums)
        for album in albums:
            if infos := get_album_info(album, session):
                logger.info("Found info %s", infos)

        add_file_to_zip(input_file, album, overwrite=True)


def init_model():
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

    return model, preprocess


def get_collection(name: str = "bd-images") -> chromadb.Collection:
    # Configuration de la connexion à ChromaDB
    client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT, ssl=False)
    try:
        collection = client.create_collection(name)
    except Exception:
        collection = client.get_collection(name)

    return collection


class EndResult(TypedDict):
    id: str
    distance: float
    embedding: list[float] | None
    metadata: str | None


def execute_search(
    model: torch.nn.Module,
    preprocess: transforms.Compose,
    collection: chromadb.Collection,
    folder: Path,
    image_path: Path,
    k: int,
    distance_cutoff: int,
    show: bool = False,
) -> list[EndResult]:
    results = search(image_path, model, preprocess, collection, k)

    # Afficher les résultats
    end_results = []

    for index, id_ in enumerate(results["ids"][0]):
        logger.info("Found %s", id_)
        logger.info("Distance: %s", results["distances"][0][index])
        if results["distances"][0][index] > distance_cutoff:
            logger.warning("Distance too high, skipping")
            continue
        end_results.append(
            EndResult(
                id=id_,
                distance=results["distances"][0][index],
                embedding=results["embeddings"][0][index]
                if results["embeddings"]
                else None,
                metadata=results["metadata"][0][index]
                if results.get("metadata")
                else None,
            )
        )

        if show:
            Image.open(folder / id_.removesuffix(".jpg").zfill(6)[:3] / id_).show()

    return end_results


if __name__ == "__main__":
    main()
