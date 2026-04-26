/**
 * Recommendation API type definitions.
 */

export type RecommendationMarket = 'cn' | 'hk' | 'us' | 'all';
export type RecommendationAssetType = 'stock' | 'etf' | 'all';
export type RecommendationRiskPreference = 'conservative' | 'balanced' | 'aggressive';

export interface RecommendationRequest {
  markets: RecommendationMarket[];
  assetType: RecommendationAssetType;
  maxCandidates: number;
  topN: number;
  riskPreference: RecommendationRiskPreference;
  includeNews?: boolean;
  sendNotification?: boolean;
  reportType?: 'brief' | 'simple' | 'detailed' | 'full';
}

export interface RecommendationCandidate {
  code: string;
  name: string;
  market: string;
  assetType: string;
  score: number;
  reasons: string[];
  risks: string[];
  signals: Record<string, number | string | boolean | null | undefined>;
  sources: string[];
  shouldAnalyze: boolean;
}

export interface RecommendationAnalysisSummary {
  code: string;
  name?: string;
  success: boolean;
  sentimentScore?: number | null;
  operationAdvice?: string;
  trendPrediction?: string;
  analysisSummary?: string;
  reportType?: string;
}

export interface RecommendationResponse {
  candidates: RecommendationCandidate[];
  analyzedResults: RecommendationAnalysisSummary[];
  metadata: Record<string, unknown>;
}
