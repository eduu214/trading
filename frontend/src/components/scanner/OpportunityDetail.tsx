'use client';

import { Opportunity } from '@/types/scanner';

interface OpportunityDetailProps {
  opportunity: Opportunity;
  onClose: () => void;
}

export default function OpportunityDetail({ opportunity, onClose }: OpportunityDetailProps) {
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block w-full max-w-2xl my-8 overflow-hidden text-left align-middle transition-all transform bg-white dark:bg-gray-800 shadow-xl rounded-lg">
          {/* Header */}
          <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {opportunity.symbol}
                </h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Opportunity Details
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-4">
            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Asset Class</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white capitalize">
                  {opportunity.asset_class}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Opportunity Type</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white capitalize">
                  {opportunity.strategy_type}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Opportunity Score</dt>
                <dd className="mt-1">
                  <div className="flex items-center">
                    <div className="flex-1 mr-2 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${Math.min(opportunity.opportunity_score, 100)}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {opportunity.opportunity_score.toFixed(1)}%
                    </span>
                  </div>
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Entry Price</dt>
                <dd className="mt-1 text-sm font-medium text-gray-900 dark:text-white">
                  ${(opportunity.entry_conditions?.price || 0).toFixed(2)}
                </dd>
              </div>
            </div>

            {/* Price & Volume Information */}
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Market Data
              </h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <dt className="text-xs text-gray-500 dark:text-gray-400">Expected Return</dt>
                  <dd className={`mt-1 text-sm font-medium ${
                    (opportunity.expected_return || 0) >= 0 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {(opportunity.expected_return || 0) >= 0 ? '+' : ''}
                    {(opportunity.expected_return || 0).toFixed(2)}%
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500 dark:text-gray-400">Volume</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                    {opportunity.entry_conditions?.volume?.toLocaleString() || 'N/A'}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500 dark:text-gray-400">Inefficiency Score</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                    {opportunity.technical_indicators?.inefficiency_score?.toFixed(1) || 'N/A'}
                  </dd>
                </div>
              </div>
            </div>

            {/* Inefficiency Analysis */}
            {opportunity.technical_indicators?.inefficiencies && opportunity.technical_indicators.inefficiencies.length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Detected Inefficiencies
                </h4>
                <div className="space-y-2">
                  {opportunity.technical_indicators.inefficiencies.slice(0, 3).map((inefficiency: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-900 rounded">
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {inefficiency.type}
                      </span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {inefficiency.strength?.toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Metadata */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Additional Information
              </h4>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500 dark:text-gray-400">Discovered At</dt>
                  <dd className="text-sm text-gray-900 dark:text-white">
                    {new Date(opportunity.discoveredAt).toLocaleString()}
                  </dd>
                </div>
                {opportunity.metadata?.spread && (
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500 dark:text-gray-400">Bid-Ask Spread</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">
                      {(opportunity.metadata.spread * 10000).toFixed(2)} bps
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600"
              >
                Close
              </button>
              <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
                Create Strategy
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}