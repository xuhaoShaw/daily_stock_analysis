# -*- coding: utf-8 -*-
"""Recommendation API schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    markets: List[str] = Field(default_factory=lambda: ["cn"], description="市场范围：cn/us/all；hk 暂未支持候选发现")
    asset_type: Literal["stock", "etf", "all"] = Field("stock", description="资产类型")
    max_candidates: int = Field(100, ge=10, le=500, description="候选池最大数量")
    top_n: int = Field(10, ge=1, le=50, description="返回推荐数量")
    risk_preference: Literal["conservative", "balanced", "aggressive"] = Field(
        "balanced",
        description="风险偏好",
    )
    include_news: bool = Field(False, description="是否尝试补充热点新闻证据")
    send_notification: bool = Field(False, description="深度分析时是否发送通知")
    report_type: Literal["brief", "simple", "detailed", "full"] = Field(
        "simple",
        description="深度分析报告类型",
    )


class RecommendationCandidate(BaseModel):
    code: str
    name: str
    market: str
    asset_type: str
    score: float
    reasons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)
    sources: List[str] = Field(default_factory=list)
    should_analyze: bool = True


class RecommendationAnalysisSummary(BaseModel):
    code: str
    name: str = ""
    success: bool = True
    sentiment_score: int | float | None = None
    operation_advice: str = ""
    trend_prediction: str = ""
    analysis_summary: str = ""
    report_type: str = "simple"


class RecommendationResponse(BaseModel):
    candidates: List[RecommendationCandidate] = Field(default_factory=list)
    analyzed_results: List[RecommendationAnalysisSummary] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
