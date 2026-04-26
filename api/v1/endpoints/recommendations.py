# -*- coding: utf-8 -*-
"""Market recommendation endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_config_dep
from api.v1.schemas.common import ErrorResponse
from api.v1.schemas.recommendations import (
    RecommendationRequest,
    RecommendationResponse,
)
from src.config import Config
from src.services.recommendation_service import (
    RecommendationRequest as ServiceRecommendationRequest,
    RecommendationService,
    recommendation_result_to_dict,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _to_service_request(request: RecommendationRequest, *, auto_analyze: bool = False) -> ServiceRecommendationRequest:
    return ServiceRecommendationRequest(
        markets=request.markets,
        asset_type=request.asset_type,
        max_candidates=request.max_candidates,
        top_n=request.top_n,
        risk_preference=request.risk_preference,
        include_news=request.include_news,
        auto_analyze=auto_analyze,
        send_notification=request.send_notification,
        report_type=request.report_type,
    )


@router.post(
    "/discover",
    response_model=RecommendationResponse,
    responses={
        200: {"description": "推荐候选列表"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="发现市场推荐候选",
    description="根据行情活跃度、成交额、量比和风险规则发现股票/ETF候选，不触发深度分析。",
)
def discover_recommendations(
    request: RecommendationRequest,
    config: Config = Depends(get_config_dep),
) -> RecommendationResponse:
    try:
        if not getattr(config, "recommendation_enabled", True):
            raise HTTPException(
                status_code=403,
                detail={"error": "disabled", "message": "推荐功能未启用"},
            )
        service = RecommendationService(config=config)
        result = service.discover(_to_service_request(request))
        return RecommendationResponse(**recommendation_result_to_dict(result))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("发现推荐候选失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"发现推荐候选失败: {str(exc)}"},
        )


@router.post(
    "/analyze",
    response_model=RecommendationResponse,
    responses={
        200: {"description": "推荐候选及深度分析摘要"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="推荐并分析 Top N 候选",
    description="先发现推荐候选，再将 Top N 交给现有股票分析流水线生成深度分析结果。",
)
def analyze_recommendations(
    request: RecommendationRequest,
    config: Config = Depends(get_config_dep),
) -> RecommendationResponse:
    try:
        if not getattr(config, "recommendation_enabled", True):
            raise HTTPException(
                status_code=403,
                detail={"error": "disabled", "message": "推荐功能未启用"},
            )
        service = RecommendationService(config=config)
        result = service.analyze_top_picks(_to_service_request(request, auto_analyze=True))
        return RecommendationResponse(**recommendation_result_to_dict(result))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("推荐候选深度分析失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"推荐候选深度分析失败: {str(exc)}"},
        )
