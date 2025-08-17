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
    """
    logger.info("Starting market scan across all asset classes")
    
    config = scan_config or {
        "equities": {"enabled": True, "min_volume": 1000000, "min_price_change": 0.02},
        "futures": {"enabled": True, "min_volume": 100, "min_price_change": 0.01},
        "fx": {"enabled": True, "min_volume": 10000, "min_price_change": 0.005}
    }
    
    results = {}
    
    # Call functions directly instead of using apply_async().get() within a task
    if config.get("equities", {}).get("enabled", True):
        results["equities"] = scan_equities(config.get("equities", {}))
    
    if config.get("futures", {}).get("enabled", True):
        results["futures"] = scan_futures(config.get("futures", {}))
    
    if config.get("fx", {}).get("enabled", True):
        results["fx"] = scan_forex(config.get("fx", {}))
    
    # Store scan results in database
    store_scan_results(results)
    
    total_opportunities = sum(len(v) for v in results.values())
    logger.info(f"Market scan completed. Found {total_opportunities} opportunities")
    
    return results


@shared_task
def scan_equities(config: Optional[Dict] = None) -> List[Dict]:
    """Scan US equity markets for inefficiencies - enhanced version with free tier support"""
    logger.info("Scanning US equities with enhanced service...")
    
    config = config or {}
    min_volume = config.get("min_volume", 1000000)
    min_price_change = config.get("min_price_change", 0.02)
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Use enhanced service with rate limiting and free tier support
        opportunities = loop.run_until_complete(
            polygon_service_enhanced.scan_for_opportunities_limited(
                asset_classes=["stocks"],
                min_volume=min_volume,
                min_price_change=min_price_change
            )
        )
        
        # Enrich opportunities with additional data and detect inefficiencies
        enriched_opportunities = []
        for opp in opportunities[:20]:  # Limit to top 20
            # Get last quote for bid/ask spread
            quote = loop.run_until_complete(
                polygon_service_enhanced.get_last_quote(opp["ticker"])
            )
            
            if quote:
                opp["spread"] = (quote["ask"] - quote["bid"]) / quote["bid"] if quote["bid"] > 0 else 0
                opp["bid"] = quote["bid"]
                opp["ask"] = quote["ask"]
            
            # Get historical data for inefficiency detection
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            historical_data = loop.run_until_complete(
                polygon_service_enhanced.get_aggregates(
                    ticker=opp["ticker"],
                    multiplier=1,
                    timespan="day",
                    from_date=start_date,
                    to_date=end_date
                )
            )
            
            # Detect inefficiencies
            if historical_data:
                inefficiencies = inefficiency_detector.detect_all_inefficiencies(
                    ticker=opp["ticker"],
                    price_data=historical_data,
                    quote_data=quote
                )
                
                if inefficiencies:
                    # Rank and attach inefficiencies
                    ranked_inefficiencies = inefficiency_detector.rank_inefficiencies(inefficiencies)
                    opp["inefficiencies"] = ranked_inefficiencies
                    opp["primary_inefficiency"] = ranked_inefficiencies[0] if ranked_inefficiencies else None
                    opp["inefficiency_score"] = max([i.get("score", 0) for i in ranked_inefficiencies]) if ranked_inefficiencies else 0
            
            opp["asset_class"] = "equities"
            opp["scan_timestamp"] = datetime.utcnow().isoformat()
            enriched_opportunities.append(opp)
        
        logger.info(f"Found {len(enriched_opportunities)} equity opportunities")
        return enriched_opportunities
        
    finally:
        loop.close()


@shared_task
def scan_futures(config: Optional[Dict] = None) -> List[Dict]:
    """Scan CME micro futures for opportunities"""
    logger.info("Scanning CME micro futures...")
    
    config = config or {}
    min_volume = config.get("min_volume", 100)
    min_price_change = config.get("min_price_change", 0.01)
    
    # Key micro futures symbols
    futures_symbols = [
        "I:MES1!",  # Micro E-mini S&P 500
        "I:MNQ1!",  # Micro E-mini Nasdaq-100
        "I:MYM1!",  # Micro E-mini Dow
        "I:M2K1!",  # Micro E-mini Russell 2000
        "I:MGC1!",  # Micro Gold
        "I:MCL1!",  # Micro WTI Crude Oil
    ]
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        opportunities = []
        
        for symbol in futures_symbols:
            try:
                # Get recent aggregates
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5)
                
                aggs = loop.run_until_complete(
                    polygon_service.get_aggregates(
                        ticker=symbol,
                        multiplier=1,
                        timespan="day",
                        from_date=start_date,
                        to_date=end_date
                    )
                )
                
                if len(aggs) >= 2:
                    # Calculate recent price change
                    recent = aggs[-1]
                    previous = aggs[-2]
                    
                    if previous["close"] > 0:
                        pct_change = (recent["close"] - previous["close"]) / previous["close"]
                        
                        if abs(pct_change) >= min_price_change and recent["volume"] >= min_volume:
                            opportunities.append({
                                "ticker": symbol,
                                "asset_class": "futures",
                                "volume": recent["volume"],
                                "price_change": pct_change,
                                "open": recent["open"],
                                "close": recent["close"],
                                "high": recent["high"],
                                "low": recent["low"],
                                "opportunity_type": "momentum" if pct_change > 0 else "reversal",
                                "scan_timestamp": datetime.utcnow().isoformat()
                            })
                            
            except Exception as e:
                logger.warning(f"Error scanning futures symbol {symbol}: {e}")
                continue
        
        # Sort by absolute price change
        opportunities.sort(key=lambda x: abs(x["price_change"]), reverse=True)
        
        logger.info(f"Found {len(opportunities)} futures opportunities")
        return opportunities
        
    finally:
        loop.close()


@shared_task
def scan_forex(config: Optional[Dict] = None) -> List[Dict]:
    """Scan major FX pairs for trading opportunities"""
    logger.info("Scanning FX markets...")
    
    config = config or {}
    min_volume = config.get("min_volume", 10000)
    min_price_change = config.get("min_price_change", 0.005)
    
    # Major FX pairs
    fx_pairs = [
        "C:EURUSD",  # Euro/USD
        "C:GBPUSD",  # British Pound/USD
        "C:USDJPY",  # USD/Japanese Yen
        "C:USDCHF",  # USD/Swiss Franc
        "C:AUDUSD",  # Australian Dollar/USD
        "C:USDCAD",  # USD/Canadian Dollar
        "C:NZDUSD",  # New Zealand Dollar/USD
    ]
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        opportunities = []
        
        for pair in fx_pairs:
            try:
                # Get recent aggregates
                end_date = datetime.now()
                start_date = end_date - timedelta(hours=24)
                
                aggs = loop.run_until_complete(
                    polygon_service.get_aggregates(
                        ticker=pair,
                        multiplier=1,
                        timespan="hour",
                        from_date=start_date,
                        to_date=end_date
                    )
                )
                
                if len(aggs) >= 2:
                    # Calculate recent price change
                    recent = aggs[-1]
                    previous = aggs[0]  # Compare to 24 hours ago
                    
                    if previous["close"] > 0:
                        pct_change = (recent["close"] - previous["close"]) / previous["close"]
                        
                        if abs(pct_change) >= min_price_change:
                            # Get current quote for spread
                            quote = loop.run_until_complete(
                                polygon_service.get_last_quote(pair)
                            )
                            
                            opportunity = {
                                "ticker": pair,
                                "asset_class": "fx",
                                "price_change": pct_change,
                                "open": recent["open"],
                                "close": recent["close"],
                                "high": recent["high"],
                                "low": recent["low"],
                                "opportunity_type": "momentum" if pct_change > 0 else "reversal",
                                "scan_timestamp": datetime.utcnow().isoformat()
                            }
                            
                            if quote:
                                opportunity["spread"] = quote["ask"] - quote["bid"]
                                opportunity["bid"] = quote["bid"]
                                opportunity["ask"] = quote["ask"]
                            
                            opportunities.append(opportunity)
                            
            except Exception as e:
                logger.warning(f"Error scanning FX pair {pair}: {e}")
                continue
        
        # Sort by absolute price change
        opportunities.sort(key=lambda x: abs(x["price_change"]), reverse=True)
        
        logger.info(f"Found {len(opportunities)} FX opportunities")
        return opportunities
        
    finally:
        loop.close()


def store_scan_results(results: Dict) -> None:
    """Store scan results in the database"""
    db: Session = SessionLocal()
    
    try:
        # Create scan result record
        scan_result = ScanResult(
            scan_id=f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            asset_classes=list(results.keys()),
            opportunities_found=sum(len(v) for v in results.values()),
            symbols_scanned=sum(len(v) for v in results.values()),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            scan_metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "results_by_class": {k: len(v) for k, v in results.items()}
            }
        )
        
        db.add(scan_result)
        db.commit()
        
        # Store individual opportunities
        for asset_class, opportunities in results.items():
            for opp in opportunities:
                opportunity = Opportunity(
                    ticker=opp["ticker"],
                    asset_class=asset_class,
                    opportunity_type=opp.get("opportunity_type", "unknown"),
                    signal_strength=abs(opp.get("price_change", 0)) * 100,  # Convert to percentage
                    entry_price=opp.get("close", 0),
                    metadata=opp,
                    scan_result_id=scan_result.id
                )
                db.add(opportunity)
        
        db.commit()
        logger.info(f"Stored scan results with ID: {scan_result.id}")
        
    except Exception as e:
        logger.error(f"Error storing scan results: {e}")
        db.rollback()
    finally:
        db.close()