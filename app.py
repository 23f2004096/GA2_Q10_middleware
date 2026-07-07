from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uuid
import time


app = FastAPI()


# -------------------------------
# Your email
# -------------------------------

EMAIL = "23f2004096@ds.study.iitm.ac.in"


# -------------------------------
# Rate limiter settings
# 15 requests / 10 seconds
# -------------------------------

RATE_LIMIT = 15
WINDOW_SECONDS = 10

client_requests = {}



# -------------------------------
# Middleware 1:
# Request Context Middleware
# -------------------------------

@app.middleware("http")
async def request_context(request: Request, call_next):

    # Check incoming request ID

    request_id = request.headers.get("X-Request-ID")


    # If missing create new UUID

    if not request_id:
        request_id = str(uuid.uuid4())


    # Store it inside request state

    request.state.request_id = request_id


    response = await call_next(request)


    # Add response header

    response.headers["X-Request-ID"] = request_id


    return response



# -------------------------------
# Middleware 2:
# Rate Limiting Middleware
# -------------------------------

@app.middleware("http")
async def rate_limit(request: Request, call_next):

    client_id = request.headers.get(
        "X-Client-Id",
        "unknown"
    )


    current_time = time.time()


    if client_id not in client_requests:
        client_requests[client_id] = []


    # Keep only requests inside 10 seconds

    client_requests[client_id] = [
        t for t in client_requests[client_id]
        if current_time - t < WINDOW_SECONDS
    ]


    # Check limit

    if len(client_requests[client_id]) >= RATE_LIMIT:

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded"
            }
        )


    # Save this request time

    client_requests[client_id].append(current_time)


    response = await call_next(request)

    return response



# -------------------------------
# Middleware 3:
# CORS Middleware
# -------------------------------


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "https://app-tabs4t.example.com",
        # exam page origin will also be added if required
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)



# -------------------------------
# API Endpoint
# -------------------------------


@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }