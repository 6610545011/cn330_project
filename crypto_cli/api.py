from fastapi import FastAPI, Query, HTTPException
from .utils import get_crypto_price, get_top_coins, search_coins, get_coin_details, _get_coin_map, get_tickers, get_ticker

# Create a FastAPI app instance
crypto_cli = FastAPI()

@crypto_cli.get("/")
def root():
    return {"message": "Welcome to the Crypto API! Visit /docs for documentation."}

@crypto_cli.get("/price/{coin}")
def price(coin: str):
    data = get_crypto_price(coin)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@crypto_cli.get("/top")
def top_coins(limit: int = Query(10, ge=1, le=100)):
    return get_top_coins(limit)

@crypto_cli.get("/tickers")
def tickers(limit: int = Query(100, ge=1, le=1000)):
    return get_tickers(limit)

@crypto_cli.get("/tickers/{coin}")
def ticker(coin: str):
    data = get_ticker(coin)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@crypto_cli.get("/search")
def search(query: str = Query(..., min_length=1)):
    return search_coins(query)

@crypto_cli.get("/details/{coin_id}")
def details(coin_id: str):
    data = get_coin_details(coin_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data