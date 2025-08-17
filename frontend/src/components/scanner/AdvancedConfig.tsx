'use client';

import { useState } from 'react';

interface AdvancedConfigProps {
  config: any;
  onChange: (config: any) => void;
}

export default function AdvancedConfig({ config, onChange }: AdvancedConfigProps) {
  const [isOpen, setIsOpen] = useState(false);

  const inefficiencyTypes = [
    { id: 'price_deviation', label: 'Price Deviation', description: 'Detect when price deviates from moving average' },
    { id: 'volume_spike', label: 'Volume Spike', description: 'Identify unusual volume patterns' },
    { id: 'momentum_shift', label: 'Momentum Shift', description: 'RSI-based momentum changes' },
    { id: 'spread_anomaly', label: 'Spread Anomaly', description: 'Unusual bid-ask spreads' },
    { id: 'support_resistance', label: 'Support/Resistance', description: 'Breakout from key levels' },
    { id: 'price_gap', label: 'Price Gaps', description: 'Gaps between sessions' },
  ];

  const timeframes = [
    { value: '1min', label: '1 Minute' },
    { value: '5min', label: '5 Minutes' },
    { value: '15min', label: '15 Minutes' },
    { value: '1hour', label: '1 Hour' },
    { value: '1day', label: '1 Day' },
  ];

  return (
    <div className="mt-4 border-t border-gray-200 dark:border-gray-700 pt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-left"
      >
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Advanced Configuration
        </span>
        <svg
          className={`w-5 h-5 text-gray-500 transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="mt-4 space-y-4">
          {/* Inefficiency Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Inefficiency Detection
            </label>
            <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded-md p-2">
              {inefficiencyTypes.map(type => (
                <label key={type.id} className="flex items-start">
                  <input
                    type="checkbox"
                    checked={config.inefficiencyTypes?.includes(type.id) ?? true}
                    onChange={(e) => {
                      const types = config.inefficiencyTypes || inefficiencyTypes.map(t => t.id);
                      if (e.target.checked) {
                        onChange({ ...config, inefficiencyTypes: [...types, type.id] });
                      } else {
                        onChange({ ...config, inefficiencyTypes: types.filter((t: string) => t !== type.id) });
                      }
                    }}
                    className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="ml-2">
                    <span className="text-sm text-gray-700 dark:text-gray-300">{type.label}</span>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{type.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Timeframe */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Analysis Timeframe
            </label>
            <select
              value={config.timeframe || '1day'}
              onChange={(e) => onChange({ ...config, timeframe: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            >
              {timeframes.map(tf => (
                <option key={tf.value} value={tf.value}>{tf.label}</option>
              ))}
            </select>
          </div>

          {/* Lookback Period */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Lookback Period (days)
            </label>
            <input
              type="number"
              min="1"
              max="365"
              value={config.lookbackDays || 30}
              onChange={(e) => onChange({ ...config, lookbackDays: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          {/* Min Signal Strength */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Min Signal Strength
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="range"
                min="0"
                max="100"
                value={config.minSignalStrength || 60}
                onChange={(e) => onChange({ ...config, minSignalStrength: parseInt(e.target.value) })}
                className="flex-1"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400 w-12">
                {config.minSignalStrength || 60}%
              </span>
            </div>
          </div>

          {/* RSI Settings */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                RSI Oversold
              </label>
              <input
                type="number"
                min="0"
                max="50"
                value={config.rsiOversold || 30}
                onChange={(e) => onChange({ ...config, rsiOversold: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                RSI Overbought
              </label>
              <input
                type="number"
                min="50"
                max="100"
                value={config.rsiOverbought || 70}
                onChange={(e) => onChange({ ...config, rsiOverbought: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
          </div>

          {/* Z-Score Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Z-Score Threshold
              <span className="ml-1 text-xs text-gray-500">(for statistical significance)</span>
            </label>
            <input
              type="number"
              step="0.5"
              min="1"
              max="4"
              value={config.zscoreThreshold || 2}
              onChange={(e) => onChange({ ...config, zscoreThreshold: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>

          {/* Include Pre/Post Market */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="includeExtended"
              checked={config.includeExtendedHours || false}
              onChange={(e) => onChange({ ...config, includeExtendedHours: e.target.checked })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="includeExtended" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Include pre-market and after-hours data
            </label>
          </div>

          {/* Exclude Penny Stocks */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="excludePenny"
              checked={config.excludePennyStocks ?? true}
              onChange={(e) => onChange({ ...config, excludePennyStocks: e.target.checked })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="excludePenny" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Exclude penny stocks (price &lt; $5)
            </label>
          </div>
        </div>
      )}
    </div>
  );
}