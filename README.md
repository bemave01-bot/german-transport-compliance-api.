# 🚛 Transport Compliance Pro API (NL-DE-AT) 2026
**The definitive fiscal and operational data bridge for logistics in the Netherlands, Germany, and Austria.**

[![Status](https://img.shields.io/badge/Status-Live-green.svg)](https://render.com)
[![Compliance](https://img.shields.io/badge/Compliance-Accountant--Ready-blue.svg)](#)
[![Year](https://img.shields.io/badge/Year-2026-orange.svg)](#)

## 🌐 Overview
The **Transport Compliance Pro API** provides logistics companies, software developers, and fleet managers with mission-critical data for the 2026 fiscal year. Operating across the NL-DE-AT corridor, this API automates the calculation of fuel costs, VAT recoveries, and complex toll regimes.

### 🚀 Key Capabilities
* **Intelligent Toll Calculation:** Support for German LKW-Maut (BFStrMG), Austrian GO-Maut (ASFINAG), and the new Dutch 'Vrachtwagenheffing' (starting July 1, 2026).
* **Energy & Fuel Compliance:** Projected 2026 pricing for Diesel, HVO100, and AdBlue, including CO2 emission factors per liter.
* **Automatic Localization:** The API detects the requested country and switches technical terms (Net/Gross/VAT) between **English, Dutch, and German** automatically.
* **Accountant-Ready Data:** Every response includes VAT breakdowns and legal disclaimers to ensure financial compliance.

---

## 🛠 API Endpoints & Usage

### 1. Fuel & Energy Compliance
Retrieve current projections for fuel prices, including VAT and CO2-kg/l impact.
- **Endpoint:** `/transport/fuel-compliance`
- **Parameters:** `country` (NL, DE, AT)

### 2. International Toll Calculator
Calculate total trip costs based on vehicle weight, CO2 class, and distance.
- **Endpoint:** `/transport/toll-calculator`
- **Parameters:** `country`, `distance_km`, `vehicle_type`, `co2_class`

---

## ⚖️ Legal & Disclaimer
This API is designed for professional planning purposes. 
* **Projections:** All rates provided are 2026 estimates based on current legislative data.
* **Liability:** The provider is not liable for operational losses, fines, or fiscal discrepancies. 
* **Verification:** Users are encouraged to cross-reference data with official governmental portals for final audit purposes.

---

## 📈 Getting Started
To integrate this API into your TMS (Transport Management System) or ERP:
1. Access the Interactive Documentation at: `https://[YOUR-RENDER-URL].onrender.com/docs`
2. Use the **Try it out** feature to test live requests.
3. For commercial licenses and high-volume API keys, contact us via ZylaLabs.

---
© 2026 Transport Compliance Solutions | Powered by FastAPI
