"""
Router implementation for Market-Asset-Fetcher automation.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import yfinance as yf
from datetime import datetime

# Use original name with dashes for route paths and tags
router = APIRouter(tags=["market-asset-fetcher"])

# Health check endpoint for this automation
@router.get("/health")
async def health_check():
    """
    Health check endpoint for market-asset-fetcher automation
    """
    return {
        "service": "market-asset-fetcher",
        "status": "healthy",
        "message": "market-asset-fetcher automation is operating normally"
    }

# Custom endpoint path from user input
@router.get("")
async def get_market_asset_fetcher_endpoint():
    """
    Main endpoint for the market-asset-fetcher automation
    """
    return {"message": "market-asset-fetcher endpoint", "status": "success"}

@router.get("/geopark")
async def get_geopark_stock():
    """
    Fetch the current value of Geopark stock (NYSE: GPRK)
    """
    try:
        # Get Geopark ticker information
        ticker = yf.Ticker("GPRK")
        
        # Get the latest market data
        ticker_data = ticker.history(period="1d")
        
        if ticker_data.empty:
            raise HTTPException(status_code=404, detail="Could not fetch Geopark stock data")
            
        # Get the latest close price
        latest_price = ticker_data['Close'].iloc[-1]
        latest_date = ticker_data.index[-1].strftime('%Y-%m-%d')
        
        # Get additional information
        info = ticker.info
        company_name = info.get('longName', 'GeoPark Limited')
        currency = info.get('currency', 'USD')
        
        return {
            "symbol": "GPRK",
            "company": company_name,
            "price": round(latest_price, 2),
            "currency": currency,
            "date": latest_date,
            "exchange": "NYSE",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Geopark stock data: {str(e)}")

# Standard CRUD endpoints for reference - comment out or remove if not needed

# @router.get("")
# async def list_market_asset_fetcher():
#     """
#     List all market-asset-fetchers
#     """
#     return {"message": "List market-asset-fetchers endpoint"}

# @router.get("/{item_id}")
# async def get_market_asset_fetcher(item_id: str):
#     """
#     Get a specific market-asset-fetcher by ID
#     """
#     return {"message": f"Get market-asset-fetcher {item_id}", "id": item_id}

# @router.post("")
# async def create_market_asset_fetcher(data: Dict[str, Any]):
#     """
#     Create a new market-asset-fetcher
#     """
#     return {"message": "Create market-asset-fetcher endpoint", "data": data}

# @router.put("/{item_id}")
# async def update_market_asset_fetcher(item_id: str, data: Dict[str, Any]):
#     """
#     Update a market-asset-fetcher by ID
#     """
#     return {"message": f"Update market-asset-fetcher {item_id}", "id": item_id, "data": data}

# @router.delete("/{item_id}")
# async def delete_market_asset_fetcher(item_id: str):
#     """
#     Delete a market-asset-fetcher by ID
#     """
#     return {"message": f"Delete market-asset-fetcher {item_id}", "id": item_id}
