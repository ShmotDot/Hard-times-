"""Skills system for Hard Times: Ottawa"""
from typing import Dict, List, Optional

class Skill:
    """Individual skill with level and progress tracking."""
    def __init__(self, name: str, current_level: int = 0):
        self.name = name
        self.level = current_level
        self.xp = 0
        self.bonuses = {}

    def add_xp(self, amount: int) -> bool:
        """Add XP and check for level up."""
        self.xp += amount
        if self.can_level_up():
            return True
        return False

    def can_level_up(self) -> bool:
        """Check if enough XP for level up."""
        required = self.get_required_xp()
        return self.xp >= required

    def get_required_xp(self) -> int:
        """Calculate XP needed for next level."""
        return int(100 * (1.5 ** self.level))

    def level_up(self) -> Dict:
        """Perform level up and return new abilities."""
        if not self.can_level_up():
            return None

        self.level += 1
        self.xp -= self.get_required_xp()

        # Get unlocks from skill tree
        return SKILL_TREES.get(self.name, {}).get('levels', {}).get(self.level, {})

class SkillManager:
    """Manages all player skills and progression."""
    def __init__(self):
        self.skills = {
            "Survival": Skill("Survival"),
            "Diplomacy": Skill("Diplomacy"),
            "Hustle": Skill("Hustle"),
            "Street Knowledge": Skill("Street Knowledge"),
            "Craft": Skill("Craft")
        }

    def add_skill_xp(self, skill_name: str, amount: int) -> Optional[Dict]:
        """Add XP to a skill and handle level ups."""
        if skill_name not in self.skills:
            return None

        skill = self.skills[skill_name]
        if skill.add_xp(amount):
            return skill.level_up()
        return None

    def get_skill_level(self, skill_name: str) -> int:
        """Get current level of a skill."""
        return self.skills[skill_name].level if skill_name in self.skills else 0

    def get_skill_progress(self, skill_name: str) -> float:
        """Get progress percentage to next level."""
        if skill_name not in self.skills:
            return 0.0

        skill = self.skills[skill_name]
        required = skill.get_required_xp()
        return (skill.xp / required) * 100 if required > 0 else 0.0

# Skill Experience Points mapping
SKILL_XP_ACTIONS = {
    "Survival": {
        "sleep_outside": 5,
        "find_food": 3,
        "craft_shelter": 8,
        "weather_survival": 10
    },
    "Diplomacy": {
        "negotiate": 5,
        "persuade": 4,
        "help_others": 3,
        "resolve_conflict": 8
    },
    "Hustle": {
        "successful_trade": 4,
        "find_work": 5,
        "scavenge_value": 3,
        "street_performance": 4
    },
    "Street Knowledge": {
        "explore_area": 3,
        "learn_route": 4,
        "avoid_danger": 6,
        "find_resources": 4
    },
    "Craft": {
        "repair_item": 3,
        "create_item": 5,
        "improve_shelter": 6,
        "salvage_parts": 4
    }
}

# Skill tree definitions
SKILL_TREES = {
    "Survival": {
        "levels": {
            1: {"unlock": "Build Basic Shelter", "bonus": {"heat_retention": 10}},
            2: {"unlock": "Identify Safe Food", "bonus": {"hunger_recovery": 15}},
            3: {"unlock": "Craft Insulation", "bonus": {"heat": 10, "energy_efficiency": 10}},
            4: {"unlock": "Safe Zone Detection", "bonus": {"safety": 15}},
            5: {"unlock": "Community Teacher", "bonus": {"group_reputation": 20, "encampment_stability": 15}}
        }
    },
    "Diplomacy": {
        "levels": {
            1: {"unlock": "De-escalation", "bonus": {"reputation": 10}},
            2: {"unlock": "Shelter Negotiation", "bonus": {"safety": 15}},
            3: {"unlock": "Dispute Mediation", "bonus": {"hope": 10, "reputation": 10}},
            4: {"unlock": "Service Connection", "bonus": {"service_access": 20}},
            5: {"unlock": "Community Leadership", "bonus": {"community_power": 25, "story_progression": 1}}
        }
    },
    "Hustle": {
        "levels": {
            1: {"unlock": "Enhanced Panhandling", "bonus": {"income": 15}},
            2: {"unlock": "Trade Mastery", "bonus": {"trade_value": 20}},
            3: {"unlock": "Safe Scavenging", "bonus": {"money": 15, "health": 10}},
            4: {"unlock": "Bylaw Evasion", "bonus": {"safety": 15}},
            5: {"unlock": "Resource Network", "bonus": {"daily_resources": 25, "group_heat": 10}}
        }
    },
    "Street Knowledge": {
        "levels": {
            1: {"unlock": "Restroom Network", "bonus": {"hygiene": 15}},
            2: {"unlock": "Patrol Pattern Reading", "bonus": {"safety": 20}},
            3: {"unlock": "Threat Detection", "bonus": {"alertness": 25}},
            4: {"unlock": "Service Route Knowledge", "bonus": {"service_access": 15, "health": 10}},
            5: {"unlock": "System Insight", "bonus": {"event_awareness": 20, "story_control": 1}}
        }
    },
    "Craft": {
        "levels": {
            1: {"unlock": "Clothing Repair", "bonus": {"warmth": 15}},
            2: {"unlock": "Basic Crafting", "bonus": {"money": 10, "creativity": 15}},
            3: {"unlock": "Equipment Repair", "bonus": {"safety": 10, "mobility": 15}},
            4: {"unlock": "Comfort Items", "bonus": {"mental_health": 20}},
            5: {"unlock": "Workshop Creation", "bonus": {"hope": 15, "reputation": 15, "story_unlock": 1}}
        }
    }
}