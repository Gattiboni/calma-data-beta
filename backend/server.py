# backend/server.py
# Calma Data API — FastAPI (GA4 + Google Ads)
# Contratos estáveis:
# - /api/health -> {"status":"ok","time":...,"integrations":{"ga4":bool,"google_ads":bool}}
# - /api/kpis -> {receita, reservas, diarias, clicks, impressoes, cpc, custo}
# - /api/performance-table -> {rows:[{name, clicks, impressoes, ctr, cpc, custo, conversoes, receita, roas}]}
# - /api/acquisition-by-channel -> {metric, points:[{date:"DD/MM/YY", values:{canal:valor}}]}
# - /api/revenue-by-uh -> {points:[{date:"DD/MM/YY", values:{<UH dinamica>:valor}}]}

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import os, json, base64, random, unicodedata, re

# =========================
# .env (DEV LOCAL) — prioridade raiz
# =========================
try:
    from dotenv import load_dotenv  # type: ignore
    root_env = Path(__file__).resolve().parents[1] / ".env"
    backend_env = Path(__file__).with_name(".env")
    if root_env.exists():
        load_dotenv(root_env)
    elif backend_env.exists():
        load_dotenv(backend_env)
except Exception:
    pass

# =========================
# ENV — GA4 / Ads (múltiplas formas)
# =========================
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID") or os.environ.get("GA4_PROPERTY")
GA4_QUOTA_PROJECT_ID = os.environ.get("GA4_QUOTA_PROJECT_ID")

# Preferidos (evitam problemas de \n/aspas)
GA4_SA_JSON_B64 = os.environ.get("GA4_SA_JSON_B64")           # JSON da SA em Base64
GA4_SERVICE_ACCOUNT_JSON = os.environ.get("GA4_SERVICE_ACCOUNT_JSON")  # JSON literal
GA4_SERVICE_ACCOUNT_FILE = os.environ.get("GA4_SERVICE_ACCOUNT_FILE")  # caminho
GA4_CLIENT_EMAIL = os.environ.get("GA4_CLIENT_EMAIL")
GA4_PRIVATE_KEY = os.environ.get("GA4_PRIVATE_KEY")
GA4_PROJECT_ID = os.environ.get("GA4_PROJECT_ID")

ADS_CONFIG_JSON_B64 = os.environ.get("ADS_CONFIG_JSON_B64")
ADS_CONFIG_JSON = os.environ.get("ADS_CONFIG_JSON")
ADS_DEVELOPER_TOKEN = os.environ.get("ADS_DEVELOPER_TOKEN")
ADS_LOGIN_CUSTOMER_ID = os.environ.get("ADS_LOGIN_CUSTOMER_ID")
ADS_CUSTOMER_ID = os.environ.get("ADS_CUSTOMER_ID")
ADS_OAUTH_CLIENT_ID = os.environ.get("ADS_OAUTH_CLIENT_ID")
ADS_OAUTH_CLIENT_SECRET = os.environ.get("ADS_OAUTH_CLIENT_SECRET")
ADS_OAUTH_REFRESH_TOKEN = os.environ.get("ADS_OAUTH_REFRESH_TOKEN")

GA4_CACHE_TTL_SECONDS = int(os.environ.get("GA4_CACHE_TTL_SECONDS", "900"))

# =========================
# App & CORS
# =========================
app = FastAPI(title="Calma Data API", version="1.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# =========================
# Cache simples em memória
# =========================
class SimpleCache:
    def __init__(self): self.store: Dict[str, Dict[str, Any]] = {}
    def _now(self) -> float: return datetime.utcnow().timestamp()
    def get(self, key: str, ttl_seconds: int) -> Optional[Any]:
        rec = self.store.get(key)
        if not rec: return None
        if self._now() - rec["ts"] > ttl_seconds:
            del self.store[key]; return None
        return rec["val"]
    def set(self, key: str, val: Any): self.store[key] = {"val": val, "ts": self._now()}
cache = SimpleCache()

# =========================
# Utils
# =========================
def daterange(start_date: datetime, end_date: datetime):
    cur = start_date
    while cur <= end_date:
        yield cur
        cur += timedelta(days=1)

def parse_dates(start: str, end: str):
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    return start_dt, end_dt

def fmt_ddmmyy(dt: datetime) -> str:
    return dt.strftime("%d/%m/%y")

def _normalize_name_key(s: str) -> str:
    if not s: return ""
    s_nfkd = unicodedata.normalize("NFKD", s)
    s_noacc = "".join(c for c in s_nfkd if not unicodedata.combining(c))
    s_clean = re.sub(r"[^a-z0-9]+", " ", s_noacc.lower())
    return re.sub(r"\s+", " ", s_clean).strip()

_PT_CHARS = set("çãõáéíóúâêôàÇÃÕÁÉÍÓÚÂÊÔÀ")
_PT_HINTS = {"quarto","andar","térreo","superior","opção","romântico","cozinha","suíte","luxo","vista","varanda","jardim","bangalô","térreo","andar"}

def _is_pt_br_label(label: str) -> bool:
    if not label: return False
    if any(ch in _PT_CHARS for ch in label): return True
    low = label.lower()
    return any(tok in low for tok in _PT_HINTS)

# =========================
# Schemas
# =========================
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

# =========================
# Clients (GA4 / Ads)
# =========================
ga4_client = None
ads_client = None
_ga4_mode = "none"
_ads_mode = "none"

def build_ga4_client():
    global _ga4_mode
    try:
        from google.oauth2 import service_account
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
    except Exception as exc:
        print(f"[GA4] libs not available: {exc}")
        return None
    cred = None

    # 1) JSON Base64
    if not cred and GA4_SA_JSON_B64:
        try:
            data = base64.b64decode(GA4_SA_JSON_B64).decode("utf-8")
            info = json.loads(data)
            cred = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            _ga4_mode = "json_b64"
        except Exception as exc:
            print(f"[GA4] json_b64 failed: {exc}")

    # 2) JSON literal
    if not cred and GA4_SERVICE_ACCOUNT_JSON:
        try:
            info = json.loads(GA4_SERVICE_ACCOUNT_JSON)
            cred = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            _ga4_mode = "json"
        except Exception as exc:
            print(f"[GA4] json literal failed: {exc}")

    # 3) Arquivo
    if not cred and GA4_SERVICE_ACCOUNT_FILE and Path(GA4_SERVICE_ACCOUNT_FILE).exists():
        try:
            cred = service_account.Credentials.from_service_account_file(
                GA4_SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            _ga4_mode = "file"
        except Exception as exc:
            print(f"[GA4] file failed: {exc}")

    # 4) Email + Private Key
    if not cred and GA4_CLIENT_EMAIL and GA4_PRIVATE_KEY:
        try:
            pk = GA4_PRIVATE_KEY.replace("\\n", "\n")
            info = {
                "type": "service_account",
                "client_email": GA4_CLIENT_EMAIL,
                "private_key": pk,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            if GA4_PROJECT_ID: info["project_id"] = GA4_PROJECT_ID
            cred = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            _ga4_mode = "emailkey"
        except Exception as exc:
            print(f"[GA4] email+key failed: {exc}")

    if not cred:
        print("[GA4] No credentials found in env")
        _ga4_mode = "none"
        return None

    if GA4_QUOTA_PROJECT_ID:
        try:
            cred = cred.with_quota_project(GA4_QUOTA_PROJECT_ID)
        except Exception as exc:
            print(f"[GA4] with_quota_project failed: {exc}")

    try:
        client = BetaAnalyticsDataClient(credentials=cred)
        return client
    except Exception as exc:
        print(f"[GA4] client init failed: {exc}")
        return None

def build_ads_client():
    global _ads_mode
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except Exception as exc:
        print(f"[ADS] libs not available: {exc}")
        return None

    cfg = None
    # 1) JSON Base64
    if ADS_CONFIG_JSON_B64:
        try:
            data = base64.b64decode(ADS_CONFIG_JSON_B64).decode("utf-8")
            cfg = json.loads(data); _ads_mode = "json_b64"
        except Exception as exc:
            print(f"[ADS] json_b64 failed: {exc}")

    # 2) JSON literal
    if cfg is None and ADS_CONFIG_JSON:
        try:
            cfg = json.loads(ADS_CONFIG_JSON); _ads_mode = "json"
        except Exception as exc:
            print(f"[ADS] json literal failed: {exc}")

    # 3) Variáveis avulsas
    if cfg is None:
        if not ADS_DEVELOPER_TOKEN or not ADS_OAUTH_CLIENT_ID or not ADS_OAUTH_CLIENT_SECRET or not ADS_OAUTH_REFRESH_TOKEN:
            print("[ADS] Missing required envs for Ads")
            _ads_mode = "none"
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
        _ads_mode = "vars"

    try:
        return GoogleAdsClient.load_from_dict(cfg)
    except Exception as exc:
        print(f"[ADS] client init failed: {exc}")
        return None

ga4_client = build_ga4_client()
ads_client = build_ads_client()
print(f"[INIT] GA4_INIT_OK={bool(ga4_client)} (mode={_ga4_mode})")
print(f"[INIT] ADS_INIT_OK={bool(ads_client)} (mode={_ads_mode})")

# =========================
# GA4 helpers
# =========================
# --- SUBSTITUA INTEGRALMENTE a função ga4_sum_item_revenue por esta ---
def ga4_sum_item_revenue(start: str, end: str) -> float:
    """
    Soma TOTAL de itemRevenue no período (agregado no GA4).
    - Sem dimensions (o GA4 já retorna 1 linha agregada)
    - Sem limit=1 desnecessário
    - Retorna 0.0 em caso de falha
    """
    try:
        if not ga4_client or not GA4_PROPERTY_ID:
            return 0.0

        from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest

        req = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            metrics=[Metric(name="itemRevenue")],
            date_ranges=[DateRange(start_date=start, end_date=end)],
        )
        resp = ga4_client.run_report(req)

        total = 0.0
        for row in getattr(resp, "rows", []) or []:
            try:
                total += float(row.metric_values[0].value or 0)
            except Exception:
                pass

        return round(total, 2)
    except Exception:
        return 0.0
# --- FIM DA SUBSTITUIÇÃO ---


def ga4_count_reservations(start: str, end: str) -> Optional[int]:
    if not GA4_PROPERTY_ID:
        return None
    client = ga4_client or build_ga4_client()
    if not client:
        return None
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest, FilterExpression, Filter
    # Evento de reserva padrão (purchase). Se quiser mudar, Neo troca aqui.
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="eventName")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimension_filter=FilterExpression(filter=Filter(field_name="eventName", string_filter=Filter.StringFilter(value="purchase")))
    )
    resp = client.run_report(req)
    if not resp.rows:
        # fallback leve: conversions (quando não há purchase)
        req2 = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="conversions")],
            date_ranges=[DateRange(start_date=start, end_date=end)],
            limit=1,
        )
        resp2 = client.run_report(req2)
        total = 0
        for r in resp2.rows:
            total += int(r.metric_values[0].value or 0)
        return total
    total = 0
    for r in resp.rows:
        total += int(r.metric_values[0].value or 0)
    return total

def ga4_revenue_by_item_per_day(start: str, end: str) -> Optional[List[Dict[str, Any]]]:
    """Σ itemRevenue por dia; tenta itemId+itemName+date, cai para itemName+date com normalização."""
    if not GA4_PROPERTY_ID:
        return None
    client = ga4_client or build_ga4_client()
    if not client:
        return None
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

    start_dt, end_dt = parse_dates(start, end)
    date_labels = [fmt_ddmmyy(d) for d in daterange(start_dt, end_dt)]

    def build_points(group_map: Dict[str, Dict[str, float]], label_map: Dict[str, str]) -> List[Dict[str, Any]]:
        # inclui apenas itens com soma > 0
        keys = [k for k, per in group_map.items() if sum(per.values()) > 0]
        # resolver colisões de rótulo
        used, final_label = {}, {}
        for k in keys:
            base = label_map.get(k, k)
            if base not in used:
                used[base] = 1; final_label[k] = base
            else:
                used[base] += 1; final_label[k] = f"{base} · {str(k)[-4:]}"
        pts = []
        for d in date_labels:
            values = {final_label[k]: round(group_map.get(k, {}).get(d, 0.0), 2) for k in keys}
            pts.append({"date": d, "values": values})
        return pts

    # 1) itemId + itemName + date
    try:
        req_id = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="itemId"), Dimension(name="itemName"), Dimension(name="date")],
            metrics=[Metric(name="itemRevenue")],
            date_ranges=[DateRange(start_date=start, end_date=end)],
            limit=250000,
        )
        resp_id = client.run_report(req_id)
        has_id = False
        group: Dict[str, Dict[str, float]] = {}
        labels: Dict[str, Dict[str, float]] = {}
        for row in resp_id.rows:
            item_id = (row.dimension_values[0].value or "").strip()
            name = (row.dimension_values[1].value or "").strip()
            d_raw = row.dimension_values[2].value  # YYYYMMDD
            if item_id: has_id = True
            try:
                d_fmt = fmt_ddmmyy(datetime.strptime(d_raw, "%Y%m%d"))
            except Exception:
                continue
            val = float(row.metric_values[0].value or 0)
            key = item_id if item_id else f"_noid::{_normalize_name_key(name)}"
            group.setdefault(key, {}); group[key][d_fmt] = group[key].get(d_fmt, 0.0) + val
            labels.setdefault(key, {}); labels[key][name] = labels[key].get(name, 0.0) + val
        if has_id and group:
            canonical: Dict[str, str] = {}
            for k, cand in labels.items():
                pt = [(nm, rv) for nm, rv in cand.items() if _is_pt_br_label(nm)]
                canonical[k] = max(pt, key=lambda x: x[1])[0] if pt else max(cand.items(), key=lambda x: x[1])[0]
            return build_points(group, canonical)
    except Exception as exc:
        print(f"[GA4] itemId path failed: {exc}")

    # 2) itemName + date (normalização)
    req = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[Dimension(name="itemName"), Dimension(name="date")],
        metrics=[Metric(name="itemRevenue")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        limit=250000,
    )
    resp = client.run_report(req)
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
        group2.setdefault(key, {}); group2[key][d_fmt] = group2[key].get(d_fmt, 0.0) + val
        labels2.setdefault(key, {}); labels2[key][name] = labels2[key].get(name, 0.0) + val
    canonical2: Dict[str, str] = {}
    for k, cand in labels2.items():
        pt = [(nm, rv) for nm, rv in cand.items() if _is_pt_br_label(nm)]
        canonical2[k] = max(pt, key=lambda x: x[1])[0] if pt else max(cand.items(), key=lambda x: x[1])[0]
    return build_points(group2, canonical2)

# =========================
# Ads helpers
# =========================
def ads_totals(start: str, end: str) -> Optional[Dict[str, Any]]:
    if not ADS_CUSTOMER_ID:
        return None
    client = ads_client or build_ads_client()
    if not client:
        return None
    service = client.get_service("GoogleAdsService")
    customer_id = ADS_CUSTOMER_ID.replace("-", "")
    query = f"""
        SELECT segments.date, metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.average_cpc
        FROM customer
        WHERE segments.date BETWEEN '{start}' AND '{end}'
    """
    resp = service.search(customer_id=customer_id, query=query)
    clicks = imp = 0
    cost = cpc_sum = 0.0
    days = 0
    for row in resp:
        days += 1
        clicks += int(row.metrics.clicks or 0)
        imp += int(row.metrics.impressions or 0)
        cost += (row.metrics.cost_micros or 0) / 1_000_000
        cpc_sum += ((row.metrics.average_cpc or 0) / 1_000_000)
    avg_cpc = round((cpc_sum / days) if days else (cost / clicks if clicks else 0), 2)
    return {"clicks": clicks, "impressoes": imp, "custo": round(cost, 2), "cpc": avg_cpc}

def ads_campaign_rows(start: str, end: str) -> Optional[List[Dict[str, Any]]]:
    if not ADS_CUSTOMER_ID:
        return None
    client = ads_client or build_ads_client()
    if not client:
        return None
    service = client.get_service("GoogleAdsService")
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

# =========================
# Endpoints
# =========================
@app.get("/api/kpis", response_model=KPIResponse)
async def get_kpis(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    start_dt, end_dt = parse_dates(start, end)
    key = f"kpis-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=GA4_CACHE_TTL_SECONDS)
        if cached: return cached

    # Base mock
    def mock_kpis():
        r = random.Random(); r.seed(f"kpis-{start}-{end}")
        days = (end_dt - start_dt).days + 1
        clicks = int((500 + r.random()*2500) * days / 14)
        imp = int(clicks * (8 + r.random()*12))
        cpc = round(1.2 + r.random()*3.2, 2)
        custo = round(clicks * cpc, 2)
        reservas = int((20 + r.random()*100) * days / 14)
        diarias = int(reservas * (1.3 + r.random()*0.8))
        receita = round(diarias * (180 + r.random()*220), 2)
        return {"receita": receita, "reservas": reservas, "diarias": diarias, "clicks": clicks, "impressoes": imp, "cpc": cpc, "custo": custo}

    data = mock_kpis()

    # GA4: receita (Σ itemRevenue) + reservas (purchase)
    try:
        r = ga4_sum_item_revenue(start, end)
        if r is not None: data["receita"] = r
    except Exception as exc:
        print(f"[GA4] kpis revenue failed: {exc}")

    try:
        rv = ga4_count_reservations(start, end)
        if rv is not None: data["reservas"] = rv
    except Exception as exc:
        print(f"[GA4] kpis reservas failed: {exc}")

    # Ads
    try:
        ads = ads_totals(start, end)
        if ads: data.update(ads)
    except Exception as exc:
        print(f"[ADS] kpis ads failed: {exc}")

    cache.set(key, data)
    return data

@app.get("/api/acquisition-by-channel", response_model=TimeSeriesResponse)
async def acquisition_by_channel(
    metric: str = Query("users"),  # aceita "users" do front
    start: str = Query(...),
    end: str = Query(...),
    refresh: Optional[int] = 0
):
    # Mapeia "users" -> métrica GA4 válida (evita 400). Escolha: activeUsers (estável para aquisição).
    ga4_metric = "activeUsers" if metric == "users" else metric

    start_dt, end_dt = parse_dates(start, end)
    key = f"acq-{ga4_metric}-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15*60)
        if cached: return cached

    points = None
    if GA4_PROPERTY_ID:
        client = ga4_client or build_ga4_client()
        if client:
            from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
            try:
                req = RunReportRequest(
                    property=f"properties/{GA4_PROPERTY_ID}",
                    dimensions=[Dimension(name="firstUserPrimaryChannelGroup"), Dimension(name="date")],
                    metrics=[Metric(name=ga4_metric)],
                    date_ranges=[DateRange(start_date=start, end_date=end)],
                )
                resp = client.run_report(req)
                bucket: Dict[str, Dict[str, float]] = {}
                for row in resp.rows:
                    ch = row.dimension_values[0].value or "(other)"
                    d_raw = row.dimension_values[1].value  # YYYYMMDD
                    v = float(row.metric_values[0].value or 0)
                    bucket.setdefault(d_raw, {})[ch] = v
                ordered = []
                for dt in daterange(start_dt, end_dt):
                    key_dt = dt.strftime("%Y%m%d")
                    ordered.append({"date": fmt_ddmmyy(dt), "values": bucket.get(key_dt, {})})
                points = ordered
            except Exception as exc:
                print(f"[GA4] acquisition failed: {exc}")

    if points is None:
        # mock simples (formata DD/MM/YY)
        rnd = random.Random(); rnd.seed(f"acq-{ga4_metric}-{start}-{end}")
        chs = ["Organic Search","Paid Search","Direct","Paid Social","Organic Social","Referral","Display"]
        temp = []
        for dt in daterange(start_dt, end_dt):
            base = 100 + (dt.weekday() * 10)
            values = {c: round(base*(1+idx*0.15)* (0.7 + rnd.random()*0.6), 2) for idx, c in enumerate(chs)}
            temp.append({"date": fmt_ddmmyy(dt), "values": values})
        points = temp

    payload = {"metric": metric, "points": points}
    cache.set(key, payload)
    return payload

@app.get("/api/revenue-by-uh", response_model=RevenueByUHResponse)
async def revenue_by_uh(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    # Sem mock silencioso: se GA4 indisponível -> points=[]
    key = f"revuh-item-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15*60)
        if cached: return cached

    points: List[Dict[str, Any]] = []
    try:
        res = ga4_revenue_by_item_per_day(start, end)
        if res is not None:
            points = res
    except Exception as exc:
        print(f"[GA4] revenue-by-uh failed: {exc}")

    payload = {"points": points}
    cache.set(key, payload)
    return payload

@app.get("/api/performance-table", response_model=PerformanceTableResponse)
async def performance_table(start: str = Query(...), end: str = Query(...), refresh: Optional[int] = 0):
    key = f"table-{start}-{end}"
    if not refresh:
        cached = cache.get(key, ttl_seconds=15*60)
        if cached: return cached
    rows = None
    try:
        rows = ads_campaign_rows(start, end)
    except Exception as exc:
        print(f"[ADS] table failed: {exc}")
        rows = None
    if rows is None: rows = []
    payload = {"rows": rows}
    cache.set(key, payload)
    return payload

# =========================
# Health (ativo) — contrato preservado; debug opcional
# =========================
@app.get("/api/health")
async def health(debug: Optional[int] = 0):
    ga4_ok = False
    ads_ok = False
    ga4_err = None
    ads_err = None

    # GA4 quick test: itemRevenue últimos 7 dias
    try:
        if GA4_PROPERTY_ID:
            client = ga4_client or build_ga4_client()
            if client:
                from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
                end_s = datetime.utcnow().strftime("%Y-%m-%d")
                start_s = (datetime.utcnow() - timedelta(days=6)).strftime("%Y-%m-%d")
                req = RunReportRequest(
                    property=f"properties/{GA4_PROPERTY_ID}",
                    dimensions=[Dimension(name="date")],
                    metrics=[Metric(name="itemRevenue")],
                    date_ranges=[DateRange(start_date=start_s, end_date=end_s)],
                    limit=1,
                )
                _ = client.run_report(req)
                ga4_ok = True
    except Exception as exc:
        ga4_err = str(exc); ga4_ok = False

    # Ads quick GAQL
    try:
        client = ads_client or build_ads_client()
        if client and ADS_CUSTOMER_ID:
            service = client.get_service("GoogleAdsService")
            customer_id = ADS_CUSTOMER_ID.replace("-", "")
            _ = service.search(customer_id=customer_id, query="SELECT campaign.id FROM campaign LIMIT 1")
            ads_ok = True
    except Exception as exc:
        ads_err = str(exc); ads_ok = False

    payload = {
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "integrations": {"ga4": ga4_ok, "google_ads": ads_ok},
    }
    if debug:
        payload["ga4_mode"] = _ga4_mode
        payload["ads_mode"] = _ads_mode
        if not ga4_ok: payload["ga4_error"] = ga4_err
        if not ads_ok: payload["ads_error"] = ads_err
    return payload
