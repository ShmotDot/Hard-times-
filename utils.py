"""
Utility functions for Hard Times: Ottawa.
"""

def safe_input(prompt="", timeout=300):  # Increased timeout from 60 to 300 seconds
    """
    A wrapper for the input function that handles EOFError exceptions and timeouts.
    
    Args:
        prompt (str): The prompt to display to the user
        timeout (int): Maximum time to wait for input in seconds
        
    Returns:
        str: The user's input, empty string if EOFError, or None if timeout
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Input timed out")
    
    try:
        # Set up timeout handler if timeout is provided and > 0
        if timeout > 0:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)  # Set alarm
        
        result = input(prompt)
        
        # Cancel alarm if it hasn't triggered
        if timeout > 0:
            signal.alarm(0)
            
        return result
    except EOFError:
        # If we're running in a non-interactive environment, return an empty string
        return ""
    except TimeoutError:
        # If input timed out, return None
        if timeout > 0:
            signal.alarm(0)  # Cancel alarm
        print("\nInput timed out. Using default action.")
        return None
    except KeyboardInterrupt:
        # If interrupted, return a sentinel value
        if timeout > 0:
            signal.alarm(0)  # Cancel alarm
        print("\nInput interrupted. Returning to game...")
        return "CANCEL_INPUT"
    except Exception as e:
        # Catch other unforeseen input errors
        if timeout > 0:
            signal.alarm(0)  # Cancel alarm
        print(f"\nError reading input: {str(e)}. Using default action.")
        return None
    finally:
        # Ensure alarm is canceled in all cases
        if timeout > 0:
            signal.alarm(0)

def check_feature_availability(feature, player, current_location, time_system, npc_manager=None):
    """
    Check if a feature should be available based on game conditions.
    
    Args:
        feature (str): The feature to check ('crafting', 'services', 'shops', 'work', 'black_market')
        player: The player object
        current_location: The current location object
        time_system: The time system object
        npc_manager: Optional NPC manager for relationship checks
        
    Returns:
        tuple: (available: bool, message: str) whether feature is available and reason if not
    """
    
    # Initialize common variables
    current_hour = time_system.get_hour()
    days_survived = time_system.get_day()
    
    # Feature-specific checks
    if feature == 'crafting':
        # Crafting is unlocked if player has learned a recipe or gathered required items
        if not player.unlocked_features.get('crafting', False):
            # Check if player has any combination of items that could be crafted
            # This is a placeholder - real implementation would check actual recipes
            craftable_item_sets = [
                {'cloth', 'needle_and_thread'},
                {'plastic_bottle', 'duct_tape'},
                {'cardboard', 'newspaper', 'duct_tape'}
            ]
            
            # Check if player has any of the craftable sets
            inventory_item_ids = set(player.inventory.items.keys())
            has_craftable_set = any(craftable_set.issubset(inventory_item_ids) for craftable_set in craftable_item_sets)
            
            if has_craftable_set:
                # Unlock crafting permanently
                player.unlocked_features['crafting'] = True
                return True, "You've figured out how to craft something with the items you have!"
            else:
                return False, "You don't know how to craft anything with your current items."
        return True, ""
    
    elif feature == 'services':
        # Services are only available at locations with services during operating hours
        if not hasattr(current_location, 'services') or not current_location.services:
            return False, "There are no services available at this location."
            
        # Check if any services are open
        current_period = time_system.get_period()
        any_open = False
        
        for service in current_location.services:
            if service.get('operating_hours', {}).get(current_period, False):
                if current_hour < service.get('closing_hour', 18) - 1:
                    any_open = True
                    break
        
        if not any_open:
            return False, "All services are currently closed. Come back during operating hours."
            
        return True, ""
    
    elif feature == 'shops':
        # Shops are only available after a couple of days of gameplay
        if days_survived < 2:
            return False, "You need to get your bearings before you can find shops."
            
        if not hasattr(current_location, 'shops') or not current_location.shops:
            return False, "There are no shops at this location."
            
        # Check shop hours (most open 9am-6pm)
        if current_hour < 9 or current_hour >= 18:
            return False, "The shops are closed right now. They're open from 9AM to 6PM."
            
        return True, ""
    
    elif feature == 'work':
        # Work is only available when player is presentable and at appropriate locations during work hours
        
        # First check if player has clean clothes
        has_clean_clothes = False
        for item_id, item in player.inventory.items.items():
            if 'clothes' in item_id and 'clean' in item_id and player.inventory.quantities.get(item_id, 0) > 0:
                has_clean_clothes = True
                break
                
        if not has_clean_clothes:
            return False, "You need clean clothes to look for work."
            
        # Check if current location has work opportunities
        if not hasattr(current_location, 'work_opportunities') or not current_location.work_opportunities:
            return False, "There are no work opportunities at this location."
            
        # Check if during work hours (typically 8am-5pm)
        if current_hour < 8 or current_hour >= 17:
            return False, "It's outside normal working hours. Try between 8AM and 5PM."
            
        return True, ""
    
    elif feature == 'black_market':
        # Black market is only available with street cred or NPC connections
        if not player.unlocked_features.get('black_market', False):
            # Check street cred threshold
            if player.street_cred >= 25:
                player.unlocked_features['black_market'] = True
                return True, "Your reputation on the streets has earned you access to the black market."
                
            # Check NPC relationships
            if npc_manager:
                for npc_id, relationship in player.relationships.items():
                    npc = npc_manager.get_npc(npc_id)
                    if npc and npc.archetype == 'dealer' and relationship >= 75:
                        player.unlocked_features['black_market'] = True
                        return True, f"{npc.name} has decided to trust you with access to the black market."
            
            return False, "You don't have the connections to access the black market yet."
            
        # Check if in suitable location for black market (away from police)
        if hasattr(current_location, 'police_presence') and current_location.police_presence > 0.5:
            return False, "There's too much police presence here for any black market activity."
            
        # Check time of day (typically evening/night activity)
        current_period = time_system.get_period()
        if current_period not in ['evening', 'night']:
            return False, "The black market only operates during evening and night hours."
            
        return True, ""
    
    # Default case - feature is available
    return True, ""