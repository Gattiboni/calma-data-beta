# Testing Protocol Acknowledgement

This file tracks backend test scope and results for this pass. No environment variables were changed and no URLs/ports were modified.

Scope for this pass (agreed):
- Backend: /api/revenue-by-uh using GA4 itemRevenue (itemId+itemName+date; fallback itemName+date). Filter total>0, zero-fill per day, dates DD/MM/YY, errors/quota ⇒ {"points": []}. No mock fallback. No changes to env loading or variable names.
- Frontend: empty states for all 4 charts; subtle monochromatic icons (Sidebar + 7 KPIs); KPI spacing/height refinements; chart palette tuning; UH by Tipo demo to 12 months.

How tests will run here:
- Contract tests (no GA4 creds required): validate 200 responses, JSON schemas, and empty-state behavior when GA4 is not configured. This ensures stability and correct fallback to {"points": []}.
- Real data validation: to be run locally by the user with their GA4/Ads env. If at any point you want me to run real-data here, I need those GA4_* env vars available to the backend process at runtime via backend/.env (gitignored).

Manual real-data checks suggested:
- GET /api/revenue-by-uh?start=2025-09-16&end=2025-09-22
  • Expect itemRevenue aggregated with itemName series, per-day points with zeros on no-sale days.
- Compare totals with GA4 UI (Ecommerce purchases — Item name) for the same period.

Notes:
- Any GA4 auth/quota error should yield {"points": []} and 200 OK.
- Health: /api/health reports ga4/google_ads availability booleans.