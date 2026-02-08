from bs4 import BeautifulSoup

html = open('google_debug.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')

# Try different selectors
divs = soup.select('div.Gx5Zad.xpd.EtOod.pkphOe')
print(f'Found {len(divs)} div.Gx5Zad.xpd.EtOod.pkphOe elements')

for i, div in enumerate(divs[:3]):
    h3 = div.find('h3')
    a = div.find('a', href=True)
    snippet_div = div.select_one('div.H66NU')
    
    print(f'\n{i+1}.')
    print(f'  H3: {h3.get_text(strip=True) if h3 else "None"}')
    print(f'  Link: {a.get("href", "")[:80] if a else "None"}')
    print(f'  Snippet: {snippet_div.get_text(strip=True)[:80] if snippet_div else "None"}...')
