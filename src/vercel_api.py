import sys
import os
import logging
from fastapi import FastAPI

# Basic logging setup for this test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

print("--- MINIMAL VERCEL_API.PY: SCRIPT STARTED ---")
logger.info("--- MINIMAL VERCEL_API.PY: SCRIPT STARTED (logger) ---")

# Mark environment as serverless (if needed by Vercel's runtime expectations)
os.environ['VERCEL'] = '1' 

app = FastAPI()
print("--- MINIMAL VERCEL_API.PY: FastAPI app object CREATED ---")
logger.info("--- MINIMAL VERCEL_API.PY: FastAPI app object CREATED (logger) ---")

@app.on_event("startup")
async def minimal_startup_event():
    print("--- MINIMAL VERCEL_API.PY: MINIMAL STARTUP EVENT STARTED (print) ---")
    logger.error("--- MINIMAL VERCEL_API.PY: MINIMAL STARTUP EVENT STARTED (logger.error) ---")
    # Simulate some work
    for i in range(3):
        print(f"Minimal startup: work item {i}")
        logger.info(f"Minimal startup: work item {i} (logger)")
    print("--- MINIMAL VERCEL_API.PY: MINIMAL STARTUP EVENT COMPLETED (print) ---")
    logger.error("--- MINIMAL VERCEL_API.PY: MINIMAL STARTUP EVENT COMPLETED (logger.error) ---")

@app.get("/")
async def root():
    print("--- MINIMAL VERCEL_API.PY: ROOT ROUTE HIT (print) ---")
    logger.info("--- MINIMAL VERCEL_API.PY: ROOT ROUTE HIT (logger) ---")
    return {"message": "Minimal FastAPI app is running!"}

print("--- MINIMAL VERCEL_API.PY: SCRIPT END ---")
logger.info("--- MINIMAL VERCEL_API.PY: SCRIPT END (logger) ---")
