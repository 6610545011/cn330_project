import requests

COINPAPRIKA_API_URL = "https://api.coinpaprika.com/v1"

# Use a session for connection pooling
session = requests.Session()

# In-memory cache for the coin map to avoid repeated API calls.
_coin_map = None

def _get_coin_map():
    """
    Fetches all coins and creates a mapping from symbol (lowercase) to coin ID.
    The result is cached in memory to be used for subsequent lookups.
    It prioritizes active, top-ranked coins for duplicate symbols.
    """
    global _coin_map
    if _coin_map is not None:
        return _coin_map

    try:
        url = f"{COINPAPRIKA_API_URL}/coins"
        response = session.get(url)
        response.raise_for_status()
        coins = response.json()

        # Normalize fields and provide safe defaults so missing data doesn't break sorting
        def safe_key(c):
            is_active = bool(c.get('is_active'))
            # Use a large number for missing ranks so they appear after ranked coins
            rank = c.get('rank') if isinstance(c.get('rank'), (int, float)) else float('inf')
            # We want active coins first, then lower rank (1 is higher) first
            return (0 if is_active else 1, rank)

        coins.sort(key=safe_key)

        # Build the map (first occurrence wins for duplicate symbols)
        mapping = {}
        for c in coins:
            sym = (c.get('symbol') or '').lower()
            cid = c.get('id')
            if sym and cid and sym not in mapping:
                mapping[sym] = cid

        _coin_map = mapping
        return _coin_map
    except Exception:
        # If we can't build the map for any reason, return an empty dict.
        # We catch all exceptions here to avoid unexpected crashes in the API.
        return {}

def get_crypto_price(coin: str):
    """Gets the price of a single cryptocurrency from Coinpaprika."""
    coin_map = _get_coin_map()
    coin_lower = coin.lower()

    # Find the coin ID: try map for symbols first
    coin_id = coin_map.get(coin_lower)

    # If not found in the map, determine whether input looks like an ID (contains '-')
    # or is likely a symbol. For symbol-like inputs, try the search endpoint as a fallback.
    if not coin_id:
        if '-' in coin_lower:
            coin_id = coin_lower
        else:
            # Fallback: try the search endpoint to resolve common symbol inputs (e.g., 'btc')
            try:
                search_url = f"{COINPAPRIKA_API_URL}/search?q={coin}&c=currencies"
                search_resp = session.get(search_url)
                search_resp.raise_for_status()
                results = search_resp.json().get('currencies', [])

                # Prefer exact symbol match (case-insensitive), else take first result
                match = None
                for c in results:
                    if c.get('symbol', '').lower() == coin_lower:
                        match = c
                        break
                if not match and results:
                    match = results[0]

                if match:
                    coin_id = match.get('id', coin_lower)
                else:
                    coin_id = coin_lower
            except requests.exceptions.RequestException:
                # If search fails, fall back to treating input as ID (will likely 404)
                coin_id = coin_lower
    url = f"{COINPAPRIKA_API_URL}/tickers/{coin_id}"
    try:
        response = session.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return {
            "name": data["name"],
            "symbol": data["symbol"],
            "price": data["quotes"]["USD"]["price"]
        }
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            return {"error": f"Coin with symbol or ID '{coin}' not found."}
        return {"error": f"HTTP error occurred: {http_err}"}
    except (KeyError, TypeError):
        return {"error": f"Invalid data structure for coin '{coin}'"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Request failed: {req_err}"}

def get_top_coins(limit: int = 10):
    """Gets the top N coins by market cap."""
    url = f"{COINPAPRIKA_API_URL}/tickers?quotes=USD"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        # Sort by rank and take the top N
        return sorted(data, key=lambda x: x['rank'])[:limit]
    except requests.exceptions.RequestException as e:
        return {"error": f"Could not fetch top coins: {e}"}

def search_coins(query: str):
    """Searches for coins by name or symbol."""
    url = f"{COINPAPRIKA_API_URL}/search?q={query}&c=currencies"
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.json().get('currencies', [])
    except requests.exceptions.RequestException as e:
        return {"error": f"Could not perform search: {e}"}

def get_coin_details(coin_id: str):
    """Gets detailed information about a specific coin."""
    coin_map = _get_coin_map()
    coin_lower = coin_id.lower()
    # Resolve symbol to ID, or use the input if it's already an ID
    resolved_id = coin_map.get(coin_lower, coin_lower)

    url = f"{COINPAPRIKA_API_URL}/coins/{resolved_id}"
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Could not fetch details for coin '{coin_id}': {e}"}