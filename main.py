import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from datetime import datetime, timedelta

app = FastAPI()

# Tijdelijk geheugen (Cache)
cache = {
    "NL": {"price": 2.785, "time": None}, 
    "DE": {"price": 1.950, "time": None},
    "AT": {"price": 1.890, "time": None}
}

def get_nl_gla():
    """Haalt de actuele GLA op van UnitedConsumers."""
    try:
        url = "https://www.unitedconsumers.com/tanken/informatie/brandstofprijzen"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Zoek de cel die 'Diesel' bevat
        td_diesel = soup.find('td', string=lambda t: t and 'Diesel' in t)
        if td_diesel:
            price_row = td_diesel.find_next_sibling('td')
            # Maak het getal schoon (verwijder € en verander , in .)
            price_str = price_row.text.replace('€', '').replace(',', '.').strip()
            return float(price_str)
        return cache["NL"]["price"]
    except Exception as e:
        print(f"Fout bij ophalen NL data: {e}")
        return cache["NL"]["price"]

@app.get("/transport/fuel-compliance")
def read_root(country: str = "NL", fuel_type: str = "diesel"):
    country = country.upper()
    
    # Zorg dat we een geldige landcode hebben, anders default naar NL
    if country not in cache:
        country = "NL"
        
    now = datetime.now()

    # Ververs de prijs als er meer dan 1 uur voorbij is
    if not cache[country]["time"] or now > cache[country]["time"] + timedelta(hours=1):
        if country == "NL":
            new_price = get_nl_gla()
            cache[country]["price"] = new_price
        # (Hier kunnen later DE en AT scrapers tussen)
        cache[country]["time"] = now

    current_price = cache[country]["price"]
    
    return {
        "compliance_header": {
            "country_selected": country,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "National Fuel Index (GLA / MTS-K)"
        },
        "fuel_data": {
            "fuel_type": fuel_type,
            "unit": "EUR/L",
            "net_price": round(current_price / 1.21, 3),
            "vat_rate": "21%",
            "gross_price": current_price
        },
        "legal_notice": "Estimates based on daily advisory prices. No liability for errors."
    }
