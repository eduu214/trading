/**
 * Backtest Results Component
 * F002-US001: Display comprehensive backtesting performance metrics per UX specifications
 */

import React from 'react';
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface BacktestResult {
  status: string;
  strategy: string;
  symbol: string;
  period: {
    start: string;
    end: string;
    days: number;
  };
  performance: {
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    profit_factor: number;
  };
  trades: {
    total: number;
    winning: number;
    losing: number;
    avg_win: number;
    avg_loss: number;
    best_trade: number;
    worst_trade: number;
  };
  capital: {
    initial: number;
    final: number;
  };
  execution_time: number;
  sharpe_validation: 'PASS' | 'FAIL';
}

interface BacktestResultsProps {
  result: BacktestResult | null;
  loading?: boolean;
  error?: string | null;
  onApproveStrategy?: () => void;
  onModifyStrategy?: () => void;
}

export default function BacktestResults({ 
  result, 
  loading = false, 
  error = null,
  onApproveStrategy,
  onModifyStrategy 
}: BacktestResultsProps) {
  
  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-64 mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-40 bg-gray-200 rounded mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Backtest Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Backtest Results</h3>
          <p className="text-gray-500">Configure and run a strategy to see performance results here.</p>
        </div>
      </div>
    );
  }

  const getMetricStatus = (metric: string, value: number) => {
    switch (metric) {
      case 'sharpe_ratio':
        return value > 1.0 ? 'success' : 'error';
      case 'max_drawdown':
        return value < 15 ? 'success' : 'error';
      case 'win_rate':
        return value > 45 ? 'success' : 'error';
      case 'total_return':
        return value > 0 ? 'success' : 'error';
      default:
        return 'neutral';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const MetricCard: React.FC<{ 
    label: string; 
    value: number; 
    format: 'number' | 'percentage' | 'currency';
    metric?: string;
  }> = ({ label, value, format, metric }) => {
    const status = metric ? getMetricStatus(metric, value) : 'neutral';
    const colorClass = getStatusColor(status);

    const formatValue = () => {
      switch (format) {
        case 'percentage':
          return `${value.toFixed(1)}%`;
        case 'currency':
          return `$${value.toFixed(2)}`;
        case 'number':
          return value.toFixed(2);
        default:
          return value.toString();
      }
    };

    return (
      <div className={`border rounded-lg p-4 ${colorClass}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium opacity-75">{label}</p>
            <p className="text-2xl font-bold mt-1">{formatValue()}</p>
          </div>
          {status === 'success' && <CheckCircleIcon className="h-6 w-6" />}
          {status === 'error' && <XCircleIcon className="h-6 w-6" />}
          {status === 'warning' && <ExclamationTriangleIcon className="h-6 w-6" />}
        </div>
      </div>
    );
  };

  const overallValidation = result.sharpe_validation === 'PASS' && 
                           result.performance.max_drawdown < 15 && 
                           result.performance.win_rate > 45;

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Backtest Results</h3>
            <p className="mt-1 text-sm text-gray-500">
              {result.strategy} • {result.symbol} • {result.period.days} days
              ({new Date(result.period.start).toLocaleDateString()} to {new Date(result.period.end).toLocaleDateString()})
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Execution Time</div>
            <div className="font-medium">{result.execution_time}s</div>
          </div>
        </div>

        {/* Validation Banner */}
        <div className={`mt-4 border rounded-lg p-4 ${
          overallValidation 
            ? 'bg-green-50 border-green-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center">
            {overallValidation ? (
              <CheckCircleIcon className="h-5 w-5 text-green-400 mr-3" />
            ) : (
              <XCircleIcon className="h-5 w-5 text-red-400 mr-3" />
            )}
            <div>
              <h4 className={`font-medium ${overallValidation ? 'text-green-800' : 'text-red-800'}`}>
                {overallValidation ? 'Strategy Validation Passed' : 'Strategy Validation Failed'}
              </h4>
              <p className={`text-sm mt-1 ${overallValidation ? 'text-green-700' : 'text-red-700'}`}>
                {overallValidation 
                  ? 'All performance thresholds met. Strategy is ready for paper trading.'
                  : 'Strategy does not meet minimum performance requirements.'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <MetricCard 
            label="Sharpe Ratio" 
            value={result.performance.sharpe_ratio} 
            format="number"
            metric="sharpe_ratio"
          />
          <MetricCard 
            label="Total Return" 
            value={result.performance.total_return} 
            format="percentage"
            metric="total_return"
          />
          <MetricCard 
            label="Max Drawdown" 
            value={result.performance.max_drawdown} 
            format="percentage"
            metric="max_drawdown"
          />
          <MetricCard 
            label="Win Rate" 
            value={result.performance.win_rate} 
            format="percentage"
            metric="win_rate"
          />
        </div>

        {/* Additional Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Performance Details */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-medium text-gray-900 mb-4">Performance Details</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Profit Factor</span>
                <span className="font-medium">{result.performance.profit_factor.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Initial Capital</span>
                <span className="font-medium">${result.capital.initial.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Final Capital</span>
                <span className="font-medium">${result.capital.final.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Profit/Loss</span>
                <span className={`font-medium ${
                  result.capital.final > result.capital.initial ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${(result.capital.final - result.capital.initial).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Trade Statistics */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-medium text-gray-900 mb-4">Trade Statistics</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Trades</span>
                <span className="font-medium">{result.trades.total}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Winning Trades</span>
                <span className="font-medium text-green-600">{result.trades.winning}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Losing Trades</span>
                <span className="font-medium text-red-600">{result.trades.losing}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Average Win</span>
                <span className="font-medium text-green-600">${result.trades.avg_win.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Average Loss</span>
                <span className="font-medium text-red-600">${result.trades.avg_loss.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Best Trade</span>
                <span className="font-medium text-green-600">${result.trades.best_trade.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Worst Trade</span>
                <span className="font-medium text-red-600">${result.trades.worst_trade.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-4 pt-6 border-t border-gray-200">
          {overallValidation ? (
            <button
              onClick={onApproveStrategy}
              className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 font-medium"
            >
              Approve for Paper Trading
            </button>
          ) : (
            <div className="flex-1 bg-gray-100 text-gray-400 py-2 px-4 rounded-md text-center font-medium">
              Strategy Validation Required
            </div>
          )}
          
          <button
            onClick={onModifyStrategy}
            className="flex-1 bg-white border border-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium"
          >
            Modify Strategy
          </button>
        </div>
      </div>
    </div>
  );
}