# Updated: 2025-09-27 18:30 - Fixed OpenAI model and added Emergent LLM support
from fastapi import FastAPI, Query, HTTPException, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, date
import os
import random
from pathlib import Path
import json
import unicodedata
import re
import uuid
import base64
from datetime import datetime, timedelta, timezone


# JWT and password hashing
from jose import JWTError, jwt
from passlib.context import CryptContext



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

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# JWT Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Security
security = HTTPBearer()

# Allowed email domains
ALLOWED_DOMAINS = ["@ilhafaceira.com.br", "@amandagattiboni.com"]
ALLOWED_EMAILS = ["alangattiboni@gmail.com"]

# ----- OpenAI (opcional) -----
try:
    from openai import OpenAI
except Exception as _e:
    OpenAI = None

openai_client = None
try:
    if os.environ.get("OPENAI_API_KEY") and OpenAI:
        openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    print("[OPENAI] init failed:", e)



# -------------------- CLIENT INIT --------------------

ga4_client = None
ads_client = None

# -------------------- SUPABASE CLIENT INIT --------------------

supabase_client = None

def build_supabase_client():
    """Initialize Supabase client"""
    global supabase_client
    if supabase_client:
        return supabase_client

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("[SUPABASE] Missing credentials")
        return None

    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("[SUPABASE] Client initialized")
        return supabase_client
    except Exception as e:
        print(f"[SUPABASE] Client init failed: {e}")
        return None


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
    """
    Totais agregados para KPIs dos dials (CR e ROAS) no período.
    Retorna: {"clicks", "conversions", "value", "cost", "cr", "roas"}
    """
    if not ads_client or not ADS_CUSTOMER_ID:
        return None

    service = ads_client.get_service("GoogleAdsService")
    customer_id = ADS_CUSTOMER_ID.replace("-", "")

    query = f"""
        SELECT
          metrics.clicks,
          metrics.conversions,
          metrics.conversions_value,
          metrics.cost_micros
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
          AND metrics.impressions > 0
    """

    print(f"[DEBUG] GAQL (ads_enabled_campaign_totals):\n{query}")

    try:
        resp = service.search(customer_id=customer_id, query=query)
    except Exception as e:
        print(f"[ERROR] ads_enabled_campaign_totals: {e}")
        return None

    clicks = 0
    conv = 0.0
    conv_value = 0.0
    cost = 0.0

    for row in resp:
        clicks += int(row.metrics.clicks or 0)
        conv += float(row.metrics.conversions or 0)
        conv_value += float(row.metrics.conversions_value or 0)
        cost += (row.metrics.cost_micros or 0) / 1_000_000

    cr = (conv / clicks) if clicks else 0.0
    roas = (conv_value / cost) if cost else 0.0

    return {
        "clicks": clicks,
        "conversions": round(conv, 2),
        "value": round(conv_value, 2),
        "cost": round(cost, 2),
        "cr": round(cr, 4),
        "roas": round(roas, 2),
    }


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

def ads_campaigns_filtered(start: str, end: str, status: str = "enabled"):
    if not ads_client or not ADS_CUSTOMER_ID:
        """
        Campanhas (Google Ads) no período, agregadas ao nível de campanha.
        - Mantém apenas linhas com métricas reais (impressões > 0) para garantir retorno útil.
        - Quando status='enabled', aplica filtro de status no GAQL; caso contrário, traz todas.
        Retorno: {"rows": [...], "total": {...}}
        """
        if not ads_client or not ADS_CUSTOMER_ID:
            return {"rows": [], "total": None}

        service = ads_client.get_service("GoogleAdsService")
        customer_id = ADS_CUSTOMER_ID.replace("-", "")

        # Cláusulas
        conditions = [
            f"segments.date BETWEEN '{start}' AND '{end}'",
            "metrics.impressions > 0",  # linhas sem métricas não retornam (boas práticas)
        ]
        if status == "enabled":
            conditions.append("campaign.status = 'ENABLED'")

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT
              campaign.name,
              campaign.advertising_channel_type,
              campaign.status,
              campaign.primary_status,
              metrics.clicks,
              metrics.impressions,
              metrics.interactions,
              metrics.interaction_rate,
              metrics.cost_micros,
              metrics.average_cpc,
              metrics.conversions,
              metrics.conversions_from_interactions_rate
            FROM campaign
            WHERE {where_clause}
            ORDER BY metrics.cost_micros DESC
            LIMIT 1000
        """

        print(f"[DEBUG] GAQL (ads_campaigns_filtered):\n{query}")

        try:
            resp = service.search(customer_id=customer_id, query=query)
        except Exception as e:
            print(f"[ERROR] ads_campaigns_filtered: {e}")
            return {"rows": [], "total": None}

        rows = []
        totals = {"clicks": 0, "impressions": 0, "interactions": 0, "cost": 0.0, "conversions": 0.0}

        for r in resp:
            clicks = int(r.metrics.clicks or 0)
            imps = int(r.metrics.impressions or 0)
            inter = int(r.metrics.interactions or 0)
            cost = (r.metrics.cost_micros or 0) / 1_000_000
            avg_cpc = (r.metrics.average_cpc or 0) / 1_000_000
            conv = float(r.metrics.conversions or 0)
            ir = float(r.metrics.interaction_rate or 0)
            cfr = float(r.metrics.conversions_from_interactions_rate or 0)

            # Backfills defensivos caso a API retorne 0 para algumas taxas
            if ir == 0 and imps > 0 and inter > 0:
                ir = inter / imps
            if cfr == 0 and inter > 0 and conv > 0:
                cfr = conv / inter

            cpcv = (cost / conv) if conv > 0 else 0.0

            rows.append({
                "name": r.campaign.name,
                "type": getattr(r.campaign.advertising_channel_type, "name", str(r.campaign.advertising_channel_type)),
                "clicks": clicks,
                "interaction_rate": ir,
                "cost_total": round(cost, 2),
                "avg_cpc": round(avg_cpc if avg_cpc else (cost / clicks if clicks else 0), 2),
                "conv_rate": cfr,
                "cost_per_conv": round(cpcv, 2),
                "status": getattr(r.campaign.status, "name", str(r.campaign.status)),
                "primary_status": getattr(r.campaign.primary_status, "name", str(r.campaign.primary_status)),
            })

            totals["clicks"] += clicks
            totals["impressions"] += imps
            totals["interactions"] += inter
            totals["cost"] += cost
            totals["conversions"] += conv

        rows.sort(key=lambda x: x["cost_total"], reverse=True)
        return {"rows": rows, "total": totals}


def ads_networks_breakdown(start: str, end: str):
    """
    Quebra por rede (Pesquisa Google, Parceiros de pesquisa, Display/YT) com shares.
    Retorna: {"nets": {...}, "totals": {...}, "shares": {...}}
    """
    if not ads_client or not ADS_CUSTOMER_ID:
        return None

    service = ads_client.get_service("GoogleAdsService")
    customer_id = ADS_CUSTOMER_ID.replace("-", "")

    # Usamos FROM campaign com o segmento ad_network_type (válido segundo docs)
    # e garantimos métricas reais no período.
    query = f"""
      SELECT
        segments.ad_network_type,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.conversions,
        metrics.conversions_value
      FROM campaign
      WHERE segments.date BETWEEN '{start}' AND '{end}'
        AND metrics.impressions > 0
    """

    print(f"[DEBUG] GAQL (ads_networks_breakdown):\n{query}")
    resp = service.search(customer_id=customer_id, query=query)

    nets = {
        "Google Search": {"conversions": 0.0, "cost": 0.0, "conv_value": 0.0},
        "Search partners": {"conversions": 0.0, "cost": 0.0, "conv_value": 0.0},
        "Display Network": {"conversions": 0.0, "cost": 0.0, "conv_value": 0.0},
    }

    def bucket_name(net):
        # net: enum => string
        n = net.name if hasattr(net, "name") else str(net)
        if n in ("SEARCH",):
            return "Google Search"
        if n in ("SEARCH_PARTNERS",):
            return "Search partners"
        # DISPLAY + YouTube (agrupa no "Display Network")
        return "Display Network"

    for row in resp:
        key = bucket_name(row.segments.ad_network_type)
        cost = (row.metrics.cost_micros or 0) / 1_000_000
        nets[key]["conversions"] += float(row.metrics.conversions or 0)
        nets[key]["cost"] += cost
        nets[key]["conv_value"] += float(row.metrics.conversions_value or 0)

    totals = {
        "conversions": sum(v["conversions"] for v in nets.values()),
        "cost": sum(v["cost"] for v in nets.values()),
        "conv_value": sum(v["conv_value"] for v in nets.values()),
    }

    def pct(val, tot): return (val / tot) if tot else 0.0

    shares = {
        "conversions": {k: pct(v["conversions"], totals["conversions"]) for k, v in nets.items()},
        "cost": {k: pct(v["cost"], totals["cost"]) for k, v in nets.items()},
        "conv_value": {k: pct(v["conv_value"], totals["conv_value"]) for k, v in nets.items()},
    }

    return {"nets": nets, "totals": totals, "shares": shares}

def get_env(k, default=None): 
    return os.environ.get(k, default)

async def read_file_b64(file: UploadFile):
    try:
        content = await file.read()
        b64 = base64.b64encode(content).decode('utf-8')
        await file.seek(0)
        return {"filename": file.filename, "content": b64, "content_type": file.content_type or "application/octet-stream"}
    except Exception:
        return None

async def send_feedback_via_resend(subject: str, text: str, html: str, attachments: list):
    api_key = get_env("RESEND_API_KEY")
    if not api_key: 
        return {"sent": False, "reason": "no_api_key"}
    try:
        import resend  # Ensure the resend module is imported
        resend.api_key = api_key
        params = {
            "from": get_env("FEEDBACK_FROM", "Calma Data <noreply@example.com>"),
            "to": [get_env("FEEDBACK_TO", "dev@example.com")],
            "subject": subject,
            "text": text,
            "html": html
        }
        if attachments:
            params["attachments"] = [{"filename": a["filename"], "content": a["content"]} for a in attachments]
        r = resend.Emails.send(params)
        return {"sent": True, "id": r.get("id")}
    except Exception as e:
        print("[RESEND] error:", e)
        return {"sent": False, "reason": "error"}



# -------------------- MONTHLY REPORT HELPERS (OpenAI + Mongo quota) --------------------

class MonthlyReportRequest(BaseModel):
    month: str  # 'YYYY-MM'

def prev_month_str(month_str: str) -> str:
    y, m = [int(x) for x in month_str.split("-")]
    return f"{y-1}-12" if m == 1 else f"{y}-{str(m-1).zfill(2)}"


def kpis_month(start: str, end: str) -> Dict[str, Any]:
    """Receita (GA4), Reservas (GA4), Diárias (itemsPurchased), Clicks/Impressões/CPC (Ads)."""
    receita = ga4_sum_item_revenue(start, end) or 0.0
    try:
        reservas = ga4_count_reservations(start, end) or 0
    except Exception:
        reservas = 0
    try:
        rows = ga4_revenue_qty_by_date(start, end) or []
        diarias = int(round(sum((r.get("qty") or 0) for r in rows)))
    except Exception:
        diarias = 0
    clicks = impressoes = 0
    custo = cpc = 0.0
    try:
        ads = ads_totals(start, end) or {}
        clicks = int(ads.get("clicks") or 0)
        impressoes = int(ads.get("impressoes") or 0)
        custo = float(ads.get("custo") or 0)
        cpc = float(ads.get("cpc") or (custo / clicks if clicks else 0))
    except Exception:
        pass
    return {
        "receita": round(receita, 2),
        "reservas": int(reservas),
        "diarias": int(diarias),
        "clicks": clicks,
        "impressoes": impressoes,
        "cpc": round(cpc, 2)
    }

def uh_totals_month(start: str, end: str) -> Dict[str, float]:
    """Total de receita por UH no mês."""
    out: Dict[str, float] = {}
    try:
        rows = ga4_revenue_by_item_per_day(start, end) or []
        for p in rows:
            for k, v in (p.get("values") or {}).items():
                out[k] = (out.get(k, 0) + (v or 0))
    except Exception:
        pass
    return {k: round(v, 2) for k, v in out.items()}

def acq_totals_month(start: str, end: str) -> Dict[str, float]:
    """Total de usuários por canal no mês (primeiro primary; fallback default)."""
    res: Dict[str, float] = {}
    try:
        def run_dim(dim):
            from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
            req = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[Dimension(name=dim)],
                metrics=[Metric(name="users")],
                date_ranges=[DateRange(start_date=start, end_date=end)],
                limit=250000,
            )
            resp = ga4_client.run_report(req)
            tmp = {}
            for row in resp.rows:
                ch = row.dimension_values[0].value or "Unassigned"
                tmp[ch] = (tmp.get(ch, 0) + float(row.metric_values[0].value or 0))
            return tmp
        try:
            res = run_dim("firstUserPrimaryChannelGroup")
        except Exception:
            res = run_dim("firstUserDefaultChannelGroup")
    except Exception:
        pass
    return {k: round(v, 2) for k, v in res.items()}

def pmc_series_month(start: str, end: str) -> List[Dict[str, Any]]:
    """Preço Médio por Compra por dia do mês (itemRevenue/itemsPurchased)."""
    try:
        rows = ga4_revenue_qty_by_date(start, end) or []
        out = []
        for r in rows:
            adr = (r["revenue"] / r["qty"]) if r.get("qty") else 0.0
            out.append({"date": r["date"], "pmc": round(adr, 2)})
        return out
    except Exception:
        return []

def networks_month(start: str, end: str) -> Dict[str, Any]:
    try:
        return ads_networks_breakdown(start, end) or {"nets": {}, "totals": {}, "shares": {}}
    except Exception:
        return {"nets": {}, "totals": {}, "shares": {}}

def build_gpt_prompt_pt(month: str, prev_month: str, data: Dict[str, Any]) -> str:
    return f"""
Você é um analista de dados sênior especializado em hotelaria e pousadas. Gere um relatório mensal completo (PT-BR) com insights acionáveis.

IMPORTANTE: Responda OBRIGATORIAMENTE em JSON com TODAS as 6 chaves abaixo. Cada seção deve ter pelo menos 2-3 frases de análise:

{{
  "resumo": "Análise geral do mês comparando com período anterior",
  "uh": "Insights sobre performance das categorias de unidades habitacionais",
  "acquisition": "Análise dos canais de aquisição de tráfego",
  "pmc": "Insights sobre o preço médio por compra e ticket médio",
  "networks": "Análise das redes Google Ads e performance por canal",
  "final": "Conclusões e recomendações estratégicas"
}}

Contexto:
- Mês analisado: {month}
- Mês anterior: {prev_month}

DADOS PARA ANÁLISE:

Resumo Comparativo (atual vs anterior):
{json.dumps(data.get("summary"), ensure_ascii=False, indent=2)}

Receita por UH (totais no mês):
{json.dumps(data.get("uh"), ensure_ascii=False, indent=2)}

Aquisição por canal (usuários no mês):
{json.dumps(data.get("acq"), ensure_ascii=False, indent=2)}

Preço Médio por Compra (primeiros 7 dias):
{json.dumps((data.get("pmc") or [])[:7], ensure_ascii=False, indent=2)}

Redes Google Ads (distribuição por conversões):
{json.dumps(data.get("networks", {}).get("shares", {}), ensure_ascii=False, indent=2)}

INSTRUÇÕES OBRIGATÓRIAS:
1. Compare SEMPRE {month} vs {prev_month}
2. Identifique tendências positivas/negativas
3. Para UH: analise qual categoria teve melhor performance
4. Para Acquisition: identifique canais com maior crescimento
5. Para PMC: analise se o ticket médio está subindo/descendo
6. Para Networks: menor Display = menos dependência de OTAs
7. Final: dê 2-3 recomendações práticas

Retorne APENAS o JSON válido, SEM código markdown nem explicações extras.
"""

def run_gpt_sections_safe(prompt: str) -> tuple[dict, dict]:
    """
    Tenta gerar as seções via OpenAI.
    Retorno: (sections_dict, meta_dict)
    meta = {"ok": bool, "reason": "ok" | "quota_exceeded" | "no_api_key" | "error"}
    """
    def fallback_sections():
        return {
            "resumo": "Análise automática indisponível no momento.",
            "uh": "—",
            "acquisition": "—",
            "pmc": "—",
            "networks": "—",
            "final": "—"
        }

    # Try Emergent LLM key first
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if emergent_key:
        try:
            import litellm
            
            # Use litellm with emergent proxy
            response = litellm.completion(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um analista de dados brasileiro especializado em hotelaria. Responda APENAS em JSON válido com todas as 6 chaves: resumo, uh, acquisition, pmc, networks, final."},
                    {"role": "user", "content": prompt}
                ],
                api_key=emergent_key,
                api_base="https://integrations.emergentagent.com/llm",
                custom_llm_provider="openai",
                temperature=0.2,
                max_tokens=3000  # Increased for complete JSON
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            try:
                sections = json.loads(content)
                # Ensure all required keys exist  
                required_keys = ["resumo", "uh", "acquisition", "pmc", "networks", "final"]
                for key in required_keys:
                    if key not in sections:
                        sections[key] = "—"
            except Exception as e:
                print(f"[GPT] JSON parse failed: {e}")
                sections = {
                    "resumo": content,
                    "uh": "—",
                    "acquisition": "—",
                    "pmc": "—",
                    "networks": "—",
                    "final": "—"
                }
            return sections, {"ok": True, "reason": "ok"}
        except Exception as e:
            print(f"[GPT] Emergent key failed: {e}")
            # Continue to regular OpenAI

    if not openai_client:
        return fallback_sections(), {"ok": False, "reason": "no_api_key"}

    try:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")  # Changed from gpt-5 to gpt-4o
        resp = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Você é um analista de dados brasileiro especializado em hotelaria. Responda APENAS em JSON válido com todas as 6 chaves: resumo, uh, acquisition, pmc, networks, final."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=3000  # Increased for complete JSON
        )
        content = (resp.choices[0].message.content or "").strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()
        
        try:
            sections = json.loads(content)
            # Ensure all required keys exist  
            required_keys = ["resumo", "uh", "acquisition", "pmc", "networks", "final"]
            for key in required_keys:
                if key not in sections:
                    sections[key] = "—"
        except Exception as e:
            print(f"[GPT] JSON parse failed: {e}")
            sections = {
                "resumo": content,
                "uh": "—",
                "acquisition": "—",
                "pmc": "—",
                "networks": "—",
                "final": "—"
            }
        return sections, {"ok": True, "reason": "ok"}
    except Exception as e:
        msg = str(e).lower()
        if "429" in msg or "quota" in msg:
            return fallback_sections(), {"ok": False, "reason": "quota_exceeded"}
        return fallback_sections(), {"ok": False, "reason": "error"}


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
            bucket: Dict[str, Dict[str, Any]] = {}
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
async def marketing_dials(
    start: str = Query(None),
    end: str = Query(None),
    period: str = Query("last30"),
    refresh: Optional[int] = 0
):
    # Se não vier start/end → aplica período padrão (últimos 30 dias)
    if not start or not end:
        from datetime import timezone
        today_utc = datetime.now(timezone.utc).date()
        if period == "last30":
            end_dt = today_utc - timedelta(days=1)        # ontem
            start_dt = end_dt - timedelta(days=29)
            start = start_dt.isoformat()
            end = end_dt.isoformat()

    # Converte datas
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


# -------------------------------------------------------------------
# Novo endpoint: /api/ads-campaigns
# -------------------------------------------------------------------

from typing import Optional
from datetime import datetime, timedelta
from fastapi import Query, HTTPException

def month_bounds(month_str: str):
    """Retorna tupla (start, end) no formato YYYY-MM-DD para o mês informado (YYYY-MM)."""
    try:
        year, month = [int(x) for x in month_str.split("-")]
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year, 12, 31)
        else:
            end = datetime(year, month + 1, 1) - timedelta(days=1)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    except Exception:
        return None, None


@app.get("/api/ads-campaigns")
async def ads_campaigns(
    status: str = Query("enabled"),
    period: str = Query("last30"),
    month: Optional[str] = None,
    refresh: Optional[int] = 0,
):
    """Endpoint para listar campanhas do Google Ads com filtros de período e status."""

    cache_key = f"ads-campaigns-{status}-{period}-{month or ''}"
    if not refresh:
        cached = cache.get(cache_key, ttl_seconds=10 * 60)
        if cached:
            return cached

    # Resolve intervalo
    start, end = None, None
    if month:
        start, end = month_bounds(month)
        if not start:
            raise HTTPException(
                status_code=422,
                detail="month deve estar no formato YYYY-MM"
            )
    elif period == "last30":
        from datetime import timezone
        today_utc = datetime.now(timezone.utc).date()
        end_dt = today_utc - timedelta(days=1)
        start_dt = end_dt - timedelta(days=29)
        start = start_dt.strftime("%Y-%m-%d")
        end = end_dt.strftime("%Y-%m-%d")
    else:
        from datetime import timezone
        today_utc = datetime.now(timezone.utc).date()
        end_dt = today_utc - timedelta(days=1)
        start_dt = end_dt - timedelta(days=29)
        start = start_dt.strftime("%Y-%m-%d")
        end = end_dt.strftime("%Y-%m-%d")


    payload = {
        "rows": [],
        "total": None,
        "start": start,
        "end": end,
        "status": status,
    }

    try:
        res = ads_campaigns_filtered(start, end, status)
        if res:
            payload.update(res)
    except Exception as e:
        print(f"[ADS] /api/ads-campaigns failed: {e}")

    cache.set(cache_key, payload)
    return payload


@app.get("/api/ads-networks")
async def ads_networks(
    period: str = Query("last30"),
    month: Optional[str] = None,
    refresh: Optional[int] = 0,
):
    cache_key = f"ads-networks-{period}-{month or ''}"
    if not refresh:
        cached = cache.get(cache_key, ttl_seconds=10 * 60)
        if cached:
            return cached

    # Resolve intervalo
    start, end = None, None
    if month:
        start, end = month_bounds(month)
        if not start:
            raise HTTPException(status_code=422, detail="month deve estar no formato YYYY-MM")
    elif period == "last30":
        from datetime import timezone
        today_utc = datetime.now(timezone.utc).date()
        end_dt = today_utc - timedelta(days=1)
        start_dt = end_dt - timedelta(days=29)
        start = start_dt.strftime("%Y-%m-%d")
        end = end_dt.strftime("%Y-%m-%d")
    else:
        from datetime import timezone
        today_utc = datetime.now(timezone.utc).date()
        end_dt = today_utc - timedelta(days=1)
        start_dt = end_dt - timedelta(days=29)
        start = start_dt.strftime("%Y-%m-%d")
        end = end_dt.strftime("%Y-%m-%d")


    payload = {"start": start, "end": end, "rows": []}
    try:
        res = ads_networks_breakdown(start, end)
        if res:
            payload.update(res)
    except Exception as e:
        print(f"[ADS] /api/ads-networks failed: {e}")

    cache.set(cache_key, payload)
    return payload


# -------------------- MONTHLY REPORT ENDPOINT --------------------

def current_month_str() -> str:
    """Retorna o mês atual no formato YYYY-MM."""
    today = datetime.utcnow().date()
    return f"{today.year}-{str(today.month).zfill(2)}"

@app.post("/api/monthly-report")
async def monthly_report(req: MonthlyReportRequest):
    # Validar mês
    try:
        assert len(req.month) == 7 and req.month[4] == "-"
        _y, _m = [int(x) for x in req.month.split("-")]
    except Exception:
        raise HTTPException(status_code=422, detail="Formato inválido. Use YYYY-MM.")
    # Mês vigente indisponível
    if req.month == current_month_str():
        raise HTTPException(status_code=422, detail="O mês vigente só fica disponível no 1º dia do mês seguinte.")
    # Limite (contabilizamos por mês de EXECUÇÃO)
    exec_period = current_month_str()
    # _ = quota_require(exec_period, limit=4)
    # exec_period = current_month_str()
    # Quota removida: não há mais controle de limite mensal

    # Intervalos
    start, end = month_bounds(req.month)
    if not start:
        raise HTTPException(status_code=422, detail="Formato inválido. Use YYYY-MM.")
    prev_m = prev_month_str(req.month)
    prev_start, prev_end = month_bounds(prev_m)

    # Dados (mês e anterior)
    kpi_curr = kpis_month(start, end)
    kpi_prev = kpis_month(prev_start, prev_end)

    # UH, Aquisição, PMC, Redes (para o mês)
    uh = uh_totals_month(start, end)
    acq = acq_totals_month(start, end)
    pmc = pmc_series_month(start, end)
    nets = networks_month(start, end)

    # Tabela-resumo + delta
    def delta(a, b):
        if b == 0:
            return (100.0 if a > 0 else 0.0)
        return round((a - b) / b * 100.0, 1)

    summary = {
        "current": kpi_curr,
        "previous": kpi_prev,
        "delta_pct": {
            "receita": delta(kpi_curr["receita"], kpi_prev["receita"]),
            "reservas": delta(kpi_curr["reservas"], kpi_prev["reservas"]),
            "diarias": delta(kpi_curr["diarias"], kpi_prev["diarias"]),
            "clicks": delta(kpi_curr["clicks"], kpi_prev["clicks"]),
            "impressoes": delta(kpi_curr["impressoes"], kpi_prev["impressoes"]),
            "cpc": delta(kpi_curr["cpc"], kpi_prev["cpc"]),
        }
    }

    payload_for_gpt = {
        "summary": summary,
        "uh": uh,
        "acq": acq,
        "pmc": pmc,
        "networks": nets
    }

    prompt = build_gpt_prompt_pt(req.month, prev_m, payload_for_gpt)
    sections, gpt_meta = run_gpt_sections_safe(prompt)

    # Se GPT ok: incrementa; se falhou, NÃO incrementa
    # Quota controle removido: define new_used como 0
    new_used = 0
    remaining = max(0, 4 - new_used)

    return {
        "month": req.month,
        "prev_month": prev_m,
        "summary": summary,
        "sections": sections,
        "gpt": gpt_meta
    }
    # Controle de quota removido
    return {
        "month": req.month,
        "prev_month": prev_m,
        "summary": summary,
        "sections": sections,
        "gpt": gpt_meta
    }



class FeedbackResponse(BaseModel):
    success: bool
    message: str


# -------------------- FEEDBACK ENDPOINT --------------------
from fastapi import Form, File, UploadFile, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import base64



@app.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    component: str = Form(...),
    files: List[UploadFile] = File([])  # Fixed: Corrected file parameter
):
    print(f"\n[FEEDBACK] Nova requisição: name={name}, email={email}, component={component}")

    try:
        # Use the global Supabase client
        supabase = build_supabase_client()
        if not supabase:
            print("[FEEDBACK] ❌ Falha ao conectar com Supabase")
            return FeedbackResponse(success=False, message="Erro de conexão com banco de dados")

        print("[FEEDBACK] ✅ Cliente Supabase inicializado")

        # Processa arquivos
        file_data = []
        if files and any(f.filename for f in files):  # Fixed: Better file check
            print(f"[FEEDBACK] Processando {len([f for f in files if f.filename])} arquivos")
            for i, file in enumerate(files):
                if file.filename:
                    content = await file.read()
                    file_info = {
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size": len(content),
                        "data": base64.b64encode(content).decode("utf-8")
                    }
                    file_data.append(file_info)
                    print(f"[FEEDBACK] Arquivo {i+1}: {file.filename} ({len(content)} bytes)")

        feedback_data = {
            "name": name,
            "email": email,
            "message": message,
            "component": component,
            "files": file_data if file_data else None
        }

        print(f"[FEEDBACK] Dados para inserir: {list(feedback_data.keys())}")

        # Insere no Supabase
        result = supabase.table("feedbacks").insert(feedback_data).execute()
        print(f"[FEEDBACK] Resultado Supabase: success={bool(result.data)}, count={len(result.data) if result.data else 0}")
        
        if hasattr(result, 'error') and result.error:
            print(f"[FEEDBACK] ❌ Erro Supabase: {result.error}")

        if result.data and len(result.data) > 0:
            print("[FEEDBACK] ✅ Sucesso - Feedback salvo!")
            return FeedbackResponse(success=True, message="Feedback salvo com sucesso!")
        else:
            print("[FEEDBACK] ❌ Falha - Nenhum dado retornado")
            return FeedbackResponse(success=False, message="Falha ao salvar feedback.")

    except Exception as e:
        print(f"[FEEDBACK] ❌ Exceção: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return FeedbackResponse(success=False, message="Erro interno do servidor")


# -------------------- AUTHENTICATION FUNCTIONS --------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback for SHA256 hashes
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password"""
    try:
        # Simple approach for bcrypt
        return pwd_context.hash(str(password))
    except Exception as e:
        print(f"[AUTH] Hash error: {e}")
        # Fallback to simple hash if bcrypt fails
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def validate_email_domain(email: str) -> bool:
    """Validate if email domain is allowed"""
    email = email.lower()
    if email in [e.lower() for e in ALLOWED_EMAILS]:
        return True
    return any(email.endswith(domain.lower()) for domain in ALLOWED_DOMAINS)


async def get_user_by_email(email: str) -> Optional[dict]:
    """Get user from Supabase by email"""
    supabase = build_supabase_client()
    if not supabase:
        return None
    
    try:
        result = supabase.from_("users").select("*").eq("email", email).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[AUTH] Error getting user: {e}")
        return None


async def create_user(name: str, email: str, password: str) -> dict:
    """Create new user in Supabase"""
    supabase = build_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        user_data = {
            "name": name,
            "email": email.lower(),
            "password_hash": get_password_hash(password)
        }
        
        result = supabase.from_("users").insert(user_data).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
    except Exception as e:
        print(f"[AUTH] Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


# -------------------- AUTHENTICATION MODELS --------------------

class UserRegister(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


# -------------------- AUTHENTICATION ENDPOINTS --------------------

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    """Register new user"""
    
    # Validate email domain
    if not validate_email_domain(user_data.email):
        raise HTTPException(
            status_code=400, 
            detail="Email domain not allowed. Use @ilhafaceira.com.br, @amandagattiboni.com or alangattiboni@gmail.com"
        )
    
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    user = await create_user(user_data.name, user_data.email, user_data.password)
    
    # Create access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user={"email": user["email"], "name": user["name"], "created_at": user.get("created_at")}
    )


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(user_data: UserLogin):
    """Login user"""
    
    # Get user
    user = await get_user_by_email(user_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user={"email": user["email"], "name": user["name"], "created_at": user.get("created_at")}
    )


@app.get("/api/auth/me")
async def get_current_user(current_user: dict = Depends(verify_token)):
    """Get current user info"""
    user = await get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"email": user["email"], "name": user["name"]}


# -------------------- SETUP USERS TABLE (TEMPORARY) --------------------
@app.post("/api/setup-users-table")
async def setup_users_table():
    """Temporary endpoint to create users table"""
    try:
        supabase = build_supabase_client()
        if not supabase:
            return {"success": False, "message": "Supabase connection failed"}
        
        # Check if table exists by trying to query it
        try:
            supabase.table("users").select("id").limit(1).execute()
            return {"success": True, "message": "Users table already exists"}
        except Exception:
            return {
                "success": False, 
                "message": "Users table doesn't exist. Please create it manually with this SQL:",
                "sql": """
CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name text NOT NULL,
    email text UNIQUE NOT NULL,
    password_hash text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);
                """
            }
            
    except Exception as e:
        print(f"[SETUP] Error: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}


# -------------------- HEALTH --------------------

@app.get("/api/health")
async def health():
    integrations = {
        "ga4": bool(os.getenv("GA4_PROPERTY_ID") and os.getenv("GA4_PRIVATE_KEY")),
        "google_ads": bool(os.getenv("ADS_DEVELOPER_TOKEN") and os.getenv("ADS_OAUTH_CLIENT_ID"))
    }
    return {"status": "ok", "integrations": integrations}



