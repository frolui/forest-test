export interface LayerState {
  enabled: boolean;
  visible: boolean;
}

export interface MapState {
  center?: [number, number]; // [lng, lat]
  zoom?: number;
  bearing?: number;
  pitch?: number;
  bounds?: [[number, number], [number, number]];
  layers?: Record<number, LayerState>;
}

export interface User {
  id: number;
  email?: string | null;
  username?: string | null;
  map_state?: MapState | null;
}

export interface DbLayer {
  id: number;
  name: string;
  description?: string | null;
  created_at?: string | null;
  bbox?: GeoJSON.Polygon | GeoJSON.MultiPolygon | null;
}
