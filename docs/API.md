# 📡 API Documentation

## Overview

The Stock Data Viewer API provides endpoints for accessing stock data, managing cache, and applying filters. All endpoints return JSON responses.

## Base URL

- **Local Development**: `http://localhost:5000`
- **Production**: `https://your-app.onrender.com`

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

## Endpoints

### 1. Main Application Interface

**GET** `/`

Returns the main HTML interface for the stock data viewer.

**Response**: HTML page

---

### 2. Get All Stock Data

**GET** `/api/stocks`

Returns complete stock data for all S&P 500 companies.

**Response**:
```json
[
  {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "price": 175.43,
    "market_cap": 2800000000000,
    "sector": "Technology",
    "eps_growth": {
      "quarter_over_quarter": 12.5
    },
    "relative_strength": {
      "rs_spy": 8.3,
      "rs_sector": 5.7
    },
    "ema_data": {
      "D_9EMA": 174.50,
      "D_21EMA": 172.80,
      "D_50EMA": 168.90,
      "W_9EMA": 175.20,
      "W_21EMA": 170.40,
      "W_50EMA": 165.80,
      "M_9EMA": 180.10,
      "M_21EMA": 175.30
    },
    "eps_history": {
      "quarterly": {
        "2024-07-01": 1.65,
        "2024-04-01": 2.40,
        "2024-01-01": 0.97,
        "2023-10-01": 1.40
      }
    }
  }
]
```

---

### 3. Refresh Stock Data

**POST** `/api/refresh`

Triggers a refresh of stock data from Yahoo Finance and updates the cache.

**Response**:
```json
{
  "message": "Data refreshed successfully and cache updated",
  "count": 503,
  "cache_updated": true
}
```

**Error Response**:
```json
{
  "message": "Failed to refresh data",
  "count": 0,
  "cache_updated": false
}
```

---

### 4. Apply Filters

**POST** `/api/filter`

Apply filters to stock data. Currently handled client-side, but endpoint exists for future server-side filtering.

**Request Body**:
```json
{
  "filters": [
    {
      "metric": "eps_growth",
      "threshold": 25.0
    },
    {
      "metric": "rs_spy",
      "threshold": 10.0
    }
  ]
}
```

**Response**: Filtered stock data array

---

### 5. Get Cache Status

**GET** `/api/cache/status`

Returns information about the current cache status.

**Response**:
```json
{
  "cache_exists": true,
  "cache_valid": true,
  "last_updated": "2025-10-04 21:18 PST",
  "cache_age_hours": 0.5
}
```

---

### 6. Clear Cache

**POST** `/api/cache/clear`

Clears the current cache and forces fresh data fetch on next request.

**Response**:
```json
{
  "message": "Cache cleared successfully",
  "success": true
}
```

## Data Models

### Stock Object

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Stock ticker symbol |
| `company_name` | string | Full company name |
| `price` | float | Current stock price |
| `market_cap` | integer | Market capitalization |
| `sector` | string | Business sector |
| `eps_growth` | object | EPS growth data |
| `relative_strength` | object | RS calculations |
| `ema_data` | object | EMA values |
| `eps_history` | object | Historical EPS data |

### EPS Growth Object

| Field | Type | Description |
|-------|------|-------------|
| `quarter_over_quarter` | float | QoQ growth percentage |

### Relative Strength Object

| Field | Type | Description |
|-------|------|-------------|
| `rs_spy` | float | RS vs SPY percentage |
| `rs_sector` | float | RS vs sector ETF percentage |

### EMA Data Object

| Field | Type | Description |
|-------|------|-------------|
| `D_9EMA` | float | Daily 9-period EMA |
| `D_21EMA` | float | Daily 21-period EMA |
| `D_50EMA` | float | Daily 50-period EMA |
| `W_9EMA` | float | Weekly 9-period EMA |
| `W_21EMA` | float | Weekly 21-period EMA |
| `W_50EMA` | float | Weekly 50-period EMA |
| `M_9EMA` | float | Monthly 9-period EMA |
| `M_21EMA` | float | Monthly 21-period EMA |

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request
- **404**: Not Found
- **500**: Internal Server Error

Error responses include a `message` field with details:

```json
{
  "error": "Error message description",
  "status": 500
}
```

## Rate Limiting

- **Yahoo Finance API**: 1 second delay between requests
- **Retry Logic**: Exponential backoff for rate-limited requests
- **Cache**: Reduces API calls by serving cached data

## Performance

- **Response Time**: < 100ms for cached data
- **Data Size**: ~2MB for 503 stocks
- **Cache Hit Rate**: > 95% during normal operation

## Examples

### JavaScript Fetch Example

```javascript
// Get all stocks
fetch('/api/stocks')
  .then(response => response.json())
  .then(data => console.log(data));

// Refresh data
fetch('/api/refresh', { method: 'POST' })
  .then(response => response.json())
  .then(result => console.log(result.message));

// Get cache status
fetch('/api/cache/status')
  .then(response => response.json())
  .then(status => console.log(status));
```

### Python Requests Example

```python
import requests

# Get all stocks
response = requests.get('http://localhost:5000/api/stocks')
stocks = response.json()

# Refresh data
response = requests.post('http://localhost:5000/api/refresh')
result = response.json()
print(result['message'])
```

## Future Enhancements

- **Authentication**: JWT-based authentication
- **Rate Limiting**: Per-user rate limiting
- **Pagination**: Large dataset pagination
- **Real-time Updates**: WebSocket support
- **Advanced Filters**: Server-side filtering
- **Export**: CSV/Excel export functionality

