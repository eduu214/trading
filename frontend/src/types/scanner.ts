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
  symbol: string;  // Changed from ticker
  asset_class: string;  // Changed from assetClass
  strategy_type: string;  // Changed from opportunityType
  opportunity_score: number;  // Changed from signalStrength
  expected_return: number;
  risk_level: string;
  discovered_at: string;  // Changed from discoveredAt
  entry_conditions?: {
    price?: number;
    volume?: number;
  };
  technical_indicators?: {
    ticker?: string;
    volume?: number;
    price_change?: number;
    open?: number;
    close?: number;
    high?: number;
    low?: number;
    opportunity_type?: string;
    spread?: number;
    inefficiencies?: any[];
    inefficiency_score?: number;
    [key: string]: any;
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