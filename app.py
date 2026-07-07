from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from collections import defaultdict, deque
from time import monotonic
import uuid

app = FastAPI()

# ============================================================
# 1) CORS SETTINGS
# ============================================================
# Replace the second origin below with the ACTUAL exam page origin
# if your instructor/grader gives it to you.
#
# Why two origins?
# - The assignment says your assigned origin must be allowed.
# - It also says the exam page origin must be allowed for verification.
#
# IMPORTANT:
# - No wildcard "*" allowed.
# - Only these exact origins should receive ACAO headers.
allowed_origins = [
    "https://app-tabs4t.example.com",
    "https://exam-tabs4t.example.com",  # <-- replace if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["X-Request-ID", "X-Client-Id", "Content-Type"],
    expose_headers=["X-Request-ID"],
)

# ============================================================
# 2) RATE LIMIT SETTINGS
# ============================================================
RATE_LIMIT = 15          # 15 requests
RATE_WINDOW_SECONDS = 10 # per 10 seconds

# Store timestamps for each client separately
# Example:
# {
#   "alice": deque([100.1, 101.4, 102.8]),
#   "bob": deque([103.0, 103.2])
# }
client_buckets = defaultdict(deque)


# ============================================================
# 3) REQUEST CONTEXT MIDDLEWARE
# ============================================================
# Job:
# - Reuse X-Request-ID if client sends one
# - Otherwise generate a new UUID
# - Save it in request.state so route handlers can access it
# - Always send it back in the response header
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    # Read request ID from incoming header, if present
    incoming_request_id = request.headers.get("X-Request-ID")

    if incoming_request_id:
        request_id = incoming_request_id
    else:
        request_id = str(uuid.uuid4())

    # Store it on request.state so other code can use it
    request.state.request_id = request_id

    # Continue processing the request
    response = await call_next(request)

    # Always return the same request ID in response header
    response.headers["X-Request-ID"] = request_id
    return response


# ============================================================
# 4) RATE LIMIT MIDDLEWARE
# ============================================================
# Job:
# - Read X-Client-Id
# - Track requests per client independently
# - Allow up to 15 requests in 10 seconds
# - Return 429 if limit exceeded
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # You can choose a fallback value if header is missing.
    # The grader will send X-Client-Id, so this is mostly for safety.
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = monotonic()
    bucket = client_buckets[client_id]

    # Remove old timestamps that are outside the 10-second window
    while bucket and now - bucket[0] > RATE_WINDOW_SECONDS:
        bucket.popleft()

    # If already at limit, reject this request
    if len(bucket) >= RATE_LIMIT:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "request_id": request_id,
            },
            headers={
                "X-Request-ID": request_id
            }
        )

    # Otherwise record this request and continue
    bucket.append(now)

    response = await call_next(request)
    return response


# ============================================================
# 5) /ping ENDPOINT
# ============================================================
# Job:
# - Return your email
# - Return the request_id from middleware
@app.get("/ping")
async def ping(request: Request):
    request_id = request.state.request_id

    return {
        "email": "your-email@example.com",  # <-- replace with your real logged-in email
        "request_id": request_id,
    }


# ============================================================
# 6) OPTIONAL ROOT ENDPOINT
# ============================================================
# Not required for the assignment, but handy for testing.
@app.get("/")
async def home():
    return {"message": "FastAPI middleware stack is running"}


# ============================================================
# 7) RUN LOCALLY
# ============================================================
# Start with:
# uvicorn main:app --reload
#
# Then open:
# http://127.0.0.1:8000/ping