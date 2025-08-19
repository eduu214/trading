'use client';

import { Opportunity } from '@/types/scanner';

interface ExportResultsProps {
  opportunities: Opportunity[];
}

export default function ExportResults({ opportunities }: ExportResultsProps) {
  const exportToJSON = () => {
    const dataStr = JSON.stringify(opportunities, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `scan_results_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const exportToCSV = () => {
    if (opportunities.length === 0) return;

    // CSV headers
    const headers = [
      'Ticker',
      'Asset Class',
      'Opportunity Type',
      'Signal Strength (%)',
      'Entry Price',
      'Price Change (%)',
      'Volume',
      'Inefficiency Score',
      'Discovered At'
    ];

    // Convert opportunities to CSV rows
    const rows = opportunities.map(opp => [
      opp.symbol,
      opp.asset_class,
      opp.strategy_type,
      opp.opportunity_score.toFixed(2),
      (opp.entry_conditions?.price || 0).toFixed(2),
      (opp.expected_return || 0).toFixed(2),
      opp.entry_conditions?.volume || opp.technical_indicators?.volume || '',
      (opp.technical_indicators?.inefficiency_score || 0).toFixed(2),
      new Date(opp.discovered_at).toLocaleString()
    ]);

    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `scan_results_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const copyToClipboard = () => {
    const summary = opportunities.map(opp => 
      `${opp.symbol} (${opp.asset_class}): ${opp.opportunity_score.toFixed(1)}% score, $${(opp.entry_conditions?.price || 0).toFixed(2)}`
    ).join('\n');

    navigator.clipboard.writeText(summary).then(() => {
      // Could add a toast notification here
      console.log('Copied to clipboard');
    });
  };

  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={exportToCSV}
        disabled={opportunities.length === 0}
        className={`flex items-center px-3 py-1.5 text-sm rounded ${
          opportunities.length > 0
            ? 'bg-green-600 text-white hover:bg-green-700'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Export CSV
      </button>
      
      <button
        onClick={exportToJSON}
        disabled={opportunities.length === 0}
        className={`flex items-center px-3 py-1.5 text-sm rounded ${
          opportunities.length > 0
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Export JSON
      </button>

      <button
        onClick={copyToClipboard}
        disabled={opportunities.length === 0}
        className={`flex items-center px-3 py-1.5 text-sm rounded ${
          opportunities.length > 0
            ? 'bg-gray-600 text-white hover:bg-gray-700'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        Copy
      </button>
    </div>
  );
}