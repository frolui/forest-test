import 'maplibre-gl/dist/maplibre-gl.css'
import './index.css'
import maplibregl from 'maplibre-gl'
import { useEffect, useRef, useState } from 'react'
import LayersPanel from './components/LayersPanel'
import LoginPage from './components/LoginPage'
import { me, saveMapState, getToken, API_BASE } from './api'
import type { User, MapState, LayerState } from './types'

const App = () => {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const [mapReady, setMapReady] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [authChecked, setAuthChecked] = useState(false)

  const [layerState, setLayerState] = useState<Record<number, LayerState>>({})
  const layerStateRef = useRef(layerState)
  useEffect(() => { layerStateRef.current = layerState }, [layerState])

  const hydratingRef = useRef(true)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const scheduleSave = () => {
    const m = mapRef.current
    if (!m || !user || hydratingRef.current) return
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(async () => {
      const s: MapState = {
        center: m.getCenter().toArray() as [number, number],
        zoom: m.getZoom(),
        bearing: m.getBearing(),
        pitch: m.getPitch(),
        layers: layerStateRef.current
      }
      try { await saveMapState(s) } catch {}
    }, 1000)
  }

  useEffect(() => {
    me().then(setUser).finally(() => setAuthChecked(true))
  }, [])

  useEffect(() => {
    if (!user) return
    if (!containerRef.current) return
    if (mapRef.current) return

    const style: maplibregl.StyleSpecification = {
      version: 8,
      sources: {
        'carto-positron-base': {
          type: 'raster',
          tiles: [
            'https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png',
            'https://b.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png',
            'https://c.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png',
            'https://d.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png'
          ],
          tileSize: 256,
          attribution: '© OpenStreetMap contributors © CARTO'
        },
        'carto-positron-labels': {
          type: 'raster',
          tiles: [
            'https://a.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png',
            'https://b.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png',
            'https://c.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png',
            'https://d.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png'
          ],
          tileSize: 256
        }
      },
      layers: [
        { id: 'base', type: 'raster', source: 'carto-positron-base' },
        { id: 'labels', type: 'raster', source: 'carto-positron-labels' }
      ]
    }

    const m = new maplibregl.Map({
      container: containerRef.current,
      style,
      center: [2.2137, 46.2276],
      zoom: 6,
      transformRequest: (url) => {
        const t = getToken()
        if (t && (url.startsWith(API_BASE) || url.includes('/tiles/'))) {
          return { url, headers: { Authorization: `Bearer ${t}` } }
        }
        return { url }
      }
    })
    m.addControl(new maplibregl.NavigationControl(), 'top-right')
    mapRef.current = m

    m.on('load', () => {
      hydratingRef.current = true
      const st = user.map_state
      if (st?.bounds) {
        m.fitBounds(st.bounds, { padding: 24, maxZoom: st.zoom ?? 22 })
      } else {
        if (st?.center) m.setCenter(st.center)
        if (typeof st?.zoom === 'number') m.setZoom(st.zoom)
        if (typeof st?.bearing === 'number') m.setBearing(st.bearing)
        if (typeof st?.pitch === 'number') m.setPitch(st.pitch)
      }
      m.once('idle', () => { hydratingRef.current = false; setMapReady(true) })
    })

    const onMoveEnd = () => scheduleSave()
    m.on('moveend', onMoveEnd)
    m.on('rotateend', onMoveEnd)
    m.on('pitchend', onMoveEnd)

    return () => { m.remove(); mapRef.current = null; setMapReady(false) }
  }, [user])

  useEffect(() => { scheduleSave() }, [layerState]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!authChecked) return null
  if (!user) return <LoginPage onSuccess={async () => { const u = await me(); setUser(u) }} />

  return (
    <div className="map">
      <LayersPanel
        map={mapRef.current}
        mapReady={mapReady}
        user={user}
        onLogout={() => setUser(null)}
        initialState={user.map_state?.layers ?? {}}
        onStateChange={(s) => setLayerState(s)}
      />
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  )
}

export default App
