"""
Hard Times Ottawa - A text-based survival game simulating homelessness in Ottawa
"""

import sys
import time
import os

# Core game systems
from game.utils import safe_input
from game.ui import UI
from game.player import Player
from game.events.event_manager import EventManager
from game.events.event import Event
from game.time_system import TimeSystem
from game.location import LocationManager
from game.economy_manager import EconomyManager
from game.error_handler import error_handler
from game.tutorial import Tutorial
from game.resources import ResourceManager

def clear_screen():
    """Clear the terminal screen."""
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Mac and Linux
        os.system('clear')

def introduction():
    """Display the game introduction and backstory."""
    print("\n============== HARD TIMES: OTTAWA ==============\n")
    print("""
    You are Devin, a 28-year-old who has fallen on hard times in Ottawa.

    After struggling with mental health issues and losing your job, you couldn't 
    make rent and were evicted from your apartment. With nowhere else to go, 
    you find yourself on the streets of Ottawa in the middle of autumn.

    This game aims to provide insight into the complex realities faced by people
    experiencing homelessness.
    """)
    print("================================================")
    safe_input("Press Enter to begin your journey...")

def about():
    """Display information about the game."""
    clear_screen()
    print("\n============== ABOUT THE GAME ==============\n")
    print("""
    Hard Times: Ottawa is a text-based survival simulation that aims to provide
    insight into the challenges faced by people experiencing homelessness in
    Ottawa, Canada.

    This game is meant to be educational and thought-provoking, while respecting
    the real hardships faced by those in similar situations.
    """)
    print("============================================")
    safe_input("Press Enter to return to the main menu...")
    clear_screen()

def game_loop(player, event_manager, time_system, tutorial):
    """Main game loop handling core gameplay mechanics."""
    location_manager = LocationManager()
    economy_manager = EconomyManager()
    ui = UI()

def game_loop(player, event_manager, time_system, tutorial):
    """Main game loop."""
    running = True
    while running:
        try:
            # Update time and weather
            time_system.update()
            
            # Display current status
            ui = UI()
            ui.display_status(player, time_system)
            
            # Process daily actions
            available_actions = player.get_available_actions()
            action = ui.get_player_action(available_actions)
            
            if action == "quit":
                running = False
                continue
                
            # Process the chosen action
            result = player.perform_action(action)
            
            # Process any triggered events
            events = event_manager.get_current_events()
            for event in events:
                event.process(player)
            
            # Check win/lose conditions
            if player.health <= 0:
                ui.display_game_over("You have died.")
                running = False
            
        except Exception as e:
            error_handler(e)
            ui.display_error("An error occurred. Please try again.")


    current_location = location_manager.get_location("Downtown")

    def get_action_time_cost(action, player_stats):
        """Calculate dynamic time cost based on player condition."""
        base_costs = {
            "food_search": 1,
            "shelter_search": 2,
            "work_search": 3,
            "travel": 1,
            "wait": 1
        }

        # Modify cost based on energy/health
        multiplier = 1.0
        if player_stats.energy < 30:
            multiplier *= 1.5
        if player_stats.health < 40:
            multiplier *= 1.3

        return max(1, int(base_costs.get(action, 1) * multiplier))

    from game.weather_visuals import WeatherVisuals
    from game.daily_summary import DailySummary
    from game.save_manager import SaveManager

    save_manager = SaveManager()
    daily_summary = DailySummary(ui)
    weather_visuals = WeatherVisuals()
    current_location = location_manager.get_location("Downtown")  # Start downtown

    # Initialize systems
    economy_manager.initialize_economy()

    try:
        while True:
            # Display current status, weather, and location
            ui.display_status(player, time_system)
            weather_effects = time_system.get_weather_effects()
            print(weather_visuals.get_weather_banner(time_system.weather, time_system.temperature, time_system.is_harsh_weather()))
            if current_location:
                ui.display_location(current_location)

            # Update economy based on weather and time
            economy_manager.update_economy(time_system)

            # Display available actions
            print("\nAvailable Actions:")
            print("1. Look for food")
            print("2. Find shelter")
            print("3. Rest")
            print("4. Check inventory")
            print("5. Travel")
            print("6. Wait")
            print("7. Help")
            print("8. Save Game")
            print("9. Load Game")
            print("10. Quit")

            choice = safe_input("\nWhat would you like to do? ")

            if choice == "1":
                event = event_manager.get_random_event(location=current_location)
                event_manager.process_event(event, current_location)
            elif choice == "2":
                # Handle shelter search
                print("\nLooking for shelter...")
                time.sleep(1)
            elif choice == "3":
                # Handle resting
                print("\nResting...")
                player.rest(10)
                time_system.advance_time(1)
            elif choice == "4":
                ui.display_inventory(player.inventory, player.money)
            elif choice == "5":
                print("\nTravel options will be available soon...")
                time.sleep(1)
            elif choice == "6":
                hours = 1
                print(f"\nWaiting for {hours} hour(s)...")
                time_system.advance_time(hours)
                player.update_waiting_stats()
            elif choice == "7":
                ui.display_help()
            elif choice == "8":
                # Save game
                save_file = save_manager.save_game(player, time_system, location_manager, event_manager)
                print(f"\nGame saved as: {save_file}")

            elif choice == "9":
                # Load game
                saves = save_manager.get_save_files()
                if not saves:
                    print("\nNo save files found.")
                else:
                    print("\nAvailable saves:")
                    for i, save in enumerate(saves, 1):
                        print(f"{i}. {save['filename']} ({save['timestamp']})")

                    save_choice = safe_input("\nEnter save number to load (or 0 to cancel): ")
                    if save_choice and save_choice.isdigit():
                        save_num = int(save_choice)
                        if 0 < save_num <= len(saves):
                            if save_manager.load_game(saves[save_num-1]["filename"], 
                                                    player, time_system, location_manager, event_manager):
                                print("\nGame loaded successfully!")
                            else:
                                print("\nFailed to load game.")
                        else:
                            print("\nInvalid save number.")

            elif choice == "10":
                confirm = safe_input("\nAre you sure you want to quit? (y/n) ")
                if confirm and confirm.lower() == 'y':
                    print("\nThanks for playing Hard Times: Ottawa.")
                    sys.exit(0)
            else:
                print("\nInvalid choice. Please try again.")

            # Update game state
            player.update_stats()

            # Check for contextual tutorial tips
            tutorial.check_for_tips(player, current_location, time_system)

            # Check for game over
            if player.health <= 0:
                print("\nYour health has dropped to zero. Game Over.")
                break

    except Exception as e:
        print(f"\nAn error occurred in the game loop: {e}")
        sys.exit(1)

def main_menu():
    """Display the main menu and handle user selection."""
    clear_screen()
    print("\n============== HARD TIMES: OTTAWA ==============\n")
    print("1. New Game")
    print("2. About")
    print("3. Quit")

    while True:
        choice = safe_input("\nEnter your choice (1-3): ")

        if choice == "1":
            return 'new_game'
        elif choice == "2":
            about()
            return 'main_menu'
        elif choice == "3":
            print("\nThank you for playing Hard Times: Ottawa.")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def main():
    """Main entry point for the game."""
    # Initialize core game systems
    player = Player()
    time_system = TimeSystem()
    event_manager = EventManager(player, time_system)
    ui = UI()
    resource_manager = ResourceManager()
    location_manager = LocationManager()
    
    # Initialize tutorial system
    tutorial = Tutorial(ui, player, resource_manager, location_manager, time_system)

    while True:
        action = main_menu()

        if action == 'new_game':
            clear_screen()
            introduction()
            # Run tutorial before starting game
            tutorial.run()
            game_loop(player, event_manager, time_system, tutorial)
        elif action == 'main_menu':
            continue

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)