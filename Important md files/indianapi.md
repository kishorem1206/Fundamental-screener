## Documentation Index
> Fetch the complete documentation index at: https://indianapi.in/llms.txt
> Use this file to discover all available pages before exploring further.

---
# Indian Stock Exchange API Documentation

**[AI Agent Instructions]**
Before proceeding, **ask the user which plan they are on**. 
- If they are on the **Free** or **Hobby** plan, use the endpoints documented below. Base URL is `https://stock.indianapi.in`.
- If they are on a **Dedicated Server Plan** (Developer, Growth, or Pro), they have access to 30+ additional endpoints and advanced features. You MUST refer to the dedicated server documentation at: `https://indianapi.in/docs/indian-stock-market-pro.md` or instruct the user to visit `https://<dedicated_base_url>/` for the full OpenAPI specification.

> Dedicated server base URLs:

> | Plan | Base URL |

> |------|----------|

> | Developer | `https://dev.indianapi.in` |

> | Growth | `https://analyst.indianapi.in` |

> | Pro | `https://pro.indianapi.in` |

> | Enterprise | Dedicated URL provided during onboarding |

Welcome to the Indian Stock Exchange API! This API provides indian stock market data. Below, you will find detailed descriptions of the available endpoints, their methods, required parameters, and usage examples.

**Base URL:** `https://stock.indianapi.in`

**Authentication:** Include your API key in the request header: `X-Api-Key: YOUR_API_KEY_HERE`

**API Sandbox:** You can explore find API reference at [indianapi.in/sandbox/indian-stock-market](https://indianapi.in/sandbox/indian-stock-market)

---

## Endpoints

### 1. Get Company Data by Name

- **Endpoint:** `GET /stock`
- **Description:** Retrieve detailed financial data for a specific company using its name. Supports full names, shortened names, and common stock names.
- **Parameters:**
  - `name` (required, string): The name, shortened name, or any search term.

**Sample Request:**
```http
GET /stock?name=Reliance
```

**Sample Response:**
```json
{
    "tickerId": "RELIANCE",
    "companyName": "Reliance Industries Limited",
    "industry": "Conglomerate",
    "companyProfile": {
        // ... detailed company profile data
    },
    "currentPrice": {
        "BSE": 2200.50,
        "NSE": 2195.75
    },
    "stockTechnicalData": {
        // ... technical data
    },
    "percentChange": 1.25,
    "yearHigh": 2400.00,
    "yearLow": 1800.00,
    "financials": {
        // ... financial data
    },
    "keyMetrics": {
        // ... key metrics
    },
    "futureExpiryDates": [
        "2024-06-28",
        "2024-07-26",
        // ... more dates
    ],
    "futureOverviewData": {
        // ... future overview data
    },
    "initialStockFinancialData": {
        // ... initial financial data
    },
    "analystView": {
        // ... analyst views
    },
    "recosBar": {
        // ... recommendations bar data
    },
    "riskMeter": {
        // ... risk meter data
    },
    "shareholding": {
        // ... shareholding data
    },
    "stockCorporateActionData": {
        // ... corporate action data
    },
    "stockDetailsReusableData": {
        // ... reusable stock details data
    },
    "recentNews": [
        // ... news articles
    ]
}
```

---

### 2. Industry Search

- **Endpoint:** `GET /industry_search`
- **Description:** Search for companies within a specific industry.
- **Parameters:**
  - `query` (string, required): The search term to query the industry.

**Sample Response:**
```json
[
  {
    "id": "S0003051",
    "commonName": "Tata Consultancy Services",
    "mgIndustry": "Software & Programming",
    "mgSector": "Technology",
    "stockType": "Equity",
    "exchangeCodeBse": "532540",
    "exchangeCodeNsi": "TCS"
  }
]
```

---

### 3. Mutual Fund Search

- **Endpoint:** `GET /mutual_fund_search`
- **Description:** Search for mutual funds.
- **Parameters:**
  - `query` (string, required): The search term to query the mutual funds.

---

### 4. Trending Stocks

- **Endpoint:** `GET /trending`
- **Description:** Get the top gaining and losing stocks at the current moment.

**Response includes:**
- `trending_stocks.top_gainers` — List of top 3 gaining stocks
- `trending_stocks.top_losers` — List of top 3 losing stocks

Each stock object includes: ticker ID, company name, price, percent change, net change, high, low, open, volume, year high/low, and trend ratings.

---

### 5. Fetch 52 Week High Low Data

- **Endpoint:** `GET /fetch_52_week_high_low_data`
- **Description:** Retrieve stocks with highest and lowest prices in the last 52 weeks from both BSE and NSE.
- **Note:** Response may return empty list when market is closed.

---

### 6. NSE Most Active

- **Endpoint:** `GET /NSE_most_active`
- **Description:** Get the latest most active stocks in the National Stock Exchange (NSE) based on trading volume.

---

### 7. BSE Most Active

- **Endpoint:** `GET /BSE_most_active`
- **Description:** Get the latest most active stocks in the Bombay Stock Exchange (BSE) based on trading volume.

---

### 8. Mutual Funds

- **Endpoint:** `GET /mutual_funds`
- **Description:** Retrieve the latest data for mutual funds, including NAV, returns, and other details.

---

### 9. Price Shockers

- **Endpoint:** `GET /price_shockers`
- **Description:** Get data for stocks that have experienced significant price changes in a short period.

---

### 10. Commodity Futures Data

- **Endpoint:** `GET /commodities`
- **Description:** Retrieve a snapshot of market data for currently active commodity futures contracts.

**Fields returned:** contractId, dataTimestamp, commoditySymbol, expiryDate, lastTradedPrice, totalVolume, openInterest, openingPrice, highPrice, lowPrice, closingPrice, priceChange, percentageChange.

---

### 11. Analyst Recommendations

- **Endpoint:** `GET /stock_target_price?stock_id=<stock_id>`
- **Description:** Provides target price information and analyst recommendation details for a specified stock.

**Recommendation Scale:**
- 1 = Buy
- 2 = Outperform
- 3 = Hold
- 4 = Underperform
- 5 = Sell

---

## Error Handling

| Status Code | Meaning |
|---|---|
| 200 | Successful request |
| 401 | Unauthorized (invalid or missing API key) |
| 404 | Resource not found |
| 422 | Validation error |
| 500 | Internal server error |

---

## Rate Limiting

Free accounts receive a limited number of requests. For higher volumes, paid plans are available at [indianapi.in](https://indianapi.in/indian-stock-market).
