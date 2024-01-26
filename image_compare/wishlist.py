from __future__ import annotations

import argparse
import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

URL = "https://www.bedetheque.com/ajax/import/id/{bd_id}/sens/Acheter"
WISHLIST_URL = "https://online.bdgest.com/wishlist?tri=datemod&sens=d&idf=&nf=&ids=&s=&t=&e=&ae=&c=&y=&ay=&o=&lang=&p=&ida=&a=&f=&p1=&p2=&p3=&p4=&et=&isbn=&dad=&daf=&dld=&dlf=&pmin=&pmax=&cmin=&cmax=&nmin=&nmax=&nummin=&nummax=&lu=&eo=&ded=&av=&i=&last=&l="

HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6",
    "Cookie": "cookie_message=1; INGRESSCOOKIE=c558ed41256d02c56575f7c9d3c3a86c|f933e2641e802ecbaaee5582d4f85af4; csrf_cookie_bel=c7abed00ca1cbcbdae3528cf040493cb; bdg_bedetheque_cookie=hef8ick4b9h1nsqh9fu2b7lkp4borcjt; bdg_bedetheque_autoconnect=1; bdg_bedetheque_id=359bb8f89f4f9e28df823a8829c15e056cdc7a0ec54a0816a556c3303edff0b5ebd890cdc7a9882c0dc73ec198c115c246737e0460714de125f513c250f75bd1ihi4SRWVeEZYitDe8%2FZJKPLhZdnf1j0k73wcoMD24Os%3D",
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
    "Cookie": "forum_bdgest_u=1; forum_bdgest_k=; forum_bdgest_sid=6e1eeafca38eed040a0719368f701210; INGRESSCOOKIE=ba6df1f627c3fcce28b7469edac61c48|5130ed5d34080472cdc487ca0a145b5c; bdg_online_autoconnect=1; bdg_online_id=393e6e44ffe17ce1ffc4e76ce0f95af0174f9a444eada14352f8060590736688f589929d9f28a2c73e5f77f91060a1c3d1b17e7e0486d5b543349baabd832cd1j1CTJFiUDivnYKt3%2BzGavgERFZV%2BrgsSjB1I3ojYOTA%3D; csrf_cookie_online=e462d2b8aaebebf1fdb06f94d4be4e1a; bdg_online_cookie=2si5cgh1oge6unf6ra812me1h4k001q8",
    "Referer": "https://online.bdgest.com/wishlist",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def add_to_wishlist(session: requests.Session, bd_id: int) -> None:
    response = session.get(URL.format(bd_id=bd_id), headers=HEADERS)
    response.raise_for_status()
    if "L'album a bien été ajouté à votre" in response.text:
        logger.info("Added %s", bd_id)


def get_series(session: requests.Session, bd_id: int) -> int:
    response = session.get(WISHLIST_URL, headers=BDGEST_HEADERS)
    response.raise_for_status()

    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")

    # Trouver le lien qui contient l'URL de la wishlist avec les identifiants de la série
    wishlist_link = None
    for link in soup.find_all("tr"):
        """<tr class="clic" data-cols="4" data-idalbum="42" id="ID-118"><td class="text-center couv tdc"><a class="zoom" href="https://www.bedetheque.com/media/Couvertures/achilletaloncouv40.JPG"><img src="https://www.bedetheque.com/cache/thb_couv/achilletaloncouv40.JPG"></img></a></td><td class="text-center couv tdc"><a class="zoom" href="https://www.bedetheque.com/media/Versos/achilletalon40v.jpg"><img src="https://www.bedetheque.com/cache/thb_versos/achilletalon40v.jpg"/></a></td><td class="info tdc"><img class="flag" src="https://www.bdgest.com/skin/flags/France.png" title="Europe - Franco-Belge"/><a class="module titre-serie" href="https://online.bdgest.com/wishlist?ids=33" title="Voir la série"><span class="bold">Achille Talon</span></a><br/><span class="semi-bold">                                                        40<span class="numa"></span>.                                Achille Talon et le monstre de l'Étang Tacule !<br/></span><ul class="infos"><li><label>Appreciation :</label><img class="appreciation" src="https://www.bdgest.com/skin/stars2/vide.png" title="Note : /10"/></li><li><label>Scénario :</label><a class="module" href="albums?ida=77">Greg</a></li><li><label>Dessin :</label><a class="module" href="albums?ida=77">Greg</a></li><li><label>Dépot légal :</label>11/1989                                                        </li><li><label>Planches :</label>46</li><li><label>Format :</label>Format normal</li><li><label>Editeur :</label><a class="module" href="albums?e=Dargaud">Dargaud</a></li></ul></td><td class="tdc"><div class="autre-info-album"><span class="coche"><i class="far fa-square"></i></span><ul class="infos"><li><label>Identifiants :</label>42 / -118                                                                </li><li><label>Achat le :</label>-</li><li><label>Prix :</label>-</li><li><label>ISBN :</label>2-205-03541-X</li><li><label>Etat :</label>Neuf</li><li><label>Cote :</label>non coté</li><li><label>Modifié le :</label>26/01/2024 01:39:56</li><li><label>Synchro le :</label>-</li><li><label>Autres infos :</label><i class="fas fa-star" title="Edition originale"></i><i class="far fa-bell" title="Alerte occasion sur cet album"></i></li></ul></div></td></tr>"""
        found_bd_id = int(link.get("data-idalbum"))
        if found_bd_id == bd_id:
            wishlist_link = link
            break
    else:
        raise ValueError("No wishlist link found")

    wishlist_link = soup.find("a", href=lambda h: h and "wishlist?ids=" in h)

    # Extraire l'identifiant de la série depuis l'URL
    serie_id = wishlist_link["href"].split("=")[-1]

    logger.info("Found series %s", serie_id)

    return int(serie_id)


def main():
    parser = argparse.ArgumentParser(description="Wishlist")
    parser.add_argument(
        "--bd_id",
        type=int,
        help="Add a new item to the wishlist",
        default=42,
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    bd_id = args.bd_id
    logger.info("Found %s", bd_id)

    with requests.Session() as session:
        add_to_wishlist(session, bd_id)
        series_id = get_series(session, bd_id)
        logger.info("Found series %s", series_id)


if __name__ == "__main__":
    main()
