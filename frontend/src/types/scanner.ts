export interface ScanConfig {
  asset_classes: string[];
  correlation_threshold?: number;
  min_opportunity_score?: number;
  max_results?: number;
  min_volume?: number;
  min_price_change?: number;
}

export interface Opportunity {
  id: string;
  ticker: string;
  assetClass: string;
  opportunityType: string;
  signalStrength: number;
  entryPrice: number;
  priceChange?: number;
  volume?: number;
  inefficiencyScore?: number;
  discoveredAt: string;
  metadata?: {
    spread?: number;
    inefficiencies?: any[];
    correlation?: number;
  };
}

export interface ScanStatus {
  task_id: string;
  state: string;
  status: string;
  result?: any;
  error?: string;
}

export interface UncorrelatedPair {
  asset1: {
    ticker: string;
    class: string;
  };
  asset2: {
    ticker: string;
    class: string;
  };
  correlation: number;
  combined_score: number;
}