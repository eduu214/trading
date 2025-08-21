/**
 * Correlation Matrix Heatmap Component
 * F001-US003 Task 4: Color-coded matrix visualization
 * 
 * Color scheme:
 * - Red: High correlation (>0.7)
 * - Yellow: Moderate correlation (0.3-0.7)
 * - Green: Low correlation (<0.3)
 */

import React, { useEffect, useState, useRef } from 'react';
import { ResponsiveContainer, Tooltip } from 'recharts';
import * as d3 from 'd3';

interface CorrelationData {
  strategies: string[];
  matrix: number[][];
  statistics: {
    avg_correlation: number;
    max_correlation: number;
    min_correlation: number;
    num_strategies: number;
  };
  high_correlations: Array<{
    strategy_1: string;
    strategy_2: string;
    correlation: number;
    severity: 'warning' | 'critical';
  }>;
}

interface CorrelationHeatmapProps {
  timePeriod?: '30d' | '60d' | '90d' | '1y';
  onCellClick?: (strategy1: string, strategy2: string, correlation: number) => void;
  showLabels?: boolean;
  cellSize?: number;
}

const CorrelationHeatmap: React.FC<CorrelationHeatmapProps> = ({
  timePeriod = '30d',
  onCellClick,
  showLabels = true,
  cellSize = 60
}) => {
  const [correlationData, setCorrelationData] = useState<CorrelationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredCell, setHoveredCell] = useState<{ row: number; col: number } | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Fetch correlation data
  useEffect(() => {
    const fetchCorrelationData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(
          `/api/v1/correlation/matrix?time_period=${timePeriod}`,
          {
            headers: {
              'Accept': 'application/json'
            }
          }
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch correlation data');
        }
        
        const data = await response.json();
        setCorrelationData({
          strategies: data.strategies,
          matrix: data.matrix,
          statistics: data.statistics,
          high_correlations: data.high_correlations
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };
    
    fetchCorrelationData();
  }, [timePeriod]);

  // Color scale function
  const getColor = (value: number) => {
    const absValue = Math.abs(value);
    
    if (absValue > 0.7) {
      // High correlation - red
      return `rgb(220, 38, 38, ${0.3 + absValue * 0.7})`;
    } else if (absValue > 0.3) {
      // Moderate correlation - yellow
      return `rgb(251, 191, 36, ${0.3 + absValue * 0.7})`;
    } else {
      // Low correlation - green
      return `rgb(34, 197, 94, ${0.3 + absValue * 0.7})`;
    }
  };

  // Draw heatmap using D3
  useEffect(() => {
    if (!correlationData || !svgRef.current) return;

    const { strategies, matrix } = correlationData;
    const margin = { top: 100, right: 100, bottom: 50, left: 100 };
    const width = strategies.length * cellSize;
    const height = strategies.length * cellSize;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create cells
    const cells = g.selectAll('.cell')
      .data(matrix.flatMap((row, i) => 
        row.map((value, j) => ({ row: i, col: j, value }))
      ))
      .enter()
      .append('g')
      .attr('class', 'cell')
      .attr('transform', d => `translate(${d.col * cellSize},${d.row * cellSize})`);

    // Add rectangles
    cells.append('rect')
      .attr('width', cellSize - 2)
      .attr('height', cellSize - 2)
      .attr('fill', d => getColor(d.value))
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1)
      .attr('rx', 4)
      .style('cursor', 'pointer')
      .on('mouseenter', (event, d) => {
        setHoveredCell({ row: d.row, col: d.col });
        
        // Highlight row and column
        d3.selectAll('.cell rect')
          .style('opacity', cell => 
            (cell.row === d.row || cell.col === d.col) ? 1 : 0.3
          );
      })
      .on('mouseleave', () => {
        setHoveredCell(null);
        d3.selectAll('.cell rect').style('opacity', 1);
      })
      .on('click', (event, d) => {
        if (onCellClick && d.row !== d.col) {
          onCellClick(
            strategies[d.row],
            strategies[d.col],
            d.value
          );
        }
      });

    // Add text values
    if (showLabels) {
      cells.append('text')
        .attr('x', cellSize / 2)
        .attr('y', cellSize / 2)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .style('font-size', '12px')
        .style('font-weight', '500')
        .style('fill', d => Math.abs(d.value) > 0.5 ? 'white' : '#1f2937')
        .style('pointer-events', 'none')
        .text(d => d.value.toFixed(2));
    }

    // Add row labels
    g.selectAll('.row-label')
      .data(strategies)
      .enter()
      .append('text')
      .attr('class', 'row-label')
      .attr('x', -10)
      .attr('y', (d, i) => i * cellSize + cellSize / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text(d => d);

    // Add column labels
    g.selectAll('.col-label')
      .data(strategies)
      .enter()
      .append('text')
      .attr('class', 'col-label')
      .attr('x', (d, i) => i * cellSize + cellSize / 2)
      .attr('y', -10)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .style('transform', (d, i) => 
        `rotate(-45deg) translate(${i * cellSize + cellSize / 2}px, -10px)`
      )
      .text(d => d);

    // Add color legend
    const legendWidth = 200;
    const legendHeight = 20;
    const legend = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${height + margin.top + 30})`);

    // Create gradient
    const gradient = svg.append('defs')
      .append('linearGradient')
      .attr('id', 'correlation-gradient')
      .attr('x1', '0%')
      .attr('x2', '100%');

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', 'rgb(34, 197, 94)');
    
    gradient.append('stop')
      .attr('offset', '50%')
      .attr('stop-color', 'rgb(251, 191, 36)');
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', 'rgb(220, 38, 38)');

    legend.append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', 'url(#correlation-gradient)');

    legend.append('text')
      .attr('x', 0)
      .attr('y', legendHeight + 15)
      .text('0.0')
      .style('font-size', '11px')
      .style('fill', '#6b7280');

    legend.append('text')
      .attr('x', legendWidth / 2)
      .attr('y', legendHeight + 15)
      .attr('text-anchor', 'middle')
      .text('0.5')
      .style('font-size', '11px')
      .style('fill', '#6b7280');

    legend.append('text')
      .attr('x', legendWidth)
      .attr('y', legendHeight + 15)
      .attr('text-anchor', 'end')
      .text('1.0')
      .style('font-size', '11px')
      .style('fill', '#6b7280');

    legend.append('text')
      .attr('x', legendWidth / 2)
      .attr('y', -5)
      .attr('text-anchor', 'middle')
      .text('Correlation Strength')
      .style('font-size', '12px')
      .style('font-weight', '500')
      .style('fill', '#1f2937');

  }, [correlationData, cellSize, showLabels, onCellClick]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">Error loading correlation data: {error}</p>
      </div>
    );
  }

  if (!correlationData) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Strategy Correlation Matrix
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Time Period: {timePeriod} | 
          Avg Correlation: {correlationData.statistics.avg_correlation.toFixed(3)} |
          Max: {correlationData.statistics.max_correlation.toFixed(3)}
        </p>
      </div>

      <div className="overflow-auto">
        <svg ref={svgRef}></svg>
      </div>

      {hoveredCell && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm font-medium text-gray-700">
            {correlationData.strategies[hoveredCell.row]} ↔ {correlationData.strategies[hoveredCell.col]}
          </p>
          <p className="text-sm text-gray-600">
            Correlation: {correlationData.matrix[hoveredCell.row][hoveredCell.col].toFixed(3)}
          </p>
        </div>
      )}

      {correlationData.high_correlations.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            ⚠️ High Correlation Warnings
          </h4>
          <div className="space-y-1">
            {correlationData.high_correlations.slice(0, 5).map((pair, index) => (
              <div
                key={index}
                className={`flex items-center justify-between p-2 rounded ${
                  pair.severity === 'critical' ? 'bg-red-50' : 'bg-yellow-50'
                }`}
              >
                <span className="text-sm">
                  {pair.strategy_1} ↔ {pair.strategy_2}
                </span>
                <span className={`text-sm font-medium ${
                  pair.severity === 'critical' ? 'text-red-700' : 'text-yellow-700'
                }`}>
                  {pair.correlation.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CorrelationHeatmap;