from django.db import models
from clients.models import Cliente
import json

class Geometria(models.Model):
    id_geometria = models.AutoField(primary_key=True)  # PK personalizada según ERD
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='geometrias')
    nombre = models.CharField(max_length=200)
    geojson = models.JSONField(help_text="Geometría almacenada en formato GeoJSON")
    monitoreo_activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id_geometria}-{self.nombre} ({self.id_cliente.nombre})"

    @property
    def geojson_string(self):
        """Retorna el GeoJSON como string para usar en templates"""
        if self.geojson:
            return json.dumps(self.geojson)
        return '{}'

    @property
    def geometry_type(self):
        """Retorna el tipo de geometría (Point, Polygon, LineString, etc.)"""
        if self.geojson and 'type' in self.geojson:
            return self.geojson.get('type', 'Unknown')
        return 'Unknown'

    @property
    def coordinates_summary(self):
        """Retorna un resumen de las coordenadas para mostrar en listas"""
        if not self.geojson or 'coordinates' not in self.geojson:
            return "No coordinates"
        
        coords = self.geojson['coordinates']
        geometry_type = self.geometry_type
        
        if geometry_type == 'Point':
            return f"Lat: {coords[1]:.4f}, Lng: {coords[0]:.4f}"
        elif geometry_type == 'Polygon':
            if coords and len(coords[0]) > 0:
                num_points = len(coords[0]) - 1  # -1 porque el último punto es igual al primero
                return f"Polygon with {num_points} vertices"
        elif geometry_type == 'LineString':
            return f"Line with {len(coords)} points"
        elif geometry_type == 'MultiPoint':
            return f"MultiPoint with {len(coords)} points"
        elif geometry_type == 'MultiPolygon':
            return f"MultiPolygon with {len(coords)} polygons"
        elif geometry_type == 'MultiLineString':
            return f"MultiLineString with {len(coords)} lines"
        
        return f"{geometry_type} geometry"

    @property
    def bounds(self):
        """Calcula los bounds (límites) de la geometría para centrar el mapa"""
        if not self.geojson or 'coordinates' not in self.geojson:
            return None
        
        coords = self.geojson['coordinates']
        geometry_type = self.geometry_type
        
        def extract_coords(coord_array, all_coords=None):
            if all_coords is None:
                all_coords = []
            
            if isinstance(coord_array[0], (int, float)):
                # Es una coordenada individual [lng, lat]
                all_coords.append(coord_array)
            else:
                # Es un array de coordenadas, recursivamente extraer
                for item in coord_array:
                    extract_coords(item, all_coords)
            return all_coords
        
        try:
            all_coords = extract_coords(coords)
            if not all_coords:
                return None
            
            lngs = [coord[0] for coord in all_coords]
            lats = [coord[1] for coord in all_coords]
            
            return {
                'min_lng': min(lngs),
                'max_lng': max(lngs),
                'min_lat': min(lats),
                'max_lat': max(lats),
                'center_lng': (min(lngs) + max(lngs)) / 2,
                'center_lat': (min(lats) + max(lats)) / 2
            }
        except (IndexError, KeyError, TypeError):
            return None

    def clean(self):
        """Validación del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar que el GeoJSON tenga la estructura correcta
        if self.geojson:
            if not isinstance(self.geojson, dict):
                raise ValidationError("GeoJSON must be a valid JSON object")
            
            if 'type' not in self.geojson:
                raise ValidationError("GeoJSON must have a 'type' field")
            
            valid_types = ['Point', 'LineString', 'Polygon', 'MultiPoint', 
                          'MultiLineString', 'MultiPolygon', 'GeometryCollection']
            
            if self.geojson['type'] not in valid_types:
                raise ValidationError(f"Invalid geometry type. Must be one of: {', '.join(valid_types)}")
            
            if 'coordinates' not in self.geojson and self.geojson['type'] != 'GeometryCollection':
                raise ValidationError("GeoJSON must have 'coordinates' field")

    class Meta:
        verbose_name = "Geometría"
        verbose_name_plural = "Geometrías"
        ordering = ['-creado_en']