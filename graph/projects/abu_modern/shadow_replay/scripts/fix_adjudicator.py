# Fix shadow_lifecycle_adjudicator.py for Stage04-C1.2.3
import re

path = r'D:\CCXXLESSON\contextledger\graph\projects\abu_modern\shadow_replay\scripts\shadow_lifecycle_adjudicator.py'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old_method = '''    def _determine_relation(
        self,
        event: dict[str, Any],
        new_node: dict[str, Any],
        prev_active: list[dict[str, Any]],
    ) -> str:
        payload = event.get("payload", {})
        new_source = event.get("source", "unknown")
        new_state = (payload.get("state") or "").strip().lower()
        content = (payload.get("content") or "").lower()

        # Provenance conflict: same adj key, different source
        if prev_active:
            prev_source = prev_active[0].get("source", "unknown")
            prev_source = prev_active[0].get("source", "unknown")
            if new_source != prev_source:
                return "CONTESTS"
        # Revival signal
        if "reviv" in content or (new_state in ("in_progress", "open", "implemented", "deployed") and any(
            n.get("state") in ("cancelled", "superseded") for n in prev_active
        )):
            return "REVIVES"

        return "SUPERCEDES"'''

new_method = '''    def _determine_relation(
        self,
        event: dict[str, Any],
        new_node: dict[str, Any],
        prev_active: list[dict[str, Any]],
    ) -> str:
        """Decision contract v2: six-step relation determination.

        Replaces the old 'different source -> CONTESTS' default assumption.
        """
        from datetime import datetime

        payload = event.get("payload", {})
        new_source = event.get("source", "unknown")
        new_state = (payload.get("state") or "").strip().lower()
        content = (payload.get("content") or "").lower()
        new_observed_at = event.get("observed_at", "")
        new_effective_at = event.get("effective_at", "")

        # Step 0: Revival signal check FIRST (before relation determination)
        if "reviv" in content or (new_state in ("in_progress", "open", "implemented", "deployed") and any(
            n.get("state") in ("cancelled", "superseded") for n in prev_active
        )):
            return "REVIVES"

        if not prev_active:
            return "SUPERCEDES"

        prev = prev_active[0]
        prev_source = prev.get("source", "unknown")
        prev_observed_at = prev.get("observed_at", "")
        prev_effective_at = prev.get("effective_at", "")

        # Step 1: Same atomic claim, same scope?
        same_adjudication_key = (
            prev.get("adjudication_key") == new_node.get("adjudication_key")
        )
        same_entity = prev.get("entity_ref") == new_node.get("entity_ref")

        # Step 2: Is there sufficient evidence for state progression?
        # New observed_at is unambiguously later than previous -> supports SUPERCEDES
        time_progression = False
        if new_observed_at and prev_observed_at:
            try:
                new_dt = datetime.fromisoformat(str(new_observed_at).replace("Z", "+00:00"))
                prev_dt = datetime.fromisoformat(str(prev_observed_at).replace("Z", "+00:00"))
                time_progression = new_dt > prev_dt
            except (ValueError, TypeError):
                pass

        # Step 3: Semantic conflict? (same time window, mutually exclusive values)
        semantic_conflict = False
        if time_progression is False and same_entity and same_adjudication_key:
            new_val = (payload.get("value") or "").strip().lower()
            prev_val = (prev.get("state") or "").strip().lower()
            if new_val and prev_val and new_val != prev_val:
                semantic_conflict = True

        # Step 4: Source authority/trustworthiness insufficient to decide?
        source_authority_questionable = False
        if new_source != prev_source:
            # Different source does NOT automatically mean CONTESTS.
            # It only matters if there's a semantic conflict AND no clear time ordering.
            if semantic_conflict and time_progression is False:
                source_authority_questionable = True

        # Step 5: Unresolvable specific conflict?
        if source_authority_questionable and semantic_conflict and not time_progression:
            return "CONTESTS"

        # Step 6: Safe default -> time progression with different source = SUPERCEDES
        # The new claim supersedes the old one because it's temporally later
        # and represents state evolution, not a provenance conflict.
        if time_progression:
            return "SUPERCEDES"

        # No clear time ordering and no semantic conflict -> SUPERCEDES (progression)
        return "SUPERCEDES"'''

if old_method in content:
    content = content.replace(old_method, new_method)
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print("SUCCESS: _determine_relation replaced")
else:
    print("ERROR: Old method not found exactly")
    # Debug: find the method
    idx = content.find('def _determine_relation')
    if idx >= 0:
        print(f"Found at index {idx}")
        print(repr(content[idx:idx+200]))
    else:
        print("Method not found at all")
