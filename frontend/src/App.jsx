// Updated: 2025-09-27 18:35 - Complete PDF and authentication system
// CALMA_MARKER_LOADING_V2
import React, { useEffect, useMemo, useState } from 'react'
import './App.css'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid,
  BarChart, Bar, AreaChart, Area
} from 'recharts'

import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'
import { toPng } from 'html-to-image'
import ReactDOM from 'react-dom/client'
// import emailjs from '@emailjs/browser'
import { AuthProvider, useAuth } from './AuthContext'
import Login from './Login'





// Definição única e clara do endpoint base
const API_BASE = import.meta.env?.VITE_API_URL;

function ensureApiBase(path) {
  const baseRaw = API_BASE || '';
  if (!baseRaw) {
    throw new Error('Backend URL ausente. Defina VITE_API_URL no .env do frontend.');
  }

  // Normaliza slashes
  const base = baseRaw.endsWith('/') ? baseRaw.slice(0, -1) : baseRaw;
  const p = path.startsWith('/') ? path : `/${path}`;

  const baseEndsWithApi = base.endsWith('/api') || base === '/api';
  const pathHasApi = p.startsWith('/api');

  let full = '';
  if (baseEndsWithApi) {
    full = base + p;
  } else {
    full = pathHasApi ? (base + p) : (base + '/api' + p);
  }
  return full;
}


async function fetchMonthlyDatasets(month) {
  const { start, end, spanDays } = monthBoundsJS(month)
  const [revUH, acq, pmc, nets] = await Promise.all([
    api('/revenue-by-uh', { start, end }),
    api('/acquisition-by-channel', { start, end, metric: 'users' }),
    api('/adr', { start, end }),
    api('/ads-networks', { month })
  ])
  return { revUH, acq, pmc, nets, spanDays }
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

function Topbar({ mode, setMode, range, setCustom, custom, onFeedbackClick, user, onLogout }) {
  const [open, setOpen] = useState(false)

  // Meses completos até o mês passado
  const months = useMemo(() => {
    const now = new Date()
    const year = now.getFullYear()
    const currentMonth = now.getMonth() + 1
    const labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    const arr = []
    for (let m = 1; m < currentMonth; m++) {
      const val = `${year}-${String(m).padStart(2, '0')}`
      arr.push({ value: val, label: `${labels[m - 1]}/${String(year).slice(-2)}` })
    }
    return arr.reverse()
  }, [])

  const [selectedMonth, setSelectedMonth] = useState(months[0]?.value || '')

  return (
    <div className="w-full flex items-center justify-between px-6 py-3 bg-surface">
      {/* Esquerda: logo e título */}
      <div className="flex items-center gap-3">
        <img src="/logo-calma-data.png" alt="Calma Data" className="h-8" />
        <div className="topbar-title">C'alma Data, o dashboard da Ilha Faceira</div>
      </div>

      {/* Centro: seletor de mês e botão Resumo Mensal */}
      <div className="flex items-center gap-2">
        <select
          value={selectedMonth}
          onChange={e => setSelectedMonth(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
          title="Selecione um mês completo (o mês vigente não aparece)"
        >
          {months.map(m => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
        <MonthlyReportButton month={selectedMonth} />
      </div>

      {/* Direita: user menu + botão de feedback + seletor de período */}
      <div className="flex items-center gap-2">
        {/* User menu */}
        {user && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Olá, {user.name}</span>
            <button
              onClick={onLogout}
              className="px-3 py-1 rounded-md text-sm text-gray-600 hover:bg-gray-100 transition-colors"
              aria-label="Sair"
            >
              Sair
            </button>
          </div>
        )}

        {/* ✅ Botão correto: chama prop passada pelo App */}
        <button
          onClick={onFeedbackClick}
          className="px-4 py-2 rounded-md text-white text-sm font-medium hover:opacity-80 transition-opacity"
          style={{ backgroundColor: '#A8C6A6' }}
          aria-label="Fale com o desenvolvedor"
        >
          Fale com o Dev
        </button>

        {/* Botões de intervalo */}
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

        {/* Se modo = custom, exibe inputs */}
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


function Sidebar({ active = 'inicio', onNavigate }) {
  const items = [
    { id: 'inicio', label: 'Início', icon: 'home' },
    { id: 'sobre', label: 'Sobre', icon: 'info' },
    { id: 'config', label: 'Configurações', icon: 'settings' }
  ]
  return (
    <aside className="w-24 shrink-0 h-full flex items-start justify-center py-4" aria-label="menu lateral">
      <div className="sidebar-capsule" role="navigation">
        {items.map(it => {
          const isActive = it.id === active
          return (
            <button
              key={it.id}
              title={it.label}
              aria-label={it.label}
              aria-current={isActive ? 'page' : undefined}
              className="hover:opacity-80"
              onClick={() => onNavigate?.(it.id)}
              style={isActive ? { outline: '2px solid #6D6A69', outlineOffset: 2, borderRadius: 8, background: 'rgba(196,169,129,0.22)' } : undefined}
            >
              <Icon name={it.icon} className="sidebar-icon" />
            </button>
          )
        })}
      </div>
    </aside>
  )
}

// Removed duplicate FeedbackModal definition to fix syntax error



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
      setLoading(true)
      try {
        // Removed duplicate 'params' declaration to fix redeclaration error
        const apiParams = { start: range.start, end: range.end }
        const prev = getPrevRange(range)
        const [kpis, acq, revUH, adr, dials] = await Promise.all([
          api('/kpis', apiParams),
          api('/acquisition-by-channel', { ...apiParams, metric: 'users' }),
          api('/revenue-by-uh', apiParams),
          api('/adr', apiParams),
          api('/marketing-dials', apiParams)
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

function formatBRL2(v) {
  return `R$${(v || 0).toFixed(2).replace('.', ',')}`
}

function formatPct2(v) {
  return `${((v || 0) * 100).toFixed(2)}%`
}

function formatPct1(v) {
  return `${((v || 0) * 100).toFixed(1)}%`
}

function monthBoundsJS(monthStr) {
  // 'YYYY-MM' -> { start:'YYYY-MM-DD', end:'YYYY-MM-DD', spanDays:n }
  const [y, m] = monthStr.split('-').map(n => parseInt(n, 10))
  const start = new Date(y, m - 1, 1)
  const end = new Date(y, m, 0) // último dia do mês
  const iso = d => d.toISOString().slice(0, 10)
  return { start: iso(start), end: iso(end), spanDays: Math.round((end - start) / (1000 * 60 * 60 * 24)) + 1 }
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
            ? `vs. ant.: ${format(prev)} (${deltaPct >= 0 ? '+' : ''
            }${(deltaPct || 0).toFixed(1)}%)`
            : 'Sem período anterior'}
        </div>
      </div>
    </div>
  );
}

function CampaignsTable() {
  const [status, setStatus] = useState('enabled')
  const [period, setPeriod] = useState('last30')
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState({ rows: [], total: null })

  const monthsOptions = useMemo(() => {
    const now = new Date()
    const y = now.getFullYear()
    const labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    return Array.from({ length: now.getMonth() + 1 }, (_, i) => {
      const mm = String(i + 1).padStart(2, '0')
      return { value: `${y}-${mm}`, label: `${labels[i]}/${String(y).slice(-2)}` }
    }).reverse()
  }, [])

  async function load() {
    setLoading(true)
    try {
      const params = period === 'last30'
        ? { status: 'all', period }
        : { status: 'all', month: period }

      const resp = await api('/ads-campaigns', params)
      setData(resp || { rows: [], total: null })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [period])

  // Tradução do status
  const translateStatus = (s) => {
    switch (s) {
      case 'ENABLED': return 'Ativa'
      case 'PAUSED': return 'Pausada'
      case 'REMOVED': return 'Removida'
      case 'ENDED': return 'Encerrada'
      case 'ELIGIBLE': return 'Elegível'
      case 'LIMITED': return 'Limitada'
      default: return s || '—'
    }
  }

  // Filtro visual
  const filteredRows = useMemo(() => {
    return (data.rows || [])
      // 1️⃣ Se "Ativas", mostra só as com status válido
      .filter(r => status === 'enabled'
        ? ['ENABLED', 'ELIGIBLE', 'LIMITED'].includes(r.status || r.primary_status)
        : true
      )
      // 2️⃣ Exclui campanhas que não têm dados (zeradas)
      .filter(r => (r.clicks > 0 || r.cost_total > 0 || r.conversions > 0));
  }, [data.rows, status]);


  // Total recalculado
  const filteredTotal = useMemo(() => {
    return filteredRows.reduce((acc, r) => {
      acc.clicks += r.clicks || 0
      acc.cost_total += r.cost_total || 0
      acc.conversions += r.conversions || 0
      return acc
    }, { clicks: 0, cost_total: 0, conversions: 0 })
  }, [filteredRows])

  return (
    <div className="card card-campaigns" style={{ position: 'relative' }}>
      <div className="card-header flex items-center justify-between">
        <div className="flex items-center gap-2">Performance de Campanhas</div>
        <div className="flex items-center gap-2">
          <select
            value={status}
            onChange={e => setStatus(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          >
            <option value="enabled">Ativas</option>
            <option value="all">Todas</option>
          </select>
          <select
            value={period}
            onChange={e => setPeriod(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          >
            <option value="last30">Últimos 30 dias</option>
            {monthsOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="card-body" style={{ position: 'relative' }}>
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center">
              <div className="spinner"></div>
              <div className="loading-text">Carregando dados…</div>
            </div>
          </div>
        )}

        <div className="table-campaigns-wrapper">
          <table className="table-campaigns">
            <thead>
              <tr>
                <th>Campanha</th>
                <th>Status</th>
                <th>Tipo</th>
                <th className="cell-right">Clicks</th>
                <th className="cell-right">Custo total</th>
                <th className="cell-right">Custo médio</th>
                <th className="cell-right">Conv. %</th>
                <th className="cell-right">Custo Conv.</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.map((r, i) => (
                <tr key={i}>
                  <td>{r.name}</td>
                  <td>{translateStatus(r.status)}</td>
                  <td>{r.type}</td>
                  <td className="cell-right">{r.clicks.toLocaleString('pt-BR')}</td>
                  <td className="cell-right">{formatBRL2(r.cost_total)}</td>
                  <td className="cell-right">{formatBRL2(r.avg_cpc)}</td>
                  <td className="cell-right">{formatPct2(r.conv_rate)}</td>
                  <td className="cell-right">{formatBRL2(r.cost_per_conv)}</td>
                </tr>
              ))}

              {filteredRows.length > 0 && (
                <tr>
                  <td><strong>Total</strong></td>
                  <td>—</td>
                  <td>—</td>
                  <td className="cell-right"><strong>{filteredTotal.clicks.toLocaleString('pt-BR')}</strong></td>
                  <td className="cell-right"><strong>{formatBRL2(filteredTotal.cost_total)}</strong></td>
                  <td className="cell-right">—</td>
                  <td className="cell-right">—</td>
                  <td className="cell-right">—</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}



function NetworksBreakdown() {
  const [period, setPeriod] = useState('last30')
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [hoverKey, setHoverKey] = useState(null) // <- NOVO

  const monthsOptions = useMemo(() => {
    const now = new Date()
    const y = now.getFullYear()
    const labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    return Array.from({ length: now.getMonth() + 1 }, (_, i) => {
      const mm = String(i + 1).padStart(2, '0')
      return { value: `${y}-${mm}`, label: `${labels[i]}/${String(y).slice(-2)}` }
    }).reverse()
  }, [])

  async function load() {
    setLoading(true)
    try {
      const params = period === 'last30' ? { period } : { month: period }
      const resp = await api('/ads-networks', params)
      setData(resp)
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { load() }, [period])

  // Cores e rótulos PT-BR
  const COLORS = { 'Google Search': '#2A8C99', 'Search partners': '#A8C6A6', 'Display Network': '#C4A981' }
  const LABEL_PT = { 'Google Search': 'Pesquisa Google', 'Search partners': 'Parceiros de pesquisa', 'Display Network': 'Rede de Display' }

  // 3 barras com shares (%)
  const bars = useMemo(() => {
    if (!data?.shares) return []
    return [
      { label: 'Conversões', key: 'conversions', ...data.shares.conversions },
      { label: 'Custo', key: 'cost', ...data.shares.cost },
      { label: 'Valor de conv.', key: 'conv_value', ...data.shares.conv_value },
    ]
  }, [data])

  const hasData = bars.length > 0

  // Helpers de formatação
  const fmtPct1 = (v) => `${((v || 0) * 100).toFixed(1)}%`
  const fmtBR = (v) => `R$${(v || 0).toFixed(2).replace('.', ',')}`
  const fmtInt = (v) => (v || 0).toLocaleString('pt-BR')

  // Tooltip customizado (valor absoluto + % do total) respeitando a série sob hover
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length || !data?.totals) return null
    const items = payload.filter(it => typeof it.value === 'number')
    const p = (hoverKey && items.find(it => it.dataKey === hoverKey)) || items[0]
    if (!p) return null

    const networkKey = p.dataKey
    const row = p.payload || {}
    const metricKey = row.key // 'conversions' | 'cost' | 'conv_value'
    const share = p.value || 0
    const total = data.totals[metricKey] || 0
    const abs = share * total

    const valueStr = metricKey === 'conversions' ? fmtInt(abs) : fmtBR(abs)
    const tituloRede = LABEL_PT[networkKey] || networkKey
    const labelMetric = row.label

    return (
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '8px 10px', boxShadow: '0 4px 14px rgba(0,0,0,0.06)' }}>
        <div style={{ fontWeight: 700, marginBottom: 4 }}>{tituloRede}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
          <span style={{ display: 'inline-block', width: 10, height: 10, background: COLORS[networkKey], borderRadius: 2 }} />
          <span>{labelMetric}:</span>
          <strong style={{ marginLeft: 4 }}>{valueStr}</strong>
        </div>
        <div style={{ fontSize: 12, color: '#6D6A69', marginTop: 4 }}>({fmtPct1(share)} do total)</div>
      </div>
    )
  }

  return (
    <div
      className="card"
      style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div>
            <div>Redes (Google Ads)</div>
            <div style={{ fontSize: 10, color: '#6D6A69', marginTop: 2 }}>
              Resumo de como seus anúncios estão performando nessas redes
            </div>
          </div>
          <div className="flex items-center gap-2">
            <select value={period} onChange={e => setPeriod(e.target.value)} className="border rounded px-2 py-1 text-sm">
              <option value="last30">Últimos 30 dias</option>
              {monthsOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </div>
        </div>

        {/* legenda compacta dentro do header */}
        <div style={{ display: 'flex', gap: 14, alignItems: 'center', fontSize: 12, color: '#6D6A69', padding: '2px 0 8px 0' }}>
          {Object.keys(COLORS).map(k => (
            <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 10, height: 10, background: COLORS[k], borderRadius: 2, display: 'inline-block' }} />
              <span>{LABEL_PT[k] || k}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card-body" style={{ minHeight: 320, position: 'relative', flex: 1 }}>
        {loading && (
          <div className="loading-overlay">
            <div className="flex flex-col items-center"><div className="spinner"></div><div className="loading-text">Carregando dados…</div></div>
          </div>
        )}

        {!hasData ? (
          typeof EmptyState === 'function'
            ? <EmptyState />
            : <div className="text-sm text-gray-500">Sem dados para o período.</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart layout="vertical" data={bars} margin={{ left: 24, right: 20, top: 4, bottom: 6 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(1)}%`} tick={{ fontSize: 12 }} />
              <YAxis dataKey="label" type="category" width={110} tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              {Object.keys(COLORS).map(k => (
                <Bar
                  key={k}
                  dataKey={k}
                  stackId="share"
                  fill={COLORS[k]}
                  isAnimationActive={false}
                  onMouseEnter={() => setHoverKey(k)}
                  onMouseMove={() => setHoverKey(k)}
                  onMouseLeave={() => setHoverKey(null)}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}



function WelcomeCard() {
  return (
    <div
      className="card"
      style={{
        background: '#2A8C99',
        color: '#2A8C99',
        borderColor: '#2A8C99',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        className="card-header"
        style={{ borderColor: 'rgba(255,255,255,0.35)', color: '#ffffff' }}
      >
        Bem-vindos ao C'alma Data
      </div>

      <div
        className="card-body"
        style={{
          flex: 1,
          minHeight: 320,
          overflowY: 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 16,
        }}
      >
        <div
          style={{
            whiteSpace: 'pre-wrap',
            textAlign: 'center',
            lineHeight: 1.8,
            fontSize: '0.95rem',
            maxWidth: 680,
          }}
        >
          {`Uma ferramenta que reflete a essência da marca

O Calma Data é mais do que um painel de indicadores: é uma janela estratégica para enxergar o coração da operação da Pousada Ilha Faceira. Assim como cada detalhe da pousada foi pensado para acolher, inspirar e encantar, esta ferramenta traduz a alma do negócio em dados acessíveis e significativos, ajudando a transformar números em decisões conscientes e cheias de propósito.

Aqui, cada gráfico, cada indicador e cada tabela foi cuidadosamente desenhado para contar uma história: a história de como a pousada acolhe seus hóspedes, gera valor, e continua crescendo de forma autêntica, sustentável e coerente com sua identidade

Se você tiver qualquer dúvidas, pergunta, sugestão de melhoria, ou simplesmente quiser falar com alguém sobre a ferramenta, basta clicar em um dos ícones “Fale com o Dev” espalhados ao longo da página, em cada componente (gráfico, card, etc).`}
        </div>
      </div>
    </div>
  )
}







// === Monthly Report (PDF) ===
function MonthlyReportButton({ month }) {
  const [busy, setBusy] = useState(false)
  const tip = "Você tem direito a 4 relatórios/mês"
  async function generate() {
    if (!month) { alert('Selecione um mês completo'); return }
    setBusy(true)
    try {
      const res = await fetch(ensureApiBase('/monthly-report'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ month })
      })
      if (res.status === 429) {
        const j = await res.json()
        alert(j.detail || 'Limite mensal de 4 relatórios atingido.')
        return
      }
      if (!res.ok) { throw new Error('Falha ao gerar resumo mensal') }
      const data = await res.json()

      // >>> AVISO GPT
      if (data?.gpt && data.gpt.ok === false) {
        if (data.gpt.reason === 'quota_exceeded') {
          console.warn('OpenAI: cota excedida. Gerando PDF com textos padrão.')
        } else if (data.gpt.reason === 'no_api_key') {
          console.warn('OpenAI: chave OpenAI ausente. Gerando PDF com textos padrão.')
        } else {
          console.warn('OpenAI: indisponível. Gerando PDF com textos padrão.')
        }
      }

      const imgs = await captureMonthlyCharts(month)
      await buildMonthlyPdf(month, data, imgs)
    } catch (e) {
      console.error(e)
      alert('Não foi possível gerar o PDF agora. Tente novamente.')
    } finally {
      setBusy(false)
    }
  }
  return (
    <button
      onClick={generate}
      title={tip}
      disabled={busy}
      style={{ background: '#A28C99', color: '#fff', border: '1px solid #6D6A69', borderRadius: 8, padding: '8px 16px', fontWeight: 600 }}
    >
      {busy ? 'Gerando…' : 'Resumo Mensal'}
    </button>
  )
}

async function buildMonthlyPdf(month, payload, imgs) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' })
  const W = doc.internal.pageSize.getWidth()
  const H = doc.internal.pageSize.getHeight()

  // Layout base
  const M = 40             // margem externa
  const GAP = 18           // gap entre colunas
  const COLW = (W - M * 2 - GAP) / 2
  const IMG_H = 190        // altura das imagens dos gráficos

  // Paleta do cabeçalho
  const BRAND = { r: 42, g: 140, b: 153 }   // #2A8C99
  const LINE = { r: 109, g: 106, b: 105 }  // #6D6A69

  // Helpers de formatação p/ a tabela
  const brl = (v) => `R$${Number(v || 0).toFixed(2).replace('.', ',')}`
  const asInt = (v) => Number(v || 0).toLocaleString('pt-BR')
  const asPct = (v) => `${Number(v || 0).toFixed(1)}%`
  const cellFmt = (metric, v) => (metric === 'Receita' || metric === 'CPC') ? brl(v) : asInt(v)

  // Cabeçalho por página
  function header(title) {
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(16)
    doc.setTextColor(BRAND.r, BRAND.g, BRAND.b)
    doc.text(title, M, M)
    doc.setDrawColor(LINE.r, LINE.g, LINE.b)
    doc.setLineWidth(1)
    doc.line(M, M + 8, W - M, M + 8)
    doc.setTextColor(0)
  }

  // Texto multilinha
  function addText(txt, x, y, maxW, lh = 14, fs = 10) {
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(fs)
    const words = (txt || '').toString().split(/\s+/)
    let line = '', yy = y
    for (let i = 0; i < words.length; i++) {
      const test = (line ? line + ' ' : '') + words[i]
      const w = doc.getTextWidth(test)
      if (w > maxW) { doc.text(line, x, yy); yy += lh; line = words[i] }
      else { line = test }
    }
    if (line) { doc.text(line, x, yy); yy += lh }
    return yy
  }

  // ===== Página 1: Título + Tabela-resumo (AutoTable) + Resumo Executivo =====
  header(`Resumo mensal – ${month}`)

  const cur = payload.summary?.current || {}
  const prev = payload.summary?.previous || {}
  const dlt = payload.summary?.delta_pct || {}

  // Linhas-base
  const rowsRaw = [
    ['Receita', cur.receita, prev.receita, dlt.receita],
    ['Reservas', cur.reservas, prev.reservas, dlt.reservas],
    ['Diárias', cur.diarias, prev.diarias, dlt.diarias],
    ['Clicks', cur.clicks, prev.clicks, dlt.clicks],
    ['Impressões', cur.impressoes, prev.impressoes, dlt.impressoes],
    ['CPC', cur.cpc, prev.cpc, dlt.cpc],
  ]
  const rows = rowsRaw.map(r => [
    r[0],
    cellFmt(r[0], r[1]),
    cellFmt(r[0], r[2]),
    asPct(r[3])
  ])

  // Tabela-resumo (coluna esquerda) — travada com AutoTable
  const tableStartY = M + 26
  autoTable(doc, {
    startY: tableStartY,
    margin: { left: M, right: W - M - COLW }, // limita à coluna esquerda
    tableWidth: COLW,
    head: [['Indicador', 'Mês atual', 'Mês anterior', 'Δ%']],
    body: rows,
    styles: {
      font: 'helvetica', fontSize: 10, cellPadding: 6,
      lineColor: [LINE.r, LINE.g, LINE.b], lineWidth: 0.5, textColor: [LINE.r, LINE.g, LINE.b]
    },
    headStyles: { fillColor: [BRAND.r, BRAND.g, BRAND.b], textColor: 255, halign: 'left' },
    alternateRowStyles: { fillColor: [250, 250, 247] },
    columnStyles: {
      1: { halign: 'right' },
      2: { halign: 'right' },
      3: { halign: 'right' }
    }
  })

  // Coluna direita: Resumo Executivo (GPT ou fallback)
  const rightX = M + COLW + GAP
  let rightY = M + 26
  doc.setFont('helvetica', 'bold'); doc.setFontSize(12); doc.setTextColor(BRAND.r, BRAND.g, BRAND.b)
  doc.text('Análise (Resumo Executivo)', rightX, rightY)
  doc.setTextColor(0); doc.setFont('helvetica', 'normal'); doc.setFontSize(10); rightY += 14

  const resumoTexto =
    payload.sections?.resumo
    || (payload?.gpt?.reason === 'quota_exceeded'
      ? 'Análise automática indisponível (cota da OpenAI excedida).'
      : payload?.gpt?.reason === 'no_api_key'
        ? 'Análise automática indisponível (chave OpenAI ausente).'
        : 'Análise automática indisponível no momento.')

  rightY = addText(resumoTexto, rightX, rightY, COLW, 14)

  // ===== Página 2: Receita por UH =====
  doc.addPage()
  header('Receita por UH')
  let leftY = M + 20
  if (imgs?.uh) { doc.addImage(imgs.uh, 'PNG', M, leftY, COLW, IMG_H) }
  else { doc.setDrawColor(196, 169, 129); doc.rect(M, leftY, COLW, IMG_H) }
  let rightX2 = M + COLW + GAP, rightY2 = M + 20
  doc.setFont('helvetica', 'bold'); doc.setFontSize(12)
  doc.text('Análise – Receita por UH', rightX2, rightY2); rightY2 += 14
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10)
  rightY2 = addText(payload.sections?.uh || '—', rightX2, rightY2, COLW, 14)

  // ===== Página 3: Aquisição =====
  doc.addPage()
  header('Aquisição de Tráfego (Users)')
  leftY = M + 20
  if (imgs?.acq) { doc.addImage(imgs.acq, 'PNG', M, leftY, COLW, IMG_H) }
  else { doc.setDrawColor(196, 169, 129); doc.rect(M, leftY, COLW, IMG_H) }
  rightX2 = M + COLW + GAP; rightY2 = M + 20
  doc.setFont('helvetica', 'bold'); doc.setFontSize(12)
  doc.text('Análise – Aquisição', rightX2, rightY2); rightY2 += 14
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10)
  rightY2 = addText(payload.sections?.acquisition || '—', rightX2, rightY2, COLW, 14)

  // ===== Página 4: Preço Médio por Compra =====
  doc.addPage()
  header('Preço Médio Por Compra')
  leftY = M + 20
  if (imgs?.pmc) { doc.addImage(imgs.pmc, 'PNG', M, leftY, COLW, IMG_H) }
  else { doc.setDrawColor(196, 169, 129); doc.rect(M, leftY, COLW, IMG_H) }
  rightX2 = M + COLW + GAP; rightY2 = M + 20
  doc.setFont('helvetica', 'bold'); doc.setFontSize(12)
  doc.text('Análise – Preço Médio por Compra', rightX2, rightY2); rightY2 += 14
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10)
  rightY2 = addText(payload.sections?.pmc || '—', rightX2, rightY2, COLW, 14)

  // ===== Página 5: Redes =====
  doc.addPage()
  header('Redes (Google Ads)')
  leftY = M + 20
  if (imgs?.nets) { doc.addImage(imgs.nets, 'PNG', M, leftY, COLW, IMG_H) }
  else { doc.setDrawColor(196, 169, 129); doc.rect(M, leftY, COLW, IMG_H) }
  rightX2 = M + COLW + GAP; rightY2 = M + 20
  doc.setFont('helvetica', 'bold'); doc.setFontSize(12)
  doc.text('Análise – Redes', rightX2, rightY2); rightY2 += 14
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10)
  rightY2 = addText(payload.sections?.networks || '—', rightX2, rightY2, COLW, 14)

  // ===== Página 6: Conclusão =====
  doc.addPage()
  header('Análise consolidada do mês')
  doc.setFont('helvetica', 'normal'); doc.setFontSize(11)
  addText(
    payload.sections?.final ||
    (payload?.gpt?.reason === 'quota_exceeded'
      ? 'Análise automática indisponível (cota da OpenAI excedida).'
      : payload?.gpt?.reason === 'no_api_key'
        ? 'Análise automática indisponível (chave OpenAI ausente).'
        : 'Análise automática indisponível no momento.'),
    M, M + 24, W - M * 2, 16
  )

  doc.save(`Resumo_Mensal-${month}.pdf`)
}



function drawSectionHeader(doc, text, x, y) {
  doc.setFont('helvetica', 'bold'); doc.setFontSize(12); doc.setTextColor(42, 140, 153)
  doc.text(text, x, y)
  doc.setTextColor(0)
}

function addMultilineText(doc, text, x, y, maxW, lh) {
  const words = (text || '').toString().split(/\s+/)
  let line = ''
  let yy = y
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10)
  for (let i = 0; i < words.length; i++) {
    const test = (line ? line + ' ' : '') + words[i]
    const w = doc.getTextWidth(test)
    if (w > maxW) {
      doc.text(line, x, yy); yy += lh; line = words[i]
    } else {
      line = test
    }
  }
  if (line) { doc.text(line, x, yy); yy += lh }
  return yy
}

function formatCell(v, key) {
  if (key === 'CPC' || key === 'Receita') return `R$${Number(v || 0).toFixed(2).replace('.', ',')}`
  if (typeof v === 'number') return v.toLocaleString('pt-BR')
  return (v || 0)
}

function SnapshotCharts({ revUH, acq, pmc, nets, spanDays, onReady }) {
  const revRef = React.useRef(null)
  const acqRef = React.useRef(null)
  const pmcRef = React.useRef(null)
  const netRef = React.useRef(null)

  const COLORS = { 'Google Search': '#2A8C99', 'Search partners': '#A8C6A6', 'Display Network': '#C4A981' }
  const bars = React.useMemo(() => {
    const s = nets?.shares || {}
    if (!s.conversions || !s.cost || !s.conv_value) return []
    return [
      { label: 'Conversões', ...s.conversions },
      { label: 'Custo', ...s.cost },
      { label: 'Valor de conv.', ...s.conv_value },
    ]
  }, [nets])

  const revChartData = React.useMemo(() => (revUH?.points || []).map(p => ({ date: p.date, ...(p.values || {}) })), [revUH])
  const acqChartData = React.useMemo(() => (acq?.points || []).map(p => ({ date: p.date, ...(p.values || {}) })), [acq])
  const pmcChartData = React.useMemo(() => (pmc?.points || []).map(p => ({ date: p.date, PMC: p.adr })), [pmc])

  React.useEffect(() => {
    const cap = async () => {
      // pequeno delay para garantir paint
      await new Promise(r => setTimeout(r, 500))
      const opts = { cacheBust: true, pixelRatio: 2, backgroundColor: '#fff' }
      const [imgRev, imgAcq, imgPmc, imgNet] = await Promise.all([
        toPng(revRef.current, opts),
        toPng(acqRef.current, opts),
        toPng(pmcRef.current, opts),
        toPng(netRef.current, opts),
      ])
      onReady({ uh: imgRev, acq: imgAcq, pmc: imgPmc, nets: imgNet })
    }
    cap()
  }, [revUH, acq, pmc, nets, onReady])

  const boxStyle = { width: 560, height: 210, background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 8 }

  return (
    <div style={{ position: 'fixed', left: '-10000px', top: 0, width: 1200, padding: 20, background: '#fff', zIndex: -1 }}>
      {/* Receita por UH */}
      <div ref={revRef} style={boxStyle}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={revChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={(v) => formatBRLShort(v)} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => formatBRLShort(v)} />
            {(() => {
              const keys = getSeriesKeys(revChartData)
              return keys.map((k, i) => <Bar key={k} dataKey={k} stackId="rev" fill={PALETTE[i % PALETTE.length]} />)
            })()}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Aquisição */}
      <div ref={acqRef} style={{ ...boxStyle, marginTop: 16 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={acqChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            {(() => {
              const keys = getSeriesKeys(acqChartData)
              return keys.map((k, i) => <Line key={k} type="linear" dataKey={k} strokeWidth={2} dot={false} stroke={PALETTE[i % PALETTE.length]} />)
            })()}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Preço Médio por Compra */}
      <div ref={pmcRef} style={{ ...boxStyle, marginTop: 16 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={pmcChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={(v) => formatBRLShort(v)} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => formatBRLShort(v)} />
            <Area type="linear" dataKey="PMC" stroke="#2A8C99" fill="#A8C6A6" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Redes */}
      <div ref={netRef} style={{ ...boxStyle, marginTop: 16 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={bars} margin={{ left: 30, right: 14, top: 6, bottom: 6 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(1)}%`} tick={{ fontSize: 11 }} />
            <YAxis dataKey="label" type="category" width={110} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v, k) => [`${(v * 100).toFixed(1)}%`, k]} />
            {Object.keys(COLORS).map(k => (<Bar key={k} dataKey={k} stackId="share" fill={COLORS[k]} />))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

async function captureMonthlyCharts(month) {
  const datasets = await fetchMonthlyDatasets(month)
  return new Promise((resolve) => {
    const mount = document.createElement('div')
    document.body.appendChild(mount)
    const root = ReactDOM.createRoot(mount)
    const handleReady = (imgs) => {
      setTimeout(() => {
        root.unmount()
        mount.remove()
      }, 0)
      resolve(imgs)
    }
    root.render(
      <SnapshotCharts
        revUH={datasets.revUH}
        acq={datasets.acq}
        pmc={datasets.pmc}
        nets={datasets.nets}
        spanDays={datasets.spanDays}
        onReady={handleReady}
      />
    )
  })
}

// === Sobre: exibe o PDF em-embutido dentro do app ===

function AboutPage({ onBack }) {
  return (
    <div className="card" style={{ borderColor: '#6D6A69' }}>
      <div className="card-header flex items-center justify-between">
        <div className="topbar-title">Sobre</div>
        <button
          onClick={onBack}
          className="chip"
          style={{ background: '#2A8C99', color: '#fff', borderColor: '#6D6A69' }}
          title="Voltar ao dashboard"
        >
          Voltar
        </button>
      </div>

      <div className="card-body pdf-container">
        {/* Usa o viewer nativo do navegador (com toolbar e navegação) */}
        <iframe
          title="Sobre - Calma Data"
          src="/About.pdf#toolbar=1&navpanes=1&view=FitH"
          className="pdf-frame"
        />
      </div>
    </div>
  )
}


function SettingsComingSoon({ onBack }) {
  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <div className="topbar-title">Configurações</div>
        <button
          onClick={onBack}
          className="chip"
          style={{ background: '#2A8C99', color: '#fff', borderColor: '#6D6A69' }}
        >
          Voltar
        </button>
      </div>
      <div className="card-body" style={{ minHeight: 320 }}>
        Em breve.
      </div>
    </div>
  )
}

function FeedbackModal({ open, onClose }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [component, setComponent] = useState('Geral')
  const [files, setFiles] = useState([])
  const [busy, setBusy] = useState(false)
  const components = [
    'Geral',
    'KPIs',
    'Receita por UH',
    'Aquisição (Users)',
    'Preço Médio por Compra',
    'Redes (Google Ads)',
    'Tabela de Campanhas',
    'Sobre / PDF',
    'Outro'
  ]
  if (!open) return null

  async function onSubmit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('name', name)
      fd.append('email', email)
      fd.append('message', message)
      fd.append('component', component)
      for (const f of files) fd.append('files', f)

      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/feedback`, { method: 'POST', body: fd })
      const j = await res.json()
      if (!res.ok) throw new Error(j?.detail || 'Falha ao enviar')

      alert('Feedback enviado! Obrigado por contribuir.')
      onClose()
      setName('')
      setEmail('')
      setMessage('')
      setComponent('Geral')
      setFiles([])
    } catch (err) {
      console.error(err)
      alert('Não foi possível enviar agora. Tente novamente mais tarde.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>Fale com o Dev</div>
          <button className="btn-ghost" onClick={onClose}>Fechar</button>
        </div>
        <div className="modal-body">
          <form onSubmit={onSubmit} className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-sm block mb-1">Seu nome</label>
                <input className="input" value={name} onChange={e => setName(e.target.value)} required />
              </div>
              <div>
                <label className="text-sm block mb-1">Seu email</label>
                <input type="email" className="input" value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-sm block mb-1">Componente relacionado</label>
                <select className="select" value={component} onChange={e => setComponent(e.target.value)}>
                  {components.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm block mb-1">Anexos (opcional)</label>
                <input type="file" multiple className="input" onChange={e => setFiles(Array.from(e.target.files || []))} />
              </div>
            </div>

            <div>
              <label className="text-sm block mb-1">Mensagem</label>
              <textarea className="textarea" rows={5} value={message} onChange={e => setMessage(e.target.value)} required />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button type="button" className="btn-ghost" onClick={onClose}>Cancelar</button>
              <button type="submit" className="btn-primary" disabled={busy}>
                {busy ? 'Enviando...' : 'Enviar'}
              </button>
            </div>
          </form>
          <div className="text-xs text-elegant/70 mt-2">
            Arquivos permitidos: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, GIF (até 10MB cada)
          </div>
        </div>
      </div>
    </div>
  )
}



function Dashboard() {
  const { user, logout } = useAuth()
  const { mode, setMode, custom, setCustom, range } = useDateRange('7d')
  const { loading, data } = useDashboardData(range)
  const [route, setRoute] = useState('inicio') // 'inicio' | 'sobre' | 'config'
  const [feedbackOpen, setFeedbackOpen] = useState(false)

  const spanDays = useMemo(() => {
    const s = new Date(range.start)
    const e = new Date(range.end)
    return Math.round((e - s) / (1000 * 60 * 60 * 24)) + 1
  }, [range.start, range.end])

  return (
    <div className="h-full flex flex-col" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      <Topbar
        mode={mode}
        setMode={setMode}
        range={range}
        setCustom={setCustom}
        custom={custom}
        onFeedbackClick={() => setFeedbackOpen(true)}
        user={user}
        onLogout={logout}
      />
      <div className="divider-horizontal w-full" />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar active={route} onNavigate={setRoute} />
        <div className="divider-vertical" />

        {route === 'sobre' && (
          <main className="flex-1 overflow-auto p-6">
            <AboutPage onBack={() => setRoute('inicio')} />
          </main>
        )}

        {route === 'config' && (
          <main className="flex-1 overflow-auto p-6">
            <SettingsComingSoon onBack={() => setRoute('inicio')} />
          </main>
        )}

        {route === 'inicio' && (
          <main className="flex-1 overflow-auto p-6 space-y-6">
            {/* KPIs */}
            <section className="kpi-grid">
              <KPI title="RECEITA" value={loading ? '—' : formatBRLShort(data?.kpis?.receita)} loading={loading} icon="money" />
              <KPI title="RESERVAS" value={loading ? '—' : data?.kpis?.reservas} loading={loading} icon="bag" />
              <KPI title="DIÁRIAS" value={loading ? '—' : data?.kpis?.diarias} loading={loading} icon="moon" />
              <KPI title="CLICKS" value={loading ? '—' : data?.kpis?.clicks?.toLocaleString('pt-BR')} loading={loading} icon="click" />
              <KPI title="IMPRESSÕES" value={loading ? '—' : data?.kpis?.impressoes?.toLocaleString('pt-BR')} loading={loading} icon="eye" />
              <KPI title="CPC" value={loading ? '—' : `R$${(data?.kpis?.cpc || 0).toFixed(2).replace('.', ',')}`} loading={loading} icon="coin" />
              <KPI title="CUSTO" value={loading ? '—' : formatBRLShort(data?.kpis?.custo)} loading={loading} icon="cost" />
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

            <CampaignsTable />

            <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              <div className="lg:col-span-6 h-full"><NetworksBreakdown /></div>
              <div className="lg:col-span-6 h-full"><WelcomeCard /></div>
            </section>
          </main>
        )}
      </div>

      {/* Feedback Modal */}
      <FeedbackModal open={feedbackOpen} onClose={() => setFeedbackOpen(false)} />
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

function AppContent() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mb-4"></div>
          <p>Carregando...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Login />
  }

  return <Dashboard />
  return <Dashboard />
}
