"""Quest events system for Hard Times: Ottawa"""

from game.events import Event
import random

class QuestChain:
    def __init__(self, chain_id, steps, requirements=None):
        self.chain_id = chain_id
        self.steps = steps
        self.current_step = 0
        self.requirements = requirements or {}
        self.branches = {}  # Store branching paths
        self.completion_effects = {}  # Store long-term effects
        self.reputation_paths = {}  # Store reputation-based alternate paths
        self.choice_history = []  # Track player choices
        self.failure_states = {}  # Track quest failure conditions
        self.time_limits = {}  # Store time-sensitive quest phases

    def get_next_event(self, player):
        """Get next event considering player choices and state."""
        if self.current_step >= len(self.steps):
            return None

        # Check for dynamic branching based on player state
        if self.current_step in self.branches:
            branch_conditions = self.branches[self.current_step]
            for condition, alternative_step in branch_conditions.items():
                if self._check_branch_condition(player, condition):
                    # Store branch choice for persistence
                    player.quest_choices[self.chain_id] = condition
                    return alternative_step

        # Check for reputation-based alternate paths
        if self._has_reputation_alternate(player):
            return self._get_reputation_path(player)

        return self.steps[self.current_step]

    def _has_reputation_alternate(self, player):
        """Check if alternate path exists based on reputation."""
        if hasattr(self.steps[self.current_step], 'reputation_paths'):
            for rep, min_value in self.steps[self.current_step].reputation_paths.items():
                if player.reputation.get(rep, 0) >= min_value:
                    return True
        return False

    def _get_reputation_path(self, player):
        """Get alternate path based on reputation levels."""
        current_event = self.steps[self.current_step]
        highest_rep_path = None
        highest_rep_value = -1

        for rep, min_value in current_event.reputation_paths.items():
            player_rep = player.reputation.get(rep, 0)
            if player_rep >= min_value and player_rep > highest_rep_value:
                highest_rep_value = player_rep
                highest_rep_path = current_event.reputation_paths[rep]

        return highest_rep_path or current_event

    def _check_branch_condition(self, player, condition):
        """Check if conditions for a branch are met."""
        if "reputation" in condition:
            for group, value in condition["reputation"].items():
                if player.reputation.get(group, 0) < value:
                    return False

        if "story_flags" in condition:
            for flag in condition["story_flags"]:
                if not player.story_flags.get(flag, False):
                    return False

        if "time_limit" in condition:
            if player.days_survived > condition["time_limit"]:
                self.fail_quest("time_expired")
                return False

        if "skills" in condition:
            for skill, level in condition["skills"].items():
                if player.skills.get(skill, 0) < level:
                    return False

        if "items" in condition:
            for item_id, quantity in condition["items"].items():
                if not player.has_item(item_id, quantity):
                    return False

        return True

    def fail_quest(self, reason):
        """Handle quest failure states."""
        if reason in self.failure_states:
            consequences = self.failure_states[reason]
            for effect, value in consequences.items():
                if effect == "reputation":
                    for group, amount in value.items():
                        # Negative reputation impact
                        player.improve_reputation(group, -amount)
                elif effect == "story_flags":
                    for flag in value:
                        player.story_flags[flag] = True
        return False

    def advance(self, player):
        """Advance quest with potential effects."""
        self.current_step += 1

        # Apply completion effects if quest is finished
        if self.current_step >= len(self.steps):
            self._apply_completion_effects(player)

    def _apply_completion_effects(self, player):
        """Apply long-term effects when quest chain completes."""
        if not self.completion_effects:
            return

        for effect_type, value in self.completion_effects.items():
            if effect_type == "unlock_location":
                player.unlock_location(value)
            elif effect_type == "reputation":
                for group, amount in value.items():
                    player.improve_reputation(group, amount, "quest_completion")
            elif effect_type == "skill":
                for skill, amount in value.items():
                    player.increase_skill(skill, amount)

class QuestEvent(Event):
    def __init__(self, quest_arc, step, description, choices, requirements=None):
        super().__init__(
            event_id=f"{quest_arc}_{step}".lower().replace(" ", "_"),
            title=step,
            description=description,
            choices=choices,
            requirements=requirements,
            type="quest"
        )
        self.quest_arc = quest_arc
        self.completed = False
        self.milestones = []
        self.current_milestone = 0
        self.milestone_rewards = {}
        self.impacted_events = set()  # Track related events
        self.unlocked_events = set()  # Track events unlocked by this quest
        self.follow_up_quests = []  # Track quests that can trigger after this one
        self.reputation_thresholds = {}  # Track reputation requirements for different outcomes

    def process_quest_flags(self, player, outcomes, location=None):
        """Process quest-specific flags and effects."""
        # Update location quest completion if provided
        if location and "complete_quest" in outcomes:
            location.complete_quest(self.quest_arc)

        # Add location-specific event updates
        if location and "location_events" in outcomes:
            for event_id in outcomes["location_events"]:
                if outcomes["location_events"][event_id]:
                    location.add_active_event(event_id)
                else:
                    location.remove_active_event(event_id)
        if "story_flags" in outcomes:
            for flag in outcomes["story_flags"]:
                player.story_flags[flag] = True

        if "quest_progress" in outcomes:
            player.quest_progress[self.quest_arc] = outcomes["quest_progress"]

        # Update related random events based on quest progress
        if "event_updates" in outcomes:
            for event_id in outcomes["event_updates"]:
                self.impacted_events.add(event_id)

        # Unlock new events based on quest completion
        if "unlock_events" in outcomes:
            self.unlocked_events.update(outcomes["unlock_events"])
            player.unlock_story_events(outcomes["unlock_events"])

        # Check for follow-up quest triggers
        self._check_follow_up_quests(player)

        # Process reputation-based outcomes
        self._process_reputation_outcomes(player)

    def _check_follow_up_quests(self, player):
        """Check and potentially trigger follow-up quests."""
        for follow_up in self.follow_up_quests:
            if self._meets_follow_up_requirements(player, follow_up):
                player.start_quest(follow_up)

    def _meets_follow_up_requirements(self, player, quest):
        """Check if player meets requirements for follow-up quest."""
        if not quest.requirements:
            return True

        for req_type, value in quest.requirements.items():
            if req_type == "reputation":
                for group, min_value in value.items():
                    if player.reputation.get(group, 0) < min_value:
                        return False
            elif req_type == "story_flags":
                for flag in value:
                    if not player.story_flags.get(flag, False):
                        return False
        return True

    def _process_reputation_outcomes(self, player):
        """Process different outcomes based on reputation levels."""
        for group, thresholds in self.reputation_thresholds.items():
            rep_level = player.reputation.get(group, 0)
            for threshold, effects in thresholds.items():
                if rep_level >= threshold:
                    self._apply_threshold_effects(player, effects)

    def _apply_threshold_effects(self, player, effects):
        """Apply effects from reaching reputation thresholds."""
        for effect_type, value in effects.items():
            if effect_type == "unlock_ability":
                player.unlocked_abilities[value] = True
            elif effect_type == "skill_bonus":
                for skill, amount in value.items():
                    player.increase_skill(skill, amount)
            elif effect_type == "item_reward":
                player.add_item(value["item"], value.get("quantity", 1))

def create_quest_event(quest_data):
    """Create a quest event from data."""
    quest_event = QuestEvent(
        quest_data["quest_arc"],
        quest_data["step"],
        quest_data["description"],
        quest_data["choices"],
        quest_data.get("requirements", {})
    )

    # Add additional quest properties if present
    if "follow_up_quests" in quest_data:
        quest_event.follow_up_quests = quest_data["follow_up_quests"]
    if "reputation_thresholds" in quest_data:
        quest_event.reputation_thresholds = quest_data["reputation_thresholds"]

    return quest_event

quest_events = {
    "friend_relapse": {
        "id": "friend_relapse",
        "title": "Friend in Crisis",
        "description": "You notice Ray, who had been clean for months, showing signs of relapse. They're struggling with the upcoming winter.",
        "choices": [
            {
                "text": "Try to intervene and offer support",
                "outcomes": {
                    "mental": -10,
                    "energy": -15,
                    "message": "You spend hours talking with Ray, sharing your own struggles. It's emotionally draining but they agree to visit the clinic tomorrow.",
                    "story_flags": ["supporting_ray", "ray_recovery_started"],
                    "reputation": {"streets": 15}
                }
            },
            {
                "text": "Keep your distance, focusing on your own survival",
                "outcomes": {
                    "mental": -20,
                    "message": "You walk away, but the guilt weighs heavily. Sometimes survival means making hard choices.",
                    "story_flags": ["ray_abandoned"]
                }
            }
        ],
        "requirements": {
            "story_flags": ["ray_friendship"]
        },
        "type": "quest"
    },
    "community_loss": {
        "id": "community_loss",
        "title": "Loss in the Community",
        "description": "An elderly homeless man who often shared his food with others hasn't been seen for days. The community is worried.",
        "choices": [
            {
                "text": "Organize a search party",
                "outcomes": {
                    "energy": -25,
                    "mental": -15,
                    "reputation": {"community": 20, "streets": 15},
                    "message": "You rally others to search. Though the outcome is tragic, the community comes together, sharing stories and supporting each other.",
                    "story_flags": ["community_united", "memorial_organized"]
                }
            },
            {
                "text": "Share information with outreach workers",
                "outcomes": {
                    "mental": -10,
                    "reputation": {"services": 10},
                    "message": "The outreach team helps coordinate with hospitals and services. The situation highlights the vulnerability you all face.",
                    "story_flags": ["reported_missing"]
                }
            }
        ],
        "type": "quest"
    },
    "lantern_discovery": {
        "id": "lantern_discovery",
        "title": "Finding The Lantern",
        "description": "Following the trail of symbols has led you to a hidden community space. A small paper lantern hangs by the entrance.",
        "choices": [
            {
                "text": "Enter cautiously",
                "outcomes": {
                    "mental": 15,
                    "hope": 20,
                    "message": "Inside you find a well-organized community of people helping each other. This could be a turning point.",
                    "story_flags": ["lantern_discovered", "safe_haven_found"],
                    "reputation": {"lantern_community": 10}
                }
            },
            {
                "text": "Observe from outside first",
                "outcomes": {
                    "energy": -5,
                    "mental": 5,
                    "message": "You watch people coming and going, all seeming to know each other. It appears to be a genuine safe space.",
                    "story_flags": ["lantern_observed"]
                }
            }
        ],
        "requirements": {
            "story_flags": ["lantern_trail_found"]
        },
        "type": "quest"
    },
    "id_quest_shelter_letter": {
        "id": "id_quest_shelter_letter",
        "title": "Shelter Documentation",
        "description": "The shelter manager offers to write a letter confirming your stays, which could help with your ID application.",
        "choices": [
            {
                "text": "Accept and explain your situation",
                "outcomes": {
                    "mental": 10,
                    "message": "The manager writes a detailed letter. This will be crucial for your ID application.",
                    "story_flags": ["shelter_letter_obtained"],
                    "inventory": {"Shelter Letter": 1}
                }
            },
            {
                "text": "Ask about additional documentation",
                "outcomes": {
                    "mental": 15,
                    "message": "They provide both a letter and information about other services that can help with documentation.",
                    "story_flags": ["shelter_letter_obtained", "service_info_received"],
                    "inventory": {"Shelter Letter": 1, "Service Information": 1}
                },
                "requirements": {
                    "reputation": {"shelters": 2}
                }
            }
        ],
        "requirements": {
            "story_flags": ["id_quest_requirements"]
        },
        "type": "quest"
    },
    "id_quest_social_worker": {
        "id": "id_quest_social_worker",
        "title": "Seeking Assistance",
        "description": "You've decided to seek help from a social worker to navigate the ID application process.",
        "choices": [
            {
                "text": "Explain your situation",
                "outcomes": {
                    "mental": 10,
                    "message": "The social worker listens attentively and offers guidance, building a bond of trust.",
                    "story_flags": ["social_worker_bond"]
                }
            },
            {
                "text": "Be cautious and reserved",
                "outcomes": {
                    "mental": 5,
                    "message": "The social worker provides some basic information but remains distant. A stronger connection is needed.",
                    "story_flags": ["social_worker_met"]
                }
            }
        ],
        "type": "quest"
    },
    "id_quest_application": {
        "id": "id_quest_application",
        "title": "Completing the Application",
        "description": "You're ready to submit your ID application.  Do you have all the required documents?",
        "choices": [
            {
                "text": "Submit the application",
                "outcomes": {
                    "mental": 20,
                    "message": "You submit the application, feeling a sense of accomplishment and hope for a positive outcome.",
                    "story_flags": ["id_quest_completed", "social_worker_network"]
                },
                "requirements": {
                    "story_flags": ["social_worker_bond"]
                }
            }
        ],
        "type": "quest"
    },
    "id_quest_celebration": {
        "id": "id_quest_celebration",
        "title": "A New Beginning",
        "description": "With your new ID in hand, you feel a weight lift from your shoulders. New possibilities seem to open up before you.",
        "choices": [
            {
                "text": "Visit the employment center",
                "outcomes": {
                    "job_prospects": 25,
                    "hope": 20,
                    "mental": 15,
                    "message": "You spend time applying for jobs, feeling optimistic now that you have proper identification.",
                    "story_flags": ["job_search_started"]
                }
            },
            {
                "text": "Apply for housing assistance",
                "outcomes": {
                    "housing_prospects": 25,
                    "hope": 20,
                    "mental": 15,
                    "message": "You begin the housing application process, finally able to provide the required documentation.",
                    "story_flags": ["housing_search_started"]
                }
            }
        ],
        "requirements": {
            "story_flags": ["id_quest_completed"]
        },
        "type": "quest"
    }
}