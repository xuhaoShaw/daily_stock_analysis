# -*- coding: utf-8 -*-
"""Tests for recommendation API endpoint functions."""

import os
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from fastapi import HTTPException

    from api.v1.endpoints.recommendations import discover_recommendations
    from api.v1.schemas.recommendations import RecommendationRequest
    from src.services.recommendation_service import (
        RecommendationCandidate,
        RecommendationResult,
    )
    FASTAPI_AVAILABLE = True
except ModuleNotFoundError:
    FASTAPI_AVAILABLE = False


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class TestRecommendationEndpoints(unittest.TestCase):
    @mock.patch("api.v1.endpoints.recommendations.RecommendationService")
    def test_discover_recommendations_returns_candidates(self, mock_service_cls):
        mock_service = mock_service_cls.return_value
        mock_service.discover.return_value = RecommendationResult(
            candidates=[
                RecommendationCandidate(
                    code="600519",
                    name="贵州茅台",
                    market="cn",
                    asset_type="stock",
                    score=88.0,
                    reasons=["成交活跃"],
                    risks=[],
                    signals={"change_pct": 2.5},
                    sources=["FakeFetcher"],
                )
            ],
            metadata={"candidate_count": 1},
        )

        response = discover_recommendations(
            RecommendationRequest(markets=["cn"], top_n=1),
            config=SimpleNamespace(recommendation_enabled=True),
        )

        self.assertEqual(len(response.candidates), 1)
        self.assertEqual(response.candidates[0].code, "600519")
        self.assertEqual(response.metadata["candidate_count"], 1)

    def test_discover_recommendations_respects_disabled_config(self):
        with self.assertRaises(HTTPException) as ctx:
            discover_recommendations(
                RecommendationRequest(markets=["cn"], top_n=1),
                config=SimpleNamespace(recommendation_enabled=False),
            )

        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
