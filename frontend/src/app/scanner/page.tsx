'use client';

import { useState } from 'react';
import ScannerConfig from '@/components/scanner/ScannerConfig';
import ScanProgress from '@/components/scanner/ScanProgress';
import OpportunityTable from '@/components/scanner/OpportunityTable';
import OpportunityDetail from '@/components/scanner/OpportunityDetail';
import ScanHistory from '@/components/scanner/ScanHistory';
import ConfigPresets from '@/components/scanner/ConfigPresets';
import ScanScheduler from '@/components/scanner/ScanScheduler';
import ExportResults from '@/components/scanner/ExportResults';
import { Opportunity, ScanConfig } from '@/types/scanner';

export default function ScannerPage() {
  const [scanning, setScanning] = useState(false);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [scanTaskId, setScanTaskId] = useState<string | null>(null);
  const [scanConfig, setScanConfig] = useState<ScanConfig>({
    asset_classes: ['equities'],
    min_volume: 1000000,
    min_price_change: 0.02,
    correlation_threshold: 0.3,
    min_opportunity_score: 0.7,
    max_results: 20,
  });

  const handleStartScan = async (config: ScanConfig) => {
    setScanning(true);
    setScanConfig(config);
    
    // Since backend scanning isn't fully implemented, use mock data
    // Remove this and uncomment the real implementation when backend is ready
    setTimeout(() => {
      fetchMockData();
    }, 5000); // Wait for progress animation to complete
    
    /* Real implementation - uncomment when backend is ready:
    try {
      const response = await fetch('http://localhost:8000/api/v1/scanner/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setScanTaskId(data.task_id);
      
      // Start polling for results
      if (data.status === 'started') {
        pollScanStatus(data.task_id);
      } else {
        // Test mode - fetch mock data
        fetchMockData();
      }
    } catch (error) {
      console.error('Error starting scan:', error);
      // Fallback to mock data
      fetchMockData();
    }
    */
  };

  const pollScanStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/scanner/scan/${taskId}`);
        const data = await response.json();
        
        if (data.state === 'SUCCESS') {
          clearInterval(interval);
          setScanning(false);
          // Fetch opportunities
          fetchOpportunities();
        } else if (data.state === 'FAILURE') {
          clearInterval(interval);
          setScanning(false);
          console.error('Scan failed:', data.error);
        }
      } catch (error) {
        console.error('Error polling scan status:', error);
      }
    }, 2000);
  };

  const fetchMockData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/scanner/test-mock');
      const data = await response.json();
      
      // Transform mock data to match new Opportunity type
      const mockOpportunities: Opportunity[] = data.opportunities.map((opp: any) => ({
        id: Math.random().toString(36).substr(2, 9),
        symbol: opp.ticker,
        asset_class: opp.asset_class,
        strategy_type: opp.opportunity_type,
        opportunity_score: opp.signal_strength,
        expected_return: opp.price_change ? opp.price_change * 100 : 0,
        risk_level: 'medium',
        discovered_at: opp.discovered_at,
        entry_conditions: {
          price: opp.entry_price,
          volume: opp.volume,
        },
        technical_indicators: {
          spread: opp.spread,
          inefficiency_score: opp.inefficiency_score,
        }
      }));
      
      setOpportunities(mockOpportunities);
      setScanning(false);
    } catch (error) {
      console.error('Error fetching mock data:', error);
      setScanning(false);
    }
  };

  const fetchOpportunities = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/scanner/opportunities');
      const data = await response.json();
      setOpportunities(data);
    } catch (error) {
      console.error('Error fetching opportunities:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Market Scanner
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Discover trading opportunities across multiple asset classes
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Configuration */}
          <div className="lg:col-span-1 space-y-6">
            <ScannerConfig onStartScan={handleStartScan} isScanning={scanning} />
            <ConfigPresets 
              currentConfig={scanConfig}
              onLoadPreset={(preset) => setScanConfig(preset)}
            />
            <ScanScheduler currentConfig={scanConfig} />
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Scan Progress */}
            {scanning && (
              <ScanProgress taskId={scanTaskId} />
            )}

            {/* Opportunities Table with Export */}
            {opportunities.length > 0 && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Scan Results
                  </h3>
                  <ExportResults opportunities={opportunities} />
                </div>
                <OpportunityTable 
                  opportunities={opportunities}
                  onSelectOpportunity={setSelectedOpportunity}
                />
              </>
            )}

            {/* No opportunities message */}
            {!scanning && opportunities.length === 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No opportunities found</h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Configure your scan parameters and click "Start Scan" to find opportunities
                </p>
              </div>
            )}

            {/* Scan History */}
            <ScanHistory />
          </div>
        </div>

        {/* Opportunity Detail Modal */}
        {selectedOpportunity && (
          <OpportunityDetail 
            opportunity={selectedOpportunity}
            onClose={() => setSelectedOpportunity(null)}
          />
        )}
      </div>
    </div>
  );
}