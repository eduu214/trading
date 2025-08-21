/**
 * Strategy Builder Component
 * F002-US001: Strategy configuration interface per UX specifications
 * Implements strategy selection and parameter configuration
 */

import React, { useState } from 'react';

// Simple SVG icons to replace heroicons
const ChevronDownIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

interface StrategyParameters {
  // RSI Parameters
  rsi_period: number;
  oversold_level: number;
  overbought_level: number;
  // MACD Parameters
  macd_fast: number;
  macd_slow: number;
  macd_signal: number;
  // Bollinger Bands Parameters
  bb_period: number;
  bb_std_dev: number;
}

interface StrategyBuilderProps {
  onStrategyRun?: (strategyId: string, symbol: string, parameters: StrategyParameters) => void;
}

const DEFAULT_PARAMETERS: StrategyParameters = {
  rsi_period: 14,
  oversold_level: 30,
  overbought_level: 70,
  macd_fast: 12,
  macd_slow: 26,
  macd_signal: 9,
  bb_period: 20,
  bb_std_dev: 2.0
};

const STRATEGY_OPTIONS = [
  {
    id: 'rsi_mean_reversion',
    name: 'RSI Mean Reversion',
    description: 'Buy when RSI is oversold (&lt;30), sell when overbought (&gt;70)',
    parameters: ['rsi_period', 'oversold_level', 'overbought_level']
  },
  {
    id: 'macd_momentum',
    name: 'MACD Momentum',
    description: 'Buy when MACD crosses above signal line, sell when crosses below',
    parameters: ['macd_fast', 'macd_slow', 'macd_signal']
  },
  {
    id: 'bollinger_breakout',
    name: 'Bollinger Bands Mean Reversion',
    description: 'Buy at lower band (oversold), sell at upper band (overbought)',
    parameters: ['bb_period', 'bb_std_dev']
  }
];

export default function StrategyBuilder({ onStrategyRun }: StrategyBuilderProps) {
  const [selectedStrategy, setSelectedStrategy] = useState<string>('rsi_mean_reversion');
  const [symbol, setSymbol] = useState<string>('AAPL');
  const [parameters, setParameters] = useState<StrategyParameters>(DEFAULT_PARAMETERS);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const selectedStrategyInfo = STRATEGY_OPTIONS.find(s => s.id === selectedStrategy);

  const validateParameters = (): boolean => {
    const newErrors: Record<string, string> = {};

    // RSI validation
    if (parameters.rsi_period < 2 || parameters.rsi_period > 50) {
      newErrors.rsi_period = 'RSI period must be between 2 and 50';
    }
    if (parameters.oversold_level < 10 || parameters.oversold_level > 40) {
      newErrors.oversold_level = 'Oversold level must be between 10 and 40';
    }
    if (parameters.overbought_level < 60 || parameters.overbought_level > 90) {
      newErrors.overbought_level = 'Overbought level must be between 60 and 90';
    }
    if (parameters.oversold_level >= parameters.overbought_level) {
      newErrors.oversold_level = 'Oversold level must be less than overbought level';
    }

    // MACD validation
    if (parameters.macd_fast <= 0 || parameters.macd_fast > 50) {
      newErrors.macd_fast = 'MACD fast period must be between 1 and 50';
    }
    if (parameters.macd_slow <= 0 || parameters.macd_slow > 100) {
      newErrors.macd_slow = 'MACD slow period must be between 1 and 100';
    }
    if (parameters.macd_signal <= 0 || parameters.macd_signal > 50) {
      newErrors.macd_signal = 'MACD signal period must be between 1 and 50';
    }
    if (parameters.macd_fast >= parameters.macd_slow) {
      newErrors.macd_fast = 'Fast period must be less than slow period';
    }

    // Bollinger Bands validation
    if (parameters.bb_period < 5 || parameters.bb_period > 100) {
      newErrors.bb_period = 'Bollinger period must be between 5 and 100';
    }
    if (parameters.bb_std_dev < 0.5 || parameters.bb_std_dev > 5.0) {
      newErrors.bb_std_dev = 'Standard deviation must be between 0.5 and 5.0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleParameterChange = (key: keyof StrategyParameters, value: number) => {
    setParameters(prev => ({ ...prev, [key]: value }));
    
    // Clear error for this field
    if (errors[key]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[key];
        return newErrors;
      });
    }
  };

  const handleRunStrategy = () => {
    if (validateParameters()) {
      onStrategyRun?.(selectedStrategy, symbol, parameters);
    }
  };

  const renderParameterField = (paramKey: string, label: string, min: number, max: number, step: number = 1) => {
    const value = parameters[paramKey as keyof StrategyParameters];
    const error = errors[paramKey];

    return (
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        <input
          type="number"
          value={value}
          onChange={(e) => handleParameterChange(paramKey as keyof StrategyParameters, parseFloat(e.target.value) || 0)}
          min={min}
          max={max}
          step={step}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
            error ? 'border-red-300' : 'border-gray-300'
          }`}
        />
        {error && <p className="text-xs text-red-600">{error}</p>}
      </div>
    );
  };

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Strategy Builder</h3>
        <p className="mt-1 text-sm text-gray-500">
          Configure technical indicators and backtesting parameters
        </p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Configuration Panel */}
          <div className="space-y-6">
            {/* Symbol Input */}
            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">
                Symbol
              </label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="Enter symbol (e.g., AAPL)"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Strategy Selection */}
            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">
                Strategy Type
              </label>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="w-full bg-white border border-gray-300 rounded-md px-3 py-2 text-left shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <span className="block truncate">{selectedStrategyInfo?.name}</span>
                  <span className="absolute inset-y-0 right-0 flex items-center pr-2">
                    <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                  </span>
                </button>

                {isDropdownOpen && (
                  <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none">
                    {STRATEGY_OPTIONS.map((strategy) => (
                      <button
                        key={strategy.id}
                        onClick={() => {
                          setSelectedStrategy(strategy.id);
                          setIsDropdownOpen(false);
                        }}
                        className={`w-full text-left px-3 py-2 hover:bg-gray-100 ${
                          selectedStrategy === strategy.id ? 'bg-blue-50 text-blue-900' : 'text-gray-900'
                        }`}
                      >
                        <div className="font-medium">{strategy.name}</div>
                        <div className="text-sm text-gray-500">{strategy.description}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Strategy Parameters */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-gray-900">Strategy Parameters</h4>
              
              {selectedStrategy === 'rsi_mean_reversion' && (
                <div className="space-y-4">
                  {renderParameterField('rsi_period', 'RSI Period', 2, 50)}
                  {renderParameterField('oversold_level', 'Oversold Level', 10, 40)}
                  {renderParameterField('overbought_level', 'Overbought Level', 60, 90)}
                </div>
              )}

              {selectedStrategy === 'macd_momentum' && (
                <div className="space-y-4">
                  {renderParameterField('macd_fast', 'Fast Period', 1, 50)}
                  {renderParameterField('macd_slow', 'Slow Period', 1, 100)}
                  {renderParameterField('macd_signal', 'Signal Period', 1, 50)}
                </div>
              )}

              {selectedStrategy === 'bollinger_breakout' && (
                <div className="space-y-4">
                  {renderParameterField('bb_period', 'Period', 5, 100)}
                  {renderParameterField('bb_std_dev', 'Standard Deviations', 0.5, 5.0, 0.1)}
                </div>
              )}
            </div>

            {/* Run Strategy Button */}
            <div className="pt-4">
              <button
                onClick={handleRunStrategy}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium"
              >
                Run Backtest
              </button>
            </div>
          </div>

          {/* Preview Panel */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Strategy Preview</h4>
            
            {selectedStrategyInfo && (
              <div className="space-y-4">
                <div>
                  <h5 className="font-medium text-gray-900">{selectedStrategyInfo.name}</h5>
                  <p className="text-sm text-gray-600 mt-1">{selectedStrategyInfo.description}</p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h6 className="font-medium text-gray-900 mb-2">Current Parameters:</h6>
                  <div className="text-sm space-y-1">
                    {selectedStrategy === 'rsi_mean_reversion' && (
                      <>
                        <div>RSI Period: <span className="font-medium">{parameters.rsi_period}</span></div>
                        <div>Oversold Level: <span className="font-medium">{parameters.oversold_level}</span></div>
                        <div>Overbought Level: <span className="font-medium">{parameters.overbought_level}</span></div>
                      </>
                    )}
                    {selectedStrategy === 'macd_momentum' && (
                      <>
                        <div>Fast Period: <span className="font-medium">{parameters.macd_fast}</span></div>
                        <div>Slow Period: <span className="font-medium">{parameters.macd_slow}</span></div>
                        <div>Signal Period: <span className="font-medium">{parameters.macd_signal}</span></div>
                      </>
                    )}
                    {selectedStrategy === 'bollinger_breakout' && (
                      <>
                        <div>Period: <span className="font-medium">{parameters.bb_period}</span></div>
                        <div>Standard Deviations: <span className="font-medium">{parameters.bb_std_dev}</span></div>
                      </>
                    )}
                  </div>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h6 className="font-medium text-gray-900 mb-2">Validation Criteria:</h6>
                  <div className="text-sm space-y-1 text-gray-600">
                    <div>• Sharpe Ratio &gt; 1.0</div>
                    <div>• Max Drawdown &lt; 15%</div>
                    <div>• Win Rate &gt; 45%</div>
                    <div>• 6+ months historical data</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}