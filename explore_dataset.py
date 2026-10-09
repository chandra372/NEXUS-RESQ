import csv
import json
import os
from collections import Counter

dataset_dir = "emergency_dataset"
stages = sorted([d for d in os.listdir(dataset_dir) if d.startswith("stage_")])

print(f"Discovered stages: {stages}")

total_messages = 0
noise_samples = []
emergency_samples = []
all_senders = Counter()

for stage in stages:
    stage_dir = os.path.join(dataset_dir, stage)
    social_dir = os.path.join(stage_dir, "social_and_sms")
    audio_dir = os.path.join(stage_dir, "audio_calls")
    
    # SMS
    sms_file = os.path.join(social_dir, "sms_helpline.csv")
    with open(sms_file, encoding="utf-8") as f:
        sms_rows = list(csv.DictReader(f))
    
    # Twitter
    tw_file = os.path.join(social_dir, "twitter_feed.csv")
    with open(tw_file, encoding="utf-8") as f:
        tw_rows = list(csv.DictReader(f))
        
    # WhatsApp
    wa_file = os.path.join(social_dir, "whatsapp_community.json")
    with open(wa_file, encoding="utf-8") as f:
        wa_data = json.load(f)
        wa_rows = wa_data.get("messages", [])
        
    # Audio
    audio_files = os.listdir(audio_dir) if os.path.exists(audio_dir) else []
    
    print(f"\n--- {stage} ---")
    print(f"SMS: {len(sms_rows)}, Twitter: {len(tw_rows)}, WhatsApp: {len(wa_rows)}, Audio: {len(audio_files)}")
    
    for r in sms_rows:
        all_senders[r.get("sender")] += 1
    for r in tw_rows:
        all_senders[r.get("username")] += 1
    for r in wa_rows:
        all_senders[r.get("sender")] += 1

print("\nSender breakdown top 15:")
for sender, count in all_senders.most_common(15):
    print(f"  {sender}: {count}")

# Check ground truth for the distributions
gt_file = os.path.join(dataset_dir, "ground_truth.json")
with open(gt_file, encoding="utf-8") as f:
    gt = json.load(f)

print("\nGround truth stories:")
for story in gt.get("stories", []):
    print(f"  Incident {story['incident_id']}: {story['name']} ({story['zone']})")
    print(f"    Canonical: {story['canonical_location']}")
    print(f"    Resource: {story['resource']}, Vulnerable: {story['vulnerable']}")
    for stg in ["stage_1", "stage_2", "stage_3"]:
        info = story.get(stg, {})
        print(f"    [{stg}] people: {info.get('people')}, urgency: {info.get('urgency')}, status: {info.get('status')}")

# Ground truth intent counts per stage
for stage, recs in gt.get("stage_records", {}).items():
    intents = Counter(r.get("intent") for r in recs)
    statuses = Counter(r.get("status") for r in recs)
    print(f"\nGT {stage} intents: {dict(intents)}, statuses: {dict(statuses)}")
