"""
Utility Routes
CRUD operations for utilities
"""

import csv
import copy
import io
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
import zipfile
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Response
from sqlalchemy.orm import Session
from shapely import wkb
from shapely.geometry import mapping, shape
from app.database.session import get_db
from app.models import Utility, UtilityInfrastructureLayer, UtilityServiceArea, DMA
from app.schemas.user import (
    UtilityCreate,
    UtilityUpdate,
    UtilityResponse,
    UtilityListResponse,
    UtilityPublicContactResponse,
    PipeNetworkIngestSummary,
    UtilityInfrastructureAssetResponse,
    UtilityInfrastructureUploadResponse,
    UtilityServiceAreaCreate,
    UtilityServiceAreaResponse,
)
from app.security.dependencies import get_current_user, require_admin, require_utility_manager, CurrentUser
from app.services.hierarchy import (
    find_nearest_dma_within_utility,
    find_nearest_utility,
    find_utility_by_region_name,
    resolve_region_name_hint,
)

utilities_router = APIRouter(prefix="/api/utilities", tags=["utilities"])

MAX_PIPE_NETWORK_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_PIPE_NETWORK_EXTENSIONS = {
    ".gpkg",
    ".shp",
    ".geojson",
    ".json",
    ".kml",
    ".kmz",
    ".zip",
    ".csv",
    ".txt",
}

PIPE_NETWORK_REQUIRED_NUMERIC_COLUMNS = (
    "intdiammm",
    "nomdiaminc",
    "diameter",
    "diam_mm",
    "diameter_mm",
    "diameter_m",
    "diameter_in",
)

PIPE_NETWORK_REQUIRED_TEXT_COLUMNS = {
    "material": ("material", "pipe_material"),
    "condition": ("condition", "status_condition", "pipe_condition"),
    "location": ("location", "zonelocati", "zone", "location_name", "address"),
}

_infrastructure_geojson_cache: dict[tuple[Any, ...], dict[str, Any]] = {}

UTILITY_INFRASTRUCTURE_ASSETS: dict[str, dict[str, Any]] = {
    "pipe_network": {
        "label": "Pipe network",
        "geometry_types": {"LineString", "MultiLineString"},
    },
    "valves": {
        "label": "Valves",
        "geometry_types": {"Point", "MultiPoint"},
    },
    "water_sources": {
        "label": "Water sources",
        "geometry_types": {"Point", "MultiPoint"},
    },
    "storage_facilities": {
        "label": "Storage facilities",
        "geometry_types": {"Point", "MultiPoint"},
    },
    "bulk_meters": {
        "label": "Bulk meters",
        "geometry_types": {"Point", "MultiPoint"},
    },
}


def _resolve_current_user_utility_id(current_user: CurrentUser, db: Session) -> Optional[str]:
    if current_user.user_type == "utility_manager":
        return current_user.utility_id

    if current_user.user_type in {"dma_manager", "engineer"} and current_user.dma_id:
        dma = db.query(DMA).filter(DMA.id == current_user.dma_id).first()
        return dma.utility_id if dma else None

    return None


def _ensure_utility_access(utility: Utility, current_user: CurrentUser, db: Session) -> None:
    if current_user.user_type == "user":
        return

    if _resolve_current_user_utility_id(current_user, db) == utility.id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this utility",
    )


def _asset_label(asset_type: str) -> str:
    return str(UTILITY_INFRASTRUCTURE_ASSETS.get(asset_type, {}).get("label") or asset_type.replace("_", " ").title())


def _build_infrastructure_asset_response(layer: UtilityInfrastructureLayer) -> UtilityInfrastructureAssetResponse:
    return UtilityInfrastructureAssetResponse(
        asset_type=layer.asset_type,
        label=_asset_label(layer.asset_type),
        file_name=layer.file_name,
        file_size=layer.file_size,
        mime_type=layer.mime_type,
        feature_count=layer.feature_count or 0,
        download_url=f"/api/utilities/{layer.utility_id}/infrastructure/{layer.asset_type}/download",
        preview_url=f"/api/utilities/{layer.utility_id}/infrastructure/{layer.asset_type}/geojson",
        uploaded_at=layer.updated_at,
    )


def _build_service_area_response(service_area: UtilityServiceArea) -> UtilityServiceAreaResponse:
    return UtilityServiceAreaResponse(
        id=service_area.id,
        utility_id=service_area.utility_id,
        category=service_area.category.value if hasattr(service_area.category, "value") else service_area.category,
        name=service_area.name,
        region_name=service_area.region_name,
        admin_area_id=service_area.admin_area_id,
        created_at=service_area.created_at,
        updated_at=service_area.updated_at,
    )


def _replace_utility_service_areas(
    utility: Utility,
    service_areas: Optional[List[UtilityServiceAreaCreate]],
) -> None:
    if service_areas is None:
        return

    utility.service_areas.clear()
    seen: set[tuple[str, str, str]] = set()
    for area in service_areas:
        category = area.category
        name = area.name.strip()
        region_name = (area.region_name or utility.region_name or "").strip() or None
        key = (category, name.casefold(), (region_name or "").casefold())
        if key in seen:
            continue
        seen.add(key)
        utility.service_areas.append(
            UtilityServiceArea(
                category=category,
                name=name,
                region_name=region_name,
                admin_area_id=area.admin_area_id,
            )
        )


def _build_utility_response(utility: Utility, db: Optional[Session] = None) -> UtilityResponse:
    infrastructure_layers = sorted(
        list(utility.infrastructure_layers or []),
        key=lambda layer: list(UTILITY_INFRASTRUCTURE_ASSETS).index(layer.asset_type)
        if layer.asset_type in UTILITY_INFRASTRUCTURE_ASSETS else 999,
    )
    boundary_geojson = _deserialize_boundary_geojson(utility.boundary_geojson)
    service_areas = sorted(
        list(utility.service_areas or []),
        key=lambda area: (
            str(area.category.value if hasattr(area.category, "value") else area.category),
            area.name.casefold(),
        ),
    )

    return UtilityResponse(
        id=utility.id,
        name=utility.name,
        region_name=utility.region_name,
        description=utility.description,
        contact_phone=utility.contact_phone,
        contact_email=utility.contact_email,
        contact_address=utility.contact_address,
        center_latitude=utility.center_latitude,
        center_longitude=utility.center_longitude,
        boundary_geojson=boundary_geojson,
        boundary_source_type=utility.boundary_source_type or ("uploaded" if boundary_geojson else "none"),
        boundary_status=utility.boundary_status or ("verified" if boundary_geojson else "none"),
        status=utility.status,
        service_areas=[_build_service_area_response(area) for area in service_areas],
        infrastructure_layers=[_build_infrastructure_asset_response(layer) for layer in infrastructure_layers],
        created_at=utility.created_at,
        updated_at=utility.updated_at,
    )


@utilities_router.get("/public/resolve", response_model=UtilityPublicContactResponse)
async def resolve_public_utility_for_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db),
):
    """
    Resolve the responsible utility for a public mobile user based on location.
    """
    resolved_region_name = resolve_region_name_hint(None, latitude, longitude)
    utility = find_utility_by_region_name(resolved_region_name, db) if resolved_region_name else None
    if not utility:
        utility, _distance = find_nearest_utility(latitude, longitude, db)
    if not utility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No utility coverage is configured for this location",
        )

    dma, _dma_distance = find_nearest_dma_within_utility(latitude, longitude, utility, db)

    return UtilityPublicContactResponse(
        utility_id=utility.id,
        utility_name=utility.name,
        region_name=resolved_region_name or utility.region_name,
        dma_id=dma.id if dma else None,
        dma_name=dma.name if dma else None,
        contact_phone=utility.contact_phone,
        contact_email=utility.contact_email,
        contact_address=utility.contact_address,
    )


def _coerce_geojson(payload: Any):
    if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
        return payload

    if isinstance(payload, dict) and payload.get("type") in {
        "Feature",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "Point",
        "MultiPoint",
        "GeometryCollection",
    }:
        return {
            "type": "FeatureCollection",
            "features": [
                payload if payload.get("type") == "Feature" else {"type": "Feature", "properties": {}, "geometry": payload}
            ],
        }

    if isinstance(payload, list):
        features = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "Feature":
                features.append(item)
            elif item.get("type"):
                features.append({"type": "Feature", "properties": {}, "geometry": item})
        if features:
            return {"type": "FeatureCollection", "features": features}

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Pipe network file could not be converted into previewable map features.",
    )


def _deserialize_boundary_geojson(raw_value: Optional[str]) -> Optional[dict[str, Any]]:
    if not raw_value:
        return None

    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def _serialize_boundary_geojson(boundary_geojson: Optional[dict[str, Any]]) -> Optional[str]:
    if boundary_geojson is None:
        return None

    if not isinstance(boundary_geojson, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Utility boundary must be a valid GeoJSON Polygon or MultiPolygon object.",
        )

    geometry_type = boundary_geojson.get("type")
    if geometry_type not in {"Polygon", "MultiPolygon"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Utility boundary must use GeoJSON Polygon or MultiPolygon geometry.",
        )

    coordinates = boundary_geojson.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Utility boundary must include coordinate rings.",
        )

    def normalize_ring(raw_ring: Any) -> list[list[float]]:
        if not isinstance(raw_ring, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Utility boundary polygon must include an outer coordinate ring.",
            )

        normalized_ring: list[list[float]] = []
        distinct_points: set[tuple[float, float]] = set()

        for raw_point in raw_ring:
            if not isinstance(raw_point, (list, tuple)) or len(raw_point) < 2:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Each utility boundary point must contain longitude and latitude values.",
                )

            try:
                longitude = float(raw_point[0])
                latitude = float(raw_point[1])
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Utility boundary points must be valid numeric coordinates.",
                ) from None

            if longitude < -180 or longitude > 180 or latitude < -90 or latitude > 90:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Utility boundary coordinates must be within valid longitude and latitude ranges.",
                )

            normalized_ring.append([longitude, latitude])
            distinct_points.add((longitude, latitude))

        if len(distinct_points) < 3:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Each utility boundary polygon must contain at least three distinct points.",
            )

        if normalized_ring[0] != normalized_ring[-1]:
            normalized_ring.append(normalized_ring[0])
        return normalized_ring

    def normalize_polygon(raw_polygon: Any) -> list[list[list[float]]]:
        if not isinstance(raw_polygon, list) or not raw_polygon:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Utility boundary polygon must include coordinate rings.",
            )
        # Store only validated rings. The first ring is the service-area exterior;
        # interior holes remain supported when uploaded by GIS tools.
        return [normalize_ring(ring) for ring in raw_polygon if isinstance(ring, list)]

    if geometry_type == "Polygon":
        normalized: dict[str, Any] = {"type": "Polygon", "coordinates": normalize_polygon(coordinates)}
    else:
        normalized_polygons = [normalize_polygon(polygon) for polygon in coordinates if isinstance(polygon, list)]
        if not normalized_polygons:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Utility boundary multipolygon must include at least one polygon.",
            )
        normalized = {"type": "MultiPolygon", "coordinates": normalized_polygons}

    try:
        boundary_shape = shape(normalized)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Utility boundary geometry is invalid.",
        ) from None

    if boundary_shape.is_empty or not boundary_shape.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Utility boundary geometry is empty or invalid.",
        )

    return json.dumps(normalized)


def _validate_utility_boundary_does_not_overlap(
    boundary_geojson_raw: Optional[str],
    db: Session,
    *,
    utility_id: Optional[str] = None,
) -> None:
    boundary_geojson = _deserialize_boundary_geojson(boundary_geojson_raw)
    if not boundary_geojson:
        return

    try:
        boundary_shape = shape(boundary_geojson)
    except Exception:
        return

    existing_utilities = db.query(Utility).filter(Utility.boundary_geojson.isnot(None)).all()
    for existing in existing_utilities:
        if utility_id and existing.id == utility_id:
            continue
        existing_geojson = _deserialize_boundary_geojson(existing.boundary_geojson)
        if not existing_geojson:
            continue
        try:
            existing_shape = shape(existing_geojson)
        except Exception:
            continue
        if boundary_shape.intersects(existing_shape) and boundary_shape.intersection(existing_shape).area > 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Utility boundary overlaps with {existing.name}. Upload a corrected non-overlapping boundary.",
            )


def _filter_pipe_network_to_dma_boundary(
    feature_collection: dict[str, Any],
    boundary_geojson_raw: Optional[str],
) -> dict[str, Any]:
    boundary_geojson = _deserialize_boundary_geojson(boundary_geojson_raw)
    if not boundary_geojson:
        return feature_collection

    try:
        boundary_shape = shape(boundary_geojson)
    except Exception:
        return feature_collection

    filtered_features: list[dict[str, Any]] = []
    for feature in feature_collection.get("features", []):
        if not isinstance(feature, dict):
            continue

        geometry = feature.get("geometry")
        if not geometry:
            continue

        try:
            feature_shape = shape(geometry)
        except Exception:
            continue

        if feature_shape.intersects(boundary_shape):
            filtered_features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": filtered_features,
    }


def _decode_text_bytes(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Pipe network text file could not be decoded.",
    )


def _parse_coordinate_sequence(raw: str) -> list[list[float]]:
    coordinates: list[list[float]] = []
    for chunk in raw.replace("\n", " ").split():
        parts = [part for part in chunk.split(",") if part]
        if len(parts) < 2:
            continue
        try:
            coordinates.append([float(parts[0]), float(parts[1])])
        except ValueError:
            continue
    return coordinates


def _strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _parse_kml_features(root: ET.Element) -> dict[str, Any]:
    features: list[dict[str, Any]] = []

    for placemark in root.iter():
        if _strip_namespace(placemark.tag) != "Placemark":
            continue

        properties: dict[str, Any] = {}
        name_node = next((child for child in placemark.iter() if _strip_namespace(child.tag) == "name"), None)
        if name_node is not None and name_node.text:
            properties["name"] = name_node.text.strip()

        for node in placemark.iter():
            tag = _strip_namespace(node.tag)
            if tag not in {"Point", "LineString", "Polygon"}:
                continue

            coord_node = next((child for child in node.iter() if _strip_namespace(child.tag) == "coordinates"), None)
            if coord_node is None or not coord_node.text:
                continue

            coordinates = _parse_coordinate_sequence(coord_node.text)
            if not coordinates:
                continue

            geometry: Optional[dict[str, Any]] = None
            if tag == "Point":
                geometry = {"type": "Point", "coordinates": coordinates[0]}
            elif tag == "LineString":
                geometry = {"type": "LineString", "coordinates": coordinates}
            elif tag == "Polygon":
                geometry = {"type": "Polygon", "coordinates": [coordinates]}

            if geometry:
                features.append({
                    "type": "Feature",
                    "properties": properties.copy(),
                    "geometry": geometry,
                })

    return {"type": "FeatureCollection", "features": features}


def _merge_feature_collections(collections: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            feature
            for collection in collections
            for feature in collection.get("features", [])
            if isinstance(feature, dict)
        ],
    }


def _tag_feature_collection_source(collection: dict[str, Any], source_name: str) -> dict[str, Any]:
    tagged_features: list[dict[str, Any]] = []
    for feature in collection.get("features", []):
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        tagged_features.append({
            **feature,
            "properties": {
                **properties,
                "source_file": source_name,
            },
        })

    return {
        **collection,
        "features": tagged_features,
    }


def _normalize_property_key(key: str) -> str:
    return key.strip().lower().replace("-", "_")


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _has_any_property_value(properties: dict[str, Any], keys: tuple[str, ...]) -> bool:
    for key in keys:
        if key in properties and not _is_missing_value(properties[key]):
            return True
    return False


def _summarize_feature_attributes(features: list[dict[str, Any]]) -> dict[str, int]:
    missing_material = 0
    missing_condition = 0
    missing_diameter = 0
    missing_location = 0

    for feature in features:
        raw_properties = feature.get("properties")
        properties = (
            {_normalize_property_key(str(key)): value for key, value in raw_properties.items()}
            if isinstance(raw_properties, dict)
            else {}
        )

        if not _has_any_property_value(properties, PIPE_NETWORK_REQUIRED_TEXT_COLUMNS["material"]):
            missing_material += 1
        if not _has_any_property_value(properties, PIPE_NETWORK_REQUIRED_TEXT_COLUMNS["condition"]):
            missing_condition += 1
        if not _has_any_property_value(properties, PIPE_NETWORK_REQUIRED_NUMERIC_COLUMNS):
            missing_diameter += 1
        if not _has_any_property_value(properties, PIPE_NETWORK_REQUIRED_TEXT_COLUMNS["location"]):
            missing_location += 1

    return {
        "missing_material": missing_material,
        "missing_condition": missing_condition,
        "missing_diameter": missing_diameter,
        "missing_location": missing_location,
    }


def _build_ingest_summary(
    feature_collection: dict[str, Any],
    *,
    total_features_read: Optional[int] = None,
    skipped_missing_geometry: int = 0,
    skipped_invalid_geometry: int = 0,
    skipped_unsupported_geometry: int = 0,
    source_layers: Optional[list[str]] = None,
) -> PipeNetworkIngestSummary:
    features = [
        feature
        for feature in feature_collection.get("features", [])
        if isinstance(feature, dict)
    ]
    previewable_features = len(features)
    total = total_features_read if total_features_read is not None else previewable_features
    skipped_features = max(
        total - previewable_features,
        skipped_missing_geometry + skipped_invalid_geometry + skipped_unsupported_geometry,
    )
    attribute_summary = _summarize_feature_attributes(features)

    has_warnings = any(
        [
            skipped_features > 0,
            attribute_summary["missing_material"] > 0,
            attribute_summary["missing_condition"] > 0,
            attribute_summary["missing_diameter"] > 0,
            attribute_summary["missing_location"] > 0,
        ]
    )

    return PipeNetworkIngestSummary(
        total_features_read=total,
        previewable_features=previewable_features,
        skipped_features=skipped_features,
        skipped_missing_geometry=skipped_missing_geometry,
        skipped_invalid_geometry=skipped_invalid_geometry,
        skipped_unsupported_geometry=skipped_unsupported_geometry,
        missing_material=attribute_summary["missing_material"],
        missing_condition=attribute_summary["missing_condition"],
        missing_diameter=attribute_summary["missing_diameter"],
        missing_location=attribute_summary["missing_location"],
        source_layers=source_layers or [],
        has_warnings=has_warnings,
    )


def _load_kml_geojson(data: bytes) -> dict[str, Any]:
    try:
        root = ET.fromstring(_decode_text_bytes(data))
    except ET.ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipe network KML file could not be parsed.",
        ) from exc

    feature_collection = _parse_kml_features(root)
    if feature_collection["features"]:
        return feature_collection

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Pipe network KML file did not contain previewable geometry.",
    )


def _split_wkt_groups(raw: str) -> list[str]:
    groups: list[str] = []
    depth = 0
    start: Optional[int] = None

    for index, character in enumerate(raw):
        if character == "(":
            depth += 1
            if depth == 1:
                start = index + 1
        elif character == ")":
            if depth == 1 and start is not None:
                groups.append(raw[start:index])
                start = None
            depth -= 1

    return groups


def _parse_wkt_coordinate_list(raw: str) -> list[list[float]]:
    coordinates: list[list[float]] = []
    for point_text in raw.split(","):
        parts = [part for part in point_text.strip().split() if part]
        if len(parts) < 2:
            continue
        try:
            coordinates.append([float(parts[0]), float(parts[1])])
        except ValueError:
            continue
    return coordinates


def _parse_wkt_geometry(raw: str) -> Optional[dict[str, Any]]:
    text = raw.strip()
    if not text:
        return None

    geometry_type, _, remainder = text.partition("(")
    normalized_type = geometry_type.strip().upper()
    if not remainder:
        return None

    body = text[len(geometry_type):].strip()
    while body.startswith("(") and body.endswith(")"):
        inner = body[1:-1].strip()
        if not inner:
            break
        body = inner
        if normalized_type in {"POINT", "LINESTRING"}:
            break

    if normalized_type == "POINT":
        coordinates = _parse_wkt_coordinate_list(body)
        return {"type": "Point", "coordinates": coordinates[0]} if coordinates else None

    if normalized_type == "LINESTRING":
        coordinates = _parse_wkt_coordinate_list(body)
        return {"type": "LineString", "coordinates": coordinates} if coordinates else None

    if normalized_type == "POLYGON":
        rings = [_parse_wkt_coordinate_list(group) for group in _split_wkt_groups(f"({body})")]
        rings = [ring for ring in rings if ring]
        return {"type": "Polygon", "coordinates": rings} if rings else None

    if normalized_type == "MULTILINESTRING":
        lines = [_parse_wkt_coordinate_list(group) for group in _split_wkt_groups(f"({body})")]
        lines = [line for line in lines if line]
        return {"type": "MultiLineString", "coordinates": lines} if lines else None

    if normalized_type == "MULTIPOLYGON":
        polygons: list[list[list[float]]] = []
        for polygon_group in _split_wkt_groups(f"({body})"):
            rings = [_parse_wkt_coordinate_list(group) for group in _split_wkt_groups(f"({polygon_group})")]
            rings = [ring for ring in rings if ring]
            if rings:
                polygons.append(rings)
        return {"type": "MultiPolygon", "coordinates": polygons} if polygons else None

    return None


def _load_delimited_geojson(data: bytes) -> dict[str, Any]:
    text = _decode_text_bytes(data)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipe network table file needs column headers for preview.",
        )

    headers = {header.lower().strip(): header for header in reader.fieldnames if header}
    geometry_header = next((headers[key] for key in ("wkt", "geometry", "geom", "the_geom", "shape") if key in headers), None)
    lon_header = next((headers[key] for key in ("longitude", "lon", "lng", "x") if key in headers), None)
    lat_header = next((headers[key] for key in ("latitude", "lat", "y") if key in headers), None)
    start_lon_header = next((headers[key] for key in ("start_lon", "from_lon", "x1") if key in headers), None)
    start_lat_header = next((headers[key] for key in ("start_lat", "from_lat", "y1") if key in headers), None)
    end_lon_header = next((headers[key] for key in ("end_lon", "to_lon", "x2") if key in headers), None)
    end_lat_header = next((headers[key] for key in ("end_lat", "to_lat", "y2") if key in headers), None)

    features: list[dict[str, Any]] = []
    for row in reader:
        geometry: Optional[dict[str, Any]] = None

        if geometry_header and row.get(geometry_header):
            geometry = _parse_wkt_geometry(row[geometry_header] or "")
        elif lon_header and lat_header and row.get(lon_header) and row.get(lat_header):
            try:
                geometry = {
                    "type": "Point",
                    "coordinates": [float(row[lon_header]), float(row[lat_header])],
                }
            except ValueError:
                geometry = None
        elif all((start_lon_header, start_lat_header, end_lon_header, end_lat_header)):
            try:
                geometry = {
                    "type": "LineString",
                    "coordinates": [
                        [float(row[start_lon_header]), float(row[start_lat_header])],
                        [float(row[end_lon_header]), float(row[end_lat_header])],
                    ],
                }
            except (TypeError, ValueError):
                geometry = None

        if not geometry:
            continue

        properties = {
            key: value
            for key, value in row.items()
            if value not in (None, "") and key not in {geometry_header, lon_header, lat_header, start_lon_header, start_lat_header, end_lon_header, end_lat_header}
        }
        features.append({
            "type": "Feature",
            "properties": properties,
            "geometry": geometry,
        })

    if not features:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipe network table file did not contain previewable geometry columns.",
        )

    return {"type": "FeatureCollection", "features": features}


def _load_plain_text_geojson(data: bytes) -> dict[str, Any]:
    text = _decode_text_bytes(data).strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipe network text file is empty.",
        )

    try:
        return _coerce_geojson(json.loads(text))
    except Exception:
        pass

    geometry = _parse_wkt_geometry(text)
    if geometry:
        return {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": geometry}]}

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    coordinates: list[list[float]] = []
    for line in lines:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            continue
        try:
            coordinates.append([float(parts[0]), float(parts[1])])
        except ValueError:
            continue

    if len(coordinates) >= 2:
        return {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": coordinates}}],
        }
    if len(coordinates) == 1:
        return {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": coordinates[0]}}],
        }

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Pipe network text file could not be converted into map geometry.",
    )



def _convert_shapefile_shape_to_geojson(shape_obj: Any) -> Optional[dict[str, Any]]:
    try:
        geometry = shape_obj.__geo_interface__
        if isinstance(geometry, dict) and geometry.get("type"):
            return geometry
    except Exception:
        pass

    points = [list(point[:2]) for point in getattr(shape_obj, "points", []) if len(point) >= 2]
    if not points:
        return None

    shape_type = int(getattr(shape_obj, "shapeType", 0) or 0)
    parts = list(getattr(shape_obj, "parts", []) or [])

    def split_parts() -> list[list[list[float]]]:
        if not parts:
            return [points]
        indexes = [int(part) for part in parts] + [len(points)]
        return [points[indexes[index]:indexes[index + 1]] for index in range(len(indexes) - 1) if points[indexes[index]:indexes[index + 1]]]

    if shape_type in {1, 11, 21}:
        return {"type": "Point", "coordinates": points[0]}
    if shape_type in {8, 18, 28}:
        return {"type": "MultiPoint", "coordinates": points}
    if shape_type in {3, 13, 23}:
        lines = split_parts()
        return {"type": "LineString", "coordinates": lines[0]} if len(lines) == 1 else {"type": "MultiLineString", "coordinates": lines}
    if shape_type in {5, 15, 25}:
        rings = split_parts()
        return {"type": "Polygon", "coordinates": rings}

    return None

def _load_shapefile_geojson(
    shp_data: bytes,
    shx_data: Optional[bytes] = None,
    dbf_data: Optional[bytes] = None,
) -> dict[str, Any]:
    try:
        import shapefile  # pyshp
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Shapefile support is unavailable on this server. Install pyshp and retry.",
        ) from exc

    try:
        reader = shapefile.Reader(
            shp=io.BytesIO(shp_data),
            shx=io.BytesIO(shx_data) if shx_data else None,
            dbf=io.BytesIO(dbf_data) if dbf_data else None,
            encoding="utf-8",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipe network shapefile could not be parsed.",
        ) from exc

    features: list[dict[str, Any]] = []
    if dbf_data:
        try:
            records = reader.shapeRecords()
            for shape_record in records:
                geometry = _convert_shapefile_shape_to_geojson(shape_record.shape)
                if not geometry:
                    continue
                raw_properties = shape_record.record.as_dict()
                properties = {
                    key: value
                    for key, value in raw_properties.items()
                    if value not in (None, "")
                }
                features.append(
                    {
                        "type": "Feature",
                        "properties": properties,
                        "geometry": geometry,
                    }
                )
        except Exception:
            pass

    if not features:
        try:
            for shape in reader.shapes():
                geometry = _convert_shapefile_shape_to_geojson(shape)
                if not geometry:
                    continue
                features.append(
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": geometry,
                    }
                )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Shapefile geometry could not be converted. Upload a ZIP containing the .shp, .shx, and .dbf files, or export this layer as GeoPackage.",
            ) from exc

    if not features:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Shapefile did not contain previewable geometry. Upload a ZIP containing the .shp, .shx, and .dbf files, or export this layer as GeoPackage.",
        )

    return {"type": "FeatureCollection", "features": features}


def _load_zip_geojson(data: bytes, allow_kml: bool = True) -> dict[str, Any]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipe network archive could not be opened.",
        ) from exc

    supported_extensions = [".geojson", ".json", ".kml", ".csv", ".txt", ".shp", ".shx", ".dbf"] if allow_kml else [".geojson", ".json", ".csv", ".txt", ".shp", ".shx", ".dbf"]
    collections: list[dict[str, Any]] = []
    archive_names = [name for name in archive.namelist() if not name.endswith("/")]

    shapefile_groups: dict[str, dict[str, bytes]] = {}
    for name in archive_names:
        extension = Path(name).suffix.lower()
        if extension not in {".shp", ".shx", ".dbf"}:
            continue
        base_name = str(Path(name).with_suffix(""))
        member_group = shapefile_groups.setdefault(base_name, {})
        with archive.open(name) as member:
            member_group[extension] = member.read()

    for base_name, group in shapefile_groups.items():
        shp_bytes = group.get(".shp")
        if not shp_bytes:
            continue
        try:
            shapefile_collection = _load_shapefile_geojson(
                shp_bytes,
                shx_data=group.get(".shx"),
                dbf_data=group.get(".dbf"),
            )
            collections.append(_tag_feature_collection_source(shapefile_collection, f"{base_name}.shp"))
        except HTTPException:
            continue

    for name in archive_names:
        extension = Path(name).suffix.lower()
        if extension not in supported_extensions or extension in {".shp", ".shx", ".dbf"}:
            continue
        with archive.open(name) as member:
            member_bytes = member.read()
        try:
            if extension in {".geojson", ".json"}:
                collections.append(
                    _tag_feature_collection_source(
                        _coerce_geojson(json.loads(_decode_text_bytes(member_bytes))),
                        name,
                    )
                )
            elif extension == ".kml":
                collections.append(_tag_feature_collection_source(_load_kml_geojson(member_bytes), name))
            elif extension == ".csv":
                collections.append(_tag_feature_collection_source(_load_delimited_geojson(member_bytes), name))
            elif extension == ".txt":
                collections.append(_tag_feature_collection_source(_load_plain_text_geojson(member_bytes), name))
        except HTTPException:
            continue

    merged = _merge_feature_collections(collections)
    if merged["features"]:
        return merged

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Pipe network archive did not contain any supported previewable geometry.",
    )


def _quote_sqlite_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _gpkg_geometry_wkb(geometry_blob: bytes) -> bytes:
    if len(geometry_blob) < 8 or geometry_blob[:2] != b"GP":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipe network GeoPackage contains unsupported geometry encoding.",
        )

    flags = geometry_blob[3]
    envelope_code = (flags >> 1) & 0b111
    header_length = 8

    if envelope_code == 1:
        header_length += 32
    elif envelope_code in {2, 3}:
        header_length += 48
    elif envelope_code == 4:
        header_length += 64

    return geometry_blob[header_length:]


def _load_gpkg_geojson_with_stats(data: bytes) -> tuple[dict[str, Any], PipeNetworkIngestSummary]:
    temp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".gpkg", delete=False) as temp_file:
            temp_file.write(data)
            temp_path = temp_file.name

        connection = sqlite3.connect(temp_path)
        try:
            cursor = connection.cursor()
            geometry_layers = cursor.execute(
                "SELECT table_name, column_name FROM gpkg_geometry_columns"
            ).fetchall()

            if not geometry_layers:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Pipe network GeoPackage did not contain any spatial layers.",
                )

            features: list[dict[str, Any]] = []
            source_layers: list[str] = []
            total_features_read = 0
            skipped_missing_geometry = 0
            skipped_invalid_geometry = 0
            skipped_unsupported_geometry = 0

            for table_name, geometry_column in geometry_layers:
                columns = [row[1] for row in cursor.execute(f"PRAGMA table_info({_quote_sqlite_identifier(table_name)})").fetchall()]
                if geometry_column not in columns:
                    continue
                source_layers.append(table_name)

                property_columns = [column for column in columns if column != geometry_column]
                select_columns = [geometry_column, *property_columns]
                query = (
                    "SELECT "
                    + ", ".join(_quote_sqlite_identifier(column) for column in select_columns)
                    + f" FROM {_quote_sqlite_identifier(table_name)}"
                )

                for row in cursor.execute(query):
                    total_features_read += 1
                    geometry_blob = row[0]
                    if not geometry_blob:
                        skipped_missing_geometry += 1
                        continue

                    try:
                        shape_geometry = wkb.loads(_gpkg_geometry_wkb(bytes(geometry_blob)))
                        geometry = mapping(shape_geometry)
                    except Exception:
                        skipped_invalid_geometry += 1
                        continue

                    if not isinstance(geometry, dict) or geometry.get("type") in {None, ""}:
                        skipped_unsupported_geometry += 1
                        continue

                    properties = {
                        column: value
                        for column, value in zip(property_columns, row[1:])
                        if value not in (None, "") and not isinstance(value, (bytes, bytearray))
                    }
                    properties.setdefault("source_table", table_name)

                    features.append(
                        {
                            "type": "Feature",
                            "properties": properties,
                            "geometry": geometry,
                        }
                    )

            if not features:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Pipe network GeoPackage could not be converted into previewable map features.",
                )

            feature_collection = {
                "type": "FeatureCollection",
                "features": features,
            }
            ingest_summary = _build_ingest_summary(
                feature_collection,
                total_features_read=total_features_read,
                skipped_missing_geometry=skipped_missing_geometry,
                skipped_invalid_geometry=skipped_invalid_geometry,
                skipped_unsupported_geometry=skipped_unsupported_geometry,
                source_layers=sorted(set(source_layers)),
            )
            return feature_collection, ingest_summary
        finally:
            connection.close()
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


def _load_gpkg_geojson(data: bytes) -> dict[str, Any]:
    feature_collection, _summary = _load_gpkg_geojson_with_stats(data)
    return feature_collection


def _load_pipe_network_geojson_with_summary(file_name: str, file_data: bytes) -> tuple[dict[str, Any], PipeNetworkIngestSummary]:
    extension = Path(file_name).suffix.lower()
    try:
        if extension == ".gpkg":
            return _load_gpkg_geojson_with_stats(file_data)
        if extension == ".shp":
            feature_collection = _load_shapefile_geojson(file_data)
            return feature_collection, _build_ingest_summary(feature_collection)
        if extension in {".geojson", ".json"}:
            feature_collection = _coerce_geojson(json.loads(_decode_text_bytes(file_data)))
            return feature_collection, _build_ingest_summary(feature_collection)
        if extension == ".kml":
            feature_collection = _load_kml_geojson(file_data)
            return feature_collection, _build_ingest_summary(feature_collection)
        if extension == ".kmz":
            feature_collection = _load_zip_geojson(file_data, allow_kml=True)
            return feature_collection, _build_ingest_summary(feature_collection)
        if extension == ".zip":
            feature_collection = _load_zip_geojson(file_data, allow_kml=True)
            return feature_collection, _build_ingest_summary(feature_collection)
        if extension == ".csv":
            feature_collection = _load_delimited_geojson(file_data)
            return feature_collection, _build_ingest_summary(feature_collection)
        if extension == ".txt":
            feature_collection = _load_plain_text_geojson(file_data)
            return feature_collection, _build_ingest_summary(feature_collection)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipe network file could not be parsed for map preview.",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Pipe network file type is not previewable on the map.",
    )


def _normalize_asset_type(asset_type: str) -> str:
    normalized = asset_type.strip().lower().replace("-", "_")
    aliases = {
        "pipe": "pipe_network",
        "pipes": "pipe_network",
        "pipelines": "pipe_network",
        "pipeline": "pipe_network",
        "valve": "valves",
        "source": "water_sources",
        "sources": "water_sources",
        "water_source": "water_sources",
        "storage": "storage_facilities",
        "storages": "storage_facilities",
        "storage_facility": "storage_facilities",
        "tank": "storage_facilities",
        "tanks": "storage_facilities",
        "meter": "bulk_meters",
        "meters": "bulk_meters",
        "bulk_meter": "bulk_meters",
    }
    return aliases.get(normalized, normalized)


def _ensure_supported_asset_type(asset_type: str) -> str:
    normalized = _normalize_asset_type(asset_type)
    if normalized not in UTILITY_INFRASTRUCTURE_ASSETS:
        supported = ", ".join(sorted(UTILITY_INFRASTRUCTURE_ASSETS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported infrastructure asset type. Supported types: {supported}",
        )
    return normalized


def _filter_feature_collection_by_asset_type(feature_collection: dict[str, Any], asset_type: str) -> dict[str, Any]:
    allowed_geometry_types = UTILITY_INFRASTRUCTURE_ASSETS[asset_type]["geometry_types"]
    features: list[dict[str, Any]] = []

    for feature in feature_collection.get("features", []):
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        geometry_type = geometry.get("type")
        if geometry_type not in allowed_geometry_types:
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        features.append({
            **feature,
            "properties": {
                **properties,
                "asset_type": asset_type,
                "asset_label": _asset_label(asset_type),
            },
        })

    if not features:
        label = _asset_label(asset_type).lower()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Uploaded file did not contain previewable {label} geometry.",
        )

    return {"type": "FeatureCollection", "features": features}


def _load_infrastructure_geojson_with_summary(file_name: str, file_data: bytes, asset_type: str) -> tuple[dict[str, Any], PipeNetworkIngestSummary]:
    feature_collection, summary = _load_pipe_network_geojson_with_summary(file_name, file_data)
    filtered_collection = _filter_feature_collection_by_asset_type(feature_collection, asset_type)
    filtered_summary = _build_ingest_summary(
        filtered_collection,
        total_features_read=summary.total_features_read,
        skipped_missing_geometry=summary.skipped_missing_geometry,
        skipped_invalid_geometry=summary.skipped_invalid_geometry,
        skipped_unsupported_geometry=summary.skipped_unsupported_geometry,
        source_layers=summary.source_layers,
    )
    return filtered_collection, filtered_summary


def _infrastructure_cache_key(layer: UtilityInfrastructureLayer) -> tuple[Any, ...]:
    return (
        "infrastructure",
        layer.id,
        layer.utility_id,
        layer.asset_type,
        layer.file_name,
        layer.file_size,
        layer.updated_at.isoformat() if layer.updated_at else None,
    )


def _load_infrastructure_geojson(layer: UtilityInfrastructureLayer) -> dict[str, Any]:
    cache_key = _infrastructure_cache_key(layer)
    cached_collection = _infrastructure_geojson_cache.get(cache_key)
    if cached_collection is not None:
        return copy.deepcopy(cached_collection)

    feature_collection, _summary = _load_infrastructure_geojson_with_summary(
        layer.file_name,
        layer.file_data,
        layer.asset_type,
    )
    _infrastructure_geojson_cache.clear()
    _infrastructure_geojson_cache[cache_key] = copy.deepcopy(feature_collection)
    return feature_collection


@utilities_router.get("", response_model=UtilityListResponse)
async def list_utilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all utilities with pagination
    Requires authentication
    """
    query = db.query(Utility)
    if current_user.user_type == "utility_manager" and current_user.utility_id:
        query = query.filter(Utility.id == current_user.utility_id)
    elif current_user.user_type in {"dma_manager", "engineer"}:
        scoped_utility_id = _resolve_current_user_utility_id(current_user, db)
        if scoped_utility_id:
            query = query.filter(Utility.id == scoped_utility_id)
        else:
            query = query.filter(Utility.id == "__no_access__")

    total = query.count()
    utilities = query.offset(skip).limit(limit).all()
    
    return UtilityListResponse(
        total=total,
        items=[_build_utility_response(u, db) for u in utilities],
    )


@utilities_router.get("/{utility_id}", response_model=UtilityResponse)
async def get_utility(
    utility_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get utility by ID
    Requires authentication
    """
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    
    if not utility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utility not found",
        )

    _ensure_utility_access(utility, current_user, db)
    return _build_utility_response(utility, db)


@utilities_router.post("", response_model=UtilityResponse, status_code=status.HTTP_201_CREATED)
async def create_utility(
    utility_data: UtilityCreate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new utility
    Requires admin role
    """
    if utility_data.center_latitude is None or utility_data.center_longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utility center latitude and longitude are required.",
        )

    boundary_geojson_raw = _serialize_boundary_geojson(utility_data.boundary_geojson)
    _validate_utility_boundary_does_not_overlap(boundary_geojson_raw, db)

    new_utility = Utility(
        name=utility_data.name,
        region_name=utility_data.region_name,
        description=utility_data.description,
        contact_phone=utility_data.contact_phone,
        contact_email=utility_data.contact_email,
        contact_address=utility_data.contact_address,
        center_latitude=utility_data.center_latitude,
        center_longitude=utility_data.center_longitude,
        boundary_geojson=boundary_geojson_raw,
        boundary_source_type="uploaded" if boundary_geojson_raw else "none",
        boundary_status="verified" if boundary_geojson_raw else "none",
        status=utility_data.status,
    )
    _replace_utility_service_areas(new_utility, utility_data.service_areas)
    
    db.add(new_utility)
    db.commit()
    db.refresh(new_utility)
    
    return _build_utility_response(new_utility, db)


@utilities_router.put("/{utility_id}", response_model=UtilityResponse)
async def update_utility(
    utility_id: str,
    utility_data: UtilityUpdate,
    current_user: CurrentUser = Depends(require_utility_manager),
    db: Session = Depends(get_db),
):
    """
    Update utility details
    Requires admin role
    """
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    
    if not utility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utility not found",
        )

    _ensure_utility_access(utility, current_user, db)
    boundary_was_sent = "boundary_geojson" in utility_data.model_fields_set
    update_data = utility_data.model_dump(exclude_unset=True)
    service_areas = update_data.pop("service_areas", None)
    raw_boundary_geojson = update_data.pop("boundary_geojson", None)
    update_data.pop("boundary_source_type", None)
    update_data.pop("boundary_status", None)
    if boundary_was_sent:
        boundary_geojson_raw = _serialize_boundary_geojson(raw_boundary_geojson)
        _validate_utility_boundary_does_not_overlap(boundary_geojson_raw, db, utility_id=utility.id)
        utility.boundary_geojson = boundary_geojson_raw
        utility.boundary_source_type = "uploaded" if boundary_geojson_raw else "none"
        utility.boundary_status = "verified" if boundary_geojson_raw else "none"
    if service_areas is not None:
        _replace_utility_service_areas(utility, [UtilityServiceAreaCreate(**area) if isinstance(area, dict) else area for area in service_areas])
    for field, value in update_data.items():
        setattr(utility, field, value)

    if utility.center_latitude is None or utility.center_longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utility center latitude and longitude are required.",
        )
    
    db.commit()
    db.refresh(utility)
    
    return _build_utility_response(utility, db)


@utilities_router.patch("/{utility_id}", response_model=UtilityResponse)
async def patch_utility(
    utility_id: str,
    utility_data: UtilityUpdate,
    current_user: CurrentUser = Depends(require_utility_manager),
    db: Session = Depends(get_db),
):
    """
    Partially update utility
    Requires admin role
    """
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    
    if not utility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utility not found",
        )

    _ensure_utility_access(utility, current_user, db)
    boundary_was_sent = "boundary_geojson" in utility_data.model_fields_set
    update_data = utility_data.model_dump(exclude_unset=True)
    service_areas = update_data.pop("service_areas", None)
    raw_boundary_geojson = update_data.pop("boundary_geojson", None)
    update_data.pop("boundary_source_type", None)
    update_data.pop("boundary_status", None)
    if boundary_was_sent:
        boundary_geojson_raw = _serialize_boundary_geojson(raw_boundary_geojson)
        _validate_utility_boundary_does_not_overlap(boundary_geojson_raw, db, utility_id=utility.id)
        utility.boundary_geojson = boundary_geojson_raw
        utility.boundary_source_type = "uploaded" if boundary_geojson_raw else "none"
        utility.boundary_status = "verified" if boundary_geojson_raw else "none"
    if service_areas is not None:
        _replace_utility_service_areas(utility, [UtilityServiceAreaCreate(**area) if isinstance(area, dict) else area for area in service_areas])
    for field, value in update_data.items():
        setattr(utility, field, value)

    if utility.center_latitude is None or utility.center_longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utility center latitude and longitude are required.",
        )
    
    db.commit()
    db.refresh(utility)
    
    return _build_utility_response(utility, db)


@utilities_router.delete("/{utility_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_utility(
    utility_id: str,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Delete utility by ID
    Requires admin role
    """
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    
    if not utility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utility not found",
        )
    
    db.delete(utility)
    db.commit()


@utilities_router.post("/{utility_id}/infrastructure/{asset_type}", response_model=UtilityInfrastructureUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_infrastructure_layer(
    utility_id: str,
    asset_type: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_utility_manager),
    db: Session = Depends(get_db),
):
    normalized_asset_type = _ensure_supported_asset_type(asset_type)
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    if not utility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utility not found",
        )

    _ensure_utility_access(utility, current_user, db)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded infrastructure file must have a filename",
        )

    extension = Path(file.filename).suffix.lower()
    if extension != ".gpkg":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Infrastructure uploads must use a single GeoPackage (.gpkg) file with geometry and attributes together.",
        )

    file_data = await file.read()
    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded infrastructure file is empty",
        )

    if len(file_data) > MAX_PIPE_NETWORK_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Infrastructure file is too large",
        )

    feature_collection, ingest_summary = _load_infrastructure_geojson_with_summary(
        file.filename,
        file_data,
        normalized_asset_type,
    )

    layer = (
        db.query(UtilityInfrastructureLayer)
        .filter(
            UtilityInfrastructureLayer.utility_id == utility.id,
            UtilityInfrastructureLayer.asset_type == normalized_asset_type,
        )
        .first()
    )
    if not layer:
        layer = UtilityInfrastructureLayer(
            utility_id=utility.id,
            asset_type=normalized_asset_type,
        )
        db.add(layer)

    layer.file_data = file_data
    layer.file_name = file.filename
    layer.mime_type = file.content_type or "application/geopackage+sqlite3"
    layer.file_size = len(file_data)
    layer.feature_count = len(feature_collection.get("features", []))
    layer.uploaded_by_manager_id = current_user.id if current_user.user_type == "utility_manager" else None

    _infrastructure_geojson_cache.clear()
    db.commit()
    db.refresh(utility)
    db.refresh(layer)
    return UtilityInfrastructureUploadResponse(
        utility=_build_utility_response(utility, db),
        asset=_build_infrastructure_asset_response(layer),
        ingest_summary=ingest_summary,
    )


@utilities_router.get("/{utility_id}/infrastructure/{asset_type}/download")
async def download_infrastructure_layer(
    utility_id: str,
    asset_type: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    normalized_asset_type = _ensure_supported_asset_type(asset_type)
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    if not utility:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utility not found")

    _ensure_utility_access(utility, current_user, db)

    layer = (
        db.query(UtilityInfrastructureLayer)
        .filter(
            UtilityInfrastructureLayer.utility_id == utility.id,
            UtilityInfrastructureLayer.asset_type == normalized_asset_type,
        )
        .first()
    )
    if not layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Infrastructure asset file not found")

    headers = {"Content-Disposition": f'attachment; filename="{layer.file_name}"'}
    return Response(content=layer.file_data, media_type=layer.mime_type, headers=headers)


@utilities_router.get("/{utility_id}/infrastructure/{asset_type}/geojson")
async def preview_infrastructure_layer_geojson(
    utility_id: str,
    asset_type: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    normalized_asset_type = _ensure_supported_asset_type(asset_type)
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    if not utility:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utility not found")

    _ensure_utility_access(utility, current_user, db)

    layer = (
        db.query(UtilityInfrastructureLayer)
        .filter(
            UtilityInfrastructureLayer.utility_id == utility.id,
            UtilityInfrastructureLayer.asset_type == normalized_asset_type,
        )
        .first()
    )
    if not layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Infrastructure asset file not found")

    return _load_infrastructure_geojson(layer)


@utilities_router.delete("/{utility_id}/infrastructure/{asset_type}", response_model=UtilityResponse)
async def delete_infrastructure_layer(
    utility_id: str,
    asset_type: str,
    current_user: CurrentUser = Depends(require_utility_manager),
    db: Session = Depends(get_db),
):
    normalized_asset_type = _ensure_supported_asset_type(asset_type)
    utility = db.query(Utility).filter(Utility.id == utility_id).first()
    if not utility:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utility not found")

    _ensure_utility_access(utility, current_user, db)

    layer = (
        db.query(UtilityInfrastructureLayer)
        .filter(
            UtilityInfrastructureLayer.utility_id == utility.id,
            UtilityInfrastructureLayer.asset_type == normalized_asset_type,
        )
        .first()
    )
    if not layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Infrastructure asset file not found")

    db.delete(layer)
    _infrastructure_geojson_cache.clear()
    db.commit()
    db.refresh(utility)
    return _build_utility_response(utility, db)
