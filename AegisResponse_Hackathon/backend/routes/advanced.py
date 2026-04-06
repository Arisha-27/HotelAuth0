"""
Phase 8 — API Routes: Advanced Features (Steps 91–97)
Exposes predictive maintenance, guest AI, fraud detection,
cross-hotel coordination, resource optimization, explainability, and chaos testing.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

from backend.services.advanced_features import (
    predictive_maintenance, guest_personalization, fraud_detection,
    cross_hotel, resource_optimizer, ai_explainability, chaos_testing,
    ChaosScenario,
)
from backend.logging_config import get_logger

logger = get_logger("routes.advanced")

router = APIRouter(prefix="/api/v1/advanced", tags=["Phase 8: Advanced Features"])


# ═══════════════════════════════════════════
# Step 91: Predictive Maintenance
# ═══════════════════════════════════════════

@router.post("/maintenance/analyze")
async def run_maintenance_analysis(hotel_id: str = "hotel-downtown"):
    """Run predictive maintenance analysis on all IoT devices for a hotel."""
    from backend.integrations.iot_service import iot_simulator
    devices = iot_simulator.get_devices(hotel_id=hotel_id)
    predictions = predictive_maintenance.analyze_devices(devices)
    return {
        "hotel_id": hotel_id,
        "devices_analyzed": len(devices),
        "predictions": [p.model_dump() for p in predictions],
        "summary": predictive_maintenance.get_health_summary(hotel_id),
    }


@router.get("/maintenance/predictions")
async def get_maintenance_predictions(
    hotel_id: str = Query(None),
    priority: str = Query(None),
    limit: int = Query(50),
):
    """Get predictive maintenance predictions."""
    return {"predictions": predictive_maintenance.get_predictions(hotel_id, priority, limit)}


@router.get("/maintenance/summary")
async def get_maintenance_summary(hotel_id: str = Query(None)):
    """Get maintenance health summary."""
    return predictive_maintenance.get_health_summary(hotel_id)


# ═══════════════════════════════════════════
# Step 92: Guest Personalization
# ═══════════════════════════════════════════

@router.post("/guests/analyze")
async def analyze_guests(hotel_id: str = "hotel-downtown"):
    """Run guest personalization analysis on all guests."""
    from backend.database.hotel_db import hotel_db
    guests_raw = hotel_db.get_guests()
    bookings_raw = hotel_db.get_bookings(hotel_id=hotel_id)
    # Convert Pydantic models to dicts
    guests = [g.model_dump() if hasattr(g, 'model_dump') else g for g in guests_raw]
    bookings = [b.model_dump() if hasattr(b, 'model_dump') else b for b in bookings_raw]
    profiles = guest_personalization.analyze_guests(guests, bookings)
    return {
        "guests_analyzed": len(profiles),
        "profiles": profiles,
        "stats": guest_personalization.get_stats(),
    }


@router.get("/guests/profiles")
async def get_guest_profiles(tier: str = Query(None)):
    """Get guest personalization profiles."""
    return {"profiles": guest_personalization.get_all_profiles(tier)}


@router.get("/guests/profiles/{guest_id}")
async def get_guest_profile(guest_id: str):
    """Get a specific guest's personalization profile."""
    profile = guest_personalization.get_profile(guest_id)
    return profile or {"error": "Profile not found — run /analyze first"}


@router.get("/guests/stats")
async def get_guest_stats():
    return guest_personalization.get_stats()


# ═══════════════════════════════════════════
# Step 93: Fraud Detection
# ═══════════════════════════════════════════

@router.post("/fraud/scan")
async def scan_for_fraud(hotel_id: str = "hotel-downtown"):
    """Run fraud detection scan on financial records and access events."""
    from backend.database.hotel_db import hotel_db
    from backend.integrations.iot_service import iot_simulator

    finance_raw = hotel_db.get_finance_records(hotel_id=hotel_id)
    finance = [r.model_dump() if hasattr(r, 'model_dump') else r for r in finance_raw]
    transaction_alerts = fraud_detection.scan_transactions(finance)

    events = iot_simulator.get_events(hotel_id=hotel_id, limit=200)
    access_alerts = fraud_detection.scan_access_patterns(events)

    # Also generate demo alerts if none exist
    demo = []
    if not fraud_detection._alerts:
        demo = fraud_detection.generate_demo_alerts(hotel_id)

    return {
        "hotel_id": hotel_id,
        "transactions_scanned": len(finance),
        "events_scanned": len(events),
        "transaction_alerts": [a.model_dump() for a in transaction_alerts],
        "access_alerts": [a.model_dump() for a in access_alerts],
        "demo_alerts": [a.model_dump() for a in demo],
        "stats": fraud_detection.get_stats(),
    }


@router.get("/fraud/alerts")
async def get_fraud_alerts(
    hotel_id: str = Query(None),
    risk_level: str = Query(None),
    limit: int = Query(50),
):
    """Get fraud detection alerts."""
    return {"alerts": fraud_detection.get_alerts(hotel_id, risk_level, limit)}


@router.get("/fraud/stats")
async def get_fraud_stats():
    return fraud_detection.get_stats()


# ═══════════════════════════════════════════
# Step 94: Cross-Hotel Coordination
# ═══════════════════════════════════════════

@router.get("/cross-hotel/overview")
async def get_chain_overview():
    """Get overview of all hotels in the chain."""
    return cross_hotel.get_chain_overview()


class AlertBroadcastRequest(BaseModel):
    source_hotel: str = "hotel-downtown"
    message: str
    severity: str = "high"

@router.post("/cross-hotel/broadcast")
async def broadcast_alert(req: AlertBroadcastRequest):
    """Broadcast an alert to all other hotels in the chain."""
    evt = cross_hotel.broadcast_alert(req.source_hotel, req.message, req.severity)
    return evt.model_dump()


class GuestTransferRequest(BaseModel):
    guest_id: str
    from_hotel: str
    to_hotel: str
    reason: str = ""

@router.post("/cross-hotel/transfer")
async def transfer_guest(req: GuestTransferRequest):
    """Transfer a guest between hotels."""
    evt = cross_hotel.transfer_guest(req.guest_id, req.from_hotel, req.to_hotel, req.reason)
    return evt.model_dump()


class ResourceShareRequest(BaseModel):
    from_hotel: str
    to_hotel: str
    resource_type: str   # staff, linen, equipment, supplies
    quantity: int

@router.post("/cross-hotel/share-resources")
async def share_resources(req: ResourceShareRequest):
    """Share resources between hotels."""
    evt = cross_hotel.share_resources(req.from_hotel, req.to_hotel, req.resource_type, req.quantity)
    return evt.model_dump()


@router.get("/cross-hotel/events")
async def get_cross_hotel_events(event_type: str = Query(None), limit: int = Query(30)):
    return {"events": cross_hotel.get_events(event_type, limit)}


# ═══════════════════════════════════════════
# Step 95: Resource Optimization
# ═══════════════════════════════════════════

@router.get("/optimization/staffing")
async def optimize_staffing(hotel_id: str = "hotel-downtown", occupancy: float = Query(0.85)):
    return resource_optimizer.optimize_staffing(hotel_id, occupancy)


@router.get("/optimization/energy")
async def optimize_energy(hotel_id: str = "hotel-downtown"):
    return resource_optimizer.optimize_energy(hotel_id)


@router.get("/optimization/pricing")
async def optimize_pricing(hotel_id: str = "hotel-downtown", occupancy: float = Query(0.85)):
    return resource_optimizer.optimize_pricing(hotel_id, occupancy)


@router.get("/optimization/full")
async def get_full_optimization(hotel_id: str = "hotel-downtown"):
    """Get complete optimization analysis (staffing + energy + pricing)."""
    return resource_optimizer.get_full_optimization(hotel_id)


# ═══════════════════════════════════════════
# Step 96: AI Explainability
# ═══════════════════════════════════════════

@router.post("/explainability/generate-demos")
async def generate_explainability_demos():
    """Generate demo AI explainability entries."""
    entries = ai_explainability.generate_demo_explanations()
    return {"generated": len(entries), "explanations": [e.model_dump() for e in entries]}


@router.get("/explainability/entries")
async def get_explainability_entries(agent_id: str = Query(None), limit: int = Query(30)):
    return {"entries": ai_explainability.get_entries(agent_id, limit)}


@router.get("/explainability/stats")
async def get_explainability_stats():
    return ai_explainability.get_stats()


# ═══════════════════════════════════════════
# Step 97: Chaos Testing
# ═══════════════════════════════════════════

@router.post("/chaos/run")
async def run_chaos_test(scenario: ChaosScenario):
    """Run a single chaos testing scenario."""
    result = await chaos_testing.run_scenario(scenario)
    return result.model_dump()


@router.post("/chaos/run-all")
async def run_all_chaos_tests():
    """Run ALL chaos testing scenarios and produce resilience report."""
    return await chaos_testing.run_all()


@router.get("/chaos/results")
async def get_chaos_results(limit: int = Query(20)):
    return {"results": chaos_testing.get_results(limit), "summary": chaos_testing.get_summary()}


# ═══════════════════════════════════════════
# Phase 8 Dashboard
# ═══════════════════════════════════════════

@router.get("/dashboard")
async def advanced_dashboard():
    """Get full Phase 8 Advanced Features dashboard summary."""
    return {
        "predictive_maintenance": predictive_maintenance.get_health_summary(),
        "guest_personalization": guest_personalization.get_stats(),
        "fraud_detection": fraud_detection.get_stats(),
        "cross_hotel": cross_hotel.get_chain_overview(),
        "resource_optimization": resource_optimizer.get_full_optimization(),
        "ai_explainability": ai_explainability.get_stats(),
        "chaos_testing": chaos_testing.get_summary(),
    }


@router.post("/initialize")
async def initialize_all_features(hotel_id: str = "hotel-downtown"):
    """Initialize all Phase 8 features with demo data for a hotel."""
    from backend.integrations.iot_service import iot_simulator
    from backend.database.hotel_db import hotel_db

    results = {}

    # 91: Predictive Maintenance
    devices = iot_simulator.get_devices(hotel_id=hotel_id)
    preds = predictive_maintenance.analyze_devices(devices)
    results["maintenance"] = {"devices_analyzed": len(devices), "predictions": len(preds)}

    # 92: Guest Personalization
    guests_raw = hotel_db.get_guests()
    guests = [g.model_dump() if hasattr(g, 'model_dump') else g for g in guests_raw]
    bookings_raw = hotel_db.get_bookings(hotel_id=hotel_id)
    bookings = [b.model_dump() if hasattr(b, 'model_dump') else b for b in bookings_raw]
    profiles = guest_personalization.analyze_guests(guests, bookings)
    results["guests"] = {"profiles_generated": len(profiles)}

    # 93: Fraud Detection
    fraud_detection.generate_demo_alerts(hotel_id)
    results["fraud"] = {"demo_alerts_generated": len(fraud_detection._alerts)}

    # 94: Cross-Hotel Events
    cross_hotel.broadcast_alert(hotel_id, "Phase 8 Advanced Features initialized — all systems operational", "info")
    results["cross_hotel"] = {"broadcast_sent": True}

    # 96: AI Explainability
    exps = ai_explainability.generate_demo_explanations()
    results["explainability"] = {"demo_explanations": len(exps)}

    return {"status": "initialized", "hotel_id": hotel_id, "features": results}
