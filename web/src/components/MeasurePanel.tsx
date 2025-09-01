// components/MeasurePanel.tsx
import { useEffect, useMemo, useRef, useState } from 'react'
import type maplibregl from 'maplibre-gl'

type Props = { map: maplibregl.Map | null; mapReady?: boolean }

type Mode = 'none' | 'length' | 'area'

const R = 6371008.8 // Earth radius (m)

function toMercMeters([lon, lat]: [number, number]) {
  const x = (lon * Math.PI) / 180
  const y = (lat * Math.PI) / 180
  const mx = R * x
  const my = R * Math.log(Math.tan(Math.PI / 4 + y / 2))
  return [mx, my] as [number, number]
}
function haversine(a: [number, number], b: [number, number]) {
  const [lon1, lat1] = a.map(v => (v * Math.PI) / 180)
  const [lon2, lat2] = b.map(v => (v * Math.PI) / 180)
  const dlon = lon2 - lon1
  const dlat = lat2 - lat1
  const h =
    Math.sin(dlat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h)) // meters
}
function polyArea3857(coords: [number, number][]) {
  if (coords.length < 3) return 0
  const pts = coords.map(toMercMeters)
  let s = 0
  for (let i = 0; i < pts.length; i++) {
    const [x1, y1] = pts[i]
    const [x2, y2] = pts[(i + 1) % pts.length]
    s += x1 * y2 - x2 * y1
  }
  return Math.abs(s) / 2 // m^2
}
function fmtLen(m: number) {
  return m < 1000 ? `${m.toFixed(1)} m` : `${(m / 1000).toFixed(2)} km`
}
function fmtArea(m2: number) {
  return m2 < 1e6 ? `${m2.toFixed(0)} m²` : `${(m2 / 1e6).toFixed(2)} km²`
}

export default function MeasurePanel({ map, mapReady }: Props) {
  const [mode, setMode] = useState<Mode>('none')
  const [coords, setCoords] = useState<[number, number][]>([])
  const finishedRef = useRef(false)

  // add source/layers once
  useEffect(() => {
    if (!map || !mapReady) return
    if (map.getSource('measure-src')) return
    map.addSource('measure-src', {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: [] }
    })
    const beforeId = map.getLayer('labels') ? 'labels' : undefined
    map.addLayer(
      { id: 'measure-fill', type: 'fill', source: 'measure-src',
        paint: { 'fill-color': '#2d6cdf', 'fill-opacity': 0.2 } },
      beforeId
    )
    map.addLayer(
      { id: 'measure-line', type: 'line', source: 'measure-src',
        paint: { 'line-color': '#2d6cdf', 'line-width': 2 } },
      beforeId
    )
    map.addLayer(
      { id: 'measure-pts', type: 'circle', source: 'measure-src',
        paint: { 'circle-radius': 4, 'circle-color': '#2d6cdf', 'circle-stroke-width': 1, 'circle-stroke-color': '#fff' } },
      beforeId
    )
  }, [map, mapReady])

  // update drawing
  useEffect(() => {
    if (!map) return
    const fc: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }
    if (mode === 'length' && coords.length >= 2) {
      fc.features.push({ type: 'Feature', geometry: { type: 'LineString', coordinates: coords }, properties: {} })
    }
    if (mode === 'area' && coords.length >= 3) {
      fc.features.push({ type: 'Feature', geometry: { type: 'Polygon', coordinates: [[...coords, coords[0]]] }, properties: {} })
    }
    // points
    for (const c of coords) {
      fc.features.push({ type: 'Feature', geometry: { type: 'Point', coordinates: c }, properties: {} })
    }
    const src = map.getSource('measure-src') as maplibregl.GeoJSONSource
    src && src.setData(fc)
  }, [map, mode, coords])

  // click handling
  useEffect(() => {
    if (!map) return
    if (mode === 'none') return
    const onClick = (e: maplibregl.MapMouseEvent & maplibregl.EventData) => {
      if (finishedRef.current) return
      setCoords(prev => [...prev, [e.lngLat.lng, e.lngLat.lat]])
    }
    map.on('click', onClick)
    map.doubleClickZoom.disable()
    return () => {
      map.off('click', onClick)
      map.doubleClickZoom.enable()
    }
  }, [map, mode])

  const length = useMemo(() => {
    if (mode !== 'length' || coords.length < 2) return 0
    let s = 0
    for (let i = 0; i < coords.length - 1; i++) s += haversine(coords[i], coords[i + 1])
    return s
  }, [mode, coords])

  const area = useMemo(() => {
    if (mode !== 'area' || coords.length < 3) return 0
    return polyArea3857(coords)
  }, [mode, coords])

  const start = (m: Mode) => {
    setMode(m)
    setCoords([])
    finishedRef.current = false
  }
  const finish = () => { finishedRef.current = true }
  const clear = () => {
    setMode('none'); setCoords([]); finishedRef.current = false
    if (map) {
      const src = map.getSource('measure-src') as maplibregl.GeoJSONSource
      src && src.setData({ type: 'FeatureCollection', features: [] })
    }
  }

  return (
    <div className="tools-panel">
      <div className="tp-header"><strong>Tools</strong></div>
      <div className="tp-row">
        <button className={`tp-btn ${mode==='length'?'active':''}`} onClick={()=>start('length')} title="Measure length">📏 Length</button>
        <button className={`tp-btn ${mode==='area'?'active':''}`} onClick={()=>start('area')} title="Measure area">📐 Area</button>
      </div>
      <div className="tp-row">
        <button className="tp-btn" onClick={finish} disabled={mode==='none'}>Finish</button>
        <button className="tp-btn" onClick={clear} disabled={mode==='none' && coords.length===0}>Clear</button>
      </div>
      <div className="tp-result">
        {mode==='length' && (coords.length>=2 ? <>Length: <b>{fmtLen(length)}</b></> : <span>Click map to add points</span>)}
        {mode==='area'   && (coords.length>=3 ? <>Area: <b>{fmtArea(area)}</b></> : <span>Click map to add vertices</span>)}
        {mode==='none'   && <span>Choose a tool</span>}
      </div>
      <div className="tp-row">
        <button className="tp-btn primary" onClick={()=>console.log('Get analysis clicked')}>Get analysis</button>
      </div>
    </div>
  )
}
