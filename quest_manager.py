"""
Quest manager module for Hard Times: Ottawa.
Handles loading, tracking, and progressing quests.
"""
import json
import random
import os
from typing import Dict, List, Optional, Any, Union
from game.quest_events import QuestEvent, create_quest_event
from game.error_handler import error_handler

class QuestManager:
    """Manages game quests and their progression."""

    def __init__(self, player):
        """Initialize the quest manager.

        Args:
            player: Player object to track quest progress
        """
        self.player = player
        self.quests = {}
        self.active_quests = {}
        self.completed_quests = set()
        self.quest_events = {}
        self.location_quest_triggers = {}
        self.load_quests()

    def load_quests(self):
        """Load quest data from the JSON file."""
        try:
            quest_file_path = os.path.join('data', 'quests.json')
            with open(quest_file_path, 'r') as file:
                self.quests = json.load(file)
            print(f"Loaded {len(self.quests)} quests successfully")
        except Exception as e:
            error_handler.handle_error(e, {"context": "loading_quests"})
            print("Error loading quests. Using default empty quest dictionary.")
            self.quests = {}

    def start_quest(self, quest_id):
        """Start a new quest for the player.

        Args:
            quest_id: ID of the quest to start

        Returns:
            bool: True if quest started successfully
        """
        if quest_id not in self.quests:
            print(f"Quest {quest_id} not found")
            return False

        if quest_id in self.active_quests:
            print(f"Quest {quest_id} already active")
            return False

        if quest_id in self.completed_quests:
            print(f"Quest {quest_id} already completed")
            return False

        quest_data = self.quests[quest_id]
        self.active_quests[quest_id] = {
            "current_step": 0,
            "progress": 0,
            "data": quest_data
        }

        # Initialize quest progress in player
        if quest_id not in self.player.quest_progress:
            self.player.quest_progress[quest_id] = 0

        # Add to active quests list
        if quest_id not in self.player.active_quests:
            self.player.active_quests.append(quest_id)

        # Set initial story flag
        self.player.story_flags[f"{quest_id}_started"] = True

        print(f"Started quest: {quest_data['title']}")
        return True

    def get_available_quest_step(self, quest_id, location=None):
        """Get the current step for an active quest.

        Args:
            quest_id: ID of the quest
            location: Current location object (optional)

        Returns:
            dict: Quest step data or None
        """
        if quest_id not in self.active_quests:
            return None

        quest_progress = self.player.quest_progress.get(quest_id, 0)
        quest_data = self.active_quests[quest_id]["data"]
        steps = quest_data["steps"]

        # Find the matching step based on quest progress
        for step in steps:
            # Get the required progress for this step
            if self._meets_step_requirements(step, location):
                return step

        return None

    def _meets_step_requirements(self, step, location=None):
        """Check if step requirements are met.

        Args:
            step: Quest step data
            location: Current location (optional)

        Returns:
            bool: True if requirements are met
        """
        if "requirements" not in step:
            return True

        requirements = step["requirements"]

        # Check story flag requirements
        if "story_flags" in requirements:
            for flag in requirements["story_flags"]:
                if not self.player.story_flags.get(flag, False):
                    return False

        # Check quest progress requirements
        if "quest_progress" in requirements:
            quest_id = step.get("quest_id", None)
            if quest_id:
                if self.player.quest_progress.get(quest_id, 0) < requirements["quest_progress"]:
                    return False

        # Check money requirements
        if "money" in requirements:
            if self.player.money < requirements["money"]:
                return False

        # Check reputation requirements
        if "reputation" in requirements:
            for faction, min_value in requirements["reputation"].items():
                if self.player.reputation.get(faction, 0) < min_value:
                    return False

        # Check location requirements
        if location and "location_types" in step:
            location_types = step.get("location_types", [])
            if location.type not in location_types:
                return False

        # Check OR conditions
        if "or" in requirements:
            if not any(self._check_condition_set(condition_set) for condition_set in requirements["or"]):
                return False

        # Check AND conditions
        if "and" in requirements:
            if not all(self._check_condition_set(condition_set) for condition_set in requirements["and"]):
                return False

        return True

    def _check_condition_set(self, condition_set):
        """Check if a condition set is met.

        Args:
            condition_set: Dictionary of conditions

        Returns:
            bool: True if conditions are met
        """
        # Check story flags
        if "story_flags" in condition_set:
            for flag in condition_set["story_flags"]:
                if not self.player.story_flags.get(flag, False):
                    return False

        # Check money
        if "money" in condition_set:
            if self.player.money < condition_set["money"]:
                return False

        # Check days since flag
        if "days_since_flag" in condition_set:
            flag, days = condition_set["days_since_flag"]
            if flag in self.player.story_flags:
                # Calculate days since flag was set
                flag_day = self.player.story_flags.get(f"{flag}_day", 0)
                days_since = self.player.days_survived - flag_day
                if days_since < days:
                    return False
            else:
                return False

        return True

    def update_quest_progress(self, quest_id, progress, story_flags=None, step_id=None, daily_summary=None):
        """Update progress for a quest, with validation and milestone tracking.

        Args:
            quest_id: ID of the quest
            progress: New progress value
            story_flags: List of story flags to set
            step_id: Optional specific step ID that was completed
            daily_summary: Optional DailySummary object for progress tracking

        Returns:
            bool: True if progress updated successfully
            
        Raises:
            ValueError: If progress value is invalid
        """
        # Validate progress value
        if progress < 0:
            raise ValueError("Progress cannot be negative")
            
        # Get quest data for validation
        if quest_id not in self.quests:
            return False
            
        quest_data = self.quests[quest_id]
        max_progress = len(quest_data["steps"]) if "steps" in quest_data else 100
        
        # Ensure progress doesn't exceed maximum
        progress = min(progress, max_progress)

        Args:
            quest_id: ID of the quest
            progress: New progress value
            story_flags: List of story flags to set
            step_id: Optional specific step ID that was completed
            daily_summary: Optional DailySummary object for progress tracking

        Returns:
            bool: True if progress updated successfully
        """
        if quest_id not in self.active_quests:
            return False

        # Get the old progress for comparison
        old_progress = self.player.quest_progress.get(quest_id, 0)

        # Update progress in player object
        self.player.quest_progress[quest_id] = progress

        # Update progress in active quests
        self.active_quests[quest_id]["progress"] = progress

        # Set story flags
        if story_flags:
            for flag in story_flags:
                self.player.story_flags[flag] = True
                # Also store the day when this flag was set
                self.player.story_flags[f"{flag}_day"] = self.player.days_survived

        # If daily summary is provided, track quest progress
        if daily_summary and quest_id in self.quests:
            quest_data = self.quests[quest_id]
            quest_title = quest_data.get('title', 'Unknown Quest')

            # If significant progress was made
            if progress > old_progress:
                # Add to journal
                daily_summary.add_journal_entry(
                    f"Made progress in quest: {quest_title}",
                    "quest"
                )

                # Complete current goal if it exists
                goal_text = f"Progress in '{quest_title}' quest"
                daily_summary.complete_goal(goal_text)

                # Add new goal with updated progress
                quest_data = self.active_quests[quest_id]["data"]
                total_steps = len(quest_data["steps"]) if "steps" in quest_data else 1
                progress_percentage = int((progress / total_steps) * 100) if total_steps > 0 else 0

                if progress_percentage < 100:
                    daily_summary.add_goal(
                        f"Continue '{quest_title}' quest ({progress_percentage}% complete)", 
                        priority=2, 
                        quest_related=True,
                        quest_id=quest_id
                    )

        # Check for quest completion
        quest_data = self.active_quests[quest_id]["data"]
        final_step_progress = len(quest_data["steps"])

        if progress >= final_step_progress:
            # If daily summary is provided and quest is completed
            if daily_summary and quest_id in self.quests:
                quest_data = self.quests[quest_id]
                quest_title = quest_data.get('title', 'Unknown Quest')

                # Add completion to journal as a milestone
                daily_summary.add_journal_entry(
                    f"Completed quest: {quest_title}!",
                    "milestone"
                )

                # Mark any related goals as complete
                daily_summary.complete_goal(f"Progress in '{quest_title}' quest")
                daily_summary.complete_goal(f"Continue '{quest_title}' quest")

            self.complete_quest(quest_id)

        return True

    def complete_quest(self, quest_id):
        """Mark a quest as completed and apply completion effects.

        Args:
            quest_id: ID of the quest to complete

        Returns:
            bool: True if completed successfully
        """
        if quest_id not in self.active_quests:
            return False

        quest_data = self.active_quests[quest_id]["data"]

        # Apply completion effects
        final_step = quest_data["steps"][-1]
        if "completion_effects" in final_step:
            self._apply_completion_effects(final_step["completion_effects"])

        # Remove from active quests
        if quest_id in self.player.active_quests:
            self.player.active_quests.remove(quest_id)

        # Add to completed quests
        self.completed_quests.add(quest_id)
        if quest_id not in self.player.completed_quests:
            self.player.completed_quests.add(quest_id)

        # Set completion flag
        self.player.story_flags[f"{quest_id}_completed"] = True

        # Check for follow-up quests
        if "completion_effects" in final_step and "follow_up_quests" in final_step["completion_effects"]:
            for follow_up_id in final_step["completion_effects"]["follow_up_quests"]:
                self.start_quest(follow_up_id)

        return True

    def _apply_completion_effects(self, effects):
        """Apply effects when a quest is completed.

        Args:
            effects: Dictionary of effects to apply
        """
        # Apply reputation effects
        if "reputation" in effects:
            for faction, amount in effects["reputation"].items():
                self.player.improve_reputation(faction, amount)

        # Unlock new features
        if "unlock_features" in effects:
            for feature in effects["unlock_features"]:
                self.player.unlocked_features[feature] = True

        # Apply dignity boost
        if "dignity" in effects:
            self.player.dignity = min(100, self.player.dignity + effects["dignity"])

        # Apply hope boost
        if "hope" in effects:
            self.player.hope = min(100, self.player.hope + effects["hope"])

        # Apply other stat effects
        for stat in ["health", "mental", "energy", "satiety"]:
            if stat in effects:
                current_value = getattr(self.player, stat)
                setattr(self.player, stat, min(100, current_value + effects[stat]))

    def get_quest_triggers_for_location(self, location_type):
        """Get quests that can trigger in a specific location type.

        Args:
            location_type: Type of location

        Returns:
            list: Quest IDs that can trigger here
        """
        triggers = []

        # Check all quests for possible triggers in this location
        for quest_id, quest_data in self.quests.items():
            # Skip already active or completed quests
            if quest_id in self.active_quests or quest_id in self.completed_quests:
                continue

            # Check first step for location trigger
            if quest_data["steps"] and "location_types" in quest_data["steps"][0]:
                if location_type in quest_data["steps"][0]["location_types"]:
                    # Check if requirements for first step are met
                    if self._meets_step_requirements(quest_data["steps"][0]):
                        triggers.append(quest_id)

        return triggers

    def check_location_quest_triggers(self, location, time_system=None, economy_manager=None):
        """Check if any quests can be triggered at the current location, considering weather and economy."""
        if not hasattr(location, 'type'):
            return []

        location_type = location.type
        potential_quests = self.get_quest_triggers_for_location(location_type)

        # Filter quests based on weather conditions
        if time_system and time_system.is_harsh_weather():
            # Prioritize survival/weather-related quests
            potential_quests = [q for q in potential_quests if 
                              any(tag in self.quests[q].get('tags', []) 
                                  for tag in ['survival', 'weather', 'shelter'])]

        # Consider economic conditions
        if economy_manager:
            # Filter based on economic state
            if economy_manager.global_economy < 0.3:
                # Prioritize economic opportunity quests in bad economy
                potential_quests = [q for q in potential_quests if 
                                  'economic' in self.quests[q].get('tags', [])]

        # Randomly select one quest to potentially trigger
        if potential_quests:
            return random.choice(potential_quests)

        return None

    def get_active_quest_count(self):
        """Get number of active quests.

        Returns:
            int: Number of active quests
        """
        return len(self.active_quests)

    def get_completed_quest_count(self):
        """Get number of completed quests.

        Returns:
            int: Number of completed quests
        """
        return len(self.completed_quests)

    def save_quest_state(self):
        """Save current quest state.
        
        Returns:
            dict: Quest state data
        """
        return {
            'active_quests': {
                quest_id: {
                    'current_step': data['current_step'],
                    'progress': data['progress']
                } for quest_id, data in self.active_quests.items()
            },
            'completed_quests': list(self.completed_quests),
            'quest_events': self.quest_events
        }

    def load_quest_state(self, state_data):
        """Load saved quest state.
        
        Args:
            state_data: Dict containing quest state
        """
        self.active_quests = {}
        for quest_id, data in state_data.get('active_quests', {}).items():
            if quest_id in self.quests:
                self.active_quests[quest_id] = {
                    'current_step': data['current_step'],
                    'progress': data['progress'],
                    'data': self.quests[quest_id]
                }
        
        self.completed_quests = set(state_data.get('completed_quests', []))
        self.quest_events = state_data.get('quest_events', {})

    def get_quest_summary(self, quest_id):
        """Get a summary of a quest's current status.

        Args:
            quest_id: ID of the quest

        Returns:
            dict: Quest summary information
        """
        if quest_id not in self.quests:
            return None

        quest_data = self.quests[quest_id]
        is_active = quest_id in self.active_quests
        is_completed = quest_id in self.completed_quests

        progress = 0
        current_step = None

        if is_active:
            progress = self.player.quest_progress.get(quest_id, 0)
            active_data = self.active_quests[quest_id]
            current_step_index = active_data["current_step"]

            if 0 <= current_step_index < len(quest_data["steps"]):
                current_step = quest_data["steps"][current_step_index]

        total_steps = len(quest_data["steps"])
        progress_percentage = int((progress / total_steps) * 100) if total_steps > 0 else 0

        return {
            "id": quest_id,
            "title": quest_data["title"],
            "description": quest_data["description"],
            "active": is_active,
            "completed": is_completed,
            "progress": progress,
            "progress_percentage": progress_percentage,
            "total_steps": total_steps,
            "current_step": current_step
        }

    def process_quest_event(self, quest_id, step_id, choice_index, location=None):
        """Process a quest event choice.

        Args:
            quest_id: ID of the quest
            step_id: ID of the step
            choice_index: Index of the chosen option
            location: Current location (optional)

        Returns:
            tuple: (success, message, effects)
        """
        if quest_id not in self.active_quests:
            return False, "Quest not active", {}

        quest_data = self.active_quests[quest_id]["data"]

        # Find the step
        step = None
        for s in quest_data["steps"]:
            if s["step_id"] == step_id:
                step = s
                break

        if not step:
            return False, "Step not found", {}

        # Get the choice
        choices = step["choices"]
        if choice_index < 0 or choice_index >= len(choices):
            return False, "Invalid choice", {}

        choice = choices[choice_index]

        # Check requirements for this choice
        if "requirements" in choice:
            for req_type, value in choice["requirements"].items():
                if req_type == "money":
                    if self.player.money < value:
                        return False, f"You need ${value} for this option", {}
                elif req_type == "reputation":
                    for faction, min_value in value.items():
                        if self.player.reputation.get(faction, 0) < min_value:
                            return False, f"You need more reputation with {faction}", {}
                elif req_type == "story_flags":
                    for flag in value:
                        if not self.player.story_flags.get(flag, False):
                            return False, "You don't meet the requirements", {}

        # Apply outcomes
        outcomes = choice["outcomes"]
        effects = {}

        # Apply outcomes to player
        if "mental" in outcomes:
            self.player.mental = min(100, max(0, self.player.mental + outcomes["mental"]))
            effects["mental"] = outcomes["mental"]

        if "energy" in outcomes:
            self.player.energy = min(100, max(0, self.player.energy + outcomes["energy"]))
            effects["energy"] = outcomes["energy"]

        if "money" in outcomes:
            self.player.money += outcomes["money"]
            effects["money"] = outcomes["money"]

        if "health" in outcomes:
            self.player.health = min(100, max(0, self.player.health + outcomes["health"]))
            effects["health"] = outcomes["health"]

        if "satiety" in outcomes:
            self.player.satiety = min(100, max(0, self.player.satiety + outcomes["satiety"]))
            effects["satiety"] = outcomes["satiety"]

        if "dignity" in outcomes:
            self.player.dignity = min(100, max(0, self.player.dignity + outcomes["dignity"]))
            effects["dignity"] = outcomes["dignity"]

        if "hope" in outcomes:
            self.player.hope = min(100, max(0, self.player.hope + outcomes["hope"]))
            effects["hope"] = outcomes["hope"]

        # Apply reputation changes
        if "reputation" in outcomes:
            for faction, amount in outcomes["reputation"].items():
                self.player.improve_reputation(faction, amount)
                if "reputation" not in effects:
                    effects["reputation"] = {}
                effects["reputation"][faction] = amount

        # Apply story flags
        if "story_flags" in outcomes:
            for flag in outcomes["story_flags"]:
                self.player.story_flags[flag] = True
                self.player.story_flags[f"{flag}_day"] = self.player.days_survived

        # Add items to inventory
        if "inventory" in outcomes:
            for item_name, quantity in outcomes["inventory"].items():
                # This assumes an add_item method that handles creating or adding to inventory
                self.player.add_item(item_name, quantity)
                if "inventory" not in effects:
                    effects["inventory"] = {}
                effects["inventory"][item_name] = quantity

        # Update quest progress
        if "quest_progress" in outcomes:
            # Get the daily_summary from the main game if available
            daily_summary = getattr(self, 'daily_summary', None)

            self.update_quest_progress(quest_id, outcomes["quest_progress"], 
                                      outcomes.get("story_flags", []), step_id, daily_summary)
            effects["quest_progress"] = outcomes["quest_progress"]

        # Unlock features
        if "unlock_features" in outcomes:
            for feature in outcomes["unlock_features"]:
                self.player.unlocked_features[feature] = True
                if "unlocked_features" not in effects:
                    effects["unlocked_features"] = []
                effects["unlocked_features"].append(feature)

        return True, outcomes.get("message", "Choice processed successfully"), effects