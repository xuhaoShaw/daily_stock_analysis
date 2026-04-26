# -*- coding: utf-8 -*-
"""Tests for market recommendation service."""

import os
import sys
import types
import importlib.util
from types import SimpleNamespace
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Keep the focused service tests runnable in minimal local environments.
for optional_module in ("pandas", "numpy"):
    try:
        __import__(optional_module)
    except ModuleNotFoundError:
        stub = types.ModuleType(optional_module)
        if optional_module == "pandas":
            stub.DataFrame = object
        sys.modules[optional_module] = stub

try:
    import tenacity  # noqa: F401
except ModuleNotFoundError:
    tenacity = types.ModuleType("tenacity")
    tenacity.retry = lambda *args, **kwargs: (lambda func: func)
    tenacity.stop_after_attempt = lambda *args, **kwargs: None
    tenacity.wait_exponential = lambda *args, **kwargs: None
    tenacity.retry_if_exception_type = lambda *args, **kwargs: None
    tenacity.before_sleep_log = lambda *args, **kwargs: None
    sys.modules["tenacity"] = tenacity

from src.services.recommendation_service import (
    RecommendationRequest,
    RecommendationService,
)


def _load_data_provider_base():
    data_provider_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data_provider")
    )
    package = sys.modules.get("data_provider")
    if package is None:
        package = types.ModuleType("data_provider")
        package.__path__ = [data_provider_dir]
        sys.modules["data_provider"] = package
    spec = importlib.util.spec_from_file_location(
        "data_provider.base",
        os.path.join(data_provider_dir, "base.py"),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["data_provider.base"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.BaseFetcher, module.DataFetcherManager


BaseFetcher, DataFetcherManager = _load_data_provider_base()


def _load_akshare_fetcher_module():
    data_provider_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data_provider")
    )
    patch_package = types.ModuleType("patch")
    patch_package.__path__ = []
    patch_module = types.ModuleType("patch.eastmoney_patch")
    patch_module.eastmoney_patch = lambda: None
    sys.modules["patch"] = patch_package
    sys.modules["patch.eastmoney_patch"] = patch_module

    spec = importlib.util.spec_from_file_location(
        "data_provider.akshare_fetcher",
        os.path.join(data_provider_dir, "akshare_fetcher.py"),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["data_provider.akshare_fetcher"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _SimpleFrame:
    def __init__(self, rows):
        self._rows = rows
        self.columns = list(rows[0].keys()) if rows else []
        self.empty = not rows

    def iterrows(self):
        for index, row in enumerate(self._rows):
            yield index, row


class _FakeDataManager:
    def __init__(self):
        self.calls = []

    def get_market_movers(self, market="cn", asset_type="stock", limit=100):
        self.calls.append((market, asset_type, limit))
        return [
            {
                "code": "600519",
                "name": "贵州茅台",
                "market": "cn",
                "asset_type": "stock",
                "price": 1688.0,
                "change_pct": 2.5,
                "amount": 1_200_000_000,
                "volume_ratio": 1.8,
                "turnover_rate": 2.2,
                "amplitude": 4.5,
                "source": "FakeFetcher",
            },
            {
                "code": "000001",
                "name": "平安银行",
                "market": "cn",
                "asset_type": "stock",
                "price": 10.0,
                "change_pct": -1.2,
                "amount": 80_000_000,
                "volume_ratio": 0.6,
                "turnover_rate": 0.5,
                "amplitude": 3.0,
                "source": "FakeFetcher",
            },
        ]

    def get_market_stats(self):
        return {"up_count": 3000, "down_count": 1800}

    def get_sector_rankings(self, n=5):
        return ([{"name": "半导体", "change_pct": 3.2}], [])


class _EmptyDataManager:
    def __init__(self):
        self.market_stats_called = False
        self.sector_rankings_called = False

    def get_market_movers(self, market="cn", asset_type="stock", limit=100):
        return []

    def get_market_stats(self):
        self.market_stats_called = True
        return {"up_count": 0}

    def get_sector_rankings(self, n=5):
        self.sector_rankings_called = True
        return ([], [])


class _UsOnlyDataManager:
    def __init__(self):
        self.calls = []
        self.market_stats_called = False
        self.sector_rankings_called = False

    def get_market_movers(self, market="cn", asset_type="stock", limit=100):
        self.calls.append((market, asset_type, limit))
        if market != "us":
            return []
        return [
            {
                "code": "QQQ",
                "name": "Invesco QQQ Trust",
                "market": "us",
                "asset_type": "etf",
                "price": 430.0,
                "change_pct": 2.1,
                "volume": 45_000_000,
                "amount": None,
                "source": "FakeUSFetcher",
            }
        ]

    def get_market_stats(self):
        self.market_stats_called = True
        return {}

    def get_sector_rankings(self, n=5):
        self.sector_rankings_called = True
        return ([], [])


class _ContextFailDataManager(_FakeDataManager):
    def get_market_stats(self):
        raise RuntimeError("market stats unavailable")

    def get_sector_rankings(self, n=5):
        raise RuntimeError("sector rankings unavailable")


class _BaseOnlyMarketMoverFetcher(BaseFetcher):
    name = "BaseOnlyFetcher"
    priority = 0

    def __init__(self):
        self.get_market_movers = self._unexpected_market_movers_call

    def _unexpected_market_movers_call(self, **_kwargs):
        raise AssertionError("base get_market_movers implementation should be skipped")

    def _fetch_raw_data(self, stock_code, start_date, end_date):
        return None

    def _normalize_data(self, df, stock_code):
        return df


class _WorkingMarketMoverFetcher:
    name = "WorkingFetcher"
    priority = 1

    def get_market_movers(self, market="cn", asset_type="stock", limit=100):
        return [{"code": "600519", "name": "贵州茅台", "amount": 1_000_000}]


class _RecordingMarketMoverFetcher:
    def __init__(self, name, priority, result):
        self.name = name
        self.priority = priority
        self.result = result
        self.calls = []

    def get_market_movers(self, market="cn", asset_type="stock", limit=100):
        self.calls.append((market, asset_type, limit))
        return self.result


class _FakePipeline:
    def __init__(self):
        self.run_calls = []

    def run(self, stock_codes, dry_run=False, send_notification=True):
        self.run_calls.append({
            "stock_codes": stock_codes,
            "dry_run": dry_run,
            "send_notification": send_notification,
        })
        return [
            SimpleNamespace(
                code=stock_codes[0],
                name="贵州茅台",
                success=True,
                sentiment_score=80,
                operation_advice="持有",
                trend_prediction="看多",
                analysis_summary="趋势稳健",
            )
        ]


def _make_config(**overrides):
    values = {
        "bocha_api_keys": [],
        "tavily_api_keys": [],
        "anspire_api_keys": [],
        "brave_api_keys": [],
        "serpapi_keys": [],
        "minimax_api_keys": [],
        "searxng_base_urls": [],
        "searxng_public_instances_enabled": False,
        "news_max_age_days": 3,
        "news_strategy_profile": "short",
        "has_search_capability_enabled": lambda: False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class TestRecommendationService(unittest.TestCase):
    def test_discover_scores_and_sorts_candidates(self):
        service = RecommendationService(
            config=_make_config(),
            data_manager=_FakeDataManager(),
        )

        result = service.discover(RecommendationRequest(top_n=2))

        self.assertEqual([candidate.code for candidate in result.candidates], ["600519", "000001"])
        self.assertGreater(result.candidates[0].score, result.candidates[1].score)
        self.assertIn("成交额超过 10 亿元", "；".join(result.candidates[0].reasons))
        self.assertIn("流动性可能不足", "；".join(result.candidates[1].risks))
        self.assertEqual(result.metadata["candidate_count"], 2)
        self.assertEqual(result.metadata["top_sectors"][0]["name"], "半导体")

    def test_discover_reports_unsupported_markets_but_keeps_cn(self):
        service = RecommendationService(
            config=_make_config(),
            data_manager=_FakeDataManager(),
        )

        result = service.discover(RecommendationRequest(markets=["cn", "hk"], top_n=1))

        self.assertEqual(len(result.candidates), 1)
        self.assertTrue(any("暂不支持 hk" in note for note in result.metadata["source_notes"]))

    def test_discover_skips_context_when_candidates_are_empty(self):
        data_manager = _EmptyDataManager()
        service = RecommendationService(
            config=_make_config(),
            data_manager=data_manager,
        )

        result = service.discover(RecommendationRequest(top_n=1))

        self.assertEqual(result.candidates, [])
        self.assertFalse(data_manager.market_stats_called)
        self.assertFalse(data_manager.sector_rankings_called)
        self.assertTrue(any("候选为空" in note for note in result.metadata["source_notes"]))

    def test_discover_supports_us_etf_without_cn_context(self):
        data_manager = _UsOnlyDataManager()
        service = RecommendationService(
            config=_make_config(),
            data_manager=data_manager,
        )

        result = service.discover(
            RecommendationRequest(markets=["us"], asset_type="etf", top_n=1)
        )

        self.assertEqual(result.candidates[0].code, "QQQ")
        self.assertEqual(result.candidates[0].market, "us")
        self.assertEqual(result.candidates[0].asset_type, "etf")
        self.assertEqual(data_manager.calls, [("us", "etf", 100)])
        self.assertFalse(data_manager.market_stats_called)
        self.assertFalse(data_manager.sector_rankings_called)
        self.assertTrue(any("非 A 股候选" in note for note in result.metadata["source_notes"]))

    def test_discover_all_expands_to_cn_and_us(self):
        data_manager = _UsOnlyDataManager()
        service = RecommendationService(
            config=_make_config(),
            data_manager=data_manager,
        )

        result = service.discover(RecommendationRequest(markets=["all"], top_n=1))

        self.assertEqual([call[0] for call in data_manager.calls], ["cn", "us"])
        self.assertEqual(result.metadata["markets"], ["cn", "us"])

    def test_discover_keeps_candidates_when_context_fails(self):
        service = RecommendationService(
            config=_make_config(),
            data_manager=_ContextFailDataManager(),
        )

        result = service.discover(RecommendationRequest(top_n=1))

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].code, "600519")
        self.assertTrue(any("市场统计补充失败" in note for note in result.metadata["source_notes"]))
        self.assertTrue(any("板块排行补充失败" in note for note in result.metadata["source_notes"]))

    def test_manager_skips_fetchers_without_market_movers_override(self):
        manager = DataFetcherManager(
            fetchers=[
                _BaseOnlyMarketMoverFetcher(),
                _WorkingMarketMoverFetcher(),
            ]
        )

        result = manager.get_market_movers(limit=1)

        self.assertEqual(result[0]["code"], "600519")

    def test_manager_prefers_longbridge_for_us_when_configured_and_falls_back(self):
        longbridge = _RecordingMarketMoverFetcher("LongbridgeFetcher", 5, None)
        yfinance = _RecordingMarketMoverFetcher(
            "YfinanceFetcher",
            4,
            [{"code": "AAPL", "name": "Apple", "market": "us", "amount": 1_000_000}],
        )
        manager = DataFetcherManager(fetchers=[yfinance, longbridge])
        manager._longbridge_preferred = lambda: True

        result = manager.get_market_movers(market="us", asset_type="stock", limit=1)

        self.assertEqual(result[0]["code"], "AAPL")
        self.assertEqual(longbridge.calls, [("us", "stock", 1)])
        self.assertEqual(yfinance.calls, [("us", "stock", 1)])

    def test_akshare_market_movers_falls_back_to_sina_when_eastmoney_fails(self):
        module = _load_akshare_fetcher_module()
        akshare = types.ModuleType("akshare")
        calls = []

        def eastmoney_fail():
            calls.append("em")
            raise RuntimeError("eastmoney down")

        def sina_success():
            calls.append("sina")
            return _SimpleFrame([
                {
                    "代码": "600519",
                    "名称": "贵州茅台",
                    "最新价": 1688.0,
                    "涨跌幅": 2.5,
                    "涨跌额": 41.0,
                    "成交量": 100000,
                    "成交额": 1_200_000_000,
                    "换手率": 2.2,
                    "振幅": 4.5,
                    "量比": 1.8,
                    "市盈率": 30.0,
                    "总市值": 2_000_000_000_000,
                    "流通市值": 1_900_000_000_000,
                }
            ])

        akshare.stock_zh_a_spot_em = eastmoney_fail
        akshare.stock_zh_a_spot = sina_success
        sys.modules["akshare"] = akshare

        fetcher = module.AkshareFetcher.__new__(module.AkshareFetcher)
        fetcher._set_random_user_agent = lambda: None
        fetcher._enforce_rate_limit = lambda: None

        with self.assertLogs("data_provider.akshare_fetcher", level="WARNING"):
            result = fetcher.get_market_movers(asset_type="stock", limit=1)

        self.assertEqual(calls, ["em", "sina"])
        self.assertEqual(result[0]["code"], "600519")
        self.assertEqual(result[0]["source"], module.AkshareFetcher.name)

    def test_analyze_top_picks_reuses_pipeline(self):
        pipeline = _FakePipeline()
        service = RecommendationService(
            config=_make_config(),
            data_manager=_FakeDataManager(),
            pipeline_factory=lambda: pipeline,
        )

        result = service.analyze_top_picks(
            RecommendationRequest(top_n=1, send_notification=False)
        )

        self.assertEqual(pipeline.run_calls[0]["stock_codes"], ["600519"])
        self.assertFalse(pipeline.run_calls[0]["send_notification"])
        self.assertEqual(result.metadata["analyzed_count"], 1)
        self.assertEqual(result.analyzed_results[0]["analysis_summary"], "趋势稳健")


if __name__ == "__main__":
    unittest.main()
