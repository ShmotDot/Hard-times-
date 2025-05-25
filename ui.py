"""
UI module for Hard Times: Ottawa.
Handles text-based interface, formatting, and display functions.
"""
import os
import sys
import time

from game.weather_visuals import WeatherVisuals

class UI:
    """Handles display and formatting of game text."""

    def __init__(self):
        """Initialize the UI with default settings."""
        # Check if terminal actually supports ANSI color codes
        self.use_colors = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

        # Maximum size for feedback log to prevent memory leaks
        self.MAX_LOG_ENTRIES = 10
        self._cleanup_feedback_log()

        # Define ANSI color codes
        self.colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "underline": "\033[4m",
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "gray": "\033[90m"
        }

        # Terminal width (default to 80 for consistency)
        self.width = 80  # Fixed width to avoid issues with terminal size detection
        
        # Store feedback and stats
        self.feedback_log = []  # Store recent feedback messages
        self.previous_stats = {}  # Store previous stat values
        self.MAX_LOG_ENTRIES = 5  # Number of recent messages to show

    def display_title(self, title):
        """Display a formatted title with border.

        Args:
            title (str): The title to display
        """
        width = min(self.width, 80)
        padding = (width - len(title) - 4) // 2
        if self.use_colors:
            border = f"{self.colors['cyan']}{'═' * width}{self.colors['reset']}"
            print(f"\n{border}")
            print(f"{self.colors['cyan']}║{' ' * padding}{self.colors['bold']}{self.colors['white']}{title}{' ' * (width - len(title) - padding - 2)}║{self.colors['reset']}")
            print(border)
        else:
            border = '═' * width
            print(f"\n{border}")
            print(f"║{' ' * padding}{title}{' ' * (width - len(title) - padding - 2)}║")
            print(border)

    def display_subtitle(self, subtitle):
        """Display a formatted subtitle.

        Args:
            subtitle (str): The subtitle to display
        """
        if self.use_colors:
            print(f"\n{self.colors['bold']}{self.colors['yellow']}{subtitle}{self.colors['reset']}")
        else:
            print(f"\n{subtitle}")

    def display_text(self, text, color=None):
        """Display text, optionally with color.

        Args:
            text (str): The text to display
            color (str, optional): Color name to use
        """
        if self.use_colors and color is not None and color in self.colors:
            print(f"{self.colors[color]}{text}{self.colors['reset']}")
        else:
            print(text)

    def display_divider(self):
        """Display a horizontal divider line."""
        line_width = min(self.width, 80)  # Cap at 80 chars
        print("\n" + "-" * line_width)

    def _animate_loading(self, message="Loading", duration=1.0):
        """Display an animated loading message.

        Args:
            message (str): Base message to display
            duration (float): Animation duration in seconds
        """
        frames = [".  ", ".. ", "..."]
        for _ in range(int(duration * 3)):
            for frame in frames:
                sys.stdout.write(f"\r{message}{frame}")
                sys.stdout.flush()
                time.sleep(0.1)
        print()

    def _get_status_color(self, value):
        """Get color based on status value with smooth transitions.

        Args:
            value (int): Status value 0-100
        """
        if value > 60:
            return self.colors["green"]
        elif value > 30:
            return self.colors["yellow"]
        return self.colors["red"]

    # Second __init__ function removed and merged into the first one

    def _cleanup_feedback_log(self):
        """Clean up old feedback messages to prevent memory leaks."""
        if hasattr(self, 'feedback_log'):
            while len(self.feedback_log) > self.MAX_LOG_ENTRIES:
                self.feedback_log.pop(0)
        else:
            self.feedback_log = []

    def add_feedback(self, message, category="info"):
        """Add a feedback message to the log.
        
        Args:
            message (str): The feedback message
            category (str): Message category (info, warning, success)
        """
        if not hasattr(self, 'feedback_log'):
            self.feedback_log = []
        self.feedback_log.append({"message": message, "category": category})
        self._cleanup_feedback_log()

    def display_status(self, player, time_system, show_daily_summary=False):
        """Display the player's status and game time with enhanced visuals.
        
        Args:
            player (Player): The player object
            time_system (TimeSystem): The time system object
            show_daily_summary (bool): Whether to show the daily summary

        Args:
            player (Player): The player object
            time_system (TimeSystem): The time system object
        """
        self.clear_screen()
        self._animate_loading("Updating status", 0.3)

        # Initialize weather visuals
        weather_visuals = WeatherVisuals(self.use_colors)

        # Create utility function for bars
        def create_bar(value, max_value=100, width=20, reverse=False):
            """Create a visual progress bar with color coding.

            Args:
                value (int): Current value
                max_value (int): Maximum possible value
                width (int): Width of the bar in characters
                reverse (bool): If True, higher values are worse (e.g., for hunger)
            """
            filled = int((value / max_value) * width)
            if self.use_colors:
                if reverse:
                    # For stats where higher is worse (e.g., hunger)
                    if value < 30:
                        color = self.colors['green']
                    elif value < 70:
                        color = self.colors['yellow']
                    else:
                        color = self.colors['red']
                else:
                    # For stats where higher is better (e.g., health)
                    if value > 60:
                        color = self.colors['green']
                    elif value > 30:
                        color = self.colors['yellow']
                    else:
                        color = self.colors['red']

                # Use different fill characters for better visual distinction
                return f"{color}{'█' * filled}{'░' * (width - filled)}{self.colors['reset']}"
            else:
                return f"{'#' * filled}{'-' * (width - filled)}"

        # Get weather effects
        weather_effects = time_system.get_weather_effects()
        weather_type = time_system.weather
        temperature = time_system.temperature
        is_harsh = time_system.is_harsh_weather()

        # Create a more decorative header with day count and time
        day_count = time_system.get_day()
        time_str = time_system.get_time_string()
        period = time_system.get_period().title()

        # Create a fancy day/time header
        if self.use_colors:
            day_header = f"{self.colors['cyan']}╔═══════════════════════════════════════════════════════╗{self.colors['reset']}"
            day_title = f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}Day {day_count} | {time_str} | {period}{' ' * (40 - len(str(day_count)) - len(time_str) - len(period))} ║{self.colors['reset']}"
            day_footer = f"{self.colors['cyan']}╚═══════════════════════════════════════════════════════╝{self.colors['reset']}"
            print(f"\n{day_header}\n{day_title}\n{day_footer}")
        else:
            print(f"\n=== Day {day_count} | {time_str} | {period} ===")

        # Display dynamic weather banner with cool visuals
        print(weather_visuals.get_weather_banner(weather_type, temperature, is_harsh))
        
        # Show daily summary if requested
        if show_daily_summary:
            daily_summary = DailySummary(self)
            daily_summary.display(player, time_system)

        # Display temperature bar with gradient
        print(weather_visuals.get_temperature_bar(temperature))

        # Display key weather effects with visual indicators in a more compact format
        effects_list = []
        for effect_name, effect_value in weather_effects.items():
            if effect_name not in ['description', 'event_modifiers']:
                effects_list.append(weather_visuals.get_weather_effect_indicator(effect_name, effect_value))

        if effects_list:
            print(f"\n{self.colors['bold']}Weather Effects:{self.colors['reset']} " + " | ".join(effects_list))

        # Create a fancy status panel with visual bars
        print(f"\n{self.colors['cyan']}╔═══════════════════════════════════════════════════════╗{self.colors['reset']}")
        print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}STATUS{' ' * 45}║{self.colors['reset']}")
        print(f"{self.colors['cyan']}╠═══════════════════════════════════════════════════════╣{self.colors['reset']}")

        # Display status bars with icons and values
        bar_width = 25

        # Health with heart icon
        health_bar = create_bar(player.health, 100, bar_width)
        health_icon = "♥" if self.use_colors else "HP"
        health_color = "green" if player.health > 60 else "yellow" if player.health > 30 else "red"
        print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors[health_color]}{health_icon}{self.colors['reset']} Health:    {health_bar} {player.health:3}/100 {self.colors['cyan']}║{self.colors['reset']}")

        # Satiety/Fullness with food icon (higher is better)
        satiety_bar = create_bar(player.satiety, 100, bar_width)
        satiety_icon = "🍽" if self.use_colors else "ST"
        satiety_color = "green" if player.satiety > 60 else "yellow" if player.satiety > 30 else "red"
        print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors[satiety_color]}{satiety_icon}{self.colors['reset']} Satiety:   {satiety_bar} {player.satiety:3}/100 {self.colors['cyan']}║{self.colors['reset']}")

        # Energy with lightning bolt icon
        energy_bar = create_bar(player.energy, 100, bar_width)
        energy_icon = "⚡" if self.use_colors else "EN"
        energy_color = "green" if player.energy > 60 else "yellow" if player.energy > 30 else "red"
        print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors[energy_color]}{energy_icon}{self.colors['reset']} Energy:    {energy_bar} {player.energy:3}/100 {self.colors['cyan']}║{self.colors['reset']}")

        # Mental with brain icon
        mental_bar = create_bar(player.mental, 100, bar_width)
        mental_icon = "🧠" if self.use_colors else "MT"
        mental_color = "green" if player.mental > 60 else "yellow" if player.mental > 30 else "red"
        print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors[mental_color]}{mental_icon}{self.colors['reset']} Mental:    {mental_bar} {player.mental:3}/100 {self.colors['cyan']}║{self.colors['reset']}")

        # Hygiene with shower icon
        hygiene_bar = create_bar(player.hygiene, 100, bar_width)
        hygiene_icon = "🚿" if self.use_colors else "HY"
        hygiene_color = "green" if player.hygiene > 60 else "yellow" if player.hygiene > 30 else "red"
        print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors[hygiene_color]}{hygiene_icon}{self.colors['reset']} Hygiene:   {hygiene_bar} {player.hygiene:3}/100 {self.colors['cyan']}║{self.colors['reset']}")

        # Money with dollar icon
        money_str = f"${player.money:.2f}"
        money_padding = ' ' * (bar_width + 8 - len(money_str))
        print(f"{self.colors['cyan']}║ {self.colors['bold']}${self.colors['reset']} Money:     {self.colors['green']}{money_str}{self.colors['reset']}{money_padding} {self.colors['cyan']}║{self.colors['reset']}")

        # Progress indicators for job and housing (if applicable)
        if player.job_prospects > 0 or player.housing_prospects > 0:
            print(f"{self.colors['cyan']}╠═══════════════════════════════════════════════════════╣{self.colors['reset']}")
            print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}PROSPECTS{' ' * 42}║{self.colors['reset']}")

            if player.job_prospects > 0:
                job_bar = create_bar(player.job_prospects, 100, bar_width)
                print(f"{self.colors['cyan']}║ {self.colors['bold']}⚒{self.colors['reset']} Job:       {job_bar} {player.job_prospects:3}/100 {self.colors['cyan']}║{self.colors['reset']}")

            if player.housing_prospects > 0:
                house_bar = create_bar(player.housing_prospects, 100, bar_width)
                print(f"{self.colors['cyan']}║ {self.colors['bold']}⌂{self.colors['reset']} Housing:   {house_bar} {player.housing_prospects:3}/100 {self.colors['cyan']}║{self.colors['reset']}")

        # Skills section (if skills are tracked)
        if hasattr(player, 'skills') and player.skills:
            print(f"{self.colors['cyan']}╠═══════════════════════════════════════════════════════╣{self.colors['reset']}")
            print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}SKILLS{' ' * 44}║{self.colors['reset']}")

            # Show top skills (limit to 3 to save space)
            skills_shown = 0
            for skill_name, skill_level in sorted(player.skills.items(), key=lambda x: x[1], reverse=True):
                if skills_shown >= 3:
                    break
                skill_bar = create_bar(skill_level, 10, bar_width)
                skill_display = skill_name.replace('_', ' ').title()
                # Truncate long skill names
                if len(skill_display) > 10:
                    skill_display = skill_display[:9] + "."
                print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['yellow']}•{self.colors['reset']} {skill_display}:{' ' * (10-len(skill_display))} {skill_bar} {skill_level}/10 {self.colors['cyan']}║{self.colors['reset']}")
                skills_shown += 1

        # Bottom of status panel
        print(f"{self.colors['cyan']}╚═══════════════════════════════════════════════════════╝{self.colors['reset']}")

        # Display recent feedback messages
        if self.feedback_log:
            print(f"\n{self.colors['bold']}Recent Events:{self.colors['reset']}")
            for entry in self.feedback_log:
                if entry["category"] == "success":
                    print(f"✓ {self.colors['green']}{entry['message']}{self.colors['reset']}")
                elif entry["category"] == "warning":
                    print(f"! {self.colors['yellow']}{entry['message']}{self.colors['reset']}")
                else:
                    print(f"• {self.colors['white']}{entry['message']}{self.colors['reset']}")

        # Display weather-specific warnings if conditions are harsh
        if is_harsh:
            print(f"\n{self.colors['bold']}⚠ WEATHER WARNING ⚠{self.colors['reset']}")
            if not player.unlocked_abilities.get("cold_resistance", False) and temperature < -10:
                print(f"{self.colors['red']}Freezing conditions! You need proper shelter or clothing.{self.colors['reset']}")
            elif weather_type == "storm":
                print(f"{self.colors['red']}Dangerous storm conditions! Seek shelter immediately.{self.colors['reset']}")
            elif weather_type == "snow" and temperature < -5:
                print(f"{self.colors['yellow']}Heavy snow and cold temperatures. Shelter is important.{self.colors['reset']}")
            elif weather_type == "rain" and temperature < 5:
                print(f"{self.colors['yellow']}Cold rain can cause hypothermia. Stay dry.{self.colors['reset']}")

        # Status effects section if applicable
        if hasattr(player, 'status_effects') and player.status_effects:
            print(f"\n{self.colors['bold']}Active Status Effects:{self.colors['reset']}")
            for effect, duration in player.status_effects.items():
                effect_name = effect.replace('_', ' ').title()
                if 'illness' in effect.lower() or 'injury' in effect.lower():
                    print(f"• {self.colors['red']}{effect_name} ({duration} hrs){self.colors['reset']}")
                elif 'buff' in effect.lower() or 'boost' in effect.lower():
                    print(f"• {self.colors['green']}{effect_name} ({duration} hrs){self.colors['reset']}")
                else:
                    print(f"• {self.colors['yellow']}{effect_name} ({duration} hrs){self.colors['reset']}")

        # Non-colored version (fallback)
        if not self.use_colors:
            print(f"\n=== Day {time_system.get_day()} | {time_system.get_time_string()} | {time_system.get_period().title()} ===")
            print(f"Weather: {time_system.weather.title()}, {time_system.temperature}°C - {weather_effects['description']}")

            print("\n=== Status ===")
            print(f"Health: {player.health}/100")
            print(f"Satiety: {player.satiety}/100")
            print(f"Energy: {player.energy}/100")
            print(f"Mental: {player.mental}/100")
            print(f"Hygiene: {player.hygiene}/100")
            print(f"Money: ${player.money:.2f}")

            if player.job_prospects > 0:
                print(f"Job Prospects: {player.job_prospects}/100")
            if player.housing_prospects > 0:
                print(f"Housing Prospects: {player.housing_prospects}/100")

    def display_location(self, location, location_effects=None, time_system=None):
        """Display information about the current location with enhanced visuals.

        Args:
            location (Location): The current location object
            location_effects (dict, optional): Dictionary of effects for this location
            time_system (TimeSystem, optional): Current time system for weather display
        """
        # Initialize weather visuals for outdoor locations
        weather_visuals = WeatherVisuals(self.use_colors)

        if self.use_colors:
            # Create a fancy boxed location header
            location_name = location.name
            header_width = 51  # Match the status box width for consistency

            # Create a colorful location banner
            banner_color = "magenta"
            if hasattr(location, 'type') and location.type:
                loc_type = location.type.lower()
                if "downtown" in loc_type:
                    banner_color = "red"
                elif "residential" in loc_type:
                    banner_color = "green"
                elif "industrial" in loc_type:
                    banner_color = "yellow"
                elif "park" in loc_type or "nature" in loc_type:
                    banner_color = "green"
                elif "commercial" in loc_type or "market" in loc_type:
                    banner_color = "cyan"
                elif "waterfront" in loc_type or "river" in loc_type:
                    banner_color = "blue"

            # Create the location header box
            print(f"\n{self.colors[banner_color]}╔═══════════════════════════════════════════════════════╗{self.colors['reset']}")

            # Create padded title that's centered
            padding = (header_width - len(location_name) - 4) // 2
            title_str = f"{self.colors[banner_color]}║{' ' * padding}{self.colors['bold']}{self.colors['white']}{location_name}{self.colors['reset']}{self.colors[banner_color]}{' ' * (header_width - len(location_name) - padding - 2)}║{self.colors['reset']}"
            print(title_str)

            # Safety level indicator in the header
            safety_text = ""
            if location.danger_level <= 3:
                safety_text = f"{self.colors['green']}Safe Area{self.colors['reset']}"
            elif location.danger_level <= 6:
                safety_text = f"{self.colors['yellow']}Moderate Risk{self.colors['reset']}"
            else:
                safety_text = f"{self.colors['red']}Dangerous Zone{self.colors['reset']}"

            padding = (header_width - len("Safety Level: ") - len(safety_text.replace(self.colors['green'], "").replace(self.colors['yellow'], "").replace(self.colors['red'], "").replace(self.colors['reset'], "")) - 2) // 2
            safety_str = f"{self.colors[banner_color]}║{' ' * padding}Safety Level: {safety_text}{' ' * (header_width - len('Safety Level: ') - len(safety_text.replace(self.colors['green'], '').replace(self.colors['yellow'], '').replace(self.colors['red'], '').replace(self.colors['reset'], '')) - padding - 2)}║{self.colors['reset']}"
            print(safety_str)

            # Bottom border of the header
            print(f"{self.colors[banner_color]}╚═══════════════════════════════════════════════════════╝{self.colors['reset']}")

            # Display location description with nicer formatting
            description_lines = self._wrap_text(location.description, 70)
            for line in description_lines:
                print(f"  {line}")

            # Create a visual divider
            print(f"\n{self.colors['cyan']}──────────────────────────────────────────────────────────{self.colors['reset']}")

            # Display weather conditions more visually for outdoor locations
            if time_system and hasattr(location, 'is_outdoor') and location.is_outdoor:
                weather_icon = weather_visuals.get_weather_icon(time_system.weather, time_system.temperature)

                # Create a compact weather info panel
                print(f"{self.colors['bold']}Weather Impact:{self.colors['reset']}")
                print(f"{weather_icon} {time_system.weather.title()}, {time_system.temperature}°C" + 
                      (f" ({self.colors['red']}Hazardous{self.colors['reset']})" if time_system.is_harsh_weather() else ""))

                # Show additional weather warnings for outdoor locations with icons
                if time_system.is_harsh_weather():
                    print(f"{self.colors['yellow']}⚠ Weather Hazard:{self.colors['reset']}")
                    if time_system.weather == "storm":
                        print(f"  {self.colors['red']}❗ Exposed to storm! Find shelter immediately!{self.colors['reset']}")
                    elif time_system.weather == "snow" and time_system.temperature < -10:
                        print(f"  {self.colors['red']}❄ Dangerously cold! Seek warmth!{self.colors['reset']}")
                    elif time_system.weather == "rain" and time_system.temperature < 5:
                        print(f"  {self.colors['yellow']}☂ Cold rain - risk of hypothermia{self.colors['reset']}")
                    elif time_system.temperature < -15:
                        print(f"  {self.colors['red']}❄ Extreme cold! Risk of frostbite!{self.colors['reset']}")

                print(f"{self.colors['cyan']}──────────────────────────────────────────────────────────{self.colors['reset']}")

            # Display location effects in a more visually appealing format
            if location_effects:
                print(f"{self.colors['bold']}Current Conditions:{self.colors['reset']}")

                # Display safety level
                if 'safety' in location_effects:
                    print(f"  • {self.colors['red']}Safety:{self.colors['reset']} {location_effects['safety']}")

                # Display description if available
                if 'description' in location_effects:
                    effect_lines = self._wrap_text(location_effects['description'], 60)
                    for line in effect_lines:
                        print(f"  • {line}")

                print(f"{self.colors['cyan']}──────────────────────────────────────────────────────────{self.colors['reset']}")

            # Display available services with opening hours and icons
            if location.services:
                print(f"{self.colors['bold']}Available Services:{self.colors['reset']}")

                for service in location.services:
                    # Add icons based on service type
                    service_icon = "•"
                    service_name = service['name'].lower()
                    if "shelter" in service_name:
                        service_icon = "⌂"
                    elif "food" in service_name or "meal" in service_name:
                        service_icon = "🍲"
                    elif "medical" in service_name or "health" in service_name:
                        service_icon = "+"
                    elif "job" in service_name or "employ" in service_name:
                        service_icon = "⚒"
                    elif "library" in service_name:
                        service_icon = "📚"

                    # Determine if service is open based on hours
                    hours = service.get('hours', 'Unknown')

                    # Wrap description for better formatting
                    description = service.get('description', '')
                    desc_lines = self._wrap_text(description, 50)

                    print(f"  {self.colors['green']}{service_icon}{self.colors['reset']} {self.colors['bold']}{service['name']}{self.colors['reset']} ({hours})")
                    for line in desc_lines:
                        print(f"     {line}")

                print(f"{self.colors['cyan']}──────────────────────────────────────────────────────────{self.colors['reset']}")

            # Display available exits/destinations with travel time
            if hasattr(location, 'connections') and location.connections:
                print(f"{self.colors['bold']}Connected Areas:{self.colors['reset']}")

                for connection in location.connections:
                    dest_name = connection.get('name', 'Unknown')
                    travel_time = connection.get('travel_time', 1)

                    # Add fancy arrow and time indicators
                    time_color = "green" if travel_time <= 1 else "yellow" if travel_time <= 3 else "red"
                    time_str = f"{travel_time} hour{'s' if travel_time > 1 else ''}"

                    print(f"  {self.colors['magenta']}→{self.colors['reset']} {dest_name} ({self.colors[time_color]}{time_str}{self.colors['reset']} away)")
        else:
            # Non-colored version
            print(f"\n=== {location.name} ===")
            print(location.description)

            # Safety level indicator
            if location.danger_level <= 3:
                safety = "Safe"
            elif location.danger_level <= 6:
                safety = "Moderate Risk"
            else:
                safety = "Dangerous"

            print(f"Safety Level: {safety}")

            # Basic weather for outdoor locations
            if time_system and hasattr(location, 'is_outdoor') and location.is_outdoor:
                print(f"\nWeather: {time_system.weather.title()}, {time_system.temperature}°C")
                if time_system.is_harsh_weather():
                    print("WARNING: Harsh weather conditions!")

            # Display location effects if provided
            if location_effects:
                print("\nCurrent Conditions:")
                for effect_type, effect in location_effects.items():
                    if effect_type == 'description':
                        print(f"  • {effect}")
                    elif effect_type != 'modifiers':  # Skip displaying raw modifiers
                        print(f"  • {effect_type.replace('_', ' ').title()}: {effect}")

            # Available services
            if location.services:
                print("\nAvailable Services:")
                for service in location.services:
                    print(f"• {service['name']} ({service['hours']})")
                    print(f"  {service['description']}")

            # Available exits/destinations
            if hasattr(location, 'connections') and location.connections:
                print("\nConnected Areas:")
                for connection in location.connections:
                    dest_name = connection.get('name', 'Unknown')
                    travel_time = connection.get('travel_time', 1)
                    print(f"• {dest_name} ({travel_time} hour{'s' if travel_time > 1 else ''} away)")

    def _wrap_text(self, text, width):
        """Wrap text to fit within specified width.

        Args:
            text (str): Text to wrap
            width (int): Maximum line width

        Returns:
            list: List of wrapped lines
        """
        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split()
            if not words:
                lines.append('')
                continue

            current_line = words[0]
            for word in words[1:]:
                if len(current_line) + len(word) + 1 <= width:
                    current_line += ' ' + word
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)
        return lines

    def display_error(self, message):
        """Display an error message.

        Args:
            message (str): The error message to display
        """
        if self.use_colors:
            print(f"{self.colors['red']}Error: {message}{self.colors['reset']}")
        else:
            print(f"Error: {message}")

    def display_success(self, message):
        """Display a success message.

        Args:
            message (str): The success message to display
        """
        if self.use_colors:
            print(f"{self.colors['green']}{message}{self.colors['reset']}")
        else:
            print(f"Success: {message}")

    def display_success(self, message):
        """Display a success message.

        Args:
            message (str): The success message to display
        """
        if self.use_colors:
            print(f"{self.colors['green']}{message}{self.colors['reset']}")
        else:
            print(f"Success: {message}")

    def display_warning(self, message):
        """Display a warning message.

        Args:
            message (str): The warning message to display
        """
        if self.use_colors:
            print(f"{self.colors['yellow']}{message}{self.colors['reset']}")
        else:
            print(f"Warning: {message}")

    def display_inventory(self, inventory, money):
        """Display the player's inventory and money with enhanced visuals and categorization.

        Args:
            inventory (Inventory): Player's inventory object
            money (float): Player's money
        """
        if self.use_colors:
            # Create a fancy inventory title banner
            print(f"\n{self.colors['cyan']}╔═══════════════════════════════════════════════════════╗{self.colors['reset']}")
            print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}INVENTORY{' ' * 42}║{self.colors['reset']}")
            print(f"{self.colors['cyan']}╚═══════════════════════════════════════════════════════╝{self.colors['reset']}")
        else:
            self.display_title("Inventory")

        if not inventory.items:
            self.display_text("Your inventory is empty.")
            self.display_subtitle("Money")
            self.display_text(f"${money:.2f}")
            return

        # Calculate total inventory weight
        total_weight = sum(item.weight * inventory.quantities.get(item_id, 0) 
                          for item_id, item in inventory.items.items())

        # Group items by category for better organization
        categories = {}
        for item_id, item in inventory.items.items():
            category = "Miscellaneous"
            if hasattr(item, 'category'):
                category = item.category

            if category not in categories:
                categories[category] = []

            categories[category].append((item_id, item))

        # Display inventory summary with weight
        if self.use_colors:
            print(f"{self.colors['bold']}Summary:{self.colors['reset']} {len(inventory.items)} items, Total Weight: {self.colors['yellow']}{total_weight:.1f}kg{self.colors['reset']}")
            print(f"{self.colors['bold']}Money:{self.colors['reset']} {self.colors['green']}${money:.2f}{self.colors['reset']}")
            print(f"{self.colors['cyan']}──────────────────────────────────────────────────────────{self.colors['reset']}")
        else:
            print(f"Summary: {len(inventory.items)} items, Total Weight: {total_weight:.1f}kg")
            print(f"Money: ${money:.2f}")
            print("─" * 40)

        # Display items grouped by category
        for category, items in sorted(categories.items()):
            if self.use_colors:
                # Create category headers with colors based on category type
                category_color = "white"
                if category.lower() in ["food", "consumable", "drink"]:
                    category_color = "green"
                elif category.lower() in ["medicine", "medical", "health"]:
                    category_color ="cyan"
                elif category.lower() in ["weapon", "tool", "gear"]:
                    category_color = "yellow"
                elif category.lower() in ["clothing", "shelter"]:
                    category_color = "blue"
                elif category.lower() in ["valuable", "currency"]:
                    category_color = "magenta"

                print(f"{self.colors['bold']}{self.colors[category_color]}■ {category.upper()}{self.colors['reset']}")
            else:
                print(f"\n=== {category.upper()} ===")

            # Sort items by name within category
            items.sort(key=lambda x: x[1].name)

            # Display items with more appealing formatting
            for item_id, item in items:
                quantity = inventory.quantities.get(item_id, 0)
                quality_color = None

                # Skip displaying items with 0 quantity
                if quantity <= 0:
                    continue

                # Determine item quality for color coding
                if hasattr(item, 'quality'):
                    if item.quality.value == "excellent":
                        quality_color = "cyan"
                    elif item.quality.value == "good":
                        quality_color = "green"
                    elif item.quality.value == "poor":
                        quality_color = "red"

                # Create item quality indicator
                quality_text = ""
                if hasattr(item, 'quality'):
                    quality_value = item.quality.value.title()
                    if self.use_colors:
                        if quality_color:
                            quality_text = f" ({self.colors[quality_color]}{quality_value}{self.colors['reset']})"
                    else:
                        quality_text = f" ({quality_value})"

                # Display item name, quality and quantity
                item_name = item.name
                if self.use_colors:
                    # Make quantities stand out
                    qty_str = f"{self.colors['bold']}{self.colors['yellow']}×{quantity}{self.colors['reset']}"

                    if quality_color:
                        print(f"  {self.colors[quality_color]}• {item_name}{self.colors['reset']}{quality_text} {qty_str}")
                    else:
                        print(f"  {self.colors['white']}• {item_name}{self.colors['reset']}{quality_text} {qty_str}")
                else:
                    print(f"  • {item_name}{quality_text} ×{quantity}")

                # Show weight and value with more visual appeal
                if hasattr(item, 'weight') and hasattr(item, 'value'):
                    total_item_weight = item.weight * quantity
                    total_item_value = item.value * quantity

                    if self.use_colors:
                        print(f"    {self.colors['gray']}Weight: {total_item_weight:.1f}kg ({item.weight:.1f}kg each) | " +
                              f"Value: ${total_item_value:.2f} (${item.value:.2f} each){self.colors['reset']}")
                    else:
                        print(f"    Weight: {total_item_weight:.1f}kg ({item.weight:.1f}kg each) | " +
                              f"Value: ${total_item_value:.2f} (${item.value:.2f} each)")

                # Display item effects if applicable
                if hasattr(item, 'effects') and item.effects:
                    if self.use_colors:
                        print(f"    {self.colors['cyan']}Effects:{self.colors['reset']}")
                        for effect_type, value in item.effects.items():
                            effect_name = effect_type.replace('_', ' ').title()
                            effect_color = "green" if value > 0 else "red"
                            sign = "+" if value > 0 else ""
                            print(f"      {self.colors[effect_color]}{effect_name}: {sign}{value}{self.colors['reset']}")
                    else:
                        print("    Effects:")
                        for effect_type, value in item.effects.items():
                            effect_name = effect_type.replace('_', ' ').title()
                            sign = "+" if value > 0 else ""
                            print(f"      {effect_name}: {sign}{value}")

                # Show brief description with text wrapping for better readability
                if hasattr(item, 'description') and item.description:
                    # Wrap description text
                    desc_lines = self._wrap_text(item.description, 60)
                    if self.use_colors:
                        for i, line in enumerate(desc_lines):
                            if i == 0:
                                print(f"    {self.colors['gray']}Description: {line}{self.colors['reset']}")
                            else:
                                print(f"                {self.colors['gray']}{line}{self.colors['reset']}")
                    else:
                        for i, line in enumerate(desc_lines):
                            if i == 0:
                                print(f"    Description: {line}")
                            else:
                                print(f"                {line}")

                # Add a small separator between items
                print()

        # Show capacity info if applicable
        if hasattr(inventory, 'capacity') and inventory.capacity > 0:
            capacity_pct = (total_weight / inventory.capacity) * 100
            capacity_bar_width = 30
            filled_width = int((total_weight / inventory.capacity) * capacity_bar_width)

            if self.use_colors:
                # Color based on how full the inventory is
                capacity_color = "green"
                if capacity_pct > 80:
                    capacity_color = "red"
                elif capacity_pct > 60:
                    capacity_color = "yellow"

                bar = self.colors[capacity_color] + "■" * filled_width + self.colors['gray'] + "□" * (capacity_bar_width - filled_width) + self.colors['reset']
                print(f"{self.colors['cyan']}──────────────────────────────────────────────────────────{self.colors['reset']}")
                print(f"{self.colors['bold']}Capacity:{self.colors['reset']} {bar} {total_weight:.1f}/{inventory.capacity}kg ({capacity_pct:.0f}%)")
            else:
                bar = "#" * filled_width + "-" * (capacity_bar_width - filled_width)
                print("─" * 40)
                print(f"Capacity: [{bar}] {total_weight:.1f}/{inventory.capacity}kg ({capacity_pct:.0f}%)")

    def display_skills(self, skills):
        """Display the player's skills with enhanced visual formatting.

        Args:
            skills (dict): Player's skills and levels
        """
        if self.use_colors:
            # Create a fancy skills title banner
            print(f"\n{self.colors['cyan']}╔═══════════════════════════════════════════════════════╗{self.colors['reset']}")
            print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}SKILLS AND ABILITIES{' ' * 32}║{self.colors['reset']}")
            print(f"{self.colors['cyan']}╚═══════════════════════════════════════════════════════╝{self.colors['reset']}")
        else:
            self.display_title("Skills")

        # Group skills by category if possible
        skill_categories = {
            "survival": [],
            "social": [],
            "technical": [],
            "mental": [],
            "physical": []
        }

        # Categorize skills (with sensible defaults for skills without explicit categories)
        for skill_name, level in skills.items():
            if "survival" in skill_name or "craft" in skill_name or "forage" in skill_name:
                skill_categories["survival"].append((skill_name, level))
            elif "speech" in skill_name or "charisma" in skill_name or "barter" in skill_name or "negotiate" in skill_name:
                skill_categories["social"].append((skill_name, level))
            elif "repair" in skill_name or "tech" in skill_name or "electronics" in skill_name:
                skill_categories["technical"].append((skill_name, level))
            elif "mental" in skill_name or "focus" in skill_name or "knowledge" in skill_name:
                skill_categories["mental"].append((skill_name, level))
            elif "strength" in skill_name or "agility" in skill_name or "endurance" in skill_name:
                skill_categories["physical"].append((skill_name, level))
            else:
                # Default categorization based on skill name
                if "talk" in skill_name or "persuade" in skill_name:
                    skill_categories["social"].append((skill_name, level))
                elif "find" in skill_name or "scavenge" in skill_name:
                    skill_categories["survival"].append((skill_name, level))
                elif "fix" in skill_name or "make" in skill_name:
                    skill_categories["technical"].append((skill_name, level))
                elif "resist" in skill_name or "health" in skill_name:
                    skill_categories["physical"].append((skill_name, level))
                else:
                    # Default to survival for uncategorized skills
                    skill_categories["survival"].append((skill_name, level))

        # Display skills by category
        for category, category_skills in skill_categories.items():
            if not category_skills:
                continue

            # Sort skills by level (descending)
            category_skills.sort(key=lambda x: x[1], reverse=True)

            # Display category header
            if self.use_colors:
                # Color code different skill categories
                category_color = "white"
                if category == "survival":
                    category_color = "green"
                elif category == "social":
                    category_color = "yellow"
                elif category == "technical":
                    category_color = "cyan"
                elif category == "mental":
                    category_color = "magenta"
                elif category == "physical":
                    category_color = "red"

                print(f"\n{self.colors['bold']}{self.colors[category_color]}■ {category.upper()} SKILLS{self.colors['reset']}")
            else:
                print(f"\n=== {category.upper()} SKILLS ===")

            # Display skills with enhanced bars and formatting
            for skill_name, level in category_skills:
                # Format skill name with spaces and capitalization
                display_name = skill_name.replace('_', ' ').title()

                # Determine color based on level
                level_color = "red"
                if level >= 8:
                    level_color = "cyan"  # Expert
                elif level >= 5:
                    level_color = "green"  # Proficient
                elif level >= 3:
                    level_color = "yellow"  # Novice

                # Create descriptive level text
                level_text = "Novice"
                if level >= 9:
                    level_text = "Master"
                elif level >= 7:
                    level_text = "Expert"
                elif level >= 5:
                    level_text = "Proficient"
                elif level >= 3:
                    level_text = "Apprentice"
                elif level >= 1:
                    level_text = "Beginner"

                # Display skill with enhanced bar
                if self.use_colors:
                    # Create a more visually interesting bar with color gradient
                    bar = ""
                    for i in range(10):
                        if i < level:
                            if i < 3:
                                bar += f"{self.colors['red']}■{self.colors['reset']}"
                            elif i < 6:
                                bar += f"{self.colors['yellow']}■{self.colors['reset']}"
                            elif i < 9:
                                bar += f"{self.colors['green']}■{self.colors['reset']}"
                            else:
                                bar += f"{self.colors['cyan']}■{self.colors['reset']}"
                        else:
                            bar += f"{self.colors['gray']}□{self.colors['reset']}"

                    # Format the skill display with right-aligned level text
                    name_width = 15  # Fixed width for alignment
                    name_display = display_name[:name_width].ljust(name_width)
                    print(f"  {name_display} {bar} {self.colors[level_color]}{level_text}{self.colors['reset']} ({level}/10)")
                else:
                    bar = "#" * level + "-" * (10 - level)
                    print(f"  {display_name.ljust(15)} {bar} {level_text} ({level}/10)")

        # Display empty line after skills
        print()

        # Display unlocked abilities section if they exist
        if hasattr(skills, 'unlocked_abilities') and skills.unlocked_abilities:
            if self.use_colors:
                print(f"\n{self.colors['cyan']}╔═══════════════════════════════════════════════════════╗{self.colors['reset']}")
                print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}SPECIAL ABILITIES{' ' * 34}║{self.colors['reset']}")
                print(f"{self.colors['cyan']}╚═══════════════════════════════════════════════════════╝{self.colors['reset']}")
            else:
                self.display_subtitle("Special Abilities")

            for ability, unlocked in skills.unlocked_abilities.items():
                if unlocked:
                    ability_name = ability.replace('_', ' ').title()
                    if self.use_colors:
                        print(f"  {self.colors['green']}✓{self.colors['reset']} {self.colors['bold']}{ability_name}{self.colors['reset']}")
                    else:
                        print(f"  ✓ {ability_name}")

    def display_event_outcome(self, event, outcome_text):
        """Display event outcome with enhanced dramatic reveal and visual styling.

        Args:
            event (str): Event title
            outcome_text (str): Description of the outcome
        """
        self.clear_screen()
        width = min(self.width, 80)

        if self.use_colors:
            # Create a more dramatic event outcome display with animation

            # Step 1: Display a loading/suspense animation
            self._animate_loading("Determining outcome", 0.8)
            time.sleep(0.3)
            print()

            # Step 2: Create a fancy event box
            print(f"\n{self.colors['magenta']}╔{'═' * (width-2)}╗{self.colors['reset']}")

            # Create centered event title with padding
            title = f"EVENT: {event}"
            padding = (width - len(title) - 2) // 2
            print(f"{self.colors['magenta']}║{' ' * padding}{self.colors['bold']}{self.colors['white']}{title}{self.colors['reset']}{self.colors['magenta']}{' ' * (width - len(title) - padding - 2)}║{self.colors['reset']}")

            # Add a divider line
            print(f"{self.colors['magenta']}╠{'═' * (width-2)}╣{self.colors['reset']}")

            # Step 3: Dramatic typing animation for outcome text
            # Split and wrap text for better presentation
            wrapped_lines = self._wrap_text(outcome_text, width - 4)

            # First line with special formatting
            if wrapped_lines:
                first_line = wrapped_lines[0]
                print(f"{self.colors['magenta']}║ {self.colors['reset']}", end='')
                for char in first_line:
                    sys.stdout.write(f"{self.colors['yellow']}{char}{self.colors['reset']}")
                    sys.stdout.flush()
                    time.sleep(0.03)
                print(f"{' ' * (width - len(first_line) - 4)}{self.colors['magenta']}║{self.colors['reset']}")

                # Remaining lines with slightly faster typing
                for line in wrapped_lines[1:]:
                    print(f"{self.colors['magenta']}║ {self.colors['reset']}", end='')
                    for char in line:
                        sys.stdout.write(f"{self.colors['white']}{char}{self.colors['reset']}")
                        sys.stdout.flush()
                        time.sleep(0.02)
                    print(f"{' ' * (width - len(line) - 4)}{self.colors['magenta']}║{self.colors['reset']}")

            # Add a bottom border
            print(f"{self.colors['magenta']}╚{'═' * (width-2)}╝{self.colors['reset']}")

            # Add a dramatic pause
            time.sleep(0.5)

            # Add reflection prompt
            print(f"\n{self.colors['cyan']}What will you do next?{self.colors['reset']}")

        else:
            # Non-colored version
            print("\n" + "=" * width)
            print(f"EVENT: {event}".center(width))
            print("-" * width)

            # Split and wrap text for better presentation
            wrapped_lines = self._wrap_text(outcome_text, width - 4)
            for line in wrapped_lines:
                print(f"  {line}")

            print("=" * width)
            print("\nWhat will you do next?")

    def display_help(self):
        """Display help information for the game with enhanced visual formatting."""
        self.clear_screen()
        
        # Create section divider utility
        def add_divider():
            if self.use_colors:
                print(f"\n{self.colors['cyan']}{'─' * 50}{self.colors['reset']}")
            else:
                print("\n" + "─" * 50)

        # Display main help sections
        if self.use_colors:
            print(f"\n{self.colors['cyan']}╔{'═' * 48}╗{self.colors['reset']}")
            print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}Game Help & Quick Reference Guide{' ' * 16}║{self.colors['reset']}")
            print(f"{self.colors['cyan']}╚{'═' * 48}╝{self.colors['reset']}")
        else:
            print("\n=== Game Help & Quick Reference Guide ===")

        # Emergency Actions
        self.display_subtitle("Emergency Actions")
        self.display_text("• Press 'q' - Quick save and quit")
        self.display_text("• Press 'h' - Show this help screen")
        self.display_text("• Press 'Esc' - Cancel current action")
        
        add_divider()

        # Critical Resources
        self.display_subtitle("Critical Resources")
        self.display_text("• Find food before satiety drops below 20")
        self.display_text("• Find shelter before night (especially in bad weather)")
        self.display_text("• Maintain hygiene above 30 to avoid infections")
        self.display_text("• Keep mental health above 40 to avoid breakdowns")
        
        add_divider()

        # Services & Locations
        self.display_subtitle("Services & Operating Hours")
        self.display_text("• Shelters: Usually open 5PM - 8AM")
        self.display_text("• Food Banks: Usually open 9AM - 3PM")
        self.display_text("• Medical Clinics: Usually open 10AM - 4PM")
        self.display_text("• Libraries: Warm shelter during day hours")
        
        add_divider()

        # Inventory Management
        self.display_subtitle("Inventory Management")
        self.display_text("• Check weight limit before picking up items")
        self.display_text("• Food items can spoil - eat perishables first")
        self.display_text("• Warm clothing crucial for winter survival")
        self.display_text("• Keep essential documents safe")
        
        add_divider()

        # Success Tips
        self.display_subtitle("Success Tips")
        self.display_text("• Build relationships with NPCs for better access to services")
        self.display_text("• Check weather forecast before traveling")
        self.display_text("• Maintain documentation for service applications")
        self.display_text("• Balance immediate needs with long-term goals")

        # Let user return to game
        if self.use_colors:
            print(f"\n{self.colors['yellow']}Press Enter to return to game...{self.colors['reset']}")
        else:
            print("\nPress Enter to return to game...")
        input()
        self.clear_screen()

        if self.use_colors:
            # Create a fancy help title banner
            print(f"\n{self.colors['cyan']}╔═══════════════════════════════════════════════════════╗{self.colors['reset']}")
            print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}GAME HELP & INFORMATION{' ' * 30}║{self.colors['reset']}")
            print(f"{self.colors['cyan']}╚═══════════════════════════════════════════════════════╝{self.colors['reset']}")
        else:
            self.display_title("HELP")

        help_sections = [
            {
                "title": "Basic Controls",
                "icon": "⌨",
                "color": "green",
                "content": [
                    "Enter the number corresponding to your choice when prompted.",
                    "Press Enter to continue through text.",
                    "Type 'help' at any prompt to view this guide again.",
                    "Type 'quit' to save and exit the game."
                ]
            },
            {
                "title": "Stats",
                "icon": "♥",
                "color": "red",
                "content": [
                    "Health: Your physical condition. If it reaches 0, the game ends.",
                    "Hunger: How hungry you are. Higher values are worse. High hunger decreases health.",
                    "Energy: Your energy level. Low energy affects mental well-being and limits activities.",
                    "Mental: Your mental well-being. Low mental health affects decision-making.",
                    "Hygiene: Your cleanliness. Low hygiene can affect health and social interactions."
                ]
            },
            {
                "title": "Time & Weather",
                "icon": "☀",
                "color": "yellow",
                "content": [
                    "The game progresses in hourly increments.",
                    "Different activities take different amounts of time.",
                    "Different locations and services are available at different times.",
                    "Weather and temperature affect your needs and available options.",
                    "Nights are cold and dangerous - always find shelter before dark.",
                    "Severe weather can cause health problems if you're not properly sheltered."
                ]
            },
            {
                "title": "Inventory & Resources",
                "icon": "▣",
                "color": "yellow",
                "content": [
                    "Items have weight - carrying too much will slow you down.",
                    "Food items reduce hunger but may have other effects.",
                    "Clothing improves cold resistance and helps in harsh weather.",
                    "Medicine can treat illnesses and injuries.",
                    "Some items can be traded or sold for money."
                ]
            },
            {
                "title": "Locations",
                "icon": "⌂",
                "color": "cyan",
                "content": [
                    "Different locations offer different resources and opportunities.",
                    "Travel between locations takes time.",
                    "Some locations are safer than others, especially at night.",
                    "Indoor locations provide shelter from the elements.",
                    "Special locations unlock as you progress through the story."
                ]
            },
            {
                "title": "Skills & Abilities",
                "icon": "⚒",
                "color": "magenta",
                "content": [
                    "Skills improve as you use them, making related actions more effective.",
                    "Higher social skills improve your interactions with NPCs.",
                    "Survival skills help with finding resources and staying alive.",
                    "Technical skills allow you to craft and repair items.",
                    "Special abilities unlock at certain skill thresholds."
                ]
            },
            {
                "title": "Survival Tips",
                "icon": "★",
                "color": "green",
                "content": [
                    "Prioritize finding shelter before nightfall, especially in bad weather.",
                    "Balance your immediate needs with long-term goals.",
                    "Build relationships with NPCs to unlock more options.",
                    "Develop skills to improve your chances of success.",
                    "Manage your resources carefully - food and medicine are precious.",
                    "Mental health is as important as physical health - take time to rest.",
                    "The city changes with weather and time - plan accordingly."
                ]
            }
        ]

        # Display each section with enhanced formatting
        for section in help_sections:
            if self.use_colors:
                # Create a colored section header with icon
                icon = section.get("icon", "•")
                color = section.get("color", "white")
                print(f"\n{self.colors['bold']}{self.colors[color]}{icon} {section['title'].upper()}{self.colors['reset']}")
                print(f"{self.colors['gray']}{'─' * 50}{self.colors['reset']}")
            else:
                print(f"\n{section['title']}")
                print("-" * len(section['title']))

            # Display content with improved formatting
            for i, line in enumerate(section['content']):
                if self.use_colors:
                    # Add subtle alternating background for easier reading
                    if i % 2 == 0:
                        print(f"  • {line}")
                    else:
                        print(f"  • {line}")
                else:
                    print(f"  • {line}")

        # Add keyboard shortcuts section at the bottom
        if self.use_colors:
            print(f"\n{self.colors['cyan']}╔═══════════════════════════════════════════════════════╗{self.colors['reset']}")
            print(f"{self.colors['cyan']}║ {self.colors['bold']}{self.colors['white']}KEYBOARD SHORTCUTS{' ' * 34}║{self.colors['reset']}")
            print(f"{self.colors['cyan']}╚═══════════════════════════════════════════════════════╝{self.colors['reset']}")

            # Display keyboard shortcuts in a grid format
            print(f"  {self.colors['yellow']}[1-9]{self.colors['reset']} - Select menu options     {self.colors['yellow']}[m]{self.colors['reset']} - View map")
            print(f"  {self.colors['yellow']}[i]{self.colors['reset']}   - Open inventory         {self.colors['yellow']}[s]{self.colors['reset']} - View stats")
            print(f"  {self.colors['yellow']}[q]{self.colors['reset']}   - Save and quit          {self.colors['yellow']}[h]{self.colors['reset']} - Show this help screen")
        else:
            print("\nKEYBOARD SHORTCUTS")
            print("-" * 18)
            print("  [1-9] - Select menu options     [m] - View map")
            print("  [i]   - Open inventory         [s] - View stats")
            print("  [q]   - Save and quit          [h] - Show this help screen")

        print("\nPress Enter to return to the game...")
        input()
        self.clear_screen()

    def animate_text(self, text, delay=0.03):
        """Display text with a typing animation effect.

        Args:
            text (str): Text to display
            delay (float): Delay between characters in seconds
        """
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    def progress_bar(self, value, max_value, width=20, title="", animate=True):
        """Display an animated progress bar.

        Args:
            value (int): Current value
            max_value (int): Maximum value
            width (int): Width of the progress bar
            title (str): Title for the bar
            animate (bool): Whether to animate the bar
        """
        # Prevent division by zero
        if max_value <= 0:
            max_value = 1
        percentage = min(1.0, max(0.0, value / max_value))
        filled_width = int(width * percentage)

        if animate:
            for i in range(filled_width + 1):
                if self.use_colors:
                    color = self._get_status_color(percentage * 100)
                    bar = f"{title} [{color}{'■' * i}{self.colors['reset']}{'□' * (width - i)}] {int((i/width) * 100)}%"
                else:
                    bar = f"{title} [{'#' * i}{'-' * (width - i)}] {int((i/width) * 100)}%"
                sys.stdout.write('\r' + bar)
                sys.stdout.flush()
                time.sleep(0.02)
            print()
        else:
            if self.use_colors:
                if percentage < 0.3:
                    color = self.colors['red']
                elif percentage < 0.7:
                    color = self.colors['yellow']
                else:
                    color = self.colors['green']

                bar = f"{title} [{color}{'■' * filled_width}{self.colors['reset']}{'□' * (width - filled_width)}] {int(percentage * 100)}%"
            else:
                bar = f"{title} [{'#' * filled_width}{'-' * (width - filled_width)}] {int(percentage * 100)}%"

            print(bar)

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')


class DailySummary:
    """Displays daily goals and progress tracking."""
    
    def __init__(self, ui):
        self.ui = ui
        
    def display(self, player, time_system):
        """Display daily summary and goals."""
        if self.ui.use_colors:
            print(f"\n{self.ui.colors['cyan']}╔═══════════════════ DAILY SUMMARY ══════════════════════╗{self.ui.colors['reset']}")
            
            # Immediate Needs Section
            print(f"{self.ui.colors['bold']}Immediate Needs:{self.ui.colors['reset']}")
            needs = []
            if player.satiety < 30:
                needs.append(f"{self.ui.colors['red']}• Find Food (Urgent){self.ui.colors['reset']}")
            if player.energy < 30:
                needs.append(f"{self.ui.colors['red']}• Need Rest{self.ui.colors['reset']}")
            if time_system.is_harsh_weather():
                needs.append(f"{self.ui.colors['red']}• Find Shelter (Bad Weather){self.ui.colors['reset']}")
            if not needs:
                needs.append(f"{self.ui.colors['green']}• Basic needs met{self.ui.colors['reset']}")
            for need in needs:
                print(f"  {need}")

            # Active Goals Section
            print(f"\n{self.ui.colors['bold']}Active Goals:{self.ui.colors['reset']}")
            if player.active_quests:
                for quest in player.active_quests:
                    progress = player.quest_progress.get(quest.id, 0)
                    print(f"  • {quest.title} ({progress}% complete)")
            else:
                print("  • No active quests")

            # Progress Indicators
            if player.job_prospects > 0:
                print(f"\n{self.ui.colors['bold']}Job Search:{self.ui.colors['reset']} {player.job_prospects}% toward employment")
            if player.housing_prospects > 0:
                print(f"{self.ui.colors['bold']}Housing Search:{self.ui.colors['reset']} {player.housing_prospects}% toward stable housing")

            print(f"{self.ui.colors['cyan']}╚════════════════════════════════════════════════════════╝{self.ui.colors['reset']}")
        else:
            print("\n=== DAILY SUMMARY ===")
            print("Immediate Needs:")
            if player.satiety < 30:
                print("  ! Find Food (Urgent)")
            if player.energy < 30:
                print("  ! Need Rest")
            if time_system.is_harsh_weather():
                print("  ! Find Shelter (Bad Weather)")
                
            print("\nActive Goals:")
            if player.active_quests:
                for quest in player.active_quests:
                    progress = player.quest_progress.get(quest.id, 0)
                    print(f"  - {quest.title} ({progress}% complete)")
            else:
                print("  - No active quests")
