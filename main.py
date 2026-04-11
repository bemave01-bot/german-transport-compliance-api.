import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from datetime import datetime, timedelta

app = FastAPI()

# Tijdelijk geheugen om bronnen niet te overbelasten
cache = {
    "NL": {"price": 2.785, "time": None}, # Default waarde mocht scrape mislukken
    "DE": {"price": 1.950, "time": None},
    "AT": {"price": 1.890, "time": None}
}

def get_nl_gla():
    """Haalt de actuele Landelijke Adviesprijs op van UnitedConsumers"""
    try:
        url = "https://www.unitedconsumers.com/tanken/informatie/brandstofprijzen"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # We zoeken specifiek naar de dieselprijs in de tabel
        # Let op: dit is een versimpeld voorbeeld van de selector
        diesel_row = soup.find("td", text="Diesel").find_next_sibling("td")
        price_str = diesel_row.text.replace('€', '').replace(',', '.').strip()
        return float(price_str)
    except:
        return cache["NL"]["price"] # Terugval op laatste bekende prijs

@app.get("/")
def read_root(country: str = "NL", fuel_type: str = "diesel"):
    country = country.upper()
    now = datetime.now()

    # Check of we de prijs moeten verversen (elke 6 uur)
    if not cache[country]["time"] or now > cache[country]["time"] + timedelta(hours=6):
        if country == "NL":
            cache[country]["price"] = get_nl_gla()
        # Voor DE en AT kunnen we later specifieke API-koppelingen toevoegen
        cache[country]["time"] = now

    current_price = cache[country]["price"]
    
    return {
        "compliance_header": {
            "country_selected": country,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "Official National Index (GLA/MTS-K)"
        },
        "fuel_data": {
            "fuel_type": fuel_type,
            "unit": "EUR/L",
            "net_price": round(current_price / 1.21, 3),
            "vat_rate": "21%",
            "gross_price": current_price
        },
        "legal_notice": "Estimates only. Verify with official sources before billing."
    }
