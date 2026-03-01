import httpx
import os
from typing import Dict, Any


async def push_dna_update_to_genesis(content_id: str, updated_dna: Dict[str, Any]):
    """
    Sends performance learnings back to Genesis service
    so future content ideation is informed by real results.
    
    Skipped if ENABLE_EXTERNAL_SERVICES=false (standalone mode)
    """
    # Skip if running in standalone mode
    if os.getenv("ENABLE_EXTERNAL_SERVICES", "false").lower() != "true":
        print(f"[Standalone Mode] Skipping Genesis update for {content_id}")
        return
    
    genesis_url = os.getenv("GENESIS_SERVICE_URL")
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{genesis_url}/genesis/performance-update",
                json={"content_id": content_id, **updated_dna},
                timeout=5.0,
            )
        print(f"[Genesis] DNA update pushed for {content_id}")
    except Exception as e:
        print(f"Could not reach Genesis service: {e}")


async def push_timing_to_orbit(content_id: str, best_repost_time: str, predicted_performance: float):
    """
    Sends performance predictions to Orbit for smarter scheduling.
    
    Skipped if ENABLE_EXTERNAL_SERVICES=false (standalone mode)
    """
    # Skip if running in standalone mode
    if os.getenv("ENABLE_EXTERNAL_SERVICES", "false").lower() != "true":
        print(f"[Standalone Mode] Skipping Orbit update for {content_id}")
        return
    
    orbit_url = os.getenv("ORBIT_SERVICE_URL")
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{orbit_url}/orbit/performance-hint",
                json={
                    "content_id": content_id,
                    "predicted_performance": predicted_performance,
                    "best_repost_time": best_repost_time,
                },
                timeout=5.0,
            )
        print(f"[Orbit] Performance hint pushed for {content_id}")
    except Exception as e:
        print(f"Could not reach Orbit service: {e}")
