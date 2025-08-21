/**
 * Strategy Approval Component
 * F002-US001 Task 20: Strategy Approval Workflow
 * 
 * Implements:
 * - Approval interface with confirmation modal 
 * - Transition to paper trading with audit trail
 * - Toast notifications for approval status
 * - Button states per design tokens
 */

import React, { useState } from 'react';

// Simple SVG icons to replace heroicons
const CheckCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-6 w-6"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ExclamationTriangleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-6 w-6"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const InformationCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-6 w-6"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const XMarkIcon = ({ className }: { className?: string }) => (
  <svg className={className || "h-6 w-6"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

interface StrategyApprovalProps {
  strategy: {
    id: string;
    name: string;
    symbol: string;
    performance: {
      sharpe_ratio: number;
      total_return: number;
      max_drawdown: number;
      win_rate: number;
    };
  };
  onApprove: (strategyId: string, approvalData: ApprovalData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

interface ApprovalData {
  approved_by: string;
  approval_date: string;
  paper_trading_enabled: boolean;
  initial_capital: number;
  risk_limit: number;
  notes?: string;
}

interface ToastNotification {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  visible: boolean;
}

export default function StrategyApproval({ 
  strategy, 
  onApprove, 
  onCancel, 
  isLoading = false 
}: StrategyApprovalProps) {
  const [showModal, setShowModal] = useState(false);
  const [approvalData, setApprovalData] = useState<Partial<ApprovalData>>({
    approved_by: 'Admin', // Would come from auth context in real app
    paper_trading_enabled: true,
    initial_capital: 10000,
    risk_limit: 2, // 2% max risk per trade
    notes: ''
  });
  const [toast, setToast] = useState<ToastNotification>({
    type: 'info',
    title: '',
    message: '',
    visible: false
  });

  const showToast = (type: ToastNotification['type'], title: string, message: string) => {
    setToast({ type, title, message, visible: true });
    setTimeout(() => {
      setToast(prev => ({ ...prev, visible: false }));
    }, 5000);
  };

  const handleApproveClick = () => {
    setShowModal(true);
  };

  const handleConfirmApproval = async () => {
    try {
      const fullApprovalData: ApprovalData = {
        approved_by: approvalData.approved_by || 'Admin',
        approval_date: new Date().toISOString(),
        paper_trading_enabled: approvalData.paper_trading_enabled || true,
        initial_capital: approvalData.initial_capital || 10000,
        risk_limit: approvalData.risk_limit || 2,
        notes: approvalData.notes || ''
      };

      await onApprove(strategy.id, fullApprovalData);
      
      setShowModal(false);
      showToast(
        'success',
        'Strategy Approved',
        `${strategy.name} has been approved for paper trading with $${fullApprovalData.initial_capital.toLocaleString()} initial capital.`
      );
    } catch (error) {
      showToast(
        'error',
        'Approval Failed',
        'An error occurred while approving the strategy. Please try again.'
      );
    }
  };

  const handleModalCancel = () => {
    setShowModal(false);
  };

  // Validation checks
  const validationChecks = [
    {
      label: 'Sharpe Ratio > 1.0',
      passed: strategy.performance.sharpe_ratio > 1.0,
      value: strategy.performance.sharpe_ratio.toFixed(2)
    },
    {
      label: 'Max Drawdown < 15%',
      passed: strategy.performance.max_drawdown < 15,
      value: `${strategy.performance.max_drawdown.toFixed(1)}%`
    },
    {
      label: 'Win Rate > 45%',
      passed: strategy.performance.win_rate > 45,
      value: `${strategy.performance.win_rate.toFixed(1)}%`
    },
    {
      label: 'Positive Total Return',
      passed: strategy.performance.total_return > 0,
      value: `${strategy.performance.total_return.toFixed(1)}%`
    }
  ];

  const allValidationsPassed = validationChecks.every(check => check.passed);

  return (
    <>
      {/* Main Approval Interface */}
      <div className="bg-white shadow rounded-lg">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Strategy Approval</h3>
          <p className="mt-1 text-sm text-gray-500">
            Review and approve {strategy.name} for paper trading deployment
          </p>
        </div>

        <div className="p-6">
          {/* Validation Summary */}
          <div className={`border rounded-lg p-4 mb-6 ${
            allValidationsPassed 
              ? 'bg-green-50 border-green-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center">
              {allValidationsPassed ? (
                <CheckCircleIcon className="h-5 w-5 text-green-400 mr-3" />
              ) : (
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-3" />
              )}
              <div>
                <h4 className={`font-medium ${allValidationsPassed ? 'text-green-800' : 'text-red-800'}`}>
                  {allValidationsPassed ? 'All Validations Passed' : 'Validation Issues Detected'}
                </h4>
                <p className={`text-sm mt-1 ${allValidationsPassed ? 'text-green-700' : 'text-red-700'}`}>
                  {allValidationsPassed 
                    ? 'Strategy meets all performance thresholds and is ready for deployment.'
                    : 'Strategy does not meet minimum performance requirements for approval.'
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Validation Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {validationChecks.map((check, index) => (
              <div key={index} className={`border rounded-lg p-4 ${
                check.passed 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${
                      check.passed ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {check.label}
                    </p>
                    <p className={`text-lg font-bold mt-1 ${
                      check.passed ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {check.value}
                    </p>
                  </div>
                  {check.passed ? (
                    <CheckCircleIcon className="h-6 w-6 text-green-600" />
                  ) : (
                    <XMarkIcon className="h-6 w-6 text-red-600" />
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Strategy Details */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Strategy Details</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Strategy Name</span>
                <p className="font-medium">{strategy.name}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Symbol</span>
                <p className="font-medium">{strategy.symbol}</p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-4">
            {allValidationsPassed ? (
              <button
                onClick={handleApproveClick}
                disabled={isLoading}
                className="flex-1 bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {isLoading ? 'Approving...' : 'Approve for Paper Trading'}
              </button>
            ) : (
              <div className="flex-1 bg-gray-100 text-gray-400 py-3 px-4 rounded-md text-center font-medium">
                Strategy Validation Required
              </div>
            )}
            
            <button
              onClick={onCancel}
              className="flex-1 bg-white border border-gray-300 text-gray-700 py-3 px-4 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium transition-colors duration-200"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-lg shadow-lg rounded-md bg-white">
            <div className="mt-3">
              {/* Modal Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Confirm Strategy Approval
                </h3>
                <button
                  onClick={handleModalCancel}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div className="flex">
                    <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5" />
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-blue-800">
                        Paper Trading Deployment
                      </h4>
                      <p className="mt-1 text-sm text-blue-700">
                        This strategy will be deployed to paper trading environment with simulated capital.
                        No real money will be at risk.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Configuration Options */}
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Initial Paper Trading Capital
                    </label>
                    <input
                      type="number"
                      value={approvalData.initial_capital}
                      onChange={(e) => setApprovalData(prev => ({ 
                        ...prev, 
                        initial_capital: Number(e.target.value) 
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      min="1000"
                      step="1000"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Maximum Risk Per Trade (%)
                    </label>
                    <input
                      type="number"
                      value={approvalData.risk_limit}
                      onChange={(e) => setApprovalData(prev => ({ 
                        ...prev, 
                        risk_limit: Number(e.target.value) 
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      min="0.5"
                      max="10"
                      step="0.5"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Approval Notes (Optional)
                    </label>
                    <textarea
                      value={approvalData.notes}
                      onChange={(e) => setApprovalData(prev => ({ 
                        ...prev, 
                        notes: e.target.value 
                      }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      rows={2}
                      placeholder="Add any notes about this approval..."
                    />
                  </div>
                </div>

                {/* Audit Trail Info */}
                <div className="bg-gray-50 rounded-md p-3">
                  <h5 className="text-sm font-medium text-gray-900 mb-2">Audit Trail</h5>
                  <div className="text-xs text-gray-600 space-y-1">
                    <p>Approved by: {approvalData.approved_by}</p>
                    <p>Approval time: {new Date().toLocaleString()}</p>
                    <p>Strategy: {strategy.name} ({strategy.symbol})</p>
                  </div>
                </div>
              </div>

              {/* Modal Actions */}
              <div className="mt-6 flex space-x-3">
                <button
                  onClick={handleConfirmApproval}
                  disabled={isLoading}
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Deploying...' : 'Confirm Approval'}
                </button>
                <button
                  onClick={handleModalCancel}
                  className="flex-1 bg-white border border-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast.visible && (
        <div className="fixed bottom-4 right-4 z-50">
          <div className={`max-w-sm w-full shadow-lg rounded-lg pointer-events-auto overflow-hidden ${
            toast.type === 'success' ? 'bg-green-50 border border-green-200' :
            toast.type === 'error' ? 'bg-red-50 border border-red-200' :
            toast.type === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
            'bg-blue-50 border border-blue-200'
          }`}>
            <div className="p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  {toast.type === 'success' && <CheckCircleIcon className="h-6 w-6 text-green-400" />}
                  {toast.type === 'error' && <XMarkIcon className="h-6 w-6 text-red-400" />}
                  {toast.type === 'warning' && <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400" />}
                  {toast.type === 'info' && <InformationCircleIcon className="h-6 w-6 text-blue-400" />}
                </div>
                <div className="ml-3 w-0 flex-1">
                  <p className={`text-sm font-medium ${
                    toast.type === 'success' ? 'text-green-800' :
                    toast.type === 'error' ? 'text-red-800' :
                    toast.type === 'warning' ? 'text-yellow-800' :
                    'text-blue-800'
                  }`}>
                    {toast.title}
                  </p>
                  <p className={`mt-1 text-sm ${
                    toast.type === 'success' ? 'text-green-700' :
                    toast.type === 'error' ? 'text-red-700' :
                    toast.type === 'warning' ? 'text-yellow-700' :
                    'text-blue-700'
                  }`}>
                    {toast.message}
                  </p>
                </div>
                <div className="ml-4 flex-shrink-0 flex">
                  <button
                    onClick={() => setToast(prev => ({ ...prev, visible: false }))}
                    className={`rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                      toast.type === 'success' ? 'focus:ring-green-500' :
                      toast.type === 'error' ? 'focus:ring-red-500' :
                      toast.type === 'warning' ? 'focus:ring-yellow-500' :
                      'focus:ring-blue-500'
                    }`}
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}