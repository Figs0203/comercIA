# ComercIA – Public Products API Guide

## Overview
- Purpose: Provide a simple JSON feed of available products for allied teams to consume.
- Base URL: your deployment URL (e.g., `https://<your-domain>`)
- Primary Endpoint: `GET /api/products/`
- Auth: none (public)
- Format: JSON (UTF-8)

## Internationalization (i18n)
- URLs are language-aware via i18n_patterns.
- Request English via either:
  - Path prefix: `/en/api/products/`
  - Header: `Accept-Language: en`
- Field behavior:
  - `name` returns `name_en` when language is EN and the EN value exists; otherwise falls back to `name`.

## Endpoint
### GET /api/products/
Returns currently available products ordered by most recent publish date.

Query params: none

Response 200 OK:
```json
{
  "count": 2,
  "results": [
    {
      "id": 12,
      "name": "French Bread",
      "price": 19900.0,
      "category": "Comida",
      "available": true,
      "image_url": "https://your-domain/media/products/pan.jpg",
      "detail_url": "https://your-domain/product/12/"
    },
    {
      "id": 9,
      "name": "Eco Tote Bag",
      "price": 35000.0,
      "category": "Ropa",
      "available": true,
      "image_url": "https://your-domain/media/products/tote.jpg",
      "detail_url": "https://your-domain/product/9/"
    }
  ]
}
```

Field definitions:
- `id` (int): product identifier
- `name` (string): product name (language-aware)
- `price` (number): price
- `category` (string): internal category code
- `available` (bool): availability flag
- `image_url` (string|null): absolute URL to image
- `detail_url` (string): absolute URL to product detail page

Errors:
- 500: server error (unexpected)

## How to consume
### cURL
```bash
curl -s https://your-domain/api/products/ | jq .
```

### cURL (English)
```bash
curl -s -H "Accept-Language: en" https://your-domain/en/api/products/ | jq .
```

### JavaScript (fetch)
```js
async function loadAlliedProducts() {
  const res = await fetch('https://your-domain/api/products/', {
    headers: { 'Accept-Language': 'en' }
  });
  if (!res.ok) throw new Error('Failed to fetch');
  const data = await res.json();
  return data.results;
}
```

### Python (requests)
```python
import requests
r = requests.get('https://your-domain/api/products/', headers={'Accept-Language': 'en'})
r.raise_for_status()
products = r.json()['results']
```

## Consumption guidelines
- Polling: ≥ 60s interval recommended.
- Cache responses for 60–120s on client.
- Display `image_url` directly; handle nulls.
- Link to `detail_url` for product details.

## Versioning
- Current v1 (unversioned). Breaking changes will introduce `/api/v2/products/`.

## Availability & limits
- Public, no auth.
- Suggested rate: ≤ 1 req/min.

## Share with allied team
- Provide: the production URL, this guide, and one sample response.
- Language handling: use `/en/` or `Accept-Language: en` to prefer English names.

## Implementation reference
- URL: `comercia/urls.py` → `path('api/products/', products_views.products_api, ...)`
- View: `products/views.py` → `products_api`
- Language: `request.LANGUAGE_CODE` selects `name_en` when EN.

## Contact
- Need extra fields (stock, seller link, etc.)? Request a non-breaking extension; we’ll add fields without changing the endpoint.
