import requests
from bs4 import BeautifulSoup

URL = "https://www.purina.fr/choisir-animal/articles/accueillir-chien/prenom/japonais"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')
    
    with open("headers_list.txt", "w", encoding="utf-8") as f:
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            f.write(f"{tag.name}: {tag.get_text(strip=True)}\n")

if __name__ == "__main__":
    main()
