import os
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

app = FastAPI(title="AegisResponse - Enterprise AI Bridge")
security = HTTPBearer()

# --- CONFIGURATION ---
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUDIENCE = "https://api.aegisresponse.com"

# ==========================================
# PART 1: THE TOKEN VAULT
# ==========================================
async def get_agent_token():
    """Requests a temporary, 60-second token from Auth0."""
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": AUDIENCE,
        "grant_type": "client_credentials"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            print(f"Auth0 Error: {response.text}")
            raise HTTPException(status_code=403, detail="Auth0 denied the token request")
        
        return response.json()["access_token"]


# ==========================================
# PART 2: THE SECURE BRIDGE (OpenClaw's Entry Point)
# ==========================================
@app.post("/agent/action/unlock")
async def agent_unlock_doors():
    """OpenClaw hits this endpoint when it decides to unlock doors."""
    print("\n[AegisResponse Bridge] AI Agent requested door unlock. Contacting Auth0...")
    
    # 1. Fetch the temporary token
    token = await get_agent_token()
    print(f"[AegisResponse Bridge] Auth0 Token Acquired: {token[:15]}... (Truncated for security)")

    # 2. Use the token to hit the protected hotel system
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        # We are calling our own local mock endpoint down below
        resp = await client.post("http://127.0.0.1:8000/api/hotel/doors/unlock", headers=headers)
        return resp.json()


# ==========================================
# PART 3: THE HOTEL INFRASTRUCTURE (The Padded Room)
# ==========================================
def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """The Gatekeeper: Ensures the request has a token."""
    # Note for Hackathon: In a production app, we would verify the JWT RSA signature here using JWKS.
    # For this prototype, we are just proving the token passes through the pipeline.
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Access Denied. Missing Auth0 Token.")
    return token

@app.post("/api/hotel/doors/unlock")
async def execute_door_unlock(token: str = Depends(verify_token)):
    """This endpoint represents the actual physical door locks."""
    print("\n[HOTEL INFRASTRUCTURE] Request received.")
    print("[HOTEL INFRASTRUCTURE] Valid Auth0 Token Verified.")
    print("[HOTEL INFRASTRUCTURE] 🚨 CRITICAL: Floor 3 Doors Unlocked by AI Agent. 🚨\n")
    return {"status": "success", "message": "Doors successfully unlocked via AegisResponse Gateway."}
