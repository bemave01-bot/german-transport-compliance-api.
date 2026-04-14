# 🚛 EU Transport & ESG Audit Backend (2026)
**Core Engine for NL, DE & AT Transport Audits**

## 🌐 Overview
This API serves as the calculation engine for the Apify Transport Auditor. It handles real-time fuel scraping, 2026 toll regimes, and ISO 14083 compliant CO2 reporting.

### 🛠 Tech Stack
* **Framework:** FastAPI (Python)
* **Scraping:** BeautifulSoup4 (Live fuel prices)
* **Deployment:** Render.com
* **Compliance:** CSRD Scope 1 & 3, EU Directive 2022/362

## 🚀 Active Endpoint
### `GET /api/v1/transport/full-audit-report`
The primary endpoint used by the Apify Actor to generate a country-specific audit.

**Key Parameters:**
- `country`: NL, DE, AT
- `lang`: NL, DE, EN
- `co2_class`: CO2_1 to CO2_5
- `km`: Distance
- `fuel_liters`: Consumption

## 📅 2026 Roadmap Logic
* **NL Vrachtwagenheffing:** Automatically switches from €0.00 to official km-rates on **July 1st, 2026**.
* **DE Maut:** Uses 2026 CO2-weighted rates (>18t / 12-18t).
* **AT GO-Maut:** Includes 2026 ASFINAG category rates.

---
© 2026 [Jouw Bedrijfsnaam] | Audit-Ready Logistics Data
