import { useEffect, useMemo, useState } from 'react'
import type maplibregl from 'maplibre-gl'
import { fetchLayers, mvtUrlFor, logout } from '../api'
import type { DbLayer, User } from '../types'

type Props = { map: maplibregl.Map | null, user: User | null, onLogout: () => void }

type LayerState = { enabled: boolean; visible: boolean }

function colorFor(id: number) {
  const h = (id * 57) % 360
  return `hsl(${h} 60% 55%)`
}
function ensureLayerAdded(map: maplibregl.Map, id: number) {
  const src = `src-${id}`
  if (!map.getSource(src)) {
    map.addSource(src, { type: 'vector', tiles: [mvtUrlFor(id)], minzoom: 0, maxzoom: 22 })
    map.addLayer({ id: `lyr-${id}-fill`, type: 'fill', source: src, 'source-layer': 'layer',
      paint: { 'fill-color': colorFor(id), 'fill-opacity': 0.35 } })
    map.addLayer({ id: `lyr-${id}-line`, type: 'line', source: src, 'source-layer': 'layer',
      paint: { 'line-color': colorFor(id), 'line-width': 1 } })
  }
}
function setLayerVisibility(map: maplibregl.Map, id: number, show: boolean) {
  for (const kind of ['fill','line'] as const) {
    const lid = `lyr-${id}-${kind}`
    if (map.getLayer(lid)) map.setLayoutProperty(lid, 'visibility', show ? 'visible' : 'none')
  }
}
function removeLayer(map: maplibregl.Map, id: number) {
  for (const kind of ['fill','line'] as const) {
    const lid = `lyr-${id}-${kind}`; if (map.getLayer(lid)) map.removeLayer(lid)
  }
  const src = `src-${id}`; if (map.getSource(src)) map.removeSource(src)
}

export default function LayersPanel({ map, user, onLogout }: Props) {
  const [rows, setRows] = useState<DbLayer[]>([])
  const [err, setErr] = useState<string | null>(null)
  const [state, setState] = useState<Record<number, LayerState>>({})

  useEffect(() => {
    let cancel = false
    fetchLayers().then(d=>{ if(!cancel) setRows(d) }).catch(e=>!cancel && setErr(String(e)))
    return () => { cancel = true }
  }, [])

  const headerRight = (
    <div className="lp-user">
      {user ? <>
        <span title={user.email}>👤 {user.email}</span>
        <button className="lp-btn lp-logout" onClick={async ()=>{
          await logout(); onLogout();
        }}>Logout</button>
      </> : <span className="lp-muted">Not signed in</span>}
    </div>
  )

  const table = useMemo(() => {
    if (err) return <div className="lp-error">{err}</div>
    if (!rows.length) return <div className="lp-muted">No layers</div>
    return (
      <table className="lp-table">
        <thead>
          <tr><th style={{width:56}}>Enable</th><th>Name</th><th style={{width:70}}>Show</th></tr>
        </thead>
        <tbody>
          {rows.map(r => {
            const st = state[r.id] ?? { enabled: false, visible: true }
            return (
              <tr key={r.id} className="lp-row" title={r.description ?? ''}>
                <td>
                  <input type="checkbox" checked={st.enabled}
                    onChange={()=>{
                      if (!map) return
                      setState(prev=>{
                        const cur = prev[r.id] ?? { enabled:false, visible:true }
                        const next = { ...cur, enabled: !cur.enabled }
                        if (next.enabled) { ensureLayerAdded(map, r.id); setLayerVisibility(map, r.id, cur.visible) }
                        else { removeLayer(map, r.id) }
                        return { ...prev, [r.id]: next }
                      })
                    }}/>
                </td>
                <td><span className="lp-name" style={{color: st.enabled ? colorFor(r.id) : '#333'}}>{r.name}</span></td>
                <td>
                  <button className="lp-btn" title={st.visible ? 'Hide' : 'Show'}
                    disabled={!st.enabled || !map}
                    onClick={()=>{
                      if (!map) return
                      setState(prev=>{
                        const cur = prev[r.id] ?? { enabled:false, visible:true }
                        const next = { ...cur, visible: !cur.visible }
                        setLayerVisibility(map, r.id, next.visible)
                        return { ...prev, [r.id]: next }
                      })
                    }}>
                    {st.visible ? '👁️' : '🚫'}
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    )
  }, [rows, state, map, err])

  return (
    <div className="lp-panel">
      <div className="lp-header">
        <strong>Layers</strong>
        <span className="lp-spacer" />
        {headerRight}
      </div>
      {table}
    </div>
  )
}
