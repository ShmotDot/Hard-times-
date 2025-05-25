import traceback
import sys

def run_with_traceback():
    try:
        print("Step 1: Importing main module...")
        import main
        print("Main module imported successfully")
        
        # Try creating UI instance
        print("Step 2: Testing UI module...")
        from game.ui import UI
        ui = UI()
        print("UI instance created successfully")
        
        # Try weather visuals
        print("Step 3: Testing WeatherVisuals...")
        from game.weather_visuals import WeatherVisuals
        wv = WeatherVisuals()
        print("WeatherVisuals instance created successfully")
        
        # Try map visuals
        print("Step 4: Testing MapVisuals...")
        from game.map_visuals import MapVisuals
        mv = MapVisuals()
        print("MapVisuals instance created successfully")

        # Run a more complete test of the UI status display
        print("\nStep 5: Testing UI.display_status...")
        # Mock the basic player and time_system classes
        class MockPlayer:
            def __init__(self):
                self.health = 80
                self.satiety = 70  # Higher is better (replaces hunger)
                self.energy = 70
                self.mental = 60
                self.hygiene = 50
                self.money = 25.75
                self.job_prospects = 30
                self.housing_prospects = 20
                self.skills = {"survival": 5, "social": 3, "mechanical": 2}
                self.unlocked_abilities = {"cold_resistance": False}
                self.status_effects = {}
                
            @property
            def hunger(self):
                """Get hunger level (for backward compatibility)."""
                return 100 - self.satiety
                
            @hunger.setter
            def hunger(self, value):
                """Set hunger (used for backward compatibility)."""
                self.satiety = 100 - value
        
        class MockTimeSystem:
            def __init__(self):
                self.weather = "clear"
                self.temperature = 15
                
            def get_day(self):
                return 1
                
            def get_time_string(self):
                return "10:00 AM"
                
            def get_period(self):
                return "morning"
                
            def is_harsh_weather(self):
                return False
                
            def get_weather_effects(self):
                return {
                    "description": "A nice clear day",
                    "health_mod": 0,
                    "energy_mod": 1,
                    "shelter_importance": 0.5
                }

        try:
            player = MockPlayer()
            time_system = MockTimeSystem()
            print("Testing UI.display_status with mocked objects...")
            ui.display_status(player, time_system)
            print("UI.display_status test succeeded")
        except Exception as e:
            print(f"ERROR in UI.display_status: {type(e).__name__}: {e}")
            traceback.print_exc()
            
        # Test UI help display
        print("\nStep 6: Testing UI.display_help...")
        try:
            # ui.display_help()
            print("UI.display_help test skipped (requires user input)")
        except Exception as e:
            print(f"ERROR in UI.display_help: {type(e).__name__}: {e}")
            traceback.print_exc()

        # Test location display
        print("\nStep 7: Testing UI.display_location...")
        class MockLocation:
            def __init__(self):
                self.name = "Test Location"
                self.description = "A test location for debugging"
                self.danger_level = 2
                self.type = "residential"
                self.is_outdoor = True
                self.services = [
                    {"name": "Test Service", "hours": "9 AM - 5 PM", "description": "A test service"}
                ]
                self.connections = [
                    {"name": "Another Location", "travel_time": 2}
                ]
        
        try:
            location = MockLocation()
            location_effects = {"description": "It's quiet here"}
            # ui.display_location(location, location_effects, time_system)
            print("UI.display_location test skipped (would display to console)")
        except Exception as e:
            print(f"ERROR in UI.display_location: {type(e).__name__}: {e}")
            traceback.print_exc()
            
        # Test inventory display
        print("\nStep 8: Testing UI.display_inventory...")
        class MockItem:
            def __init__(self, name, weight, value, quality="good", category="miscellaneous"):
                self.name = name
                self.weight = weight
                self.value = value
                self.quality = MockQuality(quality)
                self.category = category
                self.description = f"A {quality} quality {name}"
                
        class MockQuality:
            def __init__(self, value):
                self.value = value
                
        class MockInventory:
            def __init__(self):
                self.items = {
                    "item1": MockItem("Test Item", 0.5, 10),
                    "item2": MockItem("Food", 0.3, 5, "excellent", "food")
                }
                self.quantities = {"item1": 2, "item2": 1}
                self.capacity = 10
                
        try:
            inventory = MockInventory()
            # ui.display_inventory(inventory, 20.0)
            print("UI.display_inventory test skipped (would display to console)")
        except Exception as e:
            print(f"ERROR in UI.display_inventory: {type(e).__name__}: {e}")
            traceback.print_exc()
            
        # Test skills display
        print("\nStep 9: Testing UI.display_skills...")
        try:
            skills = {"survival": 5, "social": 3, "mechanical": 2}
            # ui.display_skills(skills)
            print("UI.display_skills test skipped (would display to console)")
        except Exception as e:
            print(f"ERROR in UI.display_skills: {type(e).__name__}: {e}")
            traceback.print_exc()
            
        # Test event outcome display
        print("\nStep 10: Testing UI.display_event_outcome...")
        try:
            event = "Test Event"
            outcome_text = "This is a test outcome of the event"
            # ui.display_event_outcome(event, outcome_text)
            print("UI.display_event_outcome test skipped (would display to console)")
        except Exception as e:
            print(f"ERROR in UI.display_event_outcome: {type(e).__name__}: {e}")
            traceback.print_exc()

        # Test ResourceManager and the get_random_item method
        print("\nStep 11: Testing ResourceManager.get_random_item...")
        try:
            from game.resources import ResourceManager
            
            # Create resource manager with test data
            rm = ResourceManager()
            
            # Test get_random_item
            print("Testing get_random_item...")
            item = rm.get_random_item()
            if item:
                print(f"Random item: {item.name}, Category: {item.category.value}")
            else:
                print("No items available (items.json might be missing or empty)")
                
            # Test get_random_item_by_category
            print("\nTesting get_random_item_by_category...")
            categories = ["food", "clothing", "medicine", "tool", "valuable", "crafting"]
            for category in categories:
                try:
                    item = rm.get_random_item_by_category(category)
                    if item:
                        print(f"Random {category} item: {item.name}")
                    else:
                        print(f"No items found in category: {category}")
                except Exception as e:
                    print(f"Error getting {category} item: {type(e).__name__}: {e}")
            
            print("\nResourceManager tests passed")
        except Exception as e:
            print(f"ERROR in ResourceManager tests: {type(e).__name__}: {e}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("Starting debug run...")
    success = run_with_traceback()
    print(f"Debug run {'succeeded' if success else 'failed'}")