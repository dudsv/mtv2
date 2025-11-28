import requests
from bs4 import BeautifulSoup

URL = "https://www.purina.fr/choisir-animal/articles/accueillir-chien/prenom/japonais"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'lxml')

# Find Hero Article
hero_article = soup.find(class_='article--hero')

if hero_article:
    print("=== HERO ARTICLE STRUCTURE ===\n")
    
    # Find hero--image
    hero_image = hero_article.find(class_='hero--image')
    if hero_image:
        print("Found hero--image:")
        img_tag = hero_image.find('img')
        if img_tag:
            print(f"  Image SRC: {img_tag.get('src', 'N/A')}")
            print(f"  Image ALT: {img_tag.get('alt', 'N/A')}")
        print()
    
    # Check for other images in Hero Article
    all_imgs = hero_article.find_all('img')
    print(f"Total images in Hero Article: {len(all_imgs)}")
    for i, img in enumerate(all_imgs):
        parent_class = img.parent.get('class', []) if img.parent else []
        print(f"  Image {i+1}: parent class = {parent_class}")
