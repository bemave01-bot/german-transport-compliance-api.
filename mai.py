from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="German Transport Compliance API (Incl. Historiendata)")

# Harde Maut Tabel 2026 (Cent per km)
MAUT_TABLE = {
    ">18t": {"c1": 34.8, "c2": 30.2, "c3": 25.0, "c4": 15.0, "c5": 8.7},
    "12-18t": {"c1": 23.8, "c2": 20.0, "c3": 16.0, "c4": 10.0, "c5": 5.9},
    "7.5-12t": {"c1": 21.0, "c2": 18.2, "c3": 14.5, "c4": 9.2, "c5": 5.1},
    "3.5-7.5t": {"c1": 15.1, "c2": 12.0, "c3": 9.0, "c4": 5.0, "c5": 0.0}
}

FUEL_DATA = {
    "diesel": {"netto_26": 1.47, "netto_25": 1.39, "co2": 2.64},
    "hvo100": {"netto_26": 1.81, "netto_25": 1.75, "co2": 0.25},
    "super_e10": {"netto_26": 1.54, "netto_25": 1.48, "co2": 2.31},
    "super_e5": {"netto_26": 1.59, "netto_25": 1.53, "co2": 2.39},
    "lpg": {"netto_26": 0.61, "netto_25": 0.58, "co2": 1.61},
    "adblue": {"netto_26": 0.71, "netto_25": 0.68, "co2": 0.0}
}

@app.get("/transport/fuel-compliance")
async def fuel_compliance():
    results = {}
    for fuel, data in FUEL_DATA.items():
        results[fuel] = {
            "2026_netto": data["netto_26"],
            "2026_bruto": round(data["netto_26"] * 1.19, 3),
            "2025_netto_avg": data["netto_25"],
            "diff_percent": round(((data["netto_26"] / data["netto_25"]) - 1) * 100, 2),
            "co2_kg_liter": data["co2"],
            "co2_tax_2026": "55 EUR/t",
            "co2_tax_2025": "45 EUR/t"
        }
    return {"status": "OK", "timestamp": datetime.now(), "data": results}

@app.get("/transport/maut-calculator")
async def calculate_maut(km: float, weight_class: str, co2_class: int):
    # Mapping input naar tabel
    key = f"c{co2_class}"
    base_rate = MAUT_TABLE.get(weight_class, MAUT_TABLE[">18t"]).get(key, 34.8)
    
    netto = (km * base_rate) / 100 # Van cent naar Euro
    bruto = netto * 1.19
    
    return {
        "calculation": {
            "distance_km": km,
            "weight": weight_class,
            "co2_class": co2_class,
            "eur_netto": round(netto, 2),
            "eur_bruto": round(bruto, 2),
            "rate_per_km_cent": base_rate
        },
        "legal": "BFStrMG § 2026 / German Toll Law"
    }
