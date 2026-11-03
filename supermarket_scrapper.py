from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import products_matching
import time


def run_scrapper():

    offers = []

    #------------SKLAVENITIS--------------

    url = "https://www.sklavenitis.gr/sylloges/prosfores/"
    range_end = 300 
    for page in range(1,range_end):
        response = requests.get(url, impersonate="chrome",params={"pg":page}, timeout=30)
        #checks for http errors
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.select("div.product")
        if not products:
            break
        for product in products:
            #badge class holds the offer if there is any
            badge = product.select_one("div.badge")
            if not badge:
                continue
            offer_text = badge.get_text(strip=True)
            title = product.select_one("h4.product__title a")
            if title is None:
                continue
            price = product.select_one("div.price")
            link = title["href"]
            functional_link = "https://www.sklavenitis.gr" + link
            offers.append({
            "product_name":title.get_text(strip=True),
            "price":price.get("data-price"),
            "link":functional_link,
            "product_offer": offer_text
            })

    #----------------AB------------------
    
    #url to mimic the javascript request for products 
    url = "https://www.ab.gr/api/v1/?operationName=ProductList&variables=%7B%22productListingType%22%3A%22PROMOTION_SEARCH%22%2C%22lang%22%3A%22gr%22%2C%22productCodes%22%3A%22%22%2C%22categoryCode%22%3A%22%22%2C%22excludedProductCodes%22%3A%22%22%2C%22brands%22%3A%22%22%2C%22keywords%22%3A%22%22%2C%22productTypes%22%3A%22%22%2C%22lazyLoadCount%22%3A10%2C%22pageNumber%22%3APAGE_NUMBER%2C%22sort%22%3A%22categoryOrder%22%2C%22searchQuery%22%3A%22promotions%3AcategoryOrder%3ApromotionDisplayTypes%3AREDUCTIONS%3ApromotionDisplayTypes%3AMULTIPURCHASE%22%2C%22hideProductsWithoutPromo%22%3Afalse%2C%22hideUnavailableProducts%22%3Atrue%2C%22maxItemsToDisplay%22%3A0%2C%22includePotentialActivatableOffers%22%3Atrue%2C%22customerSegment%22%3A%22newPromoPageSegment%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22ef54fc2d8da4a9ad4987b2fb18f61c59f341d018be0f4670b0c9c7dabff07e5c%22%7D%7D"
    range_end = 100
    for page in range(0, range_end):
        response = requests.get(url.replace("PAGE_NUMBER", str(page)),headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Accept-Language": "el-GR,el;q=0.9",
    "Referer": "https://www.ab.gr/search/promotions",
    "x-apollo-operation-name": "ProductList",
    }, timeout=30)
        
        response.raise_for_status()
        data = response.json()
        products = data["data"]["productList"]["products"]
        if not products:
            break
        for product in products:
            price = product["price"]
            price_text = price.get("discountedPriceFormatted") 
            product_offer = product.get("potentialPromotions")
            offer_text = product_offer[0].get("description")
            offers.append({
                "product_name": product["name"],
                "price": price_text.replace("€", ""),
                "link": "https://www.ab.gr" + product["url"],
                "product_offer": offer_text
            })
        time.sleep(1)
    #saves the offers array to the json        
    with open("offers.json","w") as f:
        json.dump(offers,f,ensure_ascii=False, indent=4)
    #calls the function to load the offers on an array on products_matching 
    products_matching.load_offers()
    
if __name__ == "__main__":
    run_scrapper()