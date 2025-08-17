from celery import shared_task
from typing import List, Dict, Optional
import logging
import asyncio
from datetime import datetime, timedelta
from app.services.polygon_service_enhanced import polygon_service_enhanced
from app.services.inefficiency_detector import inefficiency_detector
from app.models.opportunity import Opportunity
from app.models.scan_result import ScanResult
from app.core.database import SessionLocal
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.scanner_tasks.scan_all_markets")
def scan_all_markets(
    scan_config: Optional[Dict] = None
) -> Dict:
    """
    Main task to scan all configured markets for opportunities
    Enhanced version with proper error handling and free tier support
    """
    logger.info("Starting enhanced market scan across all asset classes")
    
    config = scan_config or {
        "equities": {"enabled": True, "min_volume": 1000000, "min_price_change": 0.02},
        "futures": {"enabled": False, "min_volume": 100, "min_price_change": 0.01},  # Disabled for free tier
        "fx": {"enabled": False, "min_volume": 10000, "min_price_change": 0.005}  # Disabled for free tier
    }
    
    results = {}
    errors = []
    
    # Update scan progress
    scan_all_markets.update_state(
        state='PROGRESS',
        meta={'current': 0, 'total': 3, 'status': 'Starting scan...'}
    )
    
    # Scan equities - call functions directly, not as subtasks
    if config.get("equities", {}).get("enabled", True):
        try:
            scan_all_markets.update_state(
                state='PROGRESS',
                meta={'current': 1, 'total': 3, 'status': 'Scanning equities...'}
            )
            # Call function directly instead of using apply_async().get()
            results["equities"] = scan_equities_enhanced(config.get("equities", {}))
        except Exception as e:
            logger.error(f"Error scanning equities: {e}")
            errors.append(f"Equities scan failed: {str(e)}")
            results["equities"] = []
    
    # Scan futures (if enabled and supported)
    if config.get("futures", {}).get("enabled", False):
        try:
            scan_all_markets.update_state(
                state='PROGRESS',
                meta={'current': 2, 'total': 3, 'status': 'Scanning futures...'}
            )
            # Call function directly instead of using apply_async().get()
            results["futures"] = scan_futures_enhanced(config.get("futures", {}))
        except Exception as e:
            logger.error(f"Error scanning futures: {e}")
            errors.append(f"Futures scan failed: {str(e)}")
            results["futures"] = []
    
    # Scan FX (if enabled and supported)
    if config.get("fx", {}).get("enabled", False):
        try:
            scan_all_markets.update_state(
                state='PROGRESS',
                meta={'current': 3, 'total': 3, 'status': 'Scanning FX...'}
            )
            # Call function directly instead of using apply_async().get()
            results["fx"] = scan_forex_enhanced(config.get("fx", {}))
        except Exception as e:
            logger.error(f"Error scanning FX: {e}")
            errors.append(f"FX scan failed: {str(e)}")
            results["fx"] = []
    
    # Store scan results in database
    try:
        store_scan_results(results)
    except Exception as e:
        logger.error(f"Error storing scan results: {e}")
        errors.append(f"Failed to store results: {str(e)}")
    
    total_opportunities = sum(len(v) for v in results.values())
    logger.info(f"Market scan completed. Found {total_opportunities} opportunities")
    
    # Final state
    scan_all_markets.update_state(
        state='SUCCESS',
        meta={
            'current': 3,
            'total': 3,
            'status': 'Scan complete',
            'opportunities': total_opportunities,
            'errors': errors
        }
    )
    
    return {
        "results": results,
        "errors": errors,
        "total_opportunities": total_opportunities,
        "timestamp": datetime.utcnow().isoformat()
    }


def scan_equities_enhanced(config: Optional[Dict] = None) -> List[Dict]:
    """
    Enhanced equity scanning with proper error handling and free tier support
    """
    logger.info("Running enhanced equity scan...")
    
    config = config or {}
    min_volume = config.get("min_volume", 1000000)
    min_price_change = config.get("min_price_change", 0.02)
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Use limited scan for free tier
        opportunities = loop.run_until_complete(
            polygon_service_enhanced.scan_for_opportunities_limited(
                asset_classes=["stocks"],
                min_volume=min_volume,
                min_price_change=min_price_change
            )
        )
        
        # Enrich opportunities with additional data
        enriched_opportunities = []
        for opp in opportunities[:10]:  # Limit to top 10 for free tier
            try:
                # Get last quote for bid/ask spread
                quote = loop.run_until_complete(
                    polygon_service_enhanced.get_last_quote(opp["ticker"])
                )
                
                if quote:
                    opp["spread"] = (quote["ask"] - quote["bid"]) / quote["bid"] if quote["bid"] > 0 else 0
                    opp["bid"] = quote["bid"]
                    opp["ask"] = quote["ask"]
                
                # Add basic inefficiency detection (simplified for free tier)
                opp["inefficiencies"] = [
                    {
                        "type": opp["opportunity_type"],
                        "score": abs(opp["price_change"]) * 100,
                        "description": f"{opp['opportunity_type'].capitalize()} opportunity detected"
                    }
                ]
                opp["primary_inefficiency"] = opp["inefficiencies"][0] if opp["inefficiencies"] else None
                opp["inefficiency_score"] = abs(opp["price_change"]) * 100
                
                opp["asset_class"] = "equities"
                opp["scan_timestamp"] = datetime.utcnow().isoformat()
                enriched_opportunities.append(opp)
                
            except Exception as e:
                logger.warning(f"Error enriching opportunity for {opp['ticker']}: {e}")
                # Still include the basic opportunity even if enrichment fails
                opp["asset_class"] = "equities"
                opp["scan_timestamp"] = datetime.utcnow().isoformat()
                enriched_opportunities.append(opp)
        
        logger.info(f"Found {len(enriched_opportunities)} equity opportunities")
        return enriched_opportunities
        
    except Exception as e:
        logger.error(f"Critical error in equity scan: {e}")
        # Return mock data if scan completely fails
        return get_mock_opportunities("equities")
    finally:
        loop.close()


def scan_futures_enhanced(config: Optional[Dict] = None) -> List[Dict]:
    """
    Enhanced futures scanning (limited for free tier)
    """
    logger.info("Futures scanning is limited on free tier")
    # Return empty or mock data for free tier
    return []


def scan_forex_enhanced(config: Optional[Dict] = None) -> List[Dict]:
    """
    Enhanced FX scanning (limited for free tier)
    """
    logger.info("FX scanning is limited on free tier")
    # Return empty or mock data for free tier
    return []


def get_mock_opportunities(asset_class: str) -> List[Dict]:
    """
    Generate mock opportunities for demonstration when API fails
    """
    import random
    
    mock_tickers = {
        "equities": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
        "futures": ["MES", "MNQ", "MYM", "M2K", "MGC"],
        "fx": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
    }
    
    opportunities = []
    for ticker in mock_tickers.get(asset_class, [])[:3]:
        price_change = random.uniform(-0.05, 0.05)
        opportunities.append({
            "ticker": ticker,
            "asset_class": asset_class,
            "volume": random.randint(1000000, 10000000),
            "price_change": price_change,
            "open": 100 * (1 + random.uniform(-0.01, 0.01)),
            "close": 100 * (1 + price_change),
            "high": 100 * (1 + abs(price_change) + 0.01),
            "low": 100 * (1 - abs(price_change) - 0.01),
            "opportunity_type": "momentum" if price_change > 0 else "reversal",
            "inefficiency_score": abs(price_change) * 100,
            "scan_timestamp": datetime.utcnow().isoformat(),
            "is_mock_data": True,
            "note": "Mock data - API unavailable"
        })
    
    return opportunities


def store_scan_results(results: Dict) -> None:
    """Store scan results in the database with error handling"""
    db: Session = SessionLocal()
    
    try:
        # Create scan result record
        scan_result = ScanResult(
            scan_id=f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            asset_classes=[k for k, v in results.items() if v],  # Only include classes with results
            opportunities_found=sum(len(v) for v in results.values()),
            symbols_scanned=sum(len(v) for v in results.values()),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            scan_metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "results_by_class": {k: len(v) for k, v in results.items()},
                "has_errors": any("is_mock_data" in opp for opps in results.values() for opp in opps)
            }
        )
        
        db.add(scan_result)
        db.commit()
        
        # Store individual opportunities
        for asset_class, opportunities in results.items():
            for opp in opportunities:
                try:
                    price_change = opp.get("price_change", 0)
                    opportunity = Opportunity(
                        asset_class=asset_class,
                        symbol=opp["ticker"],  # Use 'symbol' instead of 'ticker'
                        strategy_type=opp.get("opportunity_type", "unknown"),
                        opportunity_score=abs(price_change) * 100,
                        expected_return=price_change * 100,  # Convert to percentage
                        risk_level="medium" if abs(price_change) < 0.03 else "high",
                        entry_conditions={"price": opp.get("close", 0), "volume": opp.get("volume", 0)},
                        technical_indicators=opp,  # Store all data as technical indicators
                        market_conditions={"data_date": opp.get("data_date"), "note": opp.get("note")}
                    )
                    db.add(opportunity)
                except Exception as e:
                    logger.warning(f"Error storing opportunity {opp['ticker']}: {e}")
                    continue
        
        db.commit()
        logger.info(f"Stored scan results with ID: {scan_result.id}")
        
    except Exception as e:
        logger.error(f"Error storing scan results: {e}")
        db.rollback()
    finally:
        db.close()