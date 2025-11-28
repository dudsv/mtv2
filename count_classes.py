import asyncio
import aiohttp
from bs4 import BeautifulSoup

URL = "https://www.purina.fr/choisir-animal/articles/accueillir-chien/prenom/japonais"
TARGET_CLASS_STR = "clearfix text-formatted field field--name-field-c-text field--type-text-long field--label-hidden field__item"

async def main():
    print(f"Fetching {URL}...")
    async with aiohttp.ClientSession() as session:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with session.get(URL, headers=headers) as response:
            if response.status != 200:
                print(f"Failed to fetch page: {response.status}")
                return

            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            target_classes = set(TARGET_CLASS_STR.split())
            
            count = 0
            exact_matches = 0
            
            for tag in soup.find_all(class_=True):
                classes = tag.get('class')
                if not classes: continue
                
                class_set = set(classes)
                
                # Check if all target classes are present
                if target_classes.issubset(class_set):
                    count += 1
                    
                    # Check for exact match (ignoring order)
                    if class_set == target_classes:
                        exact_matches += 1

            print(f"Elements containing all target classes: {count}")
            print(f"Elements with EXACT match (no extra classes): {exact_matches}")

if __name__ == "__main__":
    # Redirect stdout to a file
    import sys
    with open("count_result.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        asyncio.run(main())

