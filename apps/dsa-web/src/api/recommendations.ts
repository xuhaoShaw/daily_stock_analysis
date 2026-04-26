import apiClient from './index';
import { toCamelCase } from './utils';
import type {
  RecommendationRequest,
  RecommendationResponse,
} from '../types/recommendations';

function toRequestPayload(params: RecommendationRequest): Record<string, unknown> {
  return {
    markets: params.markets,
    asset_type: params.assetType,
    max_candidates: params.maxCandidates,
    top_n: params.topN,
    risk_preference: params.riskPreference,
    include_news: Boolean(params.includeNews),
    send_notification: Boolean(params.sendNotification),
    report_type: params.reportType || 'simple',
  };
}

export const recommendationsApi = {
  discover: async (params: RecommendationRequest): Promise<RecommendationResponse> => {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/recommendations/discover',
      toRequestPayload(params),
    );
    return toCamelCase<RecommendationResponse>(response.data);
  },

  analyze: async (params: RecommendationRequest): Promise<RecommendationResponse> => {
    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/recommendations/analyze',
      toRequestPayload(params),
    );
    return toCamelCase<RecommendationResponse>(response.data);
  },
};
