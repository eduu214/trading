/**
 * Strategy Validation Error Interface
 * F002-US001 Slice 3 Task 16: Error UI for Sharpe ratio validation failures
 * Displays clear error messages per UX specifications
 */

import React from 'react';

// Simple SVG icons to replace heroicons
const XCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ExclamationTriangleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const InformationCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ArrowPathIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

interface ValidationError {
  type: 'error' | 'warning' | 'info';
  field: string;
  message: string;
  value?: number;
  threshold?: number;
  suggestion?: string;
}

interface StrategyValidationErrorsProps {
  errors: ValidationError[];
  onRetry?: () => void;
  onModifyStrategy?: () => void;
  strategyName?: string;
  symbol?: string;
}

const ERROR_ICONS = {
  error: XCircleIcon,
  warning: ExclamationTriangleIcon,
  info: InformationCircleIcon
};

const ERROR_COLORS = {
  error: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-800',
    icon: 'text-red-400'
  },
  warning: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    text: 'text-yellow-800',
    icon: 'text-yellow-400'
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-800',
    icon: 'text-blue-400'
  }
};

export default function StrategyValidationErrors({
  errors,
  onRetry,
  onModifyStrategy,
  strategyName = "Strategy",
  symbol = ""
}: StrategyValidationErrorsProps) {
  
  if (!errors || errors.length === 0) {
    return null;
  }

  const criticalErrors = errors.filter(e => e.type === 'error');
  const warnings = errors.filter(e => e.type === 'warning');
  const hasFailures = criticalErrors.length > 0;

  const getSharpeRatioMessage = (error: ValidationError) => {
    if (error.field === 'sharpe_ratio' && error.value !== undefined && error.threshold !== undefined) {
      return (
        <div className="mt-2 text-sm">
          <div className="flex justify-between">
            <span>Your Sharpe Ratio:</span>
            <span className="font-medium text-red-600">{error.value.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span>Required Minimum:</span>
            <span className="font-medium text-green-600">{error.threshold.toFixed(1)}</span>
          </div>
          <div className="flex justify-between border-t border-red-200 mt-1 pt-1">
            <span>Gap to Close:</span>
            <span className="font-medium text-red-600">
              {(error.threshold - error.value).toFixed(2)}
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  const ErrorItem: React.FC<{ error: ValidationError }> = ({ error }) => {
    const Icon = ERROR_ICONS[error.type];
    const colors = ERROR_COLORS[error.type];

    return (
      <div className={`rounded-md p-4 ${colors.bg} ${colors.border} border`}>
        <div className="flex">
          <div className="flex-shrink-0">
            <Icon className={`h-5 w-5 ${colors.icon}`} />
          </div>
          <div className="ml-3 flex-1">
            <h3 className={`text-sm font-medium ${colors.text}`}>
              {error.field === 'sharpe_ratio' ? 'Sharpe Ratio Validation Failed' : 
               error.field === 'max_drawdown' ? 'Maximum Drawdown Exceeded' :
               error.field === 'win_rate' ? 'Win Rate Below Threshold' :
               error.field === 'data_quality' ? 'Data Quality Issue' :
               'Validation Error'}
            </h3>
            <div className={`mt-2 text-sm ${colors.text}`}>
              <p>{error.message}</p>
              
              {/* Special formatting for Sharpe ratio */}
              {getSharpeRatioMessage(error)}
              
              {/* Suggestion */}
              {error.suggestion && (
                <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                  <p className="text-sm text-gray-700">
                    <strong>Suggestion:</strong> {error.suggestion}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Strategy Validation Results</h3>
            <p className="mt-1 text-sm text-gray-500">
              {strategyName} {symbol && `• ${symbol}`} • {errors.length} validation issue{errors.length !== 1 ? 's' : ''} found
            </p>
          </div>
          
          {hasFailures && (
            <div className="text-right">
              <span className="inline-flex px-3 py-1 text-sm font-semibold rounded-full bg-red-100 text-red-800">
                Validation Failed
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="p-6">
        {/* Summary Banner */}
        {hasFailures && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <XCircleIcon className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Strategy Does Not Meet Performance Requirements
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>
                    This strategy has failed to meet the minimum performance thresholds required 
                    for paper trading. Review the issues below and consider adjusting your strategy parameters.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error List */}
        <div className="space-y-4">
          {criticalErrors.map((error, index) => (
            <ErrorItem key={`error-${index}`} error={error} />
          ))}
          
          {warnings.map((error, index) => (
            <ErrorItem key={`warning-${index}`} error={error} />
          ))}
        </div>

        {/* Performance Improvement Tips */}
        {hasFailures && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Performance Improvement Tips
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <ul className="list-disc list-inside space-y-1">
                    <li>Try adjusting indicator periods (shorter periods may increase signals)</li>
                    <li>Consider different entry/exit thresholds (RSI 25/75 instead of 30/70)</li>
                    <li>Test on more volatile stocks (higher volatility often improves Sharpe ratios)</li>
                    <li>Review the strategy on different time periods</li>
                    <li>Consider combining multiple indicators for better performance</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex space-x-4">
          {onModifyStrategy && (
            <button
              onClick={onModifyStrategy}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium"
            >
              Modify Strategy Parameters
            </button>
          )}
          
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center justify-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Retry Validation
            </button>
          )}
        </div>

        {/* Help Text */}
        <div className="mt-4 text-xs text-gray-500 text-center">
          Strategies must achieve a Sharpe ratio &gt; 1.0, maximum drawdown &lt; 15%, and win rate &gt; 45% to qualify for paper trading.
        </div>
      </div>
    </div>
  );
}