"""Add complexity fields to strategies table

Revision ID: 002
Revises: 001
Create Date: 2025-08-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    """Add complexity-related columns to strategies table"""
    
    # Add complexity fields
    op.add_column('strategies', 
        sa.Column('complexity_level', sa.Integer(), nullable=True, default=5)
    )
    op.add_column('strategies',
        sa.Column('complexity_score', sa.Float(), nullable=True)
    )
    op.add_column('strategies',
        sa.Column('optimal_complexity', sa.Integer(), nullable=True)
    )
    op.add_column('strategies',
        sa.Column('last_optimized', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column('strategies',
        sa.Column('optimization_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )
    
    # Create index for faster complexity queries
    op.create_index(
        'ix_strategies_complexity_level',
        'strategies',
        ['complexity_level'],
        unique=False
    )
    
    # Create complexity_history table for tracking optimization history
    op.create_table('complexity_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('complexity_level', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('sharpe_ratio', sa.Float()),
        sa.Column('max_drawdown', sa.Float()),
        sa.Column('risk_adjusted_return', sa.Float()),
        sa.Column('confidence', sa.Float()),
        sa.Column('recommendation', sa.Text()),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('risk_preference', sa.String(50))
    )
    
    # Create index on strategy_id for faster lookups
    op.create_index(
        'ix_complexity_history_strategy_id',
        'complexity_history',
        ['strategy_id'],
        unique=False
    )

def downgrade():
    """Remove complexity-related changes"""
    
    # Drop complexity_history table
    op.drop_index('ix_complexity_history_strategy_id', table_name='complexity_history')
    op.drop_table('complexity_history')
    
    # Drop index
    op.drop_index('ix_strategies_complexity_level', table_name='strategies')
    
    # Remove columns from strategies table
    op.drop_column('strategies', 'optimization_metrics')
    op.drop_column('strategies', 'last_optimized')
    op.drop_column('strategies', 'optimal_complexity')
    op.drop_column('strategies', 'complexity_score')
    op.drop_column('strategies', 'complexity_level')