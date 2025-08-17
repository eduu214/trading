from celery import shared_task
from typing import Dict, List, Optional
import logging
import asyncio
from datetime import datetime, timedelta
from app.services.correlation_analyzer import correlation_analyzer
from app.services.polygon_service import polygon_service
from app.services.inefficiency_detector import inefficiency_detector
from app.models.opportunity import Opportunity
from app.models.strategy import Strategy
from app.core.database import SessionLocal
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.analysis_tasks.update_portfolio_correlations")
def update_portfolio_correlations():
    """
    Update correlation matrix for all portfolio strategies
    """
    logger.info("Updating portfolio correlations...")
    
    db: Session = SessionLocal()
    
    try:
        # Get active strategies
        active_strategies = db.query(Strategy).filter(
            Strategy.status == "active"
        ).all()
        
        if not active_strategies:
            return {"status": "completed", "strategies_analyzed": 0}
        
        # Collect price data for all strategy assets
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        price_data = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        for strategy in active_strategies:
            ticker = strategy.target_asset
            
            try:
                aggs = loop.run_until_complete(
                    polygon_service.get_aggregates(
                        ticker=ticker,
                        multiplier=1,
                        timespan="day",
                        from_date=start_date,
                        to_date=end_date
                    )
                )
                
                if aggs:
                    price_data[ticker] = [a["close"] for a in aggs]
                    
            except Exception as e:
                logger.warning(f"Error fetching data for {ticker}: {e}")
                continue
        
        loop.close()
        
        # Calculate correlation matrix
        if len(price_data) >= 2:
            portfolio_metrics = correlation_analyzer.calculate_portfolio_correlation(
                positions=[{"ticker": s.target_asset} for s in active_strategies],
                price_data=price_data
            )
            
            # Store correlation metrics in database
            for strategy in active_strategies:
                if strategy.metadata is None:
                    strategy.metadata = {}
                    
                strategy.metadata["correlation_metrics"] = {
                    "last_updated": datetime.utcnow().isoformat(),
                    "portfolio_correlation": portfolio_metrics.get("average_correlation", 0),
                    "diversification_score": portfolio_metrics.get("diversification_score", 0)
                }
                
            db.commit()
            
            logger.info(f"Updated correlations for {len(active_strategies)} strategies")
            
            return {
                "status": "completed",
                "strategies_analyzed": len(active_strategies),
                "average_correlation": portfolio_metrics.get("average_correlation", 0),
                "diversification_score": portfolio_metrics.get("diversification_score", 0)
            }
            
        return {"status": "completed", "strategies_analyzed": 0}
        
    except Exception as e:
        logger.error(f"Error updating portfolio correlations: {e}")
        db.rollback()
        return {"status": "error", "error": str(e)}
        
    finally:
        db.close()


@shared_task
def analyze_opportunity(opportunity_id: int):
    """
    Perform deep analysis on a discovered opportunity
    """
    logger.info(f"Analyzing opportunity: {opportunity_id}")
    
    db: Session = SessionLocal()
    
    try:
        # Get the opportunity
        opportunity = db.query(Opportunity).filter(
            Opportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            return {"opportunity_id": opportunity_id, "error": "Opportunity not found"}
        
        # Get historical data for deep analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        historical_data = loop.run_until_complete(
            polygon_service.get_aggregates(
                ticker=opportunity.ticker,
                multiplier=1,
                timespan="day",
                from_date=start_date,
                to_date=end_date
            )
        )
        
        # Get current quote
        quote = loop.run_until_complete(
            polygon_service.get_last_quote(opportunity.ticker)
        )
        
        loop.close()
        
        # Perform comprehensive inefficiency analysis
        if historical_data:
            inefficiencies = inefficiency_detector.detect_all_inefficiencies(
                ticker=opportunity.ticker,
                price_data=historical_data,
                quote_data=quote
            )
            
            # Rank inefficiencies
            ranked_inefficiencies = inefficiency_detector.rank_inefficiencies(inefficiencies)
            
            # Update opportunity with analysis results
            if opportunity.metadata is None:
                opportunity.metadata = {}
                
            opportunity.metadata["detailed_analysis"] = {
                "analyzed_at": datetime.utcnow().isoformat(),
                "inefficiencies": ranked_inefficiencies,
                "inefficiency_count": len(inefficiencies),
                "max_inefficiency_score": max([i.get("score", 0) for i in ranked_inefficiencies]) if ranked_inefficiencies else 0,
                "quote": quote
            }
            
            # Update signal strength based on detailed analysis
            if ranked_inefficiencies:
                opportunity.signal_strength = max([i.get("score", 0) for i in ranked_inefficiencies])
                
            db.commit()
            
            logger.info(f"Analysis complete for opportunity {opportunity_id}: {len(inefficiencies)} inefficiencies found")
            
            return {
                "opportunity_id": opportunity_id,
                "analysis_complete": True,
                "inefficiencies_found": len(inefficiencies),
                "max_score": opportunity.signal_strength
            }
            
        return {
            "opportunity_id": opportunity_id,
            "analysis_complete": False,
            "error": "Insufficient historical data"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing opportunity {opportunity_id}: {e}")
        db.rollback()
        return {"opportunity_id": opportunity_id, "error": str(e)}
        
    finally:
        db.close()


@shared_task
def find_uncorrelated_opportunities(scan_result_id: Optional[int] = None):
    """
    Find uncorrelated opportunities across asset classes
    """
    logger.info("Finding uncorrelated opportunities...")
    
    db: Session = SessionLocal()
    
    try:
        # Get recent opportunities
        query = db.query(Opportunity)
        
        if scan_result_id:
            query = query.filter(Opportunity.scan_result_id == scan_result_id)
        else:
            # Get opportunities from last 24 hours
            cutoff = datetime.utcnow() - timedelta(hours=24)
            query = query.filter(Opportunity.discovered_at >= cutoff)
        
        opportunities = query.all()
        
        if len(opportunities) < 2:
            return {"uncorrelated_pairs": [], "message": "Not enough opportunities to analyze"}
        
        # Group opportunities by asset class
        opportunities_by_class = {}
        for opp in opportunities:
            if opp.asset_class not in opportunities_by_class:
                opportunities_by_class[opp.asset_class] = []
            opportunities_by_class[opp.asset_class].append({
                "ticker": opp.ticker,
                "signal_strength": opp.signal_strength,
                "opportunity_type": opp.opportunity_type,
                "metadata": opp.metadata
            })
        
        # Analyze cross-asset correlations
        cross_asset_opps = correlation_analyzer.analyze_cross_asset_opportunities(
            opportunities_by_class
        )
        
        # Store results
        for cross_opp in cross_asset_opps[:10]:  # Top 10
            # Update opportunities with cross-asset information
            for opp in opportunities:
                if opp.ticker in [cross_opp["asset1"]["ticker"], cross_opp["asset2"]["ticker"]]:
                    if opp.metadata is None:
                        opp.metadata = {}
                    
                    opp.metadata["cross_asset_pairs"] = opp.metadata.get("cross_asset_pairs", [])
                    opp.metadata["cross_asset_pairs"].append({
                        "pair_ticker": cross_opp["asset2"]["ticker"] if opp.ticker == cross_opp["asset1"]["ticker"] else cross_opp["asset1"]["ticker"],
                        "correlation": cross_opp["correlation"],
                        "combined_score": cross_opp["combined_score"]
                    })
        
        db.commit()
        
        logger.info(f"Found {len(cross_asset_opps)} uncorrelated opportunity pairs")
        
        return {
            "uncorrelated_pairs": cross_asset_opps[:10],
            "total_pairs_found": len(cross_asset_opps),
            "opportunities_analyzed": len(opportunities)
        }
        
    except Exception as e:
        logger.error(f"Error finding uncorrelated opportunities: {e}")
        db.rollback()
        return {"error": str(e)}
        
    finally:
        db.close()