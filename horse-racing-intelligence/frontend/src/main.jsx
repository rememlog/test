import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Activity, Network, RefreshCw, Server, TrendingUp} from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App(){
  const [race,setRace]=useState(null);
  const [selected,setSelected]=useState(null);
  const [graph,setGraph]=useState(null);
  const [mode,setMode]=useState('demo');
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(false);
  const [filters,setFilters]=useState({meet:'1', rc_date:'', rc_no:''});

  const loadDemo=async()=>{
    setLoading(true); setError('');
    try{
      const r=await fetch(`${API}/api/races/demo`); const d=await r.json();
      setRace(d); setMode('demo'); setSelected(d.horses[0]);
    }finally{setLoading(false);}
  };
  const loadKra=async(force=false)=>{
    setLoading(true); setError('');
    const q=new URLSearchParams({meet:filters.meet});
    if(filters.rc_date) q.set('rc_date',filters.rc_date.replaceAll('-',''));
    if(filters.rc_no) q.set('rc_no',filters.rc_no);
    if(force) q.set('force_refresh','true');
    try{
      const r=await fetch(`${API}/api/kra/races/analysis?${q}`);
      const d=await r.json();
      if(!r.ok) throw new Error(d.detail || 'KRA API request failed');
      setRace(d); setMode('kra'); setSelected(d.horses[0]);
    }catch(e){setError(e.message);}
    finally{setLoading(false);}
  };
  useEffect(()=>{loadDemo();},[]);
  useEffect(()=>{if(selected) fetch(`${API}/api/horses/${encodeURIComponent(selected.horse_id)}/graph`).then(r=>r.json()).then(setGraph).catch(()=>setGraph(null));},[selected]);

  if(!race) return <div className="loading">데이터 로딩 중...</div>;
  return <main>
    <header><div><span className="eyebrow">HORSE RACING INTELLIGENCE</span><h1>{race.track} {race.race_no ? `${race.race_no}R` : ''} · {race.distance_m || '-'}m</h1><p>KRA 공개 출전표 → Redis 캐시 → Neo4j 관계 그래프 → baseline 확률 분석</p></div><div className={`status ${mode==='kra'?'live':''}`}><Activity size={16}/> {mode==='kra'?'KRA DATA':'DEMO'}</div></header>

    <section className="controls panel">
      <label>경마장<select value={filters.meet} onChange={e=>setFilters({...filters,meet:e.target.value})}><option value="1">서울</option><option value="2">제주</option><option value="3">부산경남</option><option value="4">영천</option></select></label>
      <label>경주일<input type="date" value={filters.rc_date} onChange={e=>setFilters({...filters,rc_date:e.target.value})}/></label>
      <label>경주번호<input type="number" min="1" max="20" placeholder="예: 7" value={filters.rc_no} onChange={e=>setFilters({...filters,rc_no:e.target.value})}/></label>
      <button onClick={()=>loadKra(false)} disabled={loading}><Server size={16}/> KRA 조회</button>
      <button className="secondary" onClick={()=>loadKra(true)} disabled={loading}><RefreshCw size={16}/> 강제 새로고침</button>
      <button className="ghost" onClick={loadDemo}>Demo</button>
      {error && <div className="error">{error}</div>}
    </section>

    <section className="metrics">
      <Card icon={<TrendingUp/>} label="Top baseline probability" value={`${(race.horses[0].model_probability*100).toFixed(1)}%`} sub={race.horses[0].horse_name}/>
      <Card icon={<Network/>} label="Graph entities" value={graph?.nodes?.length ?? '-'} sub="selected profile"/>
      <Card icon={<Activity/>} label="Data source" value={mode==='kra'?'KRA':'DEMO'} sub={race.race_date || 'local dataset'}/>
    </section>

    <section className="grid">
      <div className="panel"><h2>Baseline Ranking</h2><div className="table">
        <div className="row head"><span>#</span><span>Horse</span><span>Model</span><span>Market</span><span>Gap</span></div>
        {race.horses.map((h,i)=><button className={`row ${selected?.horse_id===h.horse_id?'active':''}`} key={h.horse_id} onClick={()=>setSelected(h)}><span>{i+1}</span><span><b>{h.horse_name}</b><small>{h.jockey || '-'} · {h.trainer || '-'}</small></span><span>{(h.model_probability*100).toFixed(1)}%</span><span>{h.market_probability==null?'—':`${(h.market_probability*100).toFixed(1)}%`}</span><span className={(h.value_gap??0)>0?'positive':'negative'}>{h.value_gap==null?'—':`${h.value_gap>0?'+':''}${(h.value_gap*100).toFixed(1)}%p`}</span></button>)}
      </div><small className="hint">KRA 출전표에는 사전 시장 배당이 포함되지 않아 실제 데이터 모드에서는 Market/Gap을 비워둡니다.</small></div>
      <div className="panel detail"><h2>{selected.horse_name}</h2><div className="score">{selected.score}<small>/100 baseline feature score</small></div><h3>근거</h3><ul>{selected.reasons.map(r=><li key={r}>{r}</li>)}</ul><h3>Relationship graph</h3><div className="graph">{graph?.nodes?.map((n,i)=><div className={`node n${i}`} key={n.id}><b>{n.label}</b><small>{n.type}</small></div>)}</div></div>
    </section>
    <footer>Research/analytics MVP · 확률은 학습된 수익예측 모델이 아닌 baseline score입니다.</footer>
  </main>
}
function Card({icon,label,value,sub}){return <div className="card"><div className="icon">{icon}</div><div><small>{label}</small><strong>{value}</strong><span>{sub}</span></div></div>}
createRoot(document.getElementById('root')).render(<App/>);
