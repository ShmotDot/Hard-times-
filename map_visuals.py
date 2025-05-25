"""
Map visualization module for Hard Times Ottawa.
Provides text-based visualization of the game world map.
"""
import math

class MapVisuals:
    """Handles generation of a visual map representation."""
    
    def __init__(self, use_colors=True):
        """Initialize the map visualization system.
        
        Args:
            use_colors (bool): Whether to use ANSI color codes
        """
        self.use_colors = use_colors
        
        # Define color codes for map visuals
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
            "magenta": "\033[95m",
            "bg_blue": "\033[44m",
            "bg_cyan": "\033[46m",
            "bg_white": "\033[47m",
            "bg_yellow": "\033[43m",
            "bg_red": "\033[41m",
            "bg_green": "\033[42m",
            "bg_magenta": "\033[45m"
        }
        
        # Map location symbols
        self.symbols = {
            "player": "P",
            "location": "■",
            "visited": "□",
            "current": "▣",
            "connection": "─",
            "corner": "┼",
            "vertical": "│",
            "horizontal": "─"
        }
        
        # Area type colors (for different neighborhoods)
        self.area_colors = {
            "downtown": "red",
            "residential": "green",
            "industrial": "yellow",
            "waterfront": "blue",
            "park": "green",
            "commercial": "cyan",
            "campus": "magenta"
        }
        
        # Default map layout for Ottawa neighborhoods
        # These are relative positions for a text-based map
        self.default_map_positions = {
            "Downtown": {"x": 5, "y": 5, "type": "downtown"},
            "ByWard Market": {"x": 7, "y": 4, "type": "commercial"},
            "Centretown": {"x": 5, "y": 7, "type": "residential"},
            "Lebreton Flats": {"x": 3, "y": 5, "type": "industrial"},
            "Lowertown": {"x": 7, "y": 6, "type": "residential"},
            "Sandy Hill": {"x": 8, "y": 5, "type": "campus"},
            "Vanier": {"x": 9, "y": 6, "type": "residential"},
            "Hintonburg": {"x": 2, "y": 7, "type": "residential"},
            "Mechanicsville": {"x": 2, "y": 5, "type": "industrial"},
            "Glebe": {"x": 6, "y": 8, "type": "residential"},
            "Little Italy": {"x": 3, "y": 8, "type": "commercial"},
            "Westboro": {"x": 1, "y": 8, "type": "residential"},
            "Chinatown": {"x": 4, "y": 6, "type": "commercial"},
            "Overbrook": {"x": 9, "y": 4, "type": "residential"},
            "Parliament Hill": {"x": 6, "y": 3, "type": "downtown"},
            "Lansdowne Park": {"x": 7, "y": 9, "type": "park"},
            "Ottawa River": {"x": 5, "y": 2, "type": "waterfront"},
            "Rideau Canal": {"x": 7, "y": 7, "type": "waterfront"}
        }
    
    def get_location_symbol(self, location_name, current_location, discovered_locations):
        """Get the appropriate symbol for a location on the map.
        
        Args:
            location_name (str): Name of the location
            current_location (str): Name of the player's current location
            discovered_locations (list): List of locations the player has discovered
            
        Returns:
            str: Symbol to use for this location
        """
        if location_name == current_location:
            return self.symbols["current"]
        elif location_name in discovered_locations:
            return self.symbols["visited"]
        else:
            return self.symbols["location"]
    
    def get_location_color(self, location_type):
        """Get the appropriate color for a location based on its type.
        
        Args:
            location_type (str): Type of the location
            
        Returns:
            str: Color to use for this location
        """
        if not self.use_colors:
            return ""
            
        return self.colors.get(self.area_colors.get(location_type, "white"), self.colors["white"])
    
    def draw_map(self, current_location, discovered_locations, location_manager):
        """Draw a text-based map of Ottawa showing known locations.
        
        Args:
            current_location (str): Name of the player's current location
            discovered_locations (list): List of locations the player has discovered
            location_manager (LocationManager): The game's location manager object
            
        Returns:
            str: Multi-line string representation of the map
        """
        # Initialize grid size
        width, height = 12, 12
        grid = [[" " for _ in range(width)] for _ in range(height)]
        
        # Add water features (decorative)
        if self.use_colors:
            # Add Ottawa River at the top
            for x in range(width):
                grid[0][x] = f"{self.colors['blue']}~{self.colors['reset']}"
                grid[1][x] = f"{self.colors['blue']}~{self.colors['reset']}"
            
            # Add Rideau Canal
            for y in range(3, height-2):
                grid[y][6] = f"{self.colors['cyan']}≈{self.colors['reset']}"
        
        # Process connections between locations
        connections = set()
        for loc_name, loc_data in self.default_map_positions.items():
            # Only show connections for discovered locations or adjacent to discovered
            if loc_name in discovered_locations:
                loc_obj = location_manager.get_location(loc_name)
                if loc_obj and hasattr(loc_obj, 'connected_locations'):
                    for connected_name in loc_obj.connected_locations:
                        # Only add connection if both locations are discovered
                        # Or if one is the current location (partially show routes)
                        if (connected_name in discovered_locations or 
                                connected_name == current_location or 
                                loc_name == current_location):
                            if connected_name in self.default_map_positions:
                                # Create a unique connection identifier (smaller name first for consistency)
                                conn = tuple(sorted([loc_name, connected_name]))
                                connections.add(conn)
        
        # Draw connections (roads)
        for loc1, loc2 in connections:
            if loc1 in self.default_map_positions and loc2 in self.default_map_positions:
                x1, y1 = self.default_map_positions[loc1]["x"], self.default_map_positions[loc1]["y"]
                x2, y2 = self.default_map_positions[loc2]["x"], self.default_map_positions[loc2]["y"]
                
                # Draw simple line for adjacent locations
                if abs(x1 - x2) + abs(y1 - y2) == 1:
                    # Horizontal connection
                    if y1 == y2:
                        x_min, x_max = min(x1, x2), max(x1, x2)
                        for x in range(x_min + 1, x_max):
                            grid[y1][x] = self.symbols["horizontal"]
                    # Vertical connection
                    elif x1 == x2:
                        y_min, y_max = min(y1, y2), max(y1, y2)
                        for y in range(y_min + 1, y_max):
                            grid[y][x1] = self.symbols["vertical"]
                # Draw L-shaped line for diagonal connections
                else:
                    # Create an L shape using a midpoint
                    mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # Just use one corner point for simplicity in text UI
                    corner_x, corner_y = x1, y2
                    
                    # Place corner symbol
                    grid[corner_y][corner_x] = self.symbols["corner"]
                    
                    # Horizontal part
                    x_min, x_max = min(x1, corner_x), max(x1, corner_x)
                    for x in range(x_min + 1, x_max):
                        grid[y1][x] = self.symbols["horizontal"]
                    
                    # Vertical part
                    y_min, y_max = min(corner_y, y2), max(corner_y, y2)
                    for y in range(y_min + 1, y_max):
                        grid[y][corner_x] = self.symbols["vertical"]
                    
                    # Horizontal part (second segment)
                    x_min, x_max = min(corner_x, x2), max(corner_x, x2)
                    for x in range(x_min + 1, x_max):
                        grid[corner_y][x] = self.symbols["horizontal"]
        
        # Place locations on the map
        for loc_name, position in self.default_map_positions.items():
            # Only show discovered locations and current location
            if loc_name in discovered_locations or loc_name == current_location:
                x, y = position["x"], position["y"]
                loc_type = position["type"]
                
                symbol = self.get_location_symbol(loc_name, current_location, discovered_locations)
                
                if self.use_colors:
                    color = self.get_location_color(loc_type)
                    grid[y][x] = f"{color}{symbol}{self.colors['reset']}"
                else:
                    grid[y][x] = symbol
        
        # Compose the final map string
        map_lines = []
        
        # Add a title
        if self.use_colors:
            map_lines.append(f"{self.colors['bold']}{self.colors['cyan']}Ottawa City Map{self.colors['reset']}")
        else:
            map_lines.append("Ottawa City Map")
            map_lines.append("=" * 15)
        
        # Add the grid
        for row in grid:
            map_lines.append("".join(row))
        
        # Add a legend
        if self.use_colors:
            map_lines.append(f"{self.colors['bold']}Legend:{self.colors['reset']}")
            map_lines.append(f"{self.colors['magenta']}{self.symbols['current']}{self.colors['reset']} - Your location")
            map_lines.append(f"{self.symbols['visited']} - Visited location")
            map_lines.append(f"{self.symbols['location']} - Undiscovered location")
        else:
            map_lines.append("Legend:")
            map_lines.append(f"{self.symbols['current']} - Your location")
            map_lines.append(f"{self.symbols['visited']} - Visited location")
            map_lines.append(f"{self.symbols['location']} - Undiscovered location")
            
        # Add location names for discovered locations
        discovered_names = []
        for loc_name in sorted(discovered_locations):
            if loc_name == current_location:
                if self.use_colors:
                    discovered_names.append(f"{self.colors['magenta']}{loc_name}{self.colors['reset']} (Current)")
                else:
                    discovered_names.append(f"{loc_name} (Current)")
            else:
                discovered_names.append(loc_name)
        
        if discovered_names:
            if self.use_colors:
                map_lines.append(f"{self.colors['bold']}Known Locations:{self.colors['reset']} {', '.join(discovered_names)}")
            else:
                map_lines.append(f"Known Locations: {', '.join(discovered_names)}")
        
        return "\n".join(map_lines)
        
    def get_mini_map(self, current_location, discovered_locations, location_manager):
        """Generate a smaller version of the map focused on the current location.
        
        Args:
            current_location (str): Name of the player's current location
            discovered_locations (list): List of locations the player has discovered
            location_manager (LocationManager): The game's location manager object
            
        Returns:
            str: Multi-line string representation of a mini-map
        """
        # Similar to draw_map but with a smaller view centered on current location
        # Only show immediate connections
        
        if current_location not in self.default_map_positions:
            # If current location isn't in our map positions, return a basic message
            return "Map unavailable for this location."
        
        # Initialize a smaller grid
        width, height = 5, 5
        grid = [[" " for _ in range(width)] for _ in range(height)]
        
        # Get current location position
        current_x = self.default_map_positions[current_location]["x"]
        current_y = self.default_map_positions[current_location]["y"]
        
        # Center coordinates for our view
        center_x, center_y = 2, 2
        
        # Calculate offsets to center the current location
        offset_x = center_x - current_x
        offset_y = center_y - current_y
        
        # Place current location at center
        grid[center_y][center_x] = self.symbols["current"]
        
        # Get connected locations
        loc_obj = location_manager.get_location(current_location)
        if loc_obj and hasattr(loc_obj, 'connected_locations'):
            for connected_name in loc_obj.connected_locations:
                if connected_name in self.default_map_positions:
                    # Get the position adjusted for our mini-map
                    conn_x = self.default_map_positions[connected_name]["x"] + offset_x
                    conn_y = self.default_map_positions[connected_name]["y"] + offset_y
                    
                    # Only show if it fits on our mini-map
                    if 0 <= conn_x < width and 0 <= conn_y < height:
                        # Show as visited or unvisited
                        symbol = self.get_location_symbol(connected_name, current_location, discovered_locations)
                        grid[conn_y][conn_x] = symbol
                        
                        # Draw a simple connection line
                        if conn_x < center_x and conn_y == center_y:
                            # Location is to the left
                            grid[center_y][center_x-1] = self.symbols["horizontal"]
                        elif conn_x > center_x and conn_y == center_y:
                            # Location is to the right
                            grid[center_y][center_x+1] = self.symbols["horizontal"]
                        elif conn_x == center_x and conn_y < center_y:
                            # Location is above
                            grid[center_y-1][center_x] = self.symbols["vertical"]
                        elif conn_x == center_x and conn_y > center_y:
                            # Location is below
                            grid[center_y+1][center_x] = self.symbols["vertical"]
                        else:
                            # Diagonal connection, simplified for mini-map
                            dx = 1 if conn_x > center_x else -1
                            dy = 1 if conn_y > center_y else -1
                            grid[center_y+dy][center_x+dx] = self.symbols["corner"]
        
        # Compose the mini-map string
        mini_map_lines = []
        
        # Add a title
        if self.use_colors:
            mini_map_lines.append(f"{self.colors['cyan']}Local Area{self.colors['reset']}")
        else:
            mini_map_lines.append("Local Area")
        
        # Add the grid
        for row in grid:
            mini_map_lines.append("".join(row))
        
        return "\n".join(mini_map_lines)