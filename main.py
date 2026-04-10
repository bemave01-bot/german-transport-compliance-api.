from fastapi import FastAPI, Query
from datetime import datetime

description = """
## Professional Transport Compliance API (NL-DE-AT) 2026

### ⚠️ LEGAL DISCLAIMER & TERMS OF USE
**Use of this API constitutes acceptance of the following terms:**
1. **No Liability:** The provider is NOT responsible for financial losses or operational errors.
2. **Estimates Only:** Rates are 2026 projections and subject to change.
3. **Data Verification:** Users must verify data with official sources (ASFINAG, Toll Collect, etc.).

---
### Features:
* **Dynamic Localization:** Automatic switching between Dutch and German based on the requested country.
* **Toll & Fuel:** Integrated calculations for the NL-DE-AT corridor.
"""

app = FastAPI(
    title="Transport Compliance Pro API",
    description=description,
    version="1.4.0"
)

# Definieer de talen en termen per land
LOCALIZATION = {
    "NL": {
        "lang_name": "Nederlands",
        "msg": "Berekening op basis van Nederlandse wetgeving.",
        "disclaimer": "DISCLAIMER: Dit zijn ramingen. Wij zijn niet aansprakelijk voor fouten.",
        "terms": {"net": "Netto", "gross": "Bruto", "vat": "BTW"}
    },
    "DE": {
        "lang_name": "Deutsch",
        "msg": "Berechnung auf Basis deutscher Gesetzgebung (BFStrMG).",
        "disclaimer": "RECHTLICHER HINWEIS: Dies sind Schätzungen. Wir haften nicht für Fehler.",
        "terms": {"net": "Netto", "gross": "Bruto", "vat": "MwSt"}
    },
    "AT": {
        "lang_name": "Deutsch",
        "msg": "Berechnung auf Basis österreichischer Gesetzgebung (ASFINAG).",
        "disclaimer": "RECHTLICHER HINWEIS: Dies sind Schätzungen. Wir haften nicht für Fehler.",
        "terms": {"net": "Netto", "gross": "Bruto", "vat": "MwSt"}
    }
}

@app.get("/transport/fuel-compliance", tags=["Energy & Compliance"])
async def get_fuel(country: str = Query("NL", description="Country code (NL, DE, AT) determines the language of the output.")):
    """Outputs data in Dutch for NL, and German for DE/AT."""
    country = country.upper()
    # Pak de NL settings als het land niet wordt herkend
    conf = LOCALIZATION.get(country, LOCALIZATION["NL"])
    t = conf["terms"]
    
    # Prijs ramingen
    price = 1.55 if country == "NL" else (1.47 if country == "DE" else 1.42)
    btw_rate = 0.21 if country == "NL" else (0.19 if country == "DE" else 0.20)

    return {
        "compliance_header": {
            "country_selected": country,
            "language": conf["lang_name"],
            "local_message": conf["msg"],
            "legal_notice": conf["disclaimer"]
        },
        "pricing_details": {
            "fuel_type": "Diesel",
            f"{t['net']}_EUR": price,
            f"{t['vat']}_EUR": round(price * btw_rate, 3),
            f"{t['gross']}_EUR": round(price * (1 + btw_rate), 3)
        }
    }

@app.get("/transport/toll-calculator", tags=["Toll & Infrastructure"])
async def get_toll(
    country: str = Query(..., description="Select NL, DE, or AT"),
    distance_km: float = Query(..., example=100.0)
):
    """Automatic language switching for toll results."""
    country = country.upper()
    conf = LOCALIZATION.get(country, LOCALIZATION["DE"])
    t = conf["terms"]
    
    # Tarief logica
    rate = 14.9 if country == "NL" else (34.8 if country == "DE" else 52.4)
    net_toll = (distance_km * rate) / 100
    btw_rate = 0.21 if country == "NL" else (0.19 if country == "DE" else 0.20)
    
    return {
        "legal": {
            "disclaimer": conf["disclaimer"],
            "regime_info": conf["msg"]
        },
        "calculation": {
            "distance": f"{distance_km} km",
            f"Totaal_{t['net']}": round(net_toll, 2),
            f"Totaal_{t['gross']}": round(net_toll * (1 + btw_rate), 2),
            "tarief_cent_km": rate
        }
    }
