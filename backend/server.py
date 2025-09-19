from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import random

# Optional integrations
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID") or os.environ.get("GA4_PROPERTY")
GA4_CLIENT_EMAIL = os.environ.get("GA4_CLIENT_EMAIL")
GA4_PRIVATE_KEY = os.environ.get("GA4_PRIVATE_KEY")

ADS_DEVELOPER_TOKEN = os.environ.get("ADS_DEVELOPER_TOKEN")
ADS_LOGIN_CUSTOMER_ID = os.environ.get("ADS_LOGIN_CUSTOMER_ID")
ADS_CUSTOMER_ID = os.environ.get("ADS_CUSTOMER_ID")
ADS_OAUTH_CLIENT_ID = os.environ.get("ADS_OAUTH_CLIENT_ID")
ADS_OAUTH_CLIENT_SECRET = os.environ.get("ADS_OAUTH_CLIENT_SECRET")
ADS_OAUTH_REFRESH_TOKEN = os.environ.get("ADS_OAUTH_REFRESH_TOKEN")

# Try lazy imports when keys available
ga4_client = None
ads_client = None

try:
    if GA4_PROPERTY_ID and GA4_CLIENT_EMAIL and GA4_PRIVATE_KEY:
        from google.oauth2 import service_account
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
        # Build credentials from env (private key with \n escaped)
        pk = GA4_PRIVATE_KEY.replace("\\n", "\n")
        info = {
            "type": "service_account",
            "client_email": GA4_CLIENT_EMAIL,
            "private_key": pk,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        ga4_client = BetaAnalyticsDataClient(credentials=credentials)
except Exception as e:
    ga4_client = None

try:
    if ADS_DEVELOPER_TOKEN and ADS_CUSTOMER_ID and ADS_OAUTH_CLIENT_ID and ADS_OAUTH_CLIENT_SECRET and ADS_OAUTH_REFRESH_TOKEN:
        from google.ads.googleads.client import GoogleAdsClient
        ads_config = {
            "developer_token": ADS_DEVELOPER_TOKEN,
            "client_id": ADS_OAUTH_CLIENT_ID,
            "client_secret": ADS_OAUTH_CLIENT_SECRET,
            "refresh_token": ADS_OAUTH_REFRESH_TOKEN,
            "login_customer_id": ADS_LOGIN_CUSTOMER_ID,
            "use_proto_plus": True,
        }
        ads_client = GoogleAdsClient.load_from_dict(ads_config)
except Exception as e:
    ads_client = None

# IMPORTANT: All routes must be prefixed with '/api' per ingress rules
app = FastAPI(title="Calma Data API", version="1.1.0")

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


# ------------------------- Integrations -------------------------

def ga4_sum_item_revenue(start: str, end: str) -> float:
    if not ga4_client or not GA4_PROPERTY_ID:
        return None
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="itemRevenue")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
    )
    resp = ga4_client.run_report(req)
    total = 0.0
    for row in resp.rows:
        total += float(row.metric_values[0].value or 0)
    return round(total, 2)


def ga4_count_reservations(start: str, end: str) -> int:
    if not ga4_client or not GA4_PROPERTY_ID:
        return None
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest, FilterExpression, Filter
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="eventName")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimension_filter=FilterExpression(filter=Filter(field_name="eventName", string_filter=Filter.StringFilter(value="reservation")))
    )
    resp = ga4_client.run_report(req)
    if not resp.rows:
        # fallback: use conversions metric if reservation not tracked
        req2 = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="conversions")],
            date_ranges=[DateRange(start_date=start, end_date=end)],
        )
        resp2 = ga4_client.run_report(req2)
        total = 0
        for r in resp2.rows:
            total += int(r.metric_values[0].value or 0)
        return total
    total = 0
    for r in resp.rows:
        total += int(r.metric_values[0].value or 0)
    return total


def ga4_sum_nights(start: str, end: str, param_name: str = "nights") -> int:
    if not ga4_client or not GA4_PROPERTY_ID:
        return None
    # Try to read numeric custom parameter via dimension customEvent:param and multiply by eventCount
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
    dim_name = f"customEvent:{param_name}"
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="eventName"), Dimension(name=dim_name)],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
    )
    resp = ga4_client.run_report(req)
    total = 0
    for row in resp.rows:
        try:
            n = float(row.dimension_values[1].value or 0)
            c = int(row.metric_values[0].value or 0)
            total += int(n * c)
        except Exception:
            continue
    return int(total)


def ads_totals(start: str, end: str) -> Dict[str, Any]:
    if not ads_client or not ADS_CUSTOMER_ID:
        return None
    service = ads_client.get_service("GoogleAdsService")
    customer_id = ADS_CUSTOMER_ID.replace("-", "")
    query = f"""
        SELECT segments.date, metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.average_cpc
        FROM customer
        WHERE segments.date BETWEEN '{start}' AND '{end}'
    """
    resp = service.search(customer_id=customer_id, query=query)
    clicks = 0
    imp = 0
    cost = 0.0
    cpc = 0.0
    days = 0
    for row in resp:
        days += 1
        clicks += int(row.metrics.clicks or 0)
        imp += int(row.metrics.impressions or 0)
        cost += (row.metrics.cost_micros or 0) / 1_000_000
        cpc += ((row.metrics.average_cpc or 0) / 1_000_000)
    avg_cpc = round((cpc / days) if days else (cost / clicks if clicks else 0), 2)
    return {"clicks": clicks, "impressoes": imp, "custo": round(cost, 2), "cpc": avg_cpc}


def ads_campaign_rows(start: str, end: str) -> List[Dict[str, Any]]:
    if not ads_client or not ADS_CUSTOMER_ID:
        return None
    service = ads_client.get_service("GoogleAdsService")
    customer_id = ADS_CUSTOMER_ID.replace("-", "")
    query = f"""
        SELECT campaign.name, metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.average_cpc, metrics.conversions, metrics.conversions_value
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
    """
    resp = service.search(customer_id=customer_id, query=query)
    rows = []
    for row in resp:
        clicks = int(row.metrics.clicks or 0)
        imp = int(row.metrics.impressions or 0)
        cost = (row.metrics.cost_micros or 0) / 1_000_000
        cpc = (row.metrics.average_cpc or 0) / 1_000_000
        conv = int(row.metrics.conversions or 0)
        revenue = float(row.metrics.conversions_value or 0)
        ctr = (clicks / imp) if imp else 0
        roas = (revenue / cost) if cost else 0
        rows.append({
            "name": row.campaign.name,
            "clicks": clicks,
            "impressoes": imp,
            "ctr": round(ctr, 4),
            "cpc": round(cpc if cpc else (cost / clicks if clicks else 0), 2),
            "custo": round(cost, 2),
            "conversoes": conv,
            "receita": round(revenue, 2),
            "roas": round(roas, 2)
        })
    return rows


# ------------------------- Endpoints -------------------------

@app.get("/api/kpis", response_model=KPIResponse)
async def get_kpis(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    s, e = parse_dates(start, end)
    key = f"kpis-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=int(os.environ.get("GA4_CACHE_TTL_SECONDS", "900")))
        if cached:
            return cached

    # Default values via mocks
    data = mock_kpis(s, e)

    # Integrations override when available
    try:
        r = ga4_sum_item_revenue(start, end)
        if r is not None:
            data["receita"] = r
    except Exception:
        pass

    try:
        reservas = ga4_count_reservations(start, end)
        if reservas is not None:
            data["reservas"] = reservas
    except Exception:
        pass

    try:
        nights = ga4_sum_nights(start, end, param_name="nights")
        if nights is not None:
            data["diarias"] = nights
    except Exception:
        pass

    try:
        ads = ads_totals(start, end)
        if ads is not None:
            data.update(ads)
    except Exception:
        pass

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

    points = None
    if ga4_client and GA4_PROPERTY_ID:
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
        # GA4: First user primary channel group (Default Channel Group)
        req = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="firstUserPrimaryChannelGroup"), Dimension(name="date")],
            metrics=[Metric(name="users")],
            date_ranges=[DateRange(start_date=start, end_date=end)],
        )
        try:
            resp = ga4_client.run_report(req)
            bucket: Dict[str, Dict[str, float]] = {}
            for row in resp.rows:
                ch = row.dimension_values[0].value or "(other)"
                d = row.dimension_values[1].value
                v = float(row.metric_values[0].value or 0)
                bucket.setdefault(d, {})[ch] = v
            points = [{"date": d, "values": bucket[d]} for d in sorted(bucket.keys())]
        except Exception:
            points = None

    if points is None:
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
    # Simulated until UH type exists in data source
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

    rows = None
    try:
        rows = ads_campaign_rows(start, end)
    except Exception:
        rows = None

    if rows is None:
        rows = mock_performance_table(s, e)

    payload = {"rows": rows}
    cache.set(key, payload)
    return payload


# Healthcheck
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "integrations": {
            "ga4": bool(ga4_client),
            "google_ads": bool(ads_client)
        }
    }