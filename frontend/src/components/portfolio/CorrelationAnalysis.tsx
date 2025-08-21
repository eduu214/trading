'use client'

import React, { useEffect, useState, useRef } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { 
  AlertTriangle,
  Info,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  ChevronRight
} from 'lucide-react'
import * as d3 from 'd3'

interface CorrelationData {
  strategies: string[]
  matrix: number[][]
  statistics: {
    avg_correlation: number
    max_correlation: number
    min_correlation: number
    num_strategies: number
  }
  high_correlations: Array<{
    strategy_1: string
    strategy_2: string
    correlation: number
    severity: 'warning' | 'critical'
  }>
}

interface DiversificationData {
  overall_score: number
  correlation_score: number
  num_strategies: number
  avg_correlation: number
  max_correlation: number
  high_correlation_pairs: number
  recommendations: string[]
}

interface CorrelationAnalysisProps {
  portfolioId?: string
  timePeriod?: '30d' | '60d' | '90d' | '1y'
  className?: string
}

export default function CorrelationAnalysis({ 
  portfolioId = 'main',
  timePeriod = '30d',
  className = ''
}: CorrelationAnalysisProps) {
  const [correlationData, setCorrelationData] = useState<CorrelationData | null>(null)
  const [diversificationData, setDiversificationData] = useState<DiversificationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedPeriod, setSelectedPeriod] = useState(timePeriod)
  const svgRef = useRef<SVGSVGElement>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      // Fetch correlation matrix
      const corrResponse = await fetch(
        `http://localhost:8000/api/v1/correlation/matrix?time_period=${selectedPeriod}`
      )
      if (corrResponse.ok) {
        const corrData = await corrResponse.json()
        setCorrelationData({
          strategies: corrData.strategies,
          matrix: corrData.matrix,
          statistics: corrData.statistics,
          high_correlations: corrData.high_correlations
        })
      }

      // Fetch diversification score
      const divResponse = await fetch(
        `http://localhost:8000/api/v1/correlation/diversification?portfolio_id=${portfolioId}`
      )
      if (divResponse.ok) {
        const divData = await divResponse.json()
        setDiversificationData(divData)
      }
    } catch (error) {
      console.error('Error fetching correlation data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [selectedPeriod, portfolioId])

  // Draw correlation heatmap
  useEffect(() => {
    if (!correlationData || !svgRef.current) return

    const { strategies, matrix } = correlationData
    const cellSize = 50
    const margin = { top: 100, right: 50, bottom: 50, left: 100 }
    const width = strategies.length * cellSize
    const height = strategies.length * cellSize

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Color scale
    const colorScale = (value: number) => {
      const absValue = Math.abs(value)
      if (absValue > 0.7) {
        return `rgba(239, 68, 68, ${0.3 + absValue * 0.7})`
      } else if (absValue > 0.3) {
        return `rgba(245, 158, 11, ${0.3 + absValue * 0.7})`
      } else {
        return `rgba(34, 197, 94, ${0.3 + absValue * 0.7})`
      }
    }

    // Create cells
    const cells = g.selectAll('.cell')
      .data(matrix.flatMap((row, i) => 
        row.map((value, j) => ({ row: i, col: j, value }))
      ))
      .enter()
      .append('g')
      .attr('class', 'cell')
      .attr('transform', d => `translate(${d.col * cellSize},${d.row * cellSize})`)

    // Add rectangles
    cells.append('rect')
      .attr('width', cellSize - 2)
      .attr('height', cellSize - 2)
      .attr('fill', d => colorScale(d.value))
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1)
      .attr('rx', 2)
      .style('cursor', 'pointer')
      .on('mouseenter', function(event, d) {
        // Highlight row and column
        d3.selectAll('.cell rect')
          .style('opacity', (cell: any) => 
            (cell.row === d.row || cell.col === d.col) ? 1 : 0.3
          )
      })
      .on('mouseleave', function() {
        d3.selectAll('.cell rect').style('opacity', 1)
      })

    // Add text values
    cells.append('text')
      .attr('x', cellSize / 2)
      .attr('y', cellSize / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .style('font-size', '10px')
      .style('font-weight', '500')
      .style('fill', d => Math.abs(d.value) > 0.5 ? 'white' : '#1f2937')
      .style('pointer-events', 'none')
      .text(d => d.value.toFixed(2))

    // Add row labels
    g.selectAll('.row-label')
      .data(strategies)
      .enter()
      .append('text')
      .attr('class', 'row-label')
      .attr('x', -5)
      .attr('y', (d, i) => i * cellSize + cellSize / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .style('font-size', '11px')
      .style('fill', '#6b7280')
      .text(d => d.replace(/_/g, ' ').substring(0, 15))

    // Add column labels  
    g.selectAll('.col-label')
      .data(strategies)
      .enter()
      .append('text')
      .attr('class', 'col-label')
      .attr('x', 0)
      .attr('y', 0)
      .attr('text-anchor', 'start')
      .style('font-size', '11px')
      .style('fill', '#6b7280')
      .attr('transform', (d, i) => 
        `translate(${i * cellSize + cellSize / 2}, -5) rotate(-45)`
      )
      .text(d => d.replace(/_/g, ' ').substring(0, 15))

  }, [correlationData])

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBadge = (score: number) => {
    if (score >= 80) return { variant: 'success' as const, text: 'Excellent' }
    if (score >= 60) return { variant: 'warning' as const, text: 'Good' }
    return { variant: 'destructive' as const, text: 'Poor' }
  }

  if (loading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </Card>
    )
  }

  return (
    <div className={className}>
      {/* Diversification Score Card */}
      {diversificationData && (
        <Card className="p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Portfolio Diversification Analysis</h2>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchData}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">Overall Score</p>
              <p className={`text-3xl font-bold ${getScoreColor(diversificationData.overall_score)}`}>
                {diversificationData.overall_score.toFixed(0)}/100
              </p>
              <Badge {...getScoreBadge(diversificationData.overall_score)} className="mt-2">
                {getScoreBadge(diversificationData.overall_score).text}
              </Badge>
            </div>

            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">Avg Correlation</p>
              <p className="text-2xl font-bold">{diversificationData.avg_correlation.toFixed(3)}</p>
              <p className="text-xs text-gray-500 mt-1">Lower is better</p>
            </div>

            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">High Corr. Pairs</p>
              <p className="text-2xl font-bold">{diversificationData.high_correlation_pairs}</p>
              <p className="text-xs text-gray-500 mt-1">&gt;0.6 correlation</p>
            </div>

            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">Strategies</p>
              <p className="text-2xl font-bold">{diversificationData.num_strategies}</p>
              <p className="text-xs text-gray-500 mt-1">In portfolio</p>
            </div>
          </div>

          {/* Recommendations */}
          <div>
            <h3 className="font-semibold mb-2 flex items-center">
              <Info className="h-4 w-4 mr-2" />
              Recommendations
            </h3>
            <div className="space-y-2">
              {diversificationData.recommendations.map((rec, idx) => (
                <div key={idx} className="flex items-start">
                  <ChevronRight className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0" />
                  <p className="text-sm text-gray-700">{rec}</p>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Correlation Matrix */}
      {correlationData && (
        <Card className="p-6 mb-6">
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-xl font-semibold">Strategy Correlation Matrix</h2>
              <div className="flex gap-2">
                {(['30d', '60d', '90d', '1y'] as const).map(period => (
                  <Button
                    key={period}
                    variant={selectedPeriod === period ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedPeriod(period)}
                  >
                    {period}
                  </Button>
                ))}
              </div>
            </div>
            <p className="text-sm text-gray-600">
              Time Period: {selectedPeriod} | 
              Avg: {correlationData.statistics.avg_correlation.toFixed(3)} | 
              Max: {correlationData.statistics.max_correlation.toFixed(3)}
            </p>
          </div>

          <div className="overflow-x-auto">
            <svg ref={svgRef}></svg>
          </div>

          {/* Color Legend */}
          <div className="mt-4 flex items-center justify-center space-x-8">
            <div className="flex items-center">
              <div className="w-4 h-4 rounded mr-2" style={{ backgroundColor: 'rgba(34, 197, 94, 0.7)' }}></div>
              <span className="text-sm text-gray-600">Low (&lt;0.3)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 rounded mr-2" style={{ backgroundColor: 'rgba(245, 158, 11, 0.7)' }}></div>
              <span className="text-sm text-gray-600">Moderate (0.3-0.7)</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 rounded mr-2" style={{ backgroundColor: 'rgba(239, 68, 68, 0.7)' }}></div>
              <span className="text-sm text-gray-600">High (&gt;0.7)</span>
            </div>
          </div>
        </Card>
      )}

      {/* High Correlation Warnings */}
      {correlationData && correlationData.high_correlations.length > 0 && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <div>
            <p className="font-semibold text-yellow-800">High Correlation Warning</p>
            <p className="text-sm text-yellow-700 mt-1">
              Found {correlationData.high_correlations.length} strategy pairs with correlation &gt;0.6
            </p>
            <div className="mt-3 space-y-1">
              {correlationData.high_correlations.slice(0, 3).map((pair, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">
                    {pair.strategy_1.replace(/_/g, ' ')} ↔ {pair.strategy_2.replace(/_/g, ' ')}
                  </span>
                  <Badge variant={pair.severity === 'critical' ? 'destructive' : 'warning'}>
                    {pair.correlation.toFixed(3)}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </Alert>
      )}
    </div>
  )
}