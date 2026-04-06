/**
 * Aegis Hospitality OS — API Service Layer
 * Connects every frontend page to the FastAPI backend.
 * All endpoints are proxied through Vite dev server → http://localhost:8000
 */

const API_BASE = '/api/v1';
const CORE_BASE = ''; // Phase 3 core endpoints have no /api/v1 prefix

// ─────────────────────────────────────────
// Generic fetch helper
// ─────────────────────────────────────────
async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`[API] ${options.method || 'GET'} ${url} failed:`, err.message);
    throw err;
  }
}

// ═══════════════════════════════════════════
//  HEALTH & METRICS (Phase 3)
// ═══════════════════════════════════════════
export async function fetchHealth() {
  return apiFetch(`${CORE_BASE}/health`);
}

export async function fetchMetrics() {
  return apiFetch(`${CORE_BASE}/metrics`);
}

// ═══════════════════════════════════════════
//  HOTEL DATABASE (Phase 5)
// ═══════════════════════════════════════════
export async function fetchHotels() {
  return apiFetch(`${API_BASE}/hotels`);
}

export async function fetchHotel(hotelId) {
  return apiFetch(`${API_BASE}/hotels/${hotelId}`);
}

export async function fetchRooms(hotelId, status = null, floor = null) {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (floor) params.set('floor', floor);
  const qs = params.toString() ? `?${params}` : '';
  return apiFetch(`${API_BASE}/hotels/${hotelId}/rooms${qs}`);
}

export async function fetchBookings(hotelId, status = null) {
  const qs = status ? `?status=${status}` : '';
  return apiFetch(`${API_BASE}/hotels/${hotelId}/bookings${qs}`);
}

export async function createBooking(hotelId, bookingData) {
  return apiFetch(`${API_BASE}/hotels/${hotelId}/bookings`, {
    method: 'POST',
    body: JSON.stringify(bookingData),
  });
}

export async function fetchIncidents(hotelId, status = null) {
  const qs = status ? `?status=${status}` : '';
  return apiFetch(`${API_BASE}/hotels/${hotelId}/incidents${qs}`);
}

export async function fetchFinanceRecords(hotelId, category = null) {
  const qs = category ? `?category=${category}` : '';
  return apiFetch(`${API_BASE}/hotels/${hotelId}/finance${qs}`);
}

export async function fetchFinanceSummary(hotelId) {
  return apiFetch(`${API_BASE}/hotels/${hotelId}/finance/summary`);
}

export async function fetchDashboard(hotelId) {
  return apiFetch(`${API_BASE}/hotels/${hotelId}/dashboard`);
}

export async function fetchGuests(vipOnly = false) {
  const qs = vipOnly ? '?vip_only=true' : '';
  return apiFetch(`${API_BASE}/guests${qs}`);
}

export async function fetchGuest(guestId) {
  return apiFetch(`${API_BASE}/guests/${guestId}`);
}

// ═══════════════════════════════════════════
//  AI AGENTS (Phase 4)
// ═══════════════════════════════════════════
export async function fetchAgents() {
  return apiFetch(`${API_BASE}/agents`);
}

export async function fetchAgentHierarchy() {
  return apiFetch(`${API_BASE}/agents/hierarchy`);
}

export async function fetchAgentStatus(agentId) {
  return apiFetch(`${API_BASE}/agents/${agentId}/status`);
}

export async function fetchAgentTrace(agentId, limit = 20) {
  return apiFetch(`${API_BASE}/agents/${agentId}/trace?limit=${limit}`);
}

export async function fetchAgentMemory(agentId) {
  return apiFetch(`${API_BASE}/agents/${agentId}/memory`);
}

export async function executeAgentCommand(message, hotelId = 'hotel-grandview', context = {}) {
  return apiFetch(`${API_BASE}/agents/execute`, {
    method: 'POST',
    body: JSON.stringify({ message, hotel_id: hotelId, context }),
  });
}

export async function directAgentCall(agentId, message, hotelId = 'hotel-grandview') {
  return apiFetch(`${API_BASE}/agents/${agentId}/direct`, {
    method: 'POST',
    body: JSON.stringify({ message, hotel_id: hotelId }),
  });
}

export async function fetchAgentHistory(limit = 20) {
  return apiFetch(`${API_BASE}/agents/history?limit=${limit}`);
}

export async function fetchBrainInfo() {
  return apiFetch(`${API_BASE}/agents/brain/info`);
}

// ═══════════════════════════════════════════
//  IoT DEVICES (Phase 5)
// ═══════════════════════════════════════════
export async function fetchIoTDevices(hotelId = null, deviceType = null) {
  const params = new URLSearchParams();
  if (hotelId) params.set('hotel_id', hotelId);
  if (deviceType) params.set('device_type', deviceType);
  const qs = params.toString() ? `?${params}` : '';
  return apiFetch(`${API_BASE}/iot/devices${qs}`);
}

export async function fetchIoTEvents(hotelId = null, deviceId = null, limit = 50) {
  const params = new URLSearchParams();
  if (hotelId) params.set('hotel_id', hotelId);
  if (deviceId) params.set('device_id', deviceId);
  params.set('limit', limit);
  return apiFetch(`${API_BASE}/iot/events?${params}`);
}

export async function fetchIoTSummary(hotelId) {
  return apiFetch(`${API_BASE}/iot/summary/${hotelId}`);
}

export async function sendIoTCommand(command) {
  return apiFetch(`${API_BASE}/iot/command`, {
    method: 'POST',
    body: JSON.stringify(command),
  });
}

export async function unlockFloor(hotelId, floor, authorizedBy = 'system') {
  return apiFetch(`${API_BASE}/iot/door/unlock-floor?hotel_id=${hotelId}&floor=${floor}&authorized_by=${authorizedBy}`, {
    method: 'POST',
  });
}

export async function triggerFireProtocol(hotelId, floor, authorizedBy = 'system') {
  return apiFetch(`${API_BASE}/iot/fire/protocol?hotel_id=${hotelId}&floor=${floor}&authorized_by=${authorizedBy}`, {
    method: 'POST',
  });
}

// ═══════════════════════════════════════════
//  INTEGRATIONS (Gmail, Notion, Twilio)
// ═══════════════════════════════════════════
export async function sendGmailAlert(alertData) {
  return apiFetch(`${API_BASE}/integrations/gmail/send`, {
    method: 'POST',
    body: JSON.stringify(alertData),
  });
}

export async function fetchGmailLog() {
  return apiFetch(`${API_BASE}/integrations/gmail/log`);
}

export async function createNotionLog(entry) {
  return apiFetch(`${API_BASE}/integrations/notion/log`, {
    method: 'POST',
    body: JSON.stringify(entry),
  });
}

export async function fetchNotionLogs() {
  return apiFetch(`${API_BASE}/integrations/notion/all`);
}

export async function sendSMSAlert(smsData) {
  return apiFetch(`${API_BASE}/integrations/twilio/send`, {
    method: 'POST',
    body: JSON.stringify(smsData),
  });
}

export async function fetchPendingApprovals() {
  return apiFetch(`${API_BASE}/integrations/twilio/pending`);
}

// ═══════════════════════════════════════════
//  GATEWAY (Phase 5)
// ═══════════════════════════════════════════
export async function fetchGatewayHealth() {
  return apiFetch(`${API_BASE}/gateway/health`);
}

export async function fetchGatewayLog(service = null, limit = 50) {
  const params = new URLSearchParams();
  if (service) params.set('service', service);
  params.set('limit', limit);
  return apiFetch(`${API_BASE}/gateway/log?${params}`);
}

// ═══════════════════════════════════════════
//  MONITORING (Phase 5)
// ═══════════════════════════════════════════
export async function fetchUsageSummary() {
  return apiFetch(`${API_BASE}/monitoring/usage`);
}

export async function fetchRecentUsage(service = null, limit = 50) {
  const params = new URLSearchParams();
  if (service) params.set('service', service);
  params.set('limit', limit);
  return apiFetch(`${API_BASE}/monitoring/usage/recent?${params}`);
}

export async function fetchCostSummary() {
  return apiFetch(`${API_BASE}/monitoring/costs`);
}

export async function fetchHotelCosts(hotelId) {
  return apiFetch(`${API_BASE}/monitoring/costs/${hotelId}`);
}

export async function fetchCacheStats() {
  return apiFetch(`${API_BASE}/cache/stats`);
}

export async function clearCache() {
  return apiFetch(`${API_BASE}/cache/clear`, { method: 'POST' });
}

// ═══════════════════════════════════════════
//  PHASE 6: HUMAN-IN-THE-LOOP + SECURITY
// ═══════════════════════════════════════════
const HITL_BASE = '/api/v1/hitl';

// Approval Workflow
export async function interceptAction(actionData) {
  return apiFetch(`${HITL_BASE}/intercept`, {
    method: 'POST',
    body: JSON.stringify(actionData),
  });
}

export async function fetchHITLPendingApprovals(hotelId = null) {
  const qs = hotelId ? `?hotel_id=${hotelId}` : '';
  return apiFetch(`${HITL_BASE}/approvals/pending${qs}`);
}

export async function fetchApproval(approvalId) {
  return apiFetch(`${HITL_BASE}/approvals/${approvalId}`);
}

export async function decideApproval(approvalId, decision) {
  return apiFetch(`${HITL_BASE}/approvals/${approvalId}/decide`, {
    method: 'POST',
    body: JSON.stringify(decision),
  });
}

export async function escalateApproval(approvalId, reason = 'Manual escalation') {
  return apiFetch(`${HITL_BASE}/approvals/${approvalId}/escalate?reason=${encodeURIComponent(reason)}`, {
    method: 'POST',
  });
}

export async function fetchApprovalHistory(limit = 50, status = null) {
  const params = new URLSearchParams();
  params.set('limit', limit);
  if (status) params.set('status', status);
  return apiFetch(`${HITL_BASE}/approvals/history?${params}`);
}

export async function fetchApprovalStats() {
  return apiFetch(`${HITL_BASE}/approvals/stats`);
}

// Step-Up Authentication
export async function verifyStepUp(approvalId, otp) {
  return apiFetch(`${HITL_BASE}/step-up/${approvalId}/verify`, {
    method: 'POST',
    body: JSON.stringify({ otp }),
  });
}

export async function getStepUpOtp(approvalId) {
  return apiFetch(`${HITL_BASE}/step-up/${approvalId}/otp`);
}

// Consent Logs
export async function fetchConsentLog(limit = 50, actionType = null, actor = null) {
  const params = new URLSearchParams();
  params.set('limit', limit);
  if (actionType) params.set('action_type', actionType);
  if (actor) params.set('actor', actor);
  return apiFetch(`${HITL_BASE}/consent/log?${params}`);
}

export async function verifyConsentIntegrity() {
  return apiFetch(`${HITL_BASE}/consent/verify`);
}

export async function fetchConsentStats() {
  return apiFetch(`${HITL_BASE}/consent/stats`);
}

// Anomaly Detection
export async function fetchAnomalyAlerts(limit = 50, threatLevel = null) {
  const params = new URLSearchParams();
  params.set('limit', limit);
  if (threatLevel) params.set('threat_level', threatLevel);
  return apiFetch(`${HITL_BASE}/anomalies?${params}`);
}

export async function acknowledgeAnomaly(alertId, acknowledgedBy = 'admin') {
  return apiFetch(`${HITL_BASE}/anomalies/${alertId}/acknowledge?acknowledged_by=${acknowledgedBy}`, {
    method: 'POST',
  });
}

// Attack Simulation
export async function runAttackSimulation(scenario, hotelId = 'hotel-grandview') {
  return apiFetch(`${HITL_BASE}/attack-sim/run?scenario=${scenario}&hotel_id=${hotelId}`, {
    method: 'POST',
  });
}

export async function runAllSimulations(hotelId = 'hotel-grandview') {
  return apiFetch(`${HITL_BASE}/attack-sim/run-all?hotel_id=${hotelId}`, {
    method: 'POST',
  });
}

export async function fetchSimulationResults(limit = 20) {
  return apiFetch(`${HITL_BASE}/attack-sim/results?limit=${limit}`);
}

// Phase 6 Dashboard
export async function fetchHITLDashboard() {
  return apiFetch(`${HITL_BASE}/dashboard`);
}

// ═══════════════════════════════════════════
//  PHASE 8: ADVANCED FEATURES
// ═══════════════════════════════════════════
const ADV_BASE = '/api/v1/advanced';

// Initialize all features
export async function initializeAdvancedFeatures(hotelId = 'hotel-downtown') {
  return apiFetch(`${ADV_BASE}/initialize?hotel_id=${hotelId}`, { method: 'POST' });
}

// Dashboard
export async function fetchAdvancedDashboard() {
  return apiFetch(`${ADV_BASE}/dashboard`);
}

// Predictive Maintenance (Step 91)
export async function analyzeMaintenace(hotelId = 'hotel-downtown') {
  return apiFetch(`${ADV_BASE}/maintenance/analyze?hotel_id=${hotelId}`, { method: 'POST' });
}
export async function fetchMaintenancePredictions(hotelId = null, priority = null) {
  const params = new URLSearchParams();
  if (hotelId) params.set('hotel_id', hotelId);
  if (priority) params.set('priority', priority);
  return apiFetch(`${ADV_BASE}/maintenance/predictions?${params}`);
}
export async function fetchMaintenanceSummary(hotelId = null) {
  const qs = hotelId ? `?hotel_id=${hotelId}` : '';
  return apiFetch(`${ADV_BASE}/maintenance/summary${qs}`);
}

// Guest Personalization (Step 92)
export async function analyzeGuests(hotelId = 'hotel-downtown') {
  return apiFetch(`${ADV_BASE}/guests/analyze?hotel_id=${hotelId}`, { method: 'POST' });
}
export async function fetchGuestProfiles(tier = null) {
  const qs = tier ? `?tier=${tier}` : '';
  return apiFetch(`${ADV_BASE}/guests/profiles${qs}`);
}
export async function fetchGuestProfile(guestId) {
  return apiFetch(`${ADV_BASE}/guests/profiles/${guestId}`);
}
export async function fetchGuestPersonalizationStats() {
  return apiFetch(`${ADV_BASE}/guests/stats`);
}

// Fraud Detection (Step 93)
export async function scanForFraud(hotelId = 'hotel-downtown') {
  return apiFetch(`${ADV_BASE}/fraud/scan?hotel_id=${hotelId}`, { method: 'POST' });
}
export async function fetchFraudAlerts(hotelId = null, riskLevel = null) {
  const params = new URLSearchParams();
  if (hotelId) params.set('hotel_id', hotelId);
  if (riskLevel) params.set('risk_level', riskLevel);
  return apiFetch(`${ADV_BASE}/fraud/alerts?${params}`);
}
export async function fetchFraudStats() {
  return apiFetch(`${ADV_BASE}/fraud/stats`);
}

// Cross-Hotel Coordination (Step 94)
export async function fetchChainOverview() {
  return apiFetch(`${ADV_BASE}/cross-hotel/overview`);
}
export async function broadcastCrossHotelAlert(sourceHotel, message, severity = 'high') {
  return apiFetch(`${ADV_BASE}/cross-hotel/broadcast`, {
    method: 'POST',
    body: JSON.stringify({ source_hotel: sourceHotel, message, severity }),
  });
}
export async function transferGuestCrossHotel(guestId, fromHotel, toHotel, reason = '') {
  return apiFetch(`${ADV_BASE}/cross-hotel/transfer`, {
    method: 'POST',
    body: JSON.stringify({ guest_id: guestId, from_hotel: fromHotel, to_hotel: toHotel, reason }),
  });
}
export async function fetchCrossHotelEvents(eventType = null) {
  const qs = eventType ? `?event_type=${eventType}` : '';
  return apiFetch(`${ADV_BASE}/cross-hotel/events${qs}`);
}

// Resource Optimization (Step 95)
export async function fetchStaffingOptimization(hotelId = 'hotel-downtown', occupancy = 0.85) {
  return apiFetch(`${ADV_BASE}/optimization/staffing?hotel_id=${hotelId}&occupancy=${occupancy}`);
}
export async function fetchEnergyOptimization(hotelId = 'hotel-downtown') {
  return apiFetch(`${ADV_BASE}/optimization/energy?hotel_id=${hotelId}`);
}
export async function fetchPricingOptimization(hotelId = 'hotel-downtown', occupancy = 0.85) {
  return apiFetch(`${ADV_BASE}/optimization/pricing?hotel_id=${hotelId}&occupancy=${occupancy}`);
}
export async function fetchFullOptimization(hotelId = 'hotel-downtown') {
  return apiFetch(`${ADV_BASE}/optimization/full?hotel_id=${hotelId}`);
}

// AI Explainability (Step 96)
export async function generateExplainabilityDemos() {
  return apiFetch(`${ADV_BASE}/explainability/generate-demos`, { method: 'POST' });
}
export async function fetchExplainabilityEntries(agentId = null) {
  const qs = agentId ? `?agent_id=${agentId}` : '';
  return apiFetch(`${ADV_BASE}/explainability/entries${qs}`);
}

// Chaos Testing (Step 97)
export async function runChaosTest(scenario) {
  return apiFetch(`${ADV_BASE}/chaos/run?scenario=${scenario}`, { method: 'POST' });
}
export async function runAllChaosTests() {
  return apiFetch(`${ADV_BASE}/chaos/run-all`, { method: 'POST' });
}
export async function fetchChaosResults() {
  return apiFetch(`${ADV_BASE}/chaos/results`);
}

