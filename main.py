def get_nl_gla():
    """Haalt de actuele GLA op en zorgt dat we altijd de laatste prijs hebben."""
    try:
        url = "https://www.unitedconsumers.com/tanken/informatie/brandstofprijzen"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # We zoeken de tabel en pakken de prijs die bij Diesel hoort
        # UnitedConsumers gebruikt vaak specifieke classes, we zoeken op de tekst 'Diesel'
        td_diesel = soup.find('td', string=lambda t: t and 'Diesel' in t)
        if td_diesel:
            price_row = td_diesel.find_next_sibling('td')
            price_str = price_row.text.replace('€', '').replace(',', '.').strip()
            return float(price_str)
        return cache["NL"]["price"]
    except Exception as e:
        print(f"Fout bij ophalen: {e}")
        return cache["NL"]["price"]

# In de API route passen we de ververs-tijd aan naar 1 uur (of zelfs korter)
@app.get("/")
def read_root(country: str = "NL", fuel_type: str = "diesel"):
    country = country.upper()
    now = datetime.now()

    # Ververs nu elk uur (3600 seconden) voor maximale scherpte
    if not cache[country]["time"] or now > cache[country]["time"] + timedelta(hours=1):
        if country == "NL":
            new_price = get_nl_gla()
            cache[country]["price"] = new_price
        cache[country]["time"] = now
