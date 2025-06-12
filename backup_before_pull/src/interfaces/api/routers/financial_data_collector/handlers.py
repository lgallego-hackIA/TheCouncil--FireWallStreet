import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import HTTPException, BackgroundTasks

from .financial_data_service import FinancialDataService

logger = logging.getLogger(__name__)

async def handle_get_test(
    params: Dict[str, Any],
    repository: Optional[Any],
    automation: Any,
    endpoint: Any,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Dict[str, Any]:
    """
    Handler for GET /test
    Endpoint de prueba simple que no depende de servicios externos.
    """
    try:
        logger.info(f"Executing handler: handle_get_test for automation {automation.id if hasattr(automation, 'id') else str(automation)}")
        return {
            "success": True,
            "time": datetime.now().isoformat(),
            "message": "Endpoint de prueba está funcionando correctamente",
            "endpoint_path": "/test",
            "automation_id": automation.id if hasattr(automation, 'id') else str(automation),
            "handler_function": "handle_get_test"
        }
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.exception(f"Error in test endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Error in test: {str(e)}", "trace": error_detail}
        )

async def handle_get_stock_price(
    params: Dict[str, Any],
    repository: Optional[Any],
    automation: Any,
    endpoint: Any,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Dict[str, Any]:
    """
    Handler for GET /stock-price
    Obtiene el precio actual de las acciones.
    """
    service = FinancialDataService()
    symbol = params.get("symbol", "GPRK")
    try:
        logger.info(f"Handler handle_get_stock_price: Request for stock price for {symbol}")
        result = await service.get_stock_price(symbol)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.exception(f"Handler handle_get_stock_price: Error getting stock price: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Error getting stock price: {str(e)}", "trace": error_detail}
        )

async def handle_get_brent_price(
    params: Dict[str, Any],
    repository: Optional[Any],
    automation: Any,
    endpoint: Any,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Dict[str, Any]:
    """
    Handler for GET /brent-price
    Obtiene el precio actual del petróleo Brent.
    """
    service = FinancialDataService()
    try:
        logger.info("Handler handle_get_brent_price: Request for Brent price")
        result = await service.get_brent_price()
        if "error" in result:
             if result.get("source") and "previous execution" in result["source"]:
                return result
             raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.exception(f"Handler handle_get_brent_price: Error getting Brent price: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Error getting Brent price: {str(e)}", "trace": error_detail}
        )

async def handle_get_trading_volume(
    params: Dict[str, Any],
    repository: Optional[Any],
    automation: Any,
    endpoint: Any,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Dict[str, Any]:
    """
    Handler for GET /trading-volume
    Obtiene el volumen de transacciones.
    """
    service = FinancialDataService()
    symbol = params.get("symbol", "GPRK")
    try:
        logger.info(f"Handler handle_get_trading_volume: Request for trading volume for {symbol}")
        result = await service.get_trading_volume(symbol)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.exception(f"Handler handle_get_trading_volume: Error getting trading volume: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Error getting trading volume: {str(e)}", "trace": error_detail}
        )

async def handle_get_market_cap(
    params: Dict[str, Any],
    repository: Optional[Any],
    automation: Any,
    endpoint: Any,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Dict[str, Any]:
    """
    Handler for GET /market-cap
    Obtiene la capitalización de mercado.
    """
    service = FinancialDataService()
    symbol = params.get("symbol", "GPRK")
    try:
        logger.info(f"Handler handle_get_market_cap: Request for market cap for {symbol}")
        result = await service.get_market_cap(symbol)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.exception(f"Handler handle_get_market_cap: Error getting market cap: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Error getting market cap: {str(e)}", "trace": error_detail}
        )

async def handle_get_all_data(
    params: Dict[str, Any],
    repository: Optional[Any],
    automation: Any,
    endpoint: Any,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Dict[str, Any]:
    """
    Handler for GET /all-data
    Obtiene todos los datos financieros.
    """
    service = FinancialDataService()
    symbol = params.get("symbol", "GPRK")
    try:
        logger.info(f"Handler handle_get_all_data: Request for all financial data for {symbol}")
        result = await service.get_all_financial_data(symbol)
        return result
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.exception(f"Handler handle_get_all_data: Error getting all financial data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Error getting all financial data: {str(e)}", "trace": error_detail}
        )

async def handle_get_collect(
    params: Dict[str, Any],
    repository: Optional[Any],
    automation: Any,
    endpoint: Any,
    background_tasks: Optional[BackgroundTasks] = None,
) -> Dict[str, Any]:
    """
    Handler for GET /collect
    Desencadena la recopilación de todos los datos financieros.
    """
    service = FinancialDataService()
    symbol = params.get("symbol", "GPRK")
    try:
        logger.info(f"Handler handle_get_collect: Triggering data collection for {symbol}")
        result = await service.get_all_financial_data(symbol)
        return {
            "message": f"Data collection triggered/fetched for symbol {symbol}",
            "data": result,
            "automation_id": automation.id if hasattr(automation, 'id') else str(automation),
            "handler_function": "handle_get_collect",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.exception(f"Handler handle_get_collect: Error during data collection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Error during data collection: {str(e)}", "trace": error_detail}
        )
