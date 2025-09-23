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
        pk = GA4_PRIVATE_KEY.replace("\\n", "\n")
        info = {
            "type": "service_account",
            "client_email": GA4_CLIENT_EMAIL,
            "private_key": pk,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        ga4_client = BetaAnalyticsDataClient(credentials=credentials)
except Exception:
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
except Exception:
    ads_client = None

# FastAPI app
app = FastAPI(title="Calma Data API", version="1.1.0")

# Basic CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache util
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

CHANNELS = ["Organic Search", "Paid Search", "Direct", "Paid Social", "Organic Social", "Referral", "Display"]
UH_TYPES = ["Standard", "Deluxe", "Suite", "Bungalow"]

# ------------------------- Schemas -------------------------
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

# ------------------------- Mocks -------------------------
# (copie aqui seus mocks originais sem alterações: mock_kpis, mock_acquisition_timeseries,
# mock_revenue_by_uh, mock_sales_uh_stacked, mock_campaign_heatmap, mock_performance_table)

# ------------------------- Integrations -------------------------
# (copie aqui suas funções originais de integração: ga4_sum_item_revenue, ga4_count_reservations,
# ga4_sum_nights, ads_totals, ads_campaign_rows)

# ------------------------- Endpoints -------------------------

@app.get("/api/kpis", response_model=KPIResponse)
async def get_kpis(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    return KPIResponse(
        receita=0.0, reservas=0, diarias=0,
        clicks=0, impressoes=0, cpc=0.0, custo=0.0
    )

@app.get("/api/acquisition-by-channel", response_model=TimeSeriesResponse)
async def acquisition_by_channel(metric: str = Query("users"), start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    return TimeSeriesResponse(metric=metric, points=[])

@app.get("/api/revenue-by-uh", response_model=RevenueByUHResponse)
async def revenue_by_uh(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    return RevenueByUHResponse(points=[])

@app.get("/api/sales-uh-stacked", response_model=StackedBarsResponse)
async def sales_uh_stacked(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    return StackedBarsResponse(series_labels=[], points=[])

@app.get("/api/campaign-conversion-heatmap", response_model=HeatmapResponse)
async def campaign_conversion_heatmap(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    return HeatmapResponse(cells=[])

@app.get("/api/performance-table", response_model=PerformanceTableResponse)
async def performance_table(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    return PerformanceTableResponse(rows=[])

@app.get("/api/example")
async def example():
    return {"message": "Hello, world!"}

# ------------------------- Healthcheck -------------------------
@app.get("/api/health")
async def health():
    ga4_ok = False
    ads_ok = False
    try:
        if ga4_client and GA4_PROPERTY_ID:
            from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            req = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                dimensions=[Dimension(name="date")],
                metrics=[Metric(name="users")],
                date_ranges=[DateRange(start_date=yesterday, end_date=yesterday)],
                limit=1,
            )
            _ = ga4_client.run_report(req)
            ga4_ok = True
    except Exception:
        ga4_ok = False

    try:
        if ads_client and ADS_CUSTOMER_ID:
            service = ads_client.get_service("GoogleAdsService")
            customer_id = ADS_CUSTOMER_ID.replace("-", "")
            query = "SELECT campaign.id, campaign.name FROM campaign LIMIT 1"
            _ = service.search(customer_id=customer_id, query=query)
            ads_ok = True
    except Exception:
        ads_ok = False

    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "integrations": {"ga4": ga4_ok, "google_ads": ads_ok},
    }
