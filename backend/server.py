from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import os
import random
from pathlib import Path
import json
import unicodedata
import re

# Load local .env (for local/dev runs). In container/production, real envs override.
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv_path=Path(__file__).with_name('.env'))
except Exception:
    pass

# -------------------- ENV --------------------
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID") or os.environ.get("GA4_PROPERTY")
GA4_CLIENT_EMAIL = os.environ.get("GA4_CLIENT_EMAIL")
GA4_PRIVATE_KEY = os.environ.get("GA4_PRIVATE_KEY")
GA4_SERVICE_ACCOUNT_JSON = os.environ.get("GA4_SERVICE_ACCOUNT_JSON")  # optional: full JSON string
GA4_SERVICE_ACCOUNT_FILE = os.environ.get("GA4_SERVICE_ACCOUNT_FILE")  # optional: path to JSON key file
GA4_PROJECT_ID = os.environ.get("GA4_PROJECT_ID")  # optional
GA4_QUOTA_PROJECT_ID = os.environ.get("GA4_QUOTA_PROJECT_ID")  # optional

ADS_DEVELOPER_TOKEN = os.environ.get("ADS_DEVELOPER_TOKEN")
ADS_LOGIN_CUSTOMER_ID = os.environ.get("ADS_LOGIN_CUSTOMER_ID")
ADS_CUSTOMER_ID = os.environ.get("ADS_CUSTOMER_ID")
ADS_OAUTH_CLIENT_ID = os.environ.get("ADS_OAUTH_CLIENT_ID")
ADS_OAUTH_CLIENT_SECRET = os.environ.get("ADS_OAUTH_CLIENT_SECRET")
ADS_OAUTH_REFRESH_TOKEN = os.environ.get("ADS_OAUTH_REFRESH_TOKEN")

# -------------------- CLIENT INIT --------------------

ga4_client = None
ads_client = None


def build_ga4_client():
    try:
        from google.oauth2 import service_account
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
    except Exception as e:
        print(f"[GA4] google libs not available: {e}")
        return None

    cred = None
    try:
        # 1) Full JSON from env
        if GA4_SERVICE_ACCOUNT_JSON:
            try:
                info = json.loads(GA4_SERVICE_ACCOUNT_JSON)
                cred = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/analytics.readonly"])
            except Exception as e:
                print(f"[GA4] Failed JSON-from-env parse: {e}")
        # 2) JSON key file path
        if cred is None and GA4_SERVICE_ACCOUNT_FILE and Path(GA4_SERVICE_ACCOUNT_FILE).exists():
            try:
                cred = service_account.Credentials.from_service_account_file(GA4_SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/analytics.readonly"])
            except Exception as e:
                print(f"[GA4] Failed file-from-path: {e}")
        # 3) Minimal info from email + private key
        if cred is None and GA4_CLIENT_EMAIL and GA4_PRIVATE_KEY:
            pk = GA4_PRIVATE_KEY.replace("\\n", "\n")
            info = {
                "type": "service_account",
                "client_email": GA4_CLIENT_EMAIL,
                "private_key": pk,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            if GA4_PROJECT_ID:
                info["project_id"] = GA4_PROJECT_ID
            cred = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/analytics.readonly"])
        if cred is None:
            print("[GA4] No credentials found in env")
            return None
        if GA4_QUOTA_PROJECT_ID:
            try:
                cred = cred.with_quota_project(GA4_QUOTA_PROJECT_ID)
            except Exception as e:
                print(f"[GA4] with_quota_project failed: {e}")
        client = BetaAnalyticsDataClient(credentials=cred)
        return client
    except Exception as e:
        print(f"[GA4] init failed: {e}")
        return None


def build_ads_client():
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except Exception as e:
        print(f"[ADS] google-ads lib not available: {e}")
        return None
    try:
        if not ADS_DEVELOPER_TOKEN or not ADS_OAUTH_CLIENT_ID or not ADS_OAUTH_CLIENT_SECRET or not ADS_OAUTH_REFRESH_TOKEN:
            print("[ADS] Missing required envs for Ads")
            return None
        cfg = {
            "developer_token": ADS_DEVELOPER_TOKEN,
            "client_id": ADS_OAUTH_CLIENT_ID,
            "client_secret": ADS_OAUTH_CLIENT_SECRET,
            "refresh_token": ADS_OAUTH_REFRESH_TOKEN,
            "use_proto_plus": True,
        }
        if ADS_LOGIN_CUSTOMER_ID:
            cfg["login_customer_id"] = ADS_LOGIN_CUSTOMER_ID
        client = GoogleAdsClient.load_from_dict(cfg)
        return client
    except Exception as e:
        print(f"[ADS] init failed: {e}")
        return None


ga4_client = build_ga4_client()
ads_client = build_ads_client()

# -------------------- APP --------------------
app = FastAPI(title="Calma Data API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- CACHE --------------------
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

# -------------------- UTILS --------------------

def daterange(start_date: datetime, end_date: datetime):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def parse_dates(start: str, end: str):
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    return start_dt, end_dt


def fmt_ddmmyy(dt: datetime) -> str:
    return dt.strftime("%d/%m/%y")


def _normalize_name_key(s: str) -> str:
    if not s:
        return ""
    s_nfkd = unicodedata.normalize("NFKD", s)
    s_noacc = "".join(c for c in s_nfkd if not unicodedata.combining(c))
    s_clean = re.sub(r"[^a-z0-9]+", " ", s_noacc.lower())
    return re.sub(r"\s+", " ", s_clean).strip()

_PT_CHARS = set("çãõáéíóúâêôàÇÃÕÁÉÍÓÚÂÊÔÀ")
_PT_HINTS = {"quarto","andar","térreo","terreo","superior","opção","romântico","romantico","cozinha","suíte","suite","luxo","planta","baja","duplo","triple","térreo"}

# Optional alias map to force canonical PT-BR labels per normalized name or itemId
ALIAS_PT: Dict[str, str] = {
    # normalized-name -> canonical label
    "habitacion triple planta baja": "Quarto Triplo – Térreo",
    "quarto terreo com mini cozinha e banheira": "Quarto térreo c/ cozinha e banheira",
    # You can add more aliases here as needed.
}

def _is_pt_br_label(label: str) -> bool:
    if not label:
        return False
    if any(ch in _PT_CHARS for ch in label):
        return True
    low = label.lower()
    return any(tok in low for tok in _PT_HINTS)

def _alias_from_candidates(names: Dict[str, float], item_id: Optional[str] = None) -> Optional[str]:
    # Try alias by normalized candidate names first (by highest revenue preference)
    sorted_names = sorted(names.items(), key=lambda x: x[1], reverse=True)
    for nm, _ in sorted_names:
        key = _normalize_name_key(nm)
        if key in ALIAS_PT:
            return ALIAS_PT[key]
    # Then by item_id (if specific mapping exists)
    if item_id and item_id in ALIAS_PT:
        return ALIAS_PT[item_id]
    return None

# -------------------- CONSTANTS --------------------
CHANNELS = ["Organic Search", "Paid Search", "Direct", "Paid Social", "Organic Social", "Referral", "Display"]
UH_TYPES = ["Standard", "Deluxe", "Suite", "Bungalow"]

# -------------------- SCHEMAS --------------------
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

class RevUHSummaryRow(BaseModel):
    name: str
    receita: float
    receita_prev: float
    delta_pct: float

class RevUHSummaryResponse(BaseModel):
    rows: List[RevUHSummaryRow]
    insights: List[str]

class AcqSummaryRow(BaseModel):
    channel: str
    users: int
    users_prev: int
    delta_pct: float

class AcqSummaryResponse(BaseModel):
    rows: List[AcqSummaryRow]
    insights: List[str]

class StackedBarPoint(BaseModel):
    label: str
    values: Dict[str, float]

class StackedBarsResponse(BaseModel):
    series_labels: List[str]
    points: List[StackedBarPoint]

class HeatCell(BaseModel):
    day: int
    hour: int
    value: float

class HeatmapResponse(BaseModel):
    cells: List[HeatCell]

class PerformanceRow(BaseModel):
    name: str
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

class ADRPoint(BaseModel):
    date: str
    adr: float

class ADRResponse(BaseModel):
    points: List[ADRPoint]

class DialsResponse(BaseModel):
    cr: Dict[str, float]
    roas: Dict[str, float]

# -------------------- MOCKS (used only where allowed) --------------------

def seeded_rand(seed: str) -> random.Random:
    r = random.Random(); r.seed(seed); return r


def mock_kpis(start: datetime, end: datetime) -> dict:
    r = seeded_rand(f"kpis-{start}-{end}")
    days = (end - start).days + 1
    clicks = int(r.uniform(500, 3000) * days / 14)
    imp = int(clicks * r.uniform(8, 20))
    cpc = round(r.uniform(1.5, 4.5), 2)
    custo = round(clicks * cpc, 2)
    reservas = int(r.uniform(20, 120) * days / 14)
    diarias = int(reservas * r.uniform(1.3, 2.1))
    receita = round(diarias * r.uniform(180, 380), 2)
    return {"receita": receita, "reservas": reservas, "diarias": diarias, "clicks": clicks, "impressoes": imp, "cpc": cpc, "custo": custo}


def mock_acquisition_timeseries(metric: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    r = seeded_rand(f"acq-{metric}-{start}-{end}")
    points = []
    for d in daterange(start, end):
        base = 100 + (d.weekday() * 10)
        values = {}
        for ch in CHANNELS:
            values[ch] = round(base * (1 + CHANNELS.index(ch) * 0.15) * r.uniform(0.7, 1.3), 2)
        points.append({"date": d.strftime("%Y-%m-%d"), "values": values})
    return points

# -------------------- INTEGRATIONS (GA4/ADS) --------------------

def ga4_revenue_qty_by_date(start: str, end: str) -> Optional[List[Dict[str, Any]]]:
    """
    Strict logic requested: by date of sale only.
    Query GA4 grouped by date with metrics itemRevenue and itemsPurchased.
    Returns list of {date: 'DD/MM/YY', revenue: float, qty: float}
    """
    if not ga4_client or not GA4_PROPERTY_ID:
        return None
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

    s_dt, e_dt = parse_dates(start, end)
    try:
        req = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="itemRevenue"), Metric(name="itemsPurchased")],
            date_ranges=[DateRange(start_date=start, end_date=end)],
            limit=250000,
        )
        resp = ga4_client.run_report(req)
        bucket: Dict[str, Dict[str, float]] = {}
        for row in resp.rows:
            d_raw = row.dimension_values[0].value
            try:
                d = datetime.strptime(d_raw, "%Y%m%d")
            except Exception:
                continue
            k = fmt_ddmmyy(d)
            rev = float(row.metric_values[0].value or 0)
            qty = float(row.metric_values[1].value or 0)
            bucket[k] = {"revenue": round(rev, 2), "qty": round(qty, 4)}
        out = []
        for d in daterange(s_dt, e_dt):
            k = fmt_ddmmyy(d)
            cell = bucket.get(k, {"revenue": 0.0, "qty": 0.0})
            out.append({"date": k, **cell})
        return out
    except Exception as e:
        print(f"[GA4] revenue/qty by date failed: {e}")
        return None


def ads_enabled_campaign_totals(start: str, end: str) -> Optional[Dict[str, Any]]:
    if not ads_client or not ADS_CUSTOMER_ID:
        return None
    service = ads_client.get_service("GoogleAdsService")
    customer_id = ADS_CUSTOMER_ID.replace("-", "")
    query = f"""
        SELECT campaign.status, metrics.clicks, metrics.conversions, metrics.conversions_value, metrics.cost_micros
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
          AND campaign.status = 'ENABLED'
    """
    resp = service.search(customer_id=customer_id, query=query)
    clicks = conv = 0
    conv_value = cost = 0.0
    for row in resp:
        clicks += int(row.metrics.clicks or 0)
        conv += int(row.metrics.conversions or 0)
        conv_value += float(row.metrics.conversions_value or 0)
        cost += (row.metrics.cost_micros or 0) / 1_000_000
    cr = (conv / clicks) if clicks else 0.0
    roas = (conv_value / cost) if cost else 0.0
    return {"clicks": clicks, "conversions": conv, "conv_value": round(conv_value, 2), "cost": round(cost, 2), "cr": cr, "roas": roas}

def ga4_sum_item_revenue(start: str, end: str) -> Optional[float]:
    if not ga4_client or not GA4_PROPERTY_ID:
        return None
    from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
    # Query without dimensions to get total directly
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        metrics=[Metric(name="itemRevenue")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
    )
    resp = ga4_client.run_report(req)
    total = 0.0
    for row in resp.rows:
        total += float(row.metric_values[0].value or 0)
    return round(total, 2)


def ga4_count_reservations(start: str, end: str) -> Optional[int]:
    if not ga4_client or not GA4_PROPERTY_ID:
        return None
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest, FilterExpression, Filter
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="eventName")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimension_filter=FilterExpression(filter=Filter(field_name="eventName", string_filter=Filter.StringFilter(value="purchase")))
    )
    resp = ga4_client.run_report(req)
    if not resp.rows:
        # fallback opcional para conversions
        req2 = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="conversions")],
            date_ranges=[DateRange(start_date=start, end_date=end)],
            limit=1,
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


def ga4_revenue_by_item_per_day(start: str, end: str) -> Optional[List[Dict[str, Any]]]:
    if not ga4_client or not GA4_PROPERTY_ID:
        return None
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

    s_dt, e_dt = parse_dates(start, end)
    date_labels = [fmt_ddmmyy(d) for d in daterange(s_dt, e_dt)]

    def build_points(group_map: Dict[str, Dict[str, float]], label_map: Dict[str, str]) -> List[Dict[str, Any]]:
        # include only items with total > 0
        keys_included = [k for k, per in group_map.items() if sum(per.values()) > 0]
        # map each key to canonical label and collapse non-"Quarto" into 'Extras'
        def canonical_label_for(k: str) -> str:
            base = label_map.get(k, str(k))
            if not base:
                return "Extras"
            low = base.lower().strip()
            if not low.startswith("quarto"):
                return "Extras"
            return base
        # aggregate per final label per day
        agg: Dict[str, Dict[str, float]] = {}
        for k in keys_included:
            lab = canonical_label_for(k)
            for d, v in group_map.get(k, {}).items():
                agg.setdefault(lab, {})
                agg[lab][d] = agg[lab].get(d, 0.0) + float(v or 0)
        # build points with zero-fill
        pts: List[Dict[str, Any]] = []
        for d in date_labels:
            values = {lab: round(agg.get(lab, {}).get(d, 0.0), 2) for lab in agg.keys()}
            pts.append({"date": d, "values": values})
        return pts

    # Try with itemId + itemName + date (preferred)
    try:
        req_id = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="itemId"), Dimension(name="itemName"), Dimension(name="date")],
            metrics=[Metric(name="itemRevenue")],
            date_ranges=[DateRange(start_date=start, end_date=end)],
            limit=250000,
        )
        resp_id = ga4_client.run_report(req_id)
        has_id = False
        group: Dict[str, Dict[str, float]] = {}
        labels: Dict[str, Dict[str, float]] = {}
        for row in resp_id.rows:
            item_id = (row.dimension_values[0].value or "").strip()
            name = (row.dimension_values[1].value or "").strip()
            d_raw = row.dimension_values[2].value
            if item_id:
                has_id = True
            try:
                d_fmt = fmt_ddmmyy(datetime.strptime(d_raw, "%Y%m%d"))
            except Exception:
                continue
            val = float(row.metric_values[0].value or 0)
            key = item_id if item_id else f"_noid::{_normalize_name_key(name)}"
            group.setdefault(key, {})
            group[key][d_fmt] = group[key].get(d_fmt, 0.0) + val
            labels.setdefault(key, {})
            labels[key][name] = labels[key].get(name, 0.0) + val
        if has_id and group:
            canonical: Dict[str, str] = {}
            for k, cand in labels.items():
                # Prefer explicit alias if available
                alias = _alias_from_candidates(cand, item_id=k if not str(k).startswith("_noid::") else None)
                if alias:
                    canonical[k] = alias
                    continue
                # Otherwise prefer a PT-BR looking label among candidates
                pt = [(nm, rv) for nm, rv in cand.items() if _is_pt_br_label(nm)]
                if pt:
                    canonical[k] = max(pt, key=lambda x: x[1])[0]
                else:
                    canonical[k] = max(cand.items(), key=lambda x: x[1])[0]
            return build_points(group, canonical)
    except Exception as e:
        print(f"[GA4] itemId path failed: {e}")

    # Fallback to itemName + date normalization
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="itemName"), Dimension(name="date")],
        metrics=[Metric(name="itemRevenue")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        limit=250000,
    )
    resp = ga4_client.run_report(req)
    group2: Dict[str, Dict[str, float]] = {}
    labels2: Dict[str, Dict[str, float]] = {}
    for row in resp.rows:
        name = (row.dimension_values[0].value or "").strip()
        d_raw = row.dimension_values[1].value
        try:
            d_fmt = fmt_ddmmyy(datetime.strptime(d_raw, "%Y%m%d"))
        except Exception:
            continue
        val = float(row.metric_values[0].value or 0)
        key = _normalize_name_key(name)
        group2.setdefault(key, {})
        group2[key][d_fmt] = group2[key].get(d_fmt, 0.0) + val
        labels2.setdefault(key, {})
        labels2[key][name] = labels2[key].get(name, 0.0) + val
    canonical2: Dict[str, str] = {}
    for k, cand in labels2.items():
        # Try explicit alias first
        alias = _alias_from_candidates(cand)
        if alias:
            canonical2[k] = alias
            continue
        pt = [(nm, rv) for nm, rv in cand.items() if _is_pt_br_label(nm)]
        if pt:
            canonical2[k] = max(pt, key=lambda x: x[1])[0]
        else:
            canonical2[k] = max(cand.items(), key=lambda x: x[1])[0]
    return build_points(group2, canonical2)

# -------------------- ADS HELPERS --------------------

def ads_totals(start: str, end: str) -> Optional[Dict[str, Any]]:
    if not ads_client or not ADS_CUSTOMER_ID:
        return None
    from google.ads.googleads.client import GoogleAdsClient  # type: ignore
    service = ads_client.get_service("GoogleAdsService")
    customer_id = ADS_CUSTOMER_ID.replace("-", "")
    query = f"""
        SELECT segments.date, metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.average_cpc
        FROM customer
        WHERE segments.date BETWEEN '{start}' AND '{end}'
    """
    resp = service.search(customer_id=customer_id, query=query)
    clicks = imp = 0
    cost = cpc = 0.0
    days = 0
    for row in resp:
        days += 1
        clicks += int(row.metrics.clicks or 0)
        imp += int(row.metrics.impressions or 0)
        cost += (row.metrics.cost_micros or 0) / 1_000_000
        cpc += ((row.metrics.average_cpc or 0) / 1_000_000)
    avg_cpc = round((cpc / days) if days else (cost / clicks if clicks else 0), 2)
    return {"clicks": clicks, "impressoes": imp, "custo": round(cost, 2), "cpc": avg_cpc}


def ads_campaign_rows(start: str, end: str) -> Optional[List[Dict[str, Any]]]:
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

# -------------------- ENDPOINTS --------------------
@app.get("/api/kpis", response_model=KPIResponse)
async def get_kpis(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    s, e = parse_dates(start, end)
    key = f"kpis-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=int(os.environ.get("GA4_CACHE_TTL_SECONDS", "900")))
        if cached:
            return cached
    data = mock_kpis(s, e)
    try:
        r = ga4_sum_item_revenue(start, end)
        if r is not None:
            data["receita"] = r
    except Exception as e:
        print(f"[GA4] kpis revenue failed: {e}")
    try:
        reservas = ga4_count_reservations(start, end)
        if reservas is not None:
            data["reservas"] = reservas
    except Exception as e:
        print(f"[GA4] kpis reservas failed: {e}")
    try:
        ads = ads_totals(start, end)
        if ads is not None:
            data.update(ads)
    except Exception as e:
        print(f"[ADS] kpis ads failed: {e}")
    cache.set(key, data)
    return data


@app.get("/api/acquisition-by-channel", response_model=TimeSeriesResponse)
async def acquisition_by_channel(metric: str = Query("users"), start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    # Always be resilient: any exception -> mock, never 500
    try:
        s, e = parse_dates(start, end)
        key = f"acq-{metric}-{start}-{end}"
        if not refresh:
            cached = cache.get(key, ttl_seconds=15 * 60)
            if cached:
                return cached

        def run_with_dim(dim_name: str) -> Optional[List[Dict[str, Any]]]:
            from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
            req = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[Dimension(name=dim_name), Dimension(name="date")],
                metrics=[Metric(name="users")],
                date_ranges=[DateRange(start_date=start, end_date=end)],
            )
            resp = ga4_client.run_report(req)
            bucket: Dict[str, Dict[str, float]] = {}
            for row in resp.rows:
                ch = row.dimension_values[0].value or "Unassigned"
                d = row.dimension_values[1].value  # YYYYMMDD
                v = float(row.metric_values[0].value or 0)
                bucket.setdefault(d, {})[ch] = v
            ordered: List[Dict[str, Any]] = []
            for dt in daterange(s, e):
                key_dt = dt.strftime("%Y%m%d")
                values = bucket.get(key_dt, {})
                ordered.append({"date": fmt_ddmmyy(dt), "values": values})
            return ordered

        points: Optional[List[Dict[str, Any]]] = None
        if ga4_client and GA4_PROPERTY_ID:
            try:
                # Try primary channel group first
                points = run_with_dim("firstUserPrimaryChannelGroup")
            except Exception as e:
                print(f"[GA4] primaryChannelGroup failed: {e}")
                points = None
            if points is None:
                try:
                    # Fallback to default channel grouping (universally supported)
                    points = run_with_dim("firstUserDefaultChannelGroup")
                except Exception as e:
                    print(f"[GA4] defaultChannelGroup failed: {e}")
                    points = None
        # Final fallback to mock (never 500)
        if points is None:
            raw = mock_acquisition_timeseries(metric, s, e)
            points = [{"date": fmt_ddmmyy(datetime.strptime(p["date"], "%Y-%m-%d")), "values": p["values"]} for p in raw]

        payload = {"metric": metric, "points": points}
        cache.set(key, payload)
        return payload
    except Exception as e:
        print(f"[ACQ] endpoint fatal error -> using mock: {e}")
        # last resort: 7-day mock using provided dates (if parse failed, fallback around 'today')
        try:
            s, e = parse_dates(start, end)
        except Exception:
            today = datetime.utcnow().date()
            s = datetime(today.year, today.month, today.day) - timedelta(days=6)
            e = datetime(today.year, today.month, today.day)
        raw = mock_acquisition_timeseries(metric, s, e)
        points = [{"date": fmt_ddmmyy(datetime.strptime(p["date"], "%Y-%m-%d")), "values": p["values"]} for p in raw]
        return {"metric": metric, "points": points}


@app.get("/api/revenue-by-uh", response_model=RevenueByUHResponse)
async def revenue_by_uh(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    # Validate dates upfront (invalid → 422)
    try:
        parse_dates(start, end)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid date format: {str(e)}")

    # No mock fallback here per request; if GA4 not available, return empty series
    key = f"revuh-item-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    points: List[Dict[str, Any]] = []
    try:
        result = ga4_revenue_by_item_per_day(start, end)
        if result is not None:
            points = result
    except Exception as e:
        print(f"[GA4] revenue-by-uh failed: {e}")
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
    # keep mock until real UH stack source exists (12 months density)
    months = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    from random import randint
    payload = {"series_labels": UH_TYPES, "points": [{"label": m, "values": {t: randint(60,260) for t in UH_TYPES}} for m in months]}
    cache.set(key, payload)
    return payload


@app.get("/api/campaign-conversion-heatmap", response_model=HeatmapResponse)
async def campaign_conversion_heatmap(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    # keep mock heatmap for now
    s, e = parse_dates(start, end)
    key = f"heatmap-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    cells = []
    for day in range(7):
        for hour in range(24):
            base = 2 + (6 - abs(12 - hour)) * 0.8
            val = max(0, random.gauss(mu=base, sigma=1.4))
            cells.append({"day": day, "hour": hour, "value": round(val, 2)})
    payload = {"cells": cells}
    cache.set(key, payload)
    return payload


@app.get("/api/performance-table", response_model=PerformanceTableResponse)
async def performance_table(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    key = f"table-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    rows = None
    try:
        rows = ads_campaign_rows(start, end)
    except Exception as e:
        print(f"[ADS] table failed: {e}")
        rows = None
    if rows is None:
        # basic mock if ads unavailable
        rows = []
    payload = {"rows": rows}
    cache.set(key, payload)
    return payload


@app.get("/api/adr", response_model=ADRResponse)
async def adr_by_stay_date(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    s, e = parse_dates(start, end)
    key = f"adr-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15 * 60)
        if cached:
            return cached
    points: List[Dict[str, Any]] = []
    try:
        rows = ga4_revenue_qty_by_date(start, end)
        if rows is not None:
            for r in rows:
                adr = (r["revenue"] / r["qty"]) if r.get("qty") else 0.0
                points.append({"date": r["date"], "adr": round(adr, 2)})
    except Exception as e:
        print(f"[GA4] ADR endpoint failed: {e}")
    payload = {"points": points}
    cache.set(key, payload)
    return payload


@app.get("/api/marketing-dials", response_model=DialsResponse)
async def marketing_dials(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    # Returns CR and ROAS with comparison to previous equivalent period
    s, e = parse_dates(start, end)
    prev = (s - timedelta(days=(e - s).days + 1), s - timedelta(days=1))
    prev_start = prev[0].strftime("%Y-%m-%d")
    prev_end = prev[1].strftime("%Y-%m-%d")

    key = f"dials-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=10 * 60)
        if cached:
            return cached

    def pack(val: float, prev_val: float) -> Dict[str, float]:
        delta = 0.0
        if prev_val == 0:
            delta = 100.0 if val > 0 else 0.0
        else:
            delta = (val - prev_val) / prev_val * 100.0
        return {"value": round(val, 4), "prev": round(prev_val, 4), "delta_pct": round(delta, 1)}

    cr_pack = {"value": 0.0, "prev": 0.0, "delta_pct": 0.0}
    roas_pack = {"value": 0.0, "prev": 0.0, "delta_pct": 0.0}

    try:
        cur = ads_enabled_campaign_totals(start, end) or {}
        prv = ads_enabled_campaign_totals(prev_start, prev_end) or {}
        cr_pack = pack(cur.get("cr", 0.0), prv.get("cr", 0.0))
        roas_pack = pack(cur.get("roas", 0.0), prv.get("roas", 0.0))
    except Exception as e:
        print(f"[ADS] dials failed: {e}")

    payload = {"cr": cr_pack, "roas": roas_pack}
    cache.set(key, payload)
    return payload


# -------------------- HEALTH --------------------
@app.get("/api/health")
async def health():
    ga4_ok = False
    ads_ok = False
    # GA4 quick check with itemRevenue over last 7 days
    try:
        if GA4_PROPERTY_ID:
            client = ga4_client or build_ga4_client()
            if client:
                from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
                end = datetime.utcnow().strftime("%Y-%m-%d")
                start = (datetime.utcnow() - timedelta(days=6)).strftime("%Y-%m-%d")
                req = RunReportRequest(
                    property=f"properties/{GA4_PROPERTY_ID}",
                    metrics=[Metric(name="itemRevenue")],
                    date_ranges=[DateRange(start_date=start, end_date=end)],
                )
                _ = client.run_report(req)
                ga4_ok = True
    except Exception as e:
        print(f"[GA4] health failed: {e}")
        ga4_ok = False

    # Ads quick check
    try:
        client = ads_client or build_ads_client()
        if client and ADS_CUSTOMER_ID:
            service = client.get_service("GoogleAdsService")
            customer_id = ADS_CUSTOMER_ID.replace("-", "")
            _ = service.search(customer_id=customer_id, query="SELECT campaign.id FROM campaign LIMIT 1")
            ads_ok = True
    except Exception as e:
        print(f"[ADS] health failed: {e}")
        ads_ok = False

    return {"status": "ok", "time": datetime.utcnow().isoformat(), "integrations": {"ga4": ga4_ok, "google_ads": ads_ok}}