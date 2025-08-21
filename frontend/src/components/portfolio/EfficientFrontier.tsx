'use client'

import React, { useEffect, useState, useCallback } from 'react'
import {
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  ReferenceDot,
  ReferenceLine
} from 'recharts'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import { Loader2, TrendingUp, Target, AlertCircle, RefreshCw } from 'lucide-react'

interface FrontierPoint {
  expected_return: number
  volatility: number
  sharpe_ratio: number
  weights: { [key: string]: number }
}

interface OptimalPortfolio {
  weights: { [key: string]: number }
  expected_return: number
  volatility: number
  sharpe_ratio: number
}

interface EfficientFrontierData {
  frontier_points: FrontierPoint[]
  optimal_portfolios: {
    max_sharpe?: OptimalPortfolio
    min_volatility?: OptimalPortfolio
  }
  n_strategies: number
  risk_free_rate: number
  constraints: {
    max_weight_per_strategy: number
    min_weight_threshold: number
  }
}

interface EfficientFrontierProps {
  portfolioId?: string
  onPortfolioSelect?: (portfolio: OptimalPortfolio) => void
  className?: string
}

export const EfficientFrontier: React.FC<EfficientFrontierProps> = ({
  portfolioId = 'main',
  onPortfolioSelect,
  className = ''
}) => {
  const [frontierData, setFrontierData] = useState<EfficientFrontierData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPoint, setSelectedPoint] = useState<FrontierPoint | OptimalPortfolio | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const fetchEfficientFrontier = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/portfolio/efficient-frontier?portfolio_id=${portfolioId}&n_points=20`
      )
      
      if (!response.ok) {
        throw new Error(`Failed to fetch efficient frontier: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      if (data.status === 'success' && data.efficient_frontier) {
        setFrontierData(data.efficient_frontier)
        
        // Auto-select max Sharpe portfolio if available
        if (data.efficient_frontier.optimal_portfolios?.max_sharpe) {
          setSelectedPoint(data.efficient_frontier.optimal_portfolios.max_sharpe)
        }
      } else {
        throw new Error(data.error || 'Failed to calculate efficient frontier')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      console.error('Efficient frontier error:', err)
    } finally {
      setLoading(false)
    }
  }, [portfolioId])

  useEffect(() => {
    fetchEfficientFrontier()
  }, [fetchEfficientFrontier, refreshKey])

  const handlePointClick = (point: FrontierPoint | OptimalPortfolio) => {
    setSelectedPoint(point)
    if (onPortfolioSelect && 'weights' in point) {
      onPortfolioSelect(point as OptimalPortfolio)
    }
  }

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`
  const formatSharpe = (value: number) => value.toFixed(2)

  const chartData = frontierData?.frontier_points.map(point => ({
    volatility: point.volatility * 100,
    return: point.expected_return * 100,
    sharpe: point.sharpe_ratio,
    ...point
  })) || []

  const optimalPoints = []
  if (frontierData?.optimal_portfolios?.max_sharpe) {
    optimalPoints.push({
      type: 'Max Sharpe',
      volatility: frontierData.optimal_portfolios.max_sharpe.volatility * 100,
      return: frontierData.optimal_portfolios.max_sharpe.expected_return * 100,
      sharpe: frontierData.optimal_portfolios.max_sharpe.sharpe_ratio,
      ...frontierData.optimal_portfolios.max_sharpe
    })
  }
  if (frontierData?.optimal_portfolios?.min_volatility) {
    optimalPoints.push({
      type: 'Min Volatility',
      volatility: frontierData.optimal_portfolios.min_volatility.volatility * 100,
      return: frontierData.optimal_portfolios.min_volatility.expected_return * 100,
      sharpe: frontierData.optimal_portfolios.min_volatility.sharpe_ratio,
      ...frontierData.optimal_portfolios.min_volatility
    })
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="font-semibold mb-1">Portfolio Metrics</p>
          <p className="text-sm">Return: {formatPercent(data.expected_return || data.return / 100)}</p>
          <p className="text-sm">Volatility: {formatPercent(data.volatility / 100)}</p>
          <p className="text-sm">Sharpe: {formatSharpe(data.sharpe)}</p>
          {data.type && <p className="text-sm font-semibold mt-1">{data.type}</p>}
        </div>
      )
    }
    return null
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Efficient Frontier Analysis
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Risk-return optimization using Modern Portfolio Theory
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setRefreshKey(prev => prev + 1)}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Refresh
          </Button>
        </div>

        {/* Chart */}
        {loading && (
          <div className="flex items-center justify-center h-96">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <span className="ml-2">Calculating efficient frontier...</span>
          </div>
        )}

        {error && (
          <Alert className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <div>
              <p className="font-semibold">Error Loading Efficient Frontier</p>
              <p className="text-sm">{error}</p>
            </div>
          </Alert>
        )}

        {!loading && !error && frontierData && (
          <div className="space-y-4">
            {/* Chart */}
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart
                margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis
                  dataKey="volatility"
                  domain={['dataMin - 1', 'dataMax + 1']}
                  label={{ value: 'Volatility (%)', position: 'insideBottom', offset: -10 }}
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  domain={['dataMin - 1', 'dataMax + 1']}
                  label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft' }}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                {/* Efficient Frontier Line */}
                {chartData.length > 0 && (
                  <Line
                    data={chartData}
                    type="monotone"
                    dataKey="return"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ r: 3, fill: '#3b82f6' }}
                    name="Efficient Frontier"
                    onClick={(data) => handlePointClick(data)}
                  />
                )}
                
                {/* Optimal Portfolios */}
                <Scatter
                  data={optimalPoints}
                  fill="#10b981"
                  name="Optimal Portfolios"
                  onClick={(data) => handlePointClick(data)}
                >
                  {optimalPoints.map((entry, index) => (
                    <ReferenceDot
                      key={index}
                      x={entry.volatility}
                      y={entry.return}
                      r={8}
                      fill="#10b981"
                      stroke="#fff"
                      strokeWidth={2}
                    />
                  ))}
                </Scatter>
              </ComposedChart>
            </ResponsiveContainer>

            {/* Optimal Portfolio Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {frontierData.optimal_portfolios?.max_sharpe && (
                <Card
                  className={`p-4 cursor-pointer transition-all ${
                    selectedPoint === frontierData.optimal_portfolios.max_sharpe
                      ? 'ring-2 ring-blue-500'
                      : 'hover:shadow-lg'
                  }`}
                  onClick={() => handlePointClick(frontierData.optimal_portfolios.max_sharpe!)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold flex items-center gap-2">
                        <Target className="h-4 w-4 text-green-500" />
                        Maximum Sharpe Ratio
                      </h3>
                      <p className="text-sm text-gray-600">Optimal risk-adjusted returns</p>
                    </div>
                    <Badge variant="success">Recommended</Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mt-3">
                    <div>
                      <p className="text-xs text-gray-500">Return</p>
                      <p className="font-semibold text-green-600">
                        {formatPercent(frontierData.optimal_portfolios.max_sharpe.expected_return)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Volatility</p>
                      <p className="font-semibold">
                        {formatPercent(frontierData.optimal_portfolios.max_sharpe.volatility)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Sharpe</p>
                      <p className="font-semibold text-blue-600">
                        {formatSharpe(frontierData.optimal_portfolios.max_sharpe.sharpe_ratio)}
                      </p>
                    </div>
                  </div>
                </Card>
              )}

              {frontierData.optimal_portfolios?.min_volatility && (
                <Card
                  className={`p-4 cursor-pointer transition-all ${
                    selectedPoint === frontierData.optimal_portfolios.min_volatility
                      ? 'ring-2 ring-blue-500'
                      : 'hover:shadow-lg'
                  }`}
                  onClick={() => handlePointClick(frontierData.optimal_portfolios.min_volatility!)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold flex items-center gap-2">
                        <Target className="h-4 w-4 text-blue-500" />
                        Minimum Volatility
                      </h3>
                      <p className="text-sm text-gray-600">Lowest risk portfolio</p>
                    </div>
                    <Badge>Conservative</Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mt-3">
                    <div>
                      <p className="text-xs text-gray-500">Return</p>
                      <p className="font-semibold">
                        {formatPercent(frontierData.optimal_portfolios.min_volatility.expected_return)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Volatility</p>
                      <p className="font-semibold text-blue-600">
                        {formatPercent(frontierData.optimal_portfolios.min_volatility.volatility)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Sharpe</p>
                      <p className="font-semibold">
                        {formatSharpe(frontierData.optimal_portfolios.min_volatility.sharpe_ratio)}
                      </p>
                    </div>
                  </div>
                </Card>
              )}
            </div>

            {/* Selected Portfolio Weights */}
            {selectedPoint && 'weights' in selectedPoint && (
              <Card className="p-4">
                <h3 className="font-semibold mb-3">Portfolio Allocation</h3>
                <div className="space-y-2">
                  {Object.entries(selectedPoint.weights)
                    .filter(([_, weight]) => weight > 0.001)
                    .sort((a, b) => b[1] - a[1])
                    .map(([strategy, weight]) => (
                      <div key={strategy} className="flex items-center justify-between">
                        <span className="text-sm">{strategy.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${weight * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-semibold w-12 text-right">
                            {formatPercent(weight)}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </Card>
            )}

            {/* Constraints Info */}
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>Max allocation per strategy: {formatPercent(frontierData.constraints.max_weight_per_strategy)}</span>
              <span>Risk-free rate: {formatPercent(frontierData.risk_free_rate)}</span>
              <span>Strategies analyzed: {frontierData.n_strategies}</span>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}

export default EfficientFrontier