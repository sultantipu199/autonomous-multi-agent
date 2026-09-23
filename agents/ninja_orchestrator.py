"""Ninja Content Orchestrator: Multi-Agent High-Ticket Content Engine.

Generates 100% unique, cutting-edge, high-converting content for an Elite High-Ticket Digital Marketing & GenAI Specialist.
Enforces:
1. Stateful persistent memory via `content_vault.json`
2. Deduplication & Memory Audit (Negative Filter > 60% similarity check)
3. Dynamic Permutation across Pillars A, B, C
4. Natural, professional Banglish mix (English tech terms, clean Bangla storytelling)
5. Strict Zero Generic Fluff & Zero Link policy
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


VAULT_FILE = "content_vault.json"


def initialize_vault() -> Dict[str, Any]:
    """Inspects or initializes content_vault.json with required memory arrays."""
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("current_day", 1)
                data.setdefault("completed_days", [])
                data.setdefault("past_topics", [])
                data.setdefault("past_hooks", [])
                data.setdefault("burned_angles", [])
                data.setdefault("used_tactics", [])
                data.setdefault("posts", [])
                return data
        except Exception:
            pass

    default_vault = {
        "metadata": {
            "version": "1.0",
            "persona": "Tipu Sultan | AI & Data-Driven Growth Architect",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        "current_day": 1,
        "completed_days": [],
        "past_topics": [],
        "past_hooks": [],
        "burned_angles": [],
        "used_tactics": [],
        "posts": []
    }
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(default_vault, f, indent=2, ensure_ascii=False)
    return default_vault


def save_vault(vault: Dict[str, Any]):
    """Persists memory state to content_vault.json."""
    vault["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2, ensure_ascii=False)


def get_current_day(vault: Optional[Dict[str, Any]] = None) -> int:
    """Retrieves the active sequential day number from the persistent vault."""
    v = vault or initialize_vault()
    day = v.get("current_day", 1)
    try:
        return max(1, int(day))
    except (ValueError, TypeError):
        return 1


def advance_current_day(completed_day: Optional[int] = None, topic_title: Optional[str] = None) -> int:
    """Advances the sequential day number after successful publication/approval."""
    vault = initialize_vault()
    curr = get_current_day(vault)
    completed = completed_day or curr
    
    if "completed_days" not in vault:
        vault["completed_days"] = []
    
    vault["completed_days"].append({
        "day_number": completed,
        "topic": topic_title or "Untitled Topic",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    next_day = completed + 1
    vault["current_day"] = next_day
    save_vault(vault)
    print(f"[Vault] Advanced to Day {next_day:02d} (Day {completed:02d} marked completed).")
    return next_day


def set_current_day(day_num: int) -> int:
    """Manually resets or aligns the sequential day counter."""
    vault = initialize_vault()
    vault["current_day"] = max(1, int(day_num))
    save_vault(vault)
    print(f"[Vault] Sequential day number manually set to Day {vault['current_day']:02d}.")
    return vault["current_day"]


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculates word-level Jaccard similarity to prevent topic and angle repetition."""
    w1 = set(text1.lower().replace("\n", " ").split())
    w2 = set(text2.lower().replace("\n", " ").split())
    if not w1 or not w2:
        return 0.0
    return len(w1.intersection(w2)) / len(w1.union(w2))


def audit_against_vault(vault: Dict[str, Any], topic: str, hook: str, tactic: str) -> bool:
    """Sentinel / Duplicate Killer: returns True if candidate is fresh (< 60% similarity)."""
    for past_t in vault["past_topics"]:
        if calculate_jaccard_similarity(topic, past_t) > 0.60:
            return False

    for past_h in vault["past_hooks"]:
        if calculate_jaccard_similarity(hook, past_h) > 0.60:
            return False

    if tactic.lower() in [t.lower() for t in vault["used_tactics"]]:
        return False

    return True


def record_post_in_vault(
    vault: Dict[str, Any],
    post_id: str,
    icp: str,
    topic: str,
    hook: str,
    tactic: str,
    angle: str,
    burned_keywords: List[str]
) -> Dict[str, Any]:
    """Appends post records to content_vault.json."""
    record = {
        "post_id": post_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "icp": icp,
        "topic": topic,
        "hook_used": hook,
        "ninja_tactic": tactic,
        "angle": angle,
        "burned_keywords": burned_keywords
    }
    vault["past_topics"].append(topic)
    vault["past_hooks"].append(hook)
    vault["used_tactics"].append(tactic)
    vault["burned_angles"].append(angle)
    vault["posts"].append(record)
    save_vault(vault)
    return record
