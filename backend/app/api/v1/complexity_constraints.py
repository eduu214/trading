"""
API endpoints for complexity constraints and multi-timeframe analysis
F001-US002 Slice 2: Alternative Flows
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.services.multi_timeframe_optimizer import (
    MultiTimeframeOptimizer,
    ConstraintEvaluator,
    SYSTEM_PRESETS
)
from app.models.strategy import Strategy
from app.models.complexity_constraint import (
    ComplexityConstraint,
    ComplexityPreset,
    MultiTimeframeAnalysis,
    ConstraintType,
    TimeframeType
)
from app.core.dependencies import get_current_user
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/constraints",
    tags=["complexity-constraints"]
)

# Request/Response models
class ConstraintRequest(BaseModel):
    strategy_id: str
    constraint_type: str
    operator: str
    value: float
    timeframe: str = "1D"
    is_hard_constraint: bool = False
    weight: float = 1.0
    
    class Config:
        schema_extra = {
            "example": {
                "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
                "constraint_type": "MIN_SHARPE",
                "operator": ">=",
                "value": 1.5,
                "timeframe": "1D",
                "is_hard_constraint": True,
                "weight": 1.0
            }
        }

class MultiTimeframeRequest(BaseModel):
    strategy_id: str
    timeframes: List[str] = Field(default=["1D"])
    lookback_days: int = Field(252, ge=30, le=730)
    constraint_ids: Optional[List[str]] = None
    preset_id: Optional[str] = None
    weights: Optional[Dict[str, float]] = None

class ConstraintResponse(BaseModel):
    id: str
    strategy_id: str
    constraint_type: str
    operator: str
    value: float
    timeframe: str
    is_active: bool
    is_hard_constraint: bool
    weight: float
    created_at: str

class PresetResponse(BaseModel):
    id: str
    name: str
    description: str
    risk_preference: str
    constraints: List[Dict]
    default_timeframe: Optional[str]
    is_system: bool
    times_used: int = 0

class MultiTimeframeResponse(BaseModel):
    id: str
    strategy_id: str
    primary_timeframe: str
    secondary_timeframes: List[str]
    weighted_complexity: float
    optimal_complexity: int
    confidence_score: float
    consistency_score: float
    results: Dict[str, Any]

# Service instances
multi_optimizer = MultiTimeframeOptimizer()
constraint_evaluator = ConstraintEvaluator()

@router.post("/", response_model=ConstraintResponse)
async def create_constraint(
    request: ConstraintRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new complexity constraint for a strategy
    """
    try:
        # Validate strategy exists
        strategy = await db.get(Strategy, request.strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Validate constraint type
        try:
            constraint_type = ConstraintType(request.constraint_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid constraint type: {request.constraint_type}"
            )
        
        # Validate timeframe
        try:
            timeframe = TimeframeType(request.timeframe)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe: {request.timeframe}"
            )
        
        # Create constraint
        constraint = ComplexityConstraint(
            strategy_id=request.strategy_id,
            constraint_type=constraint_type,
            operator=request.operator,
            value=request.value,
            timeframe=timeframe,
            is_hard_constraint=request.is_hard_constraint,
            weight=request.weight,
            is_active=True
        )
        
        db.add(constraint)
        await db.commit()
        await db.refresh(constraint)
        
        return ConstraintResponse(
            id=str(constraint.id),
            strategy_id=str(constraint.strategy_id),
            constraint_type=constraint.constraint_type.value,
            operator=constraint.operator,
            value=constraint.value,
            timeframe=constraint.timeframe.value,
            is_active=constraint.is_active,
            is_hard_constraint=constraint.is_hard_constraint,
            weight=constraint.weight,
            created_at=constraint.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create constraint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{strategy_id}", response_model=List[ConstraintResponse])
async def get_strategy_constraints(
    strategy_id: str,
    active_only: bool = Query(True, description="Return only active constraints"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all constraints for a strategy
    """
    try:
        query = select(ComplexityConstraint).where(
            ComplexityConstraint.strategy_id == strategy_id
        )
        
        if active_only:
            query = query.where(ComplexityConstraint.is_active == True)
        
        result = await db.execute(query)
        constraints = result.scalars().all()
        
        return [
            ConstraintResponse(
                id=str(c.id),
                strategy_id=str(c.strategy_id),
                constraint_type=c.constraint_type.value,
                operator=c.operator,
                value=c.value,
                timeframe=c.timeframe.value,
                is_active=c.is_active,
                is_hard_constraint=c.is_hard_constraint,
                weight=c.weight,
                created_at=c.created_at.isoformat()
            )
            for c in constraints
        ]
        
    except Exception as e:
        logger.error(f"Failed to get constraints: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{constraint_id}")
async def delete_constraint(
    constraint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete a complexity constraint
    """
    try:
        constraint = await db.get(ComplexityConstraint, constraint_id)
        if not constraint:
            raise HTTPException(status_code=404, detail="Constraint not found")
        
        await db.delete(constraint)
        await db.commit()
        
        return {"message": "Constraint deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete constraint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets/list", response_model=List[PresetResponse])
async def list_presets(
    system_only: bool = Query(False, description="Return only system presets"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    List available complexity constraint presets
    """
    try:
        query = select(ComplexityPreset)
        
        if system_only:
            query = query.where(ComplexityPreset.is_system == True)
        
        result = await db.execute(query)
        presets = result.scalars().all()
        
        # If no presets exist, create system presets
        if not presets and system_only:
            presets = await _create_system_presets(db)
        
        return [
            PresetResponse(
                id=str(p.id),
                name=p.name,
                description=p.description,
                risk_preference=p.risk_preference,
                constraints=p.constraints,
                default_timeframe=p.default_timeframe.value if p.default_timeframe else None,
                is_system=p.is_system,
                times_used=p.times_used
            )
            for p in presets
        ]
        
    except Exception as e:
        logger.error(f"Failed to list presets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/presets/{preset_id}/apply")
async def apply_preset(
    preset_id: str,
    strategy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Apply a preset to a strategy
    """
    try:
        # Get preset
        preset = await db.get(ComplexityPreset, preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail="Preset not found")
        
        # Validate strategy
        strategy = await db.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Delete existing constraints for this strategy
        existing = await db.execute(
            select(ComplexityConstraint).where(
                ComplexityConstraint.strategy_id == strategy_id
            )
        )
        for constraint in existing.scalars():
            await db.delete(constraint)
        
        # Create new constraints from preset
        created_constraints = []
        for constraint_def in preset.constraints:
            constraint = ComplexityConstraint(
                strategy_id=strategy_id,
                constraint_type=ConstraintType(constraint_def["type"]),
                operator=constraint_def["operator"],
                value=constraint_def["value"],
                timeframe=TimeframeType(
                    constraint_def.get("timeframe", preset.default_timeframe or "1D")
                ),
                is_hard_constraint=constraint_def.get("is_hard", False),
                weight=constraint_def.get("weight", 1.0),
                is_active=True
            )
            db.add(constraint)
            created_constraints.append(constraint)
        
        # Update preset usage
        preset.times_used += 1
        preset.last_used = datetime.utcnow()
        
        await db.commit()
        
        return {
            "message": f"Applied preset {preset.name} to strategy",
            "constraints_created": len(created_constraints),
            "preset_name": preset.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply preset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/multi-timeframe")
async def optimize_multi_timeframe(
    request: MultiTimeframeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Perform multi-timeframe complexity optimization
    """
    try:
        # Validate strategy
        strategy = await db.get(Strategy, request.strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Validate timeframes
        timeframes = []
        for tf in request.timeframes:
            try:
                timeframes.append(TimeframeType(tf))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid timeframe: {tf}"
                )
        
        # Get constraints if specified
        constraints = []
        if request.constraint_ids:
            for constraint_id in request.constraint_ids:
                constraint = await db.get(ComplexityConstraint, constraint_id)
                if constraint and constraint.is_active:
                    constraints.append(constraint)
        
        # Apply preset constraints if specified
        if request.preset_id:
            preset = await db.get(ComplexityPreset, request.preset_id)
            if preset:
                for constraint_def in preset.constraints:
                    constraint = ComplexityConstraint(
                        strategy_id=request.strategy_id,
                        constraint_type=ConstraintType(constraint_def["type"]),
                        operator=constraint_def["operator"],
                        value=constraint_def["value"],
                        timeframe=TimeframeType(
                            constraint_def.get("timeframe", "1D")
                        ),
                        is_hard_constraint=constraint_def.get("is_hard", False),
                        weight=constraint_def.get("weight", 1.0),
                        is_active=True
                    )
                    constraints.append(constraint)
        
        # Start optimization task
        task = celery_app.send_task(
            'optimize_multi_timeframe',
            args=[
                request.strategy_id,
                [tf.value for tf in timeframes],
                request.lookback_days,
                [c.to_dict() for c in constraints],
                request.weights
            ]
        )
        
        return {
            "task_id": task.id,
            "message": f"Multi-timeframe optimization started for {len(timeframes)} timeframes",
            "estimated_time_seconds": len(timeframes) * 30
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start multi-timeframe optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/multi-timeframe/{analysis_id}", response_model=MultiTimeframeResponse)
async def get_multi_timeframe_results(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get results of multi-timeframe analysis
    """
    try:
        analysis = await db.get(MultiTimeframeAnalysis, analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return MultiTimeframeResponse(
            id=str(analysis.id),
            strategy_id=str(analysis.strategy_id),
            primary_timeframe=analysis.primary_timeframe.value,
            secondary_timeframes=analysis.secondary_timeframes,
            weighted_complexity=analysis.weighted_complexity,
            optimal_complexity=analysis.optimal_complexity,
            confidence_score=analysis.confidence_score,
            consistency_score=analysis.consistency_score,
            results=analysis.results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate")
async def evaluate_constraints(
    strategy_id: str,
    complexity_level: int,
    metrics: Optional[Dict[str, float]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Evaluate constraints for a given complexity level and metrics
    """
    try:
        # Get strategy constraints
        result = await db.execute(
            select(ComplexityConstraint).where(
                and_(
                    ComplexityConstraint.strategy_id == strategy_id,
                    ComplexityConstraint.is_active == True
                )
            )
        )
        constraints = result.scalars().all()
        
        if not constraints:
            return {
                "all_satisfied": True,
                "violations": [],
                "score": 100.0,
                "message": "No active constraints to evaluate"
            }
        
        # Use provided metrics or fetch from strategy
        if not metrics:
            strategy = await db.get(Strategy, strategy_id)
            if not strategy or not strategy.optimization_metrics:
                raise HTTPException(
                    status_code=400,
                    detail="No metrics available for evaluation"
                )
            metrics = strategy.optimization_metrics.get("score", {}).get("metrics", {})
        
        # Evaluate constraints
        all_satisfied, violations = constraint_evaluator.evaluate_constraints(
            constraints,
            metrics
        )
        
        # Calculate score
        score = constraint_evaluator.calculate_constraint_score(
            constraints,
            metrics
        )
        
        return {
            "all_satisfied": all_satisfied,
            "violations": violations,
            "score": score,
            "total_constraints": len(constraints),
            "hard_constraints": sum(1 for c in constraints if c.is_hard_constraint),
            "soft_constraints": sum(1 for c in constraints if not c.is_hard_constraint)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to evaluate constraints: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _create_system_presets(db: AsyncSession) -> List[ComplexityPreset]:
    """Create system presets if they don't exist"""
    presets = []
    
    for preset_def in SYSTEM_PRESETS:
        preset = ComplexityPreset(
            name=preset_def["name"],
            description=preset_def["description"],
            risk_preference=preset_def["risk_preference"],
            constraints=preset_def["constraints"],
            default_timeframe=TimeframeType(preset_def.get("default_timeframe", "1D")),
            is_system=True,
            is_default=preset_def["name"] == "Balanced"
        )
        db.add(preset)
        presets.append(preset)
    
    await db.commit()
    return presets