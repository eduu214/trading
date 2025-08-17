'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Clock, 
  Activity, 
  CheckCircle, 
  XCircle,
  AlertCircle,
  Cpu,
  Database,
  TrendingUp,
  BarChart2
} from 'lucide-react';

interface ProgressStep {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  duration?: number;
  icon: React.ElementType;
}

export function OptimizationProgress({ taskId }: { taskId: string }) {
  const [steps, setSteps] = useState<ProgressStep[]>([
    { name: 'Fetching Market Data', status: 'pending', icon: Database },
    { name: 'Testing Complexity Levels', status: 'pending', icon: Cpu },
    { name: 'Calculating Risk Metrics', status: 'pending', icon: Activity },
    { name: 'Analyzing Performance', status: 'pending', icon: BarChart2 },
    { name: 'Optimizing Parameters', status: 'pending', icon: TrendingUp },
    { name: 'Generating Recommendations', status: 'pending', icon: CheckCircle }
  ]);
  
  const [currentStep, setCurrentStep] = useState(0);
  const [overallProgress, setOverallProgress] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState<number>(30);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    // Simulate progress through steps
    const interval = setInterval(() => {
      setElapsedTime(prev => prev + 1);
      
      // Update step progress
      const progressPerStep = 100 / steps.length;
      const newProgress = Math.min(100, (currentStep + 1) * progressPerStep);
      setOverallProgress(newProgress);
      
      // Move to next step
      if (currentStep < steps.length - 1 && elapsedTime % 5 === 0) {
        setSteps(prev => {
          const newSteps = [...prev];
          if (currentStep > 0) {
            newSteps[currentStep - 1].status = 'completed';
            newSteps[currentStep - 1].duration = 5;
          }
          newSteps[currentStep].status = 'running';
          return newSteps;
        });
        setCurrentStep(prev => prev + 1);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [currentStep, elapsedTime, steps.length]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStepIcon = (step: ProgressStep) => {
    const Icon = step.icon;
    
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'running':
        return <Icon className="h-5 w-5 text-blue-600 animate-pulse" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      default:
        return <Icon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStepColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'running':
        return 'text-blue-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Optimization in Progress
            </CardTitle>
            <CardDescription>
              Analyzing strategy performance across complexity levels
            </CardDescription>
          </div>
          <Badge variant="outline" className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatTime(elapsedTime)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Overall Progress</span>
            <span className="font-medium">{Math.round(overallProgress)}%</span>
          </div>
          <Progress value={overallProgress} className="h-2" />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Elapsed: {formatTime(elapsedTime)}</span>
            <span>Est. Remaining: {formatTime(Math.max(0, estimatedTime - elapsedTime))}</span>
          </div>
        </div>

        {/* Step Progress */}
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div 
              key={index}
              className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                step.status === 'running' 
                  ? 'bg-blue-50 border-blue-200' 
                  : step.status === 'completed'
                  ? 'bg-green-50 border-green-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              {getStepIcon(step)}
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className={`font-medium ${getStepColor(step.status)}`}>
                    {step.name}
                  </span>
                  {step.duration && (
                    <span className="text-xs text-muted-foreground">
                      {step.duration}s
                    </span>
                  )}
                </div>
                {step.status === 'running' && (
                  <div className="mt-1">
                    <Progress value={50} className="h-1" />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Information Panel */}
        <div className="rounded-lg bg-blue-50 p-4">
          <div className="flex gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0" />
            <div className="text-sm text-blue-900">
              <p className="font-medium mb-1">What's happening?</p>
              <p className="text-blue-700">
                The optimizer is testing your strategy at 10 different complexity levels,
                calculating risk-adjusted returns for each configuration. This helps identify
                the optimal balance between strategy sophistication and performance stability.
              </p>
            </div>
          </div>
        </div>

        {/* Current Analysis Details */}
        {currentStep > 0 && currentStep <= steps.length && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Current Analysis</h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Complexity Levels Tested</span>
                <span className="font-medium">{Math.min(10, currentStep * 2)}/10</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Data Points Analyzed</span>
                <span className="font-medium">{(currentStep * 1250).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Backtests Run</span>
                <span className="font-medium">{currentStep * 3}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Risk Scenarios</span>
                <span className="font-medium">{currentStep * 5}</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}