from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="NL-DE-AT Transport + Fuel + Toll + Compliance API")

# Fiscale instellingen
COUNTRIES = {
    "NL": {"btw": 0.21, "co2_tax_ton": 60, "maut_name": "Vrachtwagenheffing"},
    "DE": {"btw": 0.19, "co2_tax_ton": 55, "maut_name": "LKW-Maut (BFStrMG)"},
    "AT": {"btw": 0.20, "co2_tax_ton": 47.5, "maut_name": "GO-Maut (ASFINAG)"}
}

# Specifieke Tarieven per land (Cent per KM)
MAUT_DATA = {
    "NL": { # Gebaseerd op Euro 6 (meest voorkomend)
        ">12t": 14.9, 
        "3.5-12t": 8.3
    },
    "DE": { # Gewichten + CO2-Klassen
        ">18t": {"c1": 34.8, "c2": 30.2, "c3": 25.0, "c4": 15.0, "c5": 8.7},
        "12-18t": {"c1": 23.8, "c2": 20.0, "c3": 16.0, "c4": 10.0, "c5": 5.9},
        "3.5-12t": {"c1": 15.1, "c2": 12.0, "c3": 9.0, "c4": 5.0, "c5": 0.0}
    },
    "AT": { # Assen-logica (Tarief per as-groep)
        "4+ assen": {"c1": 52.4, "c5": 12.5},
        "3 assen": {"c1": 38.2, "c5": 9.2},
        "2 assen": {"c1": 25.1, "c5": 6.1}
    }
}

@app.get("/transport/fuel-compliance")
async def get_fuel(land: str = "NL"):
    land = land.upper()
    c = COUNTRIES.get(land, COUNTRIES["NL"])
    prices = {
        "diesel": 1.55 if land == "NL" else (1.47 if land == "DE" else 1.42),
        "hvo100": 1.95 if land == "NL" else 1.81,
        "super_e10": 1.68 if land == "NL" else 1.54,
        "super_e5": 1.75 if land == "NL" else 1.59,
        "lpg": 0.65 if land == "NL" else 0.61,
        "adblue": 0.75
    }
    return {
        "meta": {"country": land, "btw": f"{c['btw']*100}%"},
        "fuels": {k: {"netto": v, "bruto": round(v * (1 + c['btw']), 3)} for k, v in prices.items()}
    }

@app.get("/transport/maut-calculator")
async def get_maut(land: str, km: float, gewicht_of_assen: str, co2_klasse: int = 1):
    land = land.upper()
    c = COUNTRIES.get(land, COUNTRIES["NL"])
    
    # Selecteer juiste tarief op basis van land-logica
    if land == "NL":
        tarief = MAUT_DATA["NL"].get(gewicht_of_assen, 14.9)
    elif land == "AT":
        tarief = MAUT_DATA["AT"].get(gewicht_of_assen, MAUT_DATA["AT"]["4+ assen"]).get(f"c{co2_klasse}", 52.4)
    else: # Duitsland
        tarief = MAUT_DATA["DE"].get(gewicht_of_assen, MAUT_DATA["DE"][">18t"]).get(f"c{co2_klasse}", 34.8)
    
    netto = (km * tarief) / 100
    bruto = netto * (1 + c['btw'])
    
    return {
        "regime": c['maut_name'],
        "config": {"land": land, "unit": gewicht_of_assen, "co2_klasse": co2_klasse},
        "kosten": {
            "netto_eur": round(netto, 2),
            "btw_eur": round(bruto - netto, 2),
            "bruto_eur": round(bruto, 2),
            "cent_per_km": tarief
        }
    }
