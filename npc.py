"""
NPC system for Hard Times: Ottawa.
Handles all NPC characters, interactions and dialogue.
"""
import time
import json
import os
import random
import logging

class NPC:
    """Represents a non-player character in the game."""
    
    # Possible emotional states for NPCs
    EMOTIONAL_STATES = [
        "neutral", "happy", "sad", "stressed", "angry", 
        "grateful", "worried", "hopeful", "desperate", "content"
    ]
    
    # Types of crises NPCs might experience
    CRISIS_TYPES = [
        "health", "housing", "family", "financial", 
        "safety", "legal", "emotional", "substance"
    ]
    
    def __init__(self, npc_id, name, role, description, location, schedule, dialogue, disposition=50, services=None, personality_traits=None):
        """Initialize an NPC.
        
        Args:
            npc_id (str): Unique identifier for the NPC
            name (str): NPC's name
            role (str): NPC's role (e.g., 'shelter_worker', 'police', 'local')
            description (str): Description of the NPC
            location (str): Primary location where the NPC can be found
            schedule (dict): When the NPC is available (time periods)
            dialogue (dict): NPC's dialogue options
            disposition (int): 0-100 scale of NPC's attitude toward player (default 50)
            services (list): Services this NPC provides (optional)
            personality_traits (dict): NPC personality traits affecting interactions
        """
        # Relationship tracking with other NPCs
        self.npc_relationships = {}  # {npc_id: relationship_value}
        self.personality_state = "neutral"  # Current personality state
        self.mood_modifiers = []  # Temporary effects on personality
        self.last_mood_update = time.time()
        self.stress_level = 0  # 0-100 scale affecting behavior
        self.personality_traits = personality_traits or {
            "empathy": random.randint(30, 70),
            "helpfulness": random.randint(30, 70),
            "trust": random.randint(30, 70),
            "professionalism": random.randint(30, 70),
            "resilience": random.randint(40, 80),  # How well they handle crises
            "openness": random.randint(30, 70)     # Willingness to share personal details
        }
        
        # Initialize base attributes
        self.interactions_history = []  # Track all interactions
        self.memory = {
            "favors_done": 0,          # Track favors done for player
            "favors_received": 0,       # Track favors received from player
            "last_interaction": None,   # Last interaction date
            "promises_kept": 0,         # Track promises player kept
            "promises_broken": 0,       # Track promises player broke
            "trust_incidents": [],      # Major events affecting trust
            "shared_experiences": [],   # Significant shared experiences
            "emotional_state": "neutral",  # NPC's current emotional state
            "personal_crisis": None,    # Current personal challenge
            "player_support": 0,        # How much player has helped during crisis
            "life_changes": [],         # Major changes in NPC's situation
            "shared_struggles": []      # Common hardships faced together
        }
        
        self.relationship_level = 0     # Deeper relationship tracking (-5 to 5)
        self.faction = self._determine_faction(role)  # Determine NPC's faction
        self.npc_id = npc_id
        self.name = name
        self.role = role
        self.description = description
        self.primary_location = location
        self.schedule = schedule
        self.dialogue = dialogue
        self.disposition = disposition
        self.services = services or []
        self.met = False
        
        # Advanced emotional and narrative systems
        self.emotional_state = "neutral"  # Current emotional state
        self.emotional_reasons = []      # Reasons for current emotional state
        self.has_crisis = False          # Is this NPC experiencing a crisis?
        self.crisis = None               # Details of current crisis
        self.crisis_resolution_stage = 0  # Progress in resolving crisis (0-100)
        self.story_hooks = []            # Narrative hooks this NPC can provide
        self.player_actions_remembered = []  # Important player actions this NPC remembers
        
    def is_available(self, location_name, time_period):
        """Check if the NPC is available at the given location and time.
        
        Args:
            location_name (str): Name of the location
            time_period (str): Current time period ('morning', 'afternoon', 'evening', 'night')
            
        Returns:
            bool: True if NPC is available
        """
        # Check if NPC is at this location during this time period
        if location_name in self.schedule and time_period in self.schedule[location_name]:
            return True
        return False
        
    def get_greeting(self, player_reputation):
        """Get an appropriate greeting based on relationship and past interactions.
        
        Args:
            player_reputation (int): Player's reputation with relevant group
            
        Returns:
            str: Greeting dialogue
        """
        # Check if this is the first meeting
        if not self.met:
            self.met = True
            return self.dialogue.get("first_meeting", "Hello there.")
            
        # Determine appropriate greeting based on disposition
        if self.disposition >= 75:
            return random.choice(self.dialogue.get("friendly", ["Good to see you again."]))
        elif self.disposition >= 40:
            return random.choice(self.dialogue.get("neutral", ["Hello."]))
        else:
            return random.choice(self.dialogue.get("unfriendly", ["What do you want?"]))
            
    def get_dialogue(self, topic, player_reputation, context=None):
        """Get dialogue for a specific topic with context awareness.
        
        Args:
            topic (str): Dialogue topic
            player_reputation (int): Player's reputation with relevant group
            context (dict, optional): Additional context (time, location, etc.)
            
        Returns:
            str: Dialogue text for the topic
        """
        if not context:
            context = {}
            
        # Get dialogue based on topic and emotional state
        current_state = self.emotional_state
        if topic in self.dialogue:
            dialogue_options = self.dialogue[topic]
            
            # Check for emotional state specific dialogue
            if isinstance(dialogue_options, dict) and current_state in dialogue_options:
                return random.choice(dialogue_options[current_state])
            
            # If dialogue options are tiered by disposition/reputation
            if isinstance(dialogue_options, dict):
                if player_reputation >= 7 or self.disposition >= 80:
                    tier = "high"
                elif player_reputation >= 3 or self.disposition >= 40:
                    tier = "medium"
                else:
                    tier = "low"
                
                if tier in dialogue_options:
                    return random.choice(dialogue_options[tier])
                    
            # If dialogue options are a simple list
            elif isinstance(dialogue_options, list):
                return random.choice(dialogue_options)
                
        # Default response if topic not found
        return "I don't have anything to say about that."
        
    def modify_disposition(self, amount):
        """Change the NPC's disposition toward the player.
        
        Args:
            amount (int): Amount to change disposition (positive or negative)
        """
        self.disposition = max(0, min(100, self.disposition + amount))
        
    def provide_service(self, service_id, player):
        """Have the NPC provide a service to the player with enhanced validation.
        
        Args:
            service_id (str): The service to provide
            player (Player): Player object
            
        Returns:
            tuple: (success, message) - success is bool, message describes outcome
        """
        # Check if NPC provides this service
        service = next((s for s in self.services if s["id"] == service_id), None)
        if not service:
            return False, f"{self.name} doesn't provide that service."
            
        # Validate service requirements
        if not self._validate_service_requirements(service, player):
            return False, "Service requirements not met."
            
        # Check cooldown if applicable
        if not self._check_service_cooldown(service_id, player):
            return False, "This service is not available yet."
            
        # Apply service effects with validation
        try:
            self._apply_service_effects(service, player)
            
            # Record service usage
            self.record_interaction("service", "positive", {
                "service_id": service_id,
                "location": player.current_location
            })
            
            return True, service.get("success_message", f"{self.name} has provided you with {service_id}.")
        except Exception as e:
            return False, f"Error providing service: {str(e)}"
            
    def _validate_service_requirements(self, service, player):
        """Validate if player meets service requirements."""
        if "cost" in service and service["cost"] > 0:
            if not player.spend_money(service["cost"], validate_only=True):
                return False
                
        if "min_disposition" in service and self.disposition < service["min_disposition"]:
            return False
            
        if "required_items" in service:
            for item, count in service["required_items"].items():
                if not player.has_item(item, count):
                    return False
                    
        return True
        
    def _check_service_cooldown(self, service_id, player):
        """Check if service is available based on cooldown."""
        last_use = self.memory.get("service_cooldowns", {}).get(service_id)
        if last_use:
            cooldown = self.services[service_id].get("cooldown", 0)
            if time.time() - last_use < cooldown:
                return False
        return True
                
        if not service:
            return False, f"{self.name} doesn't provide that service."
            
        # Check service requirements
        if "cost" in service and service["cost"] > 0:
            if not player.spend_money(service["cost"]):
                return False, "You don't have enough money for that service."
                
        if "min_disposition" in service and self.disposition < service["min_disposition"]:
            return False, f"{self.name} doesn't trust you enough for that yet."
            
        # Apply service effects
        for effect_type, value in service.get("effects", {}).items():
            if effect_type == "health":
                player.health += value
            elif effect_type == "satiety" or effect_type == "hunger":
                # Convert hunger to satiety (negative hunger means increased satiety)
                if effect_type == "hunger":
                    # For backward compatibility
                    player.satiety = min(100, player.satiety - value)  # Negative value increases satiety
                else:
                    player.satiety = min(100, player.satiety + value)
            elif effect_type == "energy":
                player.energy += value
            elif effect_type == "mental":
                player.mental += value
            elif effect_type == "hygiene":
                player.hygiene += value
            elif effect_type == "job_prospects":
                player.increase_job_prospects(value)
            elif effect_type == "housing_prospects":
                player.increase_housing_prospects(value)
            elif effect_type == "item":
                # Value should be tuple (item_name, quantity)
                player.add_item(value[0], value[1])
                
        # Ensure player stats stay within bounds
        player._clamp_stats()
        
        return True, service.get("success_message", f"{self.name} has provided you with {service_id}.")
        
    def _determine_faction(self, role):
        """Determine NPC's faction based on role."""
        faction_map = {
            "shelter_worker": "shelters",
            "social_worker": "social_services",
            "police": "police",
            "business_owner": "businesses",
            "community_organizer": "community",
            "experienced_homeless": "streets"
        }
        return faction_map.get(role, "community")
        
    def record_interaction(self, interaction_type, outcome, details=None):
        """Record an interaction with the player.
        
        Args:
            interaction_type (str): Type of interaction (conversation, service, etc.)
            outcome (str): Result of the interaction
            details (dict, optional): Additional details about the interaction
        """
        # Create interaction record
        interaction_record = {
            "type": interaction_type,
            "outcome": outcome,
            "timestamp": time.time(),
            "details": details or {}
        }
        
        # Store the interaction in history
        self.interactions_history.append(interaction_record)
        self.memory["last_interaction"] = time.time()
        
        # Process relationship impact based on outcome
        if outcome == "positive":
            self.modify_disposition(3 + random.randint(0, 2))
            if interaction_type == "favor":
                self.memory["favors_received"] += 1
            elif interaction_type == "help":
                self.memory["player_support"] += 1
        elif outcome == "negative":
            self.modify_disposition(-5 + random.randint(0, 2)) 
            if interaction_type == "conflict":
                self.memory["trust_incidents"].append(interaction_record)
        elif outcome == "neutral":
            self.modify_disposition(1)
            
        # Record significant events
        if details and details.get("significant", False):
            if interaction_type == "shared_hardship":
                self.memory["shared_struggles"].append(details)
            elif interaction_type == "life_event":
                self.memory["life_changes"].append(details)
            elif interaction_type == "promise":
                if details.get("kept", False):
                    self.memory["promises_kept"] += 1
                else:
                    self.memory["promises_broken"] += 1

    def calculate_interaction_outcome(self, action_type, player_stats):
        """Calculate success and effects of an interaction based on personality and player stats.
        
        Args:
            action_type (str): Type of interaction
            player_stats (dict): Relevant player statistics
            
        Returns:
            tuple: (success_chance, effect_modifier)
        """
        base_chance = 50
        effect_mod = 1.0
        
        if action_type == "request_help":
            base_chance += self.personality_traits["helpfulness"]
            effect_mod *= (self.disposition / 50)
        elif action_type == "share_story":
            base_chance += self.personality_traits["empathy"]
            effect_mod *= (player_stats.get("charisma", 50) / 50)
        elif action_type == "build_trust":
            base_chance += self.personality_traits["trust"]
            effect_mod *= (player_stats.get("social_status", 50) / 50)
            
        return min(90, max(10, base_chance)), effect_mod
        
    def process_relationship_change(self, interaction_result, magnitude=1, interaction_type=None):
        """Update relationship based on interaction result with memory and history.
        
        Args:
            interaction_result (str): 'positive' or 'negative'
            magnitude (float): Strength of the effect
            interaction_type (str, optional): Type of interaction causing change
        """
        if interaction_result == "positive":
            base_change = 0.2 * magnitude
            disposition_change = 5 * magnitude
            
            # Adjust based on personality traits
            if self.personality_traits["empathy"] > 60:
                base_change *= 1.2
                
            # Adjust based on current emotional state
            if self.emotional_state in ["grateful", "happy"]:
                base_change *= 1.3
            elif self.emotional_state in ["stressed", "angry"]:
                base_change *= 0.7
                
            # Apply relationship changes
            self.relationship_level = min(5, self.relationship_level + base_change)
            self.disposition = min(100, self.disposition + disposition_change)
            
            # Record significant positive interactions
            if magnitude >= 2:
                self.memory["significant_interactions"].append({
                    "type": interaction_type,
                    "result": "positive",
                    "timestamp": time.time(),
                    "relationship_level": self.relationship_level
                })
        else:
            self.relationship_level = max(-5, self.relationship_level - (0.3 * magnitude))
            self.disposition = max(0, self.disposition - (7 * magnitude))
            
    def get_service_availability(self, service_id, player_stats):
        """Check if a service is available based on relationship and player stats.
        
        Args:
            service_id (str): Service identifier
            player_stats (dict): Player's current stats
            
        Returns:
            tuple: (available, reason)
        """
        service = next((s for s in self.services if s["id"] == service_id), None)
        if not service:
            return False, "Service not offered"
            
        if "min_disposition" in service and self.disposition < service["min_disposition"]:
            return False, f"Requires better relationship (Current: {self.disposition})"
            
        if "min_reputation" in service and player_stats.get("reputation", 0) < service["min_reputation"]:
            return False, "Insufficient reputation"
            
        return True, "Available"
        
    def update_relationship(self, action_type, value):
        """Update relationship based on player actions.
        
        Args:
            action_type (str): Type of action (promise, favor, etc.)
            value (int): Positive or negative value of action
        """
        if action_type == "promise_kept":
            self.memory["promises_kept"] += 1
            self.relationship_level = min(5, self.relationship_level + 0.5)
        elif action_type == "promise_broken":
            self.memory["promises_broken"] += 1
            self.relationship_level = max(-5, self.relationship_level - 1)
        elif action_type == "favor":
            if value > 0:
                self.memory["favors_received"] += 1
            else:
                self.memory["favors_done"] += 1
            self.relationship_level = min(5, max(-5, self.relationship_level + value * 0.3))
            
    def get_relationship_dialogue(self):
        """Get dialogue based on relationship level."""
        if self.relationship_level >= 4:
            return "trusted_friend"
        elif self.relationship_level >= 2:
            return "friend"
        elif self.relationship_level >= 0:
            return "neutral"
        elif self.relationship_level >= -2:
            return "unfriendly"
        else:
            return "hostile"
            
    def remember_significant_event(self, event_type, details):
        """Record a significant event in NPC's memory.
        
        Args:
            event_type (str): Type of significant event
            details (dict): Event details to remember
        """
        event_record = {
            "type": event_type,
            "details": details,
            "timestamp": time.time()
        }
        
        self.memory["shared_experiences"].append(event_record)
        
        # Also store for narrative purposes
        if details.get("significant", False) or event_type in ["quest_completion", "crisis_resolution"]:
            self.player_actions_remembered.append(event_record)
            
    def set_emotional_state(self, state, reason=None):
        """Set the NPC's emotional state.
        
        Args:
            state (str): New emotional state (should be one of EMOTIONAL_STATES)
            reason (str, optional): Reason for the emotional state
        """
        if state in self.EMOTIONAL_STATES:
            self.emotional_state = state
            if reason:
                self.emotional_reasons.append({
                    "state": state,
                    "reason": reason,
                    "timestamp": time.time()
                })
                
    def trigger_crisis(self, crisis_type, description, severity=5):
        """Put the NPC into a crisis state.
        
        Args:
            crisis_type (str): Type of crisis (should be one of CRISIS_TYPES)
            description (str): Description of the crisis situation
            severity (int): Severity of crisis (1-10)
        
        Returns:
            bool: True if crisis was set, False if invalid type
        """
        if crisis_type not in self.CRISIS_TYPES:
            return False
            
        self.has_crisis = True
        self.crisis = {
            "type": crisis_type,
            "description": description,
            "severity": severity,
            "start_time": time.time(),
            "help_attempts": 0,
            "player_involved": False
        }
        
        # Set appropriate emotional state based on crisis
        emotional_map = {
            "health": "worried",
            "housing": "stressed",
            "family": "sad",
            "financial": "stressed",
            "safety": "worried",
            "legal": "stressed",
            "emotional": "sad",
            "substance": "desperate"
        }
        
        self.set_emotional_state(
            emotional_map.get(crisis_type, "stressed"), 
            f"Experiencing a {crisis_type} crisis"
        )
        
        # Reset crisis resolution
        self.crisis_resolution_stage = 0
        
        return True
        
    def resolve_crisis_step(self, help_type, player_involved=True, step_value=25):
        """Move the NPC's crisis resolution forward by one step.
        
        Args:
            help_type (str): Type of help provided
            player_involved (bool): Whether the player was involved in helping
            step_value (int): How much to advance resolution (0-100)
            
        Returns:
            tuple: (success, message, resolved)
        """
        if not self.has_crisis or self.crisis is None:
            return False, "This person isn't currently in crisis.", False
            
        # Record help attempt
        self.crisis["help_attempts"] += 1
        
        if player_involved:
            self.crisis["player_involved"] = True
            
        # Progress resolution
        self.crisis_resolution_stage += step_value
        
        # Check for full resolution
        if self.crisis_resolution_stage >= 100:
            # Crisis resolved
            resolved_crisis = self.crisis
            self.has_crisis = False
            
            # Record in memory
            crisis_memory = {
                "type": resolved_crisis["type"],
                "description": resolved_crisis["description"],
                "severity": resolved_crisis["severity"],
                "player_helped": resolved_crisis["player_involved"],
                "resolved_time": time.time()
            }
            
            self.memory["personal_crisis"] = crisis_memory
            
            # Update emotional state
            if resolved_crisis["player_involved"]:
                self.set_emotional_state("grateful", "Crisis resolved with player's help")
                self.player_actions_remembered.append({
                    "type": "crisis_resolution",
                    "details": {
                        "crisis_type": resolved_crisis["type"],
                        "helped": True,
                        "significant": True
                    },
                    "timestamp": time.time()
                })
                
                # Significant relationship improvement
                self.process_relationship_change("positive", 3)
            else:
                self.set_emotional_state("relieved", "Crisis resolved")
                
            return True, "The crisis has been fully resolved.", True
        else:
            # Crisis improving but not resolved
            self.set_emotional_state("hopeful", "Crisis improving with help")
            return True, "The situation is improving, but more help is needed.", False
            
    def update_npc_relationship(self, other_npc_id, value_change):
        """Update relationship with another NPC.
        
        Args:
            other_npc_id (str): ID of the other NPC
            value_change (float): Change in relationship value
        """
        current = self.npc_relationships.get(other_npc_id, 0)
        self.npc_relationships[other_npc_id] = max(-5, min(5, current + value_change))

    def update_mood(self, time_passed):
        """Update NPC's mood based on time and events.
        
        Args:
            time_passed (float): Hours passed since last update
        """
        current_time = time.time()
        hours_passed = (current_time - self.last_mood_update) / 3600

        # Process mood modifiers
        self.mood_modifiers = [mod for mod in self.mood_modifiers 
                             if current_time - mod["start_time"] < mod["duration"]]
        
        # Update stress based on crisis
        if self.has_crisis:
            self.stress_level = min(100, self.stress_level + (5 * hours_passed))
        else:
            self.stress_level = max(0, self.stress_level - (2 * hours_passed))

        # Update personality state based on stress
        if self.stress_level > 80:
            self.personality_state = "unstable"
        elif self.stress_level > 50:
            self.personality_state = "stressed"
        elif self.stress_level > 20:
            self.personality_state = "tense"
        else:
            self.personality_state = "neutral"

        self.last_mood_update = current_time

    def get_current_personality(self):
        """Get current personality traits modified by state.
        
        Returns:
            dict: Current personality trait values
        """
        base_traits = self.personality_traits.copy()
        
        # Apply state modifiers
        if self.personality_state == "unstable":
            base_traits["empathy"] *= 0.5
            base_traits["trust"] *= 0.5
        elif self.personality_state == "stressed":
            base_traits["helpfulness"] *= 0.7
            base_traits["openness"] *= 0.7
        elif self.personality_state == "tense":
            base_traits["empathy"] *= 0.8
            base_traits["trust"] *= 0.9

        # Apply mood modifiers
        for mod in self.mood_modifiers:
            for trait, change in mod["effects"].items():
                if trait in base_traits:
                    base_traits[trait] = max(0, min(100, base_traits[trait] + change))

        return base_traits

    def add_mood_modifier(self, name, duration, effects):
        """Add a temporary modifier to NPC's mood.
        
        Args:
            name (str): Name of the modifier
            duration (float): Duration in seconds
            effects (dict): Effects on personality traits
        """
        self.mood_modifiers.append({
            "name": name,
            "start_time": time.time(),
            "duration": duration,
            "effects": effects
        })

    def add_story_hook(self, hook_id, title, description, min_relationship=1):
        """Add a narrative hook that this NPC can provide to the player.
        
        Args:
            hook_id (str): Unique identifier for this story hook
            title (str): Short title of the hook
            description (str): Full description of the hook
            min_relationship (int): Minimum relationship level required to unlock
        """
        self.story_hooks.append({
            "id": hook_id,
            "title": title,
            "description": description,
            "min_relationship": min_relationship,
            "revealed": False
        })

class NPCManager:
    """Manages all NPCs in the game."""
    
    def __init__(self):
        """Initialize the NPC manager and load NPC data."""
        self.npcs = {}
        self.npc_quests = {}  # Store NPC-specific quests
        self.completed_quests = set()  # Track completed quests
        self.load_npcs()
        self._load_npc_quests()  # Load NPC quests
        
    def load_npcs(self):
        """Load NPC data from the JSON file."""
        try:
            # Create default NPCs
            default_npcs = {
                "shelter_worker": {
                    "id": "shelter_worker",
                    "name": "Maria",
                    "role": "shelter_worker",
                    "description": "A compassionate shelter worker who's seen it all but still maintains a positive attitude.",
                    "location": "Downtown",
                    "schedule": {
                        "Downtown": ["morning", "afternoon", "evening"],
                        "ByWard Market": ["night"]
                    },
                    "dialogue": {
                        "first_meeting": "Hello there. My name is Maria. I work at the shelter. Let me know if you need anything.",
                        "friendly": [
                            "Good to see you again! How have you been holding up?",
                            "Hey there! Always nice to see a familiar face."
                        ],
                        "neutral": [
                            "Hello again. Need some help?",
                            "What can I help you with today?"
                        ],
                        "unfriendly": [
                            "Yes?",
                            "What is it?"
                        ],
                        "shelter": {
                            "high": [
                                "We'll always try to make space for you. You've been respectful and helpful around here.",
                                "I've put in a good word with the shelter director about you. They know you're reliable."
                            ],
                            "medium": [
                                "The shelter gets full quickly, especially in bad weather. Try to arrive early.",
                                "We do our best to accommodate everyone, but resources are limited."
                            ],
                            "low": [
                                "The shelter has rules that everyone needs to follow. Respect the staff and other residents.",
                                "If you cause problems here, you might be asked to leave."
                            ]
                        },
                        "food": [
                            "The community kitchen serves lunch from 11:30 to 1:00. They usually have good portions.",
                            "Food bank is open on Tuesdays and Thursdays. You'll need to register but they don't ask many questions."
                        ],
                        "services": {
                            "high": [
                                "Let me tell you about some programs that might help you get back on your feet. There's a job training workshop next Tuesday.",
                                "I can connect you with our housing coordinator. They might be able to fast-track your application."
                            ],
                            "medium": [
                                "We offer basic services here - showers, laundry, mail reception. All free to use during open hours.",
                                "The clinic comes on Wednesdays. You can see a nurse or doctor without health card."
                            ],
                            "low": [
                                "We have emergency services available, but there's usually a waiting list.",
                                "You can use the phone at the front desk to make important calls if you need to."
                            ]
                        }
                    },
                    "services": [
                        {
                            "id": "shower",
                            "name": "Use Shower Facilities",
                            "description": "Clean up and improve your hygiene.",
                            "effects": {
                                "hygiene": 30
                            },
                            "success_message": "You use the shelter's shower facilities and feel much cleaner."
                        },
                        {
                            "id": "meal_voucher",
                            "name": "Meal Voucher",
                            "description": "A voucher for a hot meal at the community kitchen.",
                            "min_disposition": 40,
                            "effects": {
                                "satiety": 25,  # Replaced hunger with satiety
                                "mental": 5
                            },
                            "success_message": "Maria gives you a meal voucher that you can use at the community kitchen."
                        },
                        {
                            "id": "housing_advice",
                            "name": "Housing Advice",
                            "description": "Information about housing programs and applications.",
                            "min_disposition": 60,
                            "effects": {
                                "housing_prospects": 5,
                                "mental": 5
                            },
                            "success_message": "Maria provides valuable advice about housing programs and helps you fill out an application."
                        }
                    ]
                },
                "outreach_worker": {
                    "id": "outreach_worker",
                    "name": "David",
                    "role": "outreach_worker",
                    "description": "An outreach worker who patrols the streets to help those in need. Carries a backpack of supplies.",
                    "location": "Various",
                    "schedule": {
                        "Downtown": ["afternoon"],
                        "ByWard Market": ["evening"],
                        "Lowertown": ["morning"],
                        "Vanier": ["night"],
                        "Overbrook": ["afternoon"]
                    },
                    "dialogue": {
                        "first_meeting": "Hi there, I'm David. I work with the street outreach program. Can I help you with anything today?",
                        "friendly": [
                            "Hey, good to see you again! How's everything going?",
                            "Hello friend! What do you need today?"
                        ],
                        "neutral": [
                            "Hello again. Need any supplies today?",
                            "How are you holding up? Need any assistance?"
                        ],
                        "unfriendly": [
                            "Let me know if you need anything.",
                            "What can I help you with?"
                        ],
                        "health": [
                            "If you're not feeling well, we have a mobile health clinic on Thursdays in Lowertown.",
                            "Make sure you're staying hydrated, especially in this weather."
                        ],
                        "resources": {
                            "high": [
                                "Here's a map I've marked with all the resources in the area. This should help you navigate.",
                                "I can refer you directly to our housing coordinator. They have a few emergency units available."
                            ],
                            "medium": [
                                "The resource center on Bank Street has computers you can use to look for jobs or contact family.",
                                "There's a community fridge behind the church on Elgin Street. Anyone can take what they need."
                            ],
                            "low": [
                                "Here's a basic resource guide that lists shelters and meal programs.",
                                "If you need immediate help, call this number or go to the drop-in center."
                            ]
                        }
                    },
                    "services": [
                        {
                            "id": "basic_supplies",
                            "name": "Basic Supplies",
                            "description": "Essential supplies like socks, hygiene items, etc.",
                            "effects": {
                                "hygiene": 10,
                                "item": ["Hygiene Kit", 1]
                            },
                            "success_message": "David gives you some basic supplies including a hygiene kit."
                        },
                        {
                            "id": "first_aid",
                            "name": "First Aid",
                            "description": "Basic first aid for minor injuries or health issues.",
                            "effects": {
                                "health": 15
                            },
                            "success_message": "David provides first aid, treating your minor injuries."
                        },
                        {
                            "id": "resource_referral",
                            "name": "Resource Referral",
                            "description": "Information about services tailored to your needs.",
                            "min_disposition": 30,
                            "effects": {
                                "housing_prospects": 3,
                                "job_prospects": 3,
                                "mental": 5
                            },
                            "success_message": "David provides personalized information about services that could help your situation."
                        }
                    ]
                },
                "café_owner": {
                    "id": "café_owner",
                    "name": "Sam",
                    "role": "business_owner",
                    "description": "The owner of a small café who has a soft spot for those in need but also has to run a business.",
                    "location": "Centretown",
                    "schedule": {
                        "Centretown": ["morning", "afternoon", "evening"],
                        "Glebe": ["morning"]
                    },
                    "dialogue": {
                        "first_meeting": "Welcome to my café. I'm Sam. Can't give away free food, but I might have some work if you're interested.",
                        "friendly": [
                            "Hey, good to see you! How are things going?",
                            "Welcome back! You're looking better today."
                        ],
                        "neutral": [
                            "Hello again. What brings you by today?",
                            "Need something?"
                        ],
                        "unfriendly": [
                            "Look, I'm trying to run a business here.",
                            "Please don't loiter unless you're going to buy something."
                        ],
                        "work": {
                            "high": [
                                "I could use a reliable hand like you. Come by tomorrow morning and I'll have some paid work for you.",
                                "You know, I might be able to offer you some regular shifts if you're interested."
                            ],
                            "medium": [
                                "I sometimes need help with deliveries or cleaning. It's not much, but it's honest work.",
                                "If you come by at closing time, I might have some tasks you can help with in exchange for a meal."
                            ],
                            "low": [
                                "I can't hire someone I don't know. Prove you're reliable and we can talk.",
                                "I have to be careful about who I let work here. My customers are particular."
                            ]
                        },
                        "food": [
                            "At the end of the day, I have to throw out unsold food. Come by around closing time if you need a meal.",
                            "There's a community fridge a few blocks from here where local businesses donate extra food."
                        ]
                    },
                    "services": [
                        {
                            "id": "leftover_food",
                            "name": "Leftover Food",
                            "description": "Unsold food from the day that would otherwise be thrown out.",
                            "min_disposition": 30,
                            "effects": {
                                "satiety": 20,  # Replaced hunger with satiety
                                "mental": 5
                            },
                            "success_message": "Sam gives you some unsold pastries and a sandwich from the day's leftovers."
                        },
                        {
                            "id": "temp_work",
                            "name": "Temporary Work",
                            "description": "A few hours of work at the café for cash.",
                            "min_disposition": 50,
                            "effects": {
                                "energy": -20,
                                "money": 20,
                                "job_prospects": 5,
                                "mental": 10
                            },
                            "success_message": "You spend a few hours working at the café and earn some cash. The work experience could be valuable."
                        },
                        {
                            "id": "job_reference",
                            "name": "Job Reference",
                            "description": "A reference for other job applications.",
                            "min_disposition": 70,
                            "effects": {
                                "job_prospects": 15,
                                "housing_prospects": 5
                            },
                            "success_message": "Sam agrees to be a reference for your job applications, which significantly improves your prospects."
                        }
                    ]
                },
                "community_organizer": {
                    "id": "community_organizer",
                    "name": "Jordan",
                    "role": "community_organizer",
                    "description": "A dedicated community organizer who works on housing initiatives and advocacy for the homeless.",
                    "location": "Hintonburg",
                    "schedule": {
                        "Hintonburg": ["morning", "afternoon"],
                        "Downtown": ["evening"],
                        "Centretown": ["morning"]
                    },
                    "dialogue": {
                        "first_meeting": "Hi, I'm Jordan. I work with housing initiatives and advocacy for unhoused residents. Let me know if you want to get involved.",
                        "friendly": [
                            "Great to see you! How can I support you today?",
                            "Hello friend! Are you taking care of yourself?"
                        ],
                        "neutral": [
                            "Hello there. Need any information today?",
                            "Good to see you again. How's everything going?"
                        ],
                        "unfriendly": [
                            "Yes? What do you need?",
                            "How can I help you today?"
                        ],
                        "housing": {
                            "high": [
                                "I've been advocating for more transitional housing units. I think I might be able to get you on the priority list.",
                                "There's a new housing program starting next month. I can put your name forward as someone who's shown real initiative."
                            ],
                            "medium": [
                                "Housing is tough right now, but there are a few programs you might qualify for. Let's look at the requirements.",
                                "The waiting lists are long, but I know which applications get processed faster. I can show you how to apply."
                            ],
                            "low": [
                                "To get housing, you'll need ID and some documentation. Start by getting those basics in order.",
                                "Shelter beds are limited, but at least they provide a temporary solution while you work on something more permanent."
                            ]
                        },
                        "advocacy": [
                            "We're organizing a community forum next week about affordable housing. Your perspective would be valuable.",
                            "Sometimes sharing your story can help change public perception and policy. Would you be interested in talking to some community leaders?"
                        ]
                    },
                    "services": [
                        {
                            "id": "housing_application",
                            "name": "Housing Application Assistance",
                            "description": "Help filling out housing applications correctly.",
                            "effects": {
                                "housing_prospects": 10,
                                "mental": 5
                            },
                            "success_message": "Jordan helps you complete housing applications, significantly improving your chances."
                        },
                        {
                            "id": "advocacy_participation",
                            "name": "Participate in Advocacy",
                            "description": "Join advocacy efforts to earn respect and connections.",
                            "min_disposition": 40,
                            "effects": {
                                "housing_prospects": 5,
                                "job_prospects": 5,
                                "mental": 10,
                                "energy": -10
                            },
                            "success_message": "You participate in advocacy work with Jordan, making valuable connections and gaining respect in the community."
                        },
                        {
                            "id": "emergency_housing_referral",
                            "name": "Emergency Housing Referral",
                            "description": "Referral to emergency housing program.",
                            "min_disposition": 70,
                            "effects": {
                                "housing_prospects": 20,
                                "mental": 15
                            },
                            "success_message": "Jordan gives you a priority referral to an emergency housing program, significantly improving your housing situation."
                        }
                    ]
                },
                "experienced_homeless": {
                    "id": "experienced_homeless",
                    "name": "Ray",
                    "role": "experienced_homeless",
                    "description": "An older individual who has been homeless for years and knows all the ins and outs of street survival.",
                    "location": "Various",
                    "schedule": {
                        "Lowertown": ["afternoon", "night"],
                        "Downtown": ["morning"],
                        "ByWard Market": ["evening"],
                        "Lebreton Flats": ["night"]
                    },
                    "dialogue": {
                        "first_meeting": "Hey there, newbie. Name's Ray. Been on these streets for more years than I care to count. You look like you could use some advice.",
                        "friendly": [
                            "Hey kid, good to see you're still hanging in there!",
                            "Well look who it is! Still surviving the streets, eh?"
                        ],
                        "neutral": [
                            "Oh, it's you again. What's up?",
                            "Need something?"
                        ],
                        "unfriendly": [
                            "What do you want now?",
                            "I'm not a charity, you know."
                        ],
                        "survival": {
                            "high": [
                                "Listen, I'm gonna tell you my best spots. Behind the Italian restaurant on Preston, they throw out good food at 10 PM sharp.",
                                "There's an abandoned maintenance room in the parking garage on Slater. You can access it from the service door and it's warm in winter."
                            ],
                            "medium": [
                                "The library is good during the day. Warm, quiet, and the staff usually won't bother you if you're not causing trouble.",
                                "When it rains, the overhang behind the mall is dry and the security only checks there once a night around midnight."
                            ],
                            "low": [
                                "You gotta be careful where you sleep. Some areas get checked by police, others have people who might take your stuff.",
                                "Always have a backup plan for where to go. Weather changes, people kick you out, you need options."
                            ]
                        },
                        "police": [
                            "If the cops come around, be polite but don't volunteer information. Know your rights but don't argue.",
                            "Different cops treat us differently. Some are decent, some make it their mission to move us along. Learn which is which."
                        ],
                        "resources": [
                            "The mission on Murray Street has showers on Tuesdays and Thursdays. Go early though, line gets long.",
                            "Community health center doesn't ask for ID or health card. They're good people there."
                        ]
                    },
                    "services": [
                        {
                            "id": "survival_tips",
                            "name": "Survival Tips",
                            "description": "Practical advice for urban survival.",
                            "effects": {
                                "skills": {"resourcefulness": 1},
                                "mental": 5
                            },
                            "success_message": "Ray shares some hard-earned wisdom about surviving on the streets that could prove very valuable."
                        },
                        {
                            "id": "secret_locations",
                            "name": "Secret Locations",
                            "description": "Information about hidden resources and safe spots.",
                            "min_disposition": 60,
                            "effects": {
                                "skills": {"navigation": 1},
                                "housing_prospects": 5
                            },
                            "success_message": "Ray reveals several hidden spots for sleeping safely and finding resources that few people know about."
                        },
                        {
                            "id": "share_supplies",
                            "name": "Share Supplies",
                            "description": "Share some of Ray's carefully hoarded supplies.",
                            "min_disposition": 80,
                            "effects": {
                                "item": ["Warm Clothes", 1],
                                "item": ["Food", 1]
                            },
                            "success_message": "In a rare show of generosity, Ray shares some valuable supplies with you from a carefully hidden stash."
                        }
                    ]
                },
                "police_officer": {
                    "id": "police_officer",
                    "name": "Officer Chen",
                    "role": "police",
                    "description": "A police officer who patrols various areas. Generally fair but firm in enforcing regulations.",
                    "location": "Various",
                    "schedule": {
                        "Downtown": ["morning", "night"],
                        "ByWard Market": ["evening", "night"],
                        "Centretown": ["afternoon"],
                        "Glebe": ["afternoon"]
                    },
                    "dialogue": {
                        "first_meeting": "Hello there. I'm Officer Chen. I patrol this area regularly. Just keeping things safe, not looking to cause anyone trouble who's not causing trouble.",
                        "friendly": [
                            "Hello again. Everything alright today?",
                            "Good to see you. Staying out of trouble, I hope?"
                        ],
                        "neutral": [
                            "Afternoon. Everything ok here?",
                            "Just doing my rounds. Any issues I should know about?"
                        ],
                        "unfriendly": [
                            "I need you to move along, please.",
                            "This isn't a loitering area."
                        ],
                        "regulations": {
                            "high": [
                                "Look, I understand your situation. As long as you're not blocking access or disturbing anyone, I won't give you trouble.",
                                "There's a warming center opening tonight at the community hall. Just FYI if you need somewhere to go."
                            ],
                            "medium": [
                                "I have to enforce the bylaws, but I'm not out to make your life harder. Just be discreet and considerate.",
                                "Try to avoid sleeping in doorways of businesses. It creates complaints I have to respond to."
                            ],
                            "low": [
                                "You can't camp here. I'll have to ask you to move your belongings.",
                                "This area has had complaints from businesses. I'm going to need you to move along."
                            ]
                        },
                        "safety": [
                            "If anyone's threatening you or stealing your things, you can report it. You have the same rights as anyone else.",
                            "Be careful around the north end of the market after dark. We've had several incidents there recently."
                        ]
                    },
                    "services": [
                        {
                            "id": "safety_information",
                            "name": "Safety Information",
                            "description": "Information about dangerous areas or situations to avoid.",
                            "effects": {
                                "mental": 5
                            },
                            "success_message": "Officer Chen shares some important safety information about areas to avoid and current risks in the city."
                        },
                        {
                            "id": "resource_direction",
                            "name": "Resource Direction",
                            "description": "Directions to legitimate services and resources.",
                            "min_disposition": 40,
                            "effects": {
                                "housing_prospects": 3,
                                "mental": 5
                            },
                            "success_message": "Officer Chen directs you to some legitimate services and resources that might help your situation."
                        },
                        {
                            "id": "incident_report",
                            "name": "File Incident Report",
                            "description": "Report crimes or incidents that affected you.",
                            "min_disposition": 60,
                            "effects": {
                                "mental": 10
                            },
                            "success_message": "Officer Chen takes your report seriously and files it properly, giving you a sense that your concerns matter."
                        }
                    ]
                }
            }
            
            # Try to load NPCs from JSON file
            file_path = os.path.join("data", "npcs.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    npc_data = json.load(f)
            else:
                # Use default NPCs if file doesn't exist
                npc_data = default_npcs
                
                # Ensure data directory exists
                os.makedirs("data", exist_ok=True)
                
                # Write default NPCs to JSON file
                with open(file_path, 'w') as f:
                    json.dump(default_npcs, f, indent=4)
                
            # Create NPC objects
            for npc_id, data in npc_data.items():
                npc = NPC(
                    npc_id=data["id"],
                    name=data["name"],
                    role=data["role"],
                    description=data["description"],
                    location=data["location"],
                    schedule=data["schedule"],
                    dialogue=data["dialogue"],
                    disposition=50,  # Default starting disposition
                    services=data.get("services", [])
                )
                self.npcs[npc_id] = npc
                
        except Exception as e:
            print(f"Error loading NPCs: {e}")
            # Create a minimal set of NPCs if loading fails
            shelter_worker = NPC(
                npc_id="shelter_worker",
                name="Shelter Worker",
                role="shelter_worker",
                description="A staff member at the local shelter.",
                location="Downtown",
                schedule={"Downtown": ["morning", "afternoon", "evening", "night"]},
                dialogue={
                    "first_meeting": "Welcome to the shelter. Let me know if you need anything.",
                    "services": ["We provide basic necessities and a place to sleep."]
                }
            )
            
            outreach_worker = NPC(
                npc_id="outreach_worker",
                name="Outreach Worker",
                role="outreach_worker",
                description="A community outreach worker who helps those in need.",
                location="Various",
                schedule={
                    "Downtown": ["morning", "afternoon"],
                    "ByWard Market": ["evening"]
                },
                dialogue={
                    "first_meeting": "Hello, I'm from the outreach program. Do you need any assistance?",
                    "resources": ["I can help connect you with various services in the city."]
                }
            )
            
            self.npcs = {
                "shelter_worker": shelter_worker,
                "outreach_worker": outreach_worker
            }
    
    def get_npc(self, npc_id):
        """Get an NPC by ID.
        
        Args:
            npc_id (str): NPC's ID
            
        Returns:
            NPC: The NPC object or None if not found
        """
        try:
            if not npc_id:
                logging.warning("Attempted to get NPC with empty ID")
                return None
                
            if not self.npcs:
                logging.warning("NPC dictionary is empty when trying to get an NPC")
                return None
                
            return self.npcs.get(npc_id)
        except Exception as e:
            logging.error(f"Error retrieving NPC {npc_id}: {str(e)}")
            return None
        
    def get_available_npcs(self, location_name, time_period):
        """Get NPCs available at the given location and time.
        
        Args:
            location_name (str): Name of the location
            time_period (str): Current time period
            
        Returns:
            list: List of available NPC objects
        """
        try:
            available_npcs = []
            
            if not self.npcs:
                logging.warning("NPC dictionary is empty when trying to get available NPCs")
                return available_npcs
                
            if not location_name or not time_period:
                logging.warning(f"Invalid location or time parameters: {location_name}, {time_period}")
                return available_npcs
            
            for npc_id, npc in list(self.npcs.items()):
                try:
                    if hasattr(npc, 'is_available') and npc.is_available(location_name, time_period):
                        available_npcs.append(npc)
                except Exception as e:
                    logging.error(f"Error checking availability for NPC {npc_id}: {str(e)}")
                    continue
                    
            return available_npcs
        except Exception as e:
            logging.error(f"Error in get_available_npcs: {str(e)}")
            return []
        
    def get_npc_by_role(self, role):
        """Get NPCs with a specific role.
        
        Args:
            role (str): Role to search for
            
        Returns:
            list: List of NPC objects with the specified role
        """
        return [npc for npc in self.npcs.values() if npc.role == role]
    
    def interact_with_npc(self, npc, player, ui, time_system):
        """Handle player interaction with an NPC. Enhanced with relationship mechanics and time effects.
        
        Args:
            npc (NPC): The NPC to interact with
            player (Player): Player object
            ui (UI): UI object for display
            time_system: Time system for tracking time
            
        Returns:
            bool: True if interaction occurred
        """
        ui.display_divider()
        ui.display_title(f"Talking with {npc.name}")
        ui.display_text(npc.description)
        
        # Determine relevant player reputation based on NPC role
        reputation_group = "public"  # default
        if npc.role == "shelter_worker":
            reputation_group = "shelters"
        elif npc.role in ["outreach_worker", "social_worker", "health_worker"]:
            reputation_group = "services"
            
        player_reputation = player.reputation.get(reputation_group, 0)
        
        # Display greeting
        greeting = npc.get_greeting(player_reputation)
        ui.display_text(f"\n{npc.name}: \"{greeting}\"")
        
        # Check for significant history with this NPC
        has_history = len(npc.interactions_history) > 2
        has_relationship = npc.relationship_level >= 2
        has_shared_experiences = len(npc.memory["shared_experiences"]) > 0
        has_crisis = npc.has_crisis
        
        # Record this interaction
        npc.record_interaction("conversation", "neutral", 
                              {"location": player.current_location, 
                               "time": time_system.get_time_string()})
        
        # Conversation/interaction menu
        while True:
            ui.display_divider()
            ui.display_title("Conversation Options")
            
            options = [
                "1. Ask about resources or services",
                "2. Talk about your situation",
                "3. Ask for specific help"
            ]
            
            # Check for crisis
            if has_crisis:
                # Display a special option if NPC is in crisis
                options.insert(0, f"1. Ask about their troubled demeanor")
                # Shift other option numbers
                for i in range(1, len(options)):
                    options[i] = f"{i+1}{options[i][1:]}"
            
            # Add relationship-specific options
            if has_history:
                options.append(f"{len(options) + 1}. Reminisce about past experiences")
            
            if has_relationship:
                options.append(f"{len(options) + 1}. Ask about personal life")
            
            # Check for available personal quests
            npc_quests_available = self._check_available_quests(npc, player)
            if npc_quests_available:
                options.append(f"{len(options) + 1}. Discuss specific matters")
            
            if npc.services:
                options.append(f"{len(options) + 1}. Request a service")
                
            options.append(f"{len(options) + 1}. End conversation")
            
            for option in options:
                ui.display_text(option)
                
            choice = input("\nWhat would you like to do? ")
            
            if choice == "1" and has_crisis:
                # Crisis option - help NPC with their personal crisis
                ui.display_text(f"\nYou ask {npc.name} what's troubling them, noticing they seem distressed.")
                
                # Display crisis details
                ui.display_text(f"\n{npc.name}: \"I... I'm dealing with some {npc.crisis['type']} issues right now.\"")
                ui.display_text(f"\n{npc.crisis['description']}")
                
                # Crisis help options based on type
                ui.display_title("How would you like to help?")
                help_options = []
                
                if npc.crisis['type'] == "health":
                    help_options = [
                        {"text": "Offer to get them medical supplies", "type": "practical", "value": 25, "cost": {"money": 10}},
                        {"text": "Share medical advice or resources you've learned", "type": "information", "value": 15, "cost": {}},
                        {"text": "Listen and provide emotional support", "type": "emotional", "value": 10, "cost": {"time": 1}}
                    ]
                elif npc.crisis['type'] == "housing":
                    help_options = [
                        {"text": "Share information about shelter options", "type": "information", "value": 20, "cost": {}},
                        {"text": "Offer to help them look for housing", "type": "practical", "value": 25, "cost": {"energy": 15}},
                        {"text": "Provide emotional support during their housing crisis", "type": "emotional", "value": 15, "cost": {"time": 1}}
                    ]
                elif npc.crisis['type'] == "family":
                    help_options = [
                        {"text": "Offer advice based on your own experiences", "type": "information", "value": 15, "cost": {}},
                        {"text": "Listen and provide emotional support", "type": "emotional", "value": 25, "cost": {"time": 1}},
                        {"text": "Offer to help with a specific task related to their family issue", "type": "practical", "value": 20, "cost": {"energy": 10}}
                    ]
                elif npc.crisis['type'] == "financial":
                    help_options = [
                        {"text": "Share information about financial assistance", "type": "information", "value": 20, "cost": {}},
                        {"text": "Contribute a small amount of money", "type": "practical", "value": 35, "cost": {"money": 15}},
                        {"text": "Listen and provide emotional support", "type": "emotional", "value": 10, "cost": {"time": 1}}
                    ]
                elif npc.crisis['type'] == "safety":
                    help_options = [
                        {"text": "Offer to accompany them to a safer location", "type": "practical", "value": 30, "cost": {"energy": 20}},
                        {"text": "Share information about safe spaces", "type": "information", "value": 15, "cost": {}},
                        {"text": "Listen and provide emotional support", "type": "emotional", "value": 10, "cost": {"time": 1}}
                    ]
                elif npc.crisis['type'] == "legal":
                    help_options = [
                        {"text": "Share information about legal aid resources", "type": "information", "value": 25, "cost": {}},
                        {"text": "Offer to help navigate paperwork or procedures", "type": "practical", "value": 20, "cost": {"energy": 15}},
                        {"text": "Listen and provide emotional support", "type": "emotional", "value": 10, "cost": {"time": 1}}
                    ]
                elif npc.crisis['type'] == "emotional":
                    help_options = [
                        {"text": "Spend time listening and providing support", "type": "emotional", "value": 35, "cost": {"time": 2}},
                        {"text": "Share coping strategies you've learned", "type": "information", "value": 15, "cost": {}},
                        {"text": "Offer to accompany them to a support group", "type": "practical", "value": 20, "cost": {"energy": 15}}
                    ]
                elif npc.crisis['type'] == "substance":
                    help_options = [
                        {"text": "Share information about recovery resources", "type": "information", "value": 20, "cost": {}},
                        {"text": "Offer to accompany them to a support meeting", "type": "practical", "value": 30, "cost": {"energy": 25}},
                        {"text": "Listen without judgment and provide emotional support", "type": "emotional", "value": 15, "cost": {"time": 1}}
                    ]
                else:
                    help_options = [
                        {"text": "Listen and provide emotional support", "type": "emotional", "value": 15, "cost": {"time": 1}},
                        {"text": "Offer practical assistance", "type": "practical", "value": 20, "cost": {"energy": 15}},
                        {"text": "Share relevant information or resources", "type": "information", "value": 10, "cost": {}}
                    ]
                
                # Add option to decline
                help_options.append({"text": "Express sympathy but explain you can't help right now", "type": "decline", "value": 0, "cost": {}})
                
                # Display options
                for i, option in enumerate(help_options, 1):
                    cost_text = ""
                    for cost_type, cost_value in option["cost"].items():
                        cost_text += f" ({cost_type}: -{cost_value})"
                    ui.display_text(f"{i}. {option['text']}{cost_text}")
                
                help_choice = input("\nHow would you like to help? ")
                try:
                    help_index = int(help_choice) - 1
                    if 0 <= help_index < len(help_options):
                        chosen_help = help_options[help_index]
                        
                        # Check if player can afford the cost
                        can_afford = True
                        for cost_type, cost_value in chosen_help["cost"].items():
                            if cost_type == "money" and player.money < cost_value:
                                can_afford = False
                                ui.display_error(f"You don't have enough money (need {cost_value}).")
                            elif cost_type == "energy" and player.energy < cost_value:
                                can_afford = False
                                ui.display_error(f"You don't have enough energy (need {cost_value}).")
                            elif cost_type == "time" and time_system.get_time_value() > 21:  # Late at night
                                can_afford = False
                                ui.display_error("It's too late in the day for this kind of help.")
                        
                        if can_afford:
                            # Apply costs
                            for cost_type, cost_value in chosen_help["cost"].items():
                                if cost_type == "money":
                                    player.spend_money(cost_value)
                                elif cost_type == "energy":
                                    player.energy -= cost_value
                            
                            # Process help
                            if chosen_help["type"] == "decline":
                                ui.display_text("\nYou express sympathy but explain that you're not in a position to help right now.")
                                ui.display_text(f"\n{npc.name} looks disappointed but says they understand.")
                                npc.modify_disposition(-3)
                                player.mental -= 3  # Guilt from not helping
                            else:
                                # Apply help effects
                                success, message, resolved = npc.resolve_crisis_step(
                                    chosen_help["type"], 
                                    player_involved=True, 
                                    step_value=chosen_help["value"]
                                )
                                
                                if success:
                                    ui.display_text(f"\nYou help {npc.name} with their {npc.crisis['type']} crisis.")
                                    ui.display_success(message)
                                    
                                    # Relationship impact based on help value
                                    impact = chosen_help["value"] / 10
                                    npc.process_relationship_change("positive", impact)
                                    
                                    # Mental boost for player from helping others
                                    player.mental += 5 + (impact * 2)
                                    
                                    # Record significant event if resolved
                                    if resolved:
                                        player.story_flags.append(f"helped_{npc.npc_id}_crisis")
                                        npc.remember_significant_event("crisis_help", {
                                            "crisis_type": npc.crisis['type'],
                                            "fully_resolved": True,
                                            "help_type": chosen_help["type"],
                                            "significant": True
                                        })
                                    else:
                                        npc.remember_significant_event("crisis_help", {
                                            "crisis_type": npc.crisis['type'],
                                            "help_type": chosen_help["type"]
                                        })
                                else:
                                    ui.display_error(message)
                        
                    else:
                        ui.display_error("Invalid choice.")
                except ValueError:
                    ui.display_error("Please enter a number.")
                
                input("\nPress Enter to continue...")
                
            elif choice == "1":
                # Ask about resources
                topics = {
                    "shelter": "shelter options",
                    "food": "finding food",
                    "services": "available services",
                    "health": "healthcare options"
                }
                
                ui.display_title("Ask About")
                for i, (topic_id, topic_name) in enumerate(topics.items(), 1):
                    ui.display_text(f"{i}. {topic_name}")
                ui.display_text(f"{len(topics) + 1}. Back")
                
                topic_choice = input("\nWhat would you like to ask about? ")
                try:
                    topic_index = int(topic_choice) - 1
                    if 0 <= topic_index < len(topics):
                        topic_id = list(topics.keys())[topic_index]
                        response = npc.get_dialogue(topic_id, player_reputation)
                        ui.display_text(f"\n{npc.name}: \"{response}\"")
                        npc.modify_disposition(1)  # Slight disposition increase for conversation
                        player.mental += 2  # Small mental boost for social interaction
                        input("\nPress Enter to continue...")
                    elif topic_index == len(topics):
                        continue  # Back to main conversation menu
                    else:
                        ui.display_error("Invalid choice.")
                except ValueError:
                    ui.display_error("Please enter a number.")
                    
            elif choice == "2":
                # Talk about your situation
                ui.display_text("\nYou share some details about your current situation and challenges.")
                
                # Determine NPC's response based on disposition/role
                if npc.disposition >= 60:
                    ui.display_text(f"\n{npc.name} listens sympathetically and offers some encouraging words.")
                    ui.display_text("The conversation is therapeutic and you feel a bit better afterward.")
                    player.mental += 5
                    npc.modify_disposition(2)
                else:
                    ui.display_text(f"\n{npc.name} listens politely but seems a bit guarded.")
                    ui.display_text("You feel slightly better having talked to someone, at least.")
                    player.mental += 2
                    npc.modify_disposition(1)
                    
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                # Ask for specific help
                ui.display_text("\nYou ask if there's any specific way they can help you right now.")
                
                # Response based on NPC role and disposition
                if npc.role == "shelter_worker" and npc.disposition >= 50:
                    ui.display_text(f"\n{npc.name}: \"I can put your name on the priority list for tonight's shelter beds.\"")
                    ui.display_success("Your chances of getting a shelter bed tonight have improved.")
                    player.mental += 5
                elif npc.role == "outreach_worker":
                    ui.display_text(f"\n{npc.name}: \"I have some hygiene supplies and a resource guide I can give you.\"")
                    player.add_item("Hygiene Kit", 1)
                    player.add_item("Resource Guide", 1)
                    ui.display_success("You received a Hygiene Kit and Resource Guide.")
                    player.hygiene += 5
                    player.mental += 3
                elif npc.role == "business_owner" and npc.disposition >= 60:
                    ui.display_text(f"\n{npc.name}: \"I might have some work for you later. Check back tomorrow.\"")
                    ui.display_success("Your job prospects have improved slightly.")
                    player.increase_job_prospects(3)
                    player.mental += 3
                elif npc.role == "experienced_homeless":
                    ui.display_text(f"\n{npc.name}: \"Let me tell you where you can find some food tonight without hassle.\"")
                    ui.display_success("You learned about a good spot to find food.")
                    player.increase_skill("foraging", 1)
                    player.mental += 3
                else:
                    ui.display_text(f"\n{npc.name}: \"I wish I could help more, but I'm limited in what I can offer right now.\"")
                    ui.display_text("At least they were honest with you.")
                    
                npc.modify_disposition(1)
                input("\nPress Enter to continue...")
                
            elif choice == "4" and has_history:
                # Reminisce about past experiences
                ui.display_text("\nYou bring up some of your previous interactions and shared experiences.")
                
                # Find most significant shared experience
                if has_shared_experiences:
                    experience = npc.memory["shared_experiences"][-1]
                    ui.display_text(f"\n{npc.name}: \"I remember when we {experience['details'].get('description', 'went through that together')}. That was quite something.\"")
                    ui.display_text("Reminiscing about shared experiences strengthens your connection.")
                    player.mental += 8
                    npc.modify_disposition(3)
                    npc.process_relationship_change("positive", 1.5)
                else:
                    # Generate a memory based on interaction history
                    memory_type = random.choice(["helpful", "challenging", "meaningful"])
                    if memory_type == "helpful":
                        ui.display_text(f"\n{npc.name}: \"I remember when I helped you out when things were tough. I'm glad I could be there for you.\"")
                    elif memory_type == "challenging":
                        ui.display_text(f"\n{npc.name}: \"We've both been through some difficult times, haven't we? It helps to know we're not alone in this.\"")
                    else:
                        ui.display_text(f"\n{npc.name}: \"Our conversations have always been meaningful to me. It's good to connect with someone who understands.\"")
                    
                    player.mental += 5
                    npc.modify_disposition(2)
                    
                # Record this as a significant experience
                npc.remember_significant_event("reminiscing", {
                    "description": "reminisced about past experiences",
                    "location": player.current_location,
                    "time_period": time_system.get_period(),
                    "day": time_system.get_day()
                })
                
                input("\nPress Enter to continue...")
                
            elif choice == "5" and has_relationship:
                # Ask about personal life
                ui.display_text("\nYou ask about their personal life and experiences.")
                
                if npc.role == "shelter_worker":
                    ui.display_text(f"\n{npc.name}: \"I've been working here for seven years now. I originally started as a volunteer after experiencing homelessness myself. It gives me perspective, you know?\"")
                elif npc.role == "outreach_worker":
                    ui.display_text(f"\n{npc.name}: \"This work takes a toll sometimes, but meeting people like you who keep pushing forward despite everything... that's what keeps me going.\"")
                elif npc.role == "business_owner":
                    ui.display_text(f"\n{npc.name}: \"I've had this place for about five years. It's not easy running a small business, but I try to remember that everyone's struggling in their own way.\"")
                elif npc.role == "experienced_homeless":
                    ui.display_text(f"\n{npc.name}: \"Been on the streets going on eight years now. Lost my home after medical bills piled up. I've learned a lot about survival, but it's the loneliness that's hardest.\"")
                else:
                    ui.display_text(f"\n{npc.name} shares some personal details about their life and the path that led them here.")
                
                ui.display_text("\nThe conversation is deeply meaningful. You feel a stronger connection to them after sharing this moment.")
                player.mental += 10
                npc.process_relationship_change("positive", 2.0)
                
                input("\nPress Enter to continue...")
                
            elif choice == "6" and npc_quests_available:
                # Handle NPC-specific quests
                quest = npc_quests_available[0]  # Get first available quest
                ui.display_title(quest["title"])
                ui.display_text(quest["description"])
                
                # Show quest options
                for i, option in enumerate(quest["options"], 1):
                    ui.display_text(f"{i}. {option['text']}")
                
                quest_choice = input("\nWhat would you like to do? ")
                try:
                    option_index = int(quest_choice) - 1
                    if 0 <= option_index < len(quest["options"]):
                        chosen_option = quest["options"][option_index]
                        
                        # Apply effects
                        for effect_type, value in chosen_option.get("effects", {}).items():
                            if effect_type == "relationship":
                                npc.process_relationship_change("positive", value)
                            elif effect_type == "disposition":
                                npc.modify_disposition(value)
                            elif effect_type == "mental":
                                player.mental += value
                            elif effect_type == "item":
                                player.add_item(value[0], value[1])
                            elif effect_type == "money":
                                player.money += value
                            elif effect_type == "quest_flag":
                                player.story_flags.append(value)
                                
                        # Display outcome
                        ui.display_text(f"\n{chosen_option['outcome']}")
                        
                        # Complete quest
                        self._complete_quest(npc, player, quest["id"], option_index)
                    else:
                        ui.display_error("Invalid choice.")
                except ValueError:
                    ui.display_error("Please enter a number.")
                
                input("\nPress Enter to continue...")
            
            elif (choice == "7" and npc_quests_available and npc.services) or \
                 (choice == "6" and not npc_quests_available and npc.services) or \
                 (choice == "5" and not has_relationship and npc.services) or \
                 (choice == "4" and not has_history and npc.services):
                # Request a service
                ui.display_title("Available Services")
                
                available_services = []
                for i, service in enumerate(npc.services, 1):
                    # Check if service has disposition requirement
                    available = True
                    if "min_disposition" in service and npc.disposition < service["min_disposition"]:
                        available = False
                        
                    if available:
                        available_services.append(service)
                        ui.display_text(f"{i}. {service['name']} - {service['description']}")
                    else:
                        ui.display_text(f"{i}. {service['name']} - [Unavailable]", color="red")
                        
                ui.display_text(f"{len(npc.services) + 1}. Back")
                
                service_choice = input("\nWhich service would you like? ")
                try:
                    service_index = int(service_choice) - 1
                    if 0 <= service_index < len(npc.services):
                        service = npc.services[service_index]
                        success, message = npc.provide_service(service["id"], player)
                        
                        if success:
                            ui.display_success(message)
                            npc.modify_disposition(2)
                        else:
                            ui.display_error(message)
                            
                    elif service_index == len(npc.services):
                        continue  # Back to main conversation menu
                    else:
                        ui.display_error("Invalid choice.")
                except ValueError:
                    ui.display_error("Please enter a number.")
                    
                input("\nPress Enter to continue...")
                
            elif choice == str(len(options)):
                # End conversation
                ui.display_text(f"\nYou thank {npc.name} and end the conversation.")
                break
                
            else:
                ui.display_error("Invalid choice.")
                
        return True
        
    def _load_npc_quests(self):
        """Load NPC quests from data or create default ones."""
        try:
            # Default quests if file doesn't exist
            self.npc_quests = {
                "shelter_worker": [
                    {
                        "id": "shelter_supply_run",
                        "title": "Shelter Supply Run",
                        "description": "Maria looks concerned as she sorts through dwindling supplies.\n\n\"We're running low on some essentials at the shelter. I hate to ask, but if you're able to help pick up a donation from the community center across town, I could offer you priority access to services here.\"",
                        "min_relationship": 1,
                        "options": [
                            {
                                "text": "Agree to help with the supply run",
                                "outcome": "You agree to help Maria. She gives you directions to the community center and a letter of authorization. The walk is long but worth it—Maria is extremely grateful when you return with the supplies. Your relationship with the shelter staff has improved significantly.",
                                "effects": {
                                    "relationship": 2,
                                    "disposition": 15,
                                    "mental": 10,
                                    "energy": -15,
                                    "quest_flag": "helped_shelter_supplies"
                                }
                            },
                            {
                                "text": "Politely decline, citing your own struggles",
                                "outcome": "You explain that while you'd like to help, you're struggling to manage your own situation right now. Maria understands but seems disappointed. \"Of course, I understand. You need to take care of yourself first.\"",
                                "effects": {
                                    "relationship": -0.5,
                                    "disposition": -5,
                                    "mental": -3
                                }
                            }
                        ]
                    }
                ],
                "outreach_worker": [
                    {
                        "id": "missing_person",
                        "title": "Someone's Missing",
                        "description": "David looks troubled as he speaks with you.\n\n\"There's an elderly man named Frank who I usually see in this area. He has serious health issues and hasn't been around for days. I'm worried something might have happened to him. Would you help me look around the usual spots? You might notice things I miss.\"",
                        "min_relationship": 2,
                        "options": [
                            {
                                "text": "Agree to help search for Frank",
                                "outcome": "You spend time helping David search for Frank. Eventually, you find him sheltering in an abandoned building, sick with fever. David calls medical help, potentially saving Frank's life. David is deeply grateful for your help and trusts you more now.",
                                "effects": {
                                    "relationship": 2.5,
                                    "disposition": 20,
                                    "mental": 15,
                                    "energy": -20,
                                    "quest_flag": "helped_find_frank"
                                }
                            },
                            {
                                "text": "Offer information about where you've seen similar people",
                                "outcome": "You don't have time to join the search, but you share information about locations where you've seen people seeking shelter. David appreciates the help. \"Thanks, this gives me some new places to check.\"",
                                "effects": {
                                    "relationship": 0.5,
                                    "disposition": 5,
                                    "mental": 5
                                }
                            },
                            {
                                "text": "Suggest David contact the police instead",
                                "outcome": "You suggest that this is really a job for the authorities. David looks disappointed. \"The police don't prioritize these cases, and many people on the street avoid them anyway. But I understand you can't help.\"",
                                "effects": {
                                    "relationship": -1,
                                    "disposition": -10,
                                    "mental": -5
                                }
                            }
                        ]
                    }
                ],
                "café_owner": [
                    {
                        "id": "cafe_vandalism",
                        "title": "Café Trouble",
                        "description": "You notice Sam cleaning up graffiti outside the café, looking frustrated.\n\n\"Third time this month. Some kids think it's fun to target small businesses. I can't afford a security system, and I'm losing customers who think the area isn't safe.\"",
                        "min_relationship": 2,
                        "options": [
                            {
                                "text": "Offer to keep watch at night for a few days",
                                "outcome": "You offer to keep an eye on the café during closing hours for a few nights. On the second night, you spot the teenagers and manage to talk them down, explaining how their actions hurt Sam's livelihood. Sam is incredibly grateful and offers you a steady part-time job at the café.",
                                "effects": {
                                    "relationship": 3,
                                    "disposition": 25,
                                    "mental": 15,
                                    "energy": -25,
                                    "money": 30,
                                    "job_prospects": 20,
                                    "quest_flag": "protected_cafe"
                                }
                            },
                            {
                                "text": "Help clean up the current mess",
                                "outcome": "You spend an hour helping Sam clean up the graffiti. While it doesn't solve the long-term problem, Sam really appreciates the help and gives you a free meal and coffee for your troubles.",
                                "effects": {
                                    "relationship": 1,
                                    "disposition": 10,
                                    "satiety": 25,
                                    "energy": -10,
                                    "mental": 10
                                }
                            }
                        ]
                    }
                ],
                "experienced_homeless": [
                    {
                        "id": "hidden_stash",
                        "title": "Ray's Hidden Stash",
                        "description": "Ray pulls you aside, speaking quietly.\n\n\"I've got a small problem. I hid some of my stuff—nothing illegal, just personal belongings—in a spot near the river. I injured my leg and can't make the climb down there anymore. If you could get it for me, I'd be willing to share some of what's there.\"",
                        "min_relationship": 2,
                        "options": [
                            {
                                "text": "Agree to retrieve Ray's belongings",
                                "outcome": "You follow Ray's detailed directions to a well-hidden spot by the river. It's a difficult climb, but you find a waterproof container with some survival supplies, a few keepsakes, and a surprisingly good winter coat. True to his word, Ray shares the supplies with you and gives you the coat, which will be extremely valuable when winter comes.",
                                "effects": {
                                    "relationship": 2,
                                    "disposition": 20,
                                    "item": ["Winter Coat", 1],
                                    "energy": -15,
                                    "mental": 10,
                                    "quest_flag": "helped_ray_stash"
                                }
                            },
                            {
                                "text": "Politely decline, it sounds risky",
                                "outcome": "You explain that the climb sounds too dangerous for you right now. Ray seems disappointed but understands. \"Fair enough. Gotta look out for yourself first out here.\"",
                                "effects": {
                                    "mental": -5
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Try to load quests from JSON file (future implementation)
            # For now, use the default quests
            
        except Exception as e:
            print(f"Error loading NPC quests: {e}")
            self.npc_quests = {}
    
    def _check_available_quests(self, npc, player):
        """Check if there are available quests for this NPC.
        
        Args:
            npc (NPC): The NPC to check
            player (Player): Player object
            
        Returns:
            list: Available quests
        """
        available_quests = []
        
        # Get quests for this NPC type
        npc_type_quests = self.npc_quests.get(npc.npc_id, [])
        
        for quest in npc_type_quests:
            # Check if quest is already completed
            quest_id = f"{npc.npc_id}_{quest['id']}"
            if quest_id in self.completed_quests:
                continue
                
            # Check relationship requirements
            min_relationship = quest.get("min_relationship", 0)
            if npc.relationship_level < min_relationship:
                continue
                
            # Check quest-specific requirements
            if "requires_flag" in quest and quest["requires_flag"] not in player.story_flags:
                continue
                
            # Quest is available
            available_quests.append(quest)
            
        return available_quests
    
    def _complete_quest(self, npc, player, quest_id, option_index):
        """Mark a quest as completed.
        
        Args:
            npc (NPC): The NPC involved
            player (Player): Player object
            quest_id (str): ID of the quest
            option_index (int): Index of the chosen option
        """
        # Mark quest as completed
        full_quest_id = f"{npc.npc_id}_{quest_id}"
        self.completed_quests.add(full_quest_id)
        
        # Record significant event in NPC memory
        npc.remember_significant_event("quest_completion", {
            "quest_id": quest_id,
            "choice": option_index,
            "day": player.day,
            "location": player.current_location
        })
    
    def update_npcs(self, player, time_system, game_difficulty=5):
        """Update NPCs for the current time step.
        
        Args:
            player: Player object
            time_system: Time system for tracking time
            game_difficulty: Game difficulty level (1-10)
            
        Returns:
            list: Important NPC events that occurred
        """
        important_events = []
        
        # Check if NPCs were properly loaded
        if not self.npcs:
            logging.warning("No NPCs found during update_npcs call")
            return important_events
            
        # Chance of NPC crisis based on difficulty
        crisis_chance = 0.05 + (game_difficulty * 0.01)  # 5%-15% base chance
        
        # Update each NPC
        for npc_id, npc in list(self.npcs.items()):
            try:
                # Determine if this NPC might experience a crisis
                if not getattr(npc, 'has_crisis', False) and random.random() < crisis_chance:
                    # Higher chance for NPCs player has interacted with
                    relationship_factor = 1 + (abs(getattr(npc, 'relationship_level', 0)) * 0.5)
                    adjusted_chance = crisis_chance * relationship_factor
                    
                    if random.random() < adjusted_chance:
                        # Safe access to constants
                        crisis_types = getattr(npc, 'CRISIS_TYPES', ['health', 'housing', 'financial'])
                        crisis_type = random.choice(crisis_types)
                        severity = random.randint(3, 8)
                        
                        # Generate crisis description based on NPC role and crisis type
                        description = self._generate_crisis_description(npc, crisis_type)
                        
                        # Trigger the crisis
                        npc.trigger_crisis(crisis_type, description, severity)
                        
                        # Record important event
                        important_events.append({
                            "type": "npc_crisis",
                            "npc_id": npc.npc_id,
                            "npc_name": npc.name,
                            "crisis_type": crisis_type,
                            "description": description,
                            "severity": severity
                        })
            except Exception as e:
                logging.error(f"Error updating NPC {npc_id}: {str(e)}")
                continue
        
        # Return important events
        return important_events
        
    def _generate_crisis_description(self, npc, crisis_type):
        """Generate a description for an NPC crisis.
        
        Args:
            npc (NPC): The NPC experiencing the crisis
            crisis_type (str): Type of crisis
            
        Returns:
            str: Crisis description
        """
        try:
            npc_name = getattr(npc, 'name', 'Someone')
            npc_role = getattr(npc, 'role', 'unknown')
            
            # Base descriptions by role and crisis type
            crisis_descriptions = {
                "shelter_worker": {
                    "health": f"{npc_name} has been working double shifts and is showing signs of exhaustion. The shelter is understaffed and they've been pushing themselves too hard.",
                    "housing": f"{npc_name} mentions that their landlord is selling the building and all tenants need to move out within 30 days. They're struggling to find affordable housing.",
                    "family": f"{npc_name} seems distracted and worried. They recently received news that a family member is seriously ill.",
                    "financial": f"{npc_name} is having trouble making ends meet on their shelter worker salary. Rising costs have put them in a difficult position.",
                    "safety": f"{npc_name} has been receiving threatening messages from a former shelter resident who was banned for violent behavior.",
                    "legal": f"{npc_name} has been called as a witness in a court case involving a former shelter resident. They're worried about the implications."
                },
                "outreach_worker": {
                    "health": f"{npc_name} has caught a serious illness while working with clients and is trying to continue working despite needing medical care.",
                    "safety": f"{npc_name} was recently threatened while working in a high-risk area. They're concerned about returning but don't want to abandon their clients."
                }
            }
            
            # Get description based on role and crisis type
            if npc_role in crisis_descriptions and crisis_type in crisis_descriptions[npc_role]:
                return crisis_descriptions[npc_role][crisis_type]
                
            # Generic descriptions by crisis type if specific one not found
            generic_descriptions = {
                "health": f"{npc_name} doesn't look well. They mention they've been feeling sick but can't afford to miss work or get proper treatment.",
                "housing": f"{npc_name} reveals they're facing eviction and might soon be homeless themselves if something doesn't change.",
                "family": f"{npc_name} is distracted by family problems. A relative is in trouble and needs their help urgently.",
                "financial": f"{npc_name} is struggling financially and might not be able to make rent this month.",
                "safety": f"{npc_name} seems nervous and reveals they've been threatened by someone and don't feel safe.",
                "legal": f"{npc_name} has been summoned to court for a minor offense but can't afford legal representation.",
                "emotional": f"{npc_name} is clearly going through a rough emotional time, possibly dealing with depression or anxiety.",
                "substance": f"{npc_name} appears to be struggling with substance use issues. You notice signs of addiction affecting their daily life."
            }
            
            return generic_descriptions.get(crisis_type, f"{npc_name} is going through a difficult time right now.")
        except Exception as e:
            logging.error(f"Error generating crisis description: {str(e)}")
            return "Someone is experiencing a personal crisis."
        
    def get_npcs_in_crisis(self, player_relationship_min=0):
        """Get all NPCs currently in crisis, filtered by relationship with player.
        
        Args:
            player_relationship_min (int): Minimum relationship level required
            
        Returns:
            list: NPCs in crisis
        """
        return [npc for npc in self.npcs.values() 
                if npc.has_crisis and npc.relationship_level >= player_relationship_min]
                
    def get_npc_story_hooks(self, player):
        """Get narrative hooks from NPCs that can advance the story.
        
        Args:
            player: Player object
            
        Returns:
            list: Available story hooks
        """
        available_hooks = []
        
        for npc in self.npcs.values():
            # Skip NPCs the player hasn't met
            if not npc.met:
                continue
                
            for hook in npc.story_hooks:
                # Check if hook is already revealed
                if hook["revealed"]:
                    continue
                    
                # Check relationship requirements
                if npc.relationship_level >= hook["min_relationship"]:
                    # Check if hook requires specific player flag
                    if "requires_flag" in hook and hook["requires_flag"] not in player.story_flags:
                        continue
                        
                    # Hook is available
                    hook_info = hook.copy()
                    hook_info["npc_id"] = npc.npc_id
                    hook_info["npc_name"] = npc.name
                    available_hooks.append(hook_info)
                    
        return available_hooks
