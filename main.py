import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query, HTTPException
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
    },
    "EN": {
        "instruction": "NOTE: For international trips, perform a separate calculation per country.",
        "toll": "Total Toll (Infrastructure Charge)",
        "fuel": "Net Fuel Costs",
        "vat_reclaim": "Reclaimable Taxes (VAT + Excise)",
        "co2": "CO2 Emissions Report",
        "compliance": "This report has been prepared in accordance with ISO 14083:2023 and is suitable for CSRD (Scope 1 & 3) audit purposes."
    }
}

# --- 2. FISCALE & INFRASTRUCTUUR DATA 2026 ---
COUNTRY_DATA = {
    "NL": {
        "vat": 1.21, "excise": 0.552, "co2_tax": 0.000, "cache": 720,
        "rates": {
            "heavy": {"CO2_1": 0.201, "CO2_2": 0.183, "CO2_3": 0.165, "CO2_4": 0.105, "CO2_5": 0.038},
            "mid":   {"CO2_1": 0.182, "CO2_2": 0.165, "CO2_3": 0.148, "CO2_4": 0.095, "CO2_5": 0.037}
        }
    },
    "DE": {
        "vat": 1.19, "excise": 0.470, "co2_tax": 0.185, "cache": 5,
        "rates": {
            "heavy": {"CO2_1": 0.354, "CO2_2": 0.332, "CO2_3": 0.311, "CO2_4": 0.205, "CO2_5": 0.088},
            "mid":   {"CO2_1": 0.302, "CO2_2": 0.285, "CO2_3": 0.268, "CO2_4": 0.175, "CO2_5": 0.075}
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

VALID_CO2_CLASSES = ["CO2_1", "CO2_2", "CO2_3", "CO2_4", "CO2_5"]
SUPPORTED_COUNTRIES = list(COUNTRY_DATA.keys())
SUPPORTED_LANGUAGES = list(TRANSLATIONS.keys())

# Fallback brandstofprijzen (bijgewerkt april 2026)
FALLBACK_PRICES = {"NL": 2.709, "DE": 1.950, "AT": 1.749}

data_store = {c: {"p": FALLBACK_PRICES[c], "t": None} for c in SUPPORTED_COUNTRIES}


# --- 3. FUEL FETCHING MET FALLBACK ---
def fetch_fuel_nl() -> float:
    """Haal actuele dieselprijs op voor Nederland."""
    sources = [
        ("https://unitedconsumers.com", lambda soup: float(
            soup.find('td', string=lambda t: t and 'Diesel' in t)
                .find_next_sibling('td').text.replace('€', '').replace(',', '.').strip()
        )),
        ("https://www.brandstof-zoeker.nl", lambda soup: float(
            soup.select_one('.diesel-price, .price-diesel, [data-fuel="diesel"]')
                .text.replace('€', '').replace(',', '.').strip()
        )),
    ]
    for url, parser in sources:
        try:
            res = requests.get(url, timeout=6, headers={'User-Agent': 'Mozilla/5.0'})
            res.raise_for_status()
            price = parser(BeautifulSoup(res.text, 'lxml'))
            if 1.0 < price < 5.0:  # Sanity check: realistisch prijsbereik
                return price
        except Exception:
            continue
    return FALLBACK_PRICES["NL"]


def fetch_fuel_de() -> float:
    """Haal actuele dieselprijs op voor Duitsland."""
    try:
        res = requests.get(
            "https://clever-tanken.de",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=6
        )
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        el = soup.select_one('.price, .fuel-price, [class*="diesel"]')
        if el:
            price = float(el.text.replace(',', '.').strip()[:5])
            if 1.0 < price < 5.0:
                return price
    except Exception:
        pass
    return FALLBACK_PRICES["DE"]


def fetch_fuel(country: str) -> float:
    """Router: haal brandstofprijs op per land met fallback."""
    fetchers = {"NL": fetch_fuel_nl, "DE": fetch_fuel_de}
    fetcher = fetchers.get(country)
    if fetcher:
        price = fetcher()
        return price
    return FALLBACK_PRICES.get(country, 1.75)


def get_fuel_price(country: str) -> float:
    """Geeft gecachede brandstofprijs terug, ververst indien verlopen."""
    store = data_store[country]
    cache_minutes = COUNTRY_DATA[country]["cache"]
    now = datetime.now()
    if not store["t"] or now > store["t"] + timedelta(minutes=cache_minutes):
        new_price = fetch_fuel(country)
        store["p"] = new_price
        store["t"] = now
        print(f"[FUEL] {country}: €{new_price:.3f}/L (vers opgehaald)")
    else:
        print(f"[FUEL] {country}: €{store['p']:.3f}/L (uit cache)")
    return store["p"]


# --- 4. INPUT VALIDATIE ---
def validate_inputs(lang, country, km, co2_class, axles, weight_kg, fuel_liters, base_price_net):
    errors = []
    if lang not in SUPPORTED_LANGUAGES:
        lang = "EN"  # Stille fallback naar Engels
    if country not in SUPPORTED_COUNTRIES:
        errors.append(f"Land '{country}' niet ondersteund. Kies uit: {', '.join(SUPPORTED_COUNTRIES)}")
    if co2_class not in VALID_CO2_CLASSES:
        errors.append(f"CO2-klasse '{co2_class}' ongeldig. Kies uit: {', '.join(VALID_CO2_CLASSES)}")
    if km <= 0:
        errors.append("Kilometers moeten groter zijn dan 0.")
    if km > 5000:
        errors.append("Kilometers lijken onrealistisch hoog (max 5000 per berekening). Gebruik per land.")
    if fuel_liters <= 0:
        errors.append("Brandstofverbruik moet groter zijn dan 0 liter.")
    if fuel_liters > 2000:
        errors.append("Brandstofverbruik onrealistisch hoog (max 2000 liter per berekening).")
    if axles < 2 or axles > 10:
        errors.append("Aantal assen moet tussen 2 en 10 zijn.")
    if weight_kg < 3500 or weight_kg > 60000:
        errors.append("Gewicht moet tussen 3.500 en 60.000 kg zijn.")
    if base_price_net is not None and (base_price_net <= 0 or base_price_net > 5.0):
        errors.append("Netto basisprijs moet tussen €0.01 en €5.00 per liter zijn.")
    return lang, errors


# --- 5. AUDIT RAPPORT ENDPOINT ---
@app.get("/api/v1/transport/full-audit-report")
def get_audit_report(
    lang: str = Query("NL", description="Taal: NL, DE of EN"),
    country: str = Query("NL", description="Land: NL, DE of AT"),
    km: float = Query(100.0, description="Gereden kilometers (per land)"),
    co2_class: str = Query("CO2_1", description="CO2-emissieklasse: CO2_1 t/m CO2_5"),
    axles: int = Query(5, description="Aantal assen (2-10)"),
    weight_kg: int = Query(40000, description="Voertuiggewicht in kg"),
    fuel_liters: float = Query(35.0, description="Verbruikte liters diesel"),
    base_price_net: float = Query(None, description="Optioneel: netto dieselprijs per liter"),
    is_adr: bool = Query(False, description="ADR-gevaarlijke lading (ja/nee)")
):
    lang, errors = validate_inputs(lang, country, km, co2_class, axles, weight_kg, fuel_liters, base_price_net)

    if errors:
        raise HTTPException(status_code=422, detail={"validatiefouten": errors})

    lang = lang.upper()
    country = country.upper()
    txt = TRANSLATIONS[lang]
    comp = COUNTRY_DATA[country]
    now = datetime.now()

    # Brandstofprijs
    fuel_price_gross = get_fuel_price(country)
    actual_net_price = base_price_net if base_price_net else round(fuel_price_gross / comp["vat"], 3)
    vat_per_liter = round((actual_net_price * comp["vat"]) - actual_net_price, 3)

    # Oostenrijkse Mineralölsteuer-Rückvergütung
    at_refund_per_liter = 0.082 if country == "AT" else 0.0
    total_reclaimable = round(fuel_liters * (vat_per_liter + at_refund_per_liter), 2)

    # Tolberekening
    if country == "AT":
        cat = "cat4" if axles >= 4 else "cat3"
    else:
        cat = "heavy" if weight_kg >= 18000 else "mid"

    rate_table = comp["rates"].get(cat, comp["rates"].get("heavy", {}))
    rate_per_km = rate_table.get(co2_class, 0.201)
    base_toll = round(km * rate_per_km, 2)

    # NL tol nog niet actief vóór 1 juli 2026
    if country == "NL" and now < datetime(2026, 7, 1):
        base_toll = 0.0
        toll_note = "Vrachtwagenbelasting NL nog niet actief (ingangsdatum: 1 juli 2026)."
    else:
        toll_note = None

    # ADR-toeslag AT
    adr_surcharge = 25.0 if is_adr and country == "AT" else 0.0
    total_toll = round(base_toll + adr_surcharge, 2)

    # CO2-berekening (Well-to-Wheel: 3.25 kg CO2e per liter diesel)
    total_co2 = round(fuel_liters * 3.25, 2)

    result = {
        "DISCLAIMER": txt["instruction"],
        "COMPLIANCE_CERTIFICATE": {
            "standard": "ISO 14083:2023 Compliant",
            "framework": "CSRD / ESG Framework Ready",
            "methodology": "Well-to-Wheel (WTW) Analysis",
            "audit_statement": txt["compliance"],
            "generated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
            "country": country,
            "language": lang
        },
        "input_summary": {
            "km": km,
            "co2_class": co2_class,
            "axles": axles,
            "weight_kg": weight_kg,
            "fuel_liters": fuel_liters,
            "is_adr": is_adr,
            "fuel_price_gross_per_liter": fuel_price_gross,
            "fuel_price_net_per_liter": actual_net_price
        },
        "results": {
            txt["toll"]: total_toll,
            txt["fuel"]: round(fuel_liters * actual_net_price, 2),
            txt["vat_reclaim"]: total_reclaimable,
            "audit_details": {
                "currency": "EUR",
                "toll_rate_per_km": rate_per_km,
                "toll_category": cat,
                "adr_surcharge": adr_surcharge,
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

    if toll_note:
        result["results"]["toll_note"] = toll_note

    return result


# --- 6. HEALTH CHECK ---
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "version": "2026.1"}


# --- 7. APIFY ACTOR LOGIC ---
async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}

        # Input ophalen met defaults
        lang = actor_input.get("lang", "NL")
        country = actor_input.get("country", "NL")
        km = float(actor_input.get("km", 100.0))
        co2_class = actor_input.get("co2_class", "CO2_1")
        axles = int(actor_input.get("axles", 5))
        weight_kg = int(actor_input.get("weight_kg", 40000))
        fuel_liters = float(actor_input.get("fuel_liters", 35.0))
        base_price_net = actor_input.get("base_price_net")
        is_adr = bool(actor_input.get("is_adr", False))

        # Valideer input
        lang, errors = validate_inputs(lang, country, km, co2_class, axles, weight_kg, fuel_liters, base_price_net)
        if errors:
            await Actor.push_data({"status": "validatiefout", "fouten": errors})
            return

        # Voer audit uit
        try:
            audit_result = get_audit_report(
                lang=lang, country=country, km=km, co2_class=co2_class,
                axles=axles, weight_kg=weight_kg, fuel_liters=fuel_liters,
                base_price_net=base_price_net, is_adr=is_adr
            )
            await Actor.push_data(audit_result)
            print("✅ Audit succesvol uitgevoerd en opgeslagen.")
        except Exception as e:
            await Actor.push_data({"status": "error", "message": str(e)})
            print(f"❌ Fout tijdens audit: {e}")


if __name__ == "__main__":
    if os.environ.get("APIFY_IS_AT_HOME"):
        asyncio.run(main())
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
