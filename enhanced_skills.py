"""
Enhanced Skill System for Hard Times: Ottawa.
Implements a comprehensive skill development system that responds to player actions,
environmental conditions, NPC interactions, and quest choices.
"""
import random
import math
import logging
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
import json

@dataclass
class SkillAbility:
    """Represents an ability unlocked by advancing a skill."""
    name: str
    description: str
    level_required: int
    effects: Dict[str, Any] = field(default_factory=dict)
    passive: bool = False  # Is this a passive ability or active one?
    action_type: Optional[str] = None  # Type of action this applies to
    cooldown: int = 0  # Cooldown in game hours, if applicable


class Skill:
    """Represents a specific learnable skill."""
    
    def __init__(self, skill_id: str, name: str, description: str, category: str):
        self.id = skill_id
        self.name = name
        self.description = description
        self.category = category
        self.level = 0
        self.max_level = 10
        self.xp = 0
        self.xp_next_level = 100  # Base XP needed for level 1
        self.abilities = {}  # Unlocked abilities
        self.available_abilities = {}  # Abilities that can be unlocked
        self.proficiency_bonus = 0  # Bonus applied to related actions
        self.related_stats = []  # Player stats affected by this skill
        self.mastery_events = []  # Track significant mastery points
        self.practice_count = 0  # Track number of times practiced
        self.decay_rate = 0.1  # How quickly skill degrades if unused (0 = no decay)
        self.last_used = 0  # Game day when last used
        self.primary_attribute = None  # Primary attribute this skill is based on
        self.synergy_skills = []  # Skills that have synergy with this one
        self.aptitude = 1.0  # Learning aptitude (1.0 is normal, higher learns faster)
        
    def add_xp(self, amount: int, context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Add experience to the skill and check for level-up.
        
        Args:
            amount: Amount of XP to add
            context: Optional context about how XP was earned
            
        Returns:
            tuple: (level_up_occurred, [messages])
        """
        # Apply learning aptitude
        adjusted_amount = int(amount * self.aptitude)
        
        # Apply contextual modifiers
        if context:
            # Practice/repetition bonus
            if context.get("practice", False):
                self.practice_count += 1
                # Small bonus for deliberate practice
                practice_multiplier = min(2.0, 1.0 + (self.practice_count * 0.05))
                adjusted_amount = int(adjusted_amount * practice_multiplier)
            
            # Environmental modifiers
            if "environment" in context:
                env = context["environment"]
                if env == "stressful":
                    adjusted_amount = int(adjusted_amount * 0.8)  # 20% less effective
                elif env == "focused":
                    adjusted_amount = int(adjusted_amount * 1.2)  # 20% more effective
            
            # Guidance/instruction bonus
            if context.get("guided", False):
                adjusted_amount = int(adjusted_amount * 1.5)  # 50% more effective
                
            # Record context
            if "action" in context and adjusted_amount >= 10:
                self.mastery_events.append({
                    "action": context["action"],
                    "xp": adjusted_amount,
                    "day": context.get("day", 0)
                })
        
        # Update XP
        self.xp += adjusted_amount
        
        # Check for level up
        messages = []
        level_up_occurred = False
        
        while self.xp >= self.xp_next_level and self.level < self.max_level:
            # Level up!
            self.level += 1
            self.xp -= self.xp_next_level
            
            # Update XP required for next level
            self.xp_next_level = self._calculate_next_level_xp()
            
            # Update proficiency bonus
            self.proficiency_bonus = self._calculate_proficiency_bonus()
            
            # Unlock abilities for this level
            new_abilities = self._unlock_level_abilities()
            
            # Create level up message
            level_msg = f"Your {self.name} skill increased to level {self.level}!"
            messages.append(level_msg)
            
            # Add messages about new abilities
            for ability_id in new_abilities:
                ability = self.abilities[ability_id]
                ability_msg = f"New ability unlocked: {ability.name} - {ability.description}"
                messages.append(ability_msg)
                
            level_up_occurred = True
        
        # Update last used time
        if context and "day" in context:
            self.last_used = context["day"]
            
        return level_up_occurred, messages
    
    def _calculate_next_level_xp(self) -> int:
        """Calculate XP needed for the next level."""
        # Exponential curve that grows more steeply at higher levels
        return int(100 * (1.5 ** self.level))
    
    def _calculate_proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on skill level."""
        # Simple linear bonus, adjust as needed
        return self.level // 2
    
    def _unlock_level_abilities(self) -> List[str]:
        """Unlock abilities for the current level and return their IDs."""
        newly_unlocked = []
        
        for ability_id, ability in self.available_abilities.items():
            if ability.level_required == self.level:
                # Unlock this ability
                self.abilities[ability_id] = ability
                newly_unlocked.append(ability_id)
        
        return newly_unlocked
    
    def get_progress_percentage(self) -> float:
        """Get percentage progress to next level."""
        if self.level >= self.max_level:
            return 100.0
            
        return (self.xp / self.xp_next_level) * 100 if self.xp_next_level > 0 else 0.0
    
    def check_decay(self, current_day: int) -> bool:
        """Check if skill should decay due to lack of use.
        
        Args:
            current_day: Current game day
            
        Returns:
            bool: True if decay occurred
        """
        if self.decay_rate == 0 or self.level == 0:
            return False
            
        days_since_use = current_day - self.last_used
        if days_since_use <= 0:
            return False
            
        # Determine if decay should occur
        decay_chance = self.decay_rate * (days_since_use / 10.0)
        decay_chance = min(0.5, decay_chance)  # Cap at 50% chance
        
        if random.random() < decay_chance:
            # Lose some XP
            xp_loss = int(self.xp_next_level * 0.1)  # Lose 10% of progress to next level
            self.xp = max(0, self.xp - xp_loss)
            return True
            
        return False
    
    def apply_skill_bonus(self, action_type: str, base_chance: float) -> float:
        """Apply skill bonus to an action's success chance.
        
        Args:
            action_type: Type of action
            base_chance: Base chance of success (0-100)
            
        Returns:
            float: Modified success chance
        """
        # Basic bonus from proficiency
        bonus = self.proficiency_bonus * 5  # Each proficiency point gives +5%
        
        # Check for specific ability bonuses
        for ability in self.abilities.values():
            if ability.passive and ability.action_type == action_type:
                if "success_bonus" in ability.effects:
                    bonus += ability.effects["success_bonus"]
        
        # Apply bonus with diminishing returns at high levels
        new_chance = base_chance + (bonus * (1 - (base_chance / 150)))
        
        # Cap at reasonable limits
        return max(5, min(95, new_chance))
    
    def get_mastery_insights(self) -> List[str]:
        """Get insights about skill mastery patterns."""
        if not self.mastery_events or self.level < 3:
            return []
            
        insights = []
        
        # Check for patterns in mastery events
        action_counts = {}
        for event in self.mastery_events:
            action = event["action"]
            action_counts[action] = action_counts.get(action, 0) + 1
            
        # Find most common action
        if action_counts:
            most_common = max(action_counts.items(), key=lambda x: x[1])
            if most_common[1] >= 3:
                insights.append(
                    f"You've gained significant {self.name} experience from {most_common[0]}."
                )
        
        # Check if skill is advancing rapidly
        if len(self.mastery_events) >= 5 and self.level >= 5:
            insights.append(
                f"You're showing natural aptitude for {self.name}."
            )
            
        return insights


class SkillTree:
    """Represents a related group of skills that form a progression tree."""
    
    def __init__(self, tree_id: str, name: str, description: str):
        self.id = tree_id
        self.name = name
        self.description = description
        self.skills = {}  # skill_id -> Skill
        self.perks = {}  # Perks unlocked by advancing in this tree
        self.level = 0  # Overall tree level
        self.xp = 0  # Tree XP
        self.tree_abilities = {}  # Tree-wide abilities
        self.synergy_bonus = 0  # Bonus gained from skill synergies
        self.prerequisites = {}  # Prerequisites for unlocking skills
        self.primary_attribute = None  # Primary attribute this tree is based on
        
    def add_skill(self, skill: Skill) -> None:
        """Add a skill to this tree."""
        self.skills[skill.id] = skill
        skill.synergy_skills = [s.id for s in self.skills.values() 
                              if s.id != skill.id]
    
    def update_tree_level(self) -> bool:
        """Update overall tree level based on individual skill levels.
        
        Returns:
            bool: True if tree level changed
        """
        if not self.skills:
            return False
            
        # Average of all skill levels, weighted by XP
        total_levels = sum(skill.level for skill in self.skills.values())
        avg_level = total_levels / len(self.skills)
        new_level = int(avg_level)
        
        if new_level != self.level:
            old_level = self.level
            self.level = new_level
            
            # Update synergy bonus
            self._update_synergy_bonus()
            
            # Check for newly unlocked perks
            self._unlock_tree_perks()
            
            return True
            
        return False
    
    def _update_synergy_bonus(self) -> None:
        """Update the synergy bonus based on skill relationships."""
        # Simple calculation based on overall tree level
        self.synergy_bonus = self.level // 2
    
    def _unlock_tree_perks(self) -> List[str]:
        """Unlock perks for the current tree level and return their IDs."""
        newly_unlocked = []
        
        for perk_id, perk in self.perks.items():
            if perk.get("level_required") == self.level and perk_id not in self.tree_abilities:
                # Unlock this perk
                self.tree_abilities[perk_id] = perk
                newly_unlocked.append(perk_id)
        
        return newly_unlocked
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID."""
        return self.skills.get(skill_id)
    
    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        for skill in self.skills.values():
            if skill.name.lower() == name.lower():
                return skill
        return None
    
    def add_xp_to_skill(self, skill_id: str, amount: int, 
                       context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Add XP to a specific skill in this tree.
        
        Args:
            skill_id: ID of the skill
            amount: Amount of XP to add
            context: Optional context about how XP was earned
            
        Returns:
            tuple: (level_up_occurred, [messages])
        """
        skill = self.get_skill(skill_id)
        if not skill:
            return False, []
            
        # Apply tree synergy bonus if applicable
        if context and "synergy" not in context and self.synergy_bonus > 0:
            # Only apply synergy if not already accounted for
            synergy_amount = int(amount * (self.synergy_bonus / 10))
            adjusted_amount = amount + synergy_amount
        else:
            adjusted_amount = amount
            
        # Add XP to skill
        level_up, messages = skill.add_xp(adjusted_amount, context)
        
        # Add small amount of XP to tree
        self.xp += max(1, adjusted_amount // 10)
        
        # Update tree level
        tree_level_up = self.update_tree_level()
        if tree_level_up:
            messages.append(f"{self.name} tree advanced to level {self.level}!")
            
        return level_up, messages
    
    def can_unlock_skill(self, skill_id: str, player_attrs: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a skill can be unlocked based on prerequisites.
        
        Args:
            skill_id: ID of skill to check
            player_attrs: Player attributes to check against
            
        Returns:
            tuple: (can_unlock, message)
        """
        if skill_id in self.skills:
            return True, "Skill already unlocked"
            
        if skill_id not in self.prerequisites:
            return False, "Unknown skill"
            
        prereqs = self.prerequisites[skill_id]
        
        # Check prerequisites
        for prereq_type, prereq_value in prereqs.items():
            if prereq_type == "skill":
                # Format: skill_id:level
                req_skill, req_level = prereq_value.split(":")
                skill = self.get_skill(req_skill)
                if not skill or skill.level < int(req_level):
                    return False, f"Requires {req_skill} level {req_level}"
            elif prereq_type == "attribute":
                # Format: attribute:value
                attr, value = prereq_value.split(":")
                if player_attrs.get(attr, 0) < int(value):
                    return False, f"Requires {attr} of {value}"
            elif prereq_type == "item":
                # Format: item_id
                if not player_attrs.get("inventory", {}).get(prereq_value, 0):
                    return False, f"Requires item: {prereq_value}"
            elif prereq_type == "tree_level":
                # Format: level
                if self.level < int(prereq_value):
                    return False, f"Requires tree level {prereq_value}"
        
        return True, "Can be unlocked"


class SkillContext:
    """Helper class for creating and tracking skill contexts."""
    
    @staticmethod
    def quest_context(quest_id: str, step: str, choice: int, day: int) -> Dict[str, Any]:
        """Create context for quest-based skill gain."""
        return {
            "action": "quest",
            "quest_id": quest_id,
            "step": step,
            "choice": choice,
            "day": day,
            "practice": False,  # Quests are not practice
            "guided": False  # Generally not guided
        }
    
    @staticmethod
    def npc_context(npc_id: str, interaction_type: str, outcome: str, day: int) -> Dict[str, Any]:
        """Create context for NPC interaction skill gain."""
        return {
            "action": "npc_interaction",
            "npc_id": npc_id,
            "interaction_type": interaction_type,
            "outcome": outcome,
            "day": day,
            "practice": False,
            "guided": False  # Set to True if NPC is teaching
        }
    
    @staticmethod
    def environment_context(location: str, activity: str, conditions: List[str], day: int) -> Dict[str, Any]:
        """Create context for environmental skill gain."""
        # Determine environment type based on conditions
        env_type = "normal"
        if "harsh_weather" in conditions:
            env_type = "stressful"
        elif "safe_shelter" in conditions:
            env_type = "focused"
        
        return {
            "action": activity,
            "location": location,
            "conditions": conditions,
            "environment": env_type,
            "day": day,
            "practice": "practice" in conditions,
            "guided": "instruction" in conditions
        }
    
    @staticmethod
    def crafting_context(item_id: str, difficulty: int, tools_used: List[str], day: int) -> Dict[str, Any]:
        """Create context for crafting skill gain."""
        return {
            "action": "crafting",
            "item_id": item_id,
            "difficulty": difficulty,
            "tools_used": tools_used,
            "day": day,
            "practice": True,  # Crafting is practice
            "guided": False
        }
    
    @staticmethod
    def survival_context(activity: str, success: bool, weather: str, day: int) -> Dict[str, Any]:
        """Create context for survival skill gain."""
        return {
            "action": f"survival_{activity}",
            "success": success,
            "weather": weather,
            "environment": "stressful" if weather in ["snow", "rain", "storm"] else "normal",
            "day": day,
            "practice": True,
            "guided": False
        }
    
    @staticmethod
    def social_context(activity: str, target: str, outcome: str, day: int) -> Dict[str, Any]:
        """Create context for social skill gain."""
        return {
            "action": f"social_{activity}",
            "target": target,
            "outcome": outcome,
            "day": day,
            "practice": activity == "practice_conversation",
            "guided": False
        }


class SkillSystem:
    """Main system for managing all skills and skill trees."""
    
    def __init__(self):
        self.trees = {}  # tree_id -> SkillTree
        self.skill_map = {}  # Mapping of skill_id -> tree_id
        self.initialized = False
        self.last_update_day = 0
        
        # Skill categories for grouping
        self.categories = {
            "survival": "Skills for basic survival and self-sufficiency",
            "social": "Skills for interacting with people and society",
            "mental": "Skills for mental resilience and problem solving",
            "physical": "Skills for physical tasks and health",
            "economic": "Skills for earning and managing resources"
        }
        
        # Initialize skill system
        self._initialize_skill_system()
        
    def _initialize_skill_system(self) -> None:
        """Initialize skill trees and skills."""
        # Try to load from file first
        if self._load_skills_from_file():
            self.initialized = True
            return
            
        # If loading failed, create default trees
        self._create_default_skill_trees()
        self.initialized = True
    
    def _load_skills_from_file(self, file_path='data/skills.json') -> bool:
        """Load skills from JSON file."""
        try:
            with open(file_path, 'r') as f:
                skills_data = json.load(f)
                
            # Load skill trees
            trees_data = skills_data.get("trees", {})
            for tree_id, tree_data in trees_data.items():
                tree = SkillTree(
                    tree_id=tree_id,
                    name=tree_data.get("name", tree_id.title()),
                    description=tree_data.get("description", "")
                )
                tree.primary_attribute = tree_data.get("primary_attribute")
                tree.perks = tree_data.get("perks", {})
                tree.prerequisites = tree_data.get("prerequisites", {})
                
                # Add tree to system
                self.trees[tree_id] = tree
                
            # Load individual skills
            skills_data = skills_data.get("skills", {})
            for skill_id, skill_data in skills_data.items():
                skill = Skill(
                    skill_id=skill_id,
                    name=skill_data.get("name", skill_id.title()),
                    description=skill_data.get("description", ""),
                    category=skill_data.get("category", "general")
                )
                
                # Set skill properties
                skill.max_level = skill_data.get("max_level", 10)
                skill.related_stats = skill_data.get("related_stats", [])
                skill.decay_rate = skill_data.get("decay_rate", 0.1)
                skill.primary_attribute = skill_data.get("primary_attribute")
                
                # Load available abilities
                abilities_data = skill_data.get("abilities", {})
                for ability_id, ability_data in abilities_data.items():
                    ability = SkillAbility(
                        name=ability_data.get("name", ability_id.title()),
                        description=ability_data.get("description", ""),
                        level_required=ability_data.get("level_required", 1),
                        effects=ability_data.get("effects", {}),
                        passive=ability_data.get("passive", False),
                        action_type=ability_data.get("action_type"),
                        cooldown=ability_data.get("cooldown", 0)
                    )
                    skill.available_abilities[ability_id] = ability
                
                # Add skill to appropriate tree
                tree_id = skill_data.get("tree")
                if tree_id in self.trees:
                    self.trees[tree_id].add_skill(skill)
                    self.skill_map[skill_id] = tree_id
                
            return True
            
        except (FileNotFoundError, json.JSONDecodeError):
            logging.warning(f"Could not load skills from {file_path}, creating defaults")
            return False
        except Exception as e:
            logging.error(f"Error loading skills: {str(e)}")
            return False
    
    def _create_default_skill_trees(self) -> None:
        """Create default skill trees if file loading fails."""
        # 1. Survival Tree
        survival_tree = SkillTree(
            tree_id="survival",
            name="Survival",
            description="Skills for surviving in harsh urban environments"
        )
        
        # Survival Skills
        shelter_skill = Skill(
            skill_id="shelter_finding",
            name="Shelter Finding",
            description="Ability to locate and create safe shelter",
            category="survival"
        )
        shelter_skill.related_stats = ["health", "energy"]
        shelter_skill.available_abilities = {
            "urban_camper": SkillAbility(
                name="Urban Camper",
                description="Better rest quality in makeshift shelters",
                level_required=2,
                effects={"rest_bonus": 10},
                passive=True,
                action_type="rest"
            ),
            "weather_resistant": SkillAbility(
                name="Weather Resistant",
                description="Reduce negative effects from harsh weather",
                level_required=5,
                effects={"weather_resistance": 25},
                passive=True,
                action_type="weather"
            )
        }
        
        food_skill = Skill(
            skill_id="food_acquisition",
            name="Food Acquisition",
            description="Finding, scavenging, and safely consuming food",
            category="survival"
        )
        food_skill.related_stats = ["health", "satiety"]
        food_skill.available_abilities = {
            "dumpster_diving": SkillAbility(
                name="Dumpster Diving Pro",
                description="Better chance to find good food in dumpsters",
                level_required=3,
                effects={"scavenge_bonus": 20},
                passive=True,
                action_type="scavenge_food"
            ),
            "food_preservation": SkillAbility(
                name="Food Preservation",
                description="Food items last longer before expiring",
                level_required=6,
                effects={"food_expiry_bonus": 48},  # Extra hours
                passive=True,
                action_type="inventory"
            )
        }
        
        survival_tree.add_skill(shelter_skill)
        survival_tree.add_skill(food_skill)
        
        # 2. Social Tree
        social_tree = SkillTree(
            tree_id="social",
            name="Street Diplomacy",
            description="Skills for navigating social interactions and building relationships"
        )
        
        # Social Skills
        persuasion_skill = Skill(
            skill_id="persuasion",
            name="Persuasion",
            description="Convincing others to help or cooperate",
            category="social"
        )
        persuasion_skill.related_stats = ["mental", "charisma"]
        persuasion_skill.available_abilities = {
            "convincing_story": SkillAbility(
                name="Convincing Story",
                description="Better success when asking for help",
                level_required=2,
                effects={"success_bonus": 15},
                passive=True,
                action_type="ask_for_help"
            ),
            "negotiator": SkillAbility(
                name="Negotiator",
                description="Better prices when trading",
                level_required=4,
                effects={"trade_bonus": 10},
                passive=True,
                action_type="trade"
            )
        }
        
        social_tree.add_skill(persuasion_skill)
        
        # 3. Economic Tree
        economic_tree = SkillTree(
            tree_id="economic",
            name="Urban Hustle",
            description="Skills for making and managing resources"
        )
        
        # Economic Skills
        trading_skill = Skill(
            skill_id="trading",
            name="Street Trading",
            description="Buying, selling, and bartering goods",
            category="economic"
        )
        trading_skill.related_stats = ["money"]
        trading_skill.available_abilities = {
            "keen_eye": SkillAbility(
                name="Keen Eye for Value",
                description="Better at spotting valuable items",
                level_required=3,
                effects={"value_assessment": 20},
                passive=True,
                action_type="appraisal"
            ),
            "haggling": SkillAbility(
                name="Haggling",
                description="Better prices when buying and selling",
                level_required=5,
                effects={"price_bonus": 15},
                passive=True,
                action_type="trade"
            )
        }
        
        economic_tree.add_skill(trading_skill)
        
        # Add trees to system
        self.trees["survival"] = survival_tree
        self.trees["social"] = social_tree
        self.trees["economic"] = economic_tree
        
        # Update skill map
        for tree_id, tree in self.trees.items():
            for skill_id in tree.skills:
                self.skill_map[skill_id] = tree_id
    
    def get_tree(self, tree_id: str) -> Optional[SkillTree]:
        """Get a skill tree by ID."""
        return self.trees.get(tree_id)
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID."""
        tree_id = self.skill_map.get(skill_id)
        if not tree_id:
            return None
            
        tree = self.get_tree(tree_id)
        if not tree:
            return None
            
        return tree.get_skill(skill_id)
    
    def gain_skill_xp(self, skill_id: str, amount: int, 
                     context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Add XP to a skill.
        
        Args:
            skill_id: ID of the skill
            amount: Amount of XP to add
            context: Optional context about how XP was earned
            
        Returns:
            tuple: (success, [messages])
        """
        tree_id = self.skill_map.get(skill_id)
        if not tree_id:
            return False, [f"Unknown skill: {skill_id}"]
            
        tree = self.get_tree(tree_id)
        if not tree:
            return False, [f"Unknown skill tree: {tree_id}"]
            
        # Add XP to skill in tree
        level_up, messages = tree.add_xp_to_skill(skill_id, amount, context)
        
        return level_up, messages
    
    def update_skills(self, current_day: int) -> List[str]:
        """Update all skills for a new day, check for decay, etc.
        
        Args:
            current_day: Current game day
            
        Returns:
            list: Status messages
        """
        if current_day <= self.last_update_day:
            return []
            
        messages = []
        
        # Check for skill decay
        for tree in self.trees.values():
            for skill in tree.skills.values():
                if skill.check_decay(current_day):
                    messages.append(f"Your {skill.name} skill is getting rusty from lack of use.")
        
        self.last_update_day = current_day
        return messages
    
    def get_skill_bonus(self, skill_id: str, action_type: str, base_chance: float) -> float:
        """Get skill bonus for an action.
        
        Args:
            skill_id: ID of the skill
            action_type: Type of action
            base_chance: Base chance of success (0-100)
            
        Returns:
            float: Modified success chance
        """
        skill = self.get_skill(skill_id)
        if not skill:
            return base_chance
            
        return skill.apply_skill_bonus(action_type, base_chance)
    
    def get_all_unlocked_abilities(self) -> Dict[str, List[SkillAbility]]:
        """Get all unlocked abilities across all skills.
        
        Returns:
            dict: Mapping of skill_id -> list of abilities
        """
        all_abilities = {}
        
        for tree in self.trees.values():
            for skill_id, skill in tree.skills.items():
                if skill.abilities:
                    all_abilities[skill_id] = list(skill.abilities.values())
                    
        return all_abilities
    
    def get_passive_bonuses(self) -> Dict[str, Any]:
        """Get all passive bonuses from unlocked abilities.
        
        Returns:
            dict: Mapping of bonus_type -> value
        """
        bonuses = {}
        
        for tree in self.trees.values():
            for skill in tree.skills.values():
                for ability in skill.abilities.values():
                    if ability.passive:
                        for effect_type, effect_value in ability.effects.items():
                            # Combine bonuses of the same type
                            if effect_type in bonuses:
                                bonuses[effect_type] += effect_value
                            else:
                                bonuses[effect_type] = effect_value
                                
        return bonuses
    
    def get_skill_insights(self) -> List[str]:
        """Get insights about skill mastery patterns.
        
        Returns:
            list: Insight messages
        """
        insights = []
        
        for tree in self.trees.values():
            # Tree-level insights
            if tree.level >= 3:
                insights.append(f"You've developed significant proficiency in {tree.name}.")
                
            # Individual skill insights
            for skill in tree.skills.values():
                if skill.level >= 3:
                    skill_insights = skill.get_mastery_insights()
                    insights.extend(skill_insights)
                    
        return insights
    
    def process_event_outcome(self, event_id: str, event_type: str, choice: int, 
                             outcomes: Dict, player_data: Dict, context: Dict) -> List[str]:
        """Process skill gains from an event outcome.
        
        Args:
            event_id: ID of the event
            event_type: Type of event (general, quest, etc.)
            choice: Index of chosen option
            outcomes: Outcome data
            player_data: Player data for context
            context: Additional context (location, day, etc.)
            
        Returns:
            list: Messages about skill changes
        """
        skill_messages = []
        
        # Check if outcomes include skill XP
        if "skills" in outcomes:
            skill_gains = outcomes["skills"]
            
            # Prepare skill context
            if event_type == "quest":
                skill_ctx = SkillContext.quest_context(
                    quest_id=event_id,
                    step=outcomes.get("step", "unknown"),
                    choice=choice,
                    day=context.get("day", 0)
                )
            else:
                skill_ctx = SkillContext.environment_context(
                    location=context.get("location", "unknown"),
                    activity="event_choice",
                    conditions=context.get("conditions", []),
                    day=context.get("day", 0)
                )
                
            # Process each skill gain
            for skill_id, amount in skill_gains.items():
                level_up, messages = self.gain_skill_xp(skill_id, amount, skill_ctx)
                skill_messages.extend(messages)
        
        return skill_messages
    
    def process_activity(self, activity: str, details: Dict, 
                        player_data: Dict, context: Dict) -> List[str]:
        """Process skill gains from a player activity.
        
        Args:
            activity: Type of activity
            details: Activity details
            player_data: Player data for context
            context: Additional context (location, day, etc.)
            
        Returns:
            list: Messages about skill changes
        """
        skill_messages = []
        
        # Process different activity types
        if activity == "crafting":
            # Determine crafting XP based on difficulty
            difficulty = details.get("difficulty", 1)
            base_xp = difficulty * 10
            
            skill_ctx = SkillContext.crafting_context(
                item_id=details.get("item_id", "unknown"),
                difficulty=difficulty,
                tools_used=details.get("tools", []),
                day=context.get("day", 0)
            )
            
            # Add XP to crafting skill
            level_up, messages = self.gain_skill_xp("crafting", base_xp, skill_ctx)
            skill_messages.extend(messages)
            
        elif activity == "scavenging":
            # Scavenging for resources
            success = details.get("success", False)
            items_found = details.get("items_found", 0)
            
            # Calculate XP based on success and items found
            base_xp = 5 if success else 2
            bonus_xp = items_found * 3
            total_xp = base_xp + bonus_xp
            
            skill_ctx = SkillContext.survival_context(
                activity="scavenging",
                success=success,
                weather=context.get("weather", "clear"),
                day=context.get("day", 0)
            )
            
            # Add XP to appropriate skills
            level_up, messages = self.gain_skill_xp("food_acquisition", total_xp, skill_ctx)
            skill_messages.extend(messages)
            
        elif activity == "shelter_building":
            # Building or finding shelter
            quality = details.get("quality", 0)
            weather = context.get("weather", "clear")
            
            # Calculate XP based on shelter quality and weather
            base_xp = quality * 5
            if weather in ["rain", "snow", "storm"]:
                base_xp *= 1.5  # More XP in harsh weather
                
            skill_ctx = SkillContext.survival_context(
                activity="shelter_building",
                success=quality > 0,
                weather=weather,
                day=context.get("day", 0)
            )
            
            # Add XP to shelter skill
            level_up, messages = self.gain_skill_xp("shelter_finding", int(base_xp), skill_ctx)
            skill_messages.extend(messages)
            
        elif activity == "social_interaction":
            # Social interaction with NPCs
            npc_id = details.get("npc_id", "unknown")
            interaction_type = details.get("type", "conversation")
            outcome = details.get("outcome", "neutral")
            
            # Calculate XP based on outcome
            outcome_multiplier = 1.0
            if outcome == "positive":
                outcome_multiplier = 1.5
            elif outcome == "negative":
                outcome_multiplier = 0.5
                
            base_xp = 10 * outcome_multiplier
            
            skill_ctx = SkillContext.npc_context(
                npc_id=npc_id,
                interaction_type=interaction_type,
                outcome=outcome,
                day=context.get("day", 0)
            )
            
            # Add XP to social skill
            level_up, messages = self.gain_skill_xp("persuasion", int(base_xp), skill_ctx)
            skill_messages.extend(messages)
            
        elif activity == "trading":
            # Trading with merchants
            items_traded = details.get("items_traded", 0)
            profit = details.get("profit", 0)
            haggled = details.get("haggled", False)
            
            # Calculate XP based on trading activity
            base_xp = items_traded * 5
            if profit > 0:
                base_xp += profit // 2
            if haggled:
                base_xp *= 1.2
                
            skill_ctx = SkillContext.social_context(
                activity="trading",
                target=details.get("merchant_id", "unknown"),
                outcome="profit" if profit > 0 else "loss",
                day=context.get("day", 0)
            )
            
            # Add XP to trading skill
            level_up, messages = self.gain_skill_xp("trading", int(base_xp), skill_ctx)
            skill_messages.extend(messages)
        
        return skill_messages
    
    def get_skill_summary(self) -> Dict[str, Any]:
        """Get summary of skill levels and progress.
        
        Returns:
            dict: Skill summary data
        """
        summary = {
            "trees": {},
            "highest_skills": [],
            "recent_progress": []
        }
        
        # Collect tree summaries
        for tree_id, tree in self.trees.items():
            tree_summary = {
                "name": tree.name,
                "level": tree.level,
                "skills": {}
            }
            
            for skill_id, skill in tree.skills.items():
                tree_summary["skills"][skill_id] = {
                    "name": skill.name,
                    "level": skill.level,
                    "progress": skill.get_progress_percentage()
                }
                
            summary["trees"][tree_id] = tree_summary
            
        # Find highest skills
        all_skills = []
        for tree in self.trees.values():
            for skill_id, skill in tree.skills.items():
                all_skills.append((skill_id, skill))
                
        all_skills.sort(key=lambda x: x[1].level, reverse=True)
        
        for skill_id, skill in all_skills[:3]:  # Top 3 skills
            if skill.level > 0:
                summary["highest_skills"].append({
                    "id": skill_id,
                    "name": skill.name,
                    "level": skill.level,
                    "progress": skill.get_progress_percentage()
                })
                
        # Find recent progress
        recent_progress = []
        for tree in self.trees.values():
            for skill_id, skill in tree.skills.items():
                if skill.mastery_events:
                    recent = sorted(skill.mastery_events, key=lambda x: x.get("day", 0), reverse=True)
                    recent_progress.append({
                        "id": skill_id,
                        "name": skill.name,
                        "action": recent[0]["action"],
                        "xp": recent[0]["xp"],
                        "day": recent[0]["day"]
                    })
                    
        recent_progress.sort(key=lambda x: x["day"], reverse=True)
        summary["recent_progress"] = recent_progress[:5]  # Last 5 significant gains
        
        return summary
    
    def serialize(self) -> Dict:
        """Serialize skill system data for saving."""
        data = {
            "last_update_day": self.last_update_day,
            "trees": {}
        }
        
        for tree_id, tree in self.trees.items():
            tree_data = {
                "level": tree.level,
                "xp": tree.xp,
                "synergy_bonus": tree.synergy_bonus,
                "tree_abilities": tree.tree_abilities,
                "skills": {}
            }
            
            for skill_id, skill in tree.skills.items():
                skill_data = {
                    "level": skill.level,
                    "xp": skill.xp,
                    "xp_next_level": skill.xp_next_level,
                    "proficiency_bonus": skill.proficiency_bonus,
                    "practice_count": skill.practice_count,
                    "last_used": skill.last_used,
                    "abilities": list(skill.abilities.keys()),
                    "mastery_events": skill.mastery_events
                }
                
                tree_data["skills"][skill_id] = skill_data
                
            data["trees"][tree_id] = tree_data
            
        return data
    
    def deserialize(self, data: Dict) -> bool:
        """Load skill system from saved data.
        
        Args:
            data: Saved skill system data
            
        Returns:
            bool: Success
        """
        try:
            self.last_update_day = data.get("last_update_day", 0)
            
            for tree_id, tree_data in data.get("trees", {}).items():
                if tree_id not in self.trees:
                    continue
                    
                tree = self.trees[tree_id]
                tree.level = tree_data.get("level", 0)
                tree.xp = tree_data.get("xp", 0)
                tree.synergy_bonus = tree_data.get("synergy_bonus", 0)
                tree.tree_abilities = tree_data.get("tree_abilities", {})
                
                for skill_id, skill_data in tree_data.get("skills", {}).items():
                    if skill_id not in tree.skills:
                        continue
                        
                    skill = tree.skills[skill_id]
                    skill.level = skill_data.get("level", 0)
                    skill.xp = skill_data.get("xp", 0)
                    skill.xp_next_level = skill_data.get("xp_next_level", 100)
                    skill.proficiency_bonus = skill_data.get("proficiency_bonus", 0)
                    skill.practice_count = skill_data.get("practice_count", 0)
                    skill.last_used = skill_data.get("last_used", 0)
                    skill.mastery_events = skill_data.get("mastery_events", [])
                    
                    # Restore abilities
                    ability_ids = skill_data.get("abilities", [])
                    for ability_id in ability_ids:
                        if ability_id in skill.available_abilities:
                            skill.abilities[ability_id] = skill.available_abilities[ability_id]
            
            return True
            
        except Exception as e:
            logging.error(f"Error deserializing skill system: {str(e)}")
            return False


# Example of how to handle event outcomes with skill gains
def process_quest_outcome_example(event_id, choice_index, outcomes, player, skill_system, game_time):
    """Example of processing skill gains in a quest outcome."""
    messages = []
    
    # Basic outcomes processing
    if "message" in outcomes:
        messages.append(outcomes["message"])
        
    # Apply basic stat changes
    if "health" in outcomes:
        player.health += outcomes["health"]
        
    if "mental" in outcomes:
        player.mental += outcomes["mental"]
        
    # Process reputation changes
    if "reputation" in outcomes:
        for faction, amount in outcomes["reputation"].items():
            player.reputation[faction] += amount
            messages.append(f"{faction.title()} reputation {'increased' if amount > 0 else 'decreased'} by {abs(amount)}")
    
    # Process skill gains with context
    context = {
        "day": game_time.day,
        "location": player.location,
        "conditions": [game_time.weather, game_time.period]
    }
    
    skill_messages = skill_system.process_event_outcome(
        event_id=event_id,
        event_type="quest",
        choice=choice_index,
        outcomes=outcomes,
        player_data={
            "stats": {
                "health": player.health,
                "mental": player.mental
            },
            "reputation": player.reputation
        },
        context=context
    )
    
    messages.extend(skill_messages)
    return messages