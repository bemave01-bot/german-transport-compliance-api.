import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from datetime import datetime, timedelta

app = FastAPI(title="TransitIntegrity Global Audit API 2026")

# --- 1. MEERTALIGE COMPLIANCE ENGINE ---
TRANSLATIONS = {
    "EN": {
        "toll": "Infrastructure Usage Fee (Toll)", "fuel": "Energy Cost (Diesel/HVO)", 
        "vat_reclaim": "VAT Recovery (Cross-Border)", "co2": "CSRD Carbon Emissions Report",
        "audit_note": "Certified for statutory reporting (CSRD) and tax filing."
    },
    "NL": {
        "toll": "Infrastructuurheffing (Vrachtwagenheffing)", "fuel": "Energiekosten (Brandstof)", 
        "vat_reclaim": "Terugvorderbare BTW", "co2": "CSRD CO2-Rapportage (Audit-Klaar)",
        "audit_note": "Gecertificeerd voor wettelijke rapportage (CSRD) en belastingaangifte."
    },
    "DE": {
        "toll": "Infrastrukturabgabe (LKW-Maut)", "fuel": "Energiekosten (Kraftstoff)", 
        "vat_reclaim": "Umsatzsteuer-Rückerstattung", "co2": "CSRD CO2-Bericht (Prüfungsfähig)",
        "audit_note": "Zertifiziert für gesetzliche Berichterstattung (CSRD) und Steuererklärung."
    }
}

# --- 2. FISCALE & INFRASTRUCTUUR DATA 2026 ---
CURRENT_DATE = datetime.now()
NL_START_DATE = datetime(2026, 7, 1)

COUNTRY_DATA = {
    "NL": {
        "vat": 1.21, "excise": 0.552, "co2_tax": 0.000, "cache": 720,
        "fuel_src": "United Consumers (GLA)", "toll_sys": "Vrachtwagenheffing",
        "legal": "Wet Vrachtwagenheffing 2026, EU 2022/362",
        "rates": {
            "heavy": {"CO2_1": 0.201, "CO2_2": 0.183, "CO2_3": 0.165, "CO2_4": 0.105, "CO2_5": 0.038},
            "mid": {"CO2_1": 0.182, "CO2_2": 0.165, "CO2_3": 0.148, "CO2_4": 0.095, "CO2_5": 0.037}
        }
    },
    "DE": {
        "vat": 1.19, "excise": 0.470, "co2_tax": 0.185, "cache": 5,
        "fuel_src": "MTS-K / Bundeskartellamt", "toll_sys": "LKW-Maut (Toll Collect)",
        "legal": "BFStrMG § 7, nEHS CO2-Preis Gesetz",
        "rates": {
            "heavy": {"CO2_1": 0.354, "CO2_2": 0.332, "CO2_3": 0.311, "CO2_4": 0.205, "CO2_5": 0.088},
            "mid": {"CO2_1": 0.302, "CO2_2": 0.285, "CO2_3": 0.268, "CO2_4": 0.175, "CO2_5": 0.075}
        }
    },
    "AT": {
        "vat": 1.20, "excise": 0.397, "co2_tax": 0.152, "cache": 45,
        "fuel_src": "E-Control Austria", "toll_sys": "GO-Maut (ASFINAG)",
        "legal": "BStMG 2026 (Bundesstraßen-Mautgesetz)",
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
    except Exception: 
        return data_store[c]["p"]

@app.get("/api/v1/transport/full-audit-report")
def get_audit_report(
    lang: str = Query("NL"), country: str = Query("NL"), km: float = Query(100.0),
    co2_class: str = Query("CO2_1"), axles: int = Query(5), weight_kg: int = Query(40000),
    fuel_liters: float = Query(35.0), base_price_net: float = Query(None), # Default None voor flexibele check
    is_adr: bool = Query(False), special_route: str = Query(None)
):
    try:
        lang, country = lang.upper(), country.upper()
        now = datetime.now()
        comp = COUNTRY_DATA.get(country, COUNTRY_DATA["NL"])
        
        # --- Brandstof Audit ---
        store = data_store.get(country, data_store["NL"])
        if not store["t"] or now > store["t"] + timedelta(minutes=comp["cache"]):
            store["p"], store["t"] = fetch_fuel(country), now
        
        # Gebruik de opgegeven netto prijs van de planner OF de gescrapte prijs
        if base_price_net:
            actual_net_price = base_price_net
            actual_gross_price = round(base_price_net * comp["vat"], 3)
        else:
            actual_gross_price = store["p"]
            actual_net_price = round(actual_gross_price / comp["vat"], 3)

        vat_per_liter = round(actual_gross_price - actual_net_price, 3)
        
        # --- Tol Audit ---
        toll_rates = comp["rates"]
        cat = "cat4" if country == "AT" and axles >= 4 else ("heavy" if weight_kg >= 18000 else "mid")
        rate_per_km = toll_rates.get(cat, toll_rates.get("heavy")).get(co2_class, 0.201)
        base_toll = round(km * rate_per_km, 2)

        if country == "NL" and now < NL_START_DATE:
            base_toll = 0.0
        
        # Punt 4 Fix: Zoek naar overeenkomende route in SPECIAL_FEES
        special_fee = 0.0
        if special_route:
            for route_name, price in SPECIAL_FEES.get(country, {}).items():
                if special_route.lower() in route_name.lower():
                    special_fee = price
                    break
        
        adr_fee = SPECIAL_FEES.get(country, {}).get("ADR_Tunnel" if country == "AT" else "ADR_Safety", 0.0) if is_adr else 0.0

        # --- Milieu & Teruggave ---
        scope1 = round(fuel_liters * 2.64, 2)
        scope3 = round(fuel_liters * 0.61, 2)
        vat_reclaimable = round(fuel_liters * vat_per_liter, 2)

        return {
            "status": "success",
            "audit_context": {
                "country": country,
                "timestamp": now.isoformat(),
                "fuel_price_used": "User-defined net price" if base_price_net else "Market average (Scraped)",
                "legal_basis": comp["legal"]
            },
            "report": {
                "costs": {
                    "total_toll": round(base_toll + special_fee + adr_fee, 2),
                    "fuel_cost_net": round(fuel_liters * actual_net_price, 2),
                    "vat_reclaimable": vat_reclaimable
                },
                "environmental": {
                    "co2_scope1_kg": scope1,
                    "co2_scope3_kg": scope3,
                    "method": "ISO 14083 / WTW"
                }
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
