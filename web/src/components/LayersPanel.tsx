import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'; // Change from 'import type' to regular import
import { fetchLayers, mvtUrlFor, logout } from '../api'
import type { DbLayer, User } from '../types'

type Props = {
  map: maplibregl.Map | null
  user: User | null
  onLogout: () => void
  initialState?: Record<number, LayerState>
  onStateChange?: (s: Record<number, LayerState>) => void
  mapReady?: boolean
  onLayerSelect: (layerId: number | null) => void;
}

type LayerState = { enabled: boolean; visible: boolean }

function colorFor(id: number) {
  const h = (id * 57) % 360
  return `hsl(${h} 60% 55%)`
}

function ensureLayerAdded(map: maplibregl.Map, id: number) {
  const src = `src-${id}`
  if (!map.getSource(src)) {
    // Ensure the tile template remains unchanged, only remove ?token= if it exists
    const raw = mvtUrlFor(id)
    const tilesUrl = raw.replace(/([?&])token=[^&]*/g, '').replace(/[?&]$/, '')

    const beforeId = map.getLayer('labels') ? 'labels' : undefined

    map.addSource(src, { type: 'vector', tiles: [tilesUrl], minzoom: 0, maxzoom: 22 })

    // Polygons
    map.addLayer(
      {
        id: `lyr-${id}-fill`,
        type: 'fill',
        source: src,
        'source-layer': 'layer',
        filter: ['==', ['geometry-type'], 'Polygon'],
        paint: { 'fill-color': colorFor(id), 'fill-opacity': 0.35 }
      },
      beforeId
    )

    // Lines
    map.addLayer(
      {
        id: `lyr-${id}-line`,
        type: 'line',
        source: src,
        'source-layer': 'layer',
        filter: ['==', ['geometry-type'], 'LineString'],
        paint: { 'line-color': colorFor(id), 'line-width': 1 }
      },
      beforeId
    )

    // Points
    map.addLayer(
      {
        id: `lyr-${id}-circle`,
        type: 'circle',
        source: src,
        'source-layer': 'layer',
        filter: ['==', ['geometry-type'], 'Point'],
        paint: {
          'circle-radius': 5,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#000',
          'circle-color': colorFor(id)
        }
      },
      beforeId
    )
  }
}

function setLayerVisibility(map: maplibregl.Map, id: number, show: boolean) {
  for (const kind of ['fill','line','circle'] as const) {
    const lid = `lyr-${id}-${kind}`
    if (map.getLayer(lid)) map.setLayoutProperty(lid, 'visibility', show ? 'visible' : 'none')
  }
}

function removeLayer(map: maplibregl.Map, id: number) {
  for (const kind of ['fill','line','circle'] as const) {
    const lid = `lyr-${id}-${kind}`
    if (map.getLayer(lid)) map.removeLayer(lid)
  }
  const src = `src-${id}`
  if (map.getSource(src)) map.removeSource(src)
}

export default function LayersPanel({ map, user, onLogout, initialState, onStateChange, mapReady, onLayerSelect }: Props & { onLayerSelect: (layerId: number) => void }) {
  const [rows, setRows] = useState<DbLayer[]>([])
  const [err, setErr] = useState<string | null>(null)
  const [state, setState] = useState<Record<number, LayerState>>({})
  const [selectedLayer, setSelectedLayer] = useState<number | null>(null)

  useEffect(() => {
    let cancel = false
    fetchLayers().then(d=>{ if(!cancel) setRows(d) }).catch(e=>!cancel && setErr(String(e)))
    return () => { cancel = true }
  }, [])

  // Hydrate state only after the map style has loaded
  const hydratedRef = useRef(false)
  useEffect(() => {
    if (hydratedRef.current) return
    if (!map || !mapReady) return
    if (!rows.length) return
    hydratedRef.current = true

    const init = initialState ?? {}
    setState(init)
    for (const r of rows) {
      const st = init[r.id]
      if (st?.enabled) {
        ensureLayerAdded(map, r.id)
        setLayerVisibility(map, r.id, st.visible !== false)
      }
    }
  }, [map, mapReady, rows, initialState])

  // Pass changes to the parent component for saving map_state
  useEffect(() => { onStateChange?.(state) }, [state, onStateChange])

  const onClick = (e: maplibregl.MapMouseEvent & maplibregl.EventData) => {
    console.log("Map clicked at:", e.lngLat) // Debugging log
    if (!selectedLayer) {
      console.log("No layer selected") // Debugging log
      return
    }

    // Query features from the selected layer
    const features = map.queryRenderedFeatures(e.point, {
      layers: [`lyr-${selectedLayer}-fill`, `lyr-${selectedLayer}-line`, `lyr-${selectedLayer}-circle`]
    })

    console.log("Queried features:", features) // Debugging log

    if (features.length > 0) {
      const feature = features[0]
      const properties = feature.properties

      // Create a popup with feature properties
      // Refine popup styles to ensure text wraps properly and doesn't overflow
      const popup = new maplibregl.Popup({ closeOnClick: true })
        .setLngLat(e.lngLat)
        .setHTML(
          `<div style="max-width: 300px; max-height: 400px; overflow: auto; word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap;">
            <h4>Feature Properties</h4>
            <pre style="white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;">
              ${JSON.stringify(properties, null, 2)}
            </pre>
          </div>`
        )
        .addTo(map)
    }
  }

  const headerRight = (
    <div className="lp-user">
      {user ? <>
        <span title={user.email || user.username || ''}>👤 {user.email || user.username}</span>
        <button type="button" className="lp-btn lp-logout" onClick={async ()=>{
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
              // Highlight the selected layer row
              <tr
                key={r.id}
                className={`lp-row ${selectedLayer === r.id ? 'lp-row-active' : ''}`}
                title={r.description ?? ''}
                onClick={() => {
                  const isSelected = selectedLayer === r.id;
                  setSelectedLayer(isSelected ? null : r.id); // Toggle selection
                  onLayerSelect(isSelected ? null : r.id); // Notify parent
                }}
              >
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
                  <button type="button" className="lp-btn" title={st.visible ? 'Hide' : 'Show'}
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
  }, [rows, state, map, err, onLayerSelect, selectedLayer])

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
