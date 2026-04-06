"""
Phase 5 Routes: External Integrations API
Exposes all Phase 5 services as REST endpoints.
"""
from fastapi import APIRouter, Query
from typing import Optional

from backend.integrations.gmail_service import gmail_service, EmailAlert
from backend.integrations.notion_service import notion_service, NotionLogEntry, NotionQueryFilter
from backend.integrations.twilio_service import twilio_service, SMSRequest, ApprovalSMS
from backend.integrations.iot_service import iot_simulator, IoTCommand, DeviceType
from backend.database.hotel_db import hotel_db, Booking, IncidentLog, FinanceRecord, Guest
from backend.gateway.api_gateway import api_gateway, GatewayRequest
from backend.gateway.cache import cache
from backend.monitoring.usage_tracker import usage_tracker
from backend.monitoring.cost_monitor import cost_monitor

router = APIRouter()

# ═══════════════════════════════════════════
# 📧 Gmail Integration (Step 56)
# ═══════════════════════════════════════════
@router.post("/integrations/gmail/send", tags=["Gmail"])
async def send_email_alert(alert: EmailAlert):
    """Send an email alert through Gmail."""
    result = await gmail_service.send_alert(alert)
    from backend.monitoring.usage_tracker import APIUsageRecord
    usage_tracker.record(APIUsageRecord(service="gmail", operation="send_alert", hotel_id=alert.hotel_id))
    cost_monitor.record_cost("gmail", "send_alert", alert.hotel_id)
    return result

@router.get("/integrations/gmail/log", tags=["Gmail"])
async def get_email_log():
    return {"sent_emails": gmail_service.get_sent_log()}

# ═══════════════════════════════════════════
# 📋 Notion CRM (Step 57)
# ═══════════════════════════════════════════
@router.post("/integrations/notion/log", tags=["Notion"])
async def create_notion_log(entry: NotionLogEntry):
    result = await notion_service.create_log(entry)
    cost_monitor.record_cost("notion", "create_log", entry.hotel_id)
    return result

@router.post("/integrations/notion/query", tags=["Notion"])
async def query_notion_logs(filters: NotionQueryFilter):
    result = await notion_service.query_logs(filters)
    cost_monitor.record_cost("notion", "query_logs")
    return result

@router.get("/integrations/notion/all", tags=["Notion"])
async def get_all_notion_logs():
    return {"logs": notion_service.get_all_logs()}

# ═══════════════════════════════════════════
# 📱 Twilio SMS (Step 58)
# ═══════════════════════════════════════════
@router.post("/integrations/twilio/send", tags=["Twilio"])
async def send_sms_alert(req: SMSRequest):
    result = await twilio_service.send_alert(req)
    cost_monitor.record_cost("twilio", "send_alert", req.hotel_id)
    return result

@router.post("/integrations/twilio/approval", tags=["Twilio"])
async def send_approval_sms(req: ApprovalSMS):
    result = await twilio_service.send_approval_request(req)
    cost_monitor.record_cost("twilio", "send_approval", req.hotel_id)
    return result

@router.post("/integrations/twilio/approval/{action_id}/respond", tags=["Twilio"])
async def respond_to_approval(action_id: str, approved: bool = True):
    return twilio_service.process_approval_response(action_id, approved)

@router.get("/integrations/twilio/pending", tags=["Twilio"])
async def get_pending_approvals():
    return {"pending": twilio_service.get_pending_approvals()}

@router.get("/integrations/twilio/log", tags=["Twilio"])
async def get_sms_log():
    return {"sent_messages": twilio_service.get_sent_log()}

# ═══════════════════════════════════════════
# 🏗️ IoT Devices (Step 59)
# ═══════════════════════════════════════════
@router.post("/iot/command", tags=["IoT"])
async def send_iot_command(cmd: IoTCommand):
    result = await iot_simulator.execute_command(cmd)
    cost_monitor.record_cost("iot", "execute_command", cmd.hotel_id)
    return result

@router.post("/iot/door/unlock-floor", tags=["IoT"])
async def unlock_floor(hotel_id: str, floor: int, authorized_by: str = "system"):
    results = await iot_simulator.unlock_floor(hotel_id, floor, authorized_by)
    cost_monitor.record_cost("iot", "unlock_floor", hotel_id)
    return {"hotel_id": hotel_id, "floor": floor, "doors_processed": len(results), "results": results}

@router.post("/iot/fire/protocol", tags=["IoT"])
async def trigger_fire_protocol(hotel_id: str, floor: int, authorized_by: str = "system"):
    results = await iot_simulator.trigger_fire_protocol(hotel_id, floor, authorized_by)
    cost_monitor.record_cost("iot", "fire_protocol", hotel_id)
    return {"hotel_id": hotel_id, "floor": floor, "protocol": "FIRE_EMERGENCY", "results": results}

@router.get("/iot/devices", tags=["IoT"])
async def get_iot_devices(hotel_id: Optional[str] = None, device_type: Optional[str] = None):
    dt = DeviceType(device_type) if device_type else None
    return {"devices": iot_simulator.get_devices(hotel_id, dt)}

@router.get("/iot/events", tags=["IoT"])
async def get_iot_events(hotel_id: Optional[str] = None, device_id: Optional[str] = None, limit: int = 50):
    return {"events": iot_simulator.get_events(hotel_id, device_id, limit)}

@router.get("/iot/summary/{hotel_id}", tags=["IoT"])
async def get_iot_summary(hotel_id: str):
    return iot_simulator.get_device_summary(hotel_id)

# ═══════════════════════════════════════════
# 🏨 Hotel Database (Steps 60-61)
# ═══════════════════════════════════════════
@router.get("/hotels", tags=["Hotels"])
async def list_hotels():
    cached = cache.get("hotels", "all")
    if cached:
        return {"hotels": cached, "cached": True}
    hotels = hotel_db.get_hotels()
    cache.set("hotels", "all", hotels, ttl=60)
    return {"hotels": hotels, "cached": False}

@router.get("/hotels/{hotel_id}", tags=["Hotels"])
async def get_hotel(hotel_id: str):
    return hotel_db.get_hotel(hotel_id) or {"error": "Hotel not found"}

@router.get("/hotels/{hotel_id}/rooms", tags=["Hotels"])
async def get_rooms(hotel_id: str, status: Optional[str] = None, floor: Optional[int] = None):
    return {"rooms": hotel_db.get_rooms(hotel_id, status, floor)}

@router.get("/hotels/{hotel_id}/bookings", tags=["Hotels"])
async def get_bookings(hotel_id: str, status: Optional[str] = None):
    return {"bookings": hotel_db.get_bookings(hotel_id=hotel_id, status=status)}

@router.post("/hotels/{hotel_id}/bookings", tags=["Hotels"])
async def create_booking(hotel_id: str, booking: Booking):
    booking.hotel_id = hotel_id
    hotel_db.create_booking(booking)
    cache.invalidate_namespace("hotels")
    return {"success": True, "booking_id": booking.booking_id}

@router.get("/hotels/{hotel_id}/incidents", tags=["Hotels"])
async def get_incidents(hotel_id: str, status: Optional[str] = None):
    return {"incidents": hotel_db.get_incidents(hotel_id=hotel_id, status=status)}

@router.post("/hotels/{hotel_id}/incidents", tags=["Hotels"])
async def log_incident(hotel_id: str, incident: IncidentLog):
    incident.hotel_id = hotel_id
    hotel_db.log_incident(incident)
    return {"success": True, "incident_id": incident.incident_id}

@router.get("/hotels/{hotel_id}/finance", tags=["Hotels"])
async def get_finance(hotel_id: str, category: Optional[str] = None):
    return {"records": hotel_db.get_finance_records(hotel_id=hotel_id, category=category)}

@router.get("/hotels/{hotel_id}/finance/summary", tags=["Hotels"])
async def get_finance_summary(hotel_id: str):
    return hotel_db.get_finance_summary(hotel_id)

@router.get("/hotels/{hotel_id}/dashboard", tags=["Hotels"])
async def get_dashboard(hotel_id: str):
    cached = cache.get("dashboard", hotel_id)
    if cached:
        return {**cached, "cached": True}
    stats = hotel_db.get_dashboard_stats(hotel_id)
    cache.set("dashboard", hotel_id, stats, ttl=15)
    return {**stats, "cached": False}

@router.get("/guests", tags=["Hotels"])
async def list_guests(vip_only: bool = False):
    return {"guests": hotel_db.get_guests(vip_only)}

@router.get("/guests/{guest_id}", tags=["Hotels"])
async def get_guest(guest_id: str):
    return hotel_db.get_guest(guest_id) or {"error": "Guest not found"}

# ═══════════════════════════════════════════
# 🌐 API Gateway (Step 62)
# ═══════════════════════════════════════════
@router.post("/gateway/execute", tags=["Gateway"])
async def gateway_execute(req: GatewayRequest):
    return await api_gateway.execute(req)

@router.get("/gateway/health", tags=["Gateway"])
async def gateway_health():
    return api_gateway.get_health()

@router.get("/gateway/log", tags=["Gateway"])
async def gateway_log(service: Optional[str] = None, limit: int = 50):
    return {"log": api_gateway.get_log(service, limit)}

@router.post("/gateway/reset/{service}", tags=["Gateway"])
async def reset_circuit_breaker(service: str):
    return {"reset": api_gateway.reset_cb(service)}

# ═══════════════════════════════════════════
# 📊 Cache (Step 63)
# ═══════════════════════════════════════════
@router.get("/cache/stats", tags=["Monitoring"])
async def cache_stats():
    return cache.get_stats()

@router.post("/cache/clear", tags=["Monitoring"])
async def cache_clear():
    cache.clear()
    return {"cleared": True}

# ═══════════════════════════════════════════
# 📈 Usage Tracking (Step 64)
# ═══════════════════════════════════════════
@router.get("/monitoring/usage", tags=["Monitoring"])
async def get_usage_summary():
    return usage_tracker.get_summary()

@router.get("/monitoring/usage/recent", tags=["Monitoring"])
async def get_recent_usage(service: Optional[str] = None, limit: int = 50):
    return {"records": usage_tracker.get_recent(service=service, limit=limit)}

@router.get("/monitoring/usage/rate/{service}", tags=["Monitoring"])
async def check_rate_limit(service: str):
    return usage_tracker.check_rate_limit(service)

# ═══════════════════════════════════════════
# 💰 Cost Monitoring (Step 65)
# ═══════════════════════════════════════════
@router.get("/monitoring/costs", tags=["Monitoring"])
async def get_cost_summary():
    return cost_monitor.get_summary()

@router.get("/monitoring/costs/{hotel_id}", tags=["Monitoring"])
async def get_hotel_costs(hotel_id: str):
    return cost_monitor.get_hotel_costs(hotel_id)

@router.get("/monitoring/costs/recent", tags=["Monitoring"])
async def get_recent_costs(limit: int = 50):
    return {"entries": cost_monitor.get_recent(limit)}
