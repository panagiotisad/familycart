import json
import re
import unicodedata
from difflib import SequenceMatcher

EXCLUDE_WORDS = {"gia", "kai", "me", "to", "ta", "o", "i", "oi", "tou", "tis", "ton", "tin", "apo", "se", "sto", "ston"}

#common words that are typed in another way than displayed in the supermarket
WORDS_CHANGE = {
    "krasi":"oinos",
    "mpura":"mpira",
    "mpures":"mpira",
    "ntomata":"tomata",
}

GREEK_TO_GREEKLISH = str.maketrans({
    "α": "a",
    "β": "v",
    "γ": "g",
    "δ": "d",
    "ε": "e",
    "ζ": "z",
    "η": "i",
    "θ": "th",
    "ι": "i",
    "κ": "k",
    "λ": "l",
    "μ": "m",
    "ν": "n",
    "ξ": "x",
    "ο": "o",
    "π": "p",
    "ρ": "r",
    "σ": "s",
    "ς": "s",
    "τ": "t",
    "υ": "u",
    "φ": "f",
    "χ": "ch",
    "ψ": "ps",
    "ω": "o"
})

GREEK_ACCENTS = str.maketrans({
    "ά": "α",
    "έ": "ε",
    "ή": "η",
    "ί": "ι",
    "ό": "ο",
    "ύ": "υ",
    "ώ": "ω",
    "ϊ": "ι",
    "ϋ": "υ",
    "ΐ": "ι",
    "ΰ": "υ",
})

#called on greek_to_greeklish function
def normalize(text):
    text = text.lower()
    text = text.translate(GREEK_ACCENTS)
    #replaces anything that isnt a letter,digit or space with a space
    text = re.sub(r"[^\w\s]|_", " ", text)
    #returns the text with no extra spaces 
    return " ".join(text.split())

#called on find_matches function
def greek_to_greeklish(text):

    text = normalize(text)

    combinations = {
        "ου": "ou",
        "αι": "ai",
        "ει": "ei",
        "οι": "oi",
        "υι": "yi",
        "αυ": "af",
        "ευ": "ef",
        "γκ": "gk",
        "γγ": "g",
        "μπ": "mp",
        "ντ": "nt",
        "τσ": "ts",
        "τζ": "tz"
    }

    #converts the combinations first and then the remaining text
    for greek, latin in combinations.items():
        text = text.replace(greek, latin)
    text = text.translate(GREEK_TO_GREEKLISH)

    return text

#called on familyCart.py to find the matches of offers for a product or all products
def find_matches(search_item):

    grocery = greek_to_greeklish(search_item)
    grocery_words = []
    for word in grocery.split():
        if word not in EXCLUDE_WORDS:
            grocery_words.append(word)
    matches = []
    for i, word in enumerate(grocery_words):
        if word in WORDS_CHANGE:
            grocery_words[i] = WORDS_CHANGE[word]

    for offer in offers:
        offer_product = offer["product_greeklish_name"]
        offer_product_words = []
        for word in offer_product.split():
            if word not in EXCLUDE_WORDS:
                offer_product_words.append(word)
        
        #excact match or a word match or the option to see all offer products("all products")
        if grocery == offer_product or grocery == "all products":
            score = 1.0
        elif grocery_words:
            words_score = 0
            for word in grocery_words:
                if word in offer_product_words:
                    words_score +=1
            score =  words_score/ len(grocery_words)
        else:
            score = 0
        if score>=0.7:
            matches.append((score, offer))

    #sorts the matches to display them by score
    matches.sort(key=lambda item: item[0], reverse=True)

    return matches

offers = []

#used to load the offers from the json to an array.Called on the end of each scrape by the scrapper
def load_offers():
    global offers
    try:
        with open("offers.json", "r") as f:
            offers = json.load(f)
        for offer in offers:
            offer["product_greeklish_name"] = greek_to_greeklish(offer["product_name"])
    except Exception as e:
        print(f"error while reading the offers.json file: {e}")
        

#loads the json to the offers array when starting the app
load_offers()

