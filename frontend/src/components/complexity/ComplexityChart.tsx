'use client';

import React from 'react';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  Area,
  ComposedChart
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface OptimizationResult {
  metrics: {
    sharpe_ratio: number;
    max_drawdown: number;
    volatility: number;
    win_rate: number;
    profit_factor: number;
  };
  risk_adjusted_metrics: {
    annual_return: number;
    risk_adjusted_return: number;
    calmar_ratio: number;
    sortino_ratio: number;
    information_ratio?: number;
  };
}

export function ComplexityChart({ result }: { result: OptimizationResult }) {
  // Prepare data for radar chart
  const radarData = [
    {
      metric: 'Sharpe Ratio',
      value: Math.min(100, (result.metrics.sharpe_ratio / 3) * 100),
      fullMark: 100
    },
    {
      metric: 'Win Rate',
      value: result.metrics.win_rate * 100,
      fullMark: 100
    },
    {
      metric: 'Profit Factor',
      value: Math.min(100, (result.metrics.profit_factor / 3) * 100),
      fullMark: 100
    },
    {
      metric: 'Risk Control',
      value: Math.max(0, 100 + result.metrics.max_drawdown * 100),
      fullMark: 100
    },
    {
      metric: 'Stability',
      value: Math.max(0, 100 - result.metrics.volatility * 100),
      fullMark: 100
    }
  ];

  // Prepare data for risk-adjusted metrics bar chart
  const barData = [
    {
      metric: 'Annual Return',
      value: result.risk_adjusted_metrics.annual_return * 100,
      type: 'return'
    },
    {
      metric: 'Risk-Adj Return',
      value: result.risk_adjusted_metrics.risk_adjusted_return * 100,
      type: 'adjusted'
    },
    {
      metric: 'Calmar Ratio',
      value: result.risk_adjusted_metrics.calmar_ratio,
      type: 'ratio'
    },
    {
      metric: 'Sortino Ratio',
      value: result.risk_adjusted_metrics.sortino_ratio,
      type: 'ratio'
    }
  ];

  // Custom tooltip for better formatting
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload[0]) {
      return (
        <div className="bg-white p-2 border rounded shadow-sm">
          <p className="text-sm font-medium">{label}</p>
          <p className="text-sm text-blue-600">
            {typeof payload[0].value === 'number' 
              ? payload[0].value.toFixed(2)
              : payload[0].value}
            {payload[0].unit || ''}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="radar" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="radar">Performance Radar</TabsTrigger>
          <TabsTrigger value="metrics">Risk Metrics</TabsTrigger>
          <TabsTrigger value="distribution">Distribution</TabsTrigger>
        </TabsList>

        <TabsContent value="radar" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Profile</CardTitle>
              <CardDescription>
                Multi-dimensional view of strategy performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={radarData}>
                  <PolarGrid strokeDasharray="3 3" />
                  <PolarAngleAxis dataKey="metric" className="text-xs" />
                  <PolarRadiusAxis 
                    angle={90} 
                    domain={[0, 100]} 
                    tickCount={5}
                  />
                  <Radar
                    name="Performance"
                    dataKey="value"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.6}
                  />
                  <Tooltip content={<CustomTooltip />} />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk-Adjusted Metrics</CardTitle>
              <CardDescription>
                Comparative view of return and risk metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" className="text-xs" />
                  <YAxis />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar 
                    dataKey="value" 
                    fill="#3b82f6"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="distribution" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Metric Distribution</CardTitle>
              <CardDescription>
                Distribution of key performance indicators
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Sharpe Ratio Distribution */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Sharpe Ratio</span>
                    <span className="text-sm text-muted-foreground">
                      {result.metrics.sharpe_ratio.toFixed(2)}
                    </span>
                  </div>
                  <div className="relative h-2 bg-gray-200 rounded">
                    <div 
                      className="absolute h-full bg-blue-600 rounded"
                      style={{ 
                        width: `${Math.min(100, (result.metrics.sharpe_ratio / 3) * 100)}%` 
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>0</span>
                    <span>1.5</span>
                    <span>3.0</span>
                  </div>
                </div>

                {/* Max Drawdown Distribution */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Max Drawdown</span>
                    <span className="text-sm text-muted-foreground">
                      {(result.metrics.max_drawdown * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="relative h-2 bg-gray-200 rounded">
                    <div 
                      className="absolute h-full bg-red-600 rounded"
                      style={{ 
                        width: `${Math.abs(result.metrics.max_drawdown) * 100}%` 
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>0%</span>
                    <span>-50%</span>
                    <span>-100%</span>
                  </div>
                </div>

                {/* Volatility Distribution */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Volatility</span>
                    <span className="text-sm text-muted-foreground">
                      {(result.metrics.volatility * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="relative h-2 bg-gray-200 rounded">
                    <div 
                      className="absolute h-full bg-yellow-600 rounded"
                      style={{ 
                        width: `${Math.min(100, result.metrics.volatility * 200)}%` 
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>0%</span>
                    <span>25%</span>
                    <span>50%</span>
                  </div>
                </div>

                {/* Win Rate Distribution */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Win Rate</span>
                    <span className="text-sm text-muted-foreground">
                      {(result.metrics.win_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="relative h-2 bg-gray-200 rounded">
                    <div 
                      className="absolute h-full bg-green-600 rounded"
                      style={{ 
                        width: `${result.metrics.win_rate * 100}%` 
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>0%</span>
                    <span>50%</span>
                    <span>100%</span>
                  </div>
                </div>

                {/* Profit Factor Distribution */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Profit Factor</span>
                    <span className="text-sm text-muted-foreground">
                      {result.metrics.profit_factor.toFixed(2)}
                    </span>
                  </div>
                  <div className="relative h-2 bg-gray-200 rounded">
                    <div 
                      className="absolute h-full bg-purple-600 rounded"
                      style={{ 
                        width: `${Math.min(100, (result.metrics.profit_factor / 3) * 100)}%` 
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>0</span>
                    <span>1.5</span>
                    <span>3.0</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}