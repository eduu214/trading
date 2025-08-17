'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { 
  Clock, 
  TrendingUp,
  BarChart3,
  Activity,
  Info,
  Check,
  X
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface TimeframeConfig {
  value: string;
  label: string;
  description: string;
  recommended: boolean;
  category: 'intraday' | 'swing' | 'position';
}

const TIMEFRAMES: TimeframeConfig[] = [
  { value: '1m', label: '1 Minute', description: 'Ultra-short term scalping', recommended: false, category: 'intraday' },
  { value: '5m', label: '5 Minutes', description: 'Short-term day trading', recommended: false, category: 'intraday' },
  { value: '15m', label: '15 Minutes', description: 'Intraday momentum', recommended: false, category: 'intraday' },
  { value: '30m', label: '30 Minutes', description: 'Extended intraday', recommended: false, category: 'intraday' },
  { value: '1H', label: '1 Hour', description: 'Hourly trends', recommended: true, category: 'swing' },
  { value: '4H', label: '4 Hours', description: 'Short swing trading', recommended: true, category: 'swing' },
  { value: '1D', label: '1 Day', description: 'Daily analysis', recommended: true, category: 'position' },
  { value: '1W', label: '1 Week', description: 'Weekly trends', recommended: false, category: 'position' },
  { value: '1M', label: '1 Month', description: 'Long-term positioning', recommended: false, category: 'position' }
];

interface TimeframeSelectorProps {
  selectedTimeframes: string[];
  onTimeframesChange: (timeframes: string[], weights?: Record<string, number>) => void;
  maxTimeframes?: number;
  enableWeights?: boolean;
}

export function TimeframeSelector({
  selectedTimeframes,
  onTimeframesChange,
  maxTimeframes = 5,
  enableWeights = true
}: TimeframeSelectorProps) {
  const [weights, setWeights] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    selectedTimeframes.forEach(tf => {
      initial[tf] = 100 / selectedTimeframes.length;
    });
    return initial;
  });

  const [activeCategory, setActiveCategory] = useState<'all' | 'intraday' | 'swing' | 'position'>('all');

  const toggleTimeframe = (timeframe: string) => {
    let newTimeframes: string[];
    
    if (selectedTimeframes.includes(timeframe)) {
      newTimeframes = selectedTimeframes.filter(tf => tf !== timeframe);
      const newWeights = { ...weights };
      delete newWeights[timeframe];
      
      // Redistribute weights
      if (newTimeframes.length > 0) {
        const totalWeight = 100;
        newTimeframes.forEach(tf => {
          newWeights[tf] = totalWeight / newTimeframes.length;
        });
      }
      
      setWeights(newWeights);
      onTimeframesChange(newTimeframes, newWeights);
    } else if (selectedTimeframes.length < maxTimeframes) {
      newTimeframes = [...selectedTimeframes, timeframe];
      
      // Redistribute weights
      const totalWeight = 100;
      const newWeights: Record<string, number> = {};
      newTimeframes.forEach(tf => {
        newWeights[tf] = totalWeight / newTimeframes.length;
      });
      
      setWeights(newWeights);
      onTimeframesChange(newTimeframes, newWeights);
    }
  };

  const updateWeight = (timeframe: string, value: number) => {
    const newWeights = { ...weights };
    newWeights[timeframe] = value;
    
    // Normalize other weights
    const totalOthers = Object.keys(newWeights)
      .filter(tf => tf !== timeframe)
      .reduce((sum, tf) => sum + newWeights[tf], 0);
    
    const remaining = 100 - value;
    if (totalOthers > 0) {
      Object.keys(newWeights).forEach(tf => {
        if (tf !== timeframe) {
          newWeights[tf] = (newWeights[tf] / totalOthers) * remaining;
        }
      });
    }
    
    setWeights(newWeights);
    onTimeframesChange(selectedTimeframes, newWeights);
  };

  const getFilteredTimeframes = () => {
    if (activeCategory === 'all') return TIMEFRAMES;
    return TIMEFRAMES.filter(tf => tf.category === activeCategory);
  };

  const selectPreset = (preset: 'scalping' | 'day' | 'swing' | 'position') => {
    let presetTimeframes: string[] = [];
    let presetWeights: Record<string, number> = {};
    
    switch (preset) {
      case 'scalping':
        presetTimeframes = ['1m', '5m', '15m'];
        presetWeights = { '1m': 50, '5m': 30, '15m': 20 };
        break;
      case 'day':
        presetTimeframes = ['5m', '15m', '1H'];
        presetWeights = { '5m': 20, '15m': 40, '1H': 40 };
        break;
      case 'swing':
        presetTimeframes = ['1H', '4H', '1D'];
        presetWeights = { '1H': 25, '4H': 35, '1D': 40 };
        break;
      case 'position':
        presetTimeframes = ['1D', '1W'];
        presetWeights = { '1D': 60, '1W': 40 };
        break;
    }
    
    setWeights(presetWeights);
    onTimeframesChange(presetTimeframes, presetWeights);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Timeframe Selection
            </CardTitle>
            <CardDescription>
              Select up to {maxTimeframes} timeframes for multi-timeframe analysis
            </CardDescription>
          </div>
          <Badge variant="outline">
            {selectedTimeframes.length}/{maxTimeframes} selected
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Quick Presets */}
        <div>
          <Label className="text-sm font-medium mb-3 block">Quick Presets</Label>
          <div className="grid grid-cols-4 gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => selectPreset('scalping')}
              className="text-xs"
            >
              Scalping
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => selectPreset('day')}
              className="text-xs"
            >
              Day Trading
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => selectPreset('swing')}
              className="text-xs"
            >
              Swing Trading
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => selectPreset('position')}
              className="text-xs"
            >
              Position
            </Button>
          </div>
        </div>

        {/* Category Tabs */}
        <Tabs value={activeCategory} onValueChange={(v) => setActiveCategory(v as any)}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="intraday">Intraday</TabsTrigger>
            <TabsTrigger value="swing">Swing</TabsTrigger>
            <TabsTrigger value="position">Position</TabsTrigger>
          </TabsList>
          
          <TabsContent value={activeCategory} className="mt-4">
            <div className="grid grid-cols-3 gap-2">
              {getFilteredTimeframes().map((tf) => {
                const isSelected = selectedTimeframes.includes(tf.value);
                const isDisabled = !isSelected && selectedTimeframes.length >= maxTimeframes;
                
                return (
                  <TooltipProvider key={tf.value}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant={isSelected ? "default" : "outline"}
                          size="sm"
                          disabled={isDisabled}
                          onClick={() => toggleTimeframe(tf.value)}
                          className="relative"
                        >
                          {tf.label}
                          {tf.recommended && (
                            <Badge 
                              variant="secondary" 
                              className="absolute -top-1 -right-1 h-4 px-1 text-[10px]"
                            >
                              Rec
                            </Badge>
                          )}
                          {isSelected && (
                            <Check className="ml-1 h-3 w-3" />
                          )}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="font-medium">{tf.label}</p>
                        <p className="text-xs text-muted-foreground">{tf.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                );
              })}
            </div>
          </TabsContent>
        </Tabs>

        {/* Weight Configuration */}
        {enableWeights && selectedTimeframes.length > 1 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Timeframe Weights</Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-4 w-4 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p>Adjust the importance of each timeframe in the final optimization. 
                       Higher weights give more influence to that timeframe's results.</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
            
            <div className="space-y-3">
              {selectedTimeframes.map(tf => {
                const config = TIMEFRAMES.find(t => t.value === tf);
                const weight = weights[tf] || 0;
                
                return (
                  <div key={tf} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{config?.label}</span>
                      <span className="text-muted-foreground">{Math.round(weight)}%</span>
                    </div>
                    <Slider
                      value={[weight]}
                      onValueChange={([v]) => updateWeight(tf, v)}
                      max={100}
                      min={0}
                      step={5}
                      className="w-full"
                    />
                  </div>
                );
              })}
            </div>
            
            {/* Weight Distribution Indicator */}
            <div className="flex h-2 overflow-hidden rounded-full bg-gray-100">
              {selectedTimeframes.map((tf, index) => {
                const weight = weights[tf] || 0;
                const colors = [
                  'bg-blue-500',
                  'bg-green-500',
                  'bg-yellow-500',
                  'bg-purple-500',
                  'bg-pink-500'
                ];
                
                return (
                  <div
                    key={tf}
                    className={`${colors[index % colors.length]} transition-all`}
                    style={{ width: `${weight}%` }}
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* Selected Summary */}
        {selectedTimeframes.length > 0 && (
          <div className="rounded-lg bg-muted/50 p-4">
            <div className="flex items-start gap-3">
              <BarChart3 className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="flex-1 space-y-2">
                <p className="text-sm font-medium">Analysis Configuration</p>
                <p className="text-xs text-muted-foreground">
                  The optimizer will analyze your strategy across {selectedTimeframes.length} timeframe{selectedTimeframes.length > 1 ? 's' : ''}: {' '}
                  {selectedTimeframes.map(tf => TIMEFRAMES.find(t => t.value === tf)?.label).join(', ')}.
                  {enableWeights && selectedTimeframes.length > 1 && ' Weights will be applied to determine the optimal complexity level.'}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}