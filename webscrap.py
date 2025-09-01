
import csv
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup as BS

BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "index.html")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CodeAlphaScraper/1.0)"}

MAX_PAGES_PER_CATEGORY = 2  # increase to scrape more
SLEEP_SEC = 1.0             # be nice to the demo site

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def get_categories():
    html = fetch(START_URL)
    soup = BS(html, "html.parser")
    cat_links = []
    for a in soup.select(".side_categories ul li ul li a"):
        href = a.get("href")
        name = a.text.strip()
        cat_links.append((name, urljoin(BASE_URL, href)))
    return cat_links

def parse_book(article, category):
    title = article.h3.a.get("title", "").strip()
    rel_url = article.h3.a.get("href")
    product_url = urljoin(BASE_URL, "catalogue/" + rel_url.replace("../../../", ""))
    price = article.select_one(".price_color").text.strip()
    stock = article.select_one(".availability").text.strip()
    rating = article.select_one("p.star-rating").get("class", [])
    rating_value = next((c for c in rating if c != "star-rating"), "Unknown")
    img_rel = article.find("img").get("src")
    img_url = urljoin(BASE_URL, img_rel)
    return {
        "category": category, "title": title, "price": price, "stock": stock,
        "rating": rating_value, "product_url": product_url, "image_url": img_url
    }

def scrape_category(name, url, writer, logf):
    next_url = url
    page_count = 0
    while next_url and page_count < MAX_PAGES_PER_CATEGORY:
        logf.write(f"Fetching: {next_url}\n")
        html = fetch(next_url)
        soup = BS(html, "html.parser")
        for article in soup.select("article.product_pod"):
            row = parse_book(article, name)
            writer.writerow(row)
        # find next page
        next_link = soup.select_one("li.next a")
        next_url = urljoin(next_url, next_link.get("href")) if next_link else None
        page_count += 1
        time.sleep(SLEEP_SEC)

def main():
    with open("logs.txt", "w", encoding="utf-8") as logf, \
         open("books.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["category", "title", "price", "stock", "rating", "product_url", "image_url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        cats = get_categories()
        for name, url in cats:
            logf.write(f"== Category: {name} ==\n")
            scrape_category(name, url, writer, logf)
    print("Done. Saved to books.csv")

if __name__ == "__main__":
    main()
