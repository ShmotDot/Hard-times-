"""
Events system for Hard Times: Ottawa.
Manages random events, encounters, and their outcomes.
"""

"""
Enhanced events system with journal tracking and impact analysis
"""
from datetime import datetime
import random
import json
import os
from collections import defaultdict

class EventJournal:
    def __init__(self):
        self.entries = []
        self.impact_analysis = defaultdict(list)
        self.recurring_patterns = defaultdict(int)

    def add_entry(self, event, choice, impacts, time_system):
        """Record an event and its impacts."""
        entry = {
            'timestamp': datetime.now(),
            'day': time_system.get_day(),
            'event_id': event.event_id,
            'title': event.title,
            'choice': choice['text'],
            'impacts': impacts,
            'period': time_system.get_period(),
            'weather': time_system.weather
        }
        self.entries.append(entry)
        self._analyze_impact(impacts)

    def _analyze_impact(self, impacts):
        """Analyze the impacts of choices on player wellbeing."""
        for stat, value in impacts.items():
            if isinstance(value, (int, float)):
                self.impact_analysis[stat].append(value)

    def get_insights(self):
        """Generate insights from recorded events."""
        insights = []

        # Analyze patterns
        for stat, values in self.impact_analysis.items():
            if len(values) >= 3:
                avg_impact = sum(values[-3:]) / 3
                if avg_impact < -10:
                    insights.append(f"Your {stat} has been significantly declining recently")
                elif avg_impact > 10:
                    insights.append(f"Your {stat} has been improving lately")

        return insights

import json
import os
import random

class Event:
    """Represents a game event."""

    # Event type constants
    TYPE_GENERAL = "general"
    TYPE_QUEST = "quest"
    TYPE_ENCOUNTER = "encounter"
    TYPE_WEATHER = "weather"
    TYPE_OPPORTUNITY = "opportunity"
    TYPE_CHAIN = "chain"

    def __init__(self, event_id, title, description, choices, requirements=None, type="general", chain_events=None):
        """Initialize an event.

        Args:
            event_id (str): Unique identifier for the event
            title (str): Event title
            description (str): Event description
            choices (list): List of possible choices and their outcomes
            requirements (dict): Requirements for this event to trigger (optional)
            type (str): Event type category
            chain_events (dict): Possible follow-up events based on choices
        """
        self.event_id = event_id
        self.title = title
        self.description = description
        self.choices = choices
        self.requirements = requirements or {}
        self.type = type
        self.chain_events = chain_events or {}

    def process_story_flags(self, player, outcomes):
        """Process story-related flags and effects.

        Args:
            player (Player): Player object
            outcomes (dict): Event outcomes
        """
        if "story_flags" in outcomes:
            for flag in outcomes["story_flags"]:
                player.add_story_flag(flag)

        if "long_term_effects" in outcomes:
            effects = outcomes["long_term_effects"]
            if "unlock_events" in effects:
                player.unlock_story_events(effects["unlock_events"])
            if "modify_reputation" in effects:
                for group, amount in effects["modify_reputation"].items():
                    player.improve_reputation(group, amount)

    def meets_requirements(self, player, time_system, location):
        """Check if this event's requirements are met.

        Args:
            player (Player): Player object
            time_system (TimeSystem): Time system object
            location (Location): Current location

        Returns:
            bool: True if requirements are met
        """
        # Check time period requirement
        if "time_period" in self.requirements:
            required_periods = self.requirements["time_period"]
            if isinstance(required_periods, str):
                required_periods = [required_periods]

            if time_system.get_period() not in required_periods:
                return False

        # Check weather requirement
        if "weather" in self.requirements:
            required_weather = self.requirements["weather"]
            if isinstance(required_weather, str):
                required_weather = [required_weather]

            if time_system.weather not in required_weather:
                return False

        # Check location requirement
        if "location_type" in self.requirements:
            required_location_types = self.requirements["location_type"]
            if isinstance(required_location_types, str):
                required_location_types = [required_location_types]

            # Location types could be implemented with tags on locations
            # For now, we'll use danger level as a proxy for location type
            if "high_danger" in required_location_types and location.danger_level < 7:
                return False
            if "medium_danger" in required_location_types and (location.danger_level < 4 or location.danger_level > 6):
                return False
            if "low_danger" in required_location_types and location.danger_level > 3:
                return False

        # Check player stat requirements
        for stat, requirement in self.requirements.get("player_stats", {}).items():
            if "min" in requirement and getattr(player, stat, 0) < requirement["min"]:
                return False
            if "max" in requirement and getattr(player, stat, 100) > requirement["max"]:
                return False

        # Check inventory requirements
        for item, quantity in self.requirements.get("inventory", {}).items():
            if not player.has_item(item, quantity):
                return False

        return True

class EventManager:
    """Manages game events and encounters."""

    def __init__(self, player, time_system):
        """Initialize the event manager.

        Args:
            player (Player): Player object
            time_system (TimeSystem): Time system object
        """
        self.player = player
        self.time_system = time_system
        self.events = {}
        self.load_events()
        self.event_history = []  # Track which events have occurred
        self.journal = EventJournal()
        self.last_event_type = None
        self.consecutive_similar_events = 0

    def load_events(self):
        """Load event data from the JSON file."""
        try:
            # Create default events
            default_events = {
                "food_search_success": {
                    "id": "food_search_success",
                    "title": "Found Food",
                    "description": "You search through a dumpster behind a restaurant and discover some discarded but still edible food.",
                    "choices": [
                        {
                            "text": "Take the food and eat it now",
                            "outcomes": {
                                "hunger": -20,
                                "health": -5,
                                "mental": 5,
                                "message": "The food satisfies your hunger, though it's not the most hygienic meal."
                            }
                        },
                        {
                            "text": "Take the food and save it for later",
                            "outcomes": {
                                "inventory": {"Food": 1},
                                "message": "You carefully pack the food away for when you might need it more."
                            }
                        },
                        {
                            "text": "Leave it, it doesn't look safe",
                            "outcomes": {
                                "mental": 2,
                                "message": "Better safe than sorry. Your hunger remains, but at least you won't risk getting sick."
                            }
                        }
                    ],
                    "type": "food"
                },
                "kind_stranger": {
                    "id": "kind_stranger",
                    "title": "Kind Stranger",
                    "description": "A passerby notices your situation and approaches with a sympathetic expression.",
                    "choices": [
                        {
                            "text": "Accept their help graciously",
                            "outcomes": {
                                "money": 5,
                                "mental": 10,
                                "message": "They give you $5 and wish you well. The small kindness lifts your spirits."
                            }
                        },
                        {
                            "text": "Ask if they could buy you a meal instead",
                            "outcomes": {
                                "hunger": -30,
                                "mental": 5,
                                "message": "They take you to a nearby fast food place and buy you a meal. You feel much better."
                            }
                        },
                        {
                            "text": "Politely decline",
                            "outcomes": {
                                "mental": 2,
                                "message": "You thank them but explain you'll be okay. They nod respectfully and continue on."
                            }
                        }
                    ],
                    "type": "encounter"
                },
                "police_interaction": {
                    "id": "police_interaction",
                    "title": "Police Interaction",
                    "description": "A police officer approaches and asks you to move along from where you're resting.",
                    "choices": [
                        {
                            "text": "Comply politely and move on",
                            "outcomes": {
                                "energy": -5,
                                "message": "You gather your things and move elsewhere. It's tiring, but at least there's no trouble."
                            }
                        },
                        {
                            "text": "Explain your situation and ask for resources",
                            "outcomes": {
                                "mental": 5,
                                "message": "The officer listens and provides information about a nearby shelter you weren't aware of."
                            },
                            "requirements": {
                                "skills": {"social": 2}
                            }
                        },
                        {
                            "text": "Argue that you have a right to be here",
                            "outcomes": {
                                "mental": -10,
                                "message": "The confrontation becomes tense. Eventually you have to move anyway, and now you're stressed."
                            }
                        }
                    ],
                    "requirements": {
                        "time_period": ["evening", "night"]
                    },
                    "type": "authority"
                },
                "bad_weather": {
                    "id": "bad_weather",
                    "title": "Weather Turns Bad",
                    "description": "The weather suddenly deteriorates. Rain begins to pour down heavily, and you need to find shelter quickly.",
                    "choices": [
                        {
                            "text": "Rush to the nearest overpass for cover",
                            "outcomes": {
                                "energy": -10,
                                "message": "You make it to an overpass just in time. It's not comfortable, but you stay relatively dry."

                            }
                        },
                        {
                            "text": "Try to make it to a public building",
                            "outcomes": {
                                "health": -5,
                                "energy": -15,
                                "hygiene": -10,
                                "message": "You get soaked before finding a library to dry off in. At least you're inside now."
                            }
                        },
                        {
                            "text": "Use a tarp from your inventory",
                            "outcomes": {
                                "message": "You quickly create a makeshift shelter with your tarp. It's not perfect, but it keeps the worst of the rain off."
                            },
                            "requirements": {
                                "inventory": {"Tarp": 1}
                            }
                        }
                    ],
                    "requirements": {
                        "weather": ["rain", "storm"]
                    },
                    "type": "weather"
                },
                "free_meal_program": {
                    "id": "free_meal_program",
                    "title": "Community Meal Program",
                    "description": "You notice a sign for a free community meal being served at a nearby church.",
                    "choices": [
                        {
                            "text": "Go to the meal service",
                            "outcomes": {
                                "hunger": -40,
                                "mental": 10,
                                "message": "You enjoy a hot meal and brief conversation with others. The volunteers are kind and non-judgmental."
                            }
                        },
                        {
                            "text": "Volunteer to help in exchange for food",
                            "outcomes": {
                                "hunger": -35,
                                "mental": 15,
                                "skills": {"social": 1},
                                "message": "You help serve others before eating yourself. The organizers appreciate your help and remember your face."
                            }
                        },
                        {
                            "text": "Skip it and look elsewhere",
                            "outcomes": {
                                "message": "You decide not to attend and continue on your way."
                            }
                        }
                    ],
                    "requirements": {
                        "time_period": ["afternoon", "evening"]
                    },
                    "type": "food"
                },
                "theft_attempt": {
                    "id": "theft_attempt",
                    "title": "Theft Attempt",
                    "description": "While resting, you notice someone trying to steal your backpack.",
                    "choices": [
                        {
                            "text": "Confront them directly",
                            "outcomes": {
                                "energy": -10,
                                "mental": -5,
                                "message": "You shout and grab your bag. The thief runs off, but the confrontation leaves you shaken."
                            }
                        },
                        {
                            "text": "Call for help",
                            "outcomes": {
                                "mental": -10,
                                "message": "Your shouts attract attention. The thief flees, but some passersby look at you with suspicion."
                            }
                        },
                        {
                            "text": "Try to chase them",
                            "outcomes": {
                                "energy": -20,
                                "mental": -5,
                                "message": "You chase after them, eventually recovering your belongings, but you're exhausted."
                            },
                            "requirements": {
                                "player_stats": {"energy": {"min": 40}}
                            }
                        }
                    ],
                    "requirements": {
                        "location_type": ["high_danger", "medium_danger"],
                        "time_period": ["evening", "night"]
                    },
                    "type": "danger"
                },
                "lost_id_discovery": {
                    "id": "lost_id_discovery",
                    "title": "Lost ID Realization",
                    "description": "While checking your belongings, you realize your ID is missing. Without it, accessing many services will be nearly impossible.",
                    "choices": [
                        {
                            "text": "Try to remember where you last had it",
                            "outcomes": {
                                "energy": -5,
                                "message": "You recall having it at the shelter last week. It might have been stolen or lost during your stay there.",
                                "story_flags": ["id_quest_started"]
                            }
                        },
                        {
                            "text": "Ask nearby people if they've seen an ID",
                            "outcomes": {
                                "energy": -10,
                                "mental": -5,
                                "message": "No one has seen your ID, but someone mentions that replacing lost IDs is extremely difficult when you're homeless.",
                                "story_flags": ["id_quest_started"]
                            }
                        },
                        {
                            "text": "Make a mental note to look into ID replacement",
                            "outcomes": {
                                "message": "You decide to prioritize getting a new ID. It will be crucial for accessing services and eventually finding employment.",
                                "story_flags": ["id_quest_started"]
                            }
                        }
                    ],
                    "requirements": {
                        "time_period": ["morning", "afternoon", "evening"]
                    },
                    "type": "quest"
                },
                "lantern_rumor": {
                    "id": "lantern_rumor",
                    "title": "Whispers of The Lantern",
                    "description": "While at a community meal, you overhear two people talking about a place called 'The Lantern' - supposedly a safe haven for those in need.",
                    "choices": [
                        {
                            "text": "Ask them directly about The Lantern",
                            "outcomes": {
                                "mental": 5,
                                "message": "They seem hesitant at first but tell you it's a community-run space where people look out for each other. They don't share the exact location but mention it's somewhere in the east end.",
                                "story_flags": ["lantern_quest_started"]
                            }
                        },
                        {
                            "text": "Listen without interrupting",
                            "outcomes": {
                                "message": "You gather that The Lantern is some kind of underground support network, but they speak in vague terms. You'll need to learn more.",
                                "story_flags": ["lantern_quest_partial"]
                            }
                        },
                        {
                            "text": "Ignore it and focus on your meal",
                            "outcomes": {
                                "hunger": -5,
                                "message": "You focus on your meal instead. Chasing rumors won't fill your stomach today."
                            }
                        }
                    ],
                    "type": "quest"
                },
                "lantern_clue": {
                    "id": "lantern_clue",
                    "title": "Lantern Symbol",
                    "description": "You notice a small paper lantern symbol scratched into a street sign, alongside a series of dots that might be some kind of code. It reminds you of what you've heard about 'The Lantern'.",
                    "choices": [
                        {
                            "text": "Try to decipher the dot pattern",
                            "outcomes": {
                                "energy": -5,
                                "skills": {"awareness": 1},
                                "message": "After studying the pattern, you realize it might be indicating time intervals. The Lantern might be active at specific hours.",
                                "story_flags": ["lantern_code_found"]
                            }
                        },
                        {
                            "text": "Look for more symbols nearby",
                            "outcomes": {
                                "energy": -10,
                                "message": "You discover a sequence of symbols leading toward the east end of town. This could be a trail.",
                                "story_flags": ["lantern_trail_found"]
                            }
                        },
                        {
                            "text": "Make a charcoal rubbing of the symbol",
                            "outcomes": {
                                "inventory": {"Symbol Rubbing": 1},
                                "message": "You create a copy of the symbol. Maybe showing this to others will help you learn more.",
                                "story_flags": ["lantern_symbol_copied"]
                            },
                            "requirements": {
                                "inventory": {"Paper": 1}
                            }
                        },
                        {
                            "text": "Ask a nearby homeless person about the symbol",
                            "outcomes": {
                                "message": "They glance nervously and say, 'Follow them if you need real help. But only if you're trustworthy.' They won't say more.",
                                "story_flags": ["lantern_trail_hint"]
                            }
                        },
                        {
                            "text": "Ignore it as coincidence",
                            "outcomes": {
                                "message": "You decide it's probably just graffiti and continue on your way.",
                                "story_flags": ["lantern_opportunity_missed"]
                            }
                        }
                    ],
                    "requirements": {
                        "story_flags": ["lantern_quest_started", "lantern_quest_partial"]
                    },
                    "type": "quest"
                },
                "lantern_discovery": {
                    "id": "lantern_discovery",
                    "title": "The Lantern Found",
                    "description": "After following a series of subtle markers, you arrive at an inconspicuous building with a small lantern symbol next to the door buzzer.",
                    "choices": [
                        {
                            "text": "Ring the buzzer",
                            "outcomes": {
                                "mental": 20,
                                "message": "After a brief conversation through the intercom, you're welcomed inside. The Lantern is a community center run by formerly homeless people. They offer a safe space, resources, and genuine community.",
                                "story_flags": ["lantern_discovered"]
                            }
                        },
                        {
                            "text": "Watch the location for a while first",
                            "outcomes": {
                                "energy": -10,
                                "message": "You observe for an hour and see several people enter and leave. They appear relaxed and sometimes carry supplies. It seems safe enough to approach.",
                                "story_flags": ["lantern_observed"]
                            }
                        },
                        {
                            "text": "Leave - it seems too risky",
                            "outcomes": {
                                "mental": -10,
                                "message": "You decide it might be a trap or something illegal. Better to stick with what you know for now.",
                                "story_flags": ["lantern_avoided"]
                            }
                        }
                    ],
                    "requirements": {
                        "story_flags": ["lantern_trail_found", "lantern_trail_hint"]
                    },
                    "type": "quest"
                },
                "shelter_full": {
                    "id": "shelter_full",
                    "title": "Shelter is Full",
                    "description": "You arrive at a shelter looking for a place to sleep, but they've reached capacity for the night.",
                    "choices": [
                        {
                            "text": "Ask about alternative shelters",
                            "outcomes": {
                                "energy": -5,
                                "message": "The staff suggests another shelter across town. You'll have to hurry to make it before they fill up too."
                            }
                        },
                        {
                            "text": "Ask if you can at least stay in the lobby",
                            "outcomes": {
                                "energy": 10,
                                "mental": -5,
                                "message": "They allow you to sleep in a chair in the lobby. It's not comfortable, but it's better than outside."
                            },
                            "requirements": {
                                "reputation": {"shelters": 2}
                            }
                        },
                        {
                            "text": "Leave and find a place outside",
                            "outcomes": {
                                "health": -10,
                                "energy": -15,
                                "message": "You find a hidden spot to sleep rough. The night is cold and uncomfortable."
                            }
                        }
                    ],
                    "requirements": {
                        "time_period": ["evening", "night"]
                    },
                    "type": "shelter"
                },
                "job_opportunity": {
                    "id": "job_opportunity",
                    "title": "Day Labor Opportunity",
                    "description": "A local business owner is looking for someone to help with a small job today.",
                    "choices": [
                        {
                            "text": "Accept the work opportunity",
                            "outcomes": {
                                "money": 30,
                                "energy": -30,
                                "job_prospects": 5,
                                "message": "You spend the day working hard. The pay isn't much, but it's something, and the owner says they'll keep you in mind for future work."
                            }
                        },
                        {
                            "text": "Negotiate for better pay",
                            "outcomes": {
                                "money": 40,
                                "energy": -30,
                                "job_prospects": 3,
                                "message": "You manage to negotiate a better rate. The work is tiring but rewarding."
                            },
                            "requirements": {
                                "skills": {"social": 3}
                            }
                        },
                        {
                            "text": "Decline, you need to focus on other priorities",
                            "outcomes": {
                                "message": "You thank them but explain you have other pressing matters to attend to today."
                            }
                        }
                    ],
                    "requirements": {
                        "time_period": ["morning", "afternoon"]
                    },
                    "type": "opportunity"
                },
                "illness": {
                    "id": "illness",
                    "title": "Feeling Ill",
                    "description": "You wake up feeling feverish and weak. You might be coming down with something.",
                    "choices": [
                        {
                            "text": "Try to rest and recover",
                            "outcomes": {
                                "health": 5,
                                "energy": 5,
                                "hunger": 10,
                                "message": "You spend the day resting as much as possible. You feel slightly better by evening."
                            }
                        },
                        {
                            "text": "Seek medical attention at a clinic",
                            "outcomes": {
                                "health": 15,
                                "energy": -10,
                                "money": -5,
                                "message": "The clinic provides basic treatment and some medication. It costs a little money, but you feel much better."
                            },
                            "requirements": {
                                "player_stats": {"money": {"min": 5}}
                            }
                        },
                        {
                            "text": "Ignore it and carry on",
                            "outcomes": {
                                "health": -15,
                                "energy": -10,
                                "message": "You push through the day despite feeling terrible. By evening, your condition has worsened."
                            }
                        }
                    ],
                    "requirements": {
                        "player_stats": {"health": {"max": 60}}
                    },
                    "type": "health"
                },
                "outreach_worker": {
                    "id": "outreach_worker",
                    "title": "Outreach Worker",
                    "description": "A social worker from an outreach program approaches you and offers assistance.",
                    "choices": [
                        {
                            "text": "Accept help and discuss your situation",
                            "outcomes": {
                                "housing_prospects": 10,
                                "mental": 15,
                                "inventory": {"Resource Guide": 1},
                                "message": "You have a lengthy conversation about available resources. They give you a guide with helpful information and contacts."
                            }
                        },
                        {
                            "text": "Ask specifically about housing options",
                            "outcomes": {
                                "housing_prospects": 15,
                                "message": "They provide detailed information about housing programs and add your name to a waiting list for transitional housing."
                            }
                        },
                        {
                            "text": "Thank them but decline assistance for now",
                            "outcomes": {
                                "message": "You're not ready to engage with services yet. They leave their contact information in case you change your mind."
                            }
                        }
                    ],
                    "type": "opportunity"
                },
                "found_clothing": {
                    "id": "found_clothing",
                    "title": "Donation Bin",
                    "description": "You notice a clothing donation bin. It might have something useful inside.",
                    "choices": [
                        {
                            "text": "Check if there are accessible donations",
                            "outcomes": {
                                "inventory": {"Warm Clothes": 1},
                                "hygiene": 10,
                                "message": "You find some clean, warm clothes that fit you. Changing into them makes you feel much better."
                            }
                        },
                        {
                            "text": "Try to reach inside the bin for more items",
                            "outcomes": {
                                "inventory": {"Warm Clothes": 1, "Blanket": 1},
                                "hygiene": 10,
                                "message": "You manage to retrieve both clothes and a blanket. These will be very useful."
                            },
                            "requirements": {
                                "skills": {"resourcefulness": 2}
                            }
                        },
                        {
                            "text": "Leave it alone, it's not right to take from donations",
                            "outcomes": {
                                "mental": 5,
                                "message": "You decide not to take anything, maintaining your principles despite your needs."
                            }
                        }
                    ],
                    "type": "resource"
                },
                "found_money": {
                    "id": "found_money",
                    "title": "Found Money",
                    "description": "While walking down the street, you spot some money on the ground.",
                    "choices": [
                        {
                            "text": "Take it, you need it more than whoever lost it",
                            "outcomes": {
                                "money": 10,
                                "message": "You pocket $10. It could make a real difference for your immediate needs."
                            }
                        },
                        {
                            "text": "Look around to see if someone dropped it recently",
                            "outcomes": {
                                "mental": 10,
                                "money": 5,
                                "message": "You look around but don't see an obvious owner. A passerby notices your honesty and gives you $5 as a reward."
                            }
                        },
                        {
                            "text": "Leave it, it belongs to someone else",
                            "outcomes": {
                                "mental": 15,
                                "message": "Despite your own needs, you choose not to take what isn't yours. Your integrity remains intact."
                            }
                        }
                    ],
                    "type": "opportunity"
                },
                "encampment_warning": {
                    "id": "encampment_warning",
                    "title": "Encampment Notice",
                    "description": "You notice city workers posting notices around a small homeless encampment. The papers state that the area will be cleared in 48 hours.",
                    "choices": [
                        {
                            "text": "Warn the residents about the notice",
                            "outcomes": {
                                "energy": -5,
                                "mental": 10,
                                "reputation": {"community": 15},
                                "message": "You alert everyone in the camp. They're grateful for the warning, and someone offers to share their food with you.",
                                "story_flags": ["encampment_warning_given"]
                            }
                        },
                        {
                            "text": "Observe from a distance",
                            "outcomes": {
                                "mental": -5,
                                "message": "You watch as some residents notice the papers and begin to panic. Their stress affects you as you contemplate where they'll all go.",
                                "story_flags": ["encampment_observed"]
                            }
                        },
                        {
                            "text": "Talk to the city workers",
                            "outcomes": {
                                "mental": -10,
                                "message": "The workers explain they're 'just doing their job' and suggest residents go to shelters. They seem uncomfortable with your questions.",
                                "story_flags": ["questioned_authorities"]
                            }
                        }
                    ],
                    "type": "quest"
                },
                "id_quest_social_worker": {
                    "id": "id_quest_social_worker",
                    "title": "ID Replacement Assistance",
                    "description": "At a drop-in center, you meet a social worker who specializes in helping people replace lost identification.",
                    "choices": [
                        {
                            "text": "Explain your situation and ask for help",
                            "outcomes": {
                                "mental": 15,
                                "message": "The social worker is very understanding. They explain the process and offer to help you navigate the system. They'll need to meet with you again next week to continue the process.",
                                "story_flags": ["id_quest_progress"]
                            }
                        },
                        {
                            "text": "Ask what documents you'll need",
                            "outcomes": {
                                "mental": 5,
                                "message": "They provide a list of documents and letters you'll need to gather. It seems overwhelming, but at least you know what to work toward now.",
                                "story_flags": ["id_quest_requirements"]
                            }
                        },
                        {
                            "text": "Decline help, it seems too complicated",
                            "outcomes": {
                                "mental": -10,
                                "message": "You decide the process sounds too difficult and time-consuming. You'll have to find another way.",
                                "story_flags": ["id_quest_delayed"]
                            }
                        }
                    ],
                    "requirements": {
                        "story_flags": ["id_quest_started"]
                    },
                    "type": "quest"
                },
                "id_quest_completion": {
                    "id": "id_quest_completion",
                    "title": "ID Replacement Day",
                    "description": "After weeks of paperwork, appointments, and waiting, today is finally the day you can pick up your new government ID. The office is busy, and you notice someone who seems to be in a similar situation being turned away.",
                    "choices": [
                        {
                            "text": "Share your experience and help them",
                            "outcomes": {
                                "energy": -15,
                                "mental": 20,
                                "money": -15,
                                "reputation": {"community": 15},
                                "inventory": {"Government ID": 1},
                                "message": "You take time to explain the process and share your documentation tips. They're grateful, and a staff member notices your kindness.",
                                "story_flags": ["id_quest_completed", "helped_another_homeless"]
                            }
                        },
                        {
                            "text": "Focus on your own application",
                            "outcomes": {
                                "energy": -10,
                                "mental": 15,
                                "money": -15,
                                "inventory": {"Government ID": 1},
                                "message": "You successfully get your ID. The process was challenging enough without complications.",
                                "story_flags": ["id_quest_completed"]
                            }
                        },
                        {
                            "text": "Offer to share your social worker's contact",
                            "outcomes": {
                                "energy": -5,
                                "mental": 25,
                                "money": -15,
                                "inventory": {"Government ID": 1},
                                "reputation": {"services": 10},
                                "message": "You get your ID and help another person start their journey. The social worker appreciates your referral.",
                                "story_flags": ["id_quest_completed", "social_worker_network"]
                            },
                            "requirements": {
                                "story_flags": ["social_worker_bond"]
                            }
                        }
                    ],
                    "choices": [
                        {
                            "text": "Go to the government office",
                            "outcomes": {
                               "energy": -10,
                                "mental": 25,
                                "money": -15,
                                "housing_prospects": 25,
                                "job_prospects": 25,
                                "inventory": {"Government ID": 1},
                                "message": "After hours of waiting, you finally receive your new ID. The small card represents a huge step forward in reclaiming your life and accessing services.",
                                "story_flags": ["id_quest_completed"]
                            }
                        },
                        {
                            "text": "Double-check that you have all required documents",
                            "outcomes": {
                                "energy": -5,
                                "message": "You carefully review everything and realize you're missing one signature. You get it quickly from a nearby shelter staff member, potentially saving yourself from being turned away.",
                                "story_flags": ["id_quest_prepared"]
                            }
                        },
                        {
                            "text": "Ask the social worker to accompany you",
                            "outcomes": {
                                "mental": 15,
                                "money": -10,
                                "housing_prospects": 25,
                                "job_prospects": 25,
                                "inventory": {"Government ID": 1},
                                "message": "The social worker helps navigate the bureaucracy and advocates for you when there's an issue with your application. You leave with your new ID and feel supported.",
                                "story_flags": ["id_quest_completed", "social_worker_bond"]
                            }
                        }
                    ],
                    "requirements": {
                        "story_flags": ["id_quest_progress", "id_quest_requirements"]
                    },
                    "type": "quest"
                },
                "encampment_crackdown": {
                    "id": "encampment_crackdown",
                    "title": "Encampment Clearing",
                    "description": "You arrive to find police and city workers dismantling the encampment. People are gathering their belongings as tents are being removed.",
                    "choices": [
                        {
                            "text": "Help others gather their belongings",
                            "outcomes": {
                                "energy": -20,
                                "mental": 10,
                                "reputation": {"community": 20},
                                "message": "You help several people save their important possessions before their shelters are dismantled. They're deeply grateful, and one elderly man gives you a warm jacket as thanks.",
                                "inventory": {"Winter Jacket": 1},
                                "story_flags": ["helped_during_crackdown"]
                            }
                        },
                        {
                            "text": "Document the clearing with notes",
                            "outcomes": {
                                "mental": -10,
                                "skills": {"awareness": 2},
                                "message": "You observe and take mental notes of how the clearing is conducted. The knowledge might be useful in the future, but witnessing the distress is emotionally draining.",
                                "story_flags": ["documented_crackdown"]
                            }
                        },
                        {
                            "text": "Leave quickly to avoid trouble",
                            "outcomes": {
                                "energy": -10,
                                "mental": -15,
                                "message": "You leave the area to avoid any confrontation with authorities. The guilt of not helping weighs on you.",
                                "story_flags": ["avoided_crackdown"]
                            }
                        }
                    ],
                    "requirements": {
                        "story_flags": ["encampment_warning_given", "encampment_observed", "questioned_authorities"]
                    },
                    "type": "quest"
                },
                "shelter_bully": {
                    "id": "shelter_bully",
                    "title": "Shelter Conflict",
                    "description": "At the shelter, another resident is being aggressive and trying to intimidate others.",
                    "choices": [
                        {
                            "text": "Stand up to them",
                            "outcomes": {
                                "reputation": {"shelters": 2},
                                "mental": -5,
                                "message": "You confront them and they eventually back down. Others appreciate your intervention but it was stressful."
                            }
                        },
                        {
                            "text": "Alert shelter staff",
                            "outcomes": {
                                "reputation": {"shelters": 1},
                                "message": "Staff intervene and defuse the situation. They thank you for bringing it to their attention."
                            }
                        },
                        {
                            "text": "Keep to yourself and avoid conflict",
                            "outcomes": {
                                "energy": -5,
                                "message": "You stay out of it, but have to remain vigilant which is tiring. The situation eventually calms down."
                            }
                        }
                    ],
                    "type": "shelter"
                },
                "helpful_information": {
                    "id": "helpful_information",
                    "title": "Local Knowledge",
                    "description": "You meet someone who's been homeless in Ottawa for years and knows all the best spots and resources.",
                    "choices": [
                        {
                            "text": "Ask about food resources",
                            "outcomes": {
                                "skills": {"foraging": 1},
                                "message": "They share detailed information about which places offer free meals on which days, and which dumpsters are safe to check."
                            }
                        },
                        {
                            "text": "Ask about safe places to sleep",
                            "outcomes": {
                                "skills": {"navigation": 1},
                                "message": "They point out several hidden spots where police rarely check and you'll be safe from the elements."
                            }
                        },
                        {
                            "text": "Ask about services and programs",
                            "outcomes": {
                                "housing_prospects": 5,
                                "message": "They tell you about several programs you weren't aware of that might help you get back on your feet."
                            }
                        }
                    ],
                    "type": "opportunity"
                },
                "volunteer_opportunity": {
                    "id": "volunteer_opportunity",
                    "title": "Volunteer Opportunity",
                    "description": "A community center is looking for volunteers to help with an event. Volunteers will receive a meal and small stipend.",
                    "choices": [
                        {
                            "text": "Volunteer for the full day",
                            "outcomes": {
                                "hunger": -40,
                                "money": 15,
                                "energy": -25,
                                "job_prospects": 10,
                                "mental": 10,
                                "message": "You spend the day helping out. The work is tiring but rewarding, and you make some good connections."
                            }
                        },
                        {
                            "text": "Volunteer for a few hours",
                            "outcomes": {
                                "hunger": -30,
                                "money": 5,
                                "energy": -10,
                                "job_prospects": 5,
                                "mental": 5,
                                "message": "You help for part of the day. It's a positive experience and you get a good meal."
                            }
                        },
                        {
                            "text": "Decline and focus on other priorities",
                            "outcomes": {
                                "message": "You decide your time and energy is better spent elsewhere today."
                            }
                        }
                    ],
                    "requirements": {
                        "time_period": ["morning", "afternoon"]
                    },
                    "type": "opportunity"
                }
            }

            # Try to load events from JSON file
            file_path = os.path.join("data", "events.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    event_data = json.load(f)
            else:
                # Use default events if file doesn't exist
                event_data = default_events

                # Ensure data directory exists
                os.makedirs("data", exist_ok=True)

                # Write default events to JSON file
                with open(file_path, 'w') as f:
                    json.dump(default_events, f, indent=4)

            # Create Event objects
            for event_id, data in event_data.items():
                try:
                    # Check if there's a duplicate choices field
                    if not isinstance(data["choices"], list):
                        print(f"Warning: Event {event_id} has invalid choices format. Attempting to fix.")
                        data["choices"] = data["choices"][0] if isinstance(data["choices"], list) else []
                    
                    event = Event(
                        event_id=data["id"],
                        title=data["title"],
                        description=data["description"],
                        choices=data["choices"],
                        requirements=data.get("requirements", {}),
                        type=data.get("type", "general"),
                        chain_events=data.get("chain_events", {})
                    )
                    self.events[event_id] = event
                except Exception as e:
                    print(f"Error creating event {event_id}: {e}")
                    # Log more details for debugging
                    print(f"Event data: {data}")
                    # Continue loading other events even if one fails
                    continue

        except Exception as e:
            print(f"Error loading events: {e}")
            # Create minimal set of events if loading fails
            food_event = Event(
                event_id="food_search",
                title="Found Food",
                description="You find some discarded food that looks edible.",
                choices=[
                    {
                        "text": "Eat the food",
                        "outcomes": {
                            "hunger": -20,
                            "message": "The food satisfies your hunger."
                        }
                    },
                    {
                        "text": "Leave it",
                        "outcomes": {
                            "message": "You decide not to risk it."
                        }
                    }
                ]
            )

            encounter_event = Event(
                event_id="encounter",
                title="Stranger",
                description="A stranger approaches you.",
                choices=[
                    {
                        "text": "Talk to them",
                        "outcomes": {
                            "mental": 5,
                            "message": "The conversation lifts your spirits."
                        }
                    },
                    {
                        "text": "Avoid them",
                        "outcomes": {
                            "message": "You keep to yourself."
                        }
                    }
                ]
            )

            self.events = {
                "food_search": food_event,
                "encounter": encounter_event
            }

    def get_random_event(self, location, time_system):
        """Get a random event appropriate for the current situation and weather."""
        # Initialize event pool with weights
        event_pool = []
        
        # Location type affects event selection
        location_type = getattr(location, 'type', 'general')
        danger_level = location.danger_level
        
        # Check for weather-specific events first
        if time_system.is_harsh_weather():
            # Higher chance of weather-related events in harsh conditions
            weather_events = [
                (event, 2.0)  # Double weight for weather events
                for event in self.events.values()
                if event.type == "weather" 
                and event.meets_requirements(self.player, time_system, location)
            ]
            event_pool.extend(weather_events)
            
        # Add location-specific events with appropriate weights
        for event in self.events.values():
            if not event.meets_requirements(self.player, time_system, location):
                continue
                
            weight = 1.0  # Base weight
            
            # Adjust weight based on location danger level
            if event.type == "danger" and danger_level >= 7:
                weight *= 1.5
            elif event.type == "opportunity" and danger_level <= 3:
                weight *= 1.3
                
            # Adjust for location type
            if hasattr(event, 'location_types') and location_type in event.location_types:
                weight *= 1.4
                
            # Avoid recently seen events
            if event.event_id in self.event_history[-5:]:
                weight *= 0.3
                
            event_pool.append((event, weight))
            
        # If no valid events, create a generic one
        if not event_pool:
            return self._create_generic_event(location)
            
        # Select event using weighted random choice
        total_weight = sum(weight for _, weight in event_pool)
        random_val = random.uniform(0, total_weight)
        current_weight = 0
        
        for event, weight in event_pool:
            current_weight += weight
            if current_weight >= random_val:
                self.event_history.append(event.event_id)
                return event
                
        # Fallback to first event if something goes wrong
        selected_event = event_pool[0][0]
        self.event_history.append(selected_event.event_id)
        return selected_event
        # Check location-specific quest areas
        available_areas = location.get_quest_areas(time_system.get_period())
        for area_name, area_data in available_areas.items():
            if "quest_events" in area_data:
                for quest_event in area_data["quest_events"]:
                    if quest_event not in location.completed_quests:
                        return self.events.get(quest_event)

        # Check NPC-related events
        active_hotspots = location.get_npc_hotspots(time_system.get_period())
        for spot_name, spot_data in active_hotspots.items():
            if "npc_events" in spot_data:
                for npc_event in spot_data["npc_events"]:
                    if npc_event not in location.active_events:
                        return self.events.get(npc_event)
        # Check for active quest events first with enhanced context
        if self.player.active_quests:
            for quest in self.player.active_quests:
                # Check for time-sensitive quest events
                if quest.meets_requirements(self.player, self.time_system, location):
                    # Get related random events that could enhance the quest
                    related_events = [event for event in self.events.values() 
                                    if event.event_id in quest.impacted_events]

                    # 30% chance to trigger related event instead of quest event
                    if related_events and random.random() < 0.3:
                        return random.choice(related_events)

                    return quest.get_next_event(self.player)

        # Check for newly unlocked events from quest progress
        unlocked_events = []
        for quest in self.player.completed_quests:
            unlocked_events.extend([event for event in self.events.values() 
                                  if event.event_id in quest.unlocked_events and
                                  event.meets_requirements(self.player, self.time_system, location)])

        if unlocked_events and random.random() < 0.4:  # 40% chance to trigger unlocked event
            return random.choice(unlocked_events)

        # Check for new quest opportunities
        if random.random() < 0.2:  # 20% chance for quest events
            available_quests = [event for event in self.events.values() 
                              if event.type == "quest" 
                              and event.meets_requirements(self.player, self.time_system, location)
                              and event.event_id not in self.player.completed_quests]
            if available_quests:
                return random.choice(available_quests)

        # Calculate difficulty modifier based on player progress
        difficulty = min(2.0, max(1.0, (
            self.player.days_survived * 0.1 +  # Increases with days survived
            self.player.housing_prospects * 0.005 +  # Increases with progress
            self.player.street_cred * 0.01  # Increases with street reputation
        )))

        # Apply seasonal effects
        if self.time_system.is_harsh_weather():
            difficulty *= 1.3  # 30% harder in harsh weather

        # Filter and adjust events
        valid_events = []
        for event in self.events.values():
            if event.meets_requirements(self.player, self.time_system, location):
                # Prioritize events that haven't happened recently
                if event.event_id not in self.event_history[-5:]:
                    # Scale event outcomes based on difficulty
                    scaled_event = self._scale_event(event, difficulty)
                    valid_events.append(scaled_event)

        # If no valid events, return a generic one
        if not valid_events:
            return self._create_generic_event(location)

        # Select random event from valid ones
        selected_event = random.choice(valid_events)
        self.event_history.append(selected_event.event_id)

        return selected_event

    def get_travel_event(self):
        """Get a random event that occurs during travel.

        Returns:
            Event: Travel event
        """
        # Filter events appropriate for travel
        travel_events = [event for event in self.events.values() 
                        if event.type in ["encounter", "opportunity", "danger"]
                        and event.meets_requirements(self.player, self.time_system, None)]

        if not travel_events:
            # Create a generic travel event if none exist
            return Event(
                event_id="generic_travel",
                title="On the Move",
                description="As you make your way to your destination, you observe the city around you.",
                choices=[
                    {
                        "text": "Keep an eye out for resources",
                        "outcomes": {
                            "skills": {"navigation": 1},
                            "message": "You notice a few potentially useful locations for future reference."
                        }
                    },
                    {
                        "text": "Stay focused on your destination",
                        "outcomes": {
                            "energy": 5,
                            "message": "You maintain a steady pace, saving energy by taking the most direct route."
                        }
                    }
                ]
            )

        # Select random travel event
        return random.choice(travel_events)

    def get_shelter_event(self, quality):
        """Get a random event that occurs at a shelter.

        Args:
            quality (str): Quality of the shelter ('high', 'medium', 'low')

        Returns:
            Event: Shelter event
        """
        # Filter events appropriate for shelters
        shelter_events = [event for event in self.events.values() 
                         if event.type in ["shelter", "encounter", "opportunity"]
                         and event.meets_requirements(self.player, self.time_system, None)]

        if not shelter_events:
            # Create quality-appropriate shelter event
            if quality == "high":
                return Event(
                    event_id="good_shelter_night",
                    title="Peaceful Night",
                    description="The shelter is clean and well-managed. You have a relatively comfortable night.",
                    choices=[
                        {
                            "text": "Get a full night's rest",
                            "outcomes": {
                                "energy": 15,
                                "mental": 10,
                                "message": "You sleep well and wake up feeling refreshed."
                            }
                        },
                        {
                            "text": "Chat with other residents",
                            "outcomes": {
                                "energy": 10,
                                "mental": 15,
                                "skills": {"social": 1},
                                "message": "You make some connections and share useful information."
                            }
                        }
                    ]
                )
            elif quality == "medium":
                return Event(
                    event_id="decent_shelter_night",
                    title="Basic Shelter",
                    description="The shelter is basic but meets your needs for the night.",
                    choices=[
                        {
                            "text": "Get some sleep",
                            "outcomes": {
                                "energy": 10,
                                "mental": 5,
                                "message": "You sleep adequately, though it's not the most comfortable setting."
                            }
                        },
                        {
                            "text": "Keep to yourself",
                            "outcomes": {
                                "energy": 8,
                                "message": "You find a quiet corner and get some rest, avoiding interaction."
                            }
                        }
                    ]
                )
            else:  # low quality
                return Event(
                    event_id="poor_shelter_night",
                    title="Rough Night",
                    description="The make-shift shelter barely protects you from the elements.",
                    choices=[
                        {
                            "text": "Try to get what rest you can",
                            "outcomes": {
                                "energy": 5,
                                "health": -5,
                                "message": "You sleep fitfully, constantly uncomfortable and alert for danger."
                            }
                        },
                        {
                            "text": "Stay vigilant",
                            "outcomes": {
                                "energy": -5,
                                "mental": -5,
                                "message": "You spend most of the night on guard, getting little actual rest."
                            }
                        }
                    ]
                )

        # Select random shelter event
        return random.choice(shelter_events)

    def get_danger_event(self):
        """Get a random dangerous event.

        Returns:
            Event: Danger event
        """
        # Filter events that are dangerous
        danger_events = [event for event in self.events.values() 
                        if event.type == "danger"
                        and event.meets_requirements(self.player, self.time_system, None)]

        if not danger_events:
            # Create a generic danger event
            return Event(
                event_id="generic_danger",
                title="Threatening Situation",
                description="You find yourself in a potentially dangerous situation.",
                choices=[
                    {
                        "text": "Try to leave quietly",
                        "outcomes": {
                            "energy": -10,
                            "message": "You carefully extract yourself from the situation without incident."
                        }
                    },
                    {
                        "text": "Stand your ground",
                        "outcomes": {
                            "health": -10,
                            "mental": -5,
                            "message": "The situation escalates and you sustain some injuries before getting away."
                        }
                    },
                    {
                        "text": "Call for help",
                        "outcomes": {
                            "mental": -10,
                            "message": "You shout for help, attracting attention. The danger passes but leaves you shaken."
                        }
                    }
                ]
            )

        # Select random danger event
        return random.choice(danger_events)

    def get_waiting_event(self):
        """Get a random event that occurs while waiting/passing time.

        Returns:
            Event: Waiting event
        """
        # Filter events appropriate for waiting
        waiting_events = [event for event in self.events.values() 
                         if event.type in ["encounter", "opportunity", "general"]
                         and event.meets_requirements(self.player, self.time_system, None)]

        if not waiting_events:
            # Create a generic waiting event
            return Event(
                event_id="generic_waiting",
                title="Passing Time",
                description="As you wait, you observe the world around you.",
                choices=[
                    {
                        "text": "People watch",
                        "outcomes": {
                            "mental": 5,
                            "message": "You find some small entertainment in watching the city's residents go about their day."
                        }
                    },
                    {
                        "text": "Reflect on your situation",
                        "outcomes": {
                            "mental": -5,
                            "skills": {"resourcefulness": 1},
                            "message": "You spend time thinking about how to improve your circumstances. It's somewhat depressing but useful."
                        }
                    },
                    {
                        "text": "Rest your eyes",
                        "outcomes": {
                            "energy": 5,
                            "message": "You get a small amount of rest while waiting."
                        }
                    }
                ]
            )

        # Select random waiting event
        return random.choice(waiting_events)
        
    def get_job_event(self, job_type):
        """Get a random event that occurs during work.
        
        Args:
            job_type (str): The type of job ('labor', 'skilled_labor', etc.)
            
        Returns:
            Event: Job-related event
        """
        # Filter for job events matching the job type
        job_events = [event for event in self.events.values() 
                     if event.type in ["opportunity", "general"]
                     and "job_context" in event.requirements
                     and event.requirements["job_context"] == job_type
                     and event.meets_requirements(self.player, self.time_system, None)]
        
        if not job_events:
            # Create a generic job event if no specific ones exist
            title = f"{job_type.replace('_', ' ').title()} Work"
            description = f"You spend several hours doing {job_type.replace('_', ' ')} work."
            
            choices = [
                {
                    "text": "Work diligently",
                    "outcomes": {
                        "mental": 5,
                        "job_prospects": 2,
                        "message": "You put in your best effort and it's noticed by your supervisor."
                    }
                },
                {
                    "text": "Take it easy",
                    "outcomes": {
                        "energy": 5,
                        "message": "You pace yourself, conserving energy but completing less work."
                    }
                }
            ]
            
            return Event(
                event_id=f"generic_{job_type}_job",
                title=title,
                description=description,
                choices=choices,
                type="opportunity"
            )
            
        return random.choice(job_events)

    def process_event(self, event, location):
        """Process the event and handle player choice.

        Args:
            event (Event): The event to process
            location (Location): Current location
        """
        import logging
        from game.ui import UI
        ui = UI()
        
        # Check if event is valid
        if not event:
            logging.error("Tried to process an invalid event")
            ui.display_error("Error: Tried to process an invalid event")
            ui.display_text("You continue on your way...")
            return
            
        # Validate event has required attributes
        if not hasattr(event, 'title') or not hasattr(event, 'description') or not hasattr(event, 'choices'):
            logging.error(f"Event is missing required attributes: {str(event)}")
            ui.display_error("Error: Event is malformed")
            ui.display_text("You encounter something unusual but press on...")
            return

        # Display event
        try:
            ui.display_title(event.title)
            ui.display_text(event.description)
            ui.display_divider()
        except Exception as e:
            logging.error(f"Error displaying event: {str(e)}")
            ui.display_error(f"Error displaying event: {str(e)}")
            ui.display_text("Something strange happens, but you continue on...")
            return
            
        # Validate choices
        if not event.choices or not isinstance(event.choices, list):
            logging.error(f"Event has invalid choices format: {str(event.choices)}")
            ui.display_error("This situation offers no clear options.")
            ui.display_text("You decide to move on...")
            return

        # Display choices
        ui.display_title("Options")
        for i, choice in enumerate(event.choices, 1):
            meets_reqs = True
            try:
                # Check if choice has requirements
                if "requirements" in choice and isinstance(choice["requirements"], dict):
                    reqs = choice["requirements"]

                    # Check inventory requirements
                    if "inventory" in reqs:
                        for item, quantity in reqs["inventory"].items():
                            if not self.player.has_item(item, quantity):
                                meets_reqs = False

                    # Check skill requirements
                    if "skills" in reqs:
                        for skill, level in reqs["skills"].items():
                            if self.player.skills.get(skill, 0) < level:
                                meets_reqs = False

                    # Check reputation requirements
                    if "reputation" in reqs:
                        for group, level in reqs["reputation"].items():
                            if self.player.reputation.get(group, 0) < level:
                                meets_reqs = False

                    # Check stat requirements
                    if "player_stats" in reqs:
                        for stat, values in reqs["player_stats"].items():
                            if "min" in values and getattr(self.player, stat, 0) < values["min"]:
                                meets_reqs = False
                            if "max" in values and getattr(self.player, stat, 100) > values["max"]:
                                meets_reqs = False

                # Display choice (with indicator if requirements aren't met)
                if meets_reqs:
                    ui.display_text(f"{i}. {choice['text']}")
                else:
                    ui.display_text(f"{i}. {choice['text']} (requirements not met)", color="red")
                    
            except Exception as e:
                logging.error(f"Error processing choice: {str(e)}")
                # Fallback: display the choice without requirement checking
                ui.display_text(f"{i}. {choice.get('text', 'Unknown option')}")

        # Get player choice
        from game.utils import safe_input
        while True:
            try:
                choice_input = safe_input("\nWhat do you do? ")
                if not choice_input:  # Handle empty input gracefully
                    ui.display_error("Please make a choice.")
                    continue
                    
                choice_num = int(choice_input)
                if 1 <= choice_num <= len(event.choices):
                    choice = event.choices[choice_num - 1]

                    # Check requirements again
                    meets_reqs = True
                    if "requirements" in choice:
                        reqs = choice["requirements"]

                        # Check inventory requirements
                        if "inventory" in reqs:
                            for item, quantity in reqs["inventory"].items():
                                if not self.player.has_item(item, quantity):
                                    meets_reqs = False

                        # Check skill requirements
                        if "skills" in reqs:
                            for skill, level in reqs["skills"].items():
                                if self.player.skills.get(skill, 0) < level:
                                    meets_reqs = False

                        # Check reputation requirements
                        if "reputation" in reqs:
                            for group, level in reqs["reputation"].items():
                                if self.player.reputation.get(group, 0) < level:
                                    meets_reqs = False

                        # Check stat requirements
                        if "player_stats" in reqs:
                            for stat, values in reqs["player_stats"].items():
                                if "min" in values and getattr(self.player, stat, 0) < values["min"]:
                                    meets_reqs = False
                                if "max" in values and getattr(self.player, stat, 100) > values["max"]:
                                    meets_reqs = False

                    if meets_reqs:
                        break
                    else:
                        ui.display_error("You don't meet the requirements for this choice.")
                else:
                    ui.display_error("Please enter a valid choice number.")
            except ValueError:
                ui.display_error("Please enter a number.")

        # Process outcomes
        ui.display_divider()
        
        try:
            # Enhanced outcome validation
            if not isinstance(choice, dict):
                logging.error(f"Invalid choice type: {type(choice)}")
                ui.display_error("Error processing your choice.")
                return
                
            # Validate choice structure
            required_fields = {'text', 'outcomes'}
            if not all(field in choice for field in required_fields):
                logging.error(f"Choice missing required fields: {required_fields - set(choice.keys())}")
                ui.display_error("Error: Invalid choice structure")
                return
                
            # Validate outcomes structure and values
            outcomes = choice["outcomes"]
            if not isinstance(outcomes, dict):
                logging.error(f"Invalid outcomes type: {type(outcomes)}")
                ui.display_error("Error: Invalid outcomes format")
                return
                
            # Validate specific outcome types
            for key, value in outcomes.items():
                if key in ['health', 'energy', 'mental', 'satiety', 'hygiene']:
                    if not isinstance(value, (int, float)):
                        logging.error(f"Invalid {key} value type: {type(value)}")
                        outcomes[key] = 0  # Set safe default
                elif key == 'money':
                    if not isinstance(value, (int, float)):
                        logging.error(f"Invalid money value type: {type(value)}")
                        outcomes[key] = 0.0  # Set safe default
                elif key == 'inventory' and not isinstance(value, dict):
                    logging.error(f"Invalid inventory format: {type(value)}")
                    outcomes[key] = {}  # Set safe default
                
            if "outcomes" not in choice:
                logging.error(f"Choice has no outcomes: {choice}")
                ui.display_text("You made your choice, but nothing significant happens.")
                return
                
            outcomes = choice["outcomes"]
            
            if not isinstance(outcomes, dict):
                logging.error(f"Invalid outcomes type: {type(outcomes)}")
                ui.display_text("Your choice leads to an unexpected situation.")
                return
            
            # Display outcome message
            if "message" in outcomes:
                ui.display_text(outcomes["message"])
            else:
                # Default message if none is provided
                ui.display_text("You made your choice.")
        except Exception as e:
            logging.error(f"Error processing outcomes: {str(e)}")
            ui.display_error("Something unexpected happened.")
            return

        # Apply stat changes - with error handling for each stat
        try:
            if "health" in outcomes:
                if not isinstance(outcomes["health"], (int, float)):
                    logging.warning(f"Invalid health value: {outcomes['health']}")
                else:
                    health_change = int(outcomes["health"])  # Convert to int to be safe
                    self.player.health += health_change
                    if health_change > 0:
                        ui.display_success(f"Health +{health_change}")
                    elif health_change < 0:
                        ui.display_warning(f"Health {health_change}")
        except Exception as e:
            logging.error(f"Error processing health outcomes: {str(e)}")

        # Handle both hunger (legacy) and satiety in outcomes
        try:
            if "hunger" in outcomes:
                if not isinstance(outcomes["hunger"], (int, float)):
                    logging.warning(f"Invalid hunger value: {outcomes['hunger']}")
                else:
                    # Convert hunger to satiety (negative hunger means more satiety)
                    hunger_change = int(outcomes["hunger"])  # Convert to int to be safe
                    self.player.satiety -= hunger_change
                    if hunger_change < 0:
                        ui.display_success(f"Satiety increased by {abs(hunger_change)}")
                    elif hunger_change > 0:
                        ui.display_warning(f"Satiety decreased by {hunger_change}")
        except Exception as e:
            logging.error(f"Error processing hunger outcomes: {str(e)}")
        
        try:
            if "satiety" in outcomes:
                if not isinstance(outcomes["satiety"], (int, float)):
                    logging.warning(f"Invalid satiety value: {outcomes['satiety']}")
                else:
                    # Direct satiety handling
                    satiety_change = int(outcomes["satiety"])  # Convert to int to be safe
                    self.player.satiety += satiety_change
                    if satiety_change > 0:
                        ui.display_success(f"Satiety +{satiety_change}")
                    elif satiety_change < 0:
                        ui.display_warning(f"Satiety {satiety_change}")
        except Exception as e:
            logging.error(f"Error processing satiety outcomes: {str(e)}")

        try:
            if "energy" in outcomes:
                if not isinstance(outcomes["energy"], (int, float)):
                    logging.warning(f"Invalid energy value: {outcomes['energy']}")
                else:
                    energy_change = int(outcomes["energy"])  # Convert to int to be safe
                    self.player.energy += energy_change
                    if energy_change > 0:
                        ui.display_success(f"Energy +{energy_change}")
                    elif energy_change < 0:
                        ui.display_warning(f"Energy {energy_change}")
        except Exception as e:
            logging.error(f"Error processing energy outcomes: {str(e)}")

        try:
            if "mental" in outcomes:
                if not isinstance(outcomes["mental"], (int, float)):
                    logging.warning(f"Invalid mental value: {outcomes['mental']}")
                else:
                    mental_change = int(outcomes["mental"])  # Convert to int to be safe
                    self.player.mental += mental_change
                    if mental_change > 0:
                        ui.display_success(f"Mental well-being +{mental_change}")
                    elif mental_change < 0:
                        ui.display_warning(f"Mental well-being {mental_change}")
        except Exception as e:
            logging.error(f"Error processing mental outcomes: {str(e)}")

        try:
            if "hygiene" in outcomes:
                if not isinstance(outcomes["hygiene"], (int, float)):
                    logging.warning(f"Invalid hygiene value: {outcomes['hygiene']}")
                else:
                    hygiene_change = int(outcomes["hygiene"])  # Convert to int to be safe
                    self.player.hygiene += hygiene_change
                    if hygiene_change > 0:
                        ui.display_success(f"Hygiene +{hygiene_change}")
                    elif hygiene_change < 0:
                        ui.display_warning(f"Hygiene {hygiene_change}")
        except Exception as e:
            logging.error(f"Error processing hygiene outcomes: {str(e)}")

        # Apply inventory changes with error handling
        try:
            if "inventory" in outcomes:
                if not isinstance(outcomes["inventory"], dict):
                    logging.warning(f"Invalid inventory format: {outcomes['inventory']}")
                else:
                    for item, quantity in outcomes["inventory"].items():
                        try:
                            if not isinstance(quantity, (int, float)) or quantity <= 0:
                                logging.warning(f"Invalid quantity for {item}: {quantity}")
                                continue
                                
                            self.player.add_item(item, int(quantity))
                            ui.display_text(f"Gained {quantity} {item}")
                        except Exception as e:
                            logging.error(f"Error adding item {item}: {str(e)}")
        except Exception as e:
            logging.error(f"Error processing inventory outcomes: {str(e)}")

        # Apply money changes with error handling
        try:
            if "money" in outcomes:
                if not isinstance(outcomes["money"], (int, float)):
                    logging.warning(f"Invalid money value: {outcomes['money']}")
                else:
                    money_change = float(outcomes["money"])  # Convert to float for money
                    
                    if money_change > 0:
                        self.player.add_money(money_change)
                        ui.display_success(f"Money +${money_change:.2f}")
                    elif money_change < 0:
                        # Make sure money is actually deducted by using spend_money
                        amount_to_spend = abs(money_change)
                        if self.player.spend_money(amount_to_spend):
                            ui.display_warning(f"Money -${amount_to_spend:.2f}")
                        else:
                            # Handle case where player doesn't have enough money
                            actual_spent = min(amount_to_spend, self.player.money)
                            if actual_spent > 0:
                                self.player.money = max(0, self.player.money - actual_spent)
                                ui.display_warning(f"Money -${actual_spent:.2f}")
                            ui.display_warning("You couldn't afford the full amount.")
        except Exception as e:
            logging.error(f"Error processing money outcomes: {str(e)}")

        # Apply skill changes with error handling
        try:
            if "skills" in outcomes:
                if not isinstance(outcomes["skills"], dict):
                    logging.warning(f"Invalid skills format: {outcomes['skills']}")
                else:
                    for skill, amount in outcomes["skills"].items():
                        try:
                            if not isinstance(amount, (int, float)) or amount <= 0:
                                logging.warning(f"Invalid skill amount for {skill}: {amount}")
                                continue
                                
                            self.player.increase_skill(skill, int(amount))
                            ui.display_success(f"{skill.title()} skill increased by {amount}")
                        except Exception as e:
                            logging.error(f"Error increasing skill {skill}: {str(e)}")
        except Exception as e:
            logging.error(f"Error processing skills outcomes: {str(e)}")

        # Apply reputation changes with error handling
        try:
            if "reputation" in outcomes:
                if not isinstance(outcomes["reputation"], dict):
                    logging.warning(f"Invalid reputation format: {outcomes['reputation']}")
                else:
                    for group, amount in outcomes["reputation"].items():
                        try:
                            if not isinstance(amount, (int, float)):
                                logging.warning(f"Invalid reputation amount for {group}: {amount}")
                                continue
                                
                            self.player.improve_reputation(group, float(amount))
                            ui.display_success(f"Reputation with {group} increased by {amount}")
                        except Exception as e:
                            logging.error(f"Error improving reputation with {group}: {str(e)}")
        except Exception as e:
            logging.error(f"Error processing reputation outcomes: {str(e)}")

        # Apply prospect changes with error handling
        try:
            if "job_prospects" in outcomes:
                if not isinstance(outcomes["job_prospects"], (int, float)):
                    logging.warning(f"Invalid job_prospects value: {outcomes['job_prospects']}")
                else:
                    job_change = float(outcomes["job_prospects"])
                    self.player.increase_job_prospects(job_change)
                    ui.display_success(f"Job prospects improved by {job_change}")
        except Exception as e:
            logging.error(f"Error processing job_prospects outcomes: {str(e)}")

        try:
            if "housing_prospects" in outcomes:
                if not isinstance(outcomes["housing_prospects"], (int, float)):
                    logging.warning(f"Invalid housing_prospects value: {outcomes['housing_prospects']}")
                else:
                    housing_change = float(outcomes["housing_prospects"])
                    self.player.increase_housing_prospects(housing_change)
                    ui.display_success(f"Housing prospects improved by {housing_change}")
        except Exception as e:
            logging.error(f"Error processing housing_prospects outcomes: {str(e)}")

        # Record event in journal
        self.journal.add_entry(event, choice, outcomes, self.time_system)

        # Check for insights
        insights = self.journal.get_insights()
        if insights:
            ui.display_title("\nReflections")
            for insight in insights:
                ui.display_text(f"• {insight}")

        # Track event patterns
        if event.type == self.last_event_type:
            self.consecutive_similar_events += 1
            if self.consecutive_similar_events >= 3:
                ui.display_warning("\nYou've been experiencing similar situations repeatedly. Consider trying different areas or activities.")
        else:
            self.consecutive_similar_events = 0
        self.last_event_type = event.type

        # Enhanced event chaining logic with context tracking
        choice_text = choice["text"].lower()
        next_event_id = None
        chain_context = {}

        # Track event chain state
        if not hasattr(self, 'active_chains'):
            self.active_chains = {}

        # Check if this event has any chain events defined
        if event.chain_events and len(event.chain_events) > 0:
            # Check for active chain context
            if event.event_id in self.active_chains:
                chain_context = self.active_chains[event.event_id]
            
            # Look for specific chain_event matches
            for trigger_text, event_data in event.chain_events.items():
                # Support both simple string and dict definitions
                if isinstance(event_data, dict):
                    event_id = event_data['next_event']
                    conditions = event_data.get('conditions', {})
                    
                    # Check all conditions are met
                    conditions_met = True
                    for condition, value in conditions.items():
                        if condition == 'story_flags':
                            for flag in value:
                                if not self.player.story_flags.get(flag, False):
                                    conditions_met = False
                                    break
                        elif condition == 'stats':
                            for stat, req in value.items():
                                if getattr(self.player, stat, 0) < req:
                                    conditions_met = False
                                    break
                                    
                    if conditions_met and trigger_text.lower() in choice_text:
                        next_event_id = event_id
                        break
                elif trigger_text.lower() in choice_text:
                    next_event_id = event_data
                    break
            
            # If we didn't find a match by text, try using the choice index
            if not next_event_id and str(choice_num) in event.chain_events:
                next_event_id = event.chain_events[str(choice_num)]
                
            # Process the chain event if one was found
            if next_event_id and next_event_id in self.events:
                ui.display_divider()
                ui.display_text("Your choice leads to a new situation...")
                # Store this choice in player's memory for future reference
                self.player.recent_choices = getattr(self.player, 'recent_choices', [])
                self.player.recent_choices.append({
                    'event_id': event.event_id,
                    'choice': choice_text,
                    'outcome': 'chain_to_' + next_event_id,
                    'day': self.time_system.get_day()
                })
                # Limit memory to most recent 10 choices
                if len(self.player.recent_choices) > 10:
                    self.player.recent_choices = self.player.recent_choices[-10:]
                
                chain_event = self.events[next_event_id]
                # Process the chain event after a short pause
                try:
                    safe_input("Press Enter to continue...")
                except:
                    pass  # Gracefully handle any input errors
                
                # Process the chain event
                self.process_event(chain_event, location)
                return  # End processing of current event since we've moved to a chain event
        
        # Track event outcome in player's memory for future reference
        self.player.recent_choices = getattr(self.player, 'recent_choices', [])
        self.player.recent_choices.append({
            'event_id': event.event_id,
            'choice': choice_text,
            'outcome': outcomes.get('message', 'completed'),
            'day': self.time_system.get_day()
        })
        # Limit memory to most recent 10 choices
        if len(self.player.recent_choices) > 10:
            self.player.recent_choices = self.player.recent_choices[-10:]

        # Ensure all stats stay within bounds
        self.player._clamp_stats()

        ui.display_divider()
        try:
            safe_input("Press Enter to continue...")
        except:
            pass  # Gracefully handle any input errors

    def _scale_event(self, event, difficulty):
        """Scale event outcomes based on difficulty.

        Args:
            event (Event): Event to scale
            difficulty (float): Difficulty modifier

        Returns:
            Event: Scaled event
        """
        scaled_event = Event(
            event_id=event.event_id,
            title=event.title,
            description=event.description,
            choices=event.choices.copy(),
            requirements=event.requirements,
            type=event.type,
            chain_events=event.chain_events.copy()
        )

        # Scale outcomes based on difficulty
        for choice in scaled_event.choices:
            outcomes = choice["outcomes"]
            if "health" in outcomes:
                outcomes["health"] = int(outcomes["health"] * difficulty)
            # Still using hunger in data, but will be converted to satiety at processing time
            if "hunger" in outcomes:
                outcomes["hunger"] = int(outcomes["hunger"] * difficulty)
            # Direct satiety handling
            if "satiety" in outcomes:
                outcomes["satiety"] = int(outcomes["satiety"] * difficulty)
            if "energy" in outcomes:
                outcomes["energy"] = int(outcomes["energy"] * difficulty)
            if "money" in outcomes:
                outcomes["money"] = int(outcomes["money"] * (2 - difficulty))  # Less money at higher difficulty

        return scaled_event

    def _create_generic_event(self, location):
        """Create a generic event based on location and time.

        Args:
            location (Location): Current location

        Returns:
            Event: Generic event
        """
        time_period = self.time_system.get_period()
        danger_level = location.danger_level

        if time_period == "morning":
            title = "Early Morning"
            description = "The city is coming to life as people head to work and businesses open."
            choices = [
                {
                    "text": "Look for breakfast opportunities",
                    "outcomes": {
                        "energy": -5,
                        "message": "You check a few places that might offer food, but don't find anything substantial."
                    }
                },
                {
                    "text": "Find a quiet place to rest",
                    "outcomes": {
                        "energy": 10,
                        "message": "You find a secluded spot to relax as the city wakes up."
                    }
                }
            ]
        elif time_period == "afternoon":
            title = "Busy Afternoon"
            description = "The streets are busy with people going about their day."
            choices = [
                {
                    "text": "People-watch from a public space",
                    "outcomes": {
                        "mental": 5,
                        "message": "You find some bench and observe the flow of city life, which provides a small distraction."
                    }
                },
                {
                    "text": "Look for opportunities or resources",
                    "outcomes": {
                        "energy": -10,
                        "skills": {"navigation": 1},
                        "message": "You explore the area, making mental notes of useful locations."
                    }
                }
            ]
        elif time_period == "evening":
            title = "Evening Transitions"
            description = "The character of the area changes as the work day ends and evening activities begin."
            choices = [
                {
                    "text": "Look for food as restaurants close",
                    "outcomes": {
                        "satiety": 10,  # Updated from hunger: -10
                        "message": "You manage to find some discarded but still good food from a restaurant closing for the day."
                    }
                },
                {
                    "text": "Start thinking about where to sleep",
                    "outcomes": {
                        "energy": 5,
                        "message": "You scout some potential sleeping spots, saving energy by planning ahead."
                    }
                }
            ]
        else:  # night
            title = "Night Falls"
            description = "The streets are quieter now, with different challenges and opportunities."
            choices = [
                {
                    "text": "Find a safe place to sleep",
                    "outcomes": {
                        "energy": 15,
                        "health": -5,
                        "message": "You find a hidden spot to rest for the night. It's not comfortable, but it's relatively safe."
                    }
                },
                {
                    "text": "Stay alert and keep moving",
                    "outcomes": {
                        "energy": -15,
                        "mental": -5,
                        "message": "You keep moving through the night, avoiding trouble but exhausting yourself."
                    }
                }
            ]

        # Adjust for location danger level
        if danger_level >= 7:  # High danger
            additional_choice = {
                "text": "Be extra cautious in this dangerous area",
                "outcomes": {
                    "energy": -10,
                    "mental": -5,
                    "message": "You stay on high alert in this dangerous area, which is stressful and tiring."
                }
            }
            choices.append(additional_choice)
        elif danger_level <= 3:  # Low danger
            additional_choice = {
                "text":"Relax a bit in this safer area",
                "outcomes": {
                    "mental": 10,
                    "message": "You allow yourself to relax slightly in this relatively safe area, which improves your mood."
                }
            }
            choices.append(additional_choice)

        return Event(
            event_id=f"generic_{time_period}_{location.name.lower().replace(' ', '_')}",
            title=title,
            description=description,
            choices=choices
        )

    def check_shelter_availability(self, shelter_name: str, quality: str) -> bool:
        """Check if shelter has space available."""
        base_chance = {
            "Mission": 0.2,  # Mission: 7/10 quality but 20% bed chance
            "Sal": 0.4,      # Sal: 4/10 quality but 40% bed chance 
            "Sheps": 0.85,   # Sheps: 3/10 quality but 85% bed chance
            "high": 0.3,
            "medium": 0.5,
            "low": 0.8
        }.get(shelter_name, 0.5)

        # Winter months reduce availability
        if datetime.now().month in [11, 12, 1, 2]:
            base_chance *= 0.5

        return random.random() < base_chance

    def get_shelter_quality(self, shelter_name: str) -> int:
        """Get shelter quality rating out of 10."""
        quality_ratings = {
            "Mission": 7,
            "Sal": 4,
            "Sheps": 3,
            "high": 8,
            "medium": 5,
            "low": 2
        }
        return quality_ratings.get(shelter_name, 5)