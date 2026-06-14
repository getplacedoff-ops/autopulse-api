from __future__ import annotations
import asyncio
import hashlib
import io
from urllib.parse import urlparse
import httpx
from PIL import Image
import imagehash
from typing import Dict, Any, List
from sqlmodel import select
from autopulse.pipeline.base import StageBase, StageContext
from autopulse.pipeline.registry import register_stage
from autopulse.models import StageName, MediaAsset, Trim, SourceType
from autopulse.vision.classifier import vision_classifier
from autopulse.storage.repo import Repository
from autopulse.storage.redis_client import get_limiter
from autopulse.normalizers.registry import get_normalizer
from autopulse.config.settings import settings
from autopulse.utils.logging import get_logger

log = get_logger("stage.image_verification")

def map_view_to_asset_type(view: str) -> str:
    if view.startswith("exterior"): 
        return "exterior"
    if view.startswith("interior"): 
        return "interior"
    if view == "engine_bay": 
        return "engine"
    if view == "color_swatch": 
        return "color_swatch"
    return "exterior"

@register_stage
class ImageVerificationStage(StageBase):
    stage = StageName.IMAGE
    dependencies = [StageName.SPEC] # Runs AFTER trims are certified
    max_concurrency = 5
    
    def __init__(self, context: StageContext):
        super().__init__(context)
        self.http_client = httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_connections=20))
        self.seen_hashes: set = set() # In-memory dedup for this run
    
    async def upload_to_r2(self, key: str, data: bytes, content_type: str = "image/webp") -> bool:
        account_id = settings.CLOUDFLARE_ACCOUNT_ID
        api_token = settings.CLOUDFLARE_API_TOKEN
        bucket = settings.R2_BUCKET_NAME
        if not account_id or not api_token:
            log.warning("Cloudflare credentials missing. Skipping R2 upload.")
            return False
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket}/objects/{key}"
        headers = {"Authorization": f"Bearer {api_token}", "Content-Type": content_type}
        try:
            resp = await self.http_client.put(url, headers=headers, content=data)
            if resp.status_code == 200:
                log.info("Successfully uploaded media to R2", key=key)
                return True
            log.error("Failed to upload media to R2", key=key, status=resp.status_code, response=resp.text)
            return False
        except Exception as e:
            log.error("Exception during R2 upload", key=key, error=str(e))
            return False
    
    async def execute(self) -> Dict[str, Any]:
        # Get certified trims
        trims = (await self.ctx.repo.session.exec(select(Trim))).all()
        # Filter for certified trims (GOLD status)
        gold_trims = [t for t in trims if t.metadata_ and t.metadata_.get("certification_status") == "GOLD"]
        
        async def process_trim(trim: Trim):
            # Collect candidates
            sources_dict = trim.raw_payload.get("sources", {})
            urls = []
            for src_name, src_payload in sources_dict.items():
                if isinstance(src_payload, dict):
                    try:
                        norm = get_normalizer(src_name)
                        urls.extend(norm._extract_images(src_payload))
                    except Exception:
                        pass
            
            if not urls: 
                return
            
            certified_images = []
            for cand in urls:
                url = cand.get("url")
                if not url: 
                    continue
                
                domain = urlparse(url).netloc
                await get_limiter(domain).acquire()
                
                try:
                    resp = await self.http_client.get(url)
                    if resp.status_code != 200: 
                        continue
                    img_bytes = resp.content
                except Exception: 
                    continue
                
                # Perceptual Hash (Dedup)
                try:
                    img = Image.open(io.BytesIO(img_bytes))
                    phash = str(imagehash.phash(img))
                    if phash in self.seen_hashes: 
                        continue
                    self.seen_hashes.add(phash)
                except Exception: 
                    continue
                
                # Vision Classification
                result = vision_classifier.classify(img_bytes)
                
                # QUALITY GATES
                if not result.contains_car: 
                    continue
                if result.confidence < settings.IMAGE_CONFIDENCE_THRESHOLD: 
                    continue
                
                # Map view to schema type literal
                asset_type = map_view_to_asset_type(result.view)
                
                # Convert to high quality WebP
                try:
                    out_buf = io.BytesIO()
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        img.save(out_buf, format="WEBP", quality=95)
                    else:
                        img.convert("RGB").save(out_buf, format="WEBP", quality=95)
                    webp_bytes = out_buf.getvalue()
                except Exception as e:
                    log.error("Failed to convert image to WebP", url=url, error=str(e))
                    continue

                # Upload to Cloudflare R2
                r2_key = f"trims/{trim.id}/{phash}.webp"
                uploaded = await self.upload_to_r2(r2_key, webp_bytes, "image/webp")
                media_url = f"{settings.R2_PUBLIC_URL}/{r2_key}" if uploaded else url
                
                media_data = {
                    "entity_id": trim.id,
                    "entity_type": "trim",
                    "url": media_url,
                    "type": asset_type,
                    "angle": result.view,
                    "color_name": result.color_name or cand.get("color_hint", "unknown"),
                    "vision_confidence": result.confidence,
                    "is_primary": result.view == "exterior_front",
                    "width": img.width, 
                    "height": img.height,
                    "file_size": len(webp_bytes) if uploaded else len(img_bytes),
                    "source": SourceType.AGGREGATOR,
                    "source_url": url,
                    "source_id": f"media-{trim.slug}-{phash}",
                    "content_hash": phash,
                    "raw_payload": {"vision": result.__dict__}
                }
                await self.upsert_media(media_data)
                certified_images.append(media_data)
            
            # Final Check: Does trim have MIN_REQUIRED_VIEWS?
            views = {m["angle"] for m in certified_images}
            missing = set(settings.MIN_REQUIRED_VIEWS) - views
            if missing:
                log.warning("Trim Missing Views", trim_id=trim.id, missing=missing)
                await self._flag_missing_views(trim.id, missing)
        
        await self.run_batch(gold_trims, process_trim, "Image Verification")
        return {"processed": len(gold_trims), "images_stored": len(self.seen_hashes)}

    async def _flag_missing_views(self, trim_id: Any, missing: set):
        from sqlmodel import select
        from autopulse.models import Trim
        trim = (await self.ctx.repo.session.exec(select(Trim).where(Trim.id == trim_id))).first()
        if trim:
            meta = dict(trim.metadata_ or {})
            meta["missing_views"] = list(missing)
            trim.metadata_ = meta
            self.ctx.repo.session.add(trim)
            await self.ctx.repo.session.flush()
