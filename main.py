#!/usr/bin/env python3
"""
Mental Load Tracker - A zero-dependency CLI for tracking cognitive load.
Simplified version: No dataclass fluff, just pure Python dictionaries and logic.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Constants & Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "load.json"

# Default noise words (4+ letters)
BASE_STOP_WORDS = {
    "need", "this", "that", "with", "from", "your", "have", "will", "shall", 
    "should", "about", "around", "house", "some", "they", "been", "also",
    "just", "done", "doing", "going", "make", "take", "then", "them", 
    "their", "these", "those", "which", "where", "there", "here", "when", 
    "while", "after", "before", "really", "very", "much", "many", "more"
}

# Words that convey uncertainty (for fuzzy detection)
FUZZY_KEYWORDS = {
    "maybe", "may", "think", "probably", "possibly", "somehow", "eventually", 
    "figure out", "decide", "could", "should", "would", "might", 
    "sometime", "whenever", "looking into", "?"
}

# ANSI Styles
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"

# --- Logic ---

def is_fuzzy(text):
    return any(k in text.lower() for k in FUZZY_KEYWORDS)

def get_weight_color(weight):
    if weight >= 8: return Style.RED
    if weight >= 5: return Style.YELLOW
    return Style.GREEN

def get_themes(thoughts, ignored):
    stop_words = BASE_STOP_WORDS | ignored
    words_map = {}
    for t in thoughts:
        words = {w.strip(".,!?").lower() for w in t["content"].split() if len(w) > 3 and w.lower() not in stop_words}
        for w in words:
            if w not in words_map: words_map[w] = {"count": 0, "weight": 0, "ids": []}
            words_map[w]["count"] += 1
            words_map[w]["weight"] += t["weight"]
            words_map[w]["ids"].append(t["id"])
    return {k: v for k, v in words_map.items() if v["count"] > 1}

# --- Data ---

def load_data():
    if not DATA_PATH.exists(): return {"thoughts": [], "ignored": []}
    try:
        with DATA_PATH.open("r") as f:
            data = json.load(f)
            # Ensure proper structure
            return data if isinstance(data, dict) else {"thoughts": data, "ignored": []}
    except (json.JSONDecodeError, IOError):
        return {"thoughts": [], "ignored": []}

def save_data(data):
    try:
        with DATA_PATH.open("w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"{Style.RED}Error: {e}{Style.RESET}")

# --- Actions ---

def add(content, weight):
    store = load_data()
    w = weight if weight is not None else 5
    fuzzy = is_fuzzy(content)
    
    new_thought = {
        "id": int(time.time()),
        "content": content,
        "weight": max(1, min(10, w)),
        "fuzzy": fuzzy,
        "created_at": datetime.now().isoformat()
    }
    
    store["thoughts"].append(new_thought)
    save_data(store)
    print(f"{Style.GREEN}✔ Captured{Style.RESET}")

def list_all():
    store = load_data()
    if not store["thoughts"]:
        print(f"{Style.DIM}Your mind is clear.{Style.RESET}")
        return

    print(f"\n{Style.BOLD}{'ID':<12} {'Weight':<8} {'Clarity':<10} {'Thought'}{Style.RESET}")
    print("-" * 60)
    for t in store["thoughts"]:
        color = get_weight_color(t["weight"])
        clarity = f"{Style.MAGENTA}FUZZY{Style.RESET}" if t["fuzzy"] else f"{Style.CYAN}CLEAR{Style.RESET}"
        print(f"{Style.DIM}{t['id']:<12}{Style.RESET} {color}{t['weight']:<8}{Style.RESET} {clarity:<19} {t['content']}")
    print()

def map_load():
    store = load_data()
    if not store["thoughts"]:
        print(f"{Style.DIM}Empty map.{Style.RESET}")
        return

    total_weight = sum(t["weight"] for t in store["thoughts"])
    load_percent = min(100, (total_weight / 100) * 100)

    print(f"\n{Style.BOLD}COGNITIVE LOAD MAP{Style.RESET}")
    bar_width = 40
    filled = int((load_percent / 100) * bar_width)
    bar_color = Style.GREEN if load_percent < 50 else (Style.YELLOW if load_percent < 80 else Style.RED)
    bar = f"{bar_color}{'█' * filled}{Style.DIM}{'░' * (bar_width - filled)}{Style.RESET}"
    print(f"Load: [{bar}] {load_percent:.1f}%\n")

    for t in store["thoughts"]:
        color = get_weight_color(t["weight"])
        prefix = f"{Style.MAGENTA}[?]{Style.RESET} " if t["fuzzy"] else "    "
        print(f"{prefix}{color}{'█' * t['weight']}{Style.RESET} {t['content']}")
    print(f"\n{Style.DIM}Total items: {len(store['thoughts'])} | Total weight: {total_weight}{Style.RESET}\n")

def render_summary():
    store = load_data()
    if not store["thoughts"]:
        print(f"{Style.DIM}Nothing to summarize.{Style.RESET}")
        return

    themes = get_themes(store["thoughts"], set(store.get("ignored", [])))
    total_items = len(store["thoughts"])
    
    print(f"\n{Style.BOLD}COGNITIVE SUMMARY{Style.RESET}")
    themed_ids = {tid for theme in themes.values() for tid in theme["ids"]}
    unique_count = total_items - len(themed_ids)
    frag_index = (len(themes) + unique_count) / total_items if total_items > 0 else 0
    
    status = "CALM" if frag_index < 0.4 else ("SPLIT" if frag_index < 0.7 else "FRAGMENTED")
    color = Style.GREEN if status == "CALM" else (Style.YELLOW if status == "SPLIT" else Style.RED)
    
    print(f"Fragmentation: {color}{status}{Style.RESET} ({frag_index:.2f})")
    print(f"{Style.DIM}{len(themes)} themes | {unique_count} isolated thoughts{Style.RESET}\n")

    if themes:
        print(f"{Style.BOLD}TOP THEMES{Style.RESET}")
        for name, data in sorted(themes.items(), key=lambda x: x[1]["weight"], reverse=True):
            color = get_weight_color(data["weight"])
            bar = "█" * (data["weight"] // data["count"])
            print(f"{color}{bar:<10}{Style.RESET} {Style.BOLD}{name.upper()}{Style.RESET} ({data['count']} items, Weight: {data['weight']})")
    print()

def ignore_words(words):
    store = load_data()
    if not words:
        if not store.get("ignored"): print(f"{Style.DIM}No words ignored.{Style.RESET}")
        else: print(f"{Style.BOLD}Ignored:{Style.RESET}\n{Style.DIM}{', '.join(sorted(store['ignored']))}{Style.RESET}")
        return
    store["ignored"] = list(set(store.get("ignored", [])) | {w.lower() for w in words})
    save_data(store)
    print(f"{Style.GREEN}✔ Ignored: {', '.join(words)}{Style.RESET}")

def clear(target_id):
    store = load_data()
    new_thoughts = [t for t in store["thoughts"] if str(t["id"]) != target_id]
    if len(new_thoughts) == len(store["thoughts"]):
        print(f"{Style.RED}ID {target_id} not found.{Style.RESET}")
    else:
        store["thoughts"] = new_thoughts
        save_data(store)
        print(f"{Style.GREEN}✔ Cleared{Style.RESET}")

def reset():
    if input(f"{Style.RED}{Style.BOLD}Reset all data? (y/N): {Style.RESET}").lower() == 'y':
        save_data({"thoughts": [], "ignored": []})
        print(f"{Style.GREEN}Mind wiped.{Style.RESET}")

def main():
    parser = argparse.ArgumentParser(description="Mental Load Tracker")
    sub = parser.add_subparsers(dest="command")

    add_p = sub.add_parser("add")
    add_p.add_argument("thought")
    add_p.add_argument("-w", "--weight", type=int)

    sub.add_parser("list")
    sub.add_parser("map")
    sub.add_parser("summary")
    sub.add_parser("reset")

    ignore_p = sub.add_parser("ignore")
    ignore_p.add_argument("words", nargs="*")
    
    clear_p = sub.add_parser("clear")
    clear_p.add_argument("id")

    args = parser.parse_args()

    if args.command == "add": add(args.thought, args.weight)
    elif args.command == "list": list_all()
    elif args.command == "map": map_load()
    elif args.command == "summary": render_summary()
    elif args.command == "ignore": ignore_words(args.words)
    elif args.command == "clear": clear(args.id)
    elif args.command == "reset": reset()
    else: parser.print_help()

if __name__ == "__main__":
    main()
