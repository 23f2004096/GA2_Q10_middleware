from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uuid
import time


app = FastAPI()


EMAIL = "23f2004096@ds.study.iitm.ac.in"


# -----------------------------
# Rate Limiter Storage
# -----------------------------

RATE_LIMIT = 15
WINDOW = 10

requests = {}



# -----------------------------
# Rate Limit Middleware
# (PUT FIRST)
# -----------------------------

@app.middleware("http")
async def rate_limit(request: Request, call_next):

    # Allow CORS preflight requests
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


    # Remove requests older than 10 seconds
    requests[client_id] = [
        t for t in requests[client_id]
        if now - t < WINDOW
    ]


    # Block after 15 requests
    if len(requests[client_id]) >= RATE_LIMIT:

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded"
            }
        )


    # Add current request
    requests[client_id].append(now)


    response = await call_next(request)

    return response




# -----------------------------
# Request Context Middleware
# -----------------------------

@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get(
        "X-Request-ID"
    )


    if not request_id:
        request_id = str(uuid.uuid4())


    request.state.request_id = request_id


    response = await call_next(request)


    # Always return request ID
    response.headers["X-Request-ID"] = request_id


    return response




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

    expose_headers=[
        "X-Request-ID"
    ]
)



# -----------------------------
# Endpoint
# -----------------------------

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }