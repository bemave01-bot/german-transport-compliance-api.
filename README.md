# 🚛 EU Truck Toll Calculator — ISO 14083, CSRD (NL, DE, AT)

**Calculate truck toll costs, VAT reclaim, CO₂ emissions and fuel audit reports per country. ISO 14083:2023 & CSRD compliant. Built for carriers, accountants and logistics planners.**

---

## ✅ What This Actor Does

Enter your trip details (kilometers, fuel, vehicle weight, CO2 class) and instantly receive a professional audit report including:

- 🛣️ **Toll costs** — LKW-Maut (DE), Vrachtwagenheffing (NL), GO-Maut (AT)
- ⛽ **Fuel cost calculation** — with live diesel prices per country
- 💰 **VAT reclaim** — reclaimable VAT and excise duties per country
- 🌍 **CO2 emissions** — Scope 1 & Scope 3 (Well-to-Wheel, ISO 14083:2023)
- 📋 **CSRD audit report** — ready for ESG reporting

> ⚠️ **Important:** For international trips, run the Actor **separately per country** for accurate results.

---

## 🌍 Supported Countries

| Country | Toll Logic | Fuel Source | Special Feature |
|---|---|---|---|
| 🇳🇱 Netherlands | Vrachtwagenheffing 2026 | United Consumers | CO2-class differentiation |
| 🇩🇪 Germany | Toll Collect LKW-Maut 2026 | MTS-K index | CO2 surcharge included |
| 🇦🇹 Austria | ASFINAG GO-Maut (axle-based) | E-Control | Mineralölsteuer-Rückvergütung |

🇵🇱 🇮🇹 🇫🇷 🇪🇸 🇨🇭 **More countries coming soon.**

---

## 📥 Input Fields

| Field | Type | Description | Default |
|---|---|---|---|
| `country` | string | Country: NL, DE or AT | DE |
| `lang` | string | Report language: EN, NL or DE | EN |
| `km` | number | Kilometers driven in this country | 250 |
| `co2_class` | string | CO2 emission class: CO2_1 (Euro I) to CO2_5 (Euro VI) | CO2_3 |
| `axles` | integer | Number of axles (2–10) | 5 |
| `weight_kg` | integer | Vehicle weight in kg (3,500–60,000) | 40000 |
| `fuel_liters` | number | Diesel consumed in liters | 87.5 |
| `base_price_net` | number | Optional: your net diesel price per liter | auto |
| `is_adr` | boolean | ADR dangerous goods (adds AT surcharge) | false |

---

## 📤 Output Example

```json
{
  "COMPLIANCE_CERTIFICATE": {
    "standard": "ISO 14083:2023 Compliant",
    "framework": "CSRD / ESG Framework Ready",
    "methodology": "Well-to-Wheel (WTW) Analysis"
  },
  "results": {
    "Total Toll (Infrastructure Charge)": 83.25,
    "Net Fuel Costs": 145.60,
    "Reclaimable Taxes (VAT + Excise)": 28.43,
    "CO2 Emissions Report": "284.38 kg CO2e",
    "breakdown": {
      "Scope 1 (Direct)": "230.35 kg",
      "Scope 3 (Upstream)": "54.03 kg"
    }
  }
}
```

---

## 💎 Key Features

- **ISO 14083:2023 compliant** — accepted for official transport emissions audits
- **CSRD & ESG ready** — automatic Scope 1 and Scope 3 breakdown
- **Live fuel prices** — real-time diesel prices per country with fallback
- **VAT & excise reclaim** — including Austrian Mineralölsteuer-Rückvergütung
- **Multilingual output** — reports in English, Dutch or German
- **Input validation** — clear error messages for invalid inputs
- **2026 toll rates** — updated for latest EU toll reforms

---

## 🛠 How To Use

1. Select your **country** (run separately per country for international trips)
2. Enter **kilometers**, **fuel liters** and **vehicle details**
3. Choose your **CO2 emission class** (check your vehicle registration)
4. Run the Actor and download your **audit report**

---

## 🇳🇱 Nederlandse uitleg

Bereken tolkosten, BTW-teruggave en CO₂-uitstoot per rit. Volledig conform ISO 14083:2023 en geschikt voor CSRD-rapportage. Voer internationale ritten per land in voor nauwkeurige resultaten.

## 🇩🇪 Deutsche Erklärung

Berechnen Sie LKW-Maut, MwSt.-Erstattung und CO₂-Emissionen pro Fahrt. ISO 14083:2023-konform und CSRD-ready. Für internationale Fahrten bitte pro Land separat ausführen.

---

*Maintained by Audit Logistics | Updated for 2026 EU toll regulations*
