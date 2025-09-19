import React, { useEffect, useMemo, useState } from 'react'
import './App.css'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid, BarChart, Bar } from 'recharts'

const API_BASE = (import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL)

function formatCurrency(n) {
  return n?.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function addDays(date, days) {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

function formatISO(d) {
  return d.toISOString().slice(0,10)
}

function useDateRange(initial='7d'){
  const [mode, setMode] = useState(initial)
  const [custom, setCustom] = useState({start: '', end: ''})

  const range = useMemo(()=>{
    const now = new Date()
    if(mode==='7d' || mode==='30d' || mode==='90d'){
      const days = mode==='7d'?7:mode==='30d'?30:90
      const end = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const start = addDays(end, -(days-1))
      return { start: formatISO(start), end: formatISO(end) }
    }
    if(custom.start && custom.end) return custom
    const end = formatISO(now)
    const start = formatISO(addDays(now,-6))
    return { start, end }
  },[mode, custom])

  return { mode, setMode, custom, setCustom, range }
}

async function api(path, params){
  const baseUrl = API_BASE
  if(!baseUrl){ throw new Error('Backend URL ausente. Defina REACT_APP_BACKEND_URL no .env do frontend.') }
  const fullPath = baseUrl + path
  const url = new URL(fullPath, window.location.origin)
  if(params){ Object.entries(params).forEach(([k,v])=> url.searchParams.set(k, v)) }
  const res = await fetch(url.toString())
  if(!res.ok) throw new Error('API error')
  return res.json()
}

function Topbar({mode, setMode, range, setCustom}){
  const [q, setQ] = useState('')
  return (
    <div className="w-full flex items-center justify-between px-6 py-3 bg-surface border-b border-gray-200">
      <div className="flex items-center gap-3">
        <img src="/logo-calma-data.png" alt="Calma Data" className="h-8" />
        <div className="text-darkgray font-heading text-lg">Dashboard</div>
      </div>
      <div className="flex-1 max-w-xl mx-6">
        <input aria-label="buscar" placeholder="Buscar..." value={q} onChange={e=>setQ(e.target.value)} className="w-full px-3 py-2 rounded-md border border-gray-200 shadow-softer bg-white"/>
      </div>
      <div className="flex items-center gap-2">
        {['7d','30d','90d','custom'].map(key=> (
          <button key={key} className={`chip ${mode===key?'active':''}`} onClick={()=>setMode(key)} aria-label={`intervalo ${key}`}>{key.toUpperCase()}</button>
        ))}
        {mode==='custom' && (
          <div className="flex items-center gap-2">
            <input type="date" value={range.start} onChange={e=>setCustom(s=>({...s, start:e.target.value}))} className="px-3 py-2 rounded-md border border-gray-200"/>
            <input type="date" value={range.end} onChange={e=>setCustom(s=>({...s, end:e.target.value}))} className="px-3 py-2 rounded-md border border-gray-200"/>
          </div>
        )}
      </div>
    </div>
  )
}

function Sidebar(){
  const [active, setActive] = useState('inicio')
  const items = [
    {id:'inicio', label:'Início'},
    {id:'sobre', label:'Sobre'},
    {id:'config', label:'Configurações'}
  ]
  return (
    <aside className="w-60 shrink-0 h-full bg-white border-r border-gray-100 p-4">
      {items.map(it=> (
        <button key={it.id} className={`sidebar-link ${active===it.id?'active':''}`} onClick={()=>setActive(it.id)} aria-label={it.label}>
          <span className="w-2 h-2 rounded-full bg-primary inline-block"/> {it.label}
        </button>
      ))}
    </aside>
  )
}

function KPI({title, value}){
  return (
    <div className="kpi">
      <div className="kpi-title">{title}</div>
      <div className="kpi-value">{value}</div>
    </div>
  )
}

function useDashboardData(range){
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState({})
  useEffect(()=>{
    let cancelled=false
    async function load(){
      try{
        setLoading(true)
        const params = { start: range.start, end: range.end }
        const [kpis, acq, revUH, stacked, heat, table] = await Promise.all([
          api('/kpis', params),
          api('/acquisition-by-channel', { ...params, metric: 'users' }),
          api('/revenue-by-uh', params),
          api('/sales-uh-stacked', params),
          api('/campaign-conversion-heatmap', params),
          api('/performance-table', params)
        ])
        if(!cancelled) setData({kpis, acq, revUH, stacked, heat, table})
      } finally {
        if(!cancelled) setLoading(false)
      }
    }
    load()
    return ()=>{ cancelled=true }
  },[range.start, range.end])
  return { loading, data }
}

function AcquisitionLine({series}){
  const chartData = useMemo(()=>{
    if(!series?.points) return []
    return series.points.map(p=> ({
      date: p.date,
      ...p.values
    }))
  },[series])
  return (
    <div className="card">
      <div className="card-header">Aquisição por canal (Users)</div>
      <div className="card-body" style={{height:320}}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" hide={false} tick={{fontSize:12}}/>
            <YAxis tick={{fontSize:12}}/>
            <Tooltip/>
            <Legend/>
            {Object.keys(chartData[0]||{}).filter(k=>k!=='date').map((k,i)=> (
              <Line key={k} type="monotone" dataKey={k} strokeWidth={2} dot={{r:2}} stroke={["#2A8C99","#A8C6A6","#6D6A69","#C4A981","#3b82f6","#f59e0b","#ef4444"][i%7]} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function RevenueByUH({data}){
  const chartData = useMemo(()=>{
    if(!data?.points) return []
    return data.points.map(p=> ({ date: p.date, ...p.values }))
  },[data])
  return (
    <div className="card">
      <div className="card-header">Receita por tipo (UH)</div>
      <div className="card-body" style={{height:320}}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{fontSize:12}}/>
            <YAxis tickFormatter={(v)=>formatCurrency(v)}/>
            <Tooltip formatter={(v)=>formatCurrency(v)}/>
            <Legend/>
            {Object.keys(chartData[0]||{}).filter(k=>k!=='date').map((k,i)=> (
              <Line key={k} type="monotone" dataKey={k} strokeWidth={2} dot={false} stroke={["#2A8C99","#A8C6A6","#6D6A69","#C4A981"][i%4]} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function SalesUHStacked({data}){
  const chartData = useMemo(()=> data?.points?.map(p=> ({label:p.label, ...p.values}))||[],[data])
  const keys = useMemo(()=> data?.series_labels || [], [data])
  return (
    <div className="card">
      <div className="card-header">Vendas UH por tipo (empilhado)</div>
      <div className="card-body" style={{height:320}}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label"/>
            <YAxis/>
            <Tooltip/>
            <Legend/>
            {keys.map((k,i)=> (
              <Bar key={k} dataKey={k} stackId="a" fill={["#2A8C99","#A8C6A6","#6D6A69","#C4A981"][i%4]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function Heatmap({data}){
  const cells = data?.cells || []
  const grid = Array.from({length:7}, (_,d)=> Array.from({length:24},(_,h)=> cells.find(c=>c.day===d && c.hour===h)?.value || 0))
  const max = Math.max(1, ...cells.map(c=>c.value))
  return (
    <div className="card">
      <div className="card-header">Heatmap de Conversão (dia x hora)</div>
      <div className="card-body overflow-auto">
        <div className="grid" style={{gridTemplateColumns: 'repeat(24, 28px)'}}>
          {grid.map((row,ri)=> (
            <div key={ri} className="flex gap-1 mb-1 items-center">
              <div className="w-10 text-xs text-elegant">{['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'][ri]}</div>
              {row.map((v,ci)=> (
                <div key={ci} className="w-6 h-6 rounded" title={`h${ci}: ${v}`} style={{backgroundColor:`rgba(42,140,153,${v/max})`}}></div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function PerfTable({rows}){
  return (
    <div className="card">
      <div className="card-header">Performance por Canal</div>
      <div className="card-body overflow-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-elegant">
              {['Canal','Cliques','Impressões','CTR','CPC','Custo','Conversões','Receita','ROAS'].map(h=> <th key={h} className="py-2 pr-4">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows?.map((r,i)=> (
              <tr key={i} className="border-t border-gray-100">
                <td className="py-2 pr-4">{r.name}</td>
                <td className="py-2 pr-4">{r.clicks}</td>
                <td className="py-2 pr-4">{r.impressoes}</td>
                <td className="py-2 pr-4">{(r.ctr*100).toFixed(2)}%</td>
                <td className="py-2 pr-4">{formatCurrency(r.cpc)}</td>
                <td className="py-2 pr-4">{formatCurrency(r.custo)}</td>
                <td className="py-2 pr-4">{r.conversoes}</td>
                <td className="py-2 pr-4">{formatCurrency(r.receita)}</td>
                <td className="py-2 pr-4">{r.roas}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function App(){
  const { mode, setMode, custom, setCustom, range } = useDateRange('7d')
  const { loading, data } = useDashboardData(range)

  return (
    <div className="h-full flex flex-col" style={{fontFamily:'Radley, serif'}}>
      <Topbar mode={mode} setMode={setMode} range={range} setCustom={setCustom} />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar/>
        <main className="flex-1 overflow-auto p-6 space-y-6">
          {/* KPI Grid */}
          <section className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-7 gap-4">
            <KPI title="Receita (R$)" value={loading? '—' : formatCurrency(data?.kpis?.receita)} />
            <KPI title="Reservas" value={loading? '—' : data?.kpis?.reservas} />
            <KPI title="Diárias" value={loading? '—' : data?.kpis?.diarias} />
            <KPI title="Clicks" value={loading? '—' : data?.kpis?.clicks} />
            <KPI title="Impressões" value={loading? '—' : data?.kpis?.impressoes} />
            <KPI title="CPC" value={loading? '—' : formatCurrency(data?.kpis?.cpc)} />
            <KPI title="Custo de Campanhas" value={loading? '—' : formatCurrency(data?.kpis?.custo)} />
          </section>

          {/* Charts Grid */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AcquisitionLine series={data?.acq}/>
            <RevenueByUH data={data?.revUH}/>
            <SalesUHStacked data={data?.stacked}/>
            <Heatmap data={data?.heat}/>
          </section>

          <PerfTable rows={data?.table?.rows}/>
        </main>
      </div>
    </div>
  )
}