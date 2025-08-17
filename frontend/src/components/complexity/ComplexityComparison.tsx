'use client';

import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  Area,
  ComposedChart,
  Bar
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRight, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ComplexityLevel {
  complexity_level: number;
  annual_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  risk_adjusted_return: number;
}

export function ComplexityComparison({ strategyId }: { strategyId: string }) {
  const [comparisonData, setComparisonData] = useState<ComplexityLevel[]>([]);
  const [currentLevel, setCurrentLevel] = useState<number>(5);
  const [optimalLevel, setOptimalLevel] = useState<number>(5);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComparisonData();
  }, [strategyId]);

  const fetchComparisonData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/complexity/compare/${strategyId}?levels=1,2,3,4,5,6,7,8,9,10`
      );
      
      if (response.ok) {
        const data = await response.json();
        setComparisonData(data.comparisons || []);
        setCurrentLevel(data.current_level || 5);
        setOptimalLevel(data.optimal_level || 5);
      }
    } catch (err) {
      console.error('Failed to fetch comparison data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Generate sample data if no real data available
  const sampleData = comparisonData.length > 0 ? comparisonData : [
    { complexity_level: 1, annual_return: 0.08, sharpe_ratio: 0.8, max_drawdown: -0.15, volatility: 0.10, risk_adjusted_return: 0.068 },
    { complexity_level: 2, annual_return: 0.10, sharpe_ratio: 1.0, max_drawdown: -0.14, volatility: 0.10, risk_adjusted_return: 0.086 },
    { complexity_level: 3, annual_return: 0.12, sharpe_ratio: 1.2, max_drawdown: -0.13, volatility: 0.10, risk_adjusted_return: 0.104 },
    { complexity_level: 4, annual_return: 0.14, sharpe_ratio: 1.3, max_drawdown: -0.12, volatility: 0.11, risk_adjusted_return: 0.123 },
    { complexity_level: 5, annual_return: 0.15, sharpe_ratio: 1.4, max_drawdown: -0.12, volatility: 0.11, risk_adjusted_return: 0.132 },
    { complexity_level: 6, annual_return: 0.16, sharpe_ratio: 1.5, max_drawdown: -0.11, volatility: 0.11, risk_adjusted_return: 0.142 },
    { complexity_level: 7, annual_return: 0.17, sharpe_ratio: 1.4, max_drawdown: -0.13, volatility: 0.12, risk_adjusted_return: 0.148 },
    { complexity_level: 8, annual_return: 0.17, sharpe_ratio: 1.3, max_drawdown: -0.15, volatility: 0.13, risk_adjusted_return: 0.145 },
    { complexity_level: 9, annual_return: 0.16, sharpe_ratio: 1.2, max_drawdown: -0.17, volatility: 0.14, risk_adjusted_return: 0.133 },
    { complexity_level: 10, annual_return: 0.15, sharpe_ratio: 1.0, max_drawdown: -0.20, volatility: 0.16, risk_adjusted_return: 0.120 }
  ];

  const getChangeIndicator = (current: number, optimal: number) => {
    const diff = optimal - current;
    if (diff > 0) return { icon: TrendingUp, color: 'text-green-600', text: `+${diff.toFixed(2)}` };
    if (diff < 0) return { icon: TrendingDown, color: 'text-red-600', text: diff.toFixed(2) };
    return { icon: Minus, color: 'text-gray-600', text: '0.00' };
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatRatio = (value: number) => value.toFixed(2);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="font-medium mb-2">Complexity Level {label}</p>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Annual Return:</span>
              <span className="font-medium">{formatPercent(data.annual_return)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Sharpe Ratio:</span>
              <span className="font-medium">{formatRatio(data.sharpe_ratio)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Max Drawdown:</span>
              <span className="font-medium">{formatPercent(data.max_drawdown)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Risk-Adj Return:</span>
              <span className="font-medium">{formatPercent(data.risk_adjusted_return)}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Current Level</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentLevel}</div>
            <p className="text-xs text-muted-foreground">
              Active complexity setting
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Optimal Level</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{optimalLevel}</div>
            <p className="text-xs text-muted-foreground">
              Recommended for best performance
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Improvement Potential</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <ArrowRight className="h-4 w-4" />
              <span className="text-2xl font-bold">
                {Math.abs(optimalLevel - currentLevel)} levels
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              {optimalLevel > currentLevel ? 'Increase' : optimalLevel < currentLevel ? 'Decrease' : 'Already optimal'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Risk-Return Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Risk-Return Profile Across Complexity Levels</CardTitle>
          <CardDescription>
            Compare performance metrics at different complexity levels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={sampleData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="complexity_level" 
                label={{ value: 'Complexity Level', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                yAxisId="left"
                label={{ value: 'Return (%)', angle: -90, position: 'insideLeft' }}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <YAxis 
                yAxisId="right"
                orientation="right"
                label={{ value: 'Sharpe Ratio', angle: 90, position: 'insideRight' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="annual_return"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
                name="Annual Return"
              />
              
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="sharpe_ratio"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: '#10b981' }}
                name="Sharpe Ratio"
              />
              
              <ReferenceLine 
                x={currentLevel} 
                stroke="#666" 
                strokeDasharray="5 5"
                label={{ value: "Current", position: "top" }}
              />
              
              <ReferenceLine 
                x={optimalLevel} 
                stroke="#10b981" 
                strokeDasharray="5 5"
                label={{ value: "Optimal", position: "top" }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Detailed Metrics Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Complexity Comparison</CardTitle>
          <CardDescription>
            All metrics across complexity levels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Level</th>
                  <th className="text-right p-2">Annual Return</th>
                  <th className="text-right p-2">Sharpe Ratio</th>
                  <th className="text-right p-2">Max Drawdown</th>
                  <th className="text-right p-2">Volatility</th>
                  <th className="text-right p-2">Risk-Adj Return</th>
                </tr>
              </thead>
              <tbody>
                {sampleData.map((level) => (
                  <tr 
                    key={level.complexity_level}
                    className={`border-b ${
                      level.complexity_level === currentLevel ? 'bg-blue-50' : ''
                    } ${
                      level.complexity_level === optimalLevel ? 'bg-green-50' : ''
                    }`}
                  >
                    <td className="p-2">
                      <div className="flex items-center gap-2">
                        {level.complexity_level}
                        {level.complexity_level === currentLevel && (
                          <Badge variant="outline" className="text-xs">Current</Badge>
                        )}
                        {level.complexity_level === optimalLevel && (
                          <Badge variant="outline" className="text-xs text-green-600">Optimal</Badge>
                        )}
                      </div>
                    </td>
                    <td className="text-right p-2">{formatPercent(level.annual_return)}</td>
                    <td className="text-right p-2">{formatRatio(level.sharpe_ratio)}</td>
                    <td className="text-right p-2">{formatPercent(level.max_drawdown)}</td>
                    <td className="text-right p-2">{formatPercent(level.volatility)}</td>
                    <td className="text-right p-2 font-medium">
                      {formatPercent(level.risk_adjusted_return)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Trade-off Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Complexity Trade-offs</CardTitle>
          <CardDescription>
            Understanding the balance between complexity and performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sampleData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="complexity_level"
                label={{ value: 'Complexity Level', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              <Line
                type="monotone"
                dataKey="risk_adjusted_return"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="Risk-Adjusted Return"
                dot={{ fill: '#8b5cf6' }}
              />
              
              <Line
                type="monotone"
                dataKey="volatility"
                stroke="#ef4444"
                strokeWidth={2}
                name="Volatility"
                strokeDasharray="5 5"
                dot={{ fill: '#ef4444' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}