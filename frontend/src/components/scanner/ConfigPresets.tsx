'use client';

import { useState, useEffect } from 'react';
import { ScanConfig } from '@/types/scanner';

interface ConfigPreset {
  id: string;
  name: string;
  description: string;
  config: ScanConfig;
  isDefault?: boolean;
}

interface ConfigPresetsProps {
  currentConfig: ScanConfig;
  onLoadPreset: (config: ScanConfig) => void;
}

export default function ConfigPresets({ currentConfig, onLoadPreset }: ConfigPresetsProps) {
  const [presets, setPresets] = useState<ConfigPreset[]>([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');
  const [newPresetDescription, setNewPresetDescription] = useState('');

  // Default presets
  const defaultPresets: ConfigPreset[] = [
    {
      id: 'aggressive',
      name: 'Aggressive Scanner',
      description: 'High volatility opportunities with lower thresholds',
      isDefault: true,
      config: {
        asset_classes: ['equities', 'futures', 'fx'],
        min_volume: 500000,
        min_price_change: 0.03,
        correlation_threshold: 0.5,
        min_opportunity_score: 0.6,
        max_results: 50,
      }
    },
    {
      id: 'conservative',
      name: 'Conservative Scanner',
      description: 'Stable opportunities with strict filters',
      isDefault: true,
      config: {
        asset_classes: ['equities'],
        min_volume: 2000000,
        min_price_change: 0.01,
        correlation_threshold: 0.2,
        min_opportunity_score: 0.8,
        max_results: 10,
      }
    },
    {
      id: 'momentum',
      name: 'Momentum Hunter',
      description: 'Focus on high momentum moves',
      isDefault: true,
      config: {
        asset_classes: ['equities', 'futures'],
        min_volume: 1000000,
        min_price_change: 0.05,
        correlation_threshold: 0.4,
        min_opportunity_score: 0.7,
        max_results: 20,
      }
    },
    {
      id: 'fx_focus',
      name: 'Forex Specialist',
      description: 'Optimized for currency pair trading',
      isDefault: true,
      config: {
        asset_classes: ['fx'],
        min_volume: 10000,
        min_price_change: 0.005,
        correlation_threshold: 0.3,
        min_opportunity_score: 0.65,
        max_results: 15,
      }
    },
  ];

  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = () => {
    // Load custom presets from localStorage
    const savedPresets = localStorage.getItem('scannerPresets');
    const customPresets = savedPresets ? JSON.parse(savedPresets) : [];
    setPresets([...defaultPresets, ...customPresets]);
  };

  const savePreset = () => {
    if (!newPresetName.trim()) return;

    const newPreset: ConfigPreset = {
      id: `custom_${Date.now()}`,
      name: newPresetName,
      description: newPresetDescription,
      config: currentConfig,
      isDefault: false,
    };

    // Get existing custom presets
    const savedPresets = localStorage.getItem('scannerPresets');
    const customPresets = savedPresets ? JSON.parse(savedPresets) : [];
    
    // Add new preset
    const updatedPresets = [...customPresets, newPreset];
    localStorage.setItem('scannerPresets', JSON.stringify(updatedPresets));
    
    // Update state
    setPresets([...defaultPresets, ...updatedPresets]);
    
    // Reset form
    setNewPresetName('');
    setNewPresetDescription('');
    setShowSaveDialog(false);
  };

  const deletePreset = (presetId: string) => {
    // Can only delete custom presets
    const savedPresets = localStorage.getItem('scannerPresets');
    const customPresets = savedPresets ? JSON.parse(savedPresets) : [];
    const filtered = customPresets.filter((p: ConfigPreset) => p.id !== presetId);
    localStorage.setItem('scannerPresets', JSON.stringify(filtered));
    setPresets([...defaultPresets, ...filtered]);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Configuration Presets
        </h3>
        <button
          onClick={() => setShowSaveDialog(true)}
          className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
        >
          Save Current
        </button>
      </div>

      <div className="space-y-2">
        {presets.map((preset) => (
          <div
            key={preset.id}
            className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                    {preset.name}
                  </h4>
                  {preset.isDefault && (
                    <span className="ml-2 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded">
                      Default
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {preset.description}
                </p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {preset.config.asset_classes.map(ac => (
                    <span key={ac} className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300 px-2 py-0.5 rounded">
                      {ac}
                    </span>
                  ))}
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Vol: {(preset.config.min_volume || 0).toLocaleString()}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Change: {((preset.config.min_price_change || 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-2 ml-4">
                <button
                  onClick={() => onLoadPreset(preset.config)}
                  className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Load
                </button>
                {!preset.isDefault && (
                  <button
                    onClick={() => deletePreset(preset.id)}
                    className="text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Save Configuration Preset
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Preset Name
                </label>
                <input
                  type="text"
                  value={newPresetName}
                  onChange={(e) => setNewPresetName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  placeholder="My Custom Scanner"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={newPresetDescription}
                  onChange={(e) => setNewPresetDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  rows={2}
                  placeholder="Describe this configuration..."
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setShowSaveDialog(false)}
                  className="px-4 py-2 text-sm text-gray-700 bg-gray-200 rounded hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
                >
                  Cancel
                </button>
                <button
                  onClick={savePreset}
                  className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}