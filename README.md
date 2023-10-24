# bandcamp-library-scraper

Export your bandcamp library into a csv file.

This script does not download audio files, only metadata.

It can extract any of those data:

- collection (all the albums you own)
- wishlist (all the albums in your wishlist)
- artists (basic information about the artists you follow)
- discography (all the albums from all the artists you follow - might take a long time to extract)

# Usage

- Go to your bandcamp profile in your web browser (i.e. "https://bandcamp.com/dbeley/wishlist")
- Go to the tab you want to extract data from
- Click on "see more" and scroll down until all the elements are loaded

Note: you can load all the different tabs at once in order to have all the information on the same file

- Save the page in the same folder as this script

Note: to do that properly you will have to export the generated html (example on Firefox: right click > inspect the page, right click on the `<html ...>` tag at the top of the page, copy > inner HTML, then paste this into a new file).


```
python bandcamp-library-scraper.py -f bandcamp-library-export.html -t collection
python bandcamp-library-scraper.py -f bandcamp-library-export.html -t wishlist
python bandcamp-library-scraper.py -f bandcamp-library-export.html -t artists
python bandcamp-library-scraper.py -f bandcamp-library-export.html -t discography
```

## Dependencies

- python
- requests
- bs4
- lxml

## Installation

```
git clone https://github.com/dbeley/bandcamp-library-scraper
cd bandcamp-library-scraper
pip install -r requirements.txt
python bandcamp-library-scraper.py -h
```

## Fields extracted

### collection / wishlist / discography

- artist name
- alternate artist (only for discography)
- album name
- number of collections in (only for wishlist and collection)
- price and currency for the digital release (only for wishlist and discography)
- price and currency for cassette release (only for wishlist and discography)
- price and currency for vinyl release (only for wishlist and discography)

### artists

- artist name
- url
- location
