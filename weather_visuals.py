"""
Weather visuals module for Hard Times Ottawa.
Provides visual indicators for different weather conditions in the text-based UI.
"""

class WeatherVisuals:
    """Handles generation of visual weather indicators in text UI."""
    
    def __init__(self, use_colors=True):
        """Initialize the weather visuals system.
        
        Args:
            use_colors (bool): Whether to use ANSI color codes
        """
        self.use_colors = use_colors
        
        # Define color codes for weather visuals
        self.colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "blue": "\033[94m",
            "cyan": "\033[96m", 
            "white": "\033[97m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "green": "\033[92m",
            "gray": "\033[90m",
            "bg_blue": "\033[44m",
            "bg_cyan": "\033[46m",
            "bg_white": "\033[47m",
            "bg_yellow": "\033[43m",
            "bg_red": "\033[41m"
        }
    
    def get_weather_icon(self, weather_type, temperature=None):
        """Get a text-based icon representing the current weather.
        
        Args:
            weather_type (str): The type of weather
            temperature (int, optional): Current temperature in Celsius
            
        Returns:
            str: Text-based icon for the weather
        """
        # Default icon if colors are disabled
        if not self.use_colors:
            icons = {
                "clear": "[ SUN ]",
                "cloudy": "[CLOUD]",
                "rain": "[RAIN ]",
                "snow": "[SNOW ]",
                "storm": "[STORM]"
            }
            return icons.get(weather_type, "[ ??? ]")
        
        # Colored icons for different weather types
        if weather_type == "clear":
            if temperature and temperature > 25:
                # Hot sun
                return f"{self.colors['bg_yellow']} {self.colors['red']}☀{self.colors['reset']}{self.colors['bg_yellow']} {self.colors['reset']}"
            else:
                # Normal sun
                return f"{self.colors['bg_cyan']} {self.colors['yellow']}☀{self.colors['reset']}{self.colors['bg_cyan']} {self.colors['reset']}"
        
        elif weather_type == "cloudy":
            return f"{self.colors['bg_white']} {self.colors['gray']}☁{self.colors['reset']}{self.colors['bg_white']} {self.colors['reset']}"
        
        elif weather_type == "rain":
            return f"{self.colors['bg_blue']} {self.colors['cyan']}☂{self.colors['reset']}{self.colors['bg_blue']} {self.colors['reset']}"
        
        elif weather_type == "snow":
            return f"{self.colors['bg_cyan']} {self.colors['white']}❄{self.colors['reset']}{self.colors['bg_cyan']} {self.colors['reset']}"
        
        elif weather_type == "storm":
            return f"{self.colors['bg_blue']} {self.colors['yellow']}⚡{self.colors['reset']}{self.colors['bg_blue']} {self.colors['reset']}"
        
        else:
            return f"{self.colors['bg_white']} ? {self.colors['reset']}"
    
    def get_weather_banner(self, weather_type, temperature, is_harsh=False):
        """Get a multi-line banner visualizing the current weather conditions.
        
        Args:
            weather_type (str): The type of weather
            temperature (int): Current temperature in Celsius
            is_harsh (bool): Whether current weather is classified as harsh/dangerous
            
        Returns:
            str: Multi-line string with a weather visualization
        """
        if not self.use_colors:
            # Simple non-colored banner
            if is_harsh:
                return f"!!! HARSH WEATHER: {weather_type.upper()} ({temperature}°C) !!!"
            return f"Weather: {weather_type.title()} ({temperature}°C)"
        
        # Create a colored visual banner based on weather type
        banner_lines = []
        width = 30
        temp_str = f"{temperature}°C"
        
        # Top border
        border_char = "═" if is_harsh else "─"
        if is_harsh:
            border = f"{self.colors['red']}{border_char * width}{self.colors['reset']}"
        else:
            border = f"{self.colors['cyan']}{border_char * width}{self.colors['reset']}"
        banner_lines.append(border)
        
        # Add weather-specific visuals
        if weather_type == "clear":
            if temperature > 25:
                banner_lines.append(f"{self.colors['yellow']}    \\   {self.colors['red']}☀{self.colors['yellow']}   /     {self.colors['cyan']}Temperature:{self.colors['reset']} {temp_str}")
                banner_lines.append(f"{self.colors['yellow']}     ⎯⎯⎯⎯⎯⎯⎯⎯       {self.colors['cyan']}Conditions:{self.colors['reset']} Hot & Sunny")
            else:
                banner_lines.append(f"{self.colors['cyan']}    \\   {self.colors['yellow']}☀{self.colors['cyan']}   /     {self.colors['cyan']}Temperature:{self.colors['reset']} {temp_str}")
                banner_lines.append(f"{self.colors['cyan']}     ⎯⎯⎯⎯⎯⎯⎯⎯       {self.colors['cyan']}Conditions:{self.colors['reset']} Clear")
        
        elif weather_type == "cloudy":
            banner_lines.append(f"{self.colors['gray']}     ☁   ☁       {self.colors['cyan']}Temperature:{self.colors['reset']} {temp_str}")
            banner_lines.append(f"{self.colors['gray']}   ☁   ☁         {self.colors['cyan']}Conditions:{self.colors['reset']} Cloudy")
        
        elif weather_type == "rain":
            banner_lines.append(f"{self.colors['gray']}  ☁ ☁ ☁ ☁ ☁     {self.colors['cyan']}Temperature:{self.colors['reset']} {temp_str}")
            banner_lines.append(f"{self.colors['blue']}  ╱ ╱ ╱ ╱ ╱ ╱    {self.colors['cyan']}Conditions:{self.colors['reset']} Rainy")
            if temperature < 5:
                banner_lines.append(f"{self.colors['cyan']}  ╱ ╱ ╱ ╱ ╱ ╱    {self.colors['yellow']}Warning: Cold Rain{self.colors['reset']}")
        
        elif weather_type == "snow":
            banner_lines.append(f"{self.colors['white']}  ❄   ❄   ❄      {self.colors['cyan']}Temperature:{self.colors['reset']} {temp_str}")
            banner_lines.append(f"{self.colors['white']}    ❄   ❄        {self.colors['cyan']}Conditions:{self.colors['reset']} Snowy")
            if temperature < -10:
                banner_lines.append(f"{self.colors['white']}  ❄   ❄   ❄      {self.colors['red']}Warning: Freezing{self.colors['reset']}")
        
        elif weather_type == "storm":
            if temperature > 0:
                # Thunderstorm
                banner_lines.append(f"{self.colors['gray']}  ☁☁☁☁☁☁       {self.colors['cyan']}Temperature:{self.colors['reset']} {temp_str}")
                banner_lines.append(f"{self.colors['blue']}  ╱╱{self.colors['yellow']}⚡{self.colors['blue']}╱╱{self.colors['yellow']}⚡{self.colors['blue']}╱    {self.colors['cyan']}Conditions:{self.colors['reset']} Thunderstorm")
                banner_lines.append(f"{self.colors['blue']}  ╱╱╱╱╱╱╱       {self.colors['red']}Warning: Dangerous{self.colors['reset']}")
            else:
                # Blizzard
                banner_lines.append(f"{self.colors['white']}  ❄❄❄❄❄❄❄      {self.colors['cyan']}Temperature:{self.colors['reset']} {temp_str}")
                banner_lines.append(f"{self.colors['white']}  ➙➙➙➙➙➙➙      {self.colors['cyan']}Conditions:{self.colors['reset']} Blizzard")
                banner_lines.append(f"{self.colors['white']}  ❄❄❄❄❄❄❄      {self.colors['red']}Warning: Hazardous{self.colors['reset']}")
        
        # Bottom border
        banner_lines.append(border)
        
        return "\n".join(banner_lines)
    
    def get_temperature_bar(self, temperature):
        """Generate a colored thermometer bar showing temperature.
        
        Args:
            temperature (int): Current temperature in Celsius
            
        Returns:
            str: String representing a temperature bar
        """
        if not self.use_colors:
            # Non-colored representation
            return f"Temperature: {temperature}°C"
        
        # Define temperature ranges and their colors
        freezing = self.colors['cyan']
        cold = self.colors['blue'] 
        cool = self.colors['green']
        warm = self.colors['yellow']
        hot = self.colors['red']
        
        # Map temperature to color
        if temperature < -10:
            temp_color = freezing
        elif temperature < 0:
            temp_color = cold
        elif temperature < 15:
            temp_color = cool
        elif temperature < 25:
            temp_color = warm
        else:
            temp_color = hot
        
        # Create a visual bar, scaled from -30° to +40°
        bar_width = 20
        scale_range = 70  # -30 to +40 = 70 degrees
        
        # Calculate position on the bar (clamp between -30 and +40)
        clamped_temp = max(-30, min(40, temperature))
        position = int(((clamped_temp + 30) / scale_range) * bar_width)
        
        # Construct the bar
        bar = [" "] * bar_width
        bar[position] = "█"
        
        # Format the bar with colors for different temperature ranges
        bar_str = ""
        cold_end = int(bar_width * 0.3)  # -30 to -5
        cool_end = int(bar_width * 0.5)  # -5 to 10
        warm_end = int(bar_width * 0.7)  # 10 to 25
        
        # Color the bar sections
        for i in range(bar_width):
            if i < cold_end:
                bar_str += f"{freezing}{bar[i]}"
            elif i < cool_end:
                bar_str += f"{cold}{bar[i]}"
            elif i < warm_end:
                bar_str += f"{cool}{bar[i]}"
            elif i < bar_width:
                bar_str += f"{hot}{bar[i]}"
        
        # Add reset code at the end
        bar_str += self.colors['reset']
        
        # Return the formatted string with the value
        return f"Temperature: {temp_color}{temperature}°C{self.colors['reset']} [{bar_str}]"
    
    def get_weather_effect_indicator(self, effect_name, effect_value):
        """Get a visual indicator for a specific weather effect on gameplay.
        
        Args:
            effect_name (str): Name of the effect
            effect_value (float or int): Value of the effect
            
        Returns:
            str: String representing the effect visually
        """
        if not self.use_colors:
            return f"{effect_name.replace('_', ' ').title()}: {effect_value}"
            
        # Format the name
        name = effect_name.replace('_', ' ').title()
        
        # Determine if this is a positive, neutral, or negative effect
        if effect_name in ["health_mod", "energy_mod"]:
            # Health and energy modifiers
            if effect_value < 0:
                color = self.colors["red"]
                indicator = f"▼ {abs(effect_value)}"
            elif effect_value > 0:
                color = self.colors["green"]
                indicator = f"▲ +{effect_value}"
            else:
                color = self.colors["white"]
                indicator = "◆ 0"
        elif effect_name == "shelter_importance":
            # Shelter importance
            if effect_value > 2.0:
                color = self.colors["red"]
                indicator = f"▲▲ {effect_value}x"
            elif effect_value > 1.0:
                color = self.colors["yellow"]
                indicator = f"▲ {effect_value}x"
            else:
                color = self.colors["green"]
                indicator = f"◆ {effect_value}x"
        else:
            # Default visualization
            if effect_value > 1.0:
                color = self.colors["yellow"]
                indicator = f"▲ {effect_value}x"
            elif effect_value < 1.0:
                color = self.colors["green"]
                indicator = f"▼ {effect_value}x"
            else:
                color = self.colors["white"]
                indicator = f"◆ {effect_value}x"
                
        return f"{name}: {color}{indicator}{self.colors['reset']}"