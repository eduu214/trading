'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  PieChart,
  BarChart3,
  Lock,
  Unlock,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Calculator,
  Save,
  RefreshCw
} from 'lucide-react'

interface StrategyWeight {
  strategy_id: string
  weight: number
  locked: boolean
}

interface AllocationConstraints {
  max_weight_per_strategy: number
  min_weight_threshold: number
  total_allocation: number
}

interface PortfolioMetrics {
  expected_annual_return: number
  annual_volatility: number
  sharpe_ratio: number
  max_drawdown: number
  var_95: number
  sortino_ratio: number
}

interface ValidationResult {
  is_valid: boolean
  violations: Array<{
    type: string
    strategy?: string
    current_weight?: number
    max_allowed?: number
  }>
  warnings: Array<{
    type: string
    strategy?: string
    current_weight?: number
    min_threshold?: number
  }>
}

interface StrategyAllocationProps {
  portfolioId?: string
  initialAllocations?: { [key: string]: number }
  onAllocationChange?: (allocations: { [key: string]: number }) => void
  className?: string
}

const STRATEGIES = [
  { id: 'rsi_mean_reversion', name: 'RSI Mean Reversion', color: '#3b82f6' },
  { id: 'macd_momentum', name: 'MACD Momentum', color: '#10b981' },
  { id: 'bollinger_breakout', name: 'Bollinger Breakout', color: '#f59e0b' },
  { id: 'mean_reversion_pairs', name: 'Mean Reversion Pairs', color: '#8b5cf6' },
  { id: 'momentum_breakout', name: 'Momentum Breakout', color: '#ef4444' }
]

export const StrategyAllocation: React.FC<StrategyAllocationProps> = ({
  portfolioId = 'main',
  initialAllocations = {},
  onAllocationChange,
  className = ''
}) => {
  const [allocations, setAllocations] = useState<StrategyWeight[]>([])
  const [metrics, setMetrics] = useState<PortfolioMetrics | null>(null)
  const [validation, setValidation] = useState<ValidationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [autoBalance, setAutoBalance] = useState(true)

  const constraints: AllocationConstraints = {
    max_weight_per_strategy: 0.30,
    min_weight_threshold: 0.01,
    total_allocation: 1.0
  }

  // Initialize allocations
  useEffect(() => {
    const initial = STRATEGIES.map(strategy => ({
      strategy_id: strategy.id,
      weight: initialAllocations[strategy.id] || 0.20, // Default to equal weight
      locked: false
    }))
    setAllocations(initial)
  }, [initialAllocations])

  // Fetch portfolio metrics when allocations change
  const fetchMetrics = useCallback(async (weights: { [key: string]: number }) => {
    try {
      const params = new URLSearchParams({
        allocation: JSON.stringify(weights),
        portfolio_id: portfolioId
      })
      
      const response = await fetch(
        `http://localhost:8000/api/v1/portfolio/metrics?${params}`
      )
      
      if (response.ok) {
        const data = await response.json()
        setMetrics(data.metrics)
      }
    } catch (error) {
      console.error('Error fetching metrics:', error)
    }
  }, [portfolioId])

  // Validate allocation
  const validateAllocation = useCallback(async (weights: { [key: string]: number }) => {
    try {
      const response = await fetch(
        'http://localhost:8000/api/v1/portfolio/validate-allocation',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(weights)
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setValidation(data.validation_result)
      }
    } catch (error) {
      console.error('Error validating allocation:', error)
    }
  }, [])

  // Handle allocation change
  const handleAllocationChange = (strategyId: string, newWeight: number) => {
    const updatedAllocations = [...allocations]
    const strategyIndex = updatedAllocations.findIndex(a => a.strategy_id === strategyId)
    
    if (strategyIndex === -1) return
    
    const oldWeight = updatedAllocations[strategyIndex].weight
    const weightDiff = newWeight - oldWeight
    
    updatedAllocations[strategyIndex].weight = newWeight
    
    // Auto-balance if enabled
    if (autoBalance && Math.abs(weightDiff) > 0.001) {
      const unlockedStrategies = updatedAllocations.filter(
        (a, i) => i !== strategyIndex && !a.locked
      )
      
      if (unlockedStrategies.length > 0) {
        const adjustmentPerStrategy = -weightDiff / unlockedStrategies.length
        
        updatedAllocations.forEach((allocation, i) => {
          if (i !== strategyIndex && !allocation.locked) {
            allocation.weight = Math.max(0, Math.min(1, allocation.weight + adjustmentPerStrategy))
          }
        })
      }
    }
    
    // Normalize to ensure total is 1.0
    const total = updatedAllocations.reduce((sum, a) => sum + a.weight, 0)
    if (Math.abs(total - 1.0) > 0.001) {
      const scale = 1.0 / total
      updatedAllocations.forEach(a => {
        a.weight = a.weight * scale
      })
    }
    
    setAllocations(updatedAllocations)
    
    // Create weights object
    const weights = updatedAllocations.reduce((acc, a) => {
      acc[a.strategy_id] = a.weight
      return acc
    }, {} as { [key: string]: number })
    
    // Fetch metrics and validate
    fetchMetrics(weights)
    validateAllocation(weights)
    
    // Notify parent
    if (onAllocationChange) {
      onAllocationChange(weights)
    }
  }

  // Toggle lock on strategy
  const toggleLock = (strategyId: string) => {
    setAllocations(prev => prev.map(a => 
      a.strategy_id === strategyId ? { ...a, locked: !a.locked } : a
    ))
  }

  // Reset to equal weights
  const resetToEqualWeights = () => {
    const equalWeight = 1.0 / STRATEGIES.length
    const newAllocations = allocations.map(a => ({
      ...a,
      weight: equalWeight,
      locked: false
    }))
    setAllocations(newAllocations)
    
    const weights = newAllocations.reduce((acc, a) => {
      acc[a.strategy_id] = a.weight
      return acc
    }, {} as { [key: string]: number })
    
    fetchMetrics(weights)
    validateAllocation(weights)
    
    if (onAllocationChange) {
      onAllocationChange(weights)
    }
  }

  // Apply optimal allocation (max Sharpe)
  const applyOptimalAllocation = async () => {
    setLoading(true)
    try {
      const response = await fetch(
        'http://localhost:8000/api/v1/portfolio/optimize?optimization_method=max_sharpe',
        { method: 'POST' }
      )
      
      if (response.ok) {
        const data = await response.json()
        if (data.optimization_result?.optimal_weights) {
          const optimalWeights = data.optimization_result.optimal_weights
          const newAllocations = allocations.map(a => ({
            ...a,
            weight: optimalWeights[a.strategy_id] || 0,
            locked: false
          }))
          setAllocations(newAllocations)
          
          fetchMetrics(optimalWeights)
          validateAllocation(optimalWeights)
          
          if (onAllocationChange) {
            onAllocationChange(optimalWeights)
          }
        }
      }
    } catch (error) {
      console.error('Error applying optimal allocation:', error)
    } finally {
      setLoading(false)
    }
  }

  // Save allocation
  const saveAllocation = async () => {
    setSaving(true)
    // In a real app, this would save to the backend
    await new Promise(resolve => setTimeout(resolve, 1000))
    setSaving(false)
  }

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`
  const formatMetric = (value: number, decimals: number = 2) => value.toFixed(decimals)

  // Calculate total allocation
  const totalAllocation = allocations.reduce((sum, a) => sum + a.weight, 0)
  const isValidTotal = Math.abs(totalAllocation - 1.0) < 0.001

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Strategy Allocation
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Adjust portfolio weights to optimize risk-return profile
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={resetToEqualWeights}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Equal Weights
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={applyOptimalAllocation}
              disabled={loading}
            >
              <Calculator className="h-4 w-4 mr-1" />
              Optimize
            </Button>
            <Button
              onClick={saveAllocation}
              disabled={saving || !isValidTotal || !validation?.is_valid}
            >
              <Save className="h-4 w-4 mr-1" />
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>

        {/* Auto-balance toggle */}
        <div className="flex items-center gap-2 mb-4">
          <input
            type="checkbox"
            id="autoBalance"
            checked={autoBalance}
            onChange={(e) => setAutoBalance(e.target.checked)}
            className="rounded"
          />
          <Label htmlFor="autoBalance" className="text-sm">
            Auto-balance allocations when adjusting weights
          </Label>
        </div>

        {/* Allocation Sliders */}
        <div className="space-y-4">
          {allocations.map((allocation) => {
            const strategy = STRATEGIES.find(s => s.id === allocation.strategy_id)
            if (!strategy) return null
            
            return (
              <div key={allocation.strategy_id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: strategy.color }}
                    />
                    <span className="font-medium text-sm">{strategy.name}</span>
                    <button
                      onClick={() => toggleLock(allocation.strategy_id)}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      {allocation.locked ? (
                        <Lock className="h-3 w-3 text-gray-500" />
                      ) : (
                        <Unlock className="h-3 w-3 text-gray-400" />
                      )}
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <Input
                      type="number"
                      value={(allocation.weight * 100).toFixed(1)}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value) / 100
                        if (!isNaN(value) && value >= 0 && value <= 1) {
                          handleAllocationChange(allocation.strategy_id, value)
                        }
                      }}
                      className="w-20 text-right"
                      disabled={allocation.locked}
                      step="0.1"
                      min="0"
                      max="100"
                    />
                    <span className="text-sm text-gray-600">%</span>
                  </div>
                </div>
                <Slider
                  value={[allocation.weight * 100]}
                  onValueChange={([value]) => 
                    handleAllocationChange(allocation.strategy_id, value / 100)
                  }
                  max={constraints.max_weight_per_strategy * 100}
                  step={0.1}
                  disabled={allocation.locked}
                  className="flex-1"
                />
                {allocation.weight > constraints.max_weight_per_strategy && (
                  <p className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    Exceeds maximum allocation ({formatPercent(constraints.max_weight_per_strategy)})
                  </p>
                )}
              </div>
            )
          })}
        </div>

        {/* Total Allocation */}
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between">
            <span className="font-semibold">Total Allocation</span>
            <span className={`font-bold ${isValidTotal ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercent(totalAllocation)}
            </span>
          </div>
          {!isValidTotal && (
            <p className="text-xs text-red-500 mt-1">Total must equal 100%</p>
          )}
        </div>

        {/* Validation Messages */}
        {validation && !validation.is_valid && (
          <Alert className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <div>
              <p className="font-semibold">Validation Issues</p>
              {validation.violations.map((v, i) => (
                <p key={i} className="text-sm">
                  {v.strategy}: {formatPercent(v.current_weight || 0)} exceeds max {formatPercent(v.max_allowed || 0)}
                </p>
              ))}
            </div>
          </Alert>
        )}
      </Card>

      {/* Portfolio Metrics */}
      {metrics && (
        <Card className="p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Portfolio Metrics
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <p className="text-xs text-gray-500">Expected Return</p>
              <p className="font-semibold text-green-600">
                {formatPercent(metrics.expected_annual_return)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Volatility</p>
              <p className="font-semibold">
                {formatPercent(metrics.annual_volatility)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Sharpe Ratio</p>
              <p className="font-semibold text-blue-600">
                {formatMetric(metrics.sharpe_ratio)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Max Drawdown</p>
              <p className="font-semibold text-red-600">
                {formatPercent(metrics.max_drawdown)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">VaR (95%)</p>
              <p className="font-semibold">
                {formatPercent(metrics.var_95)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Sortino Ratio</p>
              <p className="font-semibold">
                {formatMetric(metrics.sortino_ratio)}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Pie Chart Visualization */}
      <Card className="p-4">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          Allocation Breakdown
        </h3>
        <div className="space-y-2">
          {allocations
            .filter(a => a.weight > 0.001)
            .sort((a, b) => b.weight - a.weight)
            .map(allocation => {
              const strategy = STRATEGIES.find(s => s.id === allocation.strategy_id)
              if (!strategy) return null
              
              return (
                <div key={allocation.strategy_id} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: strategy.color }}
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{strategy.name}</span>
                      <span className="text-sm font-semibold">
                        {formatPercent(allocation.weight)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className="h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${allocation.weight * 100}%`,
                          backgroundColor: strategy.color
                        }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
        </div>
      </Card>
    </div>
  )
}

export default StrategyAllocation