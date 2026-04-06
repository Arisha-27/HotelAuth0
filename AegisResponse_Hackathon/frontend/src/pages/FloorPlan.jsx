import { useState, useRef, useMemo, useCallback } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Text, Line } from '@react-three/drei'
import { ChevronDown, Maximize2, RotateCcw, Eye, Layers, Thermometer, Wifi } from 'lucide-react'
import * as THREE from 'three'
import './FloorPlan.css'

/* ── Room Data per floor ── */
const generateFloorRooms = (floor) => {
  const rooms = []
  const cols = 6
  const rows = 4
  const statuses = ['occupied', 'occupied', 'occupied', 'occupied', 'occupied', 'available', 'maintenance', 'occupied', 'occupied', 'cleaning']
  const guests = ['S. Chen', 'J. Morrison', 'A. Patel', 'M. Torres', 'K. Wagner', null, null, 'L. Kim', 'R. Novak', null]

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      // Skip some cells for corridors
      if (r === 1 && (c === 2 || c === 3)) continue
      if (r === 2 && c === 3) continue

      const idx = r * cols + c
      const roomNum = floor * 100 + idx + 1
      const statusIdx = Math.floor(Math.random() * statuses.length)

      rooms.push({
        id: roomNum,
        col: c,
        row: r,
        status: statuses[statusIdx],
        guest: statuses[statusIdx] === 'occupied' ? guests[Math.floor(Math.random() * guests.length)] : null,
        temp: (20 + Math.random() * 3).toFixed(1),
        humidity: (40 + Math.random() * 20).toFixed(0),
        hvac: statuses[statusIdx] !== 'maintenance',
        lights: statuses[statusIdx] === 'occupied',
      })
    }
  }
  return rooms
}

/* ── 3D Room Component ── */
function Room3D({ room, position, isSelected, onSelect, viewMode }) {
  const meshRef = useRef()
  const [hovered, setHovered] = useState(false)

  const color = useMemo(() => {
    if (isSelected) return '#FF9900'
    if (viewMode === 'thermal') {
      const t = parseFloat(room.temp)
      if (t > 22) return '#E53935'
      if (t > 21) return '#FF9900'
      return '#4A90D9'
    }
    switch (room.status) {
      case 'occupied': return '#3D3520'
      case 'available': return '#1E3D1E'
      case 'maintenance': return '#4D1A1A'
      case 'cleaning': return '#1A2D4D'
      default: return '#2A2A30'
    }
  }, [room, isSelected, viewMode])

  const edgeColor = useMemo(() => {
    if (isSelected) return '#FFB84D'
    if (hovered) return '#8A8A93'
    switch (room.status) {
      case 'occupied': return '#6A5A30'
      case 'available': return '#5A8A5A'
      case 'maintenance': return '#8A4A4A'
      case 'cleaning': return '#4A6A8A'
      default: return '#4A4A50'
    }
  }, [room, isSelected, hovered])

  useFrame(() => {
    if (meshRef.current) {
      const targetY = isSelected ? 0.6 : hovered ? 0.35 : 0.25
      meshRef.current.scale.y = THREE.MathUtils.lerp(meshRef.current.scale.y, 1, 0.1)
      meshRef.current.position.y = THREE.MathUtils.lerp(meshRef.current.position.y, targetY, 0.1)
    }
  })

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        position={[0, 0.25, 0]}
        onPointerEnter={(e) => { e.stopPropagation(); setHovered(true); document.body.style.cursor = 'pointer' }}
        onPointerLeave={() => { setHovered(false); document.body.style.cursor = 'default' }}
        onClick={(e) => { e.stopPropagation(); onSelect(room) }}
      >
        <boxGeometry args={[0.9, 0.5, 0.9]} />
        <meshStandardMaterial
          color={color}
          emissive={isSelected ? '#FF9900' : hovered ? '#3A3520' : '#1A1510'}
          emissiveIntensity={isSelected ? 0.4 : hovered ? 0.3 : 0.15}
          transparent
          opacity={isSelected ? 0.95 : hovered ? 0.9 : 0.75}
          roughness={0.7}
          metalness={0.15}
        />
      </mesh>
      {/* Wireframe edges */}
      <mesh position={[0, 0.25, 0]}>
        <boxGeometry args={[0.9, 0.5, 0.9]} />
        <meshBasicMaterial color={edgeColor} wireframe transparent opacity={0.8} />
      </mesh>
      {/* Room number label */}
      <Text
        position={[0, 0.55, 0]}
        fontSize={0.13}
        color={isSelected ? '#FFB84D' : '#B0B0B8'}
        anchorX="center"
        anchorY="bottom"
      >
        {room.id}
      </Text>
      {/* Status indicator */}
      {room.status === 'occupied' && (
        <mesh position={[0.3, 0.52, 0.3]}>
          <sphereGeometry args={[0.04, 8, 8]} />
          <meshBasicMaterial color={isSelected ? '#FFB84D' : '#B4C4B1'} />
        </mesh>
      )}
      {room.status === 'maintenance' && (
        <mesh position={[0.3, 0.52, 0.3]}>
          <sphereGeometry args={[0.04, 8, 8]} />
          <meshBasicMaterial color="#E53935" />
        </mesh>
      )}
      {/* Glow effect for selected room */}
      {isSelected && (
        <pointLight position={[0, 1, 0]} color="#FF9900" intensity={2} distance={3} />
      )}
    </group>
  )
}

/* ── Floor Plane ── */
function FloorPlane({ cols, rows }) {
  return (
    <group>
      {/* Base floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[cols / 2 - 0.5, -0.01, rows / 2 - 0.5]}>
        <planeGeometry args={[cols + 1, rows + 1]} />
        <meshStandardMaterial color="#0F0F12" roughness={0.95} metalness={0.05} />
      </mesh>
      {/* Grid lines */}
      {Array.from({ length: cols + 2 }).map((_, i) => (
        <Line
          key={`v-${i}`}
          points={[
            [i - 0.5, 0, -0.5],
            [i - 0.5, 0, rows + 0.5],
          ]}
          color="#2A2A30"
          lineWidth={1}
        />
      ))}
      {Array.from({ length: rows + 2 }).map((_, i) => (
        <Line
          key={`h-${i}`}
          points={[
            [-0.5, 0, i - 0.5],
            [cols + 0.5, 0, i - 0.5],
          ]}
          color="#1A1A1D"
          lineWidth={0.5}
        />
      ))}
      {/* Corridor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[cols / 2 - 0.5, 0.001, 0.5]}>
        <planeGeometry args={[cols + 1, 0.3]} />
        <meshStandardMaterial color="#121214" roughness={0.9} />
      </mesh>
    </group>
  )
}

/* ── Walls ── */
function Walls({ cols, rows }) {
  const wallHeight = 0.8
  const wallColor = '#1A1A1D'
  const wireColor = '#2A2A2E'

  return (
    <group>
      {/* Back wall */}
      <mesh position={[cols / 2 - 0.5, wallHeight / 2, -0.5]}>
        <boxGeometry args={[cols + 1, wallHeight, 0.05]} />
        <meshStandardMaterial color={wallColor} transparent opacity={0.3} />
      </mesh>
      <mesh position={[cols / 2 - 0.5, wallHeight / 2, -0.5]}>
        <boxGeometry args={[cols + 1, wallHeight, 0.05]} />
        <meshBasicMaterial color={wireColor} wireframe />
      </mesh>
      {/* Left wall */}
      <mesh position={[-0.5, wallHeight / 2, rows / 2 - 0.5]}>
        <boxGeometry args={[0.05, wallHeight, rows + 1]} />
        <meshStandardMaterial color={wallColor} transparent opacity={0.3} />
      </mesh>
      <mesh position={[-0.5, wallHeight / 2, rows / 2 - 0.5]}>
        <boxGeometry args={[0.05, wallHeight, rows + 1]} />
        <meshBasicMaterial color={wireColor} wireframe />
      </mesh>
    </group>
  )
}

/* ── Scene ── */
function Scene({ rooms, selectedRoom, onSelectRoom, viewMode }) {
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 15, 10]} intensity={1.2} color="#F3F3F4" />
      <directionalLight position={[-5, 8, -5]} intensity={0.5} color="#FFB84D" />
      <pointLight position={[3, 5, 2]} intensity={0.8} color="#FF9900" distance={20} />
      <pointLight position={[0, 3, 0]} intensity={0.4} color="#FFD699" distance={15} />

      <FloorPlane cols={6} rows={4} />
      <Walls cols={6} rows={4} />

      {rooms.map(room => (
        <Room3D
          key={room.id}
          room={room}
          position={[room.col, 0, room.row]}
          isSelected={selectedRoom?.id === room.id}
          onSelect={onSelectRoom}
          viewMode={viewMode}
        />
      ))}

      <OrbitControls
        enablePan
        enableZoom
        enableRotate
        maxPolarAngle={Math.PI / 2.2}
        minPolarAngle={Math.PI / 6}
        maxDistance={15}
        minDistance={4}
        target={[2.5, 0, 1.5]}
      />
    </>
  )
}

/* ── Room Detail Panel ── */
function RoomDetail({ room, onClose }) {
  if (!room) return null

  const statusColors = {
    occupied: { bg: 'var(--accent-primary-dim)', color: 'var(--accent-primary-light)', label: 'OCCUPIED' },
    available: { bg: 'var(--status-positive-dim)', color: 'var(--status-positive)', label: 'AVAILABLE' },
    maintenance: { bg: 'var(--status-critical-dim)', color: 'var(--status-critical)', label: 'MAINTENANCE' },
    cleaning: { bg: 'rgba(74, 144, 217, 0.15)', color: '#4A90D9', label: 'CLEANING' },
  }

  const s = statusColors[room.status] || statusColors.available

  return (
    <div className="room-detail-panel card">
      <div className="card-header">
        <h3>Room {room.id}</h3>
        <button className="btn btn-ghost" onClick={onClose} style={{ padding: '2px 6px', fontSize: '0.7rem' }}>✕</button>
      </div>
      <div className="card-body">
        <div className="room-detail-status" style={{ background: s.bg, color: s.color }}>
          <span className="status-dot" style={{ background: s.color }} />
          <span className="font-mono">{s.label}</span>
        </div>

        {room.guest && (
          <div className="room-detail-row">
            <span className="room-detail-label">GUEST</span>
            <span className="room-detail-value font-mono">{room.guest}</span>
          </div>
        )}

        <div className="room-detail-row">
          <span className="room-detail-label">TEMPERATURE</span>
          <span className="room-detail-value font-mono">{room.temp}°C</span>
        </div>

        <div className="room-detail-row">
          <span className="room-detail-label">HUMIDITY</span>
          <span className="room-detail-value font-mono">{room.humidity}%</span>
        </div>

        <div className="room-detail-row">
          <span className="room-detail-label">HVAC</span>
          <span className={`room-detail-value font-mono ${room.hvac ? 'text-positive' : 'text-critical'}`}>
            {room.hvac ? 'ACTIVE' : 'FAULT'}
          </span>
        </div>

        <div className="room-detail-row">
          <span className="room-detail-label">LIGHTING</span>
          <span className="room-detail-value font-mono">{room.lights ? 'ON' : 'OFF'}</span>
        </div>

        <div className="room-detail-actions">
          <button className="btn btn-primary" style={{ flex: 1 }}>
            <Wifi size={12} /> CONTROL IOT
          </button>
          <button className="btn" style={{ flex: 1 }}>
            <Eye size={12} /> VIEW CCTV
          </button>
        </div>
      </div>
    </div>
  )
}

/* ── Floor Plan Page ── */
export default function FloorPlan() {
  const [currentFloor, setCurrentFloor] = useState(7)
  const [selectedRoom, setSelectedRoom] = useState(null)
  const [viewMode, setViewMode] = useState('default') // default, thermal, occupancy
  const [showFloorPicker, setShowFloorPicker] = useState(false)

  const rooms = useMemo(() => generateFloorRooms(currentFloor), [currentFloor])

  const stats = useMemo(() => {
    const occupied = rooms.filter(r => r.status === 'occupied').length
    const available = rooms.filter(r => r.status === 'available').length
    const maintenance = rooms.filter(r => r.status === 'maintenance').length
    return { total: rooms.length, occupied, available, maintenance }
  }, [rooms])

  return (
    <div className="floorplan-page">
      {/* Top Bar */}
      <div className="floorplan-topbar">
        <div className="floorplan-title">
          <Layers size={16} className="text-accent" />
          <h2>3D FLOOR WIREFRAME</h2>
        </div>

        <div className="floorplan-controls">
          {/* View modes */}
          <div className="view-mode-group">
            <button
              className={`btn ${viewMode === 'default' ? 'btn-primary' : ''}`}
              onClick={() => setViewMode('default')}
            >
              <Eye size={12} /> DEFAULT
            </button>
            <button
              className={`btn ${viewMode === 'thermal' ? 'btn-primary' : ''}`}
              onClick={() => setViewMode('thermal')}
            >
              <Thermometer size={12} /> THERMAL
            </button>
          </div>

          {/* Floor selector */}
          <div className="floor-selector-wrap">
            <button
              className="btn"
              onClick={() => setShowFloorPicker(!showFloorPicker)}
            >
              <Layers size={12} />
              <span className="font-mono">LEVEL {currentFloor}</span>
              <ChevronDown size={12} />
            </button>
            {showFloorPicker && (
              <div className="floor-picker card">
                {Array.from({ length: 12 }, (_, i) => i + 1).map(f => (
                  <button
                    key={f}
                    className={`floor-picker-item ${f === currentFloor ? 'active' : ''}`}
                    onClick={() => { setCurrentFloor(f); setShowFloorPicker(false); setSelectedRoom(null) }}
                  >
                    <span className="font-mono">LEVEL {f}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button className="btn" onClick={() => setSelectedRoom(null)}>
            <RotateCcw size={12} /> RESET
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="floorplan-stats">
        <div className="stat-chip">
          <span className="stat-label">TOTAL</span>
          <span className="stat-value font-mono">{stats.total}</span>
        </div>
        <div className="stat-chip">
          <span className="stat-label">OCCUPIED</span>
          <span className="stat-value font-mono text-accent">{stats.occupied}</span>
        </div>
        <div className="stat-chip">
          <span className="stat-label">AVAILABLE</span>
          <span className="stat-value font-mono" style={{ color: 'var(--status-positive)' }}>{stats.available}</span>
        </div>
        <div className="stat-chip">
          <span className="stat-label">MAINTENANCE</span>
          <span className="stat-value font-mono" style={{ color: 'var(--status-critical)' }}>{stats.maintenance}</span>
        </div>
      </div>

      {/* 3D Canvas + Detail */}
      <div className="floorplan-main">
        <div className="floorplan-canvas-container card">
          <Canvas
            camera={{ position: [8, 6, 8], fov: 45 }}
            gl={{ antialias: true, alpha: true }}
            style={{ background: '#0A0A0B' }}
          >
            <Scene
              rooms={rooms}
              selectedRoom={selectedRoom}
              onSelectRoom={setSelectedRoom}
              viewMode={viewMode}
            />
          </Canvas>

          {/* Overlay corner info */}
          <div className="canvas-overlay-info font-mono">
            <span>FLOOR {currentFloor} • {viewMode.toUpperCase()} VIEW</span>
            <span className="text-muted">DRAG TO ROTATE • SCROLL TO ZOOM</span>
          </div>
        </div>

        {selectedRoom && (
          <RoomDetail room={selectedRoom} onClose={() => setSelectedRoom(null)} />
        )}
      </div>
    </div>
  )
}
