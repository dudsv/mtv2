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
    print("=== ARTICLES LIST COMPONENT FOUND ===\n")
    
    # Check for component title/heading
    heading = articles_list.find(['h2', 'h3', 'h4'])
    if heading:
        print(f"Component Title: {heading.get_text(strip=True)}")
        print(f"Title Tag: {heading.name}\n")
    
    # Find all article elements
    article_elements = articles_list.find_all('article')
    print(f"Found {len(article_elements)} <article> elements\n")
    
    # Detailed inspection of each article
    for i, article in enumerate(article_elements, 1):
        print(f"--- Article {i} ---")
        print(f"Article classes: {article.get('class')}")
        
        # Find title
        title_field = article.find(class_='field--name-title')
        if title_field:
            print(f"Title field found: {title_field.get_text(strip=True)[:80]}...")
            
            # Look for link
            link_in_title = title_field.find('a')
            if link_in_title:
                print(f"  Link in title: {link_in_title.get('href', 'N/A')}")
            else:
                print(f"  No link in title field")
        else:
            print("No title field found")
        
        # Look for any link in article
        all_links = article.find_all('a')
        print(f"Total links in article: {len(all_links)}")
        if all_links:
            print(f"  First link href: {all_links[0].get('href', 'N/A')}")
        
        print()
else:
    print("Articles List component NOT found\n")
    
    # Check what components exist
    print("All components with 'component--' class:")
    all_components = soup.find_all(class_=lambda x: x and any('component--' in cls for cls in x))
    for comp in all_components:
        print(f"  {comp.get('class')}")
