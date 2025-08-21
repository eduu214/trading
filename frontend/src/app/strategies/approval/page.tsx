/**
 * Strategy Approval Demo Page
 * F002-US001 Task 20: Strategy Approval Workflow
 * 
 * Demonstrates:
 * - Strategy approval interface with validation
 * - Confirmation modal with audit trail
 * - Paper trading transition workflow
 * - Toast notifications for approval status
 */

'use client';

import React, { useState } from 'react';
import { StrategyApproval } from '@/components/strategies';

// Mock strategy data for demonstration
const MOCK_STRATEGIES = [
  {
    id: 'rsi_mean_reversion',
    name: 'RSI Mean Reversion',
    symbol: 'AAPL',
    performance: {
      sharpe_ratio: 1.45,
      total_return: 12.3,
      max_drawdown: 8.5,
      win_rate: 67.8
    }
  },
  {
    id: 'macd_momentum',
    name: 'MACD Momentum',
    symbol: 'TSLA',
    performance: {
      sharpe_ratio: 0.85,
      total_return: 8.7,
      max_drawdown: 18.2,
      win_rate: 52.1
    }
  },
  {
    id: 'bollinger_breakout',
    name: 'Bollinger Band Breakout',
    symbol: 'NVDA',
    performance: {
      sharpe_ratio: 1.78,
      total_return: 24.6,
      max_drawdown: 6.3,
      win_rate: 71.4
    }
  }
];

interface ApprovalData {
  approved_by: string;
  approval_date: string;
  paper_trading_enabled: boolean;
  initial_capital: number;
  risk_limit: number;
  notes?: string;
}

export default function StrategyApprovalPage() {
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>('rsi_mean_reversion');
  const [isLoading, setIsLoading] = useState(false);
  const [approvalResults, setApprovalResults] = useState<any>(null);

  const selectedStrategy = MOCK_STRATEGIES.find(s => s.id === selectedStrategyId);

  const handleApprove = async (strategyId: string, approvalData: ApprovalData) => {
    setIsLoading(true);
    
    try {
      // Call backend API to approve strategy
      const response = await fetch(`http://localhost:8000/api/v1/strategies/${strategyId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(approvalData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setApprovalResults(result);
      
      console.log('Strategy approved:', result);
    } catch (error) {
      console.error('Approval failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    console.log('Approval cancelled');
    setApprovalResults(null);
  };

  const handleStrategyChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedStrategyId(event.target.value);
    setApprovalResults(null);
  };

  if (!selectedStrategy) {
    return <div>Strategy not found</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Strategy Approval Workflow</h1>
          <p className="mt-2 text-lg text-gray-600">
            Task 20: Approval interface with confirmation modal and paper trading transition
          </p>
        </div>

        {/* Strategy Selection */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Select Strategy for Approval</h2>
          <div className="flex items-center space-x-4">
            <label htmlFor="strategy-select" className="text-sm font-medium text-gray-700">
              Strategy:
            </label>
            <select
              id="strategy-select"
              value={selectedStrategyId}
              onChange={handleStrategyChange}
              className="block w-64 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              {MOCK_STRATEGIES.map((strategy) => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.name} ({strategy.symbol})
                </option>
              ))}
            </select>
          </div>
          
          {/* Strategy Performance Preview */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Sharpe Ratio</div>
              <div className={`text-lg font-semibold ${
                selectedStrategy.performance.sharpe_ratio > 1.0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {selectedStrategy.performance.sharpe_ratio.toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Total Return</div>
              <div className={`text-lg font-semibold ${
                selectedStrategy.performance.total_return > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {selectedStrategy.performance.total_return.toFixed(1)}%
              </div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Max Drawdown</div>
              <div className={`text-lg font-semibold ${
                selectedStrategy.performance.max_drawdown < 15 ? 'text-green-600' : 'text-red-600'
              }`}>
                {selectedStrategy.performance.max_drawdown.toFixed(1)}%
              </div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm text-gray-600">Win Rate</div>
              <div className={`text-lg font-semibold ${
                selectedStrategy.performance.win_rate > 45 ? 'text-green-600' : 'text-red-600'
              }`}>
                {selectedStrategy.performance.win_rate.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>

        {/* Approval Results Display */}
        {approvalResults && (
          <div className="bg-white shadow rounded-lg p-6 mb-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <svg className="h-5 w-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Approval Successful
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Approval Details */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Approval Details</h3>
                <div className="space-y-2 text-sm">
                  <div><span className="text-gray-600">Approval ID:</span> {approvalResults.approval_id}</div>
                  <div><span className="text-gray-600">Strategy:</span> {approvalResults.audit_trail.strategy_id}</div>
                  <div><span className="text-gray-600">Approved By:</span> {approvalResults.audit_trail.approved_by}</div>
                  <div><span className="text-gray-600">Approval Date:</span> {new Date(approvalResults.audit_trail.approval_date).toLocaleString()}</div>
                  <div><span className="text-gray-600">Status:</span> 
                    <span className="ml-1 inline-flex px-2 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded-full">
                      {approvalResults.audit_trail.status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Paper Trading Config */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Paper Trading Deployment</h3>
                <div className="space-y-2 text-sm">
                  <div><span className="text-gray-600">Deployment ID:</span> {approvalResults.paper_trading.deployment_id}</div>
                  <div><span className="text-gray-600">Environment:</span> {approvalResults.paper_trading.environment}</div>
                  <div><span className="text-gray-600">Initial Capital:</span> ${approvalResults.paper_trading.initial_capital.toLocaleString()}</div>
                  <div><span className="text-gray-600">Status:</span> 
                    <span className="ml-1 inline-flex px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded-full">
                      {approvalResults.paper_trading.status}
                    </span>
                  </div>
                  <div><span className="text-gray-600">Deployed:</span> {new Date(approvalResults.paper_trading.deployed_at).toLocaleString()}</div>
                </div>
              </div>
            </div>

            {/* Next Steps */}
            <div className="mt-6">
              <h3 className="font-medium text-gray-900 mb-3">Next Steps</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                {approvalResults.next_steps.map((step: string, index: number) => (
                  <li key={index}>{step}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Strategy Approval Component */}
        <StrategyApproval
          strategy={selectedStrategy}
          onApprove={handleApprove}
          onCancel={handleCancel}
          isLoading={isLoading}
        />

        {/* Implementation Details */}
        <div className="mt-8 bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Implementation Details</h2>
          <div className="prose prose-sm text-gray-600">
            <p className="mb-4">
              <strong>Task 20: Strategy Approval Workflow</strong> - This interface demonstrates the complete approval workflow including:
            </p>
            <ul className="list-disc list-inside space-y-2 mb-4">
              <li><strong>Validation Checks:</strong> Automated validation against performance thresholds (Sharpe &gt; 1.0, Drawdown &lt; 15%, etc.)</li>
              <li><strong>Confirmation Modal:</strong> Modal dialog with deployment configuration options and audit trail preview</li>
              <li><strong>Paper Trading Transition:</strong> Automatic deployment to paper trading environment with risk controls</li>
              <li><strong>Audit Trail:</strong> Complete audit log with approval ID, timestamps, and configuration details</li>
              <li><strong>Toast Notifications:</strong> Real-time feedback for approval status with proper error handling</li>
              <li><strong>Button States:</strong> Loading states and disabled states per design token specifications</li>
            </ul>
            <p>
              The workflow follows the UX specifications from the design documents, implementing proper color coding, 
              hover effects, and transitions as defined in the design tokens.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}