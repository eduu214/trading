'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  BarChart,
  Bar,
  Line,
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart
} from 'recharts';
import { 
  TrendingUp,
  Shield,
  BarChart3,
  Info,
  Download
} from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface ComplexityLevel {
  level: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
  winRate: number;
  profitFactor: number;
  annualReturn: number;
  score: number;
  constraintsSatisfied: number;
  totalConstraints: number;
}

interface TimeframeResult {
  timeframe: string;
  optimalComplexity: number;
  score: number;
  metrics: {
    sharpeRatio: number;
    maxDrawdown: number;
    volatility: number;
    winRate: number;
  };
}

interface ComplexityComparisonProps {
  strategyId: string;
  complexityLevels?: ComplexityLevel[];
  timeframeResults?: TimeframeResult[];
  recommendedLevel?: number;
  currentLevel?: number;
}

export function ComplexityComparisonView({
  strategyId,
  complexityLevels = generateMockData(),
  timeframeResults = generateMockTimeframes(),
  recommendedLevel = 5,
  currentLevel = 3
}: ComplexityComparisonProps) {
  const [selectedView, setSelectedView] = useState<'metrics' | 'timeframes'>('metrics');

  const getMetricColor = (value: number, metric: string) => {
    switch (metric) {
      case 'sharpe':
        return value >= 1.5 ? 'text-green-600' : value >= 1 ? 'text-yellow-600' : 'text-red-600';
      case 'drawdown':
        return value >= -10 ? 'text-green-600' : value >= -20 ? 'text-yellow-600' : 'text-red-600';
      case 'winRate':
        return value >= 60 ? 'text-green-600' : value >= 50 ? 'text-yellow-600' : 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatDrawdown = (value: number) => `${value.toFixed(1)}%`;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Complexity Analysis Results
            </CardTitle>
            <CardDescription>
              Compare performance metrics across different complexity levels
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">Current: Level {currentLevel}</Badge>
            <Badge variant="default">Recommended: Level {recommendedLevel}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs value={selectedView} onValueChange={(v) => setSelectedView(v as any)}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="metrics">Metrics Comparison</TabsTrigger>
            <TabsTrigger value="timeframes">Multi-Timeframe</TabsTrigger>
          </TabsList>

          {/* Metrics Comparison View */}
          <TabsContent value="metrics" className="space-y-6">
            {/* Key Metrics Chart */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium">Risk-Adjusted Returns by Complexity</h3>
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={complexityLevels}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="level" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <RechartsTooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="sharpeRatio" fill="#3b82f6" name="Sharpe Ratio" />
                  <Line yAxisId="right" type="monotone" dataKey="annualReturn" stroke="#10b981" name="Annual Return %" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Detailed Metrics Table */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium">Detailed Metrics by Complexity Level</h3>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Level</TableHead>
                      <TableHead>Sharpe</TableHead>
                      <TableHead>Max DD</TableHead>
                      <TableHead>Volatility</TableHead>
                      <TableHead>Win Rate</TableHead>
                      <TableHead>Annual Return</TableHead>
                      <TableHead>Score</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {complexityLevels.map((level) => (
                      <TableRow 
                        key={level.level}
                        className={
                          level.level === recommendedLevel 
                            ? 'bg-primary/5 font-medium' 
                            : level.level === currentLevel
                            ? 'bg-secondary/5'
                            : ''
                        }
                      >
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {level.level}
                            {level.level === recommendedLevel && (
                              <Badge variant="default" className="text-xs">Optimal</Badge>
                            )}
                            {level.level === currentLevel && (
                              <Badge variant="outline" className="text-xs">Current</Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className={getMetricColor(level.sharpeRatio, 'sharpe')}>
                          {level.sharpeRatio.toFixed(2)}
                        </TableCell>
                        <TableCell className={getMetricColor(level.maxDrawdown, 'drawdown')}>
                          {formatDrawdown(level.maxDrawdown)}
                        </TableCell>
                        <TableCell>{formatPercentage(level.volatility / 100)}</TableCell>
                        <TableCell className={getMetricColor(level.winRate, 'winRate')}>
                          {level.winRate.toFixed(1)}%
                        </TableCell>
                        <TableCell>{level.annualReturn.toFixed(1)}%</TableCell>
                        <TableCell>{level.score.toFixed(0)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          </TabsContent>

          {/* Multi-Timeframe View */}
          <TabsContent value="timeframes" className="space-y-6">
            <div className="space-y-3">
              <h3 className="text-sm font-medium">Optimal Complexity by Timeframe</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={timeframeResults}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timeframe" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="optimalComplexity" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Timeframe Metrics Table */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium">Performance Metrics by Timeframe</h3>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timeframe</TableHead>
                      <TableHead>Optimal Level</TableHead>
                      <TableHead>Score</TableHead>
                      <TableHead>Sharpe Ratio</TableHead>
                      <TableHead>Max Drawdown</TableHead>
                      <TableHead>Win Rate</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {timeframeResults.map((result) => (
                      <TableRow key={result.timeframe}>
                        <TableCell className="font-medium">{result.timeframe}</TableCell>
                        <TableCell>
                          <Badge variant="outline">Level {result.optimalComplexity}</Badge>
                        </TableCell>
                        <TableCell>{result.score.toFixed(0)}</TableCell>
                        <TableCell className={getMetricColor(result.metrics.sharpeRatio, 'sharpe')}>
                          {result.metrics.sharpeRatio.toFixed(2)}
                        </TableCell>
                        <TableCell className={getMetricColor(result.metrics.maxDrawdown, 'drawdown')}>
                          {formatDrawdown(result.metrics.maxDrawdown)}
                        </TableCell>
                        <TableCell className={getMetricColor(result.metrics.winRate, 'winRate')}>
                          {result.metrics.winRate.toFixed(1)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Recommendation Summary */}
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-600" />
                Improvement Potential
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Sharpe Ratio</span>
                  <span className="font-medium text-green-600">+34%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Annual Return</span>
                  <span className="font-medium text-green-600">+12%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Win Rate</span>
                  <span className="font-medium text-green-600">+8%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Shield className="h-4 w-4 text-blue-600" />
                Risk Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Max Drawdown</span>
                  <span className="font-medium text-yellow-600">-2%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Volatility</span>
                  <span className="font-medium text-green-600">-15%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Risk Score</span>
                  <span className="font-medium text-green-600">Improved</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              Keep Current (Level {currentLevel})
            </Button>
            <Button size="sm">
              Apply Recommended (Level {recommendedLevel})
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Helper function to generate mock data
function generateMockData(): ComplexityLevel[] {
  return Array.from({ length: 10 }, (_, i) => {
    const level = i + 1;
    const baseScore = 40 + Math.random() * 30;
    return {
      level,
      sharpeRatio: 0.5 + (level * 0.15) + (Math.random() * 0.3) - (level > 7 ? (level - 7) * 0.2 : 0),
      maxDrawdown: -5 - (level * 1.5) - Math.random() * 5,
      volatility: 10 + (level * 2) + Math.random() * 5,
      winRate: 45 + (level * 2) + Math.random() * 10,
      profitFactor: 1.0 + (level * 0.15) + Math.random() * 0.3,
      annualReturn: 5 + (level * 3) + Math.random() * 10 - (level > 7 ? (level - 7) * 5 : 0),
      score: baseScore + (level <= 5 ? level * 5 : 25 - (level - 5) * 3),
      constraintsSatisfied: Math.floor(Math.random() * 3) + (level === 5 ? 5 : 3),
      totalConstraints: 5
    };
  });
}

function generateMockTimeframes(): TimeframeResult[] {
  return [
    { timeframe: '1m', optimalComplexity: 2, score: 72, metrics: { sharpeRatio: 1.1, maxDrawdown: -8, volatility: 0.12, winRate: 58 } },
    { timeframe: '5m', optimalComplexity: 3, score: 75, metrics: { sharpeRatio: 1.2, maxDrawdown: -10, volatility: 0.14, winRate: 56 } },
    { timeframe: '15m', optimalComplexity: 4, score: 78, metrics: { sharpeRatio: 1.3, maxDrawdown: -12, volatility: 0.16, winRate: 54 } },
    { timeframe: '1H', optimalComplexity: 5, score: 82, metrics: { sharpeRatio: 1.5, maxDrawdown: -14, volatility: 0.18, winRate: 52 } },
    { timeframe: '4H', optimalComplexity: 6, score: 80, metrics: { sharpeRatio: 1.4, maxDrawdown: -16, volatility: 0.20, winRate: 51 } },
    { timeframe: '1D', optimalComplexity: 5, score: 85, metrics: { sharpeRatio: 1.6, maxDrawdown: -15, volatility: 0.19, winRate: 53 } }
  ];
}