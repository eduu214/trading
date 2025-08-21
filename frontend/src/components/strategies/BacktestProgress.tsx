/**
 * Backtest Progress Component
 * F002-US001 Slice 3 Task 15 & 16: Progress tracking with timeout warnings
 * Shows real-time backtesting progress with timeout protection
 */

import React, { useState, useEffect } from 'react';

// Simple SVG icons to replace heroicons
const ClockIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ExclamationTriangleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const CheckCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const XCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

interface ProgressStage {
  stage: string;
  progress: number;
  details: string;
  timestamp: number;
}

interface BacktestProgressProps {
  isRunning: boolean;
  currentStage?: ProgressStage;
  error?: string | null;
  onCancel?: () => void;
  maxTimeout?: number; // in seconds
  softTimeout?: number; // in seconds
}

const STAGE_LABELS = {
  'initialization': 'Initializing Backtest',
  'indicators': 'Calculating Technical Indicators',
  'signals': 'Generating Buy/Sell Signals',
  'backtesting': 'Running Vectorized Backtest',
  'metrics': 'Calculating Performance Metrics',
  'completed': 'Backtest Completed',
  'error': 'Error Occurred'
};

const STAGE_DESCRIPTIONS = {
  'initialization': 'Setting up strategy parameters and validating data',
  'indicators': 'Computing RSI, MACD, and Bollinger Bands indicators',
  'signals': 'Determining entry and exit points based on strategy rules',
  'backtesting': 'Simulating trades over historical data with fees and slippage',
  'metrics': 'Computing Sharpe ratio, drawdown, win rate, and other metrics',
  'completed': 'All calculations finished successfully',
  'error': 'An error occurred during backtesting'
};

export default function BacktestProgress({
  isRunning,
  currentStage,
  error,
  onCancel,
  maxTimeout = 300, // 5 minutes
  softTimeout = 240  // 4 minutes
}: BacktestProgressProps) {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);

  useEffect(() => {
    if (isRunning && !startTime) {
      setStartTime(Date.now());
      setElapsedTime(0);
    } else if (!isRunning) {
      setStartTime(null);
      setElapsedTime(0);
    }
  }, [isRunning, startTime]);

  useEffect(() => {
    if (!isRunning || !startTime) return;

    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning, startTime]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimeoutStatus = () => {
    if (elapsedTime >= maxTimeout) {
      return { status: 'timeout', color: 'text-red-600', bg: 'bg-red-50' };
    } else if (elapsedTime >= softTimeout) {
      return { status: 'warning', color: 'text-yellow-600', bg: 'bg-yellow-50' };
    }
    return { status: 'normal', color: 'text-gray-600', bg: 'bg-gray-50' };
  };

  const timeoutStatus = getTimeoutStatus();
  const progress = currentStage?.progress || 0;

  if (!isRunning && !error && !currentStage) {
    return null;
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          {error ? 'Backtest Failed' : 
           currentStage?.stage === 'completed' ? 'Backtest Completed' :
           'Backtest in Progress'}
        </h3>
        
        {/* Timer */}
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${timeoutStatus.bg}`}>
          <ClockIcon className={`h-4 w-4 ${timeoutStatus.color}`} />
          <span className={`text-sm font-medium ${timeoutStatus.color}`}>
            {formatTime(elapsedTime)}
          </span>
          {timeoutStatus.status === 'warning' && (
            <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
          )}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Backtest Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
                {error.includes('timeout') && (
                  <p className="mt-2">
                    The backtest operation exceeded the {maxTimeout / 60}-minute time limit. 
                    This may be due to complex parameters or system load.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {isRunning && !error && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>
              {currentStage ? STAGE_LABELS[currentStage.stage as keyof typeof STAGE_LABELS] || currentStage.stage : 'Starting...'}
            </span>
            <span>{Math.round(progress * 100)}%</span>
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
          
          {currentStage && (
            <p className="mt-2 text-sm text-gray-500">
              {STAGE_DESCRIPTIONS[currentStage.stage as keyof typeof STAGE_DESCRIPTIONS] || currentStage.details}
            </p>
          )}
        </div>
      )}

      {/* Completed State */}
      {currentStage?.stage === 'completed' && !isRunning && (
        <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <CheckCircleIcon className="h-5 w-5 text-green-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Backtest Completed Successfully</h3>
              <div className="mt-2 text-sm text-green-700">
                <p>Backtesting finished in {formatTime(elapsedTime)}. Review the results below.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Timeout Warning */}
      {timeoutStatus.status === 'warning' && isRunning && (
        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Long Running Operation</h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  This backtest has been running for over {softTimeout / 60} minutes. 
                  It will automatically timeout at {maxTimeout / 60} minutes to prevent system overload.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Stats */}
      {(isRunning || error) && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center text-sm">
          <div>
            <div className="text-gray-500">Elapsed Time</div>
            <div className="font-medium">{formatTime(elapsedTime)}</div>
          </div>
          <div>
            <div className="text-gray-500">Time Limit</div>
            <div className="font-medium">{formatTime(maxTimeout)}</div>
          </div>
          <div>
            <div className="text-gray-500">Progress</div>
            <div className="font-medium">{Math.round(progress * 100)}%</div>
          </div>
          <div>
            <div className="text-gray-500">Status</div>
            <div className={`font-medium ${
              error ? 'text-red-600' : 
              currentStage?.stage === 'completed' ? 'text-green-600' :
              timeoutStatus.status === 'warning' ? 'text-yellow-600' :
              'text-blue-600'
            }`}>
              {error ? 'Failed' :
               currentStage?.stage === 'completed' ? 'Complete' :
               timeoutStatus.status === 'warning' ? 'Long Running' :
               'Running'}
            </div>
          </div>
        </div>
      )}

      {/* Cancel Button */}
      {isRunning && onCancel && (
        <div className="mt-4 text-center">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 text-sm font-medium"
          >
            Cancel Backtest
          </button>
        </div>
      )}
    </div>
  );
}