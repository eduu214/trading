'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Percent,
  AlertTriangle,
  Shield,
  Target,
  BarChart3,
  PieChart,
  RefreshCw,
  Info
} from 'lucide-react'

interface PortfolioMetrics {
  expected_annual_return: number
  annual_volatility: number
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown: number
  var_95: number
  cvar_95: number
  calmar_ratio: number
  skewness: number
  kurtosis: number
}

interface PortfolioState {
  total_value: number
  total_pnl: number
  cash_balance: number
  portfolio_volatility?: number
  portfolio_sharpe?: number
  max_drawdown?: number
  var_1d_95?: number
}

interface PerformanceData {
  date: string
  value: number
  return: number
  drawdown: number
}

interface PortfolioMetricsProps {
  portfolioId?: string
  allocations?: { [key: string]: number }
  refreshInterval?: number
  className?: string
}

export const PortfolioMetrics: React.FC<PortfolioMetricsProps> = ({
  portfolioId = 'main',
  allocations,
  refreshInterval = 5000,
  className = ''
}) => {
  const [metrics, setMetrics] = useState<PortfolioMetrics | null>(null)
  const [portfolioState, setPortfolioState] = useState<PortfolioState | null>(null)
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([])
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch portfolio metrics
  const fetchMetrics = useCallback(async () => {
    if (!allocations) return
    
    try {
      const params = new URLSearchParams({
        allocation: JSON.stringify(allocations),
        portfolio_id: portfolioId
      })
      
      const response = await fetch(
        `http://localhost:8000/api/v1/portfolio/metrics?${params}`
      )
      
      if (response.ok) {
        const data = await response.json()
        setMetrics(data.metrics)
        if (typeof window !== 'undefined') {
          setLastUpdate(new Date())
        }
      }
    } catch (error) {
      console.error('Error fetching metrics:', error)
    }
  }, [portfolioId, allocations])

  // Fetch portfolio state
  const fetchPortfolioState = useCallback(async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/portfolio/?portfolio_id=${portfolioId}`
      )
      
      if (response.ok) {
        const data = await response.json()
        setPortfolioState({
          total_value: parseFloat(data.total_value),
          total_pnl: parseFloat(data.total_pnl),
          cash_balance: parseFloat(data.cash_balance),
          portfolio_volatility: data.portfolio_volatility ? parseFloat(data.portfolio_volatility) : undefined,
          portfolio_sharpe: data.portfolio_sharpe ? parseFloat(data.portfolio_sharpe) : undefined,
          max_drawdown: data.max_drawdown ? parseFloat(data.max_drawdown) : undefined,
          var_1d_95: data.var_1d_95 ? parseFloat(data.var_1d_95) : undefined
        })
      }
    } catch (error) {
      console.error('Error fetching portfolio state:', error)
    }
  }, [portfolioId])

  // Generate mock performance data
  const generatePerformanceData = useCallback(() => {
    const data: PerformanceData[] = []
    const days = 30
    let value = 10000
    let peak = value
    
    for (let i = 0; i < days; i++) {
      const dailyReturn = (Math.random() - 0.48) * 0.03 // -1.5% to +1.5% daily
      value = value * (1 + dailyReturn)
      peak = Math.max(peak, value)
      const drawdown = (value - peak) / peak
      
      data.push({
        date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        value: Math.round(value),
        return: dailyReturn * 100,
        drawdown: drawdown * 100
      })
    }
    
    setPerformanceData(data)
  }, [])

  // Initialize lastUpdate on client side only
  useEffect(() => {
    if (typeof window !== 'undefined' && !lastUpdate) {
      setLastUpdate(new Date())
    }
  }, [lastUpdate])

  // Initial load and refresh
  useEffect(() => {
    if (allocations) {
      fetchMetrics()
    }
    fetchPortfolioState()
    generatePerformanceData()
  }, [allocations, fetchMetrics, fetchPortfolioState, generatePerformanceData])

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh || !refreshInterval) return
    
    const interval = setInterval(() => {
      if (allocations) {
        fetchMetrics()
      }
      fetchPortfolioState()
    }, refreshInterval)
    
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, allocations, fetchMetrics, fetchPortfolioState])

  const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`
  const formatCurrency = (value: number) => `$${Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`
  const formatNumber = (value: number, decimals: number = 2) => value.toFixed(decimals)

  // Risk level calculation
  const getRiskLevel = (volatility: number) => {
    if (volatility < 0.10) return { level: 'Low', color: 'text-green-600', badge: 'success' }
    if (volatility < 0.20) return { level: 'Moderate', color: 'text-yellow-600', badge: 'warning' }
    return { level: 'High', color: 'text-red-600', badge: 'danger' }
  }

  // Sharpe ratio rating
  const getSharpeRating = (sharpe: number) => {
    if (sharpe < 0) return { rating: 'Poor', color: 'text-red-600' }
    if (sharpe < 1) return { rating: 'Suboptimal', color: 'text-yellow-600' }
    if (sharpe < 2) return { rating: 'Good', color: 'text-green-600' }
    return { rating: 'Excellent', color: 'text-blue-600' }
  }

  const riskLevel = metrics ? getRiskLevel(metrics.annual_volatility) : null
  const sharpeRating = metrics ? getSharpeRating(metrics.sharpe_ratio) : null

  // Prepare data for radial chart
  const radialData = metrics ? [
    {
      name: 'Sharpe',
      value: Math.min(Math.max(metrics.sharpe_ratio * 33.33, 0), 100),
      fill: '#3b82f6'
    },
    {
      name: 'Sortino',
      value: Math.min(Math.max(metrics.sortino_ratio * 33.33, 0), 100),
      fill: '#10b981'
    },
    {
      name: 'Calmar',
      value: Math.min(Math.max(metrics.calmar_ratio * 20, 0), 100),
      fill: '#f59e0b'
    }
  ] : []

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Expected Return</p>
              <p className="text-2xl font-bold text-green-600">
                {metrics ? formatPercent(metrics.expected_annual_return) : '--'}
              </p>
              <p className="text-xs text-gray-500 mt-1">Annual</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500 opacity-50" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Volatility</p>
              <p className="text-2xl font-bold">
                {metrics ? formatPercent(metrics.annual_volatility) : '--'}
              </p>
              {riskLevel && (
                <Badge variant={riskLevel.badge as any} className="mt-1">
                  {riskLevel.level} Risk
                </Badge>
              )}
            </div>
            <Activity className="h-8 w-8 text-blue-500 opacity-50" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Sharpe Ratio</p>
              <p className={`text-2xl font-bold ${sharpeRating?.color || ''}`}>
                {metrics ? formatNumber(metrics.sharpe_ratio) : '--'}
              </p>
              {sharpeRating && (
                <p className="text-xs text-gray-500 mt-1">{sharpeRating.rating}</p>
              )}
            </div>
            <Target className="h-8 w-8 text-purple-500 opacity-50" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Max Drawdown</p>
              <p className="text-2xl font-bold text-red-600">
                {metrics ? formatPercent(metrics.max_drawdown) : '--'}
              </p>
              <p className="text-xs text-gray-500 mt-1">Historical</p>
            </div>
            <TrendingDown className="h-8 w-8 text-red-500 opacity-50" />
          </div>
        </Card>
      </div>

      {/* Main Metrics Dashboard */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Portfolio Metrics Dashboard
          </h2>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              Last update: {lastUpdate ? lastUpdate.toISOString().split('T')[1].split('.')[0] : '--:--:--'}
            </Badge>
            <button
              onClick={() => {
                if (allocations) fetchMetrics()
                fetchPortfolioState()
              }}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="risk">Risk Analysis</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="ratios">Ratios</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-gray-600">Portfolio Value</p>
                <p className="text-lg font-semibold">
                  {portfolioState ? formatCurrency(portfolioState.total_value) : '--'}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-gray-600">Total P&L</p>
                <p className={`text-lg font-semibold ${portfolioState && portfolioState.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {portfolioState ? formatCurrency(portfolioState.total_pnl) : '--'}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-gray-600">Cash Balance</p>
                <p className="text-lg font-semibold">
                  {portfolioState ? formatCurrency(portfolioState.cash_balance) : '--'}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-gray-600">Active Strategies</p>
                <p className="text-lg font-semibold">
                  {allocations ? Object.values(allocations).filter(w => w > 0.01).length : 0}
                </p>
              </div>
            </div>

            {/* Performance Chart */}
            <div className="mt-6">
              <h3 className="text-sm font-semibold mb-3">Portfolio Value (30 Days)</h3>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.1}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          <TabsContent value="risk" className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  <p className="text-sm font-semibold">Value at Risk (95%)</p>
                </div>
                <p className="text-2xl font-bold">
                  {metrics ? formatPercent(metrics.var_95) : '--'}
                </p>
                <p className="text-xs text-gray-500">1-day potential loss</p>
              </div>
              
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-4 w-4 text-blue-500" />
                  <p className="text-sm font-semibold">CVaR (95%)</p>
                </div>
                <p className="text-2xl font-bold">
                  {metrics ? formatPercent(metrics.cvar_95) : '--'}
                </p>
                <p className="text-xs text-gray-500">Expected shortfall</p>
              </div>

              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="h-4 w-4 text-purple-500" />
                  <p className="text-sm font-semibold">Risk Level</p>
                </div>
                {riskLevel && (
                  <>
                    <p className={`text-2xl font-bold ${riskLevel.color}`}>
                      {riskLevel.level}
                    </p>
                    <Progress 
                      value={metrics ? metrics.annual_volatility * 333 : 0} 
                      className="mt-2"
                    />
                  </>
                )}
              </div>
            </div>

            {/* Distribution Metrics */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-semibold mb-3">Distribution Characteristics</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-600">Skewness</p>
                  <p className="font-semibold">
                    {metrics ? formatNumber(metrics.skewness, 3) : '--'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {metrics && metrics.skewness > 0 ? 'Right-tailed' : 'Left-tailed'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Kurtosis</p>
                  <p className="font-semibold">
                    {metrics ? formatNumber(metrics.kurtosis, 3) : '--'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {metrics && metrics.kurtosis > 3 ? 'Fat-tailed' : 'Normal-tailed'}
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="performance" className="space-y-4">
            {/* Daily Returns Chart */}
            <div>
              <h3 className="text-sm font-semibold mb-3">Daily Returns (%)</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar
                    dataKey="return"
                    fill="#3b82f6"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Drawdown Chart */}
            <div>
              <h3 className="text-sm font-semibold mb-3">Drawdown (%)</h3>
              <ResponsiveContainer width="100%" height={150}>
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="drawdown"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          <TabsContent value="ratios" className="space-y-4">
            {/* Radial Chart for Ratios */}
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={250}>
                <RadialBarChart 
                  cx="50%" 
                  cy="50%" 
                  innerRadius="10%" 
                  outerRadius="80%" 
                  data={radialData}
                >
                  <RadialBar dataKey="value" cornerRadius={10} fill="#8884d8" />
                  <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                  <Tooltip />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>

            {/* Ratio Details */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-600">Sharpe Ratio</p>
                <p className="text-xl font-bold text-blue-600">
                  {metrics ? formatNumber(metrics.sharpe_ratio) : '--'}
                </p>
                <p className="text-xs text-gray-500">Risk-adjusted return</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Sortino Ratio</p>
                <p className="text-xl font-bold text-green-600">
                  {metrics ? formatNumber(metrics.sortino_ratio) : '--'}
                </p>
                <p className="text-xs text-gray-500">Downside risk-adjusted</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Calmar Ratio</p>
                <p className="text-xl font-bold text-yellow-600">
                  {metrics ? formatNumber(metrics.calmar_ratio) : '--'}
                </p>
                <p className="text-xs text-gray-500">Return / Max DD</p>
              </div>
            </div>

            {/* Ratio Interpretation */}
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start gap-2">
                <Info className="h-4 w-4 text-blue-500 mt-0.5" />
                <div className="text-sm">
                  <p className="font-semibold mb-1">Ratio Interpretation</p>
                  <p className="text-gray-600">
                    {metrics && metrics.sharpe_ratio > 1
                      ? 'Portfolio shows good risk-adjusted returns. '
                      : 'Portfolio may benefit from optimization. '}
                    {metrics && metrics.sortino_ratio > metrics.sharpe_ratio
                      ? 'Downside protection is strong. '
                      : ''}
                    {metrics && metrics.calmar_ratio > 3
                      ? 'Excellent recovery from drawdowns.'
                      : 'Consider reducing drawdown risk.'}
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  )
}

export default PortfolioMetrics