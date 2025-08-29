import 'maplibre-gl/dist/maplibre-gl.css'
import './index.css'
import maplibregl from 'maplibre-gl'
import { useEffect, useRef, useState } from 'react'
import LayersPanel from './components/LayersPanel'
import LoginPage from './components/LoginPage'
import { me } from './api'
import type { User } from './types'

const App = () => {
  const mapRef = useRef<HTMLDivElement>(null)
  const [map, setMap] = useState<maplibregl.Map | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [authChecked, setAuthChecked] = useState(false)

  useEffect(() => {  // проверяем сессию при загрузке
    me().then(u => setUser(u)).finally(()=>setAuthChecked(true))
  }, [])

  useEffect(() => {
    if (!mapRef.current) return
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

    const m = new maplibregl.Map({ container: mapRef.current, style, center: [2.2137, 46.2276], zoom: 6 })
    m.addControl(new maplibregl.NavigationControl(), 'top-right')
    setMap(m)
    return () => m.remove()
  }, [])

  if (!authChecked) return null

  if (!user) {
    return <LoginPage onSuccess={async ()=>{ const u = await me(); setUser(u) }} />
  }

  return (
    <div className="map">
      <LayersPanel map={map} user={user} onLogout={()=>setUser(null)} />
      <div ref={mapRef} style={{ width:'100%', height:'100%' }} />
    </div>
  )
}

export default App
