#!/usr/bin/env python3
"""
Simple script to view events from events.jsonl file.
"""

import json
import sys
import os

EVENTS_FILE = "output/events.jsonl"

def view_events():
    """View events from the events.jsonl file."""
    if not os.path.exists(EVENTS_FILE):
        print(f"❌ Events file not found: {EVENTS_FILE}")
        print("💡 Run the app and generate a project first to create events.")
        return
    
    print(f"📡 Reading events from: {EVENTS_FILE}\n")
    
    events = []
    with open(EVENTS_FILE, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"⚠️  Error parsing event: {e}")
    
    if not events:
        print("❌ No events found in file.")
        return
    
    print(f"✅ Found {len(events)} events\n")
    print("=" * 80)
    
    # Event type summary
    event_types = {}
    for event in events:
        event_type = event.get("event_type", "unknown")
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    print("\n📊 Event Type Summary:")
    print("-" * 80)
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type:30s} : {count:3d}")
    
    print("\n" + "=" * 80)
    print("\n📋 Recent Events (last 10):")
    print("-" * 80)
    
    for i, event in enumerate(events[-10:], 1):
        event_type = event.get("event_type", "unknown")
        event_id = event.get("event_id", "unknown")
        timestamp = event.get("timestamp", "unknown")
        payload = event.get("payload", {})
        
        print(f"\n{i}. {event_type} ({event_id})")
        print(f"   Timestamp: {timestamp}")
        if event_type == "chat.message":
            print(f"   Content: {payload.get('content', 'N/A')[:100]}")
        elif event_type == "fs.write":
            path = payload.get('path', 'N/A')
            language = payload.get('language', 'N/A')
            content_len = len(payload.get('content', ''))
            print(f"   Path: {path}")
            print(f"   Language: {language}")
            print(f"   Content length: {content_len} chars")
        elif event_type == "progress.update":
            step_id = payload.get('step_id', 'N/A')
            status = payload.get('status', 'N/A')
            print(f"   Step: {step_id}, Status: {status}")
        else:
            # Show first 100 chars of payload
            payload_str = json.dumps(payload)[:100]
            print(f"   Payload: {payload_str}...")
    
    print("\n" + "=" * 80)
    print(f"\n💾 Full events saved to: {EVENTS_FILE}")
    print("💡 Events are saved in JSONL format and can be consumed by frontend/backend applications.")
    
    # Option to show full JSON of first event
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        print("\n" + "=" * 80)
        print("\n📄 Full JSON of first event:")
        print("-" * 80)
        print(json.dumps(events[0], indent=2))


if __name__ == "__main__":
    view_events()


