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
    print("=== ARTICLES LIST STRUCTURE ===\n")
    
    # Show first 500 chars of HTML
    html_snippet = str(articles_list)[:1000]
    print(f"HTML snippet:\n{html_snippet}\n...\n")
    
    # Find any divs, sections, or other containers
    print("Direct children:")
    for child in articles_list.find_all(recursive=False):
        print(f"  Tag: {child.name}, Classes: {child.get('class')}")
    
    print("\nAll elements with 'article' in class:")
    article_like = articles_list.find_all(class_=lambda x: x and any('article' in cls for cls in x))
    for elem in article_like[:5]:
        print(f"  Tag: {elem.name}, Classes: {elem.get('class')}")
        # Check for title and link
        title = elem.find(class_='field--name-title')
        link = elem.find('a')
        if title:
            print(f"    Title: {title.get_text(strip=True)[:60]}")
        if link:
            print(f"    Link: {link.get('href', 'N/A')}")
    
    print("\nAll links in component:")
    all_links = articles_list.find_all('a')
    for i, link in enumerate(all_links[:5], 1):
        print(f"  Link {i}: {link.get('href', 'N/A')}")
        print(f"    Text: {link.get_text(strip=True)[:60]}")
