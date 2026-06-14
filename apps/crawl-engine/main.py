"""
AutoPulse Crawl Engine — FastAPI + Playwright + Multi-AI
Oracle Cloud Infrastructure (OCI) · Python 3.11
# Environment variables (set via OCI instance environment or .env file) — June 2026
"""
from fastapi import FastAPI, BackgroundTasks, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import os
import io
import hashlib
from PIL import Image
from dotenv import load_dotenv
load_dotenv()

from agents.scheduler import AutonomousScheduler
from agents.crawler import AutomotiveCrawler
from agents.enricher import AIEnricher
from agents.news_generator import NewsGenerator
from agents.seed_static_fleet import seed_all as seed_static_fleet
from models.schemas import CrawlRequest, EnrichRequest, NewsRequest, HealthResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("autopulse")

# Global scheduler instance
scheduler: AutonomousScheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start autonomous scheduler on startup"""
    global scheduler
    logger.info("🚀 AutoPulse Crawl Engine starting...")
    if os.getenv("START_SCHEDULER", "1") == "1":
        scheduler = AutonomousScheduler()
        asyncio.create_task(scheduler.start())
        logger.info("✅ Autonomous scheduler launched (24/7 continuous nonstop mode)")
    else:
        logger.info("ℹ️ Autonomous scheduler startup skipped (managed externally)")
    yield
    logger.info("🛑 Shutting down...")
    if scheduler:
        await scheduler.stop()

app = FastAPI(
    title="AutoPulse Crawl Engine",
    description="Autonomous automotive intelligence — Playwright + Multi-AI",
    version="2.0.0",
    lifespan=lifespan,
)

from autopulse.internal_api.routes.admin import router as admin_router
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://autopulse-web.pages.dev",
        "https://autopulse-api.workers.dev",
        "https://autopulse-api.getplacedoff.workers.dev",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "autopulse-webhook-secret-2024")

def verify_secret(x_webhook_secret: str = Header(None)):
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ============================================================
# Routes
# ============================================================

@app.get("/health", response_model=HealthResponse)
async def health():
    return {
        "status": "operational",
        "service": "AutoPulse Crawl Engine",
        "version": "2.0.0",
        "scheduler_running": scheduler.running if scheduler else False,
        "cycle_count": scheduler.cycle_count if scheduler else 0,
        "mode": scheduler.mode if scheduler else "starting",
    }

@app.post("/crawl")
async def crawl(request: CrawlRequest, background_tasks: BackgroundTasks,
                x_webhook_secret: str = Header(None)):
    verify_secret(x_webhook_secret)
    background_tasks.add_task(_run_crawl, request)
    return {"message": "Crawl started", "job_id": request.job_id, "url": request.url}

@app.post("/enrich")
async def enrich(request: EnrichRequest, x_webhook_secret: str = Header(None)):
    verify_secret(x_webhook_secret)
    enricher = AIEnricher()
    result = await enricher.enrich(request.raw_html, request.url, request.context)
    return {"result": result}

@app.post("/news")
async def generate_news(request: NewsRequest, background_tasks: BackgroundTasks,
                        x_webhook_secret: str = Header(None)):
    verify_secret(x_webhook_secret)
    background_tasks.add_task(_generate_news_batch, request)
    return {"message": "News generation started", "topics": request.topics}

@app.get("/scheduler/status")
async def scheduler_status():
    if not scheduler:
        return {"status": "not_started"}
    return scheduler.get_status()

@app.post("/scheduler/trigger")
async def trigger_crawl(x_webhook_secret: str = Header(None)):
    verify_secret(x_webhook_secret)
    if scheduler:
        asyncio.create_task(scheduler.run_crawl_cycle())
    return {"message": "Crawl cycle triggered"}

@app.post("/seed")
async def trigger_seed(background_tasks: BackgroundTasks, x_webhook_secret: str = Header(None)):
    """Immediately seed all 180+ static car models into Supabase."""
    verify_secret(x_webhook_secret)
    background_tasks.add_task(_run_seed)
    return {"message": "Static fleet seed started in background"}

# ============================================================
# Background Tasks
# ============================================================

async def _process_and_upload_to_r2(img_url: str, folder: str = "cars") -> str:
    if not img_url or "assets.autopulse.pages.dev" in img_url:
        return img_url
    
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    bucket = os.getenv("R2_BUCKET_NAME", "autopulse-assets")
    
    if not account_id or not api_token:
        logger.warning(f"[R2] Cloudflare credentials missing. Skipping upload for {img_url}")
        return img_url
        
    import httpx
    try:
        # Download image
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(img_url, follow_redirects=True)
            if resp.status_code != 200:
                logger.error(f"[R2] Failed to download image {img_url}, status={resp.status_code}")
                return img_url
            img_bytes = resp.content
            
        # Parse and convert to WebP
        img = Image.open(io.BytesIO(img_bytes))
        phash = hashlib.sha256(img_bytes).hexdigest()[:16]
        
        out_buf = io.BytesIO()
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img.save(out_buf, format="WEBP", quality=95)
        else:
            img.convert("RGB").save(out_buf, format="WEBP", quality=95)
        webp_bytes = out_buf.getvalue()
        
        # Upload to R2
        key = f"{folder}/{phash}.webp"
        r2_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket}/objects/{key}"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "image/webp"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            put_resp = await client.put(r2_url, headers=headers, content=webp_bytes)
            if put_resp.status_code == 200:
                public_url = f"https://assets.autopulse.pages.dev/{key}"
                logger.info(f"[R2] Successfully uploaded {img_url} to {public_url}")
                return public_url
            else:
                logger.error(f"[R2] Failed to upload to R2: {put_resp.status_code} - {put_resp.text}")
                return img_url
    except Exception as e:
        logger.error(f"[R2] Error processing image {img_url}: {e}")
        return img_url

async def _run_crawl(request: CrawlRequest):
    from agents.crawler import AutomotiveCrawler
    from agents.enricher import AIEnricher
    import httpx

    crawler = AutomotiveCrawler()
    enricher = AIEnricher()
    hono_url = os.getenv("HONO_WORKER_URL", "https://autopulse-api.workers.dev")

    try:
        logger.info(f"[Crawl] Starting: {request.url}")
        raw_result = await crawler.crawl(request.url, request.source_type)
        enriched = await enricher.enrich(raw_result.get("html", ""), request.url, request.source_type, raw_result.get("image_mappings"))

        # Process and upload images in enriched['cars'] to R2
        if enriched and "cars" in enriched and isinstance(enriched["cars"], list):
            for car in enriched["cars"]:
                if car.get("thumbnail_url"):
                    car["thumbnail_url"] = await _process_and_upload_to_r2(car["thumbnail_url"], folder="cars")
                if car.get("hero_image_url"):
                    car["hero_image_url"] = await _process_and_upload_to_r2(car["hero_image_url"], folder="cars")

        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(f"{hono_url}/api/webhook/complete", json={
                "job_id": request.job_id,
                "status": "done",
                "result": enriched,
                "items_found": enriched.get("items_found", 0),
                "items_new": enriched.get("items_new", 0),
                "duration_ms": raw_result.get("duration_ms", 0),
            }, headers={"X-Webhook-Secret": WEBHOOK_SECRET})

        logger.info(f"[Crawl] ✅ Complete: {request.url}")
    except Exception as e:
        logger.error(f"[Crawl] ❌ Failed: {e}")
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(f"{hono_url}/api/webhook/complete", json={
                "job_id": request.job_id,
                "status": "failed",
                "error": str(e),
            }, headers={"X-Webhook-Secret": WEBHOOK_SECRET})

async def _generate_news_batch(request: NewsRequest):
    generator = NewsGenerator()
    await generator.generate_and_publish(request.topics)

async def _run_seed():
    try:
        total = await seed_static_fleet()
        logger.info(f'[Seed] Complete — {total} models upserted')
    except Exception as e:
        logger.error(f'[Seed] Failed: {e}')
