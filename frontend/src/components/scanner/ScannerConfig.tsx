'use client';

import { useState } from 'react';
import { ScanConfig } from '@/types/scanner';
import AdvancedConfig from './AdvancedConfig';

interface ScannerConfigProps {
  onStartScan: (config: ScanConfig) => void;
  isScanning: boolean;
}

export default function ScannerConfig({ onStartScan, isScanning }: ScannerConfigProps) {
  const [config, setConfig] = useState<ScanConfig>({
    asset_classes: ['equities'],
    min_volume: 1000000,
    min_price_change: 0.02,
    correlation_threshold: 0.3,
    min_opportunity_score: 0.7,
    max_results: 20,
  });

  const assetClasses = [
    { id: 'equities', label: 'Equities', icon: '📈' },
    { id: 'futures', label: 'Futures', icon: '📊' },
    { id: 'fx', label: 'Forex', icon: '💱' },
  ];

  const handleAssetClassToggle = (assetClass: string) => {
    setConfig(prev => ({
      ...prev,
      asset_classes: prev.asset_classes.includes(assetClass)
        ? prev.asset_classes.filter(ac => ac !== assetClass)
        : [...prev.asset_classes, assetClass]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStartScan(config);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Scanner Configuration
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Asset Classes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Asset Classes
          </label>
          <div className="space-y-2">
            {assetClasses.map(ac => (
              <label key={ac.id} className="flex items-center">
                <input
                  type="checkbox"
                  checked={config.asset_classes.includes(ac.id)}
                  onChange={() => handleAssetClassToggle(ac.id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  disabled={isScanning}
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  <span className="mr-1">{ac.icon}</span>
                  {ac.label}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Min Volume */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Min Volume
          </label>
          <input
            type="number"
            value={config.min_volume}
            onChange={(e) => setConfig({ ...config, min_volume: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            disabled={isScanning}
          />
        </div>

        {/* Min Price Change */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Min Price Change (%)
          </label>
          <input
            type="number"
            step="0.01"
            value={config.min_price_change}
            onChange={(e) => setConfig({ ...config, min_price_change: parseFloat(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            disabled={isScanning}
          />
        </div>

        {/* Correlation Threshold */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Max Correlation
            <span className="ml-1 text-xs text-gray-500">(for uncorrelated pairs)</span>
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={config.correlation_threshold}
            onChange={(e) => setConfig({ ...config, correlation_threshold: parseFloat(e.target.value) })}
            className="w-full"
            disabled={isScanning}
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>0.0</span>
            <span className="font-medium">{config.correlation_threshold?.toFixed(1)}</span>
            <span>1.0</span>
          </div>
        </div>

        {/* Max Results */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Max Results
          </label>
          <select
            value={config.max_results}
            onChange={(e) => setConfig({ ...config, max_results: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            disabled={isScanning}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>

        {/* Advanced Configuration */}
        <AdvancedConfig config={config} onChange={setConfig} />

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isScanning || config.asset_classes.length === 0}
          className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
            isScanning || config.asset_classes.length === 0
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
          }`}
        >
          {isScanning ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Scanning...
            </span>
          ) : (
            'Start Scan'
          )}
        </button>
      </form>
    </div>
  );
}