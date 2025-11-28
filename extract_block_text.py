import asyncio
import aiohttp
from bs4 import BeautifulSoup

URL = "https://www.purina.fr/choisir-animal/articles/accueillir-chien/prenom/japonais"
TARGET_CLASS_STR = "clearfix text-formatted field field--name-field-c-text field--type-text-long field--label-hidden field__item"

async def main():
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
            
            print("--- Extracted Block Content ---")
            for tag in soup.find_all(class_=True):
                classes = tag.get('class')
                if not classes: continue
                
                class_set = set(classes)
                
                if target_classes.issubset(class_set):
                    count += 1
                    text = tag.get_text(strip=True)[:50] # Get first 50 chars for matching
                    print(f"BLOCK_{count}: {text}")

if __name__ == "__main__":
    asyncio.run(main())
