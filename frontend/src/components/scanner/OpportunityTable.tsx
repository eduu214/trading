'use client';

import { useState, useMemo } from 'react';
import { Opportunity } from '@/types/scanner';

interface OpportunityTableProps {
  opportunities: Opportunity[];
  onSelectOpportunity: (opportunity: Opportunity) => void;
}

type SortKey = 'symbol' | 'opportunity_score' | 'expected_return' | 'volume' | 'asset_class';

export default function OpportunityTable({ opportunities, onSelectOpportunity }: OpportunityTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('opportunity_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  const sortedOpportunities = useMemo(() => {
    return [...opportunities].sort((a, b) => {
      let aVal: any = a[sortKey as keyof Opportunity];
      let bVal: any = b[sortKey as keyof Opportunity];

      if (sortKey === 'expected_return') {
        aVal = a.expected_return || 0;
        bVal = b.expected_return || 0;
      }

      if (sortKey === 'volume') {
        aVal = a.entry_conditions?.volume || 0;
        bVal = b.entry_conditions?.volume || 0;
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }, [opportunities, sortKey, sortOrder]);

  const getAssetClassBadge = (assetClass: string) => {
    const badges = {
      equities: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      futures: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
      fx: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    };
    return badges[assetClass as keyof typeof badges] || 'bg-gray-100 text-gray-800';
  };

  const getOpportunityTypeBadge = (type: string) => {
    const badges = {
      momentum: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
      reversal: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
      breakout: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300',
    };
    return badges[type as keyof typeof badges] || 'bg-gray-100 text-gray-800';
  };

  const getSignalStrengthColor = (strength: number) => {
    if (strength >= 80) return 'text-green-600 dark:text-green-400';
    if (strength >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Trading Opportunities
        </h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {opportunities.length} opportunities found
        </p>
      </div>

      <div className="w-full">
        <table className="w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th 
                onClick={() => handleSort('symbol')}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-700 dark:hover:text-gray-200 w-24"
              >
                <div className="flex items-center">
                  Symbol
                  {sortKey === 'symbol' && (
                    <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th 
                onClick={() => handleSort('asset_class')}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-700 dark:hover:text-gray-200 w-32"
              >
                <div className="flex items-center">
                  Asset Class
                  {sortKey === 'asset_class' && (
                    <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-28">
                Type
              </th>
              <th 
                onClick={() => handleSort('opportunity_score')}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-700 dark:hover:text-gray-200 w-40"
              >
                <div className="flex items-center">
                  Score
                  {sortKey === 'opportunity_score' && (
                    <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th 
                onClick={() => handleSort('expected_return')}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-700 dark:hover:text-gray-200 w-28"
              >
                <div className="flex items-center">
                  Return %
                  {sortKey === 'expected_return' && (
                    <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th 
                onClick={() => handleSort('volume')}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-700 dark:hover:text-gray-200 w-32"
              >
                <div className="flex items-center">
                  Volume
                  {sortKey === 'volume' && (
                    <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-28">
                Entry Price
              </th>
              <th className="relative px-4 py-3 w-20">
                <span className="sr-only">View</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {sortedOpportunities.map((opportunity) => (
              <tr 
                key={opportunity.id} 
                className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                onClick={() => onSelectOpportunity(opportunity)}
              >
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {opportunity.symbol}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getAssetClassBadge(opportunity.asset_class)}`}>
                    {opportunity.asset_class}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getOpportunityTypeBadge(opportunity.strategy_type)}`}>
                    {opportunity.strategy_type}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="mr-2 w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${Math.min(opportunity.opportunity_score, 100)}%` }}
                      />
                    </div>
                    <span className={`text-sm font-medium ${getSignalStrengthColor(opportunity.opportunity_score)}`}>
                      {opportunity.opportunity_score.toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`text-sm font-medium ${
                    (opportunity.expected_return || 0) >= 0 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {(opportunity.expected_return || 0) >= 0 ? '+' : ''}
                    {(opportunity.expected_return || 0).toFixed(2)}%
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {opportunity.entry_conditions?.volume?.toLocaleString() || '-'}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  ${(opportunity.entry_conditions?.price || 0).toFixed(2)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                  <button className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300">
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}