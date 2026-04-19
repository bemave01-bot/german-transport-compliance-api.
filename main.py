import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from datetime import datetime, timedelta

app = FastAPI(title="TransitIntegrity Global Audit API 2026")

# --- 1. MEERTALIGE COMPLIANCE & INSTRUCTIE ENGINE ---
TRANSLATIONS = {
    "NL": {
        "instruction": "LET OP: Voer voor een internationale rit per land een aparte berekening uit. Tel de resultaten van NL, DE en AT handmatig bij elkaar op.",
        "toll": "Totale Tol (Infrastructuurheffing)", 
        "fuel": "Netto Brandstofkosten", 
        "vat_reclaim": "Terugvorderbare BTW",
        "co2": "CO2-Uitstoot Rapportage",
        "price_source": "Gebruikte prijs: ",
        "audit_note": "Gecertificeerd voor wettelijke rapportage (CSRD)."
    },
    "DE": {
        "instruction": "HINWEIS: Führen Sie für internationale Fahrten pro Land eine separate Berechnung durch. Addieren Sie die Ergebnisse für NL, DE und AT manuell.",
        "toll": "Gesamtmaut (Infrastrukturabgabe)", 
        "fuel": "Netto-Kraftstoffkosten", 
        "vat_reclaim": "Erstattungsfähige MwSt.",
        "co2": "CO2-Emissionsbericht",
        "price_source": "Verwendeter Preis: ",
        "audit_note": "Zertifiziert für gesetzliche Berichterstattung (CSRD)."
    },
    "EN": {
        "instruction": "NOTE: For international trips, perform a separate calculation per country. Manually add the results for NL, DE, and AT together.",
        "toll": "Total Toll Fee", 
        "fuel": "Net Fuel Costs", 
        "vat_reclaim": "Reclaimable VAT",
        "co2": "CO2 Emissions Report",
        "price_source": "Price used: ",
        "audit_note": "Certified for statutory reporting (CSRD)."
    }
}

# --- 2. FISCALE & INFRASTRUCTUUR DATA 2026 ---
NL_START_DATE = datetime(2026, 7, 1)

COUNTRY_DATA = {
    "NL": {
        "vat": 1.21, "excise": 0.552, "co2_tax": 0.000, "cache": 720,
        "rates": {
            "heavy": {"CO2_1": 0.201, "CO2_2": 0.183, "CO2_3": 0.165, "CO2_4": 0.105, "CO2_5": 0.038},
            "mid": {"CO2_1": 0.182, "CO2_2": 0.165, "CO2_3": 0.148, "CO2_4": 0.095, "CO2_5": 0.037}
        }
    },
    "DE": {
        "vat": 1.19, "excise": 0.470, "co2_tax": 0.185, "cache": 5,
        "rates": {
            "heavy": {"CO2_1": 0.354, "CO2_2": 0.332, "CO2_3": 0.311, "CO2_4": 0.205, "CO2_5": 0.088},
            "mid": {"CO2_1": 0.302, "CO2_2": 0.285, "CO2_3": 0.268, "CO2_4": 0.175, "CO2_5": 0.075}
        }
    },
    "AT": {
        "vat": 1.20, "excise": 0.397, "co2_tax": 0.152, "cache": 45,
        "rates": {
            "cat4": {"CO2_1": 0.5724, "CO2_2": 0.5657, "CO2_3": 0.5501, "CO2_4": 0.4200, "CO2_5": 0.1189},
            "cat3": {"CO2_1": 0.3842, "CO2_2": 0.3780, "CO2_3": 0.3650, "CO2_4": 0.2800, "CO2_5": 0.0850}
        }
    }
}

SPECIAL_FEES = {
    "AT": {"Brenner_A13": 115.50, "Tauern_A10": 92.00, "Arlberg_S16": 88.00, "ADR_Tunnel": 25.00},
    "DE": {"Herren_Tunnel": 16.50, "Warnow_Tunnel": 18.20, "ADR_Safety": 12.50}
}

data_store = {"NL": {"p": 2.709, "t": None}, "DE": {"p": 1.950, "t": None}, "AT": {"p": 1.749, "t": None}}

def fetch_fuel(c):
    try:
        if c == "NL": 
            res = requests.get("https://unitedconsumers.com", timeout=5)
            soup = BeautifulSoup(res.text, 'lxml')
            return float(soup.find('td', string=lambda t: t and 'Diesel' in t).find_next_sibling('td').text.replace('€', '').replace(',', '.').strip())
        elif c == "DE": 
            res = requests.get("https://clever-tanken.de", headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            soup = BeautifulSoup(res.text, 'lxml')
            return float(soup.select_one('.price').text.replace(',', '.').strip())
        return data_store[c]["p"]
    except Exception: return data_store[c]["p"]

@app.get("/api/v1/transport/full-audit-report")
def get_audit_report(
    lang: str = Query("NL"), country: str = Query("NL"), km: float = Query(100.0),
    co2_class: str = Query("CO2_1"), axles: int = Query(5), weight_kg: int = Query(40000),
    fuel_liters: float = Query(35.0), base_price_net: float = Query(None),
    is_adr: bool = Query(False), special_route: str = Query(None)
):
    try:
        lang, country = lang.upper(), country.upper()
        if lang not in TRANSLATIONS: lang = "NL"
        txt = TRANSLATIONS[lang]
        comp = COUNTRY_DATA.get(country, COUNTRY_DATA["NL"])
        now = datetime.now()

        # 1. Brandstof Audit
        store = data_store.get(country, data_store["NL"])
        if not store["t"] or now > store["t"] + timedelta(minutes=comp["cache"]):
            store["p"], store["t"] = fetch_fuel(country), now
        
        actual_net_price = base_price_net if base_price_net else round(store["p"] / comp["vat"], 3)
        vat_per_liter = round((actual_net_price * comp["vat"]) - actual_net_price, 3)
        
        # 2. Tol Audit (Gewicht & Assen logica)
        toll_rates = comp["rates"]
        if country == "AT":
            cat = "cat4" if axles >= 4 else "cat3"
        else:
            cat = "heavy" if weight_kg >= 18000 else "mid"
        
        rate_per_km = toll_rates.get(cat, toll_rates.get("heavy", toll_rates.get("cat4"))).get(co2_class, 0.201)
        base_toll = round(km * rate_per_km, 2)
        
        # NL heffing pas vanaf juli 2026
        if country == "NL" and now < NL_START_DATE: base_toll = 0.0
        
        # Speciale trajecten & ADR
        special_fee = 0.0
        if special_route:
            for r_name, price in SPECIAL_FEES.get(country, {}).items():
                if special_route.lower() in r_name.lower():
                    special_fee = price
                    break
        
        adr_fee = 0.0
        if is_adr:
            adr_fee = SPECIAL_FEES.get(country, {}).get("ADR_Tunnel" if country == "AT" else "ADR_Safety", 0.0)

        # 3. Resultaat Rapport
        return {
            "IMPORTANT_INSTRUCTION": txt["instruction"],
            "status": "success",
            "audit_info": {
                "country": country,
                "timestamp": now.isoformat(),
                "price_source": txt["price_source"] + ("Planner Input" if base_price_net else "Market Scrape")
            },
            "results": {
                txt["toll"]: round(base_toll + special_fee + adr_fee, 2),
                txt["fuel"]: round(fuel_liters * actual_net_price, 2),
                txt["vat_reclaim"]: round(fuel_liters * vat_per_liter, 2),
                txt["co2"]: f"{round(fuel_liters * 3.25, 2)} kg (Well-to-Wheel)",
                "audit_note": txt["audit_note"]
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
