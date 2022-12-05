import requests
from bs4 import BeautifulSoup
import time
import argparse
import logging

logger = logging.getLogger()


def read_from_fs(file_name: str):
    with open(file_name, "r") as f:
        content = f.read()
    return BeautifulSoup(content, "html.parser")


def get_soup(url):
    return BeautifulSoup(requests.get(url).content, "lxml")


def extract_collection_infos(soup):
    list_albums = []
    for item in (
        soup.find("div", {"id": "wishlist-grid"})
        .find("ol")
        .find_all("li", {"class": "collection-item-container"})
    ):
        album_infos = item.find("a", {"class": "item-link"})
        collected = None
        album_name = album_infos.find(
            "div", {"class": "collection-item-title"}
        ).text.strip()
        try:
            collected = (
                item.find("div", {"class": "collected-by-header"})
                .find("a")
                .text.strip()
                .split(" ")[0]
            )
        except Exception as e:
            logger.warning(
                f"Couldn't extract number of collections for album {album_name}."
            )
        list_albums.append(
            {
                "artist": album_infos.find(
                    "div", {"class": "collection-item-artist"}
                ).text.strip()[4:],
                "name": album_name,
                "url": album_infos["href"],
                "collected": collected,
            }
        )
    return list_albums


def extract_album_infos(album):
    soup_album = get_soup(album["url"])
    digital_element = soup_album.find("li", {"class": "buyItem digital"})
    try:
        first_element = digital_element.find("span", {"base-text-color"}).text[1:]
        second_element = digital_element.find("span", {"buyItemExtra"}).text
        album["price"] = first_element
        album["currency"] = second_element
    except Exception as e:
        logger.warning(
            f"Couldn't extract price for {album.get('artist')} - {album.get('name')}. It might be free or name-your-price."
        )
    logger.info(
        f"Finished extracting infos for {album.get('artist')} - {album.get('name')} (price: {album.get('price')} {album.get('currency')})."
    )
    return album


def export_to_csv(list_items, file_name: str = "Export_bandcamp.csv"):
    with open(file_name, "w") as f:
        f.write("artist;name;url;collected;price;currency;\n")
        for i in list_items:
            f.write(
                f"{i.get('artist')};{i.get('name')};{i.get('url')};{i.get('collected')};{i.get('price')};{i.get('currency')};\n"
            )
    logger.debug("Export finished successfully.")


def main():
    args = parse_args()
    export_file_name = f"Export_bandcamp_{int(time.time())}.csv"
    soup = read_from_fs(args.file)
    list_albums = extract_collection_infos(soup)
    logger.info(f"Extracting infos for {len(list_albums)} albums.")

    list_albums_with_price = [extract_album_infos(album) for album in list_albums]
    logger.debug(list_albums_with_price)

    export_to_csv(list_albums_with_price, export_file_name)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert bandcamp collection into a CSV file."
    )
    parser.add_argument(
        "--debug",
        help="Display debugging information.",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
    )
    parser.add_argument(
        "--file",
        "-f",
        help="File containing bandcamp html data.",
        type=str,
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    return args


if __name__ == "__main__":
    main()
