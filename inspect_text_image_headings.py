import requests
from bs4 import BeautifulSoup

URL = "https://www.purina.fr/choisir-animal/articles/accueillir-chien/prenom/chien-petite-taille"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'lxml')

# Find all Text Image components
text_images = soup.find_all(class_='component--text-image')

print(f"Found {len(text_images)} Text Image components\n")

for i, component in enumerate(text_images[:3], 1):
    print(f"=== TEXT IMAGE {i} ===")
    
    # Find headings
    headings = component.find_all(['h2', 'h3', 'h4', 'h5', 'h6'])
    print(f"Headings found: {len(headings)}")
    for h in headings:
        print(f"  {h.name}: {h.get_text(strip=True)}")
    
    # Find paragraphs
    paragraphs = component.find_all('p')
    print(f"Paragraphs found: {len(paragraphs)}")
    for p in paragraphs[:2]:
        print(f"  p: {p.get_text(strip=True)[:60]}...")
    
    print()
