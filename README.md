# Aegis Hospitality OS (AHOS) 🏨

![Version](https://img.shields.io/badge/version-5.0.0-blue.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Python Backend](https://img.shields.io/badge/FastAPI-Python_3.10+-009688.svg?logo=fastapi)
![React Frontend](https://img.shields.io/badge/React-Vite_|_Three.js-61DAFB.svg?logo=react)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> **Research-Grade Multi-Agent Hotel Chain Operating System** designed to flawlessly integrate cutting-edge AI agency, deep operational tooling, and human-in-the-loop security into a single, cohesive pane of glass. Originally developed as an advanced Hackathon project.

---

## 📖 Overview

Aegis Hospitality OS brings the power of **hierarchical LLM-agnostic agents** to hospitality management. It operates through various phases of technological evolution:

*   **Phase 3**: Core backend foundation with Auth0 integration, Rate Limiting, Audit Middlewares, and Background Task Orchestrator.
*   **Phase 4**: Hierarchical Agent System. An "Executive" agent delegates to Domain agents (Security, Operations, Finance), backed by a pluggable LLM "Brain" supporting OpenAI, Gemini, Mistral, Ollama, and Mock providers.
*   **Phase 5**: Real-world integrations connecting AHOS to Gmail, Notion, Twilio, and an internal IoT Simulator.
*   **Phase 6**: **Human-in-the-Loop (HITL) & Security**. Ensures critical agent actions require human consent, complete with attack simulations and anomaly detection. 
*   **Phase 8**: Advanced interactive features surfaced in our highly advanced 3D frontend UI.

## ✨ Key Features

1.  **🎛️ 3D Interactive UI**: A Next-generation React frontend utilizing `@react-three/fiber` for an immersive data management experience.
2.  **🧠 Pluggable LLM Brain**: Zero vendor lock-in. Switch via `.env` between OpenAI, Google Gemini, local Ollama models, or a fallback Mock Brain for consistent latency testing.
3.  **🤝 Hierarchical Agents**: Complex operations are digested by the Executive Agent, fragmented to Domain Agents, and executed by specialized Sub-Agents.
4.  **🛡️ Zero-Trust HITL**: Sensitive automated operations generate "Consent Requests." The AI will pause execution via asynchronous polling until a human operator signs off.
5.  **🔗 Cross-Platform Integrations**: Out-of-the-box automated tooling for Slack, Gmail (Email routing), Twilio (SMS), Notion (Database replication).

---

## 🏛️ System Architecture

### 1. High-Level System Communication

```mermaid
graph TD
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff
    classDef api fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    classDef agent fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
    classDef external fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff
    classDef db fill:#64748b,stroke:#334155,stroke-width:2px,color:#fff

    User((User Operator)) -->|Action| UI[React / Vite 3D UI]:::frontend
    UI -->|REST API| Gateway[FastAPI Gateway/Middlewares]:::api
    
    Gateway -->|Auth0 JWT| Auth[Auth0 Verification]:::external
    Gateway -->|Tasks| ExecAgent[Executive Agent]:::agent
    
    ExecAgent <--> AgentRegistry[Agent Registry]:::agent
    ExecAgent <--> Brain[LLM Brain - Pluggable]:::agent
    
    AgentRegistry -->|Spawns| DomainAgents[Domain Agents]:::agent
    DomainAgents -->|Trigger| Integrations[External Integrations]:::external
    Integrations --> IoT(IoT Devices/Simulators):::external
    Integrations --> Tools(Gmail / Notion / Twilio):::external
    
    DomainAgents -->|Query/Mutation| DB[(Local Hotel DB)]:::db
```

### 2. Multi-Agent Hierarchy

The "Brain" orchestration ensures that context isn't lost. High-level requests from operations are systematically broken down.

```mermaid
graph TD
    classDef exec fill:#ef4444,stroke:#b91c1c,stroke-width:2px,color:#fff
    classDef domain fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff
    classDef sub fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff

    EA{Executive Agent}:::exec
    
    SA[Security Domain Agent]:::domain
    OA[Operations Domain Agent]:::domain
    FA[Finance Domain Agent]:::domain
    
    EA -->|Delegates Security| SA
    EA -->|Delegates Ops| OA
    EA -->|Delegates Finance| FA
    
    SA -->|Access Control| Sub1(Access Sub-Agent):::sub
    SA -->|Anomaly Scanning| Sub2(Threat Monitor Sub-Agent):::sub
    
    OA -->|Room Servicing| Sub3(Housekeeping Sub-Agent):::sub
    OA -->|HVAC/IoT| Sub4(IoT Control Sub-Agent):::sub
    
    FA -->|Ledger/Billing| Sub5(Billing Sub-Agent):::sub
    FA -->|Forecasting| Sub6(Analytics Sub-Agent):::sub
```

### 3. Human-in-the-Loop (HITL) Execution Flow

When an AI Agent attempts an operation that alters secure states (e.g., unlocking a secure door, processing a large refund), AHOS pauses and routes through the HITL framework.

```mermaid
sequenceDiagram
    participant U as User / Operator
    participant API as FastAPI Backend
    participant A as Autonomous Agent
    participant Sec as HITL Security Module
    
    U->>API: Initiates High-Risk Prompt
    API->>A: Evaluate Request
    Note over A: Identifies "Risk Scope" > Threshold
    A->>Sec: Pause & Create Consent Request
    Sec-->>API: 202 Accepted (Pending HITL)
    API-->>U: Show Pending Approval UI
    
    U->>API: Approves / Denies Request
    API->>Sec: Resolve Consent Ledger
    
    alt is Approved
        Sec->>A: Unblock Execution Queue
        A->>API: Execute Payload
        API-->>U: 200 OK (Task Completed)
    else is Denied
        Sec->>A: Drop Context / Log Failure
        API-->>U: 403 Forbidden (Blocked)
    end
```

---

## 📁 Repository Structure

```text
AegisResponse_Hackathon/
├── backend/
│   ├── agents/          # Multi-agent AI core (Executive, Domain, Sub-agents)
│   ├── auth/            # Auth0 integrations and JWT validation 
│   ├── database/        # Mock/Local DB connections
│   ├── integrations/    # Connectivity for IoT, Gmail, Notion, Twilio
│   ├── middleware/      # Rate-limiting, Error Handlers, Audit flows
│   ├── monitoring/      # System vitals and logs
│   ├── routes/          # RESTful endpoints grouped chronologically/logically
│   └── services/        # Service mesh & background task queue
│
├── frontend/
│   ├── public/          # Static assets
│   └── src/
│       ├── assets/      # 3d models / image assets
│       ├── components/  # React reusable components
│       ├── pages/       # Route-based views
│       ├── services/    # Frontend API integrations
│       └── App.jsx
│
├── main.py              # Root ASGI entry point targeting /backend
├── requirements.txt     # Python Dependencies
└── .env.example         # Template for environment variables
```

---

## 🚀 Getting Started

### Prerequisites

*   `Python 3.10+`
*   `Node.js 18+` & `npm` or `yarn`
*   [Auth0 Account](https://auth0.com/) for authentication routing

### Environment Setup

1. Copy the example `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate the `.env` with your secure variables. `LLM_PROVIDER` can be left as `mock` for testing without API keys, or switch to `openai` / `gemini` if you supply an `LLM_API_KEY`.

### 1. Launch Backend (FastAPI)
```bash
# Create and activate a Virtual Environment
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install Backend requirements
pip install -r requirements.txt

# Run Uvicorn Server
uvicorn main:app --reload --port 8000
```
*The API Docs will be available at `http://localhost:8000/docs`.*

### 2. Launch Frontend (React + Vite)
```bash
# Navigate to frontend
cd frontend

# Install Node modules
npm install

# Start Vite hot-reload server
npm run dev
```
*The Interactive OS will surface gracefully on `http://localhost:5173`.*

---
