# -*- coding: utf-8 -*-
"""Market recommendation service.

The recommendation layer discovers candidates first, then optionally delegates
top picks to the existing stock analysis pipeline.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass, field
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Sequence, TYPE_CHECKING

from src.config import Config, get_config
from src.enums import ReportType

if TYPE_CHECKING:
    from data_provider.base import DataFetcherManager

logger = logging.getLogger(__name__)

SUPPORTED_RECOMMENDATION_MARKETS = {"cn", "us"}
SUPPORTED_ASSET_TYPES = {"stock", "etf", "all"}
SUPPORTED_RISK_PREFERENCES = {"conservative", "balanced", "aggressive"}


@dataclass
class RecommendationRequest:
    """Service-level recommendation request."""

    markets: List[str] = field(default_factory=lambda: ["cn"])
    asset_type: str = "stock"
    max_candidates: int = 100
    top_n: int = 10
    risk_preference: str = "balanced"
    include_news: bool = False
    auto_analyze: bool = False
    send_notification: bool = False
    report_type: str = "simple"


@dataclass
class RecommendationCandidate:
    """Explainable recommendation candidate."""

    code: str
    name: str
    market: str
    asset_type: str
    score: float
    reasons: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    signals: Dict[str, Any] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    should_analyze: bool = True


@dataclass
class RecommendationResult:
    """Recommendation result with optional analysis output."""

    candidates: List[RecommendationCandidate]
    analyzed_results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RecommendationService:
    """Discover and rank market candidates."""

    def __init__(
        self,
        config: Optional[Config] = None,
        data_manager: Optional["DataFetcherManager"] = None,
        pipeline_factory: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.config = config or get_config()
        if data_manager is None:
            from data_provider.base import DataFetcherManager

            data_manager = DataFetcherManager()
        self.data_manager = data_manager
        self.pipeline_factory = pipeline_factory

    def discover(self, request: RecommendationRequest) -> RecommendationResult:
        """Discover and rank recommendation candidates."""
        normalized_request = self._normalize_request(request)
        markets = self._normalize_markets(normalized_request.markets)

        raw_candidates: List[Dict[str, Any]] = []
        unsupported_markets: List[str] = []
        source_notes: List[str] = []

        for market in markets:
            if market not in SUPPORTED_RECOMMENDATION_MARKETS:
                unsupported_markets.append(market)
                continue
            movers = self.data_manager.get_market_movers(
                market=market,
                asset_type=normalized_request.asset_type,
                limit=normalized_request.max_candidates,
            )
            raw_candidates.extend(movers)

        deduped = self._dedupe_candidates(raw_candidates)
        has_cn_candidates = any(str(item.get("market") or "cn").lower() == "cn" for item in deduped)
        if not deduped:
            market_context = {
                "market_stats": {},
                "top_sectors": [],
                "bottom_sectors": [],
                "context_notes": ["候选为空，已跳过市场统计和板块排行补充"],
            }
        elif has_cn_candidates:
            market_context = self._build_market_context()
        else:
            market_context = {
                "market_stats": {},
                "top_sectors": [],
                "bottom_sectors": [],
                "context_notes": ["非 A 股候选已跳过 A 股市场统计和板块排行补充"],
            }
        scored_candidates = [
            self._score_candidate(candidate, normalized_request.risk_preference)
            for candidate in deduped
        ]
        scored_candidates.sort(key=lambda item: item.score, reverse=True)
        top_candidates = scored_candidates[: normalized_request.top_n]

        if unsupported_markets:
            source_notes.append(
                f"暂不支持 {', '.join(sorted(set(unsupported_markets)))} 全市场推荐，当前支持 A 股和美股候选"
            )
        if not top_candidates:
            source_notes.append("未获取到可用候选，请检查实时行情数据源或稍后重试")
        source_notes.extend(market_context.get("context_notes", []))

        if normalized_request.include_news and top_candidates:
            news_topics = self._discover_news_topics(market_context)
        else:
            news_topics = []

        metadata = {
            "markets": markets,
            "asset_type": normalized_request.asset_type,
            "risk_preference": normalized_request.risk_preference,
            "candidate_count": len(deduped),
            "returned_count": len(top_candidates),
            "market_stats": market_context.get("market_stats", {}),
            "top_sectors": market_context.get("top_sectors", []),
            "bottom_sectors": market_context.get("bottom_sectors", []),
            "news_topics": news_topics,
            "source_notes": source_notes,
        }
        return RecommendationResult(candidates=top_candidates, metadata=metadata)

    def analyze_top_picks(self, request: RecommendationRequest) -> RecommendationResult:
        """Discover candidates and run deep analysis for the top picks."""
        normalized_request = self._normalize_request(request)
        result = self.discover(normalized_request)
        if not result.candidates:
            return result

        codes = [self._canonical_candidate_code(candidate.code) for candidate in result.candidates]
        try:
            pipeline = self._build_pipeline()
            report_type = ReportType.from_str(normalized_request.report_type)
            analysis_results = pipeline.run(
                stock_codes=codes,
                dry_run=False,
                send_notification=normalized_request.send_notification,
            )
            result.analyzed_results = [
                self._summarize_analysis_result(item, report_type.value)
                for item in analysis_results
            ]
            result.metadata["analyzed_count"] = len(result.analyzed_results)
        except Exception as exc:
            logger.error("推荐候选深度分析失败: %s", exc, exc_info=True)
            result.metadata["analysis_error"] = str(exc)
            result.metadata["analyzed_count"] = 0
        return result

    def _normalize_request(self, request: RecommendationRequest) -> RecommendationRequest:
        asset_type = (request.asset_type or "stock").strip().lower()
        if asset_type not in SUPPORTED_ASSET_TYPES:
            asset_type = "stock"

        risk_preference = (request.risk_preference or "balanced").strip().lower()
        if risk_preference not in SUPPORTED_RISK_PREFERENCES:
            risk_preference = "balanced"

        max_candidates = min(max(int(request.max_candidates or 100), 10), 500)
        top_n = min(max(int(request.top_n or 10), 1), 50)
        top_n = min(top_n, max_candidates)

        report_type = (request.report_type or "simple").strip().lower()
        try:
            ReportType.from_str(report_type)
        except Exception:
            report_type = "simple"

        return RecommendationRequest(
            markets=request.markets or ["cn"],
            asset_type=asset_type,
            max_candidates=max_candidates,
            top_n=top_n,
            risk_preference=risk_preference,
            include_news=bool(request.include_news),
            auto_analyze=bool(request.auto_analyze),
            send_notification=bool(request.send_notification),
            report_type=report_type,
        )

    @staticmethod
    def _normalize_markets(markets: Sequence[str]) -> List[str]:
        normalized: List[str] = []
        for market in markets or ["cn"]:
            value = (market or "cn").strip().lower()
            if value == "all":
                normalized.extend(["cn", "us"])
            elif value in {"a", "ashare", "a_share", "a-share"}:
                normalized.append("cn")
            else:
                normalized.append(value)
        return list(dict.fromkeys(normalized)) or ["cn"]

    @staticmethod
    def _dedupe_candidates(candidates: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: Dict[str, Dict[str, Any]] = {}
        for candidate in candidates:
            code = str(candidate.get("code") or "").strip()
            market = str(candidate.get("market") or "cn").strip().lower()
            if not code:
                continue
            key = f"{market}:{code}"
            previous = deduped.get(key)
            if previous is None or float(candidate.get("amount") or 0) > float(previous.get("amount") or 0):
                deduped[key] = dict(candidate)
        return list(deduped.values())

    def _build_market_context(self, timeout_seconds: float = 3.0) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "market_stats": {},
            "top_sectors": [],
            "bottom_sectors": [],
            "context_notes": [],
        }

        market_stats, market_stats_error = self._run_context_call(
            "市场统计",
            lambda: self.data_manager.get_market_stats() or {},
            timeout_seconds,
        )
        if market_stats_error:
            logger.info("推荐上下文跳过市场统计: %s", market_stats_error)
            context["context_notes"].append(f"市场统计补充失败: {market_stats_error}")
        elif isinstance(market_stats, dict):
            context["market_stats"] = market_stats

        sector_rankings, sector_error = self._run_context_call(
            "板块排行",
            lambda: self.data_manager.get_sector_rankings(5),
            timeout_seconds,
        )
        if sector_error:
            logger.info("推荐上下文跳过板块排行: %s", sector_error)
            context["context_notes"].append(f"板块排行补充失败: {sector_error}")
        elif sector_rankings:
            top_sectors, bottom_sectors = sector_rankings
            context["top_sectors"] = top_sectors or []
            context["bottom_sectors"] = bottom_sectors or []
        return context

    @staticmethod
    def _run_context_call(
        label: str,
        func: Callable[[], Any],
        timeout_seconds: float,
    ) -> tuple[Optional[Any], Optional[str]]:
        """Run optional recommendation context calls with a short fail-open timeout."""
        result_holder: Dict[str, Any] = {}
        error_holder: Dict[str, Exception] = {}

        def runner() -> None:
            try:
                result_holder["value"] = func()
            except Exception as exc:
                error_holder["error"] = exc

        timeout = max(0.1, float(timeout_seconds))
        worker = Thread(target=runner, daemon=True, name=f"recommendation-{label}")
        worker.start()
        worker.join(timeout)
        if worker.is_alive():
            return None, f"{label}超过 {timeout:.1f}s，已跳过"
        if "error" in error_holder:
            return None, str(error_holder["error"])
        return result_holder.get("value"), None

    def _score_candidate(
        self,
        raw: Dict[str, Any],
        risk_preference: str,
    ) -> RecommendationCandidate:
        score = 45.0
        reasons: List[str] = []
        risks: List[str] = []

        change_pct = self._safe_float(raw.get("change_pct"))
        amount = self._safe_float(raw.get("amount"))
        volume_ratio = self._safe_float(raw.get("volume_ratio"))
        turnover_rate = self._safe_float(raw.get("turnover_rate"))
        amplitude = self._safe_float(raw.get("amplitude"))
        pe_ratio = self._safe_float(raw.get("pe_ratio"))
        volume = self._safe_int(raw.get("volume"))
        market = str(raw.get("market") or "cn").lower()
        asset_type = str(raw.get("asset_type") or "stock").lower()
        is_etf = asset_type == "etf"

        if change_pct is not None:
            if change_pct > 0:
                score += min(change_pct * 2.5, 22)
                reasons.append(f"当日涨幅 {change_pct:.2f}%，短线强度靠前")
            elif change_pct < 0:
                score += max(change_pct * 1.5, -15)
                risks.append(f"当日下跌 {abs(change_pct):.2f}%，趋势仍需确认")

            if change_pct >= 8:
                risks.append(
                    "短线涨幅较大，注意溢价和回撤风险"
                    if is_etf
                    else "短线涨幅较大，注意追高和回撤风险"
                )
                if risk_preference == "conservative":
                    score -= 8
            elif 2 <= change_pct < 8:
                reasons.append("涨幅处于强势但未极端区间")
        else:
            risks.append("缺少涨跌幅数据")
            score -= 8

        if amount is not None:
            if amount >= 1_000_000_000:
                score += 12
                reasons.append("成交额超过 10 亿元，市场关注度较高")
            elif amount >= 500_000_000:
                score += 8
                reasons.append("成交额超过 5 亿元，流动性较好")
            elif amount >= 100_000_000:
                score += 4
                reasons.append("成交额超过 1 亿元，具备基本流动性")
            else:
                risks.append("成交额偏低，流动性可能不足")
                score -= 4
        else:
            if volume is not None and volume >= 1_000_000:
                score += 3
                reasons.append("成交量较高，具备基础流动性")
            elif market == "us":
                risks.append("缺少成交额数据，已按成交量辅助判断流动性")
            else:
                risks.append("缺少成交额数据")
                score -= 5

        if volume_ratio is not None:
            if volume_ratio >= 2:
                score += min((volume_ratio - 1) * 5, 12)
                reasons.append(f"量比 {volume_ratio:.2f}，资金活跃度提升")
            elif volume_ratio < 0.8:
                risks.append("量比偏低，主动资金关注不足")
                score -= 3

            if volume_ratio >= 5:
                risks.append("量比过高，可能存在短线情绪过热")
                if risk_preference == "conservative":
                    score -= 4

        if turnover_rate is not None:
            if 1 <= turnover_rate <= 12:
                score += 5
                reasons.append(f"换手率 {turnover_rate:.2f}%，交易活跃度健康")
            elif turnover_rate > 20:
                risks.append("换手率过高，筹码波动可能较大")
                score -= 5

        if amplitude is not None and amplitude >= 10:
            risks.append("日内振幅较大，需控制仓位")
            score -= 4 if risk_preference != "aggressive" else 1

        if (not is_etf) and pe_ratio is not None and pe_ratio >= 80:
            risks.append("估值指标偏高，需结合基本面确认")
            score -= 3

        if is_etf:
            score += 2
            reasons.append("ETF 分散度较高，单一公司风险较低")
        if market == "us":
            reasons.append("候选来自美股高流动性股票/ETF 池")

        if risk_preference == "aggressive" and change_pct and change_pct > 3:
            score += 4
        elif risk_preference == "conservative" and not risks:
            score += 3

        score = max(0.0, min(100.0, round(score, 1)))
        should_analyze = score >= 55 and len(risks) <= 4

        signals = {
            "price": self._safe_float(raw.get("price")),
            "change_pct": change_pct,
            "change_amount": self._safe_float(raw.get("change_amount")),
            "volume": volume,
            "amount": amount,
            "volume_ratio": volume_ratio,
            "turnover_rate": turnover_rate,
            "amplitude": amplitude,
            "pe_ratio": pe_ratio,
            "total_mv": self._safe_float(raw.get("total_mv")),
            "circ_mv": self._safe_float(raw.get("circ_mv")),
        }
        sources = [str(raw.get("source") or "unknown")]

        return RecommendationCandidate(
            code=str(raw.get("code") or ""),
            name=str(raw.get("name") or ""),
            market=str(raw.get("market") or "cn"),
            asset_type=str(raw.get("asset_type") or "stock"),
            score=score,
            reasons=reasons or ["候选来自市场活跃榜，需进一步深度分析确认"],
            risks=risks,
            signals=signals,
            sources=sources,
            should_analyze=should_analyze,
        )

    def _discover_news_topics(self, market_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Best-effort news topic discovery from hot sectors."""
        if not getattr(self.config, "has_search_capability_enabled", lambda: False)():
            return []
        top_sectors = market_context.get("top_sectors") or []
        if not top_sectors:
            return []
        try:
            from src.search_service import SearchService

            search_service = SearchService(
                bocha_keys=self.config.bocha_api_keys,
                tavily_keys=self.config.tavily_api_keys,
                anspire_keys=self.config.anspire_api_keys,
                brave_keys=self.config.brave_api_keys,
                serpapi_keys=self.config.serpapi_keys,
                minimax_keys=self.config.minimax_api_keys,
                searxng_base_urls=self.config.searxng_base_urls,
                searxng_public_instances_enabled=self.config.searxng_public_instances_enabled,
                news_max_age_days=self.config.news_max_age_days,
                news_strategy_profile=getattr(self.config, "news_strategy_profile", "short"),
            )
            topics: List[Dict[str, Any]] = []
            for sector in top_sectors[:3]:
                name = str(sector.get("name") or sector.get("板块") or "").strip()
                if not name:
                    continue
                response = search_service.search(f"A股 {name} 热点 资金流 新闻", max_results=3)
                topics.append({
                    "topic": name,
                    "summary": getattr(response, "summary", "") or "",
                    "result_count": len(getattr(response, "results", []) or []),
                })
            return topics
        except Exception as exc:
            logger.debug("推荐新闻热点发现失败: %s", exc)
            return []

    def _build_pipeline(self) -> Any:
        if self.pipeline_factory is not None:
            return self.pipeline_factory()
        from src.core.pipeline import StockAnalysisPipeline

        return StockAnalysisPipeline(
            config=self.config,
            query_id=uuid.uuid4().hex,
            query_source="recommendation",
        )

    @staticmethod
    def _canonical_candidate_code(code: str) -> str:
        try:
            from data_provider.base import canonical_stock_code

            return canonical_stock_code(code)
        except Exception:
            return (code or "").strip().upper()

    @staticmethod
    def _summarize_analysis_result(result: Any, report_type: str) -> Dict[str, Any]:
        return {
            "code": getattr(result, "code", ""),
            "name": getattr(result, "name", ""),
            "success": bool(getattr(result, "success", True)),
            "sentiment_score": getattr(result, "sentiment_score", None),
            "operation_advice": getattr(result, "operation_advice", ""),
            "trend_prediction": getattr(result, "trend_prediction", ""),
            "analysis_summary": getattr(result, "analysis_summary", ""),
            "report_type": report_type,
        }

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        try:
            if value is None or value == "":
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None


def recommendation_result_to_dict(result: RecommendationResult) -> Dict[str, Any]:
    """Convert dataclass result into plain dictionaries."""
    return {
        "candidates": [asdict(candidate) for candidate in result.candidates],
        "analyzed_results": list(result.analyzed_results),
        "metadata": dict(result.metadata),
    }
