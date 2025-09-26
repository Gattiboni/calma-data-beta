// CALMA_MARKER_LOADING_V2
import React, { useEffect, useMemo, useState } from 'react'
import './App.css'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid,
  BarChart, Bar, AreaChart, Area
} from 'recharts'

const API_BASE = (
  import.meta.env?.VITE_BACKEND_URL ||
  import.meta.env?.REACT_APP_BACKEND_URL ||
  process.env.REACT_APP_BACKEND_URL
)

function ensureApiBase(path) {
  const baseRaw = API_BASE || ''
  if (!baseRaw) throw new Error('Backend URL ausente. Defina REACT_APP_BACKEND_URL no .env do frontend.')
  const base = baseRaw.endsWith('/') ? baseRaw.slice(0, -1) : baseRaw
  const p = path.startsWith('/') ? path : `/${path}`
  const baseEndsWithApi = base.endsWith('/api') || base === '/api'
  const pathHasApi = p.startsWith('/api')
  let full = ''
  if (baseEndsWithApi) {
    full = base + p
  } else {
    full = pathHasApi ? (base + p) : (base + '/api' + p)
  }
  return full
}

function formatBRLShort(n) {
  if (n === null || n === undefined || isNaN(n)) return '—'
  const sign = n < 0 ? '-' : ''
  const abs = Math.abs(n)
  if (abs >= 1000) {
    const k = abs / 1000
    const oneDecimal = Math.round(k * 10) / 10
    const str = oneDecimal.toString().replace('.', ',')
    return `${sign}R$${str}K`
  }
  return `${sign}R$${Math.round(abs)}`
}

function addDays(date, days) {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}
function formatISO(d) {
  return d.toISOString().slice(0, 10)
}

function useDateRange(initial = '7d') {
  const [mode, setMode] = useState(initial)
  const [custom, setCustom] = useState({ start: '', end: '' })
  const range = useMemo(() => {
    const now = new Date()
    if (mode === '7d' || mode === '30d' || mode === '90d') {
      const days = mode === '7d' ? 7 : mode === '30d' ? 30 : 90
      const end = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const start = addDays(end, -(days - 1))
      return { start: formatISO(start), end: formatISO(end) }
    }
    if (mode === 'custom') {
      const { start, end } = custom
      if (start && end) return { start, end }
      const endDef = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const startDef = addDays(endDef, -6)
      return { start: formatISO(startDef), end: formatISO(endDef) }
    }
    const end = formatISO(now)
    const start = formatISO(addDays(now, -6))
    return { start, end }
  }, [mode, custom])
  return { mode, setMode, custom, setCustom, range }
}

function getPrevRange(range) {
  const s = new Date(range.start)
  const e = new Date(range.end)
  const span = Math.round((e - s) / (1000 * 60 * 60 * 24)) + 1
  const prevEnd = addDays(s, -1)
  const prevStart = addDays(prevEnd, -(span - 1))
  return { start: formatISO(prevStart), end: formatISO(prevEnd), span }
}

async function api(path, params) {
  const fullPath = ensureApiBase(path)
  const url = new URL(fullPath, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))
  }
  const res = await fetch(url.toString())
  if (!res.ok) throw new Error('API error')
  return res.json()
}

function Icon({ name, className = 'w-4 h-4 text-elegant' }) {
  const S = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' }
  if (name === 'home') return (<svg className={className} viewBox="0 0 32 32"><circle cx="16" cy="16" r="13" {...S} /><path {...S} d="M8 16l8-7 8 7M11 18v7h10v-7" /></svg>)
  if (name === 'info') return (<svg className={className} viewBox="0 0 32 32"><circle cx="16" cy="16" r="13" {...S} /><path {...S} d="M16 12h.01M15 16h2v6h-2" /></svg>)
  if (name === 'settings') return (<svg className={className} viewBox="0 0 32 32"><circle cx="16" cy="16" r="13" {...S} /><path {...S} d="M8 11h14M8 16h10M8 21h12" /></svg>)
  if (name === 'money') return (<svg className={className} viewBox="0 0 24 24"><path {...S} d="M3 7h18v10H3zM6 12h12M8 9v6m8-6v6" /></svg>)
  if (name === 'bag') return (<svg className={className} viewBox="0 0 24 24"><path {...S} d="M6 7h12l-1 12H7L6 7zM9 7a3 3 0 1 1 6 0" /></svg>)
  if (name === 'moon') return (<svg className={className} viewBox="0 0 24 24"><path {...S} d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>)
  if (name === 'click') return (<svg className={className} viewBox="0 0 24 24"><path {...S} d="M9 12 3 10l8-2 2-8 2 8 8 2-8 2-2 8-2-8z" /></svg>)
  if (name === 'eye') return (<svg className={className} viewBox="0 0 24 24"><path {...S} d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" /><circle cx="12" cy="12" r="3" fill="currentColor" /></svg>)
  if (name === 'coin') return (<svg className={className} viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" {...S} /><path {...S} d="M8 12h8M12 8v8" /></svg>)
  if (name === 'cost') return (<svg className={className} viewBox="0 0 24 24"><path {...S} d="M3 12h18M4 8h10M6 16h8" /></svg>)
  return null
}

function Topbar({ mode, setMode, range, setCustom, custom }) {
  const [q, setQ] = useState('')
  return (
    <div className="w-full flex items-center justify-between px-6 py-3 bg-surface">
      <div className="flex items-center gap-3">
        <img src="/logo-calma-data.png" alt="Calma Data" className="h-8" />
        <div className="topbar-title">C'alma Data, o dashboard da Ilha Faceira</div>
      </div>

      <div className="flex-1 max-w-xl mx-6">
        <input
          aria-label="buscar"
          placeholder="Informações, dicas e tudo sobre seu dashboard"
          value={q}
          onChange={e => setQ(e.target.value)}
          className="w-full px-3 py-2 rounded-md border border-gray-200 shadow-softer bg-white"
        />
      </div>

      <div className="flex items-center gap-2">
        {['7d', '30d', '90d', 'custom'].map(key => (
          <button
            key={key}
            className={`chip ${mode === key ? 'active' : ''}`}
            onClick={() => setMode(key)}
            aria-label={`intervalo ${key}`}
          >
            {key.toUpperCase()}
          </button>
        ))}
        {mode === 'custom' && (
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={custom?.start || range.start}
              onChange={e => setCustom(s => ({ ...s, start: e.target.value }))}
              className="px-3 py-2 rounded-md border border-gray-200"
            />
            <input
              type="date"
              value={custom?.end || range.end}
              onChange={e => setCustom(s => ({ ...s, end: e.target.value }))}
              className="px-3 py-2 rounded-md border border-gray-200"
            />
          </div>
        )}
      </div>
    </div>
  )
}

function Sidebar() {
  const items = [
    { id: 'inicio', label: 'Início', icon: 'home' },
    { id: 'sobre', label: 'Sobre', icon: 'info' },
    { id: 'config', label: 'Configurações', icon: 'settings' }
  ]
  return (
    <aside className="w-24 shrink-0 h-full flex items-start justify-center py-4" aria-label="menu lateral">
      <div className="sidebar-capsule" role="navigation">
        {items.map(it => (
          <button key={it.id} title={it.label} className="hover:opacity-80" aria-label={it.label}>
            <Icon name={it.icon} className="sidebar-icon" />
          </button>
        ))}
      </div>
    </aside>
  )
}

const KPIGREEN = '#A8C6A6'

function KPI({ title, value, bg = KPIGREEN, icon, loading }) {
  return (
    <div className="kpi kpi-colored relative" style={{ backgroundColor: bg }}>
      {loading && (
        <div className="loading-overlay">
          <div className="flex flex-col items-center">
            <div className="spinner"></div>
            <div className="loading-text">Carregando…</div>
          </div>
        </div>
      )}
      <div className="kpi-title flex items-center gap-2">
        <Icon name={icon} className="w-3.5 h-3.5 text-white/90" /> {title}
      </div>
      <div className="kpi-value mt-1">{value}</div>
    </div>
  )
}

// Demo
function buildDemo(range) {
  const days = 7
  const dates = Array.from({ length: days }, (_, i) =>
    formatISO(addDays(new Date(range.end), -(days - 1 - i)))
  )
  const acqPoints = dates.map((d, idx) => ({
    date: d,
    values: {
      'Organic Search': 120 + idx * 60,
      'Paid Search': 80 + idx * 30,
      'Direct': 200 - idx * 15,
      'Paid Social': 40 + idx * 25,
      'Organic Social': 90 + idx * 40,
      'Referral': 60 + idx * 15,
      'Display': 30 + idx * 35
    }
  }))
  const revPoints = dates.map((d, idx) => ({
    date: d,
    values: {
      'Standard': 1800 - idx * 120,
      'Deluxe': 2200 + idx * 160,
      'Suite': 2600 + idx * 280,
      'Premium': 900 + idx * 60
    }
  }))
  return {
    kpis: { receita: 71400, reservas: 32, diarias: 51, clicks: 5290, impressoes: 148000, cpc: 0.12, custo: 615 },
    acq: { metric: 'users', points: acqPoints },
    revUH: { points: revPoints }
  }
}

function useDashboardData(range) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState({})
  const demo = typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('demo') === '1'

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setLoading(true)
        if (demo) {
          const d = buildDemo(range)
          if (!cancelled) setData(d)
          return
        }
        const params = { start: range.start, end: range.end }
        const prev = getPrevRange(range)
        const [kpis, acq, revUH, adr, dials] = await Promise.all([
          api('/kpis', params),
          api('/acquisition-by-channel', { ...params, metric: 'users' }),
          api('/revenue-by-uh', params),
          api('/adr', params),
          api('/marketing-dials', params)
        ])
        const [prevAcq, prevRevUH, prevAdr, prevDials] = await Promise.all([
          api('/acquisition-by-channel', { start: prev.start, end: prev.end, metric: 'users' }),
          api('/revenue-by-uh', { start: prev.start, end: prev.end }),
          api('/adr', { start: prev.start, end: prev.end }),
          api('/marketing-dials', { start: prev.start, end: prev.end })
        ])
        if (!cancelled) setData({ kpis, acq, revUH, adr, dials, prevAcq, prevRevUH, prevAdr, prevDials, prev })
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [range.start, range.end, demo])

  return { loading, data, demo }
}

// Helpers
function getSeriesKeys(chartData) {
  const set = new Set()
  for (const row of chartData || []) {
    Object.keys(row || {}).forEach(k => { if (k !== 'date') set.add(k) })
  }
  return Array.from(set)
}
function parseDDMMYY(s) {
  const [dd, mm, yy] = s.split('/')
  return new Date(2000 + parseInt(yy, 10), parseInt(mm, 10) - 1, parseInt(dd, 10))
}
function monthAbbrevFromDDMMYY(dstr) {
  const d = parseDDMMYY(dstr)
  const m = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][d.getMonth()]
  const yy = ('' + d.getFullYear()).slice(-2)
  return `${m}/${yy}`
}

const CHANNEL_PT = {
  'Organic Search': 'Busca Orgânica',
  'Paid Search': 'Busca Paga',
  'Direct': 'Direto',
  'Paid Social': 'Social Pago',
  'Organic Social': 'Social Orgânico',
  'Referral': 'Referência',
  'Display': 'Display',
  'Unassigned': 'Não atribuído'
}

function translatePoints(points) {
  return (points || []).map(p => ({
    date: p.date,
    values: Object.fromEntries(Object.entries(p.values || {}).map(([k, v]) => [CHANNEL_PT[k] || k, v]))
  }))
}

function bucketize(points, spanDays) {
  if (!points || !points.length) return points || []
  if (spanDays > 90) {
    const order = []
    const agg = {}
    for (const p of points) {
      const label = monthAbbrevFromDDMMYY(p.date)
      if (!order.includes(label)) order.push(label)
      for (const [k, v] of Object.entries(p.values || {})) {
        agg[label] = agg[label] || {}
        agg[label][k] = (agg[label][k] || 0) + (v || 0)
      }
    }
    return order.map(label => ({ date: label, values: agg[label] || {} }))
  }
  if (spanDays >= 30) {
    const res = []
    for (let i = 0; i < points.length; i += 7) {
      const block = points.slice(i, i + 7)
      const first = block[0]; const last = block[block.length - 1]
      const label = `${first.date.slice(0, 5)}–${last.date.slice(0, 5)}`
      const values = {}
      for (const p of block) {
        for (const [k, v] of Object.entries(p.values || {})) {
          values[k] = (values[k] || 0) + (v || 0)
        }
      }
      res.push({ date: label, values })
    }
    return res
  }
  return points
}

function sumBySeries(points) {
  const totals = {}
  for (const p of (points || [])) {
    for (const [k, v] of Object.entries(p.values || {})) {
      totals[k] = (totals[k] || 0) + (v || 0)
    }
  }
  return totals
}

function makeDeltaRows(currTotals, prevTotals) {
  const keys = Array.from(new Set([...Object.keys(currTotals || {}), ...Object.keys(prevTotals || {})]))
  return keys.map(k => {
    const a = currTotals[k] || 0
    const b = prevTotals[k] || 0
    const delta = b === 0 ? (a > 0 ? 100 : 0) : ((a - b) / b * 100)
    return { key: k, a, b, delta }
  }).sort((x, y) => y.a - x.a)
}

const PALETTE = ["#2A8C99", "#A8C6A6", "#6D6A69", "#C4A981", "#0E7490", "#64748b", "#94a3b8"]
function colorForKey(key, allKeys) {
  const idx = allKeys.indexOf(key)
  return PALETTE[(idx >= 0 ? idx : 0) % PALETTE.length]
}
function abbrev(name) {
  if (!name) return ''
  if (name.toLowerCase() === 'extras') return 'Extras'
  return name.split(/\s+/).map(w => w[0]?.toUpperCase()).join('').slice(0, 4)
}

function EmptyState() {
  return (<div className="w-full h-full flex items-center justify-center text-sm text-elegant/70">Sem dados para o período selecionado</div>)
}

// Summaries/Insights com loading
function RevUHSummary({ curr, prev, loading }) {
  const rows = useMemo(() => makeDeltaRows(sumBySeries(curr?.points), sumBySeries(prev?.points)), [curr, prev])
  const keys = useMemo(() =>
    getSeriesKeys((curr?.points || []).map(p => ({ date: p.date, ...p.values }))),
    [curr]
  )
  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">Quadro-Resumo</div>
      <div className="card-body" style={{ height: 320, overflowY: 'auto', position: 'relative' }}>
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center">
              <div className="spinner"></div>
              <div className="loading-text">Carregando…</div>
            </div>
          </div>
        )}
        <table className="table-mini text-sm w-full">
          <thead><tr><th>UH</th><th>Receita</th><th>Anterior</th><th>Δ%</th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.key}>
                <td className="flex items-center gap-2">
                  <span className="inline-block w-3 h-3 rounded-sm" style={{ backgroundColor: colorForKey(r.key, keys) }}></span>
                  {abbrev(r.key)}
                </td>
                <td>{formatBRLShort(r.a)}</td>
                <td>{formatBRLShort(r.b)}</td>
                <td className={r.delta >= 0 ? 'delta-pos' : 'delta-neg'}>{r.delta.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function RevUHInsights({ curr, prev, loading }) {
  const content = useMemo(() => {
    const rows = makeDeltaRows(sumBySeries(curr?.points), sumBySeries(prev?.points))
    if (!rows.length) return []
    const top = rows[0]
    const gains = rows.filter(r => r.delta > 0).sort((a, b) => b.delta - a.delta)
    const drops = rows.filter(r => r.delta < 0).sort((a, b) => a.delta - b.delta)
    const totalA = rows.reduce((s, r) => s + r.a, 0)
    const totalB = rows.reduce((s, r) => s + r.b, 0)
    const d = totalB === 0 ? (totalA > 0 ? 100 : 0) : ((totalA - totalB) / totalB * 100)
    return [
      <p key="p1">No período, a unidade <strong>{top.key}</strong> apresentou a maior receita, somando <strong>{formatBRLShort(top.a)}</strong>.</p>,
      gains[0] ? <p key="p2">Maior crescimento: <strong>{gains[0].key}</strong> (+<strong>{gains[0].delta.toFixed(1)}%</strong>).</p> : null,
      drops[0] ? <p key="p3">Maior queda: <strong>{drops[0].key}</strong> (<strong>{drops[0].delta.toFixed(1)}%</strong>).</p> : null,
      <p key="p4">Tendência geral (vs. período anterior): <strong>{d >= 0 ? '+' : ''}{d.toFixed(1)}%</strong>.</p>
    ].filter(Boolean)
  }, [curr, prev])

  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">Insights</div>
      <div className="card-body" style={{ height: 320, overflowY: 'auto', position: 'relative' }}>
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center">
              <div className="spinner"></div>
              <div className="loading-text">Carregando…</div>
            </div>
          </div>
        )}
        {content.length ? content : <div className="text-elegant/70 text-sm">Sem destaques para o período.</div>}
      </div>
    </div>
  )
}

function AcquisitionSummary({ curr, prev, loading }) {
  const rows = useMemo(() => makeDeltaRows(sumBySeries(curr?.points), sumBySeries(prev?.points)), [curr, prev])
  const keys = useMemo(() =>
    getSeriesKeys(translatePoints(curr?.points).map(p => ({ date: p.date, ...p.values }))),
    [curr]
  )
  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">Quadro-Resumo</div>
      <div className="card-body" style={{ height: 320, overflowY: 'auto', position: 'relative' }}>
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center">
              <div className="spinner"></div>
              <div className="loading-text">Carregando…</div>
            </div>
          </div>
        )}
        <table className="table-mini text-sm w-full">
          <thead><tr><th>Canal</th><th>Users</th><th>Anterior</th><th>Δ%</th></tr></thead>
          <tbody>
            {rows.map(r => {
              const name = CHANNEL_PT[r.key] || r.key
              return (
                <tr key={r.key}>
                  <td className="flex items-center gap-2">
                    <span className="inline-block w-3 h-3 rounded-sm" style={{ backgroundColor: colorForKey(name, keys) }}></span>
                    {abbrev(name)}
                  </td>
                  <td>{Math.round(r.a).toLocaleString('pt-BR')}</td>
                  <td>{Math.round(r.b).toLocaleString('pt-BR')}</td>
                  <td className={r.delta >= 0 ? 'delta-pos' : 'delta-neg'}>{r.delta.toFixed(1)}%</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function AcquisitionInsights({ curr, prev, loading }) {
  const content = useMemo(() => {
    const rows = makeDeltaRows(sumBySeries(curr?.points), sumBySeries(prev?.points))
    if (!rows.length) return []
    const top = rows[0]
    const gains = rows.filter(r => r.delta > 0).sort((a, b) => b.delta - a.delta)
    const drops = rows.filter(r => r.delta < 0).sort((a, b) => a.delta - b.delta)
    const totalA = rows.reduce((s, r) => s + r.a, 0)
    const totalB = rows.reduce((s, r) => s + r.b, 0)
    const d = totalB === 0 ? (totalA > 0 ? 100 : 0) : ((totalA - totalB) / totalB * 100)
    const topName = CHANNEL_PT[top.key] || top.key
    return [
      <p key="p1">Canal líder: <strong>{topName}</strong> com <strong>{Math.round(top.a).toLocaleString('pt-BR')}</strong> usuários.</p>,
      gains[0] ? <p key="p2">Maior crescimento: <strong>{CHANNEL_PT[gains[0].key] || gains[0].key}</strong> (+<strong>{gains[0].delta.toFixed(1)}%</strong>).</p> : null,
      drops[0] ? <p key="p3">Maior queda: <strong>{CHANNEL_PT[drops[0].key] || drops[0].key}</strong> (<strong>{drops[0].delta.toFixed(1)}%</strong>).</p> : null,
      <p key="p4">Tendência geral (vs. período anterior): <strong>{d >= 0 ? '+' : ''}{d.toFixed(1)}%</strong>.</p>
    ].filter(Boolean)
  }, [curr, prev])

  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">Insights</div>
      <div className="card-body" style={{ height: 320, overflowY: 'auto', position: 'relative' }}>
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center">
              <div className="spinner"></div>
              <div className="loading-text">Carregando…</div>
            </div>
          </div>
        )}
        {content.length ? content : <div className="text-elegant/70 text-sm">Sem destaques para o período.</div>}
      </div>
    </div>
  )
}

function AcquisitionLine({ series, spanDays, loading }) {
  const translated = useMemo(() => translatePoints(series?.points), [series])
  const bucketed = useMemo(() => bucketize(translated, spanDays), [translated, spanDays])
  const chartData = useMemo(() => bucketed.map(p => ({ date: p.date, ...p.values })), [bucketed])
  const keys = useMemo(() => getSeriesKeys(chartData), [chartData])
  const hasData = chartData.length > 0 && keys.length > 0

  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">Aquisição de Tráfego (Users)</div>
      <div className="card-body" style={{ height: 320, position: 'relative' }}>
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center">
              <div className="spinner"></div>
              <div className="loading-text">Carregando…</div>
            </div>
          </div>
        )}
        {!hasData ? (
          <EmptyState />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              {keys.map((k, i) => (
                <Line key={k} type="linear" dataKey={k} strokeWidth={2} dot={{ r: 2 }} stroke={PALETTE[i % PALETTE.length]} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

function bucketizeRevenue(points, spanDays) {
  if (!points || !points.length) return points || []
  if (spanDays >= 90) {
    const res = []
    for (let i = 0; i < points.length; i += 7) {
      const block = points.slice(i, i + 7)
      const first = block[0]; const last = block[block.length - 1]
      const label = `${first.date.slice(0, 5)}–${last.date.slice(0, 5)}`
      const values = {}
      for (const p of block) {
        for (const [k, v] of Object.entries(p.values || {})) {
          values[k] = (values[k] || 0) + (v || 0)
        }
      }
      res.push({ date: label, values })
    }
    return res
  }
  return points
}

function RevenueByUH({ data, spanDays, loading }) {
  const raw = useMemo(() => data?.points ? data.points : [], [data])
  const bucketed = useMemo(() => bucketizeRevenue(raw, spanDays), [raw, spanDays])
  const chartData = useMemo(() => bucketed.map(p => ({ date: p.date, ...p.values })), [bucketed])
  const keys = useMemo(() => getSeriesKeys(chartData), [chartData])
  const hasData = chartData.length > 0 && keys.length > 0

  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">Receita por período (por UH)</div>
      <div className="card-body" style={{ height: 320, position: 'relative' }}>
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center">
              <div className="spinner"></div>
              <div className="loading-text">Carregando…</div>
            </div>
          </div>
        )}
        {!hasData ? (
          <EmptyState />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => formatBRLShort(v)} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => formatBRLShort(v)} />
              <Legend />
              {keys.map((k, i) => (
                <Bar key={k} dataKey={k} stackId="rev" fill={PALETTE[i % PALETTE.length]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

// ADR novo
function ADRChart({ series, loading, spanDays }) {
  const raw = useMemo(() => (series?.points || []).map(p => ({ date: p.date, ADR: p.adr })), [series])
  const dataAgg = useMemo(() => {
    if (!raw?.length) return raw
    if (spanDays >= 90) {
      const res = []
      for (let i = 0; i < raw.length; i += 7) {
        const blk = raw.slice(i, i + 7)
        const label = `${blk[0].date.slice(0, 5)}–${blk[blk.length - 1].date.slice(0, 5)}`
        const avg = blk.reduce((s, r) => s + (r.ADR || 0), 0) / blk.length
        res.push({ date: label, ADR: avg })
      }
      return res
    }
    return raw
  }, [raw, spanDays])

  const hasData = (dataAgg?.length || 0) > 0

  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">
        <span title='(total da receita dividido pelo total do evento "compras" do dia)' style={{ cursor: 'help' }}>
          Preço Médio Por Compra <span style={{ fontSize: 10 }}>(total da receita dividido pelo total do evento "compras" do dia)</span>
        </span>
      </div>
      <div className="card-body" style={{ height: 320, position: 'relative' }}>
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center">
              <div className="spinner"></div>
              <div className="loading-text">Carregando dados…</div>
            </div>
          </div>
        )}
        {!hasData ? (
          <EmptyState />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dataAgg}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => formatBRLShort(v)} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => formatBRLShort(v)} />
              <Area type="linear" dataKey="ADR" stroke="#2A8C99" fill="#A8C6A6" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

function DialCard({ label, titleHint, value, prev, deltaPct, format, loading }) {
  const pct = Math.max(
    0,
    Math.min(1, prev > 0 ? value / (prev * 1.5) : value > 0 ? 0.66 : 0)
  );
  const angle = -90 + pct * 180;

  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="card-header">
        <span title={titleHint} style={{ cursor: 'help' }}>
          {label}
        </span>
      </div>

      <div
        className="card-body"
        style={{
          height: 320,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}
      >
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center">
              <div className="spinner" />
              <div className="loading-text">Carregando dados…</div>
            </div>
          </div>
        )}

        {/* Gauge */}
        <div className="gauge">
          <div className="gauge-arc" />
          <div className="gauge-mask" />
          <div
            className="gauge-needle"
            style={{ transform: `rotate(${angle}deg) translateX(-50%)` }}
          />
          <div className="gauge-hub" />
        </div>

        <div className="mt-3 text-2xl font-bold">{format(value)}</div>
        <div className="text-sm mt-1 text-elegant/80">
          {prev > 0
            ? `vs. ant.: ${format(prev)} (${
                deltaPct >= 0 ? '+' : ''
              }${(deltaPct || 0).toFixed(1)}%)`
            : 'Sem período anterior'}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const { mode, setMode, custom, setCustom, range } = useDateRange('7d')
  const { loading, data } = useDashboardData(range)
  const spanDays = useMemo(() => {
    const s = new Date(range.start); const e = new Date(range.end)
    return Math.round((e - s) / (1000 * 60 * 60 * 24)) + 1
  }, [range.start, range.end])

  return (
    <div className="h-full flex flex-col" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      <Topbar mode={mode} setMode={setMode} range={range} setCustom={setCustom} custom={custom} />
      <div className="divider-horizontal w-full" />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <div className="divider-vertical" />
        <main className="flex-1 overflow-auto p-6 space-y-6">

          {/* KPIs */}
          <section className="kpi-grid">
            <KPI title="RECEITA" value={loading ? '—' : formatBRLShort(data?.kpis?.receita)} loading={loading} icon="money" />
            <KPI title="RESERVAS" value={loading ? '—' : data?.kpis?.reservas} loading={loading} icon="bag" />
            <KPI title="DIÁRIAS" value={loading ? '—' : data?.kpis?.diarias} loading={loading} icon="moon" />
            <KPI title="CLICKS" value={loading ? '—' : data?.kpis?.clicks?.toLocaleString('pt-BR')} loading={loading} icon="click" />
            <KPI title="IMPRESSÕES" value={loading ? '—' : data?.kpis?.impressoes?.toLocaleString('pt-BR')} loading={loading} icon="eye" />
            <KPI title="CPC" value={loading ? '—' : `R$${(data?.kpis?.cpc || 0).toFixed(2).replace('.', ',')}`} loading={loading} icon="coin" />
            <KPI title="CUSTO" value={loading ? '—' : `R$${(data?.kpis?.custo || 0).toFixed(2).replace('.', ',')}`} loading={loading} icon="cost" />
          </section>

          {/* Receita por UH + painéis */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-6"><RevenueByUH data={data?.revUH} spanDays={spanDays} loading={loading} /></div>
            <div className="lg:col-span-3"><RevUHSummary curr={data?.revUH} prev={data?.prevRevUH} loading={loading} /></div>
            <div className="lg:col-span-3"><RevUHInsights curr={data?.revUH} prev={data?.prevRevUH} loading={loading} /></div>
          </section>

          {/* Aquisição + painéis */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-6"><AcquisitionLine series={data?.acq} spanDays={spanDays} loading={loading} /></div>
            <div className="lg:col-span-3"><AcquisitionSummary curr={data?.acq} prev={data?.prevAcq} loading={loading} /></div>
            <div className="lg:col-span-3"><AcquisitionInsights curr={data?.acq} prev={data?.prevAcq} loading={loading} /></div>
          </section>

          {/* ADR + Dials */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-6"><ADRChart series={data?.adr} loading={loading} spanDays={spanDays} /></div>
            <div className="lg:col-span-3">
              <DialCard
                label="Conversões"
                titleHint="Conversion Rate = conversions ÷ clicks (Google Ads – campanhas ENABLED). Comparado ao período anterior."
                value={data?.dials?.cr?.value || 0}
                prev={data?.dials?.cr?.prev || 0}
                deltaPct={data?.dials?.cr?.delta_pct || 0}
                format={(v) => `${(v * 100).toFixed(2)}%`}
                loading={loading}
              />
            </div>
            <div className="lg:col-span-3">
              <DialCard
                label="ROAS por Campanha"
                titleHint="ROAS = Receita atribuída ao Google Ads (GA4) ÷ Custo (Google Ads). Comparado ao período anterior."
                value={data?.dials?.roas?.value || 0}
                prev={data?.dials?.roas?.prev || 0}
                deltaPct={data?.dials?.roas?.delta_pct || 0}
                format={(v) => `R$${(v || 0).toFixed(2).replace('.', ',')}`}
                loading={loading}
              />
            </div>
          </section>

          {/* Tabela */}
          <div className="card" style={{ position: 'relative' }}>
            <div className="card-header">Performance de Campanhas (Geral)</div>
            <div className="card-body overflow-auto" style={{ position: 'relative' }}>
              <table className="min-w-full text-sm" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
                <thead>
                  <tr className="text-left">
                    {['Campanha', 'Cliques', 'Impressões', 'CTR', 'CPC', 'Custo', 'Receita', 'ROAS'].map(h => (
                      <th key={h} className="py-2 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data?.table?.rows?.map((r, i) => (
                    <tr key={i} className="border-t border-gray-100">
                      <td className="py-2 pr-4">{r.name}</td>
                      <td className="py-2 pr-4">{r.clicks}</td>
                      <td className="py-2 pr-4">{r.impressoes}</td>
                      <td className="py-2 pr-4">{(r.ctr * 100).toFixed(2)}%</td>
                      <td className="py-2 pr-4">{`R$${(r.cpc || 0).toFixed(2).replace('.', ',')}`}</td>
                      <td className="py-2 pr-4">{`R$${(r.custo || 0).toFixed(2).replace('.', ',')}`}</td>
                      <td className="py-2 pr-4">{formatBRLShort(r.receita)}</td>
                      <td className="py-2 pr-4">{r.roas}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </main>
      </div>
    </div>
  )
}
