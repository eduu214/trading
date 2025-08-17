'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { 
  Shield,
  Plus,
  Trash2,
  AlertTriangle,
  CheckCircle,
  Info,
  TrendingUp,
  TrendingDown,
  Target,
  Zap,
  Lock,
  Unlock,
  Save,
  Download
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert';

interface Constraint {
  id: string;
  type: string;
  operator: string;
  value: number;
  timeframe: string;
  isHard: boolean;
  weight: number;
  isActive: boolean;
}

interface ConstraintPreset {
  id: string;
  name: string;
  description: string;
  constraints: Omit<Constraint, 'id'>[];
  isSystem: boolean;
}

const CONSTRAINT_TYPES = [
  { value: 'MIN_SHARPE', label: 'Minimum Sharpe Ratio', icon: TrendingUp, unit: '', min: 0, max: 3, step: 0.1 },
  { value: 'MAX_DRAWDOWN', label: 'Maximum Drawdown', icon: TrendingDown, unit: '%', min: -50, max: 0, step: 1 },
  { value: 'MAX_VOLATILITY', label: 'Maximum Volatility', icon: AlertTriangle, unit: '%', min: 0, max: 100, step: 1 },
  { value: 'MIN_WIN_RATE', label: 'Minimum Win Rate', icon: CheckCircle, unit: '%', min: 0, max: 100, step: 1 },
  { value: 'MIN_PROFIT_FACTOR', label: 'Minimum Profit Factor', icon: Target, unit: '', min: 1, max: 5, step: 0.1 },
  { value: 'TARGET_RETURN', label: 'Target Annual Return', icon: TrendingUp, unit: '%', min: 0, max: 200, step: 5 },
  { value: 'MAX_COMPLEXITY', label: 'Maximum Complexity', icon: Zap, unit: '', min: 1, max: 10, step: 1 },
  { value: 'MIN_COMPLEXITY', label: 'Minimum Complexity', icon: Zap, unit: '', min: 1, max: 10, step: 1 }
];

const OPERATORS = {
  MIN_SHARPE: ['>='],
  MAX_DRAWDOWN: ['>='],  // Note: drawdown is negative
  MAX_VOLATILITY: ['<='],
  MIN_WIN_RATE: ['>='],
  MIN_PROFIT_FACTOR: ['>='],
  TARGET_RETURN: ['>=', '=='],
  MAX_COMPLEXITY: ['<='],
  MIN_COMPLEXITY: ['>=']
};

const SYSTEM_PRESETS: ConstraintPreset[] = [
  {
    id: 'conservative',
    name: 'Conservative',
    description: 'Low risk, stable returns',
    isSystem: true,
    constraints: [
      { type: 'MAX_DRAWDOWN', operator: '>=', value: -10, timeframe: '1D', isHard: true, weight: 1, isActive: true },
      { type: 'MAX_VOLATILITY', operator: '<=', value: 15, timeframe: '1D', isHard: false, weight: 0.8, isActive: true },
      { type: 'MIN_SHARPE', operator: '>=', value: 1.0, timeframe: '1D', isHard: false, weight: 1, isActive: true }
    ]
  },
  {
    id: 'balanced',
    name: 'Balanced',
    description: 'Moderate risk and return',
    isSystem: true,
    constraints: [
      { type: 'MAX_DRAWDOWN', operator: '>=', value: -15, timeframe: '1D', isHard: true, weight: 1, isActive: true },
      { type: 'MIN_SHARPE', operator: '>=', value: 1.2, timeframe: '1D', isHard: false, weight: 1, isActive: true }
    ]
  },
  {
    id: 'aggressive',
    name: 'Aggressive',
    description: 'Higher risk for maximum returns',
    isSystem: true,
    constraints: [
      { type: 'MAX_DRAWDOWN', operator: '>=', value: -25, timeframe: '1D', isHard: false, weight: 0.5, isActive: true },
      { type: 'MIN_SHARPE', operator: '>=', value: 1.5, timeframe: '1D', isHard: true, weight: 1, isActive: true },
      { type: 'TARGET_RETURN', operator: '>=', value: 20, timeframe: '1D', isHard: false, weight: 0.7, isActive: true }
    ]
  }
];

interface ConstraintBuilderProps {
  strategyId: string;
  onConstraintsChange?: (constraints: Constraint[]) => void;
  initialConstraints?: Constraint[];
}

export function ConstraintBuilder({
  strategyId,
  onConstraintsChange,
  initialConstraints = []
}: ConstraintBuilderProps) {
  const [constraints, setConstraints] = useState<Constraint[]>(initialConstraints);
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const addConstraint = () => {
    const newConstraint: Constraint = {
      id: `constraint-${Date.now()}`,
      type: 'MIN_SHARPE',
      operator: '>=',
      value: 1.0,
      timeframe: '1D',
      isHard: false,
      weight: 1.0,
      isActive: true
    };
    
    const updated = [...constraints, newConstraint];
    setConstraints(updated);
    onConstraintsChange?.(updated);
  };

  const updateConstraint = (id: string, updates: Partial<Constraint>) => {
    const updated = constraints.map(c => 
      c.id === id ? { ...c, ...updates } : c
    );
    setConstraints(updated);
    onConstraintsChange?.(updated);
  };

  const removeConstraint = (id: string) => {
    const updated = constraints.filter(c => c.id !== id);
    setConstraints(updated);
    onConstraintsChange?.(updated);
  };

  const applyPreset = (presetId: string) => {
    const preset = SYSTEM_PRESETS.find(p => p.id === presetId);
    if (!preset) return;
    
    const newConstraints = preset.constraints.map((c, index) => ({
      ...c,
      id: `constraint-${Date.now()}-${index}`
    }));
    
    setConstraints(newConstraints);
    setSelectedPreset(presetId);
    onConstraintsChange?.(newConstraints);
  };

  const toggleConstraintActive = (id: string) => {
    updateConstraint(id, { 
      isActive: !constraints.find(c => c.id === id)?.isActive 
    });
  };

  const getConstraintIcon = (type: string) => {
    const config = CONSTRAINT_TYPES.find(ct => ct.value === type);
    return config?.icon || Shield;
  };

  const getConstraintConfig = (type: string) => {
    return CONSTRAINT_TYPES.find(ct => ct.value === type);
  };

  const validateConstraints = () => {
    const issues: string[] = [];
    
    // Check for conflicting constraints
    const complexityConstraints = constraints.filter(c => 
      c.isActive && (c.type === 'MAX_COMPLEXITY' || c.type === 'MIN_COMPLEXITY')
    );
    
    if (complexityConstraints.length >= 2) {
      const max = complexityConstraints.find(c => c.type === 'MAX_COMPLEXITY')?.value;
      const min = complexityConstraints.find(c => c.type === 'MIN_COMPLEXITY')?.value;
      
      if (max !== undefined && min !== undefined && max < min) {
        issues.push('Minimum complexity cannot be greater than maximum complexity');
      }
    }
    
    // Check for too many hard constraints
    const hardConstraints = constraints.filter(c => c.isActive && c.isHard);
    if (hardConstraints.length > 5) {
      issues.push('Too many hard constraints may make optimization impossible');
    }
    
    return issues;
  };

  const validationIssues = validateConstraints();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Complexity Constraints
            </CardTitle>
            <CardDescription>
              Define rules to guide the optimization process
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {constraints.filter(c => c.isActive).length} active
            </Badge>
            <Badge variant={constraints.some(c => c.isHard) ? "destructive" : "secondary"}>
              {constraints.filter(c => c.isHard).length} hard
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Preset Selection */}
        <div className="space-y-3">
          <Label>Quick Presets</Label>
          <div className="grid grid-cols-3 gap-2">
            {SYSTEM_PRESETS.map(preset => (
              <Button
                key={preset.id}
                variant={selectedPreset === preset.id ? "default" : "outline"}
                size="sm"
                onClick={() => applyPreset(preset.id)}
                className="flex flex-col items-start p-3 h-auto"
              >
                <span className="font-medium">{preset.name}</span>
                <span className="text-xs text-muted-foreground">{preset.description}</span>
              </Button>
            ))}
          </div>
        </div>

        {/* Validation Issues */}
        {validationIssues.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Constraint Issues</AlertTitle>
            <AlertDescription>
              <ul className="list-disc list-inside mt-2">
                {validationIssues.map((issue, index) => (
                  <li key={index} className="text-sm">{issue}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Constraints List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Active Constraints</Label>
            <Button
              variant="outline"
              size="sm"
              onClick={addConstraint}
              className="h-8"
            >
              <Plus className="h-3 w-3 mr-1" />
              Add Constraint
            </Button>
          </div>

          {constraints.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Shield className="h-12 w-12 mx-auto mb-3 opacity-20" />
              <p className="text-sm">No constraints defined</p>
              <p className="text-xs mt-1">Add constraints or select a preset to get started</p>
            </div>
          ) : (
            <Accordion type="single" collapsible className="space-y-2">
              {constraints.map((constraint, index) => {
                const Icon = getConstraintIcon(constraint.type);
                const config = getConstraintConfig(constraint.type);
                
                return (
                  <AccordionItem 
                    key={constraint.id} 
                    value={constraint.id}
                    className={`border rounded-lg ${!constraint.isActive ? 'opacity-50' : ''}`}
                  >
                    <AccordionTrigger className="px-4 py-3 hover:no-underline">
                      <div className="flex items-center justify-between w-full pr-4">
                        <div className="flex items-center gap-3">
                          <Icon className="h-4 w-4" />
                          <span className="font-medium">
                            {config?.label}
                          </span>
                          <Badge variant={constraint.isHard ? "destructive" : "secondary"} className="text-xs">
                            {constraint.isHard ? 'Hard' : 'Soft'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">
                            {constraint.operator} {constraint.value}{config?.unit}
                          </span>
                          <Switch
                            checked={constraint.isActive}
                            onCheckedChange={() => toggleConstraintActive(constraint.id)}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="px-4 pb-4">
                      <div className="grid grid-cols-2 gap-4 mt-4">
                        {/* Constraint Type */}
                        <div className="space-y-2">
                          <Label className="text-xs">Type</Label>
                          <Select
                            value={constraint.type}
                            onValueChange={(value) => updateConstraint(constraint.id, { type: value })}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {CONSTRAINT_TYPES.map(type => (
                                <SelectItem key={type.value} value={type.value}>
                                  {type.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Operator */}
                        <div className="space-y-2">
                          <Label className="text-xs">Operator</Label>
                          <Select
                            value={constraint.operator}
                            onValueChange={(value) => updateConstraint(constraint.id, { operator: value })}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {OPERATORS[constraint.type as keyof typeof OPERATORS]?.map(op => (
                                <SelectItem key={op} value={op}>
                                  {op}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Value */}
                        <div className="space-y-2">
                          <Label className="text-xs">
                            Value {config?.unit && `(${config.unit})`}
                          </Label>
                          <div className="flex items-center gap-2">
                            <Slider
                              value={[constraint.value]}
                              onValueChange={([v]) => updateConstraint(constraint.id, { value: v })}
                              min={config?.min || 0}
                              max={config?.max || 100}
                              step={config?.step || 1}
                              className="flex-1"
                            />
                            <Input
                              type="number"
                              value={constraint.value}
                              onChange={(e) => updateConstraint(constraint.id, { value: parseFloat(e.target.value) })}
                              className="w-20 h-9"
                              min={config?.min}
                              max={config?.max}
                              step={config?.step}
                            />
                          </div>
                        </div>

                        {/* Timeframe */}
                        <div className="space-y-2">
                          <Label className="text-xs">Timeframe</Label>
                          <Select
                            value={constraint.timeframe}
                            onValueChange={(value) => updateConstraint(constraint.id, { timeframe: value })}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="1m">1 Minute</SelectItem>
                              <SelectItem value="5m">5 Minutes</SelectItem>
                              <SelectItem value="15m">15 Minutes</SelectItem>
                              <SelectItem value="30m">30 Minutes</SelectItem>
                              <SelectItem value="1H">1 Hour</SelectItem>
                              <SelectItem value="4H">4 Hours</SelectItem>
                              <SelectItem value="1D">1 Day</SelectItem>
                              <SelectItem value="1W">1 Week</SelectItem>
                              <SelectItem value="1M">1 Month</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Constraint Type Toggle */}
                        <div className="space-y-2">
                          <Label className="text-xs">Constraint Type</Label>
                          <div className="flex items-center gap-2">
                            <Button
                              variant={constraint.isHard ? "destructive" : "outline"}
                              size="sm"
                              onClick={() => updateConstraint(constraint.id, { isHard: true })}
                              className="flex-1"
                            >
                              <Lock className="h-3 w-3 mr-1" />
                              Hard
                            </Button>
                            <Button
                              variant={!constraint.isHard ? "default" : "outline"}
                              size="sm"
                              onClick={() => updateConstraint(constraint.id, { isHard: false })}
                              className="flex-1"
                            >
                              <Unlock className="h-3 w-3 mr-1" />
                              Soft
                            </Button>
                          </div>
                        </div>

                        {/* Weight (for soft constraints) */}
                        {!constraint.isHard && (
                          <div className="space-y-2">
                            <Label className="text-xs">
                              Weight
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Info className="h-3 w-3 ml-1 inline" />
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p className="max-w-xs text-xs">
                                      Higher weights make this constraint more important during optimization
                                    </p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            </Label>
                            <div className="flex items-center gap-2">
                              <Slider
                                value={[constraint.weight]}
                                onValueChange={([v]) => updateConstraint(constraint.id, { weight: v })}
                                min={0.1}
                                max={2}
                                step={0.1}
                                className="flex-1"
                              />
                              <span className="text-sm w-12 text-right">{constraint.weight.toFixed(1)}</span>
                            </div>
                          </div>
                        )}

                        {/* Delete Button */}
                        <div className="col-span-2 flex justify-end mt-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeConstraint(constraint.id)}
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 className="h-3 w-3 mr-1" />
                            Remove
                          </Button>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                );
              })}
            </Accordion>
          )}
        </div>

        {/* Info Section */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Understanding Constraints</AlertTitle>
          <AlertDescription className="mt-2 space-y-2">
            <p className="text-sm">
              <strong>Hard constraints</strong> must be satisfied for a complexity level to be considered valid.
            </p>
            <p className="text-sm">
              <strong>Soft constraints</strong> are preferences that guide the optimization but don't eliminate options.
            </p>
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}