"""
Step 59: Mock IoT APIs for Hotel Infrastructure
Simulates real IoT devices: door locks, fire alarms, HVAC, elevators, lighting.
Each device has realistic state management, event history, and failure simulation.
"""

import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("ahos.integrations.iot")


# ─────────────────────────────────────────────
# Enums & Models
# ─────────────────────────────────────────────
class DeviceType(str, Enum):
    DOOR_LOCK = "door_lock"
    FIRE_ALARM = "fire_alarm"
    HVAC = "hvac"
    ELEVATOR = "elevator"
    LIGHTING = "lighting"
    CAMERA = "camera"
    WATER_SENSOR = "water_sensor"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class DoorState(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    EMERGENCY_OPEN = "emergency_open"


class FireAlarmState(str, Enum):
    NORMAL = "normal"
    ALERT = "alert"
    TESTING = "testing"
    SUPPRESSION_ACTIVE = "suppression_active"


class IoTCommand(BaseModel):
    """Command to send to an IoT device."""
    device_id: str
    action: str  # e.g., "unlock", "lock", "trigger_alarm", "set_temp"
    parameters: dict = Field(default_factory=dict)
    authorized_by: str = Field(default="system", description="Agent or user that authorized this")
    hotel_id: str = Field(default="HQ")


class IoTEvent(BaseModel):
    """An event emitted by an IoT device."""
    event_id: str
    device_id: str
    device_type: str
    hotel_id: str
    event_type: str  # "state_change", "alert", "error", "command_executed"
    description: str
    timestamp: str
    data: dict = Field(default_factory=dict)


class IoTDevice(BaseModel):
    """Represents an IoT device in a hotel."""
    device_id: str
    device_type: DeviceType
    hotel_id: str
    location: str  # e.g., "Floor 3 - Room 301"
    status: DeviceStatus = DeviceStatus.ONLINE
    state: dict = Field(default_factory=dict)
    last_heartbeat: str = ""
    firmware_version: str = "2.1.4"
    battery_level: Optional[float] = None  # None for wired devices


# ─────────────────────────────────────────────
# IoT Simulator
# ─────────────────────────────────────────────
class IoTSimulator:
    """
    Simulates an IoT infrastructure for a hotel chain.
    Manages devices, processes commands, and generates realistic events.
    """

    def __init__(self):
        self.devices: dict[str, IoTDevice] = {}
        self.events: list[IoTEvent] = []
        self._init_default_devices()

    def _init_default_devices(self):
        """Initialize default IoT devices for demo hotels."""
        hotels = {
            "hotel-downtown": "Aegis Downtown",
            "hotel-airport": "Aegis Airport",
            "hotel-resort": "Aegis Beach Resort",
        }

        for hotel_id, hotel_name in hotels.items():
            # Door locks for 3 floors × 10 rooms
            for floor in range(1, 4):
                for room in range(1, 11):
                    room_num = f"{floor}{room:02d}"
                    self._add_device(IoTDevice(
                        device_id=f"{hotel_id}-door-{room_num}",
                        device_type=DeviceType.DOOR_LOCK,
                        hotel_id=hotel_id,
                        location=f"Floor {floor} - Room {room_num}",
                        state={"lock_state": DoorState.LOCKED, "access_log": []},
                        battery_level=85.0 + (room % 15),
                    ))

                # Fire alarm per floor
                self._add_device(IoTDevice(
                    device_id=f"{hotel_id}-fire-F{floor}",
                    device_type=DeviceType.FIRE_ALARM,
                    hotel_id=hotel_id,
                    location=f"Floor {floor} - Hallway",
                    state={"alarm_state": FireAlarmState.NORMAL, "smoke_level": 0.0, "temperature": 22.0},
                ))

                # HVAC per floor
                self._add_device(IoTDevice(
                    device_id=f"{hotel_id}-hvac-F{floor}",
                    device_type=DeviceType.HVAC,
                    hotel_id=hotel_id,
                    location=f"Floor {floor} - Central",
                    state={"mode": "auto", "target_temp": 22.0, "current_temp": 22.5, "humidity": 45},
                ))

            # Elevators
            for e in range(1, 3):
                self._add_device(IoTDevice(
                    device_id=f"{hotel_id}-elevator-{e}",
                    device_type=DeviceType.ELEVATOR,
                    hotel_id=hotel_id,
                    location=f"Elevator {e}",
                    state={"current_floor": 1, "direction": "idle", "doors": "closed", "in_service": True},
                ))

            # Lobby camera
            self._add_device(IoTDevice(
                device_id=f"{hotel_id}-camera-lobby",
                device_type=DeviceType.CAMERA,
                hotel_id=hotel_id,
                location="Lobby - Main Entrance",
                state={"recording": True, "motion_detected": False, "night_mode": False},
            ))

    def _add_device(self, device: IoTDevice):
        device.last_heartbeat = datetime.now(timezone.utc).isoformat()
        self.devices[device.device_id] = device

    def _emit_event(self, device: IoTDevice, event_type: str, description: str, data: dict = None) -> IoTEvent:
        event = IoTEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            device_id=device.device_id,
            device_type=device.device_type,
            hotel_id=device.hotel_id,
            event_type=event_type,
            description=description,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data or {},
        )
        self.events.append(event)
        logger.info(f"IoT Event: [{device.device_id}] {event_type} - {description}")
        return event

    # ─── Command Processing ───
    async def execute_command(self, cmd: IoTCommand) -> dict:
        """Execute a command on an IoT device."""
        device = self.devices.get(cmd.device_id)
        if not device:
            return {"success": False, "error": f"Device {cmd.device_id} not found"}

        if device.status == DeviceStatus.OFFLINE:
            return {"success": False, "error": f"Device {cmd.device_id} is offline"}

        if device.status == DeviceStatus.MAINTENANCE:
            return {"success": False, "error": f"Device {cmd.device_id} is in maintenance"}

        handler = self._get_command_handler(device.device_type, cmd.action)
        if not handler:
            return {"success": False, "error": f"Unknown action '{cmd.action}' for device type '{device.device_type}'"}

        return await handler(device, cmd)

    def _get_command_handler(self, device_type: DeviceType, action: str):
        handlers = {
            (DeviceType.DOOR_LOCK, "unlock"): self._door_unlock,
            (DeviceType.DOOR_LOCK, "lock"): self._door_lock,
            (DeviceType.DOOR_LOCK, "emergency_open"): self._door_emergency_open,
            (DeviceType.FIRE_ALARM, "trigger"): self._fire_trigger,
            (DeviceType.FIRE_ALARM, "silence"): self._fire_silence,
            (DeviceType.FIRE_ALARM, "test"): self._fire_test,
            (DeviceType.HVAC, "set_temperature"): self._hvac_set_temp,
            (DeviceType.HVAC, "set_mode"): self._hvac_set_mode,
            (DeviceType.ELEVATOR, "recall"): self._elevator_recall,
            (DeviceType.ELEVATOR, "lock_out"): self._elevator_lockout,
        }
        return handlers.get((device_type, action))

    # ─── Door Lock Handlers ───
    async def _door_unlock(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        old_state = device.state["lock_state"]
        device.state["lock_state"] = DoorState.UNLOCKED
        device.state.setdefault("access_log", []).append({
            "action": "unlock", "by": cmd.authorized_by, "at": datetime.now(timezone.utc).isoformat()
        })
        event = self._emit_event(device, "state_change", f"Door unlocked by {cmd.authorized_by}", {"old": old_state, "new": "unlocked"})
        return {"success": True, "device_id": device.device_id, "new_state": "unlocked", "event_id": event.event_id}

    async def _door_lock(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        device.state["lock_state"] = DoorState.LOCKED
        event = self._emit_event(device, "state_change", f"Door locked by {cmd.authorized_by}")
        return {"success": True, "device_id": device.device_id, "new_state": "locked", "event_id": event.event_id}

    async def _door_emergency_open(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        device.state["lock_state"] = DoorState.EMERGENCY_OPEN
        event = self._emit_event(device, "alert", f"🚨 EMERGENCY: Door forced open by {cmd.authorized_by}", {"reason": cmd.parameters.get("reason", "emergency")})
        return {"success": True, "device_id": device.device_id, "new_state": "emergency_open", "event_id": event.event_id, "alert": "EMERGENCY_PROTOCOL_ACTIVATED"}

    # ─── Fire Alarm Handlers ───
    async def _fire_trigger(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        device.state["alarm_state"] = FireAlarmState.ALERT
        device.state["smoke_level"] = cmd.parameters.get("smoke_level", 75.0)
        device.state["temperature"] = cmd.parameters.get("temperature", 45.0)
        event = self._emit_event(device, "alert", f"🔥 FIRE ALARM TRIGGERED at {device.location}", {"smoke_level": device.state["smoke_level"], "temperature": device.state["temperature"]})
        return {"success": True, "device_id": device.device_id, "alarm_state": "alert", "event_id": event.event_id, "alert": "FIRE_PROTOCOL_ACTIVATED"}

    async def _fire_silence(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        device.state["alarm_state"] = FireAlarmState.NORMAL
        device.state["smoke_level"] = 0.0
        event = self._emit_event(device, "state_change", f"Fire alarm silenced by {cmd.authorized_by}")
        return {"success": True, "device_id": device.device_id, "alarm_state": "normal", "event_id": event.event_id}

    async def _fire_test(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        device.state["alarm_state"] = FireAlarmState.TESTING
        event = self._emit_event(device, "state_change", f"Fire alarm test initiated by {cmd.authorized_by}")
        return {"success": True, "device_id": device.device_id, "alarm_state": "testing", "event_id": event.event_id}

    # ─── HVAC Handlers ───
    async def _hvac_set_temp(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        target = cmd.parameters.get("temperature", 22.0)
        target = max(16.0, min(30.0, target))  # Clamp
        device.state["target_temp"] = target
        event = self._emit_event(device, "state_change", f"HVAC target temp set to {target}°C")
        return {"success": True, "device_id": device.device_id, "target_temp": target, "event_id": event.event_id}

    async def _hvac_set_mode(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        mode = cmd.parameters.get("mode", "auto")
        if mode not in ("auto", "cool", "heat", "fan", "off"):
            return {"success": False, "error": f"Invalid HVAC mode: {mode}"}
        device.state["mode"] = mode
        event = self._emit_event(device, "state_change", f"HVAC mode set to {mode}")
        return {"success": True, "device_id": device.device_id, "mode": mode, "event_id": event.event_id}

    # ─── Elevator Handlers ───
    async def _elevator_recall(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        target_floor = cmd.parameters.get("floor", 1)
        device.state["current_floor"] = target_floor
        device.state["direction"] = "idle"
        event = self._emit_event(device, "state_change", f"Elevator recalled to floor {target_floor}")
        return {"success": True, "device_id": device.device_id, "current_floor": target_floor, "event_id": event.event_id}

    async def _elevator_lockout(self, device: IoTDevice, cmd: IoTCommand) -> dict:
        device.state["in_service"] = False
        device.state["direction"] = "idle"
        event = self._emit_event(device, "alert", f"⚠️ Elevator locked out by {cmd.authorized_by}")
        return {"success": True, "device_id": device.device_id, "in_service": False, "event_id": event.event_id}

    # ─── Bulk Operations ───
    async def unlock_floor(self, hotel_id: str, floor: int, authorized_by: str) -> list[dict]:
        """Unlock all doors on a specific floor (emergency protocol)."""
        results = []
        for device in self.devices.values():
            if (
                device.hotel_id == hotel_id
                and device.device_type == DeviceType.DOOR_LOCK
                and f"Floor {floor}" in device.location
            ):
                cmd = IoTCommand(device_id=device.device_id, action="emergency_open", parameters={"reason": "floor_emergency"}, authorized_by=authorized_by, hotel_id=hotel_id)
                result = await self.execute_command(cmd)
                results.append(result)
        return results

    async def trigger_fire_protocol(self, hotel_id: str, floor: int, authorized_by: str) -> dict:
        """Full fire protocol: trigger alarms + unlock doors + recall elevators."""
        results = {"alarms": [], "doors": [], "elevators": []}

        # Trigger fire alarms on affected floor
        fire_id = f"{hotel_id}-fire-F{floor}"
        if fire_id in self.devices:
            cmd = IoTCommand(device_id=fire_id, action="trigger", parameters={"smoke_level": 80, "temperature": 50}, authorized_by=authorized_by, hotel_id=hotel_id)
            results["alarms"].append(await self.execute_command(cmd))

        # Unlock all doors on that floor
        results["doors"] = await self.unlock_floor(hotel_id, floor, authorized_by)

        # Recall all elevators to ground floor
        for device in self.devices.values():
            if device.hotel_id == hotel_id and device.device_type == DeviceType.ELEVATOR:
                cmd = IoTCommand(device_id=device.device_id, action="recall", parameters={"floor": 1}, authorized_by=authorized_by, hotel_id=hotel_id)
                results["elevators"].append(await self.execute_command(cmd))

        return results

    # ─── Queries ───
    def get_devices(self, hotel_id: Optional[str] = None, device_type: Optional[DeviceType] = None) -> list[dict]:
        """Get device list with optional filters."""
        devices = list(self.devices.values())
        if hotel_id:
            devices = [d for d in devices if d.hotel_id == hotel_id]
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        return [d.model_dump() for d in devices]

    def get_events(self, hotel_id: Optional[str] = None, device_id: Optional[str] = None, limit: int = 50) -> list[dict]:
        """Get recent events with optional filters."""
        events = self.events.copy()
        if hotel_id:
            events = [e for e in events if e.hotel_id == hotel_id]
        if device_id:
            events = [e for e in events if e.device_id == device_id]
        return [e.model_dump() for e in events[-limit:]]

    def get_device_summary(self, hotel_id: str) -> dict:
        """Get summary statistics for a hotel's IoT devices."""
        devices = [d for d in self.devices.values() if d.hotel_id == hotel_id]
        summary = {
            "total_devices": len(devices),
            "by_type": {},
            "by_status": {},
            "alerts_active": 0,
        }
        for d in devices:
            summary["by_type"][d.device_type] = summary["by_type"].get(d.device_type, 0) + 1
            summary["by_status"][d.status] = summary["by_status"].get(d.status, 0) + 1
            if d.device_type == DeviceType.FIRE_ALARM and d.state.get("alarm_state") == FireAlarmState.ALERT:
                summary["alerts_active"] += 1
        return summary


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────
iot_simulator = IoTSimulator()
