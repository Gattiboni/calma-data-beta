from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import random

# IMPORTANT: All routes must be prefixed with '/api' per ingress rules
app = FastAPI(title="Calma Data Mock API", version="1.0.0")

# Basic CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache with simple TTL
class SimpleCache:
    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> float:
        return datetime.utcnow().timestamp()

    def get(self, key: str, ttl_seconds: int) -> Optional[Any]:
        record = self.store.get(key)
        if not record:
            return None
        if self._now() - record["ts"] > ttl_seconds:
            del self.store[key]
            return None
        return record["val"]

    def set(self, key: str, val: Any):
        self.store[key] = {"val": val, "ts": self._now()}

cache = SimpleCache()

# Utilities

def daterange(start_date: datetime, end_date: datetime):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def parse_dates(start: str, end: str):
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    return start_dt, end_dt


CHANNELS = [
    "Organic Search",
    "Paid Search",
    "Direct",
    "Paid Social",
    "Organic Social",
    "Referral",
    "Display",
]

UH_TYPES = ["Standard", "Deluxe", "Suite", "Bungalow"]


# ------------------------- API Schemas (Contracts) -------------------------

class KPIResponse(BaseModel):
    receita: float
    reservas: int
    diarias: int
    clicks: int
    impressoes: int
    cpc: float
    custo: float


class TimePoint(BaseModel):
    date: str
    values: Dict[str, float]


class TimeSeriesResponse(BaseModel):
    metric: str
    points: List[TimePoint]


class RevenueByUHPoint(BaseModel):
    date: str
    values: Dict[str, float]


class RevenueByUHResponse(BaseModel):
    points: List[RevenueByUHPoint]


class StackedBarPoint(BaseModel):
    label: str
    values: Dict[str, float]


class StackedBarsResponse(BaseModel):
    series_labels: List[str]
    points: List[StackedBarPoint]


class HeatCell(BaseModel):
    day: int  # 0=Mon .. 6=Sun
    hour: int  # 0..23
    value: float


class HeatmapResponse(BaseModel):
    cells: List[HeatCell]


class PerformanceRow(BaseModel):
    name: str  # channel or campaign
    clicks: int
    impressoes: int
    ctr: float
    cpc: float
    custo: float
    conversoes: int
    receita: float
    roas: float


class PerformanceTableResponse(BaseModel):
    rows: List[PerformanceRow]


# ------------------------- Mock Generators -------------------------

def seeded_rand(seed: str) -> random.Random:
    r = random.Random()
    r.seed(seed)
    return r


def mock_kpis(start: datetime, end: datetime) -> dict:
    r = seeded_rand(f"kpis-{start}-{end}")
    days = (end - start).days + 1
    clicks = int(r.uniform(500, 3000) * days / 14)
    imp = int(clicks * r.uniform(8, 20))
    cpc = round(r.uniform(1.5, 4.5), 2)
    custo = round(clicks * cpc, 2)
    reservas = int(r.uniform(20, 120) * days / 14)
    diarias = int(reservas * r.uniform(1.3, 2.1))
    receita = round(diarias * r.uniform(180, 380), 2)  # GA4: sum of itemRevenue
    return {
        "receita": receita,
        "reservas": reservas,
        "diarias": diarias,
        "clicks": clicks,
        "impressoes": imp,
        "cpc": cpc,
        "custo": custo,
    }


def mock_acquisition_timeseries(metric: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    r = seeded_rand(f"acq-{metric}-{start}-{end}")
    points: List[Dict[str, Any]] = []
    for d in daterange(start, end):
        values = {}
        base = 100 + (d.weekday() * 10)
        for ch in CHANNELS:
            mult = 1.0 + (CHANNELS.index(ch) * 0.15)
            noise = r.uniform(0.7, 1.3)
            values[ch] = round(base * mult * noise, 2)
        points.append({"date": d.strftime("%Y-%m-%d"), "values": values})
    return points


def mock_revenue_by_uh(start: datetime, end: datetime) -> List[Dict[str, Any]]:
    r = seeded_rand(f"rev-uh-{start}-{end}")
    out = []
    for d in daterange(start, end):
        values = {}
        base = 2000 + (d.weekday() * 150)
        for uh in UH_TYPES:
            mult = 1.0 + (UH_TYPES.index(uh) * 0.25)
            noise = r.uniform(0.7, 1.4)
            values[uh] = round(base * mult * noise, 2)
        out.append({"date": d.strftime("%Y-%m-%d"), "values": values})
    return out


def mock_sales_uh_stacked(start: datetime, end: datetime) -> Dict[str, Any]:
    r = seeded_rand(f"sales-uh-{start}-{end}")
    points = []
    total_days = (end - start).days + 1
    weeks = max(1, total_days // 7)
    for i in range(weeks):
        label = f"Semana {i+1}"
        values = {}
        base = 80 + i * 10
        for uh in UH_TYPES:
            values[uh] = round(base * (1 + UH_TYPES.index(uh) * 0.3) * r.uniform(0.8, 1.4))
        points.append({"label": label, "values": values})
    return {"series_labels": UH_TYPES, "points": points}


def mock_campaign_heatmap(start: datetime, end: datetime) -> List[Dict[str, int]]:
    r = seeded_rand(f"heat-{start}-{end}")
    cells = []
    for day in range(7):
        for hour in range(24):
            base = 2 + (6 - abs(12 - hour)) * 0.8  # peak midday/evening
            val = max(0, r.gauss(mu=base, sigma=1.4))
            cells.append({"day": day, "hour": hour, "value": round(val, 2)})
    return cells


def mock_performance_table(start: datetime, end: datetime) -> List[Dict[str, Any]]:
    r = seeded_rand(f"perf-{start}-{end}")
    rows = []
    for ch in CHANNELS:
        clicks = int(r.uniform(200, 3000))
        imp = int(clicks * r.uniform(8, 20))
        cpc = round(r.uniform(1.5, 4.5), 2)
        cost = round(clicks * cpc, 2)
        conv = int(clicks * r.uniform(0.01, 0.05))
        revenue = round(conv * r.uniform(250, 450), 2)
        ctr = round((clicks / imp) if imp else 0, 4)
        roas = round((revenue / cost) if cost else 0, 2)
        rows.append({
            "name": ch,
            "clicks": clicks,
            "impressoes": imp,
            "ctr": ctr,
            "cpc": cpc,
            "custo": cost,
            "conversoes": conv,
            "receita": revenue,
            "roas": roas,
        })
    return rows


# ------------------------- Endpoints -------------------------

@app.get("/api/kpis", response_model=KPIResponse)
async def get_kpis(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    s, e = parse_dates(start, end)
    key = f"kpis-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    data = mock_kpis(s, e)
    cache.set(key, data)
    return data


@app.get("/api/acquisition-by-channel", response_model=TimeSeriesResponse)
async def acquisition_by_channel(metric: str = Query("users"), start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    s, e = parse_dates(start, end)
    key = f"acq-{metric}-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    points = mock_acquisition_timeseries(metric, s, e)
    payload = {"metric": metric, "points": points}
    cache.set(key, payload)
    return payload


@app.get("/api/revenue-by-uh", response_model=RevenueByUHResponse)
async def revenue_by_uh(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    s, e = parse_dates(start, end)
    key = f"revuh-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    points = mock_revenue_by_uh(s, e)
    payload = {"points": points}
    cache.set(key, payload)
    return payload


@app.get("/api/sales-uh-stacked", response_model=StackedBarsResponse)
async def sales_uh_stacked(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    s, e = parse_dates(start, end)
    key = f"salesuh-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    payload = mock_sales_uh_stacked(s, e)
    cache.set(key, payload)
    return payload


@app.get("/api/campaign-conversion-heatmap", response_model=HeatmapResponse)
async def campaign_conversion_heatmap(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    s, e = parse_dates(start, end)
    key = f"heatmap-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    cells = mock_campaign_heatmap(s, e)
    payload = {"cells": cells}
    cache.set(key, payload)
    return payload


@app.get("/api/performance-table", response_model=PerformanceTableResponse)
async def performance_table(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    s, e = parse_dates(start, end)
    key = f"table-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    rows = mock_performance_table(s, e)
    payload = {"rows": rows}
    cache.set(key, payload)
    return payload


# Healthcheck
@app.get("/api/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}