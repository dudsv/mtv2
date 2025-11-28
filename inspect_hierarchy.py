import asyncio
import aiohttp
from bs4 import BeautifulSoup

URL = "https://www.purina.fr/choisir-animal/articles/accueillir-chien/prenom/japonais"

TARGET_TEXTS = [
    "Accueillir un chien chez soi est une expérience",
    "10 noms de chiens japonais les plus populaires",
    "Top 10 des noms masculins de chiens au Japon",
    "Top 10 des noms féminins de chiens au Japon",
    "20 noms de chiens japonais craquants",
    "20 Noms de chiens japonais inspirés de la Pop culture",
    "20 noms de plats japonais pour chiens",
    "Conseils pour choisir un nom japonais idéal pour votre chien",
    "Kotaro (petit garçon)",
    "Dango (boulettes)"
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
            
            print("--- Element Inspection ---")
            for text in TARGET_TEXTS:
                # Find element containing the text
                element = soup.find(string=lambda t: t and text in t)
                if element:
                    parent = element.parent
                    # Walk up to find the nearest div or significant container
                    container = parent
                    classes = []
                    while container and container.name != 'body':
                        cls = container.get('class')
                        if cls:
                            classes.append(f"<{container.name} class='{' '.join(cls)}'>")
                        else:
                            classes.append(f"<{container.name}>")
                        
                        # Stop if we hit the specific class we were looking for earlier
                        if cls and "clearfix" in cls and "text-formatted" in cls:
                            print(f"\nText: '{text}'")
                            print(f"  Found inside target block: <{container.name} class='{' '.join(cls)}'>")
                            break
                        
                        container = container.parent
                    else:
                        print(f"\nText: '{text}'")
                        print(f"  NOT inside target block. Immediate parent: <{parent.name} class='{' '.join(parent.get('class') or [])}'>")

if __name__ == "__main__":
    # Redirect stdout to a file
    import sys
    with open("hierarchy_result.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        asyncio.run(main())

