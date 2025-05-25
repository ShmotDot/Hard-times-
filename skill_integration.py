"""
Skill Integration module for Hard Times: Ottawa.
Connects the enhanced skill system with game events, quests, NPCs, and environmental factors.
"""
import logging
from typing import Dict, List, Optional, Any
from game.enhanced_skills import SkillSystem, SkillContext

class SkillIntegration:
    """Integration class for connecting skills with game systems."""
    
    def __init__(self, skill_system: SkillSystem):
        """Initialize with a skill system."""
        self.skill_system = skill_system
        
    def process_event_outcome(self, event_data: Dict, player_choice: int, 
                             player_data: Dict, game_state: Dict) -> List[str]:
        """Process skill gains from event outcomes.
        
        Args:
            event_data: Event data including ID, type, choices, etc.
            player_choice: Index of player's chosen option
            player_data: Current player stats and attributes
            game_state: Current game state (day, location, etc.)
            
        Returns:
            list: Messages about skill changes
        """
        messages = []
        
        # Get the chosen outcome
        if "choices" not in event_data or player_choice >= len(event_data["choices"]):
            return messages
            
        # Extract data from the event
        event_id = event_data.get("id", "unknown_event")
        event_type = event_data.get("type", "general")
        choice = event_data["choices"][player_choice]
        outcomes = choice.get("outcomes", {})
        
        # Skip if no skill effects
        if "skills" not in outcomes:
            return messages
            
        # Create appropriate context
        if event_type == "quest":
            context = SkillContext.quest_context(
                event_id=event_id,
                difficulty=outcomes.get("difficulty", 1),
                skill_type=outcomes.get("skill_type", "general")
            )
        else:
            context = SkillContext.general_context(
                event_type=event_type,
                location=game_state.get("location"),
                time=game_state.get("time")
            )
            
        # Process each skill effect
        for skill_name, change in outcomes["skills"].items():
            success = self.skill_system.modify_skill(
                skill_name,
                change,
                context
            )
            if success:
                messages.append(f"Improved {skill_name} skill!")
                
        return messages
                quest_id=event_id,
                step=event_data.get("title", "unknown"),
                choice=player_choice,
                day=game_state.get("day", 0)
            )
        else:
            # Create environment context for other event types
            conditions = []
            if "weather" in game_state:
                conditions.append(game_state["weather"])
            if "time_period" in game_state:
                conditions.append(game_state["time_period"])
            if event_type in ["encounter", "opportunity"]:
                conditions.append(event_type)
                
            context = SkillContext.environment_context(
                location=game_state.get("location", "unknown"),
                activity="event_" + event_type,
                conditions=conditions,
                day=game_state.get("day", 0)
            )
            
        # Process each skill gain
        for skill_id, amount in outcomes["skills"].items():
            # Apply XP gain and get messages
            level_up, skill_messages = self.skill_system.gain_skill_xp(skill_id, amount, context)
            messages.extend(skill_messages)
            
        return messages
    
    def process_quest_milestone(self, quest_id: str, milestone: str, 
                               player_data: Dict, game_state: Dict) -> List[str]:
        """Process skill gains from reaching quest milestones.
        
        Args:
            quest_id: ID of the quest
            milestone: Milestone reached
            player_data: Current player stats
            game_state: Current game state
            
        Returns:
            list: Messages about skill changes
        """
        messages = []
        
        # Define skill XP for different quest types and milestones
        milestone_skill_gains = {
            "housing_quest": {
                "application_submitted": {"bureaucracy_navigation": 15},
                "approval_received": {"bureaucracy_navigation": 25, "persuasion": 10},
                "housing_secured": {"bureaucracy_navigation": 50, "stress_management": 30}
            },
            "shelter_quest": {
                "first_night": {"shelter_finding": 10},
                "week_survived": {"shelter_finding": 30, "endurance": 20},
                "safe_haven": {"shelter_finding": 40, "street_awareness": 25}
            },
            "job_quest": {
                "application_completed": {"odd_jobs": 15},
                "interview_success": {"persuasion": 30, "odd_jobs": 20},
                "first_paycheck": {"odd_jobs": 40, "trading": 15}
            },
            "id_quest": {
                "forms_completed": {"bureaucracy_navigation": 20},
                "documentation_gathered": {"bureaucracy_navigation": 25},
                "id_obtained": {"bureaucracy_navigation": 50, "persuasion": 15}
            }
        }
        
        # Extract quest type from ID if needed
        quest_type = next((qt for qt in milestone_skill_gains.keys() 
                         if qt in quest_id), "general_quest")
        
        # Check if we have defined gains for this quest type and milestone
        if quest_type in milestone_skill_gains and milestone in milestone_skill_gains[quest_type]:
            skill_gains = milestone_skill_gains[quest_type][milestone]
            
            # Create quest context
            context = SkillContext.quest_context(
                quest_id=quest_id,
                step=milestone,
                choice=-1,  # Not applicable for milestones
                day=game_state.get("day", 0)
            )
            
            # Apply each skill gain
            for skill_id, amount in skill_gains.items():
                level_up, skill_messages = self.skill_system.gain_skill_xp(skill_id, amount, context)
                messages.extend(skill_messages)
        
        return messages
    
    def process_npc_interaction(self, npc_data: Dict, interaction_type: str, 
                              outcome: str, player_data: Dict, game_state: Dict) -> List[str]:
        """Process skill gains from NPC interactions.
        
        Args:
            npc_data: NPC data
            interaction_type: Type of interaction
            outcome: Outcome of interaction
            player_data: Current player stats
            game_state: Current game state
            
        Returns:
            list: Messages about skill changes
        """
        messages = []
        
        # Define skill XP based on NPC role, interaction type, and outcome
        if interaction_type == "conversation":
            base_xp = 5
            # More XP for positive outcomes
            if outcome == "positive":
                base_xp = 10
                
            # Create NPC context
            context = SkillContext.npc_context(
                npc_id=npc_data.get("id", "unknown"),
                interaction_type=interaction_type,
                outcome=outcome,
                day=game_state.get("day", 0)
            )
            
            # Different skills based on NPC role
            role = npc_data.get("role", "general")
            
            if role in ["shelter_worker", "social_worker"]:
                skill_id = "persuasion"
                # Social workers can teach you bureaucracy navigation
                if outcome == "positive" and role == "social_worker":
                    context["guided"] = True
                    skill_id = "bureaucracy_navigation"
                    base_xp = 15
            elif role == "street_vendor":
                skill_id = "trading"
            elif role in ["street_survivor", "homeless"]:
                skill_id = "street_awareness" if outcome == "positive" else "persuasion"
            elif role == "healthcare_worker":
                skill_id = "health_management"
                if outcome == "positive":
                    context["guided"] = True
                    base_xp = 15
            else:
                skill_id = "persuasion"
                
            # Apply the skill gain
            level_up, skill_messages = self.skill_system.gain_skill_xp(skill_id, base_xp, context)
            messages.extend(skill_messages)
            
        elif interaction_type == "trade":
            # Trading interactions improve trading skill
            base_xp = 8
            if outcome == "profit":
                base_xp = 15
                
            context = SkillContext.npc_context(
                npc_id=npc_data.get("id", "unknown"),
                interaction_type=interaction_type,
                outcome=outcome,
                day=game_state.get("day", 0)
            )
            
            level_up, skill_messages = self.skill_system.gain_skill_xp("trading", base_xp, context)
            messages.extend(skill_messages)
            
        elif interaction_type == "help_request":
            # Asking for help improves persuasion
            base_xp = 10 if outcome == "success" else 5
            
            context = SkillContext.npc_context(
                npc_id=npc_data.get("id", "unknown"),
                interaction_type=interaction_type,
                outcome=outcome,
                day=game_state.get("day", 0)
            )
            
            level_up, skill_messages = self.skill_system.gain_skill_xp("persuasion", base_xp, context)
            messages.extend(skill_messages)
            
        elif interaction_type == "get_advice":
            # Getting advice can be guided learning
            base_xp = 10
            
            context = SkillContext.npc_context(
                npc_id=npc_data.get("id", "unknown"),
                interaction_type=interaction_type,
                outcome=outcome,
                day=game_state.get("day", 0)
            )
            
            # Different skills based on NPC role and advice topic
            role = npc_data.get("role", "general")
            topic = npc_data.get("advice_topic", "general")
            
            skill_id = "street_awareness"  # Default
            
            if role == "shelter_worker" and topic == "shelter":
                skill_id = "shelter_finding"
                context["guided"] = True
                base_xp = 15
            elif role == "street_survivor" and topic == "food":
                skill_id = "food_acquisition"
                context["guided"] = True
                base_xp = 15
            elif role == "healthcare_worker" and topic == "health":
                skill_id = "health_management"
                context["guided"] = True
                base_xp = 15
                
            level_up, skill_messages = self.skill_system.gain_skill_xp(skill_id, base_xp, context)
            messages.extend(skill_messages)
        
        return messages
    
    def process_environment_interaction(self, action: str, details: Dict, 
                                      player_data: Dict, game_state: Dict) -> List[str]:
        """Process skill gains from environmental interactions.
        
        Args:
            action: Type of action performed
            details: Details about the action
            player_data: Current player stats
            game_state: Current game state
            
        Returns:
            list: Messages about skill changes
        """
        messages = []
        
        # Define conditions based on game state
        conditions = []
        if "weather" in game_state:
            conditions.append(game_state["weather"])
        if "time_period" in game_state:
            conditions.append(game_state["time_period"])
            
        # Add special conditions
        if game_state.get("shelter_quality", 0) >= 7:
            conditions.append("safe_shelter")
        if game_state.get("weather_severity", 0) >= 7:
            conditions.append("harsh_weather")
            
        # Create context based on action type
        if action == "shelter_setup":
            shelter_quality = details.get("quality", 0)
            base_xp = max(5, shelter_quality * 3)
            
            context = SkillContext.environment_context(
                location=game_state.get("location", "unknown"),
                activity=action,
                conditions=conditions,
                day=game_state.get("day", 0)
            )
            
            # Add practice condition if deliberately practicing
            if details.get("practice", False):
                context["practice"] = True
                base_xp *= 1.5
                
            level_up, skill_messages = self.skill_system.gain_skill_xp("shelter_finding", int(base_xp), context)
            messages.extend(skill_messages)
            
        elif action == "food_scavenge":
            success = details.get("success", False)
            food_quality = details.get("food_quality", 0)
            base_xp = 5 if success else 2
            
            if food_quality > 0:
                base_xp += food_quality * 2
                
            context = SkillContext.environment_context(
                location=game_state.get("location", "unknown"),
                activity=action,
                conditions=conditions,
                day=game_state.get("day", 0)
            )
            
            level_up, skill_messages = self.skill_system.gain_skill_xp("food_acquisition", base_xp, context)
            messages.extend(skill_messages)
            
        elif action == "fire_making":
            success = details.get("success", False)
            fire_quality = details.get("fire_quality", 0)
            base_xp = 8 if success else 3
            
            if fire_quality > 0:
                base_xp += fire_quality * 3
                
            context = SkillContext.environment_context(
                location=game_state.get("location", "unknown"),
                activity=action,
                conditions=conditions,
                day=game_state.get("day", 0)
            )
            
            level_up, skill_messages = self.skill_system.gain_skill_xp("fire_making", base_xp, context)
            messages.extend(skill_messages)
            
        elif action == "crafting":
            item_id = details.get("item_id", "unknown")
            difficulty = details.get("difficulty", 1)
            success = details.get("success", False)
            
            base_xp = difficulty * 5
            if not success:
                base_xp = max(2, base_xp // 2)
                
            context = SkillContext.crafting_context(
                item_id=item_id,
                difficulty=difficulty,
                tools_used=details.get("tools_used", []),
                day=game_state.get("day", 0)
            )
            
            level_up, skill_messages = self.skill_system.gain_skill_xp("crafting", base_xp, context)
            messages.extend(skill_messages)
            
        elif action == "travel":
            distance = details.get("distance", 1)
            terrain = details.get("terrain", "urban")
            energy_used = details.get("energy_used", 10)
            
            # More XP for challenging travel
            base_xp = max(3, (distance + (energy_used // 10)) * 2)
            
            # Winter travel trains winter survival
            if "snow" in conditions or "winter" in conditions:
                context = SkillContext.survival_context(
                    activity="winter_travel",
                    success=True,
                    weather=game_state.get("weather", "clear"),
                    day=game_state.get("day", 0)
                )
                
                winter_xp = int(base_xp * 1.5)
                level_up, skill_messages = self.skill_system.gain_skill_xp("winter_survival", winter_xp, context)
                messages.extend(skill_messages)
                
            # Regular travel trains endurance
            context = SkillContext.environment_context(
                location=game_state.get("location", "unknown"),
                activity="travel",
                conditions=conditions,
                day=game_state.get("day", 0)
            )
            
            level_up, skill_messages = self.skill_system.gain_skill_xp("endurance", base_xp, context)
            messages.extend(skill_messages)
            
        elif action == "health_care":
            action_type = details.get("type", "general")
            success = details.get("success", False)
            
            base_xp = 8 if success else 3
            
            if action_type == "treat_injury":
                base_xp += 5
            elif action_type == "treat_illness":
                base_xp += 7
                
            context = SkillContext.environment_context(
                location=game_state.get("location", "unknown"),
                activity="health_care",
                conditions=conditions,
                day=game_state.get("day", 0)
            )
            
            level_up, skill_messages = self.skill_system.gain_skill_xp("health_management", base_xp, context)
            messages.extend(skill_messages)
            
        elif action == "meditation":
            duration = details.get("duration", 1)
            quality = details.get("quality", 0)
            
            base_xp = duration * 3
            if quality > 0:
                base_xp += quality * 2
                
            context = SkillContext.environment_context(
                location=game_state.get("location", "unknown"),
                activity="meditation",
                conditions=conditions,
                day=game_state.get("day", 0)
            )
            
            level_up, skill_messages = self.skill_system.gain_skill_xp("stress_management", base_xp, context)
            messages.extend(skill_messages)
        
        return messages
    
    def get_skill_bonus_for_action(self, action_type: str, skill_id: str, base_chance: float) -> float:
        """Get skill bonus for an action's success chance.
        
        Args:
            action_type: Type of action
            skill_id: ID of the relevant skill
            base_chance: Base chance of success (0-100)
            
        Returns:
            float: Modified success chance
        """
        return self.skill_system.get_skill_bonus(skill_id, action_type, base_chance)
    
    def get_passive_effects(self) -> Dict[str, Any]:
        """Get all passive effects from unlocked skill abilities.
        
        Returns:
            dict: Mapping of effect_type -> value
        """
        return self.skill_system.get_passive_bonuses()
    
    def update_skills_daily(self, day: int) -> List[str]:
        """Update skills for a new day and get status messages.
        
        Args:
            day: Current game day
            
        Returns:
            list: Status messages
        """
        return self.skill_system.update_skills(day)
    
    def get_skill_insights(self) -> List[str]:
        """Get insights about skill mastery patterns.
        
        Returns:
            list: Insight messages
        """
        return self.skill_system.get_skill_insights()
    
    def get_skill_summary(self) -> Dict[str, Any]:
        """Get summary of skill levels and progress.
        
        Returns:
            dict: Skill summary data
        """
        return self.skill_system.get_skill_summary()
    
    def serialize(self) -> Dict:
        """Serialize skill system data for saving.
        
        Returns:
            dict: Serialized data
        """
        return self.skill_system.serialize()
    
    def deserialize(self, data: Dict) -> bool:
        """Load skill system from saved data.
        
        Args:
            data: Saved skill system data
            
        Returns:
            bool: Success
        """
        return self.skill_system.deserialize(data)


# Example usage for different scenarios
def example_usage():
    """Example of how to use the skill integration module."""
    # Initialize skill system
    skill_system = SkillSystem()
    skill_integration = SkillIntegration(skill_system)
    
    # Example: Processing event outcome
    event_data = {
        "id": "shelter_search",
        "type": "general",
        "title": "Finding Shelter",
        "choices": [
            {
                "text": "Search the abandoned building",
                "outcomes": {
                    "message": "You find a dry corner that will serve as shelter for the night.",
                    "health": -5,
                    "skills": {
                        "shelter_finding": 10
                    }
                }
            },
            {
                "text": "Sleep under the bridge",
                "outcomes": {
                    "message": "It's cold but relatively safe.",
                    "health": -10,
                    "skills": {
                        "shelter_finding": 15,
                        "endurance": 5
                    }
                }
            }
        ]
    }
    
    player_data = {
        "stats": {
            "health": 80,
            "mental": 70
        }
    }
    
    game_state = {
        "day": 3,
        "location": "Downtown",
        "weather": "rain",
        "time_period": "night"
    }
    
    # Player chose option 1
    messages = skill_integration.process_event_outcome(event_data, 1, player_data, game_state)
    print("Event outcome messages:", messages)
    
    # Example: NPC interaction
    npc_data = {
        "id": "street_sam",
        "name": "Street Sam",
        "role": "street_survivor"
    }
    
    messages = skill_integration.process_npc_interaction(
        npc_data, "conversation", "positive", player_data, game_state
    )
    print("NPC interaction messages:", messages)
    
    # Example: Environmental interaction
    details = {
        "quality": 7,
        "practice": True
    }
    
    messages = skill_integration.process_environment_interaction(
        "shelter_setup", details, player_data, game_state
    )
    print("Environment interaction messages:", messages)
    
    # Get skill summary
    summary = skill_integration.get_skill_summary()
    print("Skill summary:", summary)


if __name__ == "__main__":
    example_usage()