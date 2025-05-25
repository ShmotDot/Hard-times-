
"""Combat and conflict system for Hard Times: Ottawa."""
import random
from typing import Dict, List, Tuple

class CombatStyle:
    """Represents a fighting style with specific bonuses and penalties."""
    def __init__(self, name: str, bonuses: Dict[str, float], penalties: Dict[str, float]):
        self.name = name
        self.bonuses = bonuses
        self.penalties = penalties

class CombatSystem:
    """Handles combat and conflict encounters."""
    
    def __init__(self):
        self.threat_levels = {
            "unarmed_civilian": 1,
            "aggressive_drunk": 2,
            "gang_member": 3,
            "police": 4,
            "armed_thug": 5
        }
        
        self.combat_styles = {
            "defensive": CombatStyle(
                "defensive",
                {"damage_reduction": 0.3, "escape_chance": 0.2},
                {"damage_dealt": -0.2}
            ),
            "aggressive": CombatStyle(
                "aggressive",
                {"damage_dealt": 0.3, "intimidation": 0.2},
                {"damage_reduction": -0.2}
            ),
            "evasive": CombatStyle(
                "evasive",
                {"escape_chance": 0.4, "counter_attack": 0.2},
                {"damage_dealt": -0.1}
            ),
            "technical": CombatStyle(
                "technical",
                {"critical_chance": 0.2, "stamina_efficiency": 0.2},
                {"raw_damage": -0.1}
            )
        }
        
        self.defense_options = {
            "retreat": {
                "success_chance": 0.7,
                "energy_cost": 15,
                "heat_if_fail": 10,
                "heat_on_success": 5
            },
            "de_escalate": {
                "success_chance": 0.5,
                "energy_cost": 5,
                "skill_bonus": "persuasion",
                "reputation_gain": 2
            },
            "defend": {
                "success_chance": 0.4,
                "energy_cost": 20,
                "skill_bonus": "survival",
                "injury_chance": 0.3
            },
            "intimidate": {
                "success_chance": 0.3,
                "energy_cost": 25,
                "skill_bonus": "intimidation",
                "street_cred_gain": 5
            }
        }
        
        self.tactical_options = {
            "disarm": {
                "success_chance": 0.3,
                "energy_cost": 30,
                "skill_bonus": "self_defense",
                "advantage_gain": "weapon_removed"
            },
            "create_distance": {
                "success_chance": 0.6,
                "energy_cost": 15,
                "skill_bonus": "survival",
                "advantage_gain": "space_gained"
            },
            "find_weapon": {
                "success_chance": 0.4,
                "energy_cost": 10,
                "skill_bonus": "street_smarts",
                "advantage_gain": "improvised_weapon"
            },
            "call_for_help": {
                "success_chance": 0.5,
                "energy_cost": 20,
                "skill_bonus": "persuasion",
                "advantage_gain": "backup_arrived"
            }
        }
        
        self.injury_types = [
            "bruise",
            "cut",
            "sprain",
            "concussion"
        ]
        
    def handle_combat(self, player, threat_type: str, location, combat_style: str = "defensive") -> Tuple[List, List]:
        """Process a combat encounter with chosen style."""
        threat_level = self.threat_levels.get(threat_type, 1)
        difficulty = threat_level * (1 + (location.danger_level / 10))
        
        # Apply combat style modifiers
        style = self.combat_styles[combat_style]
        for stat, bonus in style.bonuses.items():
            if stat == "damage_reduction":
                difficulty *= (1 - bonus)
            elif stat == "escape_chance":
                self.defense_options["retreat"]["success_chance"] += bonus
                
        # Player condition affects options
        condition_modifier = self._calculate_condition_modifier(player)
        
        options = []
        messages = []
        
        # Generate tactical options based on environment and style
        available_tactics = self._get_available_tactics(location, combat_style)
        for tactic_name, tactic_data in available_tactics.items():
            success_chance = self._calculate_tactic_success(player, tactic_data, condition_modifier)
            options.append((tactic_name, success_chance))
            messages.append(self._get_tactic_description(tactic_name, threat_type))
        
        # Add standard defense options
        for option_name, option_data in self.defense_options.items():
            base_chance = option_data["success_chance"] * condition_modifier
            
            # Apply skill bonuses
            if "skill_bonus" in option_data:
                skill_level = player.skills.get(option_data["skill_bonus"], 0)
                base_chance += skill_level * 0.1
                
            options.append((option_name, min(0.95, base_chance)))
            messages.append(self._get_option_description(option_name, threat_type))
            
        return options, messages
        
    def _calculate_condition_modifier(self, player) -> float:
        """Calculate player's combat effectiveness based on condition."""
        condition_modifier = 1.0
        if player.energy < 20:
            condition_modifier *= 0.7
        if player.health < 30:
            condition_modifier *= 0.8
        if player.satiety < 30:  # Equivalent to old hunger > 70
            condition_modifier *= 0.9
        return condition_modifier
        
    def _get_available_tactics(self, location, combat_style: str) -> Dict:
        """Get tactics available based on location and style."""
        available = {}
        for tactic, data in self.tactical_options.items():
            # Location-based availability
            if tactic == "find_weapon" and location.danger_level < 3:
                continue
            if tactic == "call_for_help" and location.danger_level > 8:
                continue
                
            # Style-based availability
            style = self.combat_styles[combat_style]
            if combat_style == "aggressive" and tactic == "create_distance":
                continue
            if combat_style == "defensive" and tactic == "disarm":
                continue
                
            available[tactic] = data
            
        return available
        
    def _calculate_tactic_success(self, player, tactic_data: Dict, condition_modifier: float) -> float:
        """Calculate success chance for a tactical option."""
        base_chance = tactic_data["success_chance"] * condition_modifier
        
        if "skill_bonus" in tactic_data:
            skill_level = player.skills.get(tactic_data["skill_bonus"], 0)
            base_chance += skill_level * 0.1
            
        return min(0.95, base_chance)
        
    def _get_tactic_description(self, tactic: str, threat_type: str) -> str:
        """Get contextual description for tactical options."""
        descriptions = {
            "disarm": "Attempt to remove their weapon",
            "create_distance": "Try to gain some space",
            "find_weapon": "Look for something to defend yourself with",
            "call_for_help": "Attract attention from others"
        }
        return descriptions.get(tactic, "Unknown tactic")
        
    def _get_option_description(self, option: str, threat_type: str) -> str:
        """Get contextual description for combat options."""
        if option == "retreat":
            return "Try to escape the situation quickly"
        elif option == "de_escalate":
            return "Attempt to calm things down through dialogue"
        elif option == "defend":
            return "Take a defensive stance and protect yourself"
        elif option == "intimidate":
            return "Try to scare them off with an aggressive display"
            
    def process_outcome(self, player, choice: str, threat_type: str, combat_style: str) -> Dict:
        """Process combat outcome and apply effects."""
        style = self.combat_styles[combat_style]
        option_data = self.defense_options.get(choice) or self.tactical_options.get(choice)
        
        effects = {
            "health": 0,
            "energy": -option_data["energy_cost"],
            "mental": 0,
            "heat": 0,
            "message": "",
            "injury": None,
            "advantage_gained": None
        }
        
        # Apply style modifiers to outcome
        base_success_chance = option_data["success_chance"]
        for bonus_type, bonus_value in style.bonuses.items():
            if bonus_type == "damage_reduction" and "damage" in effects:
                effects["health"] *= (1 - bonus_value)
                
        success = random.random() < base_success_chance
        
        if choice in self.tactical_options:
            self._process_tactical_outcome(success, choice, effects, player)
        else:
            self._process_standard_outcome(success, choice, effects, player, threat_type)
            
        return effects
        
    def _process_tactical_outcome(self, success: bool, choice: str, effects: Dict, player):
        """Process outcome of tactical choices."""
        if success:
            effects["advantage_gained"] = self.tactical_options[choice]["advantage_gain"]
            if choice == "disarm":
                effects["message"] = "You successfully disarm your opponent!"
                player.increase_skill("self_defense", 1)
            elif choice == "create_distance":
                effects["message"] = "You create some space between you and your opponent."
                player.increase_skill("survival", 1)
            elif choice == "find_weapon":
                effects["message"] = "You find something to defend yourself with."
                player.increase_skill("street_smarts", 1)
            elif choice == "call_for_help":
                effects["message"] = "Others notice and intervene!"
                player.increase_skill("persuasion", 1)
        else:
            effects["health"] = -10
            effects["mental"] = -5
            effects["message"] = f"Your attempt to {choice.replace('_', ' ')} fails."
            
    def _process_standard_outcome(self, success: bool, choice: str, effects: Dict, player, threat_type: str):
        """Process outcome of standard combat options."""
        if choice == "retreat":
            if success:
                effects["message"] = "You successfully escape the situation."
                effects["heat"] = self.defense_options["retreat"]["heat_on_success"]
                player.increase_skill("stealth", 1)
            else:
                effects["health"] = -15
                effects["mental"] = -10
                effects["heat"] = self.defense_options["retreat"]["heat_if_fail"]
                effects["message"] = "Your escape attempt fails, leaving you vulnerable."
                self._apply_injury(player, effects, 0.5)
        elif choice == "de_escalate":
            if success:
                effects["mental"] = 5
                effects["message"] = "You successfully defuse the situation."
                player.improve_reputation("public", self.defense_options["de_escalate"]["reputation_gain"])
                player.increase_skill("persuasion", 1)
            else:
                effects["mental"] = -5
                effects["message"] = "Your attempts at peaceful resolution fail."
                self._apply_injury(player, effects, 0.2)
                
    def _apply_injury(self, player, effects: Dict, chance: float):
        """Apply random injury based on chance."""
        if random.random() < chance:
            injury_type = random.choice(self.injury_types)
            severity = random.randint(1, 3)
            player.add_injury(injury_type, severity)
            effects["injury"] = f"You suffer a {injury_type} of severity {severity}"
