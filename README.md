# bandcamp-wishlist-scraper

Export your bandcamp wishlist into a csv file.

This script does not download audio files, only metadata.

Dependencies:
- requests
- bs4
- lxml

Fields extracted:
- artist name
- album name
- number of collections in
- price (for the digital release)

# Usage

- Go to your wishlist in your web browser (i.e. "https://bandcamp.com/dbeley/wishlist")
- Go to your wishlist tab
- Click on "see more" and scroll down until all the elements are loaded
- Save the page in html in the same folder as this script

```
python bandcamp-wishlist-scraper.py -f bandcamp-wishlist-export.html
```
