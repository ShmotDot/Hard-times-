"""
Location system for Hard Times: Ottawa.
Handles all location-related functionality.
"""
import json
import os
import random
from collections import defaultdict

class Location:
    """Represents a location in the game world."""
    
    def __init__(self, name, description, danger_level, food_availability, 
                 shelter_options, connected_locations, travel_time, period_modifiers,
                 services, discovery_text, quest_areas=None, npc_hotspots=None, location_type="general"):
        """Initialize a location with enhanced features.
        
        Args:
            name (str): Location name
            description (str): Location description
            danger_level (int): Base danger level (1-10)
            food_availability (float): Base food availability (0-1)
            shelter_options (dict): Enhanced shelter options with quality metrics
            connected_locations (list): Connected location names
            travel_time (int): Hours needed to travel here
            period_modifiers (dict): Time period effects
            services (list): Available services with requirements/benefits
            discovery_text (str): Initial discovery description
            quest_areas (dict): Areas for quest generation
            npc_hotspots (dict): NPC encounter locations
            location_type (str): Type of location for quest triggers
        """
        self.name = name
        self.description = description
        self.danger_level = danger_level
        self.food_availability = food_availability
        self.shelter_options = shelter_options
        self.connected_locations = connected_locations
        self.travel_time = travel_time
        self.period_modifiers = period_modifiers
        self.services = services
        self.discovery_text = discovery_text
        self.discovered = False
        self.quest_areas = quest_areas or {}
        self.npc_hotspots = npc_hotspots or {}
        self.active_events = set()
        self.completed_quests = set()
        
    def get_quest_areas(self, time_period):
        """Get available quest areas during the given time period."""
        available_areas = {}
        for area_name, area_data in self.quest_areas.items():
            if time_period in area_data.get("available_periods", []):
                available_areas[area_name] = area_data
        return available_areas
        
    def get_npc_hotspots(self, time_period):
        """Get NPC hotspots active during the given time period."""
        active_hotspots = {}
        for spot_name, spot_data in self.npc_hotspots.items():
            if time_period in spot_data.get("active_periods", []):
                active_hotspots[spot_name] = spot_data
        return active_hotspots
        
    def add_active_event(self, event_id):
        """Track an active event at this location."""
        self.active_events.add(event_id)
        
    def remove_active_event(self, event_id):
        """Remove an event from active events."""
        self.active_events.discard(event_id)
        
    def complete_quest(self, quest_id):
        """Mark a quest as completed at this location."""
        self.completed_quests.add(quest_id)
        
    def get_shelter_options(self):
        """Get available shelter options at this location.
        
        Returns:
            dict: Available shelter options and their quality
        """
        return self.shelter_options
        
    def get_location_effects(self, time_system):
        """Get current effects of the location based on weather and time.
        
        Args:
            time_system (TimeSystem): Current time system instance
            
        Returns:
            dict: Current location effects
        """
        effects = {
            "safety": self.danger_level,
            "food_availability": self.food_availability,
            "shelter_quality": 1.0,
            "description": ""
        }
        
        # Modify effects based on weather
        weather_effects = time_system.get_weather_effects()
        if weather_effects["shelter_importance"] > 1.5:
            effects["shelter_quality"] *= 0.7
            effects["food_availability"] *= 0.5
            
        # Time of day modifications
        current_period = time_system.get_period()
        if current_period in self.period_modifiers:
            mods = self.period_modifiers[current_period]
            effects["safety"] += mods.get("danger", 0)
            effects["food_availability"] += mods.get("food", 0)
            
        # Season effects
        season = time_system.get_season()
        if season == "winter":
            if "Community Center" in self.shelter_options or "Shelter" in self.shelter_options:
                effects["shelter_quality"] *= 1.5
                effects["description"] = "The indoor shelter provides crucial protection from the cold."
                
        return effects

    def get_rest_quality(self, time_period, time_system=None):
        """Get the quality of rest at this location during the given time period.
        
        Args:
            time_period (str): Time period ('morning', 'afternoon', 'evening', 'night')
            time_system (TimeSystem, optional): Time system object for weather effects
            
        Returns:
            str: Rest quality ('dangerous', 'poor', 'decent', 'good')
        """
        # Base danger level determines rest quality
        if self.danger_level >= 8:
            base_quality = "dangerous"
        elif self.danger_level >= 5:
            base_quality = "poor"
        elif self.danger_level >= 3:
            base_quality = "decent"
        else:
            base_quality = "good"
            
        # Time period modifiers can change the quality
        if time_period in self.period_modifiers:
            period_danger_mod = self.period_modifiers[time_period].get("danger", 0)
            
            # Adjust quality based on time-specific danger modifier
            if period_danger_mod >= 3 and base_quality != "dangerous":
                return "dangerous"
            elif period_danger_mod >= 2 and base_quality not in ["dangerous", "poor"]:
                return "poor"
            elif period_danger_mod <= -2 and base_quality != "good":
                return "decent" if base_quality == "poor" else "good"
                
        return base_quality
        
    def discover(self):
        """Mark this location as discovered."""
        self.discovered = True
        
    def get_service(self, service_name):
        """Get details of a specific service at this location.
        
        Args:
            service_name (str): The name of the service
            
        Returns:
            dict: Service details or None if not available
        """
        for service in self.services:
            if service["name"] == service_name:
                return service
        return None

class LocationManager:
    """Manages locations in the game world."""
    
    def __init__(self):
        """Initialize the location manager and load location data."""
        self.locations = {}
        self.load_locations()
        
    def load_locations(self):
        """Load location data from the JSON file."""
        try:
            # Create a locations dictionary to use if the file doesn't exist
            default_locations = {
                "Downtown": {
                    "name": "Downtown",
                    "description": "The busy downtown core with businesses, offices, and pedestrian traffic.",
                    "danger_level": 5,
                    "food_availability": 0.7,
                    "shelter_options": {
                        "City Mission Shelter": "medium",
                        "Downtown Alley": "low",
                        "Public Park Bench": "low"
                    },
                    "connected_locations": ["ByWard Market", "Centretown", "Lebreton Flats"],
                    "travel_time": 1,
                    "period_modifiers": {
                        "morning": {"danger": -1, "food": 0.1},
                        "afternoon": {"danger": -1, "food": 0.2},
                        "evening": {"danger": 0, "food": 0.1},
                        "night": {"danger": 2, "food": -0.2}
                    },
                    "services": [
                        {"name": "Drop-in Center", "hours": "8:00-16:00", "description": "Provides meals and basic services during the day."},
                        {"name": "Public Library", "hours": "9:00-21:00", "description": "Warm place to rest and access computers."}
                    ],
                    "discovery_text": "You find yourself in the busy downtown core of Ottawa. The streets are filled with office workers and tourists."
                },
                "ByWard Market": {
                    "name": "ByWard Market",
                    "description": "A historic market district with food vendors, restaurants, and nightlife.",
                    "danger_level": 4,
                    "food_availability": 0.8,
                    "shelter_options": {
                        "Market Alleyway": "low",
                        "Youth Shelter": "high"
                    },
                    "connected_locations": ["Downtown", "Lowertown", "Sandy Hill"],
                    "travel_time": 1,
                    "period_modifiers": {
                        "morning": {"danger": -1, "food": 0.2},
                        "afternoon": {"danger": -1, "food": 0.1},
                        "evening": {"danger": 0, "food": 0.3},
                        "night": {"danger": 2, "food": 0.1}
                    },
                    "services": [
                        {"name": "Food Bank", "hours": "10:00-14:00", "description": "Provides food packages once per week."},
                        {"name": "Community Kitchen", "hours": "11:00-13:00", "description": "Offers a hot meal at lunchtime."}
                    ],
                    "discovery_text": "The ByWard Market is bustling with activity. The smell of food wafts from numerous vendors and restaurants."
                },
                "Centretown": {
                    "name": "Centretown",
                    "description": "A mixed residential and commercial area with apartment buildings and small businesses.",
                    "danger_level": 3,
                    "food_availability": 0.5,
                    "shelter_options": {
                        "Community Center": "medium",
                        "Apartment Building Stairwell": "low"
                    },
                    "connected_locations": ["Downtown", "Glebe", "Little Italy"],
                    "travel_time": 1,
                    "period_modifiers": {
                        "morning": {"danger": -1, "food": 0},
                        "afternoon": {"danger": -1, "food": 0.1},
                        "evening": {"danger": 0, "food": 0},
                        "night": {"danger": 1, "food": -0.1}
                    },
                    "services": [
                        {"name": "Health Clinic", "hours": "9:00-17:00", "description": "Provides basic healthcare for those in need."},
                        {"name": "Community Support Center", "hours": "8:30-16:30", "description": "Offers assistance with housing applications and support services."}
                    ],
                    "discovery_text": "Centretown is a quieter area with a mix of apartment buildings and small businesses."
                },
                "Lebreton Flats": {
                    "name": "Lebreton Flats",
                    "description": "A developing area with open spaces and construction sites.",
                    "danger_level": 6,
                    "food_availability": 0.3,
                    "shelter_options": {
                        "Abandoned Construction Site": "low",
                        "Undeveloped Lot": "low"
                    },
                    "connected_locations": ["Downtown", "Hintonburg", "Mechanicsville"],
                    "travel_time": 1,
                    "period_modifiers": {
                        "morning": {"danger": 0, "food": -0.1},
                        "afternoon": {"danger": -1, "food": 0},
                        "evening": {"danger": 1, "food": -0.1},
                        "night": {"danger": 2, "food": -0.2}
                    },
                    "services": [
                        {"name": "Outreach Van", "hours": "19:00-22:00", "description": "Mobile service providing basic supplies and support."}
                    ],
                    "discovery_text": "Lebreton Flats is mostly open space with construction sites. It feels exposed but has some hidden corners."
                },
                "Lowertown": {
                    "name": "Lowertown",
                    "description": "A historic neighborhood with a mix of housing, shelters, and social services.",
                    "danger_level": 7,
                    "food_availability": 0.5,
                    "shelter_options": {
                        "Main Shelter": "medium",
                        "Underpass Camp": "low"
                    },
                    "connected_locations": ["ByWard Market", "Sandy Hill", "Vanier"],
                    "travel_time": 1,
                    "period_modifiers": {
                        "morning": {"danger": 0, "food": 0},
                        "afternoon": {"danger": -1, "food": 0.1},
                        "evening": {"danger": 1, "food": 0},
                        "night": {"danger": 3, "food": -0.1}
                    },
                    "services": [
                        {"name": "Soup Kitchen", "hours": "17:00-19:00", "description": "Provides evening meals."},
                        {"name": "Clothing Bank", "hours": "13:00-16:00", "description": "Offers free clothing and personal items."}
                    ],
                    "discovery_text": "Lowertown has a gritty feel but also houses many services for those in need."
                },
                "Sandy Hill": {
                    "name": "Sandy Hill",
                    "description": "A residential area with student housing, apartments, and the University of Ottawa.",
                    "danger_level": 2,
                    "food_availability": 0.4,
                    "shelter_options": {
                        "Student Center": "medium",
                        "Campus Building": "low"
                    },
                    "connected_locations": ["ByWard Market", "Lowertown", "Vanier"],
                    "travel_time": 1,
                    "period_modifiers": {
                        "morning": {"danger": -1, "food": 0},
                        "afternoon": {"danger": -1, "food": 0.1},
                        "evening": {"danger": 0, "food": 0.2},
                        "night": {"danger": 1, "food": 0}
                    },
                    "services": [
                        {"name": "University Cafeteria", "hours": "7:00-19:00", "description": "Sometimes has leftover food at closing time."},
                        {"name": "Student Health Services", "hours": "9:00-16:00", "description": "Can provide basic medical care in emergencies."}
                    ],
                    "discovery_text": "Sandy Hill is filled with student housing and university buildings. Young people hurry to and from classes."
                },
                "Vanier": {
                    "name": "Vanier",
                    "description": "A diverse neighborhood east of downtown with affordable housing and immigrant communities.",
                    "danger_level": 6,
                    "food_availability": 0.6,
                    "shelter_options": {
                        "Community Housing": "medium",
                        "Wooded Area": "low"
                    },
                    "connected_locations": ["Lowertown", "Sandy Hill", "Overbrook"],
                    "travel_time": 2,
                    "period_modifiers": {
                        "morning": {"danger": 0, "food": 0.1},
                        "afternoon": {"danger": -1, "food": 0.1},
                        "evening": {"danger": 1, "food": 0},
                        "night": {"danger": 2, "food": -0.2}
                    },
                    "services": [
                        {"name": "Cultural Food Bank", "hours": "11:00-15:00", "description": "Provides culturally diverse food options."},
                        {"name": "Employment Center", "hours": "9:00-17:00", "description": "Offers job search assistance and training programs."}
                    ],
                    "discovery_text": "Vanier is a melting pot of cultures with various small shops and community spaces."
                },
                "Hintonburg": {
                    "name": "Hintonburg",
                    "description": "An up-and-coming neighborhood with art studios, coffee shops, and gentrifying streets.",
                    "danger_level": 3,
                    "food_availability": 0.5,
                    "shelter_options": {
                        "Art Space": "medium",
                        "Industrial Building": "low"
                    },
                    "connected_locations": ["Lebreton Flats", "Mechanicsville", "Westboro"],
                    "travel_time": 2,
                    "period_modifiers": {
                        "morning": {"danger": -1, "food": 0.1},
                        "afternoon": {"danger": -2, "food": 0.2},
                        "evening": {"danger": -1, "food": 0.1},
                        "night": {"danger": 1, "food": -0.1}
                    },
                    "services": [
                        {"name": "Community Art Center", "hours": "10:00-18:00", "description": "Offers free programs and a warm place to stay during the day."},
                        {"name": "Coffee Shop Donations", "hours": "20:00-21:00", "description": "Some cafes give away unsold food at closing time."}
                    ],
                    "discovery_text": "Hintonburg has a creative vibe with murals on buildings and small galleries scattered about."
                },
                "Mechanicsville": {
                    "name": "Mechanicsville",
                    "description": "A riverside working-class neighborhood with industrial history.",
                    "danger_level": 5,
                    "food_availability": 0.4,
                    "shelter_options": {
                        "Riverside Camp": "low",
                        "Warehouse": "low"
                    },
                    "connected_locations": ["Lebreton Flats", "Hintonburg"],
                    "travel_time": 1,
                    "period_modifiers": {
                        "morning": {"danger": 0, "food": 0},
                        "afternoon": {"danger": -1, "food": 0.1},
                        "evening": {"danger": 0, "food": 0},
                        "night": {"danger": 2, "food": -0.1}
                    },
                    "services": [
                        {"name": "Workers' Aid Center", "hours": "7:00-15:00", "description": "Provides day labor opportunities and basic services."}
                    ],
                    "discovery_text": "Mechanicsville sits by the river with old industrial buildings and modest homes."
                },
                "Glebe": {
                    "name": "Glebe",
                    "description": "An affluent neighborhood with upscale shops, restaurants, and the TD Place stadium.",
                    "danger_level": 2,
                    "food_availability": 0.6,
                    "shelter_options": {
                        "Park Pavilion": "low",
                        "Stadium Area": "low"
                    },
                    "connected_locations": ["Centretown", "Old Ottawa South"],
                    "travel_time": 2,
                    "period_modifiers": {
                        "morning": {"danger": -1, "food": 0.1},
                        "afternoon": {"danger": -1, "food": 0.2},
                        "evening": {"danger": 0, "food": 0.2},
                        "night": {"danger": 1, "food": 0}
                    },
                    "services": [
                        {"name": "Community Center", "hours": "8:00-22:00", "description": "Has public washrooms and occasional community meals."},
                        {"name": "Stadium Events", "hours": "varies", "description": "Opportunities for bottle collection and leftover food after events."}
                    ],
                    "discovery_text": "The Glebe is clearly affluent, with well-kept homes and trendy shops. People here seem to have money to spare."
                },
                "Westboro": {
                    "name": "Westboro",
                    "description": "A trendy neighborhood with outdoor retailers, restaurants, and beach access.",
                    "danger_level": 2,
                    "food_availability": 0.5,
                    "shelter_options": {
                        "Beach Area": "low",
                        "Wooded Park": "medium"
                    },
                    "connected_locations": ["Hintonburg", "Nepean"],
                    "travel_time": 3,
                    "period_modifiers": {
                        "morning": {"danger": -1, "food": 0},
                        "afternoon": {"danger": -1, "food": 0.1},
                        "evening": {"danger": 0, "food": 0.2},
                        "night": {"danger": 1, "food": -0.1}
                    },
                    "services": [
                        {"name": "Outdoor Store Donations", "hours": "19:00-20:00", "description": "Some stores donate unsold food and occasionally equipment."},
                        {"name": "Beach Facilities", "hours": "6:00-23:00", "description": "Public washrooms and water fountains available seasonally."}
                    ],
                    "discovery_text": "Westboro has an outdoor lifestyle vibe with shops selling expensive gear and a beach along the river."
                },
                "Overbrook": {
                    "name": "Overbrook",
                    "description": "A diverse residential area with a mix of housing types and community facilities.",
                    "danger_level": 4,
                    "food_availability": 0.4,
                    "shelter_options": {
                        "Community Center": "medium",
                        "Train Yard": "low"
                    },
                    "connected_locations": ["Vanier", "Train Yards"],
                    "travel_time": 2,
                    "period_modifiers": {
                        "morning": {"danger": 0, "food": 0},
                        "afternoon": {"danger": -1, "food": 0.1},
                        "evening": {"danger": 0, "food": 0},
                        "night": {"danger": 2, "food": -0.1}
                    },
                    "services": [
                        {"name": "Recreation Center", "hours": "6:00-22:00", "description": "Public facilities and occasional community programs."},
                        {"name": "Food Pantry", "hours": "14:00-16:00 (Wed/Fri)", "description": "Provides food packages twice weekly."}
                    ],
                    "discovery_text": "Overbrook is a quiet residential area with community facilities and varied housing types."
                },
                "Train Yards": {
                    "name": "Train Yards",
                    "description": "A shopping district with big box stores and parking lots.",
                    "danger_level": 4,
                    "food_availability": 0.6,
                    "shelter_options": {
                        "Loading Area": "low",
                        "Abandoned Structure": "low"
                    },
                    "connected_locations": ["Overbrook", "St. Laurent"],
                    "travel_time": 2,
                    "period_modifiers": {
                        "morning": {"danger": 0, "food": 0},
                        "afternoon": {"danger": -1, "food": 0.2},
                        "evening": {"danger": 0, "food": 0.1},
                        "night": {"danger": 1, "food": -0.2}
                    },
                    "services": [
                        {"name": "Grocery Store Dumpster", "hours": "always", "description": "Sometimes has discarded but still edible food."},
                        {"name": "Food Court", "hours": "10:00-21:00", "description": "Leftover food sometimes available at closing time."}
                    ],
                    "discovery_text": "The Train Yards is a sprawling shopping complex with large stores and vast parking lots."
                }
            }
            
            # Try to load locations from JSON file
            file_path = os.path.join("data", "locations.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    location_data = json.load(f)
            else:
                # Use default locations if file doesn't exist
                location_data = default_locations
                
                # Ensure data directory exists
                os.makedirs("data", exist_ok=True)
                
                # Write default locations to JSON file
                with open(file_path, 'w') as f:
                    json.dump(default_locations, f, indent=4)
                
            # Create Location objects
            for name, data in location_data.items():
                # Handle potential differences in shelter_options format between JSON and code
                shelter_options = data.get("shelter_options", {})
                # Handle case where shelter options might be simple strings in a dict
                if isinstance(shelter_options, dict) and any(isinstance(value, str) for value in shelter_options.values()):
                    normalized_shelters = {}
                    for shelter_name, quality in shelter_options.items():
                        if isinstance(quality, str):
                            normalized_shelters[shelter_name] = {"quality": quality, "cost": 0, "warmth": 0.5, "security": 0.5}
                        else:
                            normalized_shelters[shelter_name] = quality
                    shelter_options = normalized_shelters

                location = Location(
                    name=data["name"],
                    description=data["description"],
                    danger_level=data["danger_level"],
                    food_availability=data["food_availability"],
                    shelter_options=shelter_options,
                    connected_locations=data["connected_locations"],
                    travel_time=data["travel_time"],
                    period_modifiers=data["period_modifiers"],
                    services=data["services"],
                    discovery_text=data.get("discovery_text", f"You arrive in {data['name']}.")
                )
                
                # Mark Downtown as discovered by default
                if name == "Downtown":
                    location.discovered = True
                    
                self.locations[name] = location
                
        except Exception as e:
            print(f"Error loading locations: {e}")
            # Create a minimal set of locations if loading fails
            downtown = Location(
                name="Downtown",
                description="The busy downtown core of Ottawa.",
                danger_level=5,
                food_availability=0.7,
                shelter_options={"Shelter": "medium", "Alley": "low"},
                connected_locations=["ByWard Market"],
                travel_time=1,
                period_modifiers={},
                services=[],
                discovery_text="You find yourself in downtown Ottawa."
            )
            downtown.discovered = True
            
            byward = Location(
                name="ByWard Market",
                description="A historic market district with many food options.",
                danger_level=4,
                food_availability=0.8,
                shelter_options={"Market Shelter": "medium"},
                connected_locations=["Downtown"],
                travel_time=1,
                period_modifiers={},
                services=[],
                discovery_text="The ByWard Market is full of food vendors and shops."
            )
            
            self.locations = {
                "Downtown": downtown,
                "ByWard Market": byward
            }
            
    def get_location(self, name):
        """Get a location by name.
        
        Args:
            name (str): The name of the location
            
        Returns:
            Location: The location object or None if not found
        """
        return self.locations.get(name)
        
    def get_available_locations(self, current_location):
        """Get locations that are available to travel to from the current location.
        
        Args:
            current_location (Location): The current location
            
        Returns:
            list: List of available location objects
        """
        available = []
        
        for loc_name in current_location.connected_locations:
            location = self.get_location(loc_name)
            if location:
                # Only add to available if already discovered or adjacent to current
                if location.discovered:
                    available.append(location)
                else:
                    # Discover new connected locations
                    location.discover()
                    available.append(location)
                    
        return available
        
    def get_all_discovered_locations(self):
        """Get all locations that have been discovered.
        
        Returns:
            list: List of discovered location objects
        """
        return [loc for loc in self.locations.values() if loc.discovered]
    
    def get_discovered_location_names(self):
        """Get names of all locations that have been discovered.
        
        Returns:
            list: List of discovered location names
        """
        return [loc.name for loc in self.locations.values() if loc.discovered]
        
    def mark_location_discovered(self, location_name):
        """Mark a location as discovered by name.
        
        Args:
            location_name (str): The name of the location to mark as discovered
            
        Returns:
            bool: True if the location was marked, False if not found
        """
        location = self.get_location(location_name)
        if location:
            location.discover()
            return True
        return False
