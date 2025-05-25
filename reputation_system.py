"""
Enhanced Reputation System for Hard Times: Ottawa.
Handles complex faction relationships, reputation levels, and unlockable benefits.
"""
import random
from typing import Dict, List, Tuple, Set, Optional, Any
import json

class FactionRelationship:
    """Represents the player's relationship with a specific faction."""
    
    def __init__(self, faction_id: str, name: str, description: str):
        self.id = faction_id
        self.name = name
        self.description = description
        self.level = 0  # 0-100 scale
        self.trust = 0  # 0-100 scale
        self.interactions = []
        self.unlocked_benefits = set()
        self.status = "Neutral"  # Neutral, Friendly, Allied, Hostile, etc.
        self.contacts = []  # Key NPCs within this faction
        self.key_interactions = {}  # Historical record of important interactions
        self.conflict_status = {}  # Conflicts with other factions
        
    def add_interaction(self, interaction_type: str, value: int, context: str = None) -> Tuple[int, List[str]]:
        """Add an interaction with this faction and return level change and messages.
        
        Args:
            interaction_type: Type of interaction (helped, promised, etc.)
            value: Value/impact of the interaction
            context: Optional context for the interaction
            
        Returns:
            tuple: (reputation_change, [messages])
        """
        # Track interaction
        timestamp = "Day X"  # Would use actual game time
        self.interactions.append({
            "type": interaction_type,
            "value": value,
            "context": context,
            "timestamp": timestamp
        })
        
        # Calculate impact
        impact = self._calculate_impact(interaction_type, value, context)
        
        # Update relationship
        old_level = self.level
        self.level = max(0, min(100, self.level + impact))
        
        # Update trust separately - trust changes faster but is more volatile
        trust_impact = impact * 1.5
        self.trust = max(0, min(100, self.trust + trust_impact))
        
        # Check for status changes
        messages = []
        new_status = self._determine_status()
        if new_status != self.status:
            messages.append(f"Your status with {self.name} changed to {new_status}.")
            self.status = new_status
            
        # Check for newly unlocked benefits
        new_benefits = self._check_unlocked_benefits()
        if new_benefits:
            for benefit in new_benefits:
                messages.append(f"Unlocked {benefit} with {self.name}.")
            self.unlocked_benefits.update(new_benefits)
        
        return (self.level - old_level, messages)
    
    def _calculate_impact(self, interaction_type: str, value: int, context: str = None) -> float:
        """Calculate the reputation impact of an interaction.
        
        Args:
            interaction_type: Type of interaction
            value: Base value of interaction
            context: Optional context affecting impact
            
        Returns:
            float: Actual impact value
        """
        # Base impact modifiers by interaction type
        type_modifiers = {
            "helped_critical": 2.5,
            "helped_major": 2.0,
            "helped_minor": 1.0,
            "promised_kept": 1.5,
            "promised_broken": -3.0,
            "traded_fair": 0.5,
            "traded_unfair": -1.0,
            "defended": 2.0,
            "insulted": -2.0,
            "betrayed": -5.0,
            "donated": 1.0,
            "stole": -3.0,
            "assaulted": -4.0,
            "default": 1.0
        }
        
        # Context modifiers
        context_modifiers = {
            "public": 1.2,  # Public actions have higher impact
            "crisis": 1.5,  # Actions during crisis matter more
            "celebration": 1.3,  # Festive occasions
            "default": 1.0
        }
        
        # Relationship momentum - bigger changes if relationship was already moving
        last_interactions = self.interactions[-3:] if len(self.interactions) >= 3 else []
        momentum = 1.0
        if last_interactions:
            direction_sum = sum(1 if i["value"] > 0 else -1 for i in last_interactions)
            if direction_sum >= 2 and value > 0:  # Positive momentum
                momentum = 1.2
            elif direction_sum <= -2 and value < 0:  # Negative momentum
                momentum = 1.2
                
        # Calculate final impact
        type_mod = type_modifiers.get(interaction_type, type_modifiers["default"])
        context_mod = context_modifiers.get(context, context_modifiers["default"])
        
        # Diminishing returns at higher levels
        diminishing_factor = 1.0
        if self.level > 50:
            diminishing_factor = 0.8
        if self.level > 75:
            diminishing_factor = 0.6
        if self.level > 90:
            diminishing_factor = 0.3
            
        # Trust affects impact - low trust = lower impact of positive actions
        trust_modifier = 1.0
        if self.trust < 30 and value > 0:
            trust_modifier = 0.7
            
        return value * type_mod * context_mod * momentum * diminishing_factor * trust_modifier
    
    def _determine_status(self) -> str:
        """Determine relationship status based on level and trust."""
        if self.level < 10:
            return "Hostile"
        elif self.level < 30:
            return "Unfriendly"
        elif self.level < 50:
            return "Neutral"
        elif self.level < 70:
            return "Friendly"
        elif self.level < 90:
            return "Allied"
        else:
            return "Dedicated Ally"
            
    def _check_unlocked_benefits(self) -> Set[str]:
        """Check if any new benefits are unlocked with level changes."""
        benefits_map = {
            # Format: min_level: [benefit_ids]
            20: ["basic_trade"],
            40: ["discounted_trade", "basic_services"],
            60: ["faction_quests", "protection", "advanced_services"],
            80: ["special_items", "faction_secrets", "elite_services"],
            95: ["leadership_position", "faction_safehouse"]
        }
        
        new_benefits = set()
        for level, benefits in benefits_map.items():
            if self.level >= level:
                for benefit in benefits:
                    if benefit not in self.unlocked_benefits:
                        new_benefits.add(benefit)
                        
        return new_benefits
        
    def get_conflict_impacts(self, other_factions: Dict[str, 'FactionRelationship']) -> Dict[str, float]:
        """Calculate how relationships with other factions affect this one.
        
        Args:
            other_factions: Dict of other faction relationships
            
        Returns:
            dict: Faction impacts {faction_id: impact_value}
        """
        impacts = {}
        for faction_id, conflict_value in self.conflict_status.items():
            if faction_id in other_factions:
                other_level = other_factions[faction_id].level
                # Positive conflict value means factions are enemies,
                # so high reputation with one harms reputation with the other
                if conflict_value > 0:
                    impact = -0.1 * conflict_value * (other_level / 100)
                # Negative conflict value means factions are allies,
                # so high reputation with one helps reputation with the other
                else:
                    impact = 0.05 * abs(conflict_value) * (other_level / 100)
                impacts[faction_id] = impact
        return impacts
        
    def get_interaction_options(self, player_stats: Dict[str, Any]) -> List[Dict]:
        """Get available interaction options based on reputation level and player stats.
        
        Args:
            player_stats: Player's current stats
            
        Returns:
            list: Available interaction options
        """
        all_options = [
            {
                "id": "basic_greeting",
                "name": "Greet members",
                "description": "Basic friendly interaction",
                "min_level": 0,
                "stats_required": {},
                "outcomes": {"reputation": 1}
            },
            {
                "id": "request_info",
                "name": "Ask for information",
                "description": "Request basic information",
                "min_level": 20,
                "stats_required": {},
                "outcomes": {"reputation": 0, "knowledge": 1}
            },
            {
                "id": "offer_help",
                "name": "Offer assistance",
                "description": "Volunteer to help with faction tasks",
                "min_level": 30,
                "stats_required": {"energy": 30},
                "outcomes": {"reputation": 3, "energy": -20}
            },
            {
                "id": "request_help",
                "name": "Request assistance",
                "description": "Ask faction members for help",
                "min_level": 40,
                "stats_required": {},
                "outcomes": {"reputation": -1, "money": 5}
            },
            {
                "id": "joint_operation",
                "name": "Propose joint operation",
                "description": "Work together with faction on a major task",
                "min_level": 60,
                "stats_required": {"diplomatic_skill": 3},
                "outcomes": {"reputation": 8, "energy": -30, "risk": "high"}
            },
            {
                "id": "faction_quest",
                "name": "Take on faction mission",
                "description": "Accept a special mission for the faction",
                "min_level": 70,
                "stats_required": {"appropriate_skills": 5},
                "outcomes": {"reputation": 10, "xp": 50, "reward": "special"}
            }
        ]
        
        # Filter options based on player stats and reputation level
        available_options = []
        for option in all_options:
            if self.level >= option["min_level"]:
                meets_requirements = True
                for stat, required_value in option["stats_required"].items():
                    if stat in player_stats and player_stats[stat] < required_value:
                        meets_requirements = False
                        break
                if meets_requirements:
                    available_options.append(option)
                    
        return available_options
    
    def serialize(self) -> Dict:
        """Serialize faction data for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "trust": self.trust,
            "status": self.status,
            "unlocked_benefits": list(self.unlocked_benefits),
            "interactions": self.interactions,
            "contacts": self.contacts,
            "key_interactions": self.key_interactions,
            "conflict_status": self.conflict_status
        }
        
    @classmethod
    def deserialize(cls, data: Dict, faction_data: Dict) -> 'FactionRelationship':
        """Create faction from saved data."""
        faction = cls(
            data["id"],
            faction_data.get("name", data["name"]),
            faction_data.get("description", "")
        )
        faction.level = data["level"]
        faction.trust = data["trust"]
        faction.status = data["status"]
        faction.unlocked_benefits = set(data["unlocked_benefits"])
        faction.interactions = data["interactions"]
        faction.contacts = data["contacts"]
        faction.key_interactions = data["key_interactions"]
        faction.conflict_status = data["conflict_status"]
        return faction


class ReputationSystem:
    """Manages player reputation with different factions."""
    
    def __init__(self):
        self.factions = {}
        self.global_reputation = 0  # Overall reputation in the city
        self.personal_notoriety = 0  # How well-known the player is
        self.faction_rivalries = {}  # Tracks relationships between factions
        self._load_factions()
        
    def _load_factions(self, file_path='data/factions.json'):
        """Load faction data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                faction_data = json.load(f)
                
            for faction_id, data in faction_data.items():
                self.factions[faction_id] = FactionRelationship(
                    faction_id=faction_id,
                    name=data["name"],
                    description=data["description"]
                )
                
                # Set up conflicts
                for rival, value in data.get("conflicts", {}).items():
                    self.factions[faction_id].conflict_status[rival] = value
                    
            # Set up global faction rivalries for reference
            self.faction_rivalries = {
                faction_id: {
                    rival: value for rival, value in data.get("conflicts", {}).items()
                } for faction_id, data in faction_data.items()
            }
                
        except FileNotFoundError:
            # Create default factions if file not found
            self._create_default_factions()
        except Exception as e:
            print(f"Error loading factions: {e}")
            self._create_default_factions()
    
    def _create_default_factions(self):
        """Create default factions if data file is missing."""
        default_factions = {
            "shelter_network": {
                "name": "Shelter Network",
                "description": "Coalition of homeless shelters and service providers.",
                "conflicts": {"street_crew": -20, "police": 30}
            },
            "street_crew": {
                "name": "Street Crews",
                "description": "Loose association of people surviving on the streets.",
                "conflicts": {"police": 80, "business_owners": 50, "shelter_network": -20}
            },
            "police": {
                "name": "Ottawa Police",
                "description": "Local law enforcement.",
                "conflicts": {"street_crew": 80, "activists": 40}
            },
            "business_owners": {
                "name": "Business Association",
                "description": "Local business owners in commercial districts.",
                "conflicts": {"street_crew": 50, "activists": 30}
            },
            "social_services": {
                "name": "Social Services",
                "description": "Government social assistance programs.",
                "conflicts": {"street_crew": -10, "activists": -20}
            },
            "activists": {
                "name": "Community Activists",
                "description": "Housing and poverty activists working for systemic change.",
                "conflicts": {"police": 40, "business_owners": 30, "social_services": -20}
            },
            "healthcare_workers": {
                "name": "Healthcare Workers",
                "description": "Medical professionals working with vulnerable populations.",
                "conflicts": {}
            }
        }
        
        for faction_id, data in default_factions.items():
            self.factions[faction_id] = FactionRelationship(
                faction_id=faction_id,
                name=data["name"],
                description=data["description"]
            )
            
            # Set up conflicts
            for rival, value in data.get("conflicts", {}).items():
                self.factions[faction_id].conflict_status[rival] = value
                
        # Set up global faction rivalries for reference
        self.faction_rivalries = {
            faction_id: {
                rival: value for rival, value in data.get("conflicts", {}).items()
            } for faction_id, data in default_factions.items()
        }
    
    def add_interaction(self, faction_id: str, interaction_type: str, 
                       value: int, context: str = None) -> Dict[str, Any]:
        """Add an interaction with a faction and process ripple effects.
        
        Args:
            faction_id: ID of the faction interacted with
            interaction_type: Type of interaction
            value: Impact value
            context: Context of interaction
            
        Returns:
            dict: Results including messages and changes
        """
        if faction_id not in self.factions:
            return {"success": False, "message": f"Unknown faction: {faction_id}"}
            
        # Process primary interaction
        primary_change, messages = self.factions[faction_id].add_interaction(
            interaction_type, value, context
        )
        
        # Calculate notoriety increase
        notoriety_change = abs(value) * 0.2
        if context == "public":
            notoriety_change *= 2
        self.personal_notoriety = min(100, self.personal_notoriety + notoriety_change)
        
        # Update global reputation
        global_change = primary_change * 0.1
        self.global_reputation = max(0, min(100, self.global_reputation + global_change))
        
        # Calculate ripple effects to other factions
        ripple_effects = {}
        for other_id, other_faction in self.factions.items():
            if other_id == faction_id:
                continue
                
            # Check if factions have a relationship
            if faction_id in other_faction.conflict_status:
                conflict_value = other_faction.conflict_status[faction_id]
                
                # Calculate ripple effect
                if conflict_value > 0:  # Rivals
                    ripple_change = -primary_change * (conflict_value / 100) * 0.5
                else:  # Allies
                    ripple_change = primary_change * (abs(conflict_value) / 100) * 0.3
                    
                # Only process significant changes
                if abs(ripple_change) >= 0.5:
                    # Apply the change
                    old_level = other_faction.level
                    other_faction.level = max(0, min(100, other_faction.level + ripple_change))
                    actual_change = other_faction.level - old_level
                    
                    if abs(actual_change) >= 1:
                        ripple_effects[other_id] = actual_change
                        if actual_change < 0:
                            messages.append(f"Your actions have damaged your standing with {other_faction.name}.")
                        else:
                            messages.append(f"Your actions have improved your standing with {other_faction.name}.")
        
        # High notoriety actions affect ALL factions slightly
        if notoriety_change > 5:
            for other_id, other_faction in self.factions.items():
                if other_id != faction_id and other_id not in ripple_effects:
                    small_effect = notoriety_change * 0.1 * (1 if value > 0 else -1)
                    other_faction.level = max(0, min(100, other_faction.level + small_effect))
        
        return {
            "success": True,
            "primary_change": primary_change,
            "global_change": global_change,
            "notoriety_change": notoriety_change,
            "ripple_effects": ripple_effects,
            "messages": messages
        }
    
    def get_faction_status(self, faction_id: str) -> Dict:
        """Get detailed status of relationship with a faction.
        
        Args:
            faction_id: ID of the faction
            
        Returns:
            dict: Status information
        """
        if faction_id not in self.factions:
            return {"error": f"Unknown faction: {faction_id}"}
            
        faction = self.factions[faction_id]
        recent_interactions = faction.interactions[-5:] if faction.interactions else []
        
        return {
            "name": faction.name,
            "level": faction.level,
            "status": faction.status,
            "trust": faction.trust,
            "recent_interactions": recent_interactions,
            "unlocked_benefits": list(faction.unlocked_benefits),
            "contacts": faction.contacts
        }
    
    def get_available_interactions(self, faction_id: str, player_stats: Dict[str, Any]) -> List[Dict]:
        """Get available interactions with a faction.
        
        Args:
            faction_id: ID of the faction
            player_stats: Player's current stats
            
        Returns:
            list: Available interaction options
        """
        if faction_id not in self.factions:
            return []
            
        return self.factions[faction_id].get_interaction_options(player_stats)
    
    def get_faction_benefits(self, faction_id: str) -> Set[str]:
        """Get unlocked benefits with a faction.
        
        Args:
            faction_id: ID of the faction
            
        Returns:
            set: Unlocked benefits
        """
        if faction_id not in self.factions:
            return set()
            
        return self.factions[faction_id].unlocked_benefits
    
    def find_best_faction(self, min_level: int = 0) -> Optional[str]:
        """Find faction with highest reputation.
        
        Args:
            min_level: Minimum reputation level required
            
        Returns:
            str or None: ID of highest-reputation faction, or None if none meet min_level
        """
        best_faction = None
        best_level = min_level - 1
        
        for faction_id, faction in self.factions.items():
            if faction.level > best_level:
                best_level = faction.level
                best_faction = faction_id
                
        return best_faction
    
    def get_status_summary(self) -> Dict:
        """Get summary of reputation with all factions.
        
        Returns:
            dict: Summary of faction relationships
        """
        summary = {
            "global_reputation": self.global_reputation,
            "notoriety": self.personal_notoriety,
            "factions": {}
        }
        
        for faction_id, faction in self.factions.items():
            summary["factions"][faction_id] = {
                "name": faction.name,
                "level": faction.level,
                "status": faction.status
            }
            
        return summary
    
    def get_notification_messages(self) -> List[str]:
        """Get important notification messages about faction relationships.
        
        Returns:
            list: Notification messages
        """
        messages = []
        
        # Check for hostile factions
        hostile_factions = [f.name for f in self.factions.values() if f.status == "Hostile"]
        if hostile_factions:
            if len(hostile_factions) == 1:
                messages.append(f"Warning: {hostile_factions[0]} is openly hostile toward you.")
            else:
                messages.append(f"Warning: {', '.join(hostile_factions)} are openly hostile toward you.")
                
        # Check for new allies
        allied_factions = [f.name for f in self.factions.values() 
                          if f.status in ["Allied", "Dedicated Ally"] and
                          any(i["timestamp"] == "Day X" for i in f.interactions[-3:])]
        if allied_factions:
            if len(allied_factions) == 1:
                messages.append(f"Good news: {allied_factions[0]} now considers you an ally.")
            else:
                messages.append(f"Good news: {', '.join(allied_factions)} now consider you an ally.")
                
        # Check for faction conflicts affecting player
        caught_in_conflicts = []
        for faction_id, faction in self.factions.items():
            if faction.level >= 60:  # Only check for factions where you have good reputation
                for rival_id, conflict_value in faction.conflict_status.items():
                    rival = self.factions.get(rival_id)
                    if rival and conflict_value > 50 and rival.level >= 40:
                        caught_in_conflicts.append((faction.name, rival.name))
                        
        for ally, rival in caught_in_conflicts:
            messages.append(f"Conflict: Your alliance with {ally} is causing tension with {rival}.")
            
        return messages
    
    def serialize(self) -> Dict:
        """Serialize reputation data for saving."""
        return {
            "global_reputation": self.global_reputation,
            "personal_notoriety": self.personal_notoriety,
            "factions": {
                faction_id: faction.serialize()
                for faction_id, faction in self.factions.items()
            }
        }
    
    @classmethod
    def deserialize(cls, data: Dict) -> 'ReputationSystem':
        """Create reputation system from saved data."""
        try:
            # Load faction data for descriptions
            with open('data/factions.json', 'r') as f:
                faction_data = json.load(f)
        except:
            faction_data = {}
            
        system = cls()
        system.global_reputation = data["global_reputation"]
        system.personal_notoriety = data["personal_notoriety"]
        
        system.factions = {}
        for faction_id, faction_data_saved in data["factions"].items():
            system.factions[faction_id] = FactionRelationship.deserialize(
                faction_data_saved,
                faction_data.get(faction_id, {})
            )
            
        return system