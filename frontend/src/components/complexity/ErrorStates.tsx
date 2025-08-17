'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  AlertTriangle,
  XCircle,
  RefreshCw,
  Clock,
  Database,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  ChevronRight,
  FileX,
  WifiOff,
  Timer,
  Settings
} from 'lucide-react';

export type ErrorCode = 
  | 'INSUFFICIENT_DATA'
  | 'INVALID_TIMEFRAME'
  | 'CONFLICTING_CONSTRAINTS'
  | 'OPTIMIZATION_TIMEOUT'
  | 'INVALID_PARAMETERS'
  | 'DATA_QUALITY_ISSUE'
  | 'CONSTRAINT_IMPOSSIBLE'
  | 'MARKET_DATA_UNAVAILABLE'
  | 'CALCULATION_ERROR'
  | 'DATABASE_ERROR'
  | 'NETWORK_ERROR';

interface ErrorDetails {
  code: ErrorCode;
  message: string;
  details?: Record<string, any>;
  suggestions?: string[];
  canRetry?: boolean;
  retryCount?: number;
  timestamp?: string;
}

interface ErrorStateProps {
  error: ErrorDetails;
  onRetry?: () => void;
  onDismiss?: () => void;
  onViewDetails?: () => void;
}

const ERROR_ICONS: Record<ErrorCode, React.ElementType> = {
  INSUFFICIENT_DATA: FileX,
  INVALID_TIMEFRAME: Clock,
  CONFLICTING_CONSTRAINTS: AlertTriangle,
  OPTIMIZATION_TIMEOUT: Timer,
  INVALID_PARAMETERS: Settings,
  DATA_QUALITY_ISSUE: TrendingDown,
  CONSTRAINT_IMPOSSIBLE: XCircle,
  MARKET_DATA_UNAVAILABLE: WifiOff,
  CALCULATION_ERROR: AlertCircle,
  DATABASE_ERROR: Database,
  NETWORK_ERROR: WifiOff
};

const ERROR_COLORS: Record<ErrorCode, string> = {
  INSUFFICIENT_DATA: 'text-yellow-600',
  INVALID_TIMEFRAME: 'text-blue-600',
  CONFLICTING_CONSTRAINTS: 'text-orange-600',
  OPTIMIZATION_TIMEOUT: 'text-purple-600',
  INVALID_PARAMETERS: 'text-red-600',
  DATA_QUALITY_ISSUE: 'text-yellow-600',
  CONSTRAINT_IMPOSSIBLE: 'text-red-600',
  MARKET_DATA_UNAVAILABLE: 'text-gray-600',
  CALCULATION_ERROR: 'text-red-600',
  DATABASE_ERROR: 'text-red-600',
  NETWORK_ERROR: 'text-gray-600'
};

export function ErrorState({ error, onRetry, onDismiss, onViewDetails }: ErrorStateProps) {
  const Icon = ERROR_ICONS[error.code] || AlertCircle;
  const iconColor = ERROR_COLORS[error.code] || 'text-red-600';

  return (
    <Card className="border-red-200 bg-red-50/50">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <Icon className={`h-5 w-5 mt-0.5 ${iconColor}`} />
            <div>
              <CardTitle className="text-lg">Optimization Error</CardTitle>
              <CardDescription className="mt-1">
                {error.message}
              </CardDescription>
            </div>
          </div>
          <Badge variant="destructive" className="text-xs">
            {error.code.replace(/_/g, ' ')}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Error Details */}
        {error.details && (
          <div className="rounded-lg bg-white/50 p-3 space-y-2">
            <h4 className="text-sm font-medium">Details</h4>
            <div className="text-xs text-muted-foreground space-y-1">
              {Object.entries(error.details).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                  <span className="font-mono">{JSON.stringify(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recovery Suggestions */}
        {error.suggestions && error.suggestions.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Suggested Actions</h4>
            <ul className="space-y-1">
              {error.suggestions.map((suggestion, index) => (
                <li key={index} className="flex items-start gap-2 text-sm">
                  <ChevronRight className="h-3 w-3 mt-0.5 text-muted-foreground" />
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Retry Information */}
        {error.canRetry && error.retryCount !== undefined && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <RefreshCw className="h-3 w-3" />
            <span>Retry attempt {error.retryCount} of 3</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {error.canRetry && onRetry && (
            <Button onClick={onRetry} size="sm">
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
          {onViewDetails && (
            <Button variant="outline" size="sm" onClick={onViewDetails}>
              View Details
            </Button>
          )}
          {onDismiss && (
            <Button variant="ghost" size="sm" onClick={onDismiss}>
              Dismiss
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface TimeoutWarningProps {
  elapsedTime: number;
  estimatedTime: number;
  onCancel?: () => void;
}

export function TimeoutWarning({ elapsedTime, estimatedTime, onCancel }: TimeoutWarningProps) {
  const progress = Math.min(100, (elapsedTime / estimatedTime) * 100);
  const isOvertime = elapsedTime > estimatedTime;

  return (
    <Alert className={isOvertime ? 'border-yellow-500' : ''}>
      <Clock className="h-4 w-4" />
      <AlertTitle>
        {isOvertime ? 'Taking longer than expected' : 'Processing...'}
      </AlertTitle>
      <AlertDescription className="space-y-3 mt-2">
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
        
        <p className="text-sm">
          {isOvertime 
            ? 'The optimization is taking longer than expected. This might happen with complex constraints or multiple timeframes.'
            : `Estimated time remaining: ${Math.max(0, estimatedTime - elapsedTime)} seconds`
          }
        </p>
        
        {onCancel && (
          <Button variant="outline" size="sm" onClick={onCancel}>
            <XCircle className="h-3 w-3 mr-1" />
            Cancel Operation
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}

interface DataQualityWarningProps {
  issues: {
    type: 'missing_data' | 'gaps' | 'outliers' | 'low_volume';
    severity: 'low' | 'medium' | 'high';
    description: string;
    affected: string;
  }[];
  onProceed?: () => void;
  onCancel?: () => void;
}

export function DataQualityWarning({ issues, onProceed, onCancel }: DataQualityWarningProps) {
  const highSeverityCount = issues.filter(i => i.severity === 'high').length;
  const hasCriticalIssues = highSeverityCount > 0;

  return (
    <Card className="border-yellow-200 bg-yellow-50/50">
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-yellow-600" />
          <CardTitle>Data Quality Issues Detected</CardTitle>
        </div>
        <CardDescription>
          {hasCriticalIssues 
            ? 'Critical issues found that may affect analysis accuracy'
            : 'Minor issues found that might impact results'
          }
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          {issues.map((issue, index) => (
            <div key={index} className="flex items-start gap-3 p-2 rounded-lg bg-white/50">
              <Badge 
                variant={issue.severity === 'high' ? 'destructive' : issue.severity === 'medium' ? 'default' : 'secondary'}
                className="text-xs"
              >
                {issue.severity}
              </Badge>
              <div className="flex-1">
                <p className="text-sm font-medium">{issue.type.replace(/_/g, ' ').toUpperCase()}</p>
                <p className="text-xs text-muted-foreground">{issue.description}</p>
                <p className="text-xs text-muted-foreground mt-1">Affected: {issue.affected}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {onProceed && (
            <Button 
              onClick={onProceed} 
              size="sm"
              variant={hasCriticalIssues ? 'outline' : 'default'}
            >
              Proceed Anyway
            </Button>
          )}
          {onCancel && (
            <Button variant="ghost" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface FallbackResultProps {
  fallbackData: {
    complexity_level: number;
    confidence: number;
    score: number;
    message: string;
    metrics?: Record<string, number>;
  };
  onAccept?: () => void;
  onReject?: () => void;
}

export function FallbackResult({ fallbackData, onAccept, onReject }: FallbackResultProps) {
  return (
    <Card className="border-blue-200 bg-blue-50/50">
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-blue-600" />
          <CardTitle>Using Fallback Analysis</CardTitle>
        </div>
        <CardDescription>
          {fallbackData.message}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold">{fallbackData.complexity_level}</p>
            <p className="text-xs text-muted-foreground">Complexity Level</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{Math.round(fallbackData.confidence * 100)}%</p>
            <p className="text-xs text-muted-foreground">Confidence</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{fallbackData.score}</p>
            <p className="text-xs text-muted-foreground">Score</p>
          </div>
        </div>

        {fallbackData.metrics && (
          <div className="rounded-lg bg-white/50 p-3">
            <h4 className="text-sm font-medium mb-2">Estimated Metrics</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {Object.entries(fallbackData.metrics).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-muted-foreground capitalize">
                    {key.replace(/_/g, ' ')}:
                  </span>
                  <span className="font-mono">{typeof value === 'number' ? value.toFixed(2) : value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">
            This is a simplified analysis based on limited data. For more accurate results, 
            please ensure sufficient data is available and retry the optimization.
          </AlertDescription>
        </Alert>

        <div className="flex items-center gap-2">
          {onAccept && (
            <Button onClick={onAccept} size="sm">
              <CheckCircle className="h-3 w-3 mr-1" />
              Use This Result
            </Button>
          )}
          {onReject && (
            <Button variant="outline" size="sm" onClick={onReject}>
              <XCircle className="h-3 w-3 mr-1" />
              Retry with Different Settings
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface RetryStatusProps {
  retryCount: number;
  maxRetries: number;
  nextRetryIn?: number;
  onCancelRetry?: () => void;
}

export function RetryStatus({ retryCount, maxRetries, nextRetryIn, onCancelRetry }: RetryStatusProps) {
  return (
    <Alert>
      <RefreshCw className="h-4 w-4 animate-spin" />
      <AlertTitle>Retrying Operation</AlertTitle>
      <AlertDescription className="space-y-2 mt-2">
        <p className="text-sm">
          Attempt {retryCount} of {maxRetries}
        </p>
        {nextRetryIn && (
          <p className="text-sm text-muted-foreground">
            Next retry in {nextRetryIn} seconds...
          </p>
        )}
        {onCancelRetry && (
          <Button variant="ghost" size="sm" onClick={onCancelRetry}>
            Cancel Retry
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}