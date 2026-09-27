"""Memory + time measurement utilities for benchmarks.

The runner (``bench_data_vs_stream.py``) launches each scenario in a
fresh subprocess so that peak memory is measured in isolation.
"""

from __future__ import annotations

import gc
import json
import platform
import resource
import time
import tracemalloc
from typing import Any, Callable, Dict


def measure(func: Callable[[], Any]) -> Dict[str, Any]:
    gc.collect()
    tracemalloc.start()

    rss_before = _rss_mb()
    t0 = time.perf_counter()
    result = func()
    t1 = time.perf_counter()

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss_after = _rss_mb()

    return {
        "seconds": t1 - t0,
        "peak_python_mb": peak / (1024 * 1024),
        "rss_before_mb": rss_before,
        "rss_after_mb": rss_after,
        "rss_delta_mb": rss_after - rss_before,
        "result": result,
    }


def _rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if platform.system() == "Darwin":
        return usage.ru_maxrss / (1024 * 1024)
    return usage.ru_maxrss / 1024


def emit(stats: Dict[str, Any]) -> None:
    print("__BENCH_RESULT__" + json.dumps(stats))
