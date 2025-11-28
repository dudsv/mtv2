
import requests
from bs4 import BeautifulSoup
import collections
import re

url = "https://www.purina.fr/choisir-animal/articles/accueillir-chien/prenom/japonais"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    target_classes = ["article--hero", "hero--image", "component--contact-us-small"]
    
    print("--- Specific Classes Search ---")
    for cls in target_classes:
        elements = soup.find_all(class_=re.compile(cls))
        print(f"Found {len(elements)} elements matching '{cls}'")
        if elements:
            print(f"  Example tag: {elements[0].name} class={elements[0].get('class')}")

    print("\n--- General 'component' Classes ---")
    component_classes = collections.Counter()
    for element in soup.find_all(class_=re.compile(r"component")):
        for cls in element['class']:
            if 'component' in cls:
                component_classes[cls] += 1
    
    for cls, count in component_classes.most_common(20):
        print(f"{cls}: {count}")

except Exception as e:
    print(f"Error: {e}")
