from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uuid
import time


app = FastAPI()


EMAIL = "23f2004096@ds.study.iitm.ac.in"


# -----------------------------
# CORS Middleware
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-tabs4t.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)



# -----------------------------
# Rate Limiter Storage
# -----------------------------

RATE_LIMIT = 15
WINDOW = 10

requests = {}



# -----------------------------
# Request Context Middleware
# -----------------------------

@app.middleware("http")
async def request_context(request: Request, call_next):

    # Check incoming X-Request-ID
    request_id = request.headers.get(
        "X-Request-ID"
    )


    # Generate new ID if missing
    if not request_id:
        request_id = str(uuid.uuid4())


    # Store request ID
    request.state.request_id = request_id


    response = await call_next(request)


    # Add request ID to response header
    response.headers["X-Request-ID"] = request_id


    return response




# -----------------------------
# Rate Limit Middleware
# -----------------------------

@app.middleware("http")
async def rate_limit(request: Request, call_next):

    # ======================================
    # CHANGE ADDED HERE
    # Allow CORS preflight OPTIONS request
    # ======================================
    if request.method == "OPTIONS":
        return await call_next(request)



    client_id = request.headers.get(
        "X-Client-Id",
        "unknown"
    )


    now = time.time()


    # Create bucket for new client
    if client_id not in requests:
        requests[client_id] = []



    # Remove expired requests
    requests[client_id] = [
        t for t in requests[client_id]
        if now - t < WINDOW
    ]



    # Check rate limit
    if len(requests[client_id]) >= RATE_LIMIT:

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded"
            }
        )



    # Add current request timestamp
    requests[client_id].append(now)


    return await call_next(request)




# -----------------------------
# API Endpoint
# -----------------------------

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }