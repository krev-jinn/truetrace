"""
TrueTrace Sensor Observability & Visibility Assessment
Models sensor placement, monitored CIDR ranges, capture windows, and hardware packet-drop metrics.
Enforces the fundamental epistemic invariant: Absence of evidence is not evidence of absence.
"""

import ipaddress
import datetime
from typing import List, Tuple, Optional
from ..models import SensorConfig, ObservabilityStatus, NetworkClaim


def ip_in_network(ip_str: str, cidr_str: str) -> bool:
    """Checks whether an IPv4 address belongs to a specified CIDR network."""
    try:
        ip = ipaddress.ip_address(ip_str)
        net = ipaddress.ip_network(cidr_str, strict=False)
        return ip in net
    except Exception:
        return False


def assess_sensor_observability(claim: NetworkClaim, sensors: List[SensorConfig]) -> Tuple[ObservabilityStatus, Optional[str], str]:
    """
    Evaluates whether the network sensor infrastructure had sufficient visibility to observe the claimed flow.
    Returns: (ObservabilityStatus, covering_sensor_id, detailed_rationale)
    """
    if not sensors:
        return (
            ObservabilityStatus.UNOBSERVABLE,
            None,
            "No network sensors registered for this investigation. Absence of network evidence cannot refute host claims."
        )

    covering_sensor: Optional[SensorConfig] = None
    reasons: List[str] = []

    for sensor in sensors:
        if sensor.status.upper() != "ACTIVE":
            reasons.append(f"Sensor '{sensor.sensor_name}' is inactive/offline.")
            continue

        # Check CIDR coverage
        src_covered = any(ip_in_network(claim.src_ip, cidr) for cidr in sensor.monitored_cidrs) if claim.src_ip != "0.0.0.0" else True
        dst_covered = any(ip_in_network(claim.dst_ip, cidr) for cidr in sensor.monitored_cidrs)

        if not (src_covered or dst_covered):
            reasons.append(
                f"Sensor '{sensor.sensor_name}' does not monitor subnet for {claim.src_ip} or {claim.dst_ip} "
                f"(Monitored: {', '.join(sensor.monitored_cidrs)})."
            )
            continue

        # Check temporal coverage
        ts = claim.timestamp
        if sensor.capture_start:
            try:
                start_dt = datetime.datetime.fromisoformat(sensor.capture_start.replace("Z", "+00:00"))
                if ts < start_dt.timestamp():
                    reasons.append(f"Claim timestamp ({claim.timestamp_iso}) occurred before sensor '{sensor.sensor_name}' started capturing.")
                    continue
            except Exception:
                pass

        if sensor.capture_end:
            try:
                end_dt = datetime.datetime.fromisoformat(sensor.capture_end.replace("Z", "+00:00"))
                if ts > end_dt.timestamp():
                    reasons.append(f"Claim timestamp ({claim.timestamp_iso}) occurred after sensor '{sensor.sensor_name}' stopped capturing.")
                    continue
            except Exception:
                pass

        # We found a topologically and temporally covering sensor!
        covering_sensor = sensor
        break

    if not covering_sensor:
        explanation = "Flow was unobservable: " + "; ".join(reasons)
        return (ObservabilityStatus.UNOBSERVABLE, None, explanation)

    # Check for degraded visibility / hardware packet loss
    if covering_sensor.packet_loss_detected:
        explanation = (
            f"Sensor '{covering_sensor.sensor_name}' monitors flow topology ({claim.dst_ip}), but recorded "
            f"packet loss / buffer ring drops during the session. Evidence completeness cannot be guaranteed."
        )
        return (ObservabilityStatus.DEGRADED_VISIBILITY, covering_sensor.id, explanation)

    explanation = (
        f"Sensor '{covering_sensor.sensor_name}' was actively monitoring subnet encompassing {claim.dst_ip} "
        f"at timestamp {claim.timestamp_iso} with zero recorded packet drops."
    )
    return (ObservabilityStatus.FULLY_OBSERVABLE, covering_sensor.id, explanation)
