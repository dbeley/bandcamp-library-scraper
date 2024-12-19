import requests
from bs4 import BeautifulSoup
import time
import argparse
import logging
import itertools
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

logger = logging.getLogger()


def read_soup_from_fs(filename: str):
    with open(filename, "r") as f:
        content = f.read()
    return BeautifulSoup(content, "html.parser")


def get_soup(driver, url):
    driver.get(url)
    time.sleep(1)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "lxml")
    return soup


def extract_wishlist(soup):
    list_albums = []
    for item in (
        soup.find("div", {"id": "wishlist-grid"})
        .find("ol")
        .find_all("li", {"class": "collection-item-container"})
    ):
        album_infos = item.find("a", {"class": "item-link"})
        album_name = album_infos.find(
            "div", {"class": "collection-item-title"}
        ).text.strip()
        collected = None
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


def extract_following(soup):
    list_artists = []
    for item in (
        soup.find("div", {"id": "following-bands-container"})
        .find("ol")
        .find_all("li", {"class": "following"})
    ):
        artist_infos = item.find("div", {"class": "fan-info-inner"})
        list_artists.append(
            {
                "name": artist_infos.find("a", {"class": "fan-username"}).text,
                "url": artist_infos.find("a", {"class": "fan-username"})["href"],
                "location": artist_infos.find("div", {"class": "fan-location"}).text,
            }
        )
    return list_artists


def extract_collection(soup):
    list_albums = []
    for item in (
        soup.find("div", {"id": "collection-items"})
        .find("ol", {"class": "collection-grid"})
        .find_all("li", {"class": "collection-item-container"})
    ):
        album_infos = item.find("div", {"class": "collection-title-details"})
        artist_name = album_infos.find(
            "div", {"class": "collection-item-artist"}
        ).text.strip()[4:]
        collected = None
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
                "artist": artist_name,
                "name": album_infos.find("div", {"class": "collection-item-title"})
                .text.strip()
                .split("\n")[0],
                "url": album_infos.find("a", {"class": "item-link"})["href"],
                "collected": collected,
            }
        )
    return list_albums

def get_package_element_data(element):
    name = element.find("span", {"buyItemPackageTitle"}).text
    price = element.find("span", {"base-text-color"}).text[1:]
    currency = element.find("span", {"buyItemExtra"}).text
    return {
      "name": name,
      "price": price,
      "currency": currency
      }


def get_merch_type(merch_type):
    if "t-shirt" in merch_type.lower():
        return "t-shirt"
    elif "cassette" in merch_type.lower():
        return "cassette"
    elif "vinyl" in merch_type.lower():
        return "vinyl"
    return None




def extract_album_infos(driver, album):
    try:
        soup_album = get_soup(driver, album["url"])
    except Exception as e:
        logger.warning(f"Couldn't extract information for release {album['artist']} - {album['name']: {e}}")
        return album
    digital_element = soup_album.find("li", {"class": "buyItem digital"})
    try:
        album["price"] = digital_element.find("span", {"base-text-color"}).text[1:]
        album["currency"] = digital_element.find("span", {"buyItemExtra"}).text
    except Exception as e:
        logger.warning(
            f"Couldn't extract digital price for {album.get('artist')} - {album.get('name')}. It might be free or name-your-price."
        )

    index_tshirt = 1
    index_cassette = 1
    index_vinyl = 1
    for package_element in soup_album.find_all("li", {"class": "buyItem"}):
        if merch_type_element := package_element.find("div", {"merchtype"}):
            merch_type = merch_type_element.text.strip()
            logger.debug("Found merch type %s", merch_type)
            if any(item in merch_type.lower() for item in ["t-shirt", "cassette", "vinyl"]):
                if package_element.find("h4", {"class": "notable"}):
                    album[f"vendibles_sold_out"] = True
                else:
                    element_data = get_package_element_data(package_element)
                    simple_merch_type = get_merch_type(merch_type)
                    if simple_merch_type:
                        if simple_merch_type == "t-shirt":
                            index = index_tshirt
                            index_tshirt += 1
                        elif simple_merch_type == "cassette":
                            index = index_cassette
                            index_cassette +=1
                        else:
                            index = index_vinyl
                            index_vinyl +=1
                        album[f"vendibles_{simple_merch_type}_{index}_type"] = merch_type
                        album[f"vendibles_{simple_merch_type}_{index}_name"] = element_data.get("name")
                        album[f"vendibles_{simple_merch_type}_{index}_price"] = element_data.get("price")
                        album[f"vendibles_{simple_merch_type}_{index}_currency"] = element_data.get("currency")
                        if remaining := package_element.find("span", {"notable"}):
                            album[
                                f"vendibles_{simple_merch_type}_{index}_remaining"
                            ] = remaining.text.strip().split()[0]
    logger.info(
        f"Finished extracting infos for {album.get('artist')} - {album.get('name')} (price: {album.get('price')} {album.get('currency')})."
    )
    return album


def extract_discography(driver, artist):
    soup_artist = get_soup(driver, artist["url"] + "music")
    list_albums = []
    try:
        for item in (
            soup_artist.find("div", {"class": "leftMiddleColumns"})
            .find("ol", {"id": "music-grid"})
            .find_all("li", {"class": "music-grid-item"})
        ):
            album_element = item.find("p", {"class": "title"})
            album_name = album_element.text.strip()
            alternate_artist = None
            if alternate_element := album_element.find(
                "span", {"class": "artist-override"}
            ):
                logger.debug(
                    f"Trying to parse alternate artist name in {album_element}"
                )
                album_name = album_name.split("\n")[0]
                alternate_artist = alternate_element.text.strip()
                logger.debug(f"Found {alternate_artist}")
            url = item.find("a")["href"]
            list_albums.append(
                {
                    "artist": artist["name"],
                    "alternate_artist": alternate_artist,
                    "name": album_name,
                    "url": url if url.startswith("https://") else artist["url"] + url,
                }
            )
        return [extract_album_infos(driver, album) for album in list_albums]
    except Exception as e:
        logger.warning(
            f"Couldn't extract informations for artist {artist['name']}: {e}"
        )
        return []


def export_to_csv(list_items, filename: str):
    with open(filename, "w", encoding="utf8", newline="") as output_file:
        fc = csv.DictWriter(
            output_file, fieldnames=sorted(set().union(*(d.keys() for d in list_items)))
        )
        fc.writeheader()
        fc.writerows(list_items)

def init_driver():
    # Setup Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no GUI)
    options.add_argument('--disable-gpu')  # Disable GPU acceleration
    options.add_argument('--no-sandbox')  # Bypass OS security model (Linux only)
    options.add_argument('start-maximized')  # Start browser maximized
    options.add_argument('disable-infobars')  # Disable infobars
    options.add_argument("--disable-extensions")  # Disable extensions
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

    # Provide the path to the chromedriver executable
    # service = ChromeService(executable_path='/path/to/chromedriver')

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=options)
    return driver


def main():
    args = parse_args()
    soup = read_soup_from_fs(args.file)
    driver = None
    if args.type == "wishlist":
        driver = init_driver()
        list_wishlist = extract_wishlist(soup)
        logger.info(f"Extracting infos for {len(list_wishlist)} albums in wishlist.")

        list_wishlist_with_price = [
            extract_album_infos(driver, album) for album in list_wishlist
        ]
        logger.debug(list_wishlist_with_price)

        export_filename = f"export_bandcamp_wishlist_{int(time.time())}.csv"
        export_to_csv(list_wishlist_with_price, export_filename)
    elif args.type == "artists":
        list_artists = extract_following(soup)
        logger.info(f"Extracting infos for {len(list_artists)} followed artists.")
        export_filename = f"export_bandcamp_artists_{int(time.time())}.csv"
        export_to_csv(list_artists, export_filename)
    elif args.type == "discography":
        driver = init_driver()
        list_artists = extract_following(soup)
        logger.info(
            f"Extracting discography infos for {len(list_artists)} followed artists."
        )
        export_filename = f"export_bandcamp_discography_{int(time.time())}.csv"

        list_albums_with_price = [
            extract_discography(driver, artist) for artist in list_artists
        ]
        flattened_albums_list = list(
            itertools.chain.from_iterable(list_albums_with_price)
        )
        export_to_csv(flattened_albums_list, export_filename)
    elif args.type == "collection":
        list_albums = extract_collection(soup)
        logger.info(f"Extracting infos for {len(list_albums)} albums in collection.")
        export_filename = f"export_bandcamp_collection_{int(time.time())}.csv"
        export_to_csv(list_albums, export_filename)
    else:
        logger.warning(
            f"Type {args.type} is not supported. Choose one of wishlist, artists, discography or collection."
        )
    if driver:
        driver.quit()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export your bandcamp collection into a CSV file."
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
        required=True,
    )
    parser.add_argument(
        "--type",
        "-t",
        help="Type of data to extract (choices: wishlist, artists, collection, discography. default: wishlist)",
        type=str,
        default="wishlist",
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    return args


if __name__ == "__main__":
    main()
