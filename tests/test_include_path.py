from datetime import datetime
from types import SimpleNamespace

import pytest
from omegaconf import OmegaConf

from zotero_arxiv_daily.executor import (
    Executor,
    normalize_include_path_patterns,
    resolve_executor_sources,
)
from zotero_arxiv_daily.protocol import CorpusPaper


def test_normalize_include_path_patterns_rejects_single_string():
    with pytest.raises(TypeError, match="config.zotero.include_path must be a list of glob patterns or null"):
        normalize_include_path_patterns("2026/survey/**")


def test_normalize_include_path_patterns_accepts_list_config():
    include_path = OmegaConf.create(["2026/survey/**", "2026/reading-group/**"])

    assert normalize_include_path_patterns(include_path) == [
        "2026/survey/**",
        "2026/reading-group/**",
    ]


def test_filter_corpus_matches_any_path_against_any_pattern():
    executor = Executor.__new__(Executor)
    executor.config = SimpleNamespace(
        zotero=SimpleNamespace(include_path=["2026/survey/**", "2026/reading-group/**"])
    )
    executor.include_path_patterns = normalize_include_path_patterns(executor.config.zotero.include_path)

    corpus = [
        CorpusPaper(
            title="Survey Paper",
            abstract="",
            added_date=datetime(2026, 1, 1),
            paths=["2026/survey/topic-a", "archive/misc"],
        ),
        CorpusPaper(
            title="Reading Group Paper",
            abstract="",
            added_date=datetime(2026, 1, 2),
            paths=["notes/inbox", "2026/reading-group/week-1"],
        ),
        CorpusPaper(
            title="Excluded Paper",
            abstract="",
            added_date=datetime(2026, 1, 3),
            paths=["2025/other/topic"],
        ),
    ]

    filtered = executor.filter_corpus(corpus)

    assert [paper.title for paper in filtered] == ["Survey Paper", "Reading Group Paper"]


def test_resolve_executor_sources_returns_explicit_sources():
    config = OmegaConf.create(
        {
            "executor": {"source": ["arxiv"]},
            "source": {
                "arxiv": {"category": ["cs.AI"]},
                "biorxiv": {"category": None},
            },
        }
    )

    assert resolve_executor_sources(config) == ["arxiv"]


def test_resolve_executor_sources_infers_sources_from_categories():
    config = OmegaConf.create(
        {
            "executor": {"source": "???"},
            "source": {
                "arxiv": {"category": ["cs.AI"]},
                "biorxiv": {"category": None},
                "medrxiv": {"category": ["neurology"]},
            },
        }
    )

    assert resolve_executor_sources(config) == ["arxiv", "medrxiv"]


def test_resolve_executor_sources_raises_when_no_source_configured():
    config = OmegaConf.create(
        {
            "executor": {"source": "???"},
            "source": {
                "arxiv": {"category": None},
                "biorxiv": {"category": []},
            },
        }
    )

    with pytest.raises(ValueError, match="No paper source configured"):
        resolve_executor_sources(config)
