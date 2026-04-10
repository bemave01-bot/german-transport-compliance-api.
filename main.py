from fastapi import FastAPI, HTTPException, Header
from typing import Optional

app = FastAPI()

# Dit is je geheime sleutel. Alleen ZylaLabs en jij weten dit.
API_SECRET_KEY = "TransitIntegrity_Secret_2026"

def verify_key(x_api_key: Optional[str]):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(
            status_code=401, 
            detail="Unauthorized: Invalid or missing API Key. Access the API via ZylaLabs."
        )

@app.get("/")
async def root():
    return {"message": "Transport Compliance API is running. Access via ZylaLabs recommended."}

@app.get("/transport/fuel-compliance")
async def get_fuel_compliance(country: str, x_api_key: Optional[str] = Header(None)):
    # Controleer de beveiligingssleutel
    verify_key(x_api_key)
    
    country = country.upper()
    if country == "NL":
        return {
            "status": "success",
            "country": "NL",
            "data": {
                "diesel_price": "€1.79",
                "hvo100_price": "€2.15",
                "adblue_price": "€0.85",
                "vat_rate": "21%",
                "disclaimer": "Berekening op basis van Nederlandse wetgeving 2026."
            }
        }
    elif country == "DE":
        return {
            "status": "success",
            "country": "DE",
            "data": {
                "diesel_price": "€1.65",
                "adblue_price": "€0.75",
                "co2_tax": "€0.12 per liter",
                "vat_rate": "19%"
            }
        }
    elif country == "AT":
        return {
            "status": "success",
            "country": "AT",
            "data": {
                "diesel_price": "€1.68",
                "vat_rate": "20%",
                "note": "Inclusief Oostenrijkse CO2-beprijzing."
            }
        }
    else:
        raise HTTPException(status_code=404, detail="Country not supported. Use NL, DE or AT.")

@app.get("/transport/toll-calculator")
async def calculate_toll(country: str, distance_km: float, x_api_key: Optional[str] = Header(None)):
    # Controleer de beveiligingssleutel
    verify_key(x_api_key)
    
    country = country.upper()
    rates = {"NL": 0.15, "DE": 0.35, "AT": 0.25}
    
    if country not in rates:
        raise HTTPException(status_code=404, detail="Country not supported for toll.")
    
    total_cost = round(distance_km * rates[country], 2)
    return {
        "status": "success",
        "country": country,
        "distance": f"{distance_km} km",
        "total_toll_cost": f"€{total_cost}",
        "rate_per_km": f"€{rates[country]}"
    }
