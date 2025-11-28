import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sys

URL = "https://www.purina.fr/choisir-animal/articles/accueillir-chien/prenom/japonais"

TARGET_TEXTS = [
    "Accueillir un chien chez soi est une expérience",
    "10 noms de chiens japonais les plus populaires",
    "Top 10 des noms masculins de chiens au Japon",
    "Top 10 des noms féminins de chiens au Japon",
    "20 noms de chiens japonais craquants",
    "20 Noms de chiens japonais inspirés de la Pop culture",
    "20 noms de plats japonais pour chiens",
    "Conseils pour choisir un nom japonais idéal pour votre chien"
]

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
            
            print("--- All Occurrences Inspection ---")
            for text in TARGET_TEXTS:
                print(f"\nTarget: '{text}'")
                # Find ALL elements containing the text
                results = soup.find_all(string=lambda t: t and text in t)
                
                if not results:
                    print("  NOT FOUND")
                    continue

                for i, string_node in enumerate(results):
                    element = string_node.parent
                    print(f"  Occurrence {i+1}:")
                    print(f"    Tag: <{element.name}>")
                    print(f"    Classes: {element.get('class')}")
                    
                    # Walk up the tree
                    parent = element.parent
                    depth = 1
                    while parent and parent.name != 'body' and depth <= 4:
                        cls_str = f" class='{' '.join(parent.get('class'))}'" if parent.get('class') else ""
                        print(f"    Parent {depth}: <{parent.name}{cls_str}>")
                        parent = parent.parent
                        depth += 1

if __name__ == "__main__":
    # Redirect stdout to a file
    with open("all_occurrences_result.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        asyncio.run(main())
