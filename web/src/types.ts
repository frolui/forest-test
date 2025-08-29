export interface User {
  id: number;
  email: string;
  map_state?: any | null;
}

export interface DbLayer {
  id: number;
  name: string;
  description?: string | null;
  created_at?: string | null;
  bbox?: GeoJSON.Polygon | GeoJSON.MultiPolygon | null;
}
