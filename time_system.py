"""
Time system for Hard Times: Ottawa.
Manages game time, day/night cycle, and weather.
"""
import random

class TimeSystem:
    """Manages the passage of time in the game."""
    
    def __init__(self):
        """Initialize the time system with starting values."""
        self.hour = 8  # Start at 8 AM
        self.day = 1
        self._validate_time_values()
        self.weather = self._generate_weather()
        self.temperature = self._generate_temperature()
        
    def _validate_time_values(self):
        """Validate time system values."""
        if not (0 <= self.hour < 24):
            raise ValueError(f"Invalid hour value: {self.hour}")
        if self.day < 1:
            raise ValueError(f"Invalid day value: {self.day}")
        
    def advance_time(self, hours):
        """Advance the game time by the specified number of hours.
        
        Args:
            hours (int): Number of hours to advance
            
        Returns:
            bool: True if a new day has started
        """
        self.hour += hours
        new_day = False
        
        # Check for day change
        while self.hour >= 24:
            self.hour -= 24
            self.day += 1
            new_day = True
            # Generate new weather each day
            self.weather = self._generate_weather()
            self.temperature = self._generate_temperature()
            
        return new_day
            
    def get_hour(self):
        """Get the current hour.
        
        Returns:
            int: Current hour (0-23)
        """
        return self.hour
        
    def get_day(self):
        """Get the current day.
        
        Returns:
            int: Current day number
        """
        return self.day
        
    def get_time_string(self):
        """Get a formatted string of the current time.
        
        Returns:
            str: Formatted time string (e.g., "8:00 AM")
        """
        period = "AM" if self.hour < 12 else "PM"
        display_hour = self.hour % 12
        if display_hour == 0:
            display_hour = 12
            
        return f"{display_hour}:00 {period}"
        
    def get_period(self):
        """Get the current period of the day.
        
        Returns:
            str: Period name ('morning', 'afternoon', 'evening', 'night')
        """
        if 6 <= self.hour < 12:
            return "morning"
        elif 12 <= self.hour < 17:
            return "afternoon"
        elif 17 <= self.hour < 21:
            return "evening"
        else:
            return "night"
            
    def _generate_weather(self):
        """Generate weather based on season and previous conditions.
        
        Returns:
            str: Weather condition
        """
        season = self.get_season()
        
        # Weather probabilities adjusted by season
        season_weather = {
            "winter": {"clear": 0.3, "cloudy": 0.3, "snow": 0.3, "storm": 0.1},
            "spring": {"clear": 0.3, "cloudy": 0.4, "rain": 0.25, "storm": 0.05},
            "summer": {"clear": 0.5, "cloudy": 0.3, "rain": 0.15, "storm": 0.05},
            "fall": {"clear": 0.3, "cloudy": 0.4, "rain": 0.25, "storm": 0.05}
        }
        
        # Get current season's weather options
        weather_options = season_weather[season]
        
        # Prevent unrealistic weather transitions
        if hasattr(self, 'weather'):
            if self.weather == "storm":
                # After storm, likely cloudy or clearing
                return random.choice(["cloudy", "clear"])
            elif self.weather == "snow" and self.temperature > 2:
                # Snow can't persist in warm weather
                return random.choice(["rain", "cloudy"])
        
        # Weighted random selection
        rand = random.random()
        cumulative = 0
        for weather, probability in weather_options.items():
            cumulative += probability
            if rand <= cumulative:
                return weather
                
        return "clear"  # Default fallback
        
    def get_season(self):
        """Get current season based on day number."""
        day = self.day % 360
        if 0 <= day < 90:
            return "winter"
        elif 90 <= day < 180:
            return "spring"
        elif 180 <= day < 270:
            return "summer"
        else:
            return "fall"

    def _generate_temperature(self):
        """Generate a realistic temperature appropriate for the weather and season.
        
        Returns:
            int: Temperature in degrees Celsius
        """
        season = self.get_season()
        hour = self.get_hour()
        
        # Base temperature ranges by season with day/night variation
        season_ranges = {
            "winter": {"day": (-15, 0), "night": (-25, -10)},
            "spring": {"day": (5, 20), "night": (0, 10)},
            "summer": {"day": (20, 30), "night": (15, 25)},
            "fall": {"day": (10, 20), "night": (5, 15)}
        }
        
        # Determine if it's day or night
        is_day = 6 <= hour < 18
        period = "day" if is_day else "night"
        min_temp, max_temp = season_ranges[season][period]
        
        # Generate base temperature
        base_temp = random.randint(min_temp, max_temp)
        
        # Apply weather modifications within realistic bounds
        weather_mods = {
            "clear": lambda t: min(max_temp, t + random.randint(0, 3)),
            "cloudy": lambda t: t - random.randint(0, 2),
            "rain": lambda t: t - random.randint(1, 3),
            "snow": lambda t: min(-2, t - random.randint(2, 5)),  # Snow only when cold
            "storm": lambda t: t - random.randint(2, 4)
        }
        
        if self.weather in weather_mods:
            base_temp = weather_mods[self.weather](base_temp)
            
        return max(min_temp, min(max_temp, base_temp))  # Ensure within season range
        
    def get_weather_effects(self):
        """Get the gameplay effects of the current weather.
        
        Returns:
            dict: Weather effects on gameplay
        """
        effects = {
            "health_mod": 0,
            "energy_mod": 0,
            "shelter_importance": 1.0,
            "scavenging_mod": 1.0,
            "social_mod": 1.0,
            "travel_difficulty": 1.0,
            "event_modifiers": [],
            "description": ""
        }
        
        # Add event modifiers based on weather
        if self.weather == "storm":
            effects["event_modifiers"] = ["dangerous", "isolation"]
        elif self.weather == "snow":
            effects["event_modifiers"] = ["cold", "community"]
        elif self.weather == "rain":
            effects["event_modifiers"] = ["wet", "indoor_focus"]
        
        # Modify effects based on weather and temperature
        if self.weather == "clear":
            effects["description"] = "It's a clear day."
            if self.temperature > 20:
                effects["description"] = "It's hot and sunny."
                effects["energy_mod"] = -1
            elif self.temperature < 0:
                effects["description"] = "It's clear but very cold."
                effects["health_mod"] = -1
                effects["shelter_importance"] = 1.5
                
        elif self.weather == "cloudy":
            effects["description"] = "The sky is overcast with clouds."
            if self.temperature < 0:
                effects["description"] = "It's cloudy and cold."
                effects["shelter_importance"] = 1.2
                
        elif self.weather == "rain":
            effects["description"] = "It's raining."
            effects["health_mod"] = -1
            effects["energy_mod"] = -1
            effects["shelter_importance"] = 1.5
            if self.temperature < 5:
                effects["description"] = "It's raining and uncomfortably cold."
                effects["health_mod"] = -2
                effects["shelter_importance"] = 2.0
                
        elif self.weather == "snow":
            effects["description"] = "It's snowing."
            effects["health_mod"] = -2
            effects["energy_mod"] = -1
            effects["shelter_importance"] = 2.0
            if self.temperature < -10:
                effects["description"] = "Heavy snow and freezing temperatures make being outside dangerous."
                effects["health_mod"] = -3
                effects["shelter_importance"] = 2.5
                
        elif self.weather == "storm":
            if self.temperature > 0:
                effects["description"] = "A thunderstorm is raging outside."
            else:
                effects["description"] = "A blizzard is making conditions treacherous."
            effects["health_mod"] = -3
            effects["energy_mod"] = -2
            effects["shelter_importance"] = 3.0
            
        return effects
        
    def is_harsh_weather(self):
        """Check if current weather conditions are harsh.
        
        Returns:
            bool: True if weather is harsh and dangerous
        """
        if self.weather in ["snow", "storm"]:
            return True
        if self.weather == "rain" and self.temperature < 5:
            return True
        if self.temperature < -15:
            return True
            
        return False
