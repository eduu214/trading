/**
 * Data Quality Validation Component
 * F002-US001 Slice 3 Task 17: Data quality validation interface
 * Displays data quality validation results with gap analysis and recommendations
 */

import React, { useState } from 'react';

// Simple SVG icons to replace heroicons
const CheckCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ExclamationTriangleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const XCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const InformationCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ChartBarIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const ClockIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-5 w-5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

interface DataQualitySummary {
  total_days: number;
  trading_days: number;
  data_completeness: number;
  start_date: string;
  end_date: string;
  gaps_detected: number;
  critical_gaps: number;
}

interface ValidationDetails {
  period_check?: string;
  trading_days_check?: string;
  gap_analysis?: {
    total_gaps: number;
    critical_gaps: number;
    max_gap_days: number;
    gap_details: Array<{
      start_date: string;
      end_date: string;
      days: number;
      is_critical: boolean;
    }>;
  };
  integrity_check?: {
    valid: boolean;
    issues: string[];
  };
  summary?: DataQualitySummary;
}

interface DataQualityResult {
  passed: boolean;
  data_source: string;
  summary: DataQualitySummary;
  errors: string[];
  warnings: string[];
}

interface DataQualityValidatorProps {
  symbol?: string;
  onValidate?: (symbol: string) => Promise<{
    data_quality: DataQualityResult;
    validation_details: ValidationDetails;
    recommendation: string;
  }>;
}

export default function DataQualityValidator({
  symbol: initialSymbol = "AAPL",
  onValidate
}: DataQualityValidatorProps) {
  const [symbol, setSymbol] = useState(initialSymbol);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    data_quality: DataQualityResult;
    validation_details: ValidationDetails;
    recommendation: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleValidate = async () => {
    if (!onValidate) {
      setError("Validation function not provided");
      return;
    }

    setIsValidating(true);
    setError(null);
    setValidationResult(null);

    try {
      const result = await onValidate(symbol.toUpperCase());
      setValidationResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setIsValidating(false);
    }
  };

  const getStatusIcon = (passed: boolean) => {
    if (passed) {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    }
    return <XCircleIcon className="h-5 w-5 text-red-500" />;
  };

  const getGapSeverityColor = (isCritical: boolean) => {
    return isCritical ? "text-red-600 bg-red-50" : "text-yellow-600 bg-yellow-50";
  };

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Data Quality Validation</h3>
            <p className="mt-1 text-sm text-gray-500">
              Validate market data quality for backtesting requirements
            </p>
          </div>
          <ChartBarIcon className="h-8 w-8 text-gray-400" />
        </div>
      </div>

      <div className="p-6">
        {/* Input Section */}
        <div className="mb-6">
          <div className="flex space-x-4">
            <div className="flex-1">
              <label htmlFor="symbol" className="block text-sm font-medium text-gray-700">
                Symbol
              </label>
              <input
                type="text"
                id="symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter symbol (e.g., AAPL)"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={handleValidate}
                disabled={isValidating || !symbol.trim()}
                className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isValidating ? "Validating..." : "Validate"}
              </button>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <XCircleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Validation Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isValidating && (
          <div className="text-center py-8">
            <ClockIcon className="mx-auto h-8 w-8 text-gray-400 animate-spin" />
            <p className="mt-2 text-sm text-gray-500">Validating data quality...</p>
          </div>
        )}

        {/* Results Display */}
        {validationResult && (
          <div className="space-y-6">
            {/* Overall Status */}
            <div className={`rounded-md p-4 ${
              validationResult.data_quality.passed 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex">
                {getStatusIcon(validationResult.data_quality.passed)}
                <div className="ml-3">
                  <h3 className={`text-sm font-medium ${
                    validationResult.data_quality.passed ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {validationResult.data_quality.passed ? 'Data Quality Passed' : 'Data Quality Failed'}
                  </h3>
                  <div className={`mt-2 text-sm ${
                    validationResult.data_quality.passed ? 'text-green-700' : 'text-red-700'
                  }`}>
                    <p>{validationResult.recommendation}</p>
                    <p className="mt-1">
                      <strong>Data Source:</strong> {validationResult.data_quality.data_source}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Summary Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Trading Days</div>
                <div className="text-2xl font-semibold text-gray-900">
                  {validationResult.data_quality.summary.trading_days}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Data Completeness</div>
                <div className="text-2xl font-semibold text-gray-900">
                  {validationResult.data_quality.summary.data_completeness.toFixed(1)}%
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Gaps Detected</div>
                <div className="text-2xl font-semibold text-gray-900">
                  {validationResult.data_quality.summary.gaps_detected}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-500">Critical Gaps</div>
                <div className="text-2xl font-semibold text-gray-900">
                  {validationResult.data_quality.summary.critical_gaps}
                </div>
              </div>
            </div>

            {/* Errors */}
            {validationResult.data_quality.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <XCircleIcon className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Quality Errors</h3>
                    <div className="mt-2 text-sm text-red-700">
                      <ul className="list-disc list-inside space-y-1">
                        {validationResult.data_quality.errors.map((error, index) => (
                          <li key={index}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Warnings */}
            {validationResult.data_quality.warnings.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <div className="flex">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800">Quality Warnings</h3>
                    <div className="mt-2 text-sm text-yellow-700">
                      <ul className="list-disc list-inside space-y-1">
                        {validationResult.data_quality.warnings.map((warning, index) => (
                          <li key={index}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Gap Analysis Details */}
            {validationResult.validation_details.gap_analysis && 
             validationResult.validation_details.gap_analysis.gap_details.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Data Gap Analysis</h4>
                <div className="space-y-2">
                  {validationResult.validation_details.gap_analysis.gap_details.map((gap, index) => (
                    <div 
                      key={index}
                      className={`p-3 rounded-md border ${getGapSeverityColor(gap.is_critical)}`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">
                          {gap.is_critical ? 'Critical Gap' : 'Minor Gap'}: {gap.days} days
                        </span>
                        <span className="text-xs">
                          {new Date(gap.start_date).toLocaleDateString()} - {new Date(gap.end_date).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Data Integrity Issues */}
            {validationResult.validation_details.integrity_check && 
             !validationResult.validation_details.integrity_check.valid && (
              <div className="bg-orange-50 border border-orange-200 rounded-md p-4">
                <div className="flex">
                  <ExclamationTriangleIcon className="h-5 w-5 text-orange-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-orange-800">Data Integrity Issues</h3>
                    <div className="mt-2 text-sm text-orange-700">
                      <ul className="list-disc list-inside space-y-1">
                        {validationResult.validation_details.integrity_check.issues.map((issue, index) => (
                          <li key={index}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Recommendations */}
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex">
                <InformationCircleIcon className="h-5 w-5 text-blue-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">Data Quality Requirements</h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <ul className="list-disc list-inside space-y-1">
                      <li>Minimum 6 months (180 days) of historical data</li>
                      <li>At least 120 trading days for statistical validity</li>
                      <li>Maximum 5 consecutive days of missing data</li>
                      <li>Valid OHLCV price relationships (High ≥ Low, Close within range)</li>
                      <li>No extreme price movements (&gt;50% daily changes)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}