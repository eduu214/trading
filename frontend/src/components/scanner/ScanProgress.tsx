'use client';

import { useEffect, useState } from 'react';

interface ScanProgressProps {
  taskId: string | null;
}

export default function ScanProgress({ taskId }: ScanProgressProps) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Initializing scan...');
  const [assetsScanned, setAssetsScanned] = useState({
    equities: false,
    futures: false,
    fx: false,
  });

  useEffect(() => {
    // Simulate progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 500);

    // Simulate asset scanning
    setTimeout(() => {
      setStatus('Scanning equities...');
      setAssetsScanned(prev => ({ ...prev, equities: true }));
    }, 1000);

    setTimeout(() => {
      setStatus('Scanning futures...');
      setAssetsScanned(prev => ({ ...prev, futures: true }));
    }, 2000);

    setTimeout(() => {
      setStatus('Scanning forex pairs...');
      setAssetsScanned(prev => ({ ...prev, fx: true }));
    }, 3000);

    setTimeout(() => {
      setStatus('Analyzing correlations...');
    }, 4000);

    setTimeout(() => {
      setStatus('Ranking opportunities...');
    }, 4500);

    return () => clearInterval(interval);
  }, [taskId]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Scanning Markets
          </h3>
          <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
            {progress}%
          </span>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 mb-3">
          <div 
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Status Message */}
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {status}
        </p>

        {/* Asset Class Progress */}
        <div className="grid grid-cols-3 gap-4">
          <div className="flex items-center space-x-2">
            <div className={`w-4 h-4 rounded-full ${
              assetsScanned.equities ? 'bg-green-500' : 'bg-gray-300 animate-pulse'
            }`} />
            <span className="text-sm text-gray-700 dark:text-gray-300">Equities</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-4 h-4 rounded-full ${
              assetsScanned.futures ? 'bg-green-500' : 'bg-gray-300 animate-pulse'
            }`} />
            <span className="text-sm text-gray-700 dark:text-gray-300">Futures</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-4 h-4 rounded-full ${
              assetsScanned.fx ? 'bg-green-500' : 'bg-gray-300 animate-pulse'
            }`} />
            <span className="text-sm text-gray-700 dark:text-gray-300">Forex</span>
          </div>
        </div>
      </div>

      {/* Live Updates (simulated) */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Live Updates
        </h4>
        <div className="space-y-1 text-xs text-gray-500 dark:text-gray-400 max-h-20 overflow-y-auto">
          <div>• Found 5 opportunities in NASDAQ stocks</div>
          <div>• Analyzing micro futures correlations</div>
          <div>• EUR/USD showing momentum signal</div>
          <div>• Detected volume spike in AAPL</div>
        </div>
      </div>
    </div>
  );
}