/**
 * Strategy Comparison Component
 * F002-US001 Slice 2: Multi-Strategy Comparison Interface
 * Creates sortable performance metrics table per UX specifications
 */

import React, { useState, useEffect } from 'react';
import { ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

interface StrategyResult {
  strategy: string;
  sharpe_ratio: number;
  total_return: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  sharpe_validation: 'PASS' | 'FAIL';
  error?: string;
}

interface ComparisonResponse {
  status: string;
  symbol: string;
  period: string;
  strategies_tested: number;
  best_strategy: string | null;
  results: StrategyResult[];
  recommendation: string;
}

type SortField = keyof Pick<StrategyResult, 'sharpe_ratio' | 'total_return' | 'max_drawdown' | 'win_rate' | 'profit_factor' | 'total_trades'>;
type SortDirection = 'asc' | 'desc';

interface StrategyComparisonProps {
  symbol?: string;
  onStrategySelect?: (strategy: string) => void;
}

export default function StrategyComparison({ 
  symbol = 'AAPL', 
  onStrategySelect 
}: StrategyComparisonProps) {
  const [comparisonData, setComparisonData] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('sharpe_ratio');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/strategies/compare?symbol=${symbol}`);
      
      if (!response.ok) {
        throw new Error(`Failed to compare strategies: ${response.statusText}`);
      }

      const data: ComparisonResponse = await response.json();
      setComparisonData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison();
  }, [symbol]);

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedResults = comparisonData?.results.slice().sort((a, b) => {
    if (a.error || b.error) return 0;
    
    const aValue = a[sortField];
    const bValue = b[sortField];
    
    if (sortDirection === 'asc') {
      return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
    } else {
      return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
    }
  });

  const formatValue = (field: SortField, value: number): string => {
    switch (field) {
      case 'sharpe_ratio':
      case 'profit_factor':
        return value.toFixed(2);
      case 'total_return':
      case 'max_drawdown':
      case 'win_rate':
        return `${value.toFixed(1)}%`;
      case 'total_trades':
        return value.toString();
      default:
        return value.toString();
    }
  };

  const getMetricColor = (field: SortField, value: number, validation?: string): string => {
    switch (field) {
      case 'sharpe_ratio':
        return value > 1.0 ? 'text-green-600' : 'text-red-600';
      case 'total_return':
        return value > 0 ? 'text-green-600' : 'text-red-600';
      case 'max_drawdown':
        return value < 15 ? 'text-green-600' : 'text-red-600';
      case 'win_rate':
        return value > 45 ? 'text-green-600' : 'text-red-600';
      case 'profit_factor':
        return value > 1.0 ? 'text-green-600' : 'text-red-600';
      default:
        return 'text-gray-900';
    }
  };

  const SortableHeader: React.FC<{ field: SortField; children: React.ReactNode }> = ({ field, children }) => (
    <th 
      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center space-x-1">
        <span>{children}</span>
        {sortField === field && (
          sortDirection === 'asc' ? 
            <ChevronUpIcon className="w-4 h-4" /> : 
            <ChevronDownIcon className="w-4 h-4" />
        )}
      </div>
    </th>
  );

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-4">
            <div className="h-6 bg-gray-200 rounded w-48"></div>
            <div className="h-8 bg-gray-200 rounded w-32"></div>
          </div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Strategy Comparison Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={fetchComparison}
                  className="bg-red-100 text-red-800 px-4 py-2 rounded-md text-sm font-medium hover:bg-red-200"
                >
                  Retry Comparison
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!comparisonData) {
    return null;
  }

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Strategy Performance Comparison</h3>
            <p className="mt-1 text-sm text-gray-500">
              {comparisonData.symbol} • {comparisonData.period} • {comparisonData.strategies_tested} strategies tested
            </p>
          </div>
          <button
            onClick={fetchComparison}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
          >
            Refresh Comparison
          </button>
        </div>

        {/* Recommendation Banner */}
        {comparisonData.best_strategy && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Recommendation</h3>
                <div className="mt-2 text-sm text-green-700">
                  <p>{comparisonData.recommendation}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Strategy
              </th>
              <SortableHeader field="sharpe_ratio">Sharpe Ratio</SortableHeader>
              <SortableHeader field="total_return">Total Return</SortableHeader>
              <SortableHeader field="max_drawdown">Max Drawdown</SortableHeader>
              <SortableHeader field="win_rate">Win Rate</SortableHeader>
              <SortableHeader field="profit_factor">Profit Factor</SortableHeader>
              <SortableHeader field="total_trades">Total Trades</SortableHeader>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Validation
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedResults?.map((result, index) => (
              <tr key={result.strategy} className={index === 0 ? 'bg-green-50' : 'hover:bg-gray-50'}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{result.strategy}</div>
                      {index === 0 && (
                        <div className="text-xs text-green-600 font-medium">Best Performing</div>
                      )}
                      {result.error && (
                        <div className="text-xs text-red-600">{result.error}</div>
                      )}
                    </div>
                  </div>
                </td>

                {!result.error ? (
                  <>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium ${getMetricColor('sharpe_ratio', result.sharpe_ratio)}`}>
                        {formatValue('sharpe_ratio', result.sharpe_ratio)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium ${getMetricColor('total_return', result.total_return)}`}>
                        {formatValue('total_return', result.total_return)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium ${getMetricColor('max_drawdown', result.max_drawdown)}`}>
                        {formatValue('max_drawdown', result.max_drawdown)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium ${getMetricColor('win_rate', result.win_rate)}`}>
                        {formatValue('win_rate', result.win_rate)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium ${getMetricColor('profit_factor', result.profit_factor)}`}>
                        {formatValue('profit_factor', result.profit_factor)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatValue('total_trades', result.total_trades)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        result.sharpe_validation === 'PASS' 
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {result.sharpe_validation}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => onStrategySelect?.(result.strategy)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Select Strategy
                      </button>
                    </td>
                  </>
                ) : (
                  <td colSpan={7} className="px-6 py-4 text-center text-sm text-red-600">
                    Error processing strategy
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div>
            Sorted by {sortField} ({sortDirection === 'desc' ? 'highest first' : 'lowest first'})
          </div>
          <div>
            Performance validation requires Sharpe ratio > 1.0
          </div>
        </div>
      </div>
    </div>
  );
}