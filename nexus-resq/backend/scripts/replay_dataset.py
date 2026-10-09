import sys
import os
import time
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.stages.stage_engine import stage_engine

def main():
    parser = argparse.ArgumentParser(description="Replay emergency stream through NEXUS RESQ pipeline")
    parser.add_argument("--stages", type=int, default=3, help="Number of stages to replay (1, 2, or 3)")
    parser.add_argument("--speed", type=int, default=10, help="Replay speed multiplier")
    args = parser.parse_args()

    print("==========================================")
    print("NEXUS RESQ - STREAM REPLAY RUNNER")
    print("==========================================")

    for s_idx in range(args.stages):
        stg = stage_engine.current_stage
        print(f"\n--- Processing {stg.upper()} ---")
        t0 = time.time()
        count = stage_engine.process_all_current_stage()
        dur = time.time() - t0

        incidents = stage_engine.memory.get_all_incidents()
        active = sum(1 for i in incidents if not i.is_resolved)
        resolved = sum(1 for i in incidents if i.is_resolved)

        print(f"[{stg}] Processed {count} reports in {dur:.2f}s")
        print(f"Total Incidents Discovered: {len(incidents)} (Active: {active}, Resolved: {resolved})")
        for inc in incidents:
            print(f"  * {inc.incident_id} | {inc.name[:45]} | Status: {inc.status} | Priority: {inc.priority_level} ({inc.priority_score}) | People: {inc.current_people} | Ev: {inc.evidence_count}")

        if s_idx < args.stages - 1:
            print(f"\nAdvancing to next stage...")
            stage_engine.advance_to_next_stage()

    stats = stage_engine.get_overall_stats()
    print("\n==========================================")
    print("REPLAY COMPLETE - SUMMARY STATS")
    print("==========================================")
    print(f"Total Reports Processed: {stats.reports_processed}")
    print(f"Active Incidents:        {stats.active_incidents}")
    print(f"Critical Incidents:      {stats.critical_incidents}")
    print(f"Resolved Incidents:      {stats.resolved_incidents}")
    print(f"Noise Filtered:          {stats.noise_count}")
    print(f"Rumors Detected:         {stats.rumor_count}")

if __name__ == "__main__":
    main()
