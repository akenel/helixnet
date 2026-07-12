"""Live supplier-site search — registry + orchestrator.

Public entrypoint: ``await search_suppliers(q)``. Runs the enabled adapters CONCURRENTLY
over one shared browser-shaped client, merges + ranks their results, and never lets one
slow/broken supplier sink the rest (per-supplier errors are captured, not raised).

Adopting a live result should write it back into ``reference_products`` so the next lookup
is a local hit (self-heal) — that wiring lives in the route, not here.
"""
from __future__ import annotations

import asyncio
import logging

from .artemis import ArtemisAdapter
from .base import BaseAdapter, SupplierResult, make_client
from .fourtwenty import FourTwentyAdapter
from .neardark import NearDarkAdapter

log = logging.getLogger("supplier_search")

# Registered adapters, in default display priority (Felix's ~90% first).
ADAPTERS: dict[str, BaseAdapter] = {
    a.supplier_key: a for a in (FourTwentyAdapter(), ArtemisAdapter(), NearDarkAdapter())
}


async def search_suppliers(q: str, suppliers: list[str] | None = None,
                           limit: int = 5, timeout: float = 15.0) -> dict:
    """Search the supplier sites live. Returns
    ``{"query", "results": [dict...], "errors": {supplier: msg}, "suppliers": [key...]}``.
    ``suppliers`` optionally restricts to a subset of adapter keys."""
    q = (q or "").strip()
    if not q:
        return {"query": q, "results": [], "errors": {}, "suppliers": []}

    keys = [k for k in (suppliers or list(ADAPTERS)) if k in ADAPTERS]
    chosen = [ADAPTERS[k] for k in keys]

    async def _run(adapter):
        # Per-adapter deadline: one slow/hung supplier must not sink the batch.
        return await asyncio.wait_for(adapter.search(client, q, limit), timeout=timeout)

    async with make_client(timeout) as client:
        settled = await asyncio.gather(*[_run(a) for a in chosen], return_exceptions=True)

    results: list[SupplierResult] = []
    errors: dict[str, str] = {}
    for adapter, res in zip(chosen, settled):
        if isinstance(res, Exception):
            log.warning("supplier-search %s failed for %r: %s", adapter.supplier, q, res)
            errors[adapter.supplier] = str(res) or res.__class__.__name__
            continue
        results.extend(res)

    results.sort(key=lambda r: r.score, reverse=True)
    return {
        "query": q,
        "results": [r.to_dict() for r in results],
        "errors": errors,
        "suppliers": keys,
    }
