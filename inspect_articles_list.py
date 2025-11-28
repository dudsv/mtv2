import requests
from bs4 import BeautifulSoup

URL = "https://www.purina.fr/choisir-animal/articles/accueillir-chien/prenom/chien-petite-taille"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'lxml')

# Find Articles List component
articles_list = soup.find(class_='component--articles-list')

if articles_list:
    print("=== ARTICLES LIST COMPONENT ===\n")
    print(f"Component classes: {articles_list.get('class')}\n")
    
    # Find all article titles
    title_fields = articles_list.find_all(class_='field--name-title')
    print(f"Found {len(title_fields)} title fields\n")
    
    for i, title_field in enumerate(title_fields, 1):
        print(f"Article {i}:")
        print(f"  Classes: {title_field.get('class')}")
        print(f"  Text: {title_field.get_text(strip=True)}")
        
        # Find link
        link = title_field.find('a')
        if link:
            print(f"  URL: {link.get('href', 'N/A')}")
        else:
            print("  No link found in title field")
        print()
else:
    print("Articles List component not found")
    print("\nSearching for component-- classes...")
    all_components = soup.find_all(class_=lambda x: x and any('component--' in cls for cls in x))
    for comp in all_components[:5]:
        print(f"  Found: {comp.get('class')}")
