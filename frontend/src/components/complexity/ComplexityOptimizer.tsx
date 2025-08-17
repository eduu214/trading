'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle2,
  Clock,
  BarChart3,
  Zap,
  Shield
} from 'lucide-react';
import { ComplexityChart } from './ComplexityChart';
import { ComplexityComparison } from './ComplexityComparison';
import { OptimizationProgress } from './OptimizationProgress';

interface Strategy {
  id: string;
  name: string;
  complexity_level: number;
  optimal_complexity?: number;
  sharpe_ratio: number;
  max_drawdown: number;
  last_optimized?: string;
}

interface OptimizationResult {
  optimal_complexity_level: number;
  current_complexity_level: number;
  recommendation: string;
  confidence: number;
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
  };
  performance_improvement: {
    sharpe_improvement: number;
    return_improvement: number;
    drawdown_improvement: number;
  };
}

export function ComplexityOptimizer({ strategyId }: { strategyId: string }) {
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  // Optimization parameters
  const [timeframe, setTimeframe] = useState('1D');
  const [lookbackDays, setLookbackDays] = useState(252);
  const [riskPreference, setRiskPreference] = useState('balanced');

  useEffect(() => {
    fetchStrategyDetails();
  }, [strategyId]);

  const fetchStrategyDetails = async () => {
    try {
      const response = await fetch(`/api/v1/strategies/${strategyId}`);
      if (response.ok) {
        const data = await response.json();
        setStrategy(data);
      }
    } catch (err) {
      console.error('Failed to fetch strategy:', err);
    }
  };

  const startOptimization = async () => {
    setIsOptimizing(true);
    setError(null);
    setProgress(0);

    try {
      const response = await fetch('/api/v1/complexity/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategy_id: strategyId,
          timeframe,
          lookback_days: lookbackDays,
          risk_preference: riskPreference
        })
      });

      if (response.ok) {
        const data = await response.json();
        setTaskId(data.task_id);
        
        // Start polling for results
        pollOptimizationStatus(data.task_id, data.estimated_time_seconds);
      } else {
        throw new Error('Failed to start optimization');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Optimization failed');
      setIsOptimizing(false);
    }
  };

  const pollOptimizationStatus = async (taskId: string, estimatedTime: number) => {
    const startTime = Date.now();
    const pollInterval = 2000; // 2 seconds
    
    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/complexity/optimize/${taskId}`);
        
        if (response.status === 200) {
          const result = await response.json();
          setOptimizationResult(result);
          setIsOptimizing(false);
          setProgress(100);
          
          // Refresh strategy details
          fetchStrategyDetails();
        } else if (response.status === 202) {
          // Still processing
          const elapsed = Date.now() - startTime;
          const progressPercent = Math.min(95, (elapsed / (estimatedTime * 1000)) * 100);
          setProgress(progressPercent);
          
          // Continue polling
          setTimeout(poll, pollInterval);
        } else {
          throw new Error('Optimization failed');
        }
      } catch (err) {
        setError('Failed to get optimization status');
        setIsOptimizing(false);
      }
    };
    
    poll();
  };

  const applyOptimalComplexity = async () => {
    try {
      const response = await fetch(`/api/v1/complexity/apply/${strategyId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // Refresh strategy details
        fetchStrategyDetails();
        setError(null);
      } else {
        throw new Error('Failed to apply optimal complexity');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply changes');
    }
  };

  const getComplexityLabel = (level: number) => {
    const labels = [
      'Minimal', 'Very Low', 'Low', 'Moderate-Low', 'Moderate',
      'Moderate-High', 'High', 'Very High', 'Extreme', 'Maximum'
    ];
    return labels[level - 1] || 'Unknown';
  };

  const getComplexityColor = (level: number) => {
    if (level <= 3) return 'text-green-600 bg-green-50';
    if (level <= 5) return 'text-blue-600 bg-blue-50';
    if (level <= 7) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Complexity Optimizer</h2>
          <p className="text-muted-foreground">
            Optimize strategy complexity for best risk-adjusted returns
          </p>
        </div>
        {strategy && (
          <Badge className={getComplexityColor(strategy.complexity_level)}>
            Level {strategy.complexity_level} - {getComplexityLabel(strategy.complexity_level)}
          </Badge>
        )}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Optimization Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Optimization Settings
            </CardTitle>
            <CardDescription>
              Configure optimization parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Timeframe</label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1m">1 Minute</SelectItem>
                  <SelectItem value="5m">5 Minutes</SelectItem>
                  <SelectItem value="1H">1 Hour</SelectItem>
                  <SelectItem value="1D">1 Day</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">
                Lookback Period: {lookbackDays} days
              </label>
              <Slider
                value={[lookbackDays]}
                onValueChange={([value]) => setLookbackDays(value)}
                min={30}
                max={730}
                step={30}
                className="mt-2"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Risk Preference</label>
              <Select value={riskPreference} onValueChange={setRiskPreference}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="conservative">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      Conservative
                    </div>
                  </SelectItem>
                  <SelectItem value="balanced">
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      Balanced
                    </div>
                  </SelectItem>
                  <SelectItem value="aggressive">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      Aggressive
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button 
              onClick={startOptimization} 
              disabled={isOptimizing}
              className="w-full"
            >
              {isOptimizing ? (
                <>
                  <Clock className="mr-2 h-4 w-4 animate-spin" />
                  Optimizing...
                </>
              ) : (
                <>
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Start Optimization
                </>
              )}
            </Button>

            {isOptimizing && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Progress</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Current Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Current Performance
            </CardTitle>
            <CardDescription>
              Strategy metrics at current complexity
            </CardDescription>
          </CardHeader>
          <CardContent>
            {strategy && (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Complexity Level</span>
                  <span className="font-medium">{strategy.complexity_level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Sharpe Ratio</span>
                  <span className="font-medium">{strategy.sharpe_ratio.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Max Drawdown</span>
                  <span className="font-medium">{(strategy.max_drawdown * 100).toFixed(1)}%</span>
                </div>
                {strategy.optimal_complexity && (
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Optimal Level</span>
                    <Badge variant="outline" className="text-green-600">
                      {strategy.optimal_complexity}
                    </Badge>
                  </div>
                )}
                {strategy.last_optimized && (
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Last Optimized</span>
                    <span className="text-sm">
                      {new Date(strategy.last_optimized).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Optimization Results */}
      {optimizationResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              Optimization Results
            </CardTitle>
            <CardDescription>
              Recommended complexity level and expected improvements
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="summary" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="metrics">Metrics</TabsTrigger>
                <TabsTrigger value="comparison">Comparison</TabsTrigger>
              </TabsList>
              
              <TabsContent value="summary" className="space-y-4">
                <Alert>
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertDescription>
                    {optimizationResult.recommendation}
                  </AlertDescription>
                </Alert>
                
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <h4 className="font-medium">Recommended Complexity</h4>
                    <div className="flex items-center gap-2">
                      <Badge className={getComplexityColor(optimizationResult.optimal_complexity_level)}>
                        Level {optimizationResult.optimal_complexity_level}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        {getComplexityLabel(optimizationResult.optimal_complexity_level)}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Confidence: {(optimizationResult.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="font-medium">Expected Improvements</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Sharpe Ratio</span>
                        <span className={optimizationResult.performance_improvement.sharpe_improvement > 0 ? 'text-green-600' : 'text-red-600'}>
                          {optimizationResult.performance_improvement.sharpe_improvement > 0 ? '+' : ''}
                          {optimizationResult.performance_improvement.sharpe_improvement.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Annual Return</span>
                        <span className={optimizationResult.performance_improvement.return_improvement > 0 ? 'text-green-600' : 'text-red-600'}>
                          {optimizationResult.performance_improvement.return_improvement > 0 ? '+' : ''}
                          {(optimizationResult.performance_improvement.return_improvement * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Max Drawdown</span>
                        <span className={optimizationResult.performance_improvement.drawdown_improvement > 0 ? 'text-green-600' : 'text-red-600'}>
                          {optimizationResult.performance_improvement.drawdown_improvement > 0 ? '+' : ''}
                          {(optimizationResult.performance_improvement.drawdown_improvement * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <Button 
                  onClick={applyOptimalComplexity}
                  className="w-full"
                  variant="default"
                >
                  Apply Optimal Complexity
                </Button>
              </TabsContent>
              
              <TabsContent value="metrics">
                <ComplexityChart result={optimizationResult} />
              </TabsContent>
              
              <TabsContent value="comparison">
                <ComplexityComparison strategyId={strategyId} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Progress Display */}
      {isOptimizing && taskId && (
        <OptimizationProgress taskId={taskId} />
      )}
    </div>
  );
}