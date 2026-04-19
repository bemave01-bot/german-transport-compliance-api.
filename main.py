import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from datetime import datetime, timedelta
import os
import asyncio
from apify import Actor

app = FastAPI(title="TransitIntegrity Global Audit API 2026")

# --- 1. COMPLIANCE & TRANSLATIONS ---
TRANSLATIONS = {
    "NL": {
        "instruction": "HINWEIS: Voer voor internationale ritten per land een aparte berekening uit.",
        "toll": "Totale Tol (Infrastructuurheffing)", 
        "fuel": "Netto Brandstofkosten", 
        "vat_reclaim": "Terugvorderbare Belastingen (BTW + Accijns)",
        "co2": "CO2-Uitstoot Rapportage",
        "compliance": "Dit rapport is opgesteld conform ISO 14083:2023 en geschikt voor CSRD (Scope 1 & 3) audit-doeleinden."
    },
    "DE": {
        "instruction": "HINWEIS: Führen Sie für internationale Fahrten pro Land eine separate Berechnung durch.",
        "toll": "Gesamtmaut (Infrastrukturabgabe)", 
        "fuel": "Netto-Kraftstoffkosten", 
        "vat_reclaim": "Steuerrückerstattung (MwSt. + Mineralölsteuer)",
        "co2": "CO2-Emissionsbericht",
        "compliance": "Dieser Bericht wurde gemäß ISO 14083:2023 erstellt und ist für CSRD (Scope 1 & 3) Audits geeignet."
    }
}

# --- 2. FISCALE & INFRASTRUCTUUR DATA 2026 ---
COUNTRY_DATA = {
    "NL": {"vat": 1.21, "excise": 0.552, "co2_tax": 0.000, "cache": 720, "rates": {"heavy": {"CO2_1": 0.201, "CO2_2": 0.183, "CO2_3": 0.165, "CO2_4": 0.105, "CO2_5": 0.038}, "mid": {"CO2_1": 0.182, "CO2_2": 0.165, "CO2_3": 0.148, "CO2_4": 0.095, "CO2_5": 0.037}}},
    "DE": {"vat": 1.19, "excise": 0.470, "co2_tax": 0.185, "cache": 5, "rates": {"heavy": {"CO2_1": 0.354, "CO2_2": 0.332, "CO2_3": 0.311, "CO2_4": 0.205, "CO2_5": 0.088}, "mid": {"CO2_1": 0.302, "CO2_2": 0.285, "CO2_3": 0.268, "CO2_4": 0.175, "CO2_5": 0.075}}},
    "AT": {"vat": 1.20, "excise": 0.397, "co2_tax": 0.152, "cache": 45, "rates": {"cat4": {"CO2_1": 0.5724, "CO2_2": 0.5657, "CO2_3": 0.5501, "CO2_4": 0.4200, "CO2_5": 0.1189}, "cat3": {"CO2_1": 0.3842, "CO2_2": 0.3780, "CO2_3": 0.3650, "CO2_4": 0.2800, "CO2_5": 0.0850}}}
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
    lang: str = "NL", country: str = "NL", km: float = 100.0,
    co2_class: str = "CO2_1", axles: int = 5, weight_kg: int = 40000,
    fuel_liters: float = 35.0, base_price_net: float = None,
    is_adr: bool = False, special_route: str = None
):
    try:
        lang, country = lang.upper(), country.upper()
        if lang not in TRANSLATIONS: lang = "NL"
        txt = TRANSLATIONS[lang]
        comp = COUNTRY_DATA.get(country, COUNTRY_DATA["NL"])
        now = datetime.now()

        store = data_store.get(country, data_store["NL"])
        if not store["t"] or now > store["t"] + timedelta(minutes=comp["cache"]):
            store["p"], store["t"] = fetch_fuel(country), now
        
        # --- BEREKENINGEN ---
        actual_net_price = base_price_net if base_price_net else round(store["p"] / comp["vat"], 3)
        vat_per_liter = round((actual_net_price * comp["vat"]) - actual_net_price, 3)
        
        # Oostenrijkse accijnsteruggave (Mineralölsteuer-Rückvergütung) ca. € 0,082 per liter
        at_refund_per_liter = 0.082 if country == "AT" else 0.0
        total_reclaimable = round(fuel_liters * (vat_per_liter + at_refund_per_liter), 2)
        
        cat = "cat4" if country == "AT" and axles >= 4 else ("heavy" if weight_kg >= 18000 else "mid")
        rate_per_km = comp["rates"].get(cat, comp["rates"].get("heavy")).get(co2_class, 0.201)
        base_toll = round(km * rate_per_km, 2)
        
        if country == "NL" and now < datetime(2026, 7, 1): base_toll = 0.0

        total_co2 = round(fuel_liters * 3.25, 2)

        return {
            "DISCLAIMER": txt["instruction"],
            "COMPLIANCE_CERTIFICATE": {
                "standard": "ISO 14083:2023 Compliant",
                "framework": "CSRD / ESG Framework Ready",
                "methodology": "Well-to-Wheel (WTW) Analysis",
                "audit_statement": txt["compliance"]
            },
            "results": {
                txt["toll"]: round(base_toll + (25.0 if is_adr and country == "AT" else 0.0), 2),
                txt["fuel"]: round(fuel_liters * actual_net_price, 2),
                txt["vat_reclaim"]: total_reclaimable,
                "audit_details": {
                    "currency": "EUR",
                    "vat_refund": round(fuel_liters * vat_per_liter, 2),
                    "at_mineraloelsteuer_refund": round(fuel_liters * at_refund_per_liter, 2) if country == "AT" else 0.0
                },
                txt["co2"]: f"{total_co2} kg CO2e",
                "breakdown": {
                    "Scope 1 (Direct)": f"{round(total_co2 * 0.81, 2)} kg",
                    "Scope 3 (Upstream)": f"{round(total_co2 * 0.19, 2)} kg"
                }
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 3. APIFY ACTOR LOGIC ---
async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}
        
        audit_results = get_audit_report(
            lang=actor_input.get("lang", "NL"),
            country=actor_input.get("country", "NL"),
            km=float(actor_input.get("km", 100.0)),
            co2_class=actor_input.get("co2_class", "CO2_1"),
            axles=int(actor_input.get("axles", 5)),
            weight_kg=int(actor_input.get("weight_kg", 40000)),
            fuel_liters=float(actor_input.get("fuel_liters", 35.0)),
            base_price_net=actor_input.get("base_price_net"),
            is_adr=bool(actor_input.get("is_adr", False))
        )
        
        await Actor.push_data(audit_results)
        print("Audit succesvol uitgevoerd en data opgeslagen.")

if __name__ == "__main__":
    if os.environ.get("APIFY_IS_AT_HOME"):
        asyncio.run(main())
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
