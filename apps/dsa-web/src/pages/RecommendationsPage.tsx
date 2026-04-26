import type React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { PlayCircle, Radar, Search } from 'lucide-react';
import { recommendationsApi } from '../api/recommendations';
import type { ParsedApiError } from '../api/error';
import { getParsedApiError } from '../api/error';
import { ApiErrorAlert, Badge, Card, EmptyState } from '../components/common';
import type {
  RecommendationAssetType,
  RecommendationCandidate,
  RecommendationMarket,
  RecommendationResponse,
  RecommendationRiskPreference,
} from '../types/recommendations';

const INPUT_CLASS =
  'input-surface input-focus-glow h-11 w-full rounded-xl border bg-transparent px-4 text-sm transition-all focus:outline-none disabled:cursor-not-allowed disabled:opacity-60';

function formatNumber(value: unknown): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--';
  if (Math.abs(value) >= 100_000_000) return `${(value / 100_000_000).toFixed(1)}亿`;
  if (Math.abs(value) >= 10_000) return `${(value / 10_000).toFixed(1)}万`;
  return value.toFixed(2);
}

function formatPct(value: unknown): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--';
  return `${value.toFixed(2)}%`;
}

function scoreBadge(candidate: RecommendationCandidate) {
  if (candidate.score >= 75) return <Badge variant="success" glow>{candidate.score}</Badge>;
  if (candidate.score >= 60) return <Badge variant="info">{candidate.score}</Badge>;
  if (candidate.score >= 50) return <Badge variant="warning">{candidate.score}</Badge>;
  return <Badge variant="default">{candidate.score}</Badge>;
}

const RecommendationsPage: React.FC = () => {
  useEffect(() => {
    document.title = '市场推荐 - DSA';
  }, []);

  const [market, setMarket] = useState<RecommendationMarket>('cn');
  const [assetType, setAssetType] = useState<RecommendationAssetType>('stock');
  const [riskPreference, setRiskPreference] = useState<RecommendationRiskPreference>('balanced');
  const [maxCandidates, setMaxCandidates] = useState(100);
  const [topN, setTopN] = useState(10);
  const [includeNews, setIncludeNews] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<ParsedApiError | null>(null);
  const [result, setResult] = useState<RecommendationResponse | null>(null);

  const request = useMemo(() => ({
    markets: [market],
    assetType,
    maxCandidates,
    topN,
    riskPreference,
    includeNews,
    sendNotification: false,
    reportType: 'simple' as const,
  }), [assetType, includeNews, market, maxCandidates, riskPreference, topN]);

  const handleDiscover = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await recommendationsApi.discover(request);
      setResult(data);
    } catch (err) {
      console.error('Failed to discover recommendations:', err);
      setError(getParsedApiError(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setError(null);
    try {
      const data = await recommendationsApi.analyze(request);
      setResult(data);
    } catch (err) {
      console.error('Failed to analyze recommendations:', err);
      setError(getParsedApiError(err));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const sourceNotes = (result?.metadata?.sourceNotes as string[] | undefined) || [];

  return (
    <div className="mx-auto flex w-full max-w-[1680px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-2">
        <span className="label-uppercase">Market Recommendations</span>
        <h1 className="text-2xl font-semibold text-foreground">市场热点推荐</h1>
        <p className="max-w-3xl text-sm text-secondary-text">
          先从 A 股实时活跃行情或美股高流动性股票/ETF 池中发现候选，再按需把 Top N 交给现有股票分析流水线做深度分析。
        </p>
      </div>

      <Card padding="md">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
          <label className="flex flex-col gap-2 text-sm">
            <span className="text-secondary-text">市场</span>
            <select className={INPUT_CLASS} value={market} onChange={(e) => setMarket(e.target.value as RecommendationMarket)}>
              <option value="cn">A 股</option>
              <option value="hk">港股（暂未支持候选池）</option>
              <option value="us">美股</option>
              <option value="all">全部（A 股 + 美股）</option>
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm">
            <span className="text-secondary-text">资产</span>
            <select className={INPUT_CLASS} value={assetType} onChange={(e) => setAssetType(e.target.value as RecommendationAssetType)}>
              <option value="stock">股票</option>
              <option value="etf">ETF</option>
              <option value="all">股票 + ETF</option>
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm">
            <span className="text-secondary-text">风险偏好</span>
            <select className={INPUT_CLASS} value={riskPreference} onChange={(e) => setRiskPreference(e.target.value as RecommendationRiskPreference)}>
              <option value="conservative">稳健</option>
              <option value="balanced">均衡</option>
              <option value="aggressive">进攻</option>
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm">
            <span className="text-secondary-text">候选池</span>
            <input
              className={INPUT_CLASS}
              type="number"
              min={10}
              max={500}
              value={maxCandidates}
              onChange={(e) => setMaxCandidates(Number(e.target.value) || 100)}
            />
          </label>
          <label className="flex flex-col gap-2 text-sm">
            <span className="text-secondary-text">返回 Top N</span>
            <input
              className={INPUT_CLASS}
              type="number"
              min={1}
              max={50}
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value) || 10)}
            />
          </label>
          <label className="flex items-center gap-2 self-end text-sm text-secondary-text">
            <input
              type="checkbox"
              checked={includeNews}
              onChange={(e) => setIncludeNews(e.target.checked)}
            />
            补充热点新闻
          </label>
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            className="btn-primary inline-flex items-center gap-2"
            onClick={handleDiscover}
            disabled={isLoading || isAnalyzing}
          >
            <Search className="h-4 w-4" />
            {isLoading ? '发现中...' : '发现推荐'}
          </button>
          <button
            type="button"
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-border/70 px-4 text-sm text-secondary-text transition-colors hover:bg-hover hover:text-foreground disabled:cursor-not-allowed disabled:opacity-60"
            onClick={handleAnalyze}
            disabled={isLoading || isAnalyzing}
          >
            <PlayCircle className="h-4 w-4" />
            {isAnalyzing ? '分析中...' : '推荐并深度分析 Top N'}
          </button>
        </div>
      </Card>

      {error ? <ApiErrorAlert error={error} /> : null}

      {sourceNotes.length > 0 ? (
        <Card padding="md">
          <div className="flex items-start gap-3 text-sm text-secondary-text">
            <Radar className="mt-0.5 h-4 w-4 shrink-0 text-cyan" />
            <div className="space-y-1">
              {sourceNotes.map((note) => <p key={note}>{note}</p>)}
            </div>
          </div>
        </Card>
      ) : null}

      <Card padding="md">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-foreground">推荐候选</h2>
            <p className="text-xs text-secondary-text">
              候选数：{String(result?.metadata?.candidateCount ?? 0)}，返回：{result?.candidates.length ?? 0}
            </p>
          </div>
          {result?.metadata?.analyzedCount != null ? (
            <Badge variant="info">已深度分析 {String(result.metadata.analyzedCount)} 只</Badge>
          ) : null}
        </div>

        {!result || result.candidates.length === 0 ? (
          <EmptyState
            title="暂无推荐结果"
            description="点击“发现推荐”后，会显示按热度、流动性和风险规则排序的候选。"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="border-b border-border/70 text-xs uppercase text-muted-text">
                <tr>
                  <th className="px-3 py-3">代码</th>
                  <th className="px-3 py-3">名称</th>
                  <th className="px-3 py-3">评分</th>
                  <th className="px-3 py-3">涨跌幅</th>
                  <th className="px-3 py-3">成交额/成交量</th>
                  <th className="px-3 py-3">量比</th>
                  <th className="px-3 py-3">推荐理由</th>
                  <th className="px-3 py-3">风险提示</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {result.candidates.map((candidate) => (
                  <tr key={`${candidate.market}:${candidate.code}`} className="align-top">
                    <td className="px-3 py-3 font-mono text-foreground">{candidate.code}</td>
                    <td className="px-3 py-3 text-foreground">{candidate.name || '--'}</td>
                    <td className="px-3 py-3">{scoreBadge(candidate)}</td>
                    <td className="px-3 py-3 text-foreground">{formatPct(candidate.signals.changePct)}</td>
                    <td className="px-3 py-3 text-foreground">
                      {typeof candidate.signals.amount === 'number'
                        ? formatNumber(candidate.signals.amount)
                        : formatNumber(candidate.signals.volume)}
                    </td>
                    <td className="px-3 py-3 text-foreground">{formatNumber(candidate.signals.volumeRatio)}</td>
                    <td className="max-w-[320px] px-3 py-3 text-secondary-text">
                      <ul className="space-y-1">
                        {candidate.reasons.slice(0, 3).map((reason) => <li key={reason}>- {reason}</li>)}
                      </ul>
                    </td>
                    <td className="max-w-[280px] px-3 py-3 text-secondary-text">
                      {candidate.risks.length > 0 ? (
                        <ul className="space-y-1">
                          {candidate.risks.slice(0, 3).map((risk) => <li key={risk}>- {risk}</li>)}
                        </ul>
                      ) : (
                        <span className="text-muted-text">暂无明显风险</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {result?.analyzedResults && result.analyzedResults.length > 0 ? (
        <Card padding="md">
          <h2 className="mb-4 text-base font-semibold text-foreground">深度分析摘要</h2>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {result.analyzedResults.map((item) => (
              <div key={item.code} className="rounded-2xl border border-border/60 bg-card/60 p-4">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span className="font-mono text-sm text-foreground">{item.code}</span>
                  <Badge variant={item.success ? 'success' : 'danger'}>{item.success ? '完成' : '失败'}</Badge>
                </div>
                <p className="text-sm font-medium text-foreground">{item.name || '--'}</p>
                <p className="mt-2 text-xs text-secondary-text">{item.analysisSummary || '暂无摘要'}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Badge variant="info">评分 {item.sentimentScore ?? '--'}</Badge>
                  <Badge variant="default">{item.operationAdvice || '--'}</Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
};

export default RecommendationsPage;
