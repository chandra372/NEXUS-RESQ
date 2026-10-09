import sys
import os
import argparse
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ingestion.discovery import DatasetDiscovery
from app.services.stages.stage_engine import stage_engine

def main():
    parser = argparse.ArgumentParser(description="Ingest emergency dataset for NEXUS RESQ")
    parser.add_argument("--stage", type=str, default="all", help="Stage to ingest (e.g. stage_1, or all)")
    args = parser.parse_args()

    discovery = DatasetDiscovery()
    stages = discovery.discover_stages()
    print(f"Discovered stages: {stages}")

    if args.stage == "all":
        target_stages = stages
    else:
        target_stages = [args.stage]

    total_events = 0
    for stg in target_stages:
        events = discovery.ingest_stage(stg, transcribe_audio=True)
        print(f"[{stg}] Ingested {len(events)} events")
        total_events += len(events)

    print(f"\nTotal events ingested across {len(target_stages)} stages: {total_events}")

if __name__ == "__main__":
    main()
