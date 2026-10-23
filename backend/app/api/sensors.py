"""
TrueTrace Sensor Configuration API
Manages registered network sensors, tap interfaces, monitored CIDRs, and loss metrics.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import uuid
import json

from ..models import SensorConfig
from ..database import get_db_connection

router = APIRouter(prefix="/api/sensors", tags=["Sensors"])


@router.get("/{inv_id}", response_model=List[SensorConfig])
def list_sensors(inv_id: str):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM sensors WHERE investigation_id = ?", (inv_id,)).fetchall()
    results = []
    for r in rows:
        results.append(SensorConfig(
            id=r["id"],
            investigation_id=r["investigation_id"],
            sensor_name=r["sensor_name"],
            interface=r["interface"],
            monitored_cidrs=json.loads(r["monitored_cidrs"]) if r["monitored_cidrs"] else [],
            capture_start=r["capture_start"],
            capture_end=r["capture_end"],
            packet_loss_detected=bool(r["packet_loss_detected"]),
            status=r["status"],
            notes=r["notes"] or ""
        ))
    conn.close()
    return results


@router.post("", response_model=SensorConfig)
def add_sensor(sensor: SensorConfig):
    conn = get_db_connection()
    with conn:
        conn.execute(
            """INSERT INTO sensors 
               (id, investigation_id, sensor_name, interface, monitored_cidrs, capture_start, capture_end, packet_loss_detected, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                sensor.id,
                sensor.investigation_id,
                sensor.sensor_name,
                sensor.interface,
                json.dumps(sensor.monitored_cidrs),
                sensor.capture_start,
                sensor.capture_end,
                1 if sensor.packet_loss_detected else 0,
                sensor.status,
                sensor.notes
            )
        )
    conn.close()
    return sensor


@router.put("/{sensor_id}", response_model=SensorConfig)
def update_sensor(sensor_id: str, sensor: SensorConfig):
    conn = get_db_connection()
    with conn:
        conn.execute(
            """UPDATE sensors 
               SET sensor_name = ?, interface = ?, monitored_cidrs = ?, capture_start = ?, capture_end = ?, packet_loss_detected = ?, status = ?, notes = ?
               WHERE id = ?""",
            (
                sensor.sensor_name,
                sensor.interface,
                json.dumps(sensor.monitored_cidrs),
                sensor.capture_start,
                sensor.capture_end,
                1 if sensor.packet_loss_detected else 0,
                sensor.status,
                sensor.notes,
                sensor_id
            )
        )
    conn.close()
    return sensor
