from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import requests
from bedetheque_scraper.scraper import Serie
from bs4 import BeautifulSoup
from requests import HTTPError

logger = logging.getLogger(__name__)

URL = "https://www.bedetheque.com/ajax/import/id/{bd_id}/sens/Acheter"
WISHLIST_URL = "https://online.bdgest.com/wishlist?tri=datemod&sens=d&idf=&nf=&ids=&s=&t=&e=&ae=&c=&y=&ay=&o=&lang=&p=&ida=&a=&f=&p1=&p2=&p3=&p4=&et=&isbn=&dad=&daf=&dld=&dlf=&pmin=&pmax=&cmin=&cmax=&nmin=&nmax=&nummin=&nummax=&lu=&eo=&ded=&av=&i=&last=&l="

COOKIES = "cookie_message=1; bdg_bedetheque_autoconnect=1; bdg_bedetheque_id=359bb8f89f4f9e28df823a8829c15e056cdc7a0ec54a0816a556c3303edff0b5ebd890cdc7a9882c0dc73ec198c115c246737e0460714de125f513c250f75bd1ihi4SRWVeEZYitDe8%2FZJKPLhZdnf1j0k73wcoMD24Os%3D; INGRESSCOOKIE=660110c4d5a21683d4521550a53a5c0d|f933e2641e802ecbaaee5582d4f85af4; csrf_cookie_bel=045787c6385a905a207cec09b4b308ad; bdg_bedetheque_cookie=i45apkrmk9inkahc6n1dg1fnk9d8nfig"


BDGEST_COOKIES = "INGRESSCOOKIE=affc44dfd49814385250236695f8d69a|5130ed5d34080472cdc487ca0a145b5c; csrf_cookie_online=c26b3977bdd43c1036886253fe418392; csrf_cookie_bdg=51d32c66b5261c00d564607f02e7e578; cookie_message=1; bdg_bdgest_cookie=v2fodkssts8u6p37b5c1t9akp7rdh08n; forum_bdgest_u=82711; forum_bdgest_k=826e942d874d6167; forum_bdgest_sid=59cbc6a53588620a5ca4687c15fcbd6f; bdg_online_cookie=3v3ier0t5idegl3s5bai84sdt9ruolhs"

HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6",
    "Cookie": COOKIES,
    "Referer": "https://www.bedetheque.com/BD-Thorgal-Saga-Tome-1-Adieu-Aaricia-466304.html",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}
BDGEST_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6",
    "Cookie": BDGEST_COOKIES,
    "Referer": "https://online.bdgest.com/wishlist",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def add_to_wishlist(session: requests.Session, bd_id: int) -> bool:
    response = session.get(URL.format(bd_id=bd_id), headers=HEADERS)
    response.raise_for_status()
    if "L'album a bien été ajouté à votre" in response.text:
        logger.info("Added %s", bd_id)
        return True
    elif "Album <u>déja présent</u>" in response.text:
        logger.info("Already present %s", bd_id)
        return True
    else:
        logger.error("Error while adding %s: %s", bd_id, response.text)
        return False


def get_series(session: requests.Session, bd_id: int) -> Serie:
    response = session.get(WISHLIST_URL, headers=BDGEST_HEADERS)
    response.raise_for_status()

    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")

    # Trouver le lien qui contient l'URL de la wishlist avec les identifiants de la série
    wishlist_link = None
    series_title = None

    for link in soup.find_all("tr"):
        """<tr class="clic" data-cols="4" data-idalbum="42" id="ID-118"><td class="text-center couv tdc"><a class="zoom" href="https://www.bedetheque.com/media/Couvertures/achilletaloncouv40.JPG"><img src="https://www.bedetheque.com/cache/thb_couv/achilletaloncouv40.JPG"></img></a></td><td class="text-center couv tdc"><a class="zoom" href="https://www.bedetheque.com/media/Versos/achilletalon40v.jpg"><img src="https://www.bedetheque.com/cache/thb_versos/achilletalon40v.jpg"/></a></td><td class="info tdc"><img class="flag" src="https://www.bdgest.com/skin/flags/France.png" title="Europe - Franco-Belge"/><a class="module titre-serie" href="https://online.bdgest.com/wishlist?ids=33" title="Voir la série"><span class="bold">Achille Talon</span></a><br/><span class="semi-bold">                                                        40<span class="numa"></span>.                                Achille Talon et le monstre de l'Étang Tacule !<br/></span><ul class="infos"><li><label>Appreciation :</label><img class="appreciation" src="https://www.bdgest.com/skin/stars2/vide.png" title="Note : /10"/></li><li><label>Scénario :</label><a class="module" href="albums?ida=77">Greg</a></li><li><label>Dessin :</label><a class="module" href="albums?ida=77">Greg</a></li><li><label>Dépot légal :</label>11/1989                                                        </li><li><label>Planches :</label>46</li><li><label>Format :</label>Format normal</li><li><label>Editeur :</label><a class="module" href="albums?e=Dargaud">Dargaud</a></li></ul></td><td class="tdc"><div class="autre-info-album"><span class="coche"><i class="far fa-square"></i></span><ul class="infos"><li><label>Identifiants :</label>42 / -118                                                                </li><li><label>Achat le :</label>-</li><li><label>Prix :</label>-</li><li><label>ISBN :</label>2-205-03541-X</li><li><label>Etat :</label>Neuf</li><li><label>Cote :</label>non coté</li><li><label>Modifié le :</label>26/01/2024 01:39:56</li><li><label>Synchro le :</label>-</li><li><label>Autres infos :</label><i class="fas fa-star" title="Edition originale"></i><i class="far fa-bell" title="Alerte occasion sur cet album"></i></li></ul></div></td></tr>"""
        found_bd_id = int(link.get("data-idalbum"))
        if found_bd_id == bd_id:
            wishlist_link = link
            series_title = link.find("span", class_="bold").text
            break
    else:
        raise ValueError("No wishlist link found")

    wishlist_link = soup.find("a", href=lambda h: h and "wishlist?ids=" in h)

    # Extraire l'identifiant de la série depuis l'URL
    serie_id = wishlist_link["href"].split("=")[-1]

    logger.info("Found series %s", serie_id)

    return Serie(id=int(serie_id), title=series_title.strip(), url="")


def get_series_from_wishlist(bd_ids: list[int]) -> set[Serie]:
    series = set()

    with requests.Session() as session:
        for bd_id in bd_ids:
            try:
                if add_to_wishlist(session, bd_id):
                    series.add(get_series(session, bd_id))
                    logger.info("Found series %s", series)
            except Exception as exc:
                logger.error("Error while processing %s: %s", bd_id, exc)
            finally:
                time.sleep(0.1)
                with Path("found.json").open("w") as file:
                    json.dump(
                        [{"id": x.id, "title": x.title, "url": x.url} for x in series],
                        file,
                        indent=4,
                    )

    return series


THUMBNAILS_FOLDER = Path(r"M:\Bédés\thumbnails")
WISHLIST_PAGINATED_URL = (
    "https://online.bdgest.com/wishlist?tri=datemod&sens=d&page={page}"
)


def get_covers_from_wishlist(bd_ids: list[int]) -> list[tuple[int, str]]:
    with requests.Session() as session:
        covers = []
        existing_bd_ids = set(bd_ids)

        # 200 results per page
        for page in range(1, len(bd_ids) // 200 + 2):
            logger.info("Page %s", page)
            response = session.get(
                WISHLIST_PAGINATED_URL.format(page=page), headers=BDGEST_HEADERS
            )
            response.raise_for_status()

            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")

            # For all <tr> tags, get url from <td class="text-center couv tdc">
            # and add to list

            for link in soup.find_all("tr"):
                found_bd_id = int(link.get("data-idalbum"))
                if found_bd_id in existing_bd_ids:
                    cover_link = link.find("td", class_="text-center couv tdc").find(
                        "a"
                    )
                    covers.append((found_bd_id, cover_link["href"]))

        return covers


def main():
    parser = argparse.ArgumentParser(description="Wishlist")
    parser.add_argument(
        "--bd-ids",
        type=int,
        nargs="+",
        help="Add a new item to the wishlist",
        default=[42],
    )
    parser.add_argument(
        "--folders",
        type=Path,
        help="Folder to add to the wishlist",
        nargs="+",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    bd_ids = args.bd_ids

    if args.folders:
        bd_ids = sorted(
            [
                int(x.stem)
                for y in args.folders
                for x in y.rglob("*.jpg")
                if x.stat().st_size < 10
            ]
        )
    elif not bd_ids:
        raise ValueError("No bd_ids or folder")

    logger.info("Found %s", bd_ids)

    series = get_series_from_wishlist(bd_ids)

    logger.info("Found %s", series)

    urls = get_covers_from_wishlist(bd_ids)

    logger.info("Found %s", urls)

    for bd_id, url in urls:
        logger.info("Downloading %s", url)
        response = requests.get(url)
        try:
            response.raise_for_status()
        except HTTPError:
            logger.error("Error while downloading %s: %s", url, response.text)
            continue

        sub_folder = THUMBNAILS_FOLDER / str(bd_id).zfill(6)[:3]
        sub_folder.mkdir(parents=True, exist_ok=True)

        with (sub_folder / f"{bd_id}.jpg").open("wb") as file_:
            file_.write(response.content)


if __name__ == "__main__":
    main()
