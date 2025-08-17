'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  Activity,
  Zap,
  BarChart3,
  ArrowRight,
  AlertCircle
} from 'lucide-react';

interface Strategy {
  id: string;
  name: string;
  type: string;
  status: string;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  complexity_level?: number;
  optimal_complexity?: number;
  last_optimized?: string;
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const response = await fetch('/api/v1/strategies/');
      if (response.ok) {
        const data = await response.json();
        setStrategies(data);
      }
    } catch (err) {
      console.error('Failed to fetch strategies:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'live':
        return 'bg-green-100 text-green-800';
      case 'paper_trading':
        return 'bg-blue-100 text-blue-800';
      case 'backtesting':
        return 'bg-yellow-100 text-yellow-800';
      case 'discovered':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getComplexityColor = (level: number) => {
    if (level <= 3) return 'text-green-600';
    if (level <= 5) return 'text-blue-600';
    if (level <= 7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const needsOptimization = (strategy: Strategy) => {
    if (!strategy.last_optimized) return true;
    const daysSinceOptimization = Math.floor(
      (Date.now() - new Date(strategy.last_optimized).getTime()) / (1000 * 60 * 60 * 24)
    );
    return daysSinceOptimization > 30; // Needs optimization if > 30 days old
  };

  // Sample data if no strategies exist
  const sampleStrategies: Strategy[] = [
    {
      id: '123e4567-e89b-12d3-a456-426614174000',
      name: 'Test Complexity Strategy',
      type: 'momentum',
      status: 'DISCOVERED',
      total_return: 0.15,
      sharpe_ratio: 1.2,
      max_drawdown: -0.08,
      win_rate: 0.58,
      complexity_level: 5,
      optimal_complexity: undefined,
      last_optimized: undefined
    }
  ];

  const displayStrategies = strategies.length > 0 ? strategies : sampleStrategies;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trading Strategies</h1>
        <p className="text-muted-foreground">
          Manage and optimize your trading strategies
        </p>
      </div>

      {/* Strategies Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {displayStrategies.map((strategy) => (
          <Card key={strategy.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{strategy.name}</CardTitle>
                  <CardDescription className="mt-1">
                    {strategy.type.charAt(0).toUpperCase() + strategy.type.slice(1)} Strategy
                  </CardDescription>
                </div>
                <Badge className={getStatusColor(strategy.status)}>
                  {strategy.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Performance Metrics */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-muted-foreground">Return</p>
                  <p className="font-medium flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    {(strategy.total_return * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Sharpe</p>
                  <p className="font-medium">{strategy.sharpe_ratio.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Drawdown</p>
                  <p className="font-medium">{(strategy.max_drawdown * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Win Rate</p>
                  <p className="font-medium">{(strategy.win_rate * 100).toFixed(0)}%</p>
                </div>
              </div>

              {/* Complexity Info */}
              <div className="pt-3 border-t">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Complexity</span>
                  <div className="flex items-center gap-2">
                    <span className={`font-medium ${getComplexityColor(strategy.complexity_level || 5)}`}>
                      Level {strategy.complexity_level || 5}
                    </span>
                    {strategy.optimal_complexity && strategy.optimal_complexity !== strategy.complexity_level && (
                      <Badge variant="outline" className="text-xs">
                        Optimal: {strategy.optimal_complexity}
                      </Badge>
                    )}
                  </div>
                </div>
                
                {needsOptimization(strategy) && (
                  <div className="flex items-center gap-1 text-xs text-yellow-600">
                    <AlertCircle className="h-3 w-3" />
                    <span>Optimization recommended</span>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-3">
                <Link href={`/strategies/${strategy.id}`} className="flex-1">
                  <Button variant="outline" className="w-full">
                    <BarChart3 className="mr-2 h-4 w-4" />
                    View Details
                  </Button>
                </Link>
                <Link href={`/strategies/${strategy.id}/optimize`} className="flex-1">
                  <Button variant="default" className="w-full">
                    <Zap className="mr-2 h-4 w-4" />
                    Optimize
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {!loading && strategies.length === 0 && (
        <Card className="p-12 text-center">
          <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No Strategies Yet</h3>
          <p className="text-muted-foreground mb-4">
            Run the scanner to discover new trading strategies
          </p>
          <Link href="/scanner">
            <Button>
              <ArrowRight className="mr-2 h-4 w-4" />
              Go to Scanner
            </Button>
          </Link>
        </Card>
      )}
    </div>
  );
}