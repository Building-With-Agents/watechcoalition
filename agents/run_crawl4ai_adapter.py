import asyncio
import json
from datetime import datetime

from agents.ingestion.sources.crawl4ai_adapter import Crawl4AIAdapter
from agents.common.types.region_config import RegionConfig


async def main():
    adapter = Crawl4AIAdapter()

    health = await adapter.health_check()
    print("\n=== health_check ===")
    print(json.dumps(health, indent=2))

    region = RegionConfig(
        region_id="us-border-elpaso-lascruces",
        display_name="U.S. Border Region - El Paso / Las Cruces",
        query_location="El Paso, TX",
        radius_miles=75,
        states=["TX", "NM"],
        countries=["US"],
        zip_codes=["79901", "88001"],
        sources=["crawl4ai"],
        role_categories=["all"],
        keywords=["jobs", "careers"],
    )

    records = await adapter.fetch(region)
    count = len(records)
    print(f"\n=== fetched count (before saving): {count} ===")

    base_name = "crawl4ai_elpaso_output.json"
    with open(base_name, "w") as f:
        json.dump([r.model_dump(mode="json") for r in records], f, indent=2)
    print(f"Saved to: {base_name}")

    if count > 0:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        timestamped_name = f"crawl4ai_elpaso_output_{ts}.json"
        with open(timestamped_name, "w") as f:
            json.dump([r.model_dump(mode="json") for r in records], f, indent=2)
        print(f"Saved timestamped copy to: {timestamped_name}")

    for r in records[:10]:
        print({
            "external_id": r.external_id,
            "title": r.title,
            "company": r.company,
            "url": r.job_url,
            "source": r.source,
        })


if __name__ == "__main__":
    asyncio.run(main())