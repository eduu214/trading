'use client'

import React, { useState } from 'react'
import { EfficientFrontier, StrategyAllocation, PortfolioMetrics, CorrelationAnalysis } from '@/components/portfolio'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import { 
  TrendingUp, 
  PieChart, 
  Calculator,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react'

interface OptimalPortfolio {
  weights: { [key: string]: number }
  expected_return: number
  volatility: number
  sharpe_ratio: number
}

export default function PortfolioPage() {
  const [selectedPortfolio, setSelectedPortfolio] = useState<OptimalPortfolio | null>(null)
  const [optimizing, setOptimizing] = useState(false)
  const [optimizationResult, setOptimizationResult] = useState<any>(null)
  const [currentAllocations, setCurrentAllocations] = useState<{ [key: string]: number }>({
    rsi_mean_reversion: 0.20,
    macd_momentum: 0.20,
    bollinger_breakout: 0.20,
    mean_reversion_pairs: 0.20,
    momentum_breakout: 0.20
  })

  const handlePortfolioSelect = (portfolio: OptimalPortfolio) => {
    setSelectedPortfolio(portfolio)
  }

  const handleOptimizePortfolio = async () => {
    if (!selectedPortfolio) return

    setOptimizing(true)
    try {
      const response = await fetch('http://localhost:8000/api/v1/portfolio/optimize?optimization_method=max_sharpe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Optimization failed')
      }

      const data = await response.json()
      setOptimizationResult(data)
    } catch (error) {
      console.error('Optimization error:', error)
    } finally {
      setOptimizing(false)
    }
  }

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Portfolio Management</h1>
        <p className="text-gray-600">
          Construct optimal portfolios using Modern Portfolio Theory and real-time optimization
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Value</p>
              <p className="text-2xl font-bold">$10,000</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Strategies</p>
              <p className="text-2xl font-bold">5</p>
            </div>
            <PieChart className="h-8 w-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Portfolio Status</p>
              <Badge variant="success" className="mt-1">Optimized</Badge>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Risk Level</p>
              <Badge className="mt-1">Moderate</Badge>
            </div>
            <AlertCircle className="h-8 w-8 text-yellow-500" />
          </div>
        </Card>
      </div>

      {/* Efficient Frontier Visualization */}
      <EfficientFrontier 
        portfolioId="main"
        onPortfolioSelect={handlePortfolioSelect}
        className="mb-8"
      />

      {/* Strategy Allocation Interface */}
      <StrategyAllocation
        portfolioId="main"
        initialAllocations={currentAllocations}
        onAllocationChange={(allocations) => setCurrentAllocations(allocations)}
        className="mb-8"
      />

      {/* Portfolio Metrics Dashboard */}
      <PortfolioMetrics
        portfolioId="main"
        allocations={currentAllocations}
        refreshInterval={5000}
        className="mb-8"
      />

      {/* Correlation Analysis */}
      <CorrelationAnalysis
        portfolioId="main"
        timePeriod="30d"
        className="mb-8"
      />

      {/* Selected Portfolio Actions */}
      {selectedPortfolio && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Selected Portfolio Configuration</h2>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setSelectedPortfolio(null)}
              >
                Clear Selection
              </Button>
              <Button
                onClick={handleOptimizePortfolio}
                disabled={optimizing}
              >
                {optimizing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Optimizing...
                  </>
                ) : (
                  <>
                    <Calculator className="h-4 w-4 mr-2" />
                    Apply Portfolio
                  </>
                )}
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="font-semibold mb-2">Expected Performance</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Annual Return</span>
                  <span className="font-semibold text-green-600">
                    {formatPercent(selectedPortfolio.expected_return)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Volatility</span>
                  <span className="font-semibold">
                    {formatPercent(selectedPortfolio.volatility)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Sharpe Ratio</span>
                  <span className="font-semibold text-blue-600">
                    {selectedPortfolio.sharpe_ratio.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Risk Metrics</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Drawdown</span>
                  <span className="font-semibold text-red-600">-8.5%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">VaR (95%)</span>
                  <span className="font-semibold">15.6%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Sortino Ratio</span>
                  <span className="font-semibold">2.38</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Allocation Summary</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Strategies</span>
                  <span className="font-semibold">
                    {Object.keys(selectedPortfolio.weights).filter(k => selectedPortfolio.weights[k] > 0.01).length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Allocation</span>
                  <span className="font-semibold">
                    {formatPercent(Math.max(...Object.values(selectedPortfolio.weights)))}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Concentration</span>
                  <Badge variant="success">Diversified</Badge>
                </div>
              </div>
            </div>
          </div>

          {optimizationResult && (
            <Alert className="mt-4">
              <CheckCircle className="h-4 w-4" />
              <div>
                <p className="font-semibold">Portfolio Applied Successfully</p>
                <p className="text-sm">Your portfolio has been optimized and is now active.</p>
              </div>
            </Alert>
          )}
        </Card>
      )}
    </div>
  )
}