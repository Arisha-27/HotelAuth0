// Mock data for the entire Lunaris system

export const SYSTEM_INFO = {
  name: 'Lunaris',
  version: 'V5.2.1',
  property: 'GRANDVIEW RESORT & SPA',
  totalRooms: 300,
  floors: 12,
};

export const AGENTS = [
  {
    id: 'exec-001',
    name: 'EXECUTIVE AGENT',
    codename: 'NEXUS.AI',
    version: 'v5.2',
    status: 'active',
    type: 'executive',
    cpu: 34,
    memory: 62,
    tasksCompleted: 1847,
    uptime: '99.97%',
    children: [
      {
        id: 'sec-001',
        name: 'SECURITY AGENT',
        codename: 'SENTINEL.AI',
        version: 'v4.1',
        status: 'active',
        type: 'domain',
        cpu: 28,
        memory: 45,
        tasksCompleted: 892,
        uptime: '99.99%',
        children: [
          { id: 'sec-sub-001', name: 'ACCESS CONTROL', codename: 'GATE.AI', version: 'v3.2', status: 'active', type: 'sub', cpu: 12, memory: 18, tasksCompleted: 445, uptime: '99.99%', children: [] },
          { id: 'sec-sub-002', name: 'SURVEILLANCE', codename: 'WATCH.AI', version: 'v3.0', status: 'active', type: 'sub', cpu: 22, memory: 31, tasksCompleted: 312, uptime: '99.98%', children: [] },
          { id: 'sec-sub-003', name: 'THREAT ANALYSIS', codename: 'SHIELD.AI', version: 'v2.8', status: 'idle', type: 'sub', cpu: 3, memory: 8, tasksCompleted: 135, uptime: '99.95%', children: [] },
        ],
      },
      {
        id: 'ops-001',
        name: 'OPERATIONS AGENT',
        codename: 'MAINTAIN.AI',
        version: 'v3.9',
        status: 'active',
        type: 'domain',
        cpu: 41,
        memory: 55,
        tasksCompleted: 2103,
        uptime: '99.96%',
        children: [
          { id: 'ops-sub-001', name: 'HOUSEKEEPING', codename: 'CLEAN.AI', version: 'v2.5', status: 'active', type: 'sub', cpu: 18, memory: 22, tasksCompleted: 1205, uptime: '99.94%', children: [] },
          { id: 'ops-sub-002', name: 'MAINTENANCE', codename: 'FIX.AI', version: 'v2.3', status: 'idle', type: 'sub', cpu: 5, memory: 10, tasksCompleted: 498, uptime: '99.93%', children: [] },
          { id: 'ops-sub-003', name: 'IOT GATEWAY', codename: 'CONNECT.AI', version: 'v3.1', status: 'active', type: 'sub', cpu: 32, memory: 40, tasksCompleted: 400, uptime: '99.97%', children: [] },
        ],
      },
      {
        id: 'fin-001',
        name: 'FINANCE AGENT',
        codename: 'LEDGER.AI',
        version: 'v2.7',
        status: 'idle',
        type: 'domain',
        cpu: 8,
        memory: 15,
        tasksCompleted: 567,
        uptime: '99.99%',
        children: [
          { id: 'fin-sub-001', name: 'REVENUE OPT', codename: 'YIELD.AI', version: 'v2.1', status: 'idle', type: 'sub', cpu: 4, memory: 8, tasksCompleted: 234, uptime: '99.99%', children: [] },
          { id: 'fin-sub-002', name: 'BILLING', codename: 'INVOICE.AI', version: 'v2.0', status: 'idle', type: 'sub', cpu: 2, memory: 5, tasksCompleted: 333, uptime: '99.99%', children: [] },
        ],
      },
      {
        id: 'guest-001',
        name: 'GUEST SERVICES',
        codename: 'HOSPITALITY.AI',
        version: 'v4.1',
        status: 'active',
        type: 'domain',
        cpu: 37,
        memory: 48,
        tasksCompleted: 3201,
        uptime: '99.98%',
        children: [
          { id: 'guest-sub-001', name: 'CONCIERGE', codename: 'CONCIERGE.AI', version: 'v3.5', status: 'active', type: 'sub', cpu: 25, memory: 30, tasksCompleted: 1890, uptime: '99.97%', children: [] },
          { id: 'guest-sub-002', name: 'RESERVATION', codename: 'RESERVE.AI', version: 'v2.0', status: 'idle', type: 'sub', cpu: 6, memory: 12, tasksCompleted: 1311, uptime: '99.99%', children: [] },
        ],
      },
    ],
  },
];

export const LOG_ENTRIES = [
  { time: '22:48:31', agent: 'EXECUTIVE', message: 'Parsed intent "check_room_status_712"', level: 'info' },
  { time: '22:48:30', agent: 'IOT_GATEWAY', message: 'Room 712 — HVAC setpoint adjusted to 22.0°C', level: 'action' },
  { time: '22:48:28', agent: 'CONCIERGE', message: 'Guest S. Chen — late checkout approved (Room 711)', level: 'info' },
  { time: '22:47:45', agent: 'SECURITY', message: 'Access granted: Staff ID #A-2291 → Floor 7 service elevator', level: 'action' },
  { time: '22:47:19', agent: 'CONCIERGE', message: 'Room 502: Check-in confirmed via Concierge.AI', level: 'action' },
  { time: '22:47:03', agent: 'SURVEILLANCE', message: 'Floor 3: Alert — Motion Sensor 3A (Staff corridor)', level: 'warning' },
  { time: '22:46:55', agent: 'MAINTENANCE', message: 'Work order #WO-8821 created: Room 612 HVAC fault detected', level: 'warning' },
  { time: '22:46:40', agent: 'HOUSEKEEPING', message: 'Room 711: Room Service Request "Extra Towels" assigned to Attendant 12', level: 'info' },
  { time: '22:46:22', agent: 'EXECUTIVE', message: 'Task delegation complete → OPERATIONS.MAINTENANCE.FIX_AI', level: 'info' },
  { time: '22:46:10', agent: 'LEDGER', message: 'Revenue report Q4 generated — RevPAR: $287.40', level: 'info' },
  { time: '22:45:58', agent: 'IOT_GATEWAY', message: '10 doors unlocked on Floor 2 (scheduled maintenance window)', level: 'action' },
  { time: '22:45:41', agent: 'SECURITY', message: 'Perimeter scan complete — no anomalies detected', level: 'info' },
  { time: '22:45:30', agent: 'SENTINEL', message: 'CCTV Feed Analysis: Lobby occupancy 34/150 capacity', level: 'info' },
  { time: '22:45:12', agent: 'EXECUTIVE', message: 'System health check — all agents reporting nominal', level: 'info' },
  { time: '22:44:58', agent: 'OPERATIONS', message: 'Email and SMS alerts dispatched — HVAC fault Room 612', level: 'action' },
  { time: '22:44:40', agent: 'RESERVE', message: 'New reservation: Conf #GV-20231027-A — Guest: J. Morrison, Suite 801', level: 'info' },
  { time: '22:44:25', agent: 'CLEAN', message: 'Floor 5: Full turnover complete — 8/8 rooms inspected', level: 'info' },
  { time: '22:44:10', agent: 'SECURITY', message: 'Badge scan anomaly: Guest wristband #W-5501 — double entry Floor 3', level: 'warning' },
  { time: '22:43:55', agent: 'IOT_GATEWAY', message: 'Energy optimization: Dimming corridors Floor 9-12 (low traffic)', level: 'action' },
  { time: '22:43:40', agent: 'EXECUTIVE', message: 'Crisis protocol STANDBY — monitoring Weather Alert (thunderstorm)', level: 'warning' },
];

export const CRITICAL_ALERTS = [
  { id: 'CA-001', room: 'Room 612', issue: 'HVAC Fault', severity: 'high', time: '22:46:55', agent: 'MAINTENANCE' },
  { id: 'CA-002', room: 'Floor 3', issue: 'Motion Sensor Anomaly', severity: 'medium', time: '22:47:03', agent: 'SURVEILLANCE' },
  { id: 'CA-003', room: 'Weather', issue: 'Thunderstorm Warning', severity: 'low', time: '22:43:40', agent: 'EXECUTIVE' },
];

export const ROOMS_DATA = {
  totalRooms: 300,
  occupied: 282,
  available: 12,
  maintenance: 4,
  cleaning: 2,
  occupancyRate: 94,
};

export const FLOOR_DATA = Array.from({ length: 12 }, (_, i) => ({
  floor: i + 1,
  totalRooms: 25,
  occupied: Math.floor(Math.random() * 6) + 19,
  maintenance: Math.floor(Math.random() * 2),
  temperature: (21 + Math.random() * 2).toFixed(1),
  humidity: (45 + Math.random() * 10).toFixed(0),
  energyUsage: (80 + Math.random() * 20).toFixed(1),
}));

export const REVENUE_DATA = [
  { month: 'Jan', revenue: 2400000, revpar: 267 },
  { month: 'Feb', revenue: 2180000, revpar: 259 },
  { month: 'Mar', revenue: 2650000, revpar: 278 },
  { month: 'Apr', revenue: 2890000, revpar: 285 },
  { month: 'May', revenue: 3100000, revpar: 295 },
  { month: 'Jun', revenue: 3350000, revpar: 310 },
  { month: 'Jul', revenue: 3500000, revpar: 322 },
  { month: 'Aug', revenue: 3420000, revpar: 318 },
  { month: 'Sep', revenue: 3100000, revpar: 298 },
  { month: 'Oct', revenue: 2950000, revpar: 287 },
  { month: 'Nov', revenue: 2780000, revpar: 275 },
  { month: 'Dec', revenue: 3200000, revpar: 305 },
];

export const EFFICIENCY_DATA = [
  { day: 'Mon', value: 96.2 },
  { day: 'Tue', value: 97.1 },
  { day: 'Wed', value: 95.8 },
  { day: 'Thu', value: 97.4 },
  { day: 'Fri', value: 96.9 },
  { day: 'Sat', value: 97.8 },
  { day: 'Sun', value: 97.4 },
];

export const SECURITY_EVENTS = [
  { id: 'SE-001', type: 'access_granted', location: 'Main Lobby', person: 'Staff #A-2291', time: '22:47:45', status: 'resolved' },
  { id: 'SE-002', type: 'motion_detected', location: 'Floor 3 Corridor', person: null, time: '22:47:03', status: 'investigating' },
  { id: 'SE-003', type: 'badge_anomaly', location: 'Floor 3 Entry', person: 'Guest #W-5501', time: '22:44:10', status: 'monitoring' },
  { id: 'SE-004', type: 'perimeter_clear', location: 'Exterior', person: null, time: '22:45:41', status: 'resolved' },
  { id: 'SE-005', type: 'access_granted', location: 'Pool Area', person: 'Guest #W-4412', time: '22:42:30', status: 'resolved' },
  { id: 'SE-006', type: 'cctv_analysis', location: 'Lobby', person: null, time: '22:45:30', status: 'resolved' },
];

export const HOUSEKEEPING_TASKS = [
  { id: 'HK-001', room: '711', task: 'Extra Towels', assignee: 'Attendant 12', status: 'in_progress', priority: 'normal' },
  { id: 'HK-002', room: '508', task: 'Full Turnover', assignee: 'Attendant 7', status: 'completed', priority: 'normal' },
  { id: 'HK-003', room: '612', task: 'HVAC Inspection Access', assignee: 'Attendant 3', status: 'pending', priority: 'high' },
  { id: 'HK-004', room: '801', task: 'Suite Prep — VIP Arrival', assignee: 'Attendant 1', status: 'in_progress', priority: 'high' },
  { id: 'HK-005', room: '305', task: 'Mini-bar Restock', assignee: 'Attendant 9', status: 'pending', priority: 'low' },
];

// Floor plan room data for the 3D wireframe
export const FLOOR_PLAN_ROOMS = [
  // Row 1 (top)
  { id: 714, x: 1, y: 0, w: 1, h: 1, status: 'occupied', guest: null, temp: 21.5 },
  { id: 713, x: 2, y: 0, w: 1, h: 1, status: 'occupied', guest: null, temp: 22.0 },
  { id: 715, x: 3, y: 0, w: 1, h: 1, status: 'available', guest: null, temp: 20.0 },
  { id: 720, x: 4, y: 0, w: 1, h: 1, status: 'occupied', guest: null, temp: 21.8 },
  // Row 2
  { id: 701, x: 0, y: 1, w: 1, h: 1, status: 'occupied', guest: null, temp: 22.1 },
  { id: 709, x: 1, y: 1, w: 1, h: 1, status: 'occupied', guest: null, temp: 21.0 },
  { id: 706, x: 2, y: 1, w: 1, h: 1, status: 'maintenance', guest: null, temp: 19.0 },
  { id: 721, x: 4, y: 1, w: 1, h: 1, status: 'occupied', guest: null, temp: 22.3 },
  // Row 3
  { id: 701.1, x: 0, y: 2, w: 1, h: 1, status: 'occupied', guest: null, temp: 21.7, label: '701B' },
  { id: 722, x: 4, y: 2, w: 1, h: 1, status: 'occupied', guest: null, temp: 21.9 },
  // Row 4 - highlighted room
  { id: 711, x: 3, y: 2, w: 1, h: 1, status: 'occupied', guest: 'S. Chen', temp: 21.5, highlight: true },
  { id: 723, x: 4, y: 3, w: 1, h: 1, status: 'occupied', guest: null, temp: 22.0 },
  { id: 724, x: 5, y: 3, w: 1, h: 1, status: 'available', guest: null, temp: 20.0 },
  // Row 5
  { id: 704, x: 0, y: 3, w: 1, h: 1, status: 'occupied', guest: null, temp: 21.4 },
  { id: 712, x: 3, y: 3, w: 1, h: 1, status: 'occupied', guest: null, temp: 22.1 },
  // Row 6
  { id: 703, x: 0, y: 4, w: 1, h: 1, status: 'occupied', guest: null, temp: 21.6 },
  { id: 702, x: 0, y: 5, w: 1, h: 1, status: 'occupied', guest: null, temp: 22.0 },
  { id: 724.1, x: 3, y: 4, w: 1, h: 1, status: 'occupied', guest: null, temp: 21.3, label: '724B' },
  // Row 7
  { id: 700, x: 1, y: 5, w: 1, h: 1, status: 'cleaning', guest: null, temp: 20.5 },
  { id: 723.1, x: 2, y: 5, w: 1, h: 1, status: 'occupied', guest: null, temp: 21.8, label: '723B' },
  { id: 721.1, x: 3, y: 5, w: 1, h: 1, status: 'occupied', guest: null, temp: 22.2, label: '721B' },
];
