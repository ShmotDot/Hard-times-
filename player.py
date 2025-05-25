"""
Player module for Hard Times: Ottawa.
Handles all player stats, inventory, and related methods.
"""
import random
from typing import Dict, List, Optional, Any, Union
from game.resources import Inventory, ItemCategory, Item
from game.error_handler import error_handler, StateError, GameError

# Simple temporary SkillTree class until proper implementation
class SkillTree:
    """Placeholder for the SkillTree system."""
    def __init__(self, name: str):
        self.name = name
        self.level = 0
        self.xp = 0
        self.skills = {}

    def add_skill(self, skill_name: str) -> None:
        """Add a skill to this tree."""
        self.skills[skill_name] = 0

    def increase_skill(self, skill_name: str, amount: int = 1) -> None:
        """Increase a skill's level."""
        if skill_name in self.skills:
            self.skills[skill_name] = min(10, self.skills[skill_name] + amount)

    def gain_xp_from_action(self, action_type: str, xp_amount: int = 5) -> None:
        """Gain XP from a specific action."""
        self.xp += xp_amount
        # Level up logic (simple example)
        if self.xp >= 100:
            self.level +=1
            self.xp -= 100


class Player:
    """Represents the player character in the game."""

    def __init__(self, name="Devin"):
        """Initialize a new player with starting attributes."""
        self.name = name
        self.quest_choices = {}
        self.quest_outcomes = {}
        self.game_time = 0
        self.quest_progress = {}
        self.skills = {}
        self.in_shelter = False
        self.status_effects = {}
        self.benefits = {
            "welfare": False,
            "disability": False,
            "food_bank_eligible": True
        }

        # Housing status
        self.current_shelter = None
        self.shelter_nights = 0
        self.housing_status = "homeless"  # homeless, shelter, temporary, permanent
        self.rent_due = 0
        self.rent_paid_until = None

        # Core stats (0-100 scale)
        self.health = 70      # Overall physical health (reduced due to recent eviction)
        self.satiety = 60     # Fullness/satiety level (higher is better, lower due to situation)
        self.energy = 60      # Energy/fatigue level (lower due to stress)
        self.mental = 50      # Mental well-being (lower due to mental illness)
        self.hygiene = 70     # Cleanliness/appearance (reduced due to recent eviction)

        # For backward compatibility
        self._hunger = 40     # Legacy hunger attribute (hidden)

        # Backstory elements
        self.has_mental_illness = True

        # Story-related flags and progress
        self.story_flags = {}
        self.service_applications = {}  # Tracks pending service applications and their deadlines

        # Health-related systems
        self.has_infection = False  # Quick property for checking infections
        self.mental_illness_type = "Undiagnosed"  # Can be discovered during gameplay
        self.has_medication = False
        self.days_without_medication = 5  # Starting scenario

        # Feature unlocking system
        self.unlocked_features = {
            'crafting': False,
            'services': True,  # Basic services are always available
            'shops': False,    # Shops are locked until player has spent time in the game
            'work': False,     # Work opportunities are locked until player has clean clothes
            'black_market': False  # Black market requires street cred or NPC relationships
        }

        # Health condition tracking
        self.injuries = {}    # Active injuries
        self.infections = {}  # Active infections
        self.addiction = 0    # Addiction level (0-100)
        self.withdrawal = 0    # Withdrawal severity (0-100)

        # Law enforcement
        self.heat = 0        # Police attention (0-100)
        self.wanted = False  # Actively wanted by police

        # Social stats
        self.dignity = 70    # Self-worth/pride (0-100)
        self.hope = 80      # Motivation/outlook (0-100)
        self.stigma = 0     # Discrimination faced (accumulates)

        # Faction and relationship tracking
        self.faction_reputation = {
            "shelters": 0,      # Reputation with shelter system
            "streets": 0,       # Reputation with street community
            "police": 0,        # Reputation with law enforcement
            "social_services": 0,  # Reputation with social workers/services
            "businesses": 0,    # Reputation with local businesses
            "community": 0      # Reputation with general community
        }
        self.npc_relationships = {}  # Track individual NPC relationships and history

        # Life simulation stats
        self.age = 25        # Player's age
        self.education = 0   # Education level (0-5)
        self.relationships = []  # List of relationships
        self.happiness = 70  # Overall happiness

        # Career and Income
        self.job = {
            "title": None,
            "salary": 0,
            "satisfaction": 0,
            "experience": 0,
            "stress": 0
        }
        self.skills_career = {
            "computer": 0,
            "customer_service": 0,
            "manual_labor": 0,
            "leadership": 0,
            "creativity": 0
        }

        # Social Life
        self.social_status = 50  # Social standing (0-100)
        self.charisma = 50      # Ability to influence others
        self.relationships = {
            "friends": [],
            "family": [],
            "romantic": None,
            "professional": []
        }

        # Lifestyle
        self.lifestyle_quality = 30  # Overall quality of life
        self.stress = 40           # Stress level
        self.fitness = 60          # Physical fitness
        self.appearance = 50       # Physical appearance

        # Resources
        self.money = 10.0     # Starting cash

        # Initialize inventory with the new system
        self.inventory = Inventory(max_weight=10.0)  # Start with 10kg capacity

        # Progression tracking
        self.days_survived = 0
        self.reputation = {   # Reputation with different groups
            "shelters": 0,
            "public": 0,
            "services": 0
        }
        # Skill trees
        self.skill_trees = {
            "Survival": SkillTree("Survival"),
            "Diplomacy": SkillTree("Diplomacy"), 
            "Hustle": SkillTree("Hustle"),
            "Street Knowledge": SkillTree("Street Knowledge"),
            "Craft": SkillTree("Craft")
        }
        self.skill_xp = {    # XP gained toward each skill
            "Survival": 0,
            "Diplomacy": 0,
            "Hustle": 0, 
            "Street Knowledge": 0,
            "Craft": 0
        }
        self.milestones = {   # Tracks major achievements
            "hardened_survivor": False,  # Sleep outside 15 nights
            "silver_tongued": False,     # Successfully persuade 10 NPCs
            "master_scavenger": False,   # Find 30 useful items
            "ghost_walker": False,       # Evade police 5 times
            "urban_engineer": False,     # Craft 10 items
            "street_boss": False         # Gain 50 Street Cred
        }
        self.milestone_progress = {  # Tracks progress toward milestones
            "nights_outside": 0,
            "successful_persuasions": 0,
            "items_found": 0,
            "police_evasions": 0,
            "items_crafted": 0,
            "street_cred": 0
        }
        self.unlocked_abilities = {  # Special abilities from milestones
            "cold_resistance": False,    # Reduced cold damage
            "better_trades": False,      # Better prices from vendors
            "scavenging_bonus": False,   # Higher quality loot
            "stealth_bonus": False,      # Reduced Heat gain
            "crafting_expert": False,    # Advanced crafting options
            "gang_leader": False         # Can recruit homeless NPCs
        }
        self.job_prospects = 0  # Progress toward employment
        self.housing_prospects = 0  # Progress toward stable housing
        self.street_cred = 0   # Influence with homeless community
        self.active_quests = []
        self.completed_quests = set()
        self.quest_progress = {}

    def apply_for_service(self, service_type, deadline_days, service_name=None):
        """Apply for a service with a specific processing deadline.

        Args:
            service_type (str): Type of service applied for (e.g., 'housing', 'benefits', 'id')
            deadline_days (int): Days until the application is processed
            service_name (str, optional): Optional specific name of the service

        Returns:
            tuple: (success, message) - success is bool, message describes outcome
        """
        if service_type in self.service_applications:
            return False, f"You already have a pending application for {service_type}."

        # Add application with deadline based on current day
        self.service_applications[service_type] = {
            'name': service_name or service_type.capitalize(),
            'application_day': self.days_survived,
            'deadline_day': self.days_survived + deadline_days,
            'processed': False
        }

        return True, f"Your application for {service_type} has been submitted. Check back in {deadline_days} days."

    def check_service_applications(self, current_day):
        """Check if any service applications have been processed.

        Args:
            current_day (int): Current game day

        Returns:
            list: Messages about processed applications
        """
        messages = []

        for service_type, application in list(self.service_applications.items()):
            # Skip already processed applications
            if application['processed']:
                continue

            # Check if deadline has been reached
            if current_day >= application['deadline_day']:
                # Mark as processed
                application['processed'] = True

                # Determine approval based on relevant factors
                approval_chance = 0.6  # Base 60% chance

                # Factors that affect approval
                if self.story_flags.get('has_id', False):
                    approval_chance += 0.2  # Having ID helps

                if service_type == 'housing':
                    # Housing applications factor in different things
                    if self.hygiene < 30:
                        approval_chance -= 0.15
                    if self.has_infection:
                        approval_chance -= 0.1
                    if self.reputation['services'] > 20:
                        approval_chance += 0.15

                elif service_type == 'benefits':
                    # Benefits approval is easier with proper documentation
                    if not self.story_flags.get('has_id', False):
                        approval_chance -= 0.3  # Hard to get benefits without ID

                # Apply random chance with weighted factors
                approved = random.random() < approval_chance

                if approved:
                    msg = f"Your application for {application['name']} has been approved!"

                    # Update story flags
                    flag_name = f"{service_type}_approved"
                    self.story_flags[flag_name] = True

                    # Special case handling
                    if service_type == 'housing':
                        self.housing_prospects += 25
                    elif service_type == 'benefits':
                        benefit_amount = random.randint(50, 100)
                        self.money += benefit_amount
                        msg += f" You received ${benefit_amount}."
                    elif service_type == 'id':
                        self.story_flags['has_id'] = True

                    messages.append(msg)
                else:
                    messages.append(f"Your application for {application['name']} was declined. Try again later.")

        return messages

    def update_stats(self):
        """Update player stats based on current conditions.
        Called after each action to apply natural changes to stats.
        """
        # Process health conditions
        self.check_injuries()
        self.process_infections()

        # Scale energy loss based on hunger/satiety
        hunger_multiplier = 1 + ((100 - self.satiety) / 50)  # Lower satiety = faster energy drain

        # Check for any completed service applications
        application_messages = self.check_service_applications(self.days_survived)

        # Satiety decreases over time (hunger increases)
        self.satiety = max(0, self.satiety - random.randint(2, 5))

        # Energy decreases gradually
        self.energy -= random.randint(1, 3)

        # Process addiction/withdrawal
        if self.addiction > 0:
            self.withdrawal += random.randint(1, 3)
            if self.withdrawal > 50:
                self.health -= random.randint(1, 3)
                self.energy -= random.randint(2, 5)
                self.mental -= random.randint(3, 6)

        # Satiety affects health and mental well-being
        if self.satiety < 20:  # Very hungry (hunger > 80)
            self.health -= random.randint(3, 6)
            self.mental -= random.randint(2, 4)
        elif self.satiety < 40:  # Hungry (hunger > 60)
            self.health -= random.randint(1, 3)
            self.mental -= random.randint(1, 2)

        # Low energy affects mental well-being
        if self.energy < 20:
            self.mental -= random.randint(2, 5)

        # Low hygiene affects health and infection risk
        if self.hygiene < 30:
            self.health -= random.randint(1, 3)
            for injury in self.injuries.values():
                injury['infection_risk'] *= 1.5

        # Update mental state
        self.update_mental_state()

        # Natural heat decay
        if not self.wanted:
            self.decrease_heat(0.5)

        # Ensure all stats stay within bounds
        self._clamp_stats()

    def update_waiting_stats(self):
        """Update stats while waiting/passing time.
        Called for each hour of waiting.
        """
        # Faster stat degradation when just waiting
        self.satiety = max(0, self.satiety - random.randint(3, 6))
        self.energy -= random.randint(2, 4)
        self.mental -= random.randint(1, 3)

        # Ensure all stats stay within bounds
        self._clamp_stats()

    @property
    def hunger(self):
        """Get hunger level (for backward compatibility).
        Returns the inverse of satiety (100 - satiety).
        Higher hunger values indicate worse condition.
        """
        return 100 - self.satiety

    @hunger.setter
    def hunger(self, value):
        """Set hunger (used for backward compatibility).
        Sets satiety to the inverse of hunger (100 - hunger).
        """
        self.satiety = 100 - value

    def _clamp_stats(self):
        """Ensure all stats stay within the 0-100 range and track changes."""
        old_stats = {
            "health": self.health,
            "satiety": self.satiety,
            "energy": self.energy,
            "mental": self.mental,
            "hygiene": self.hygiene
        }

        self.health = max(0, min(100, self.health))
        self.satiety = max(0, min(100, self.satiety))
        self.energy = max(0, min(100, self.energy))
        self.mental = max(0, min(100, self.mental))
        self.hygiene = max(0, min(100, self.hygiene))

        # Track significant changes (>5 points)
        changes = []
        for stat, old_val in old_stats.items():
            new_val = getattr(self, stat)
            if abs(new_val - old_val) >= 5:
                direction = "improved" if new_val > old_val else "decreased"
                changes.append(f"{stat.title()} {direction}")

        return changes

    def eat(self, amount):
        """Increase satiety/reduce hunger by the given amount.

        Args:
            amount (int): Amount to increase satiety/reduce hunger by
        """
        self.satiety = min(100, self.satiety + amount)
        # Eating also slightly improves mental well-being
        self.mental = min(100, self.mental + (amount // 4))

    def rest(self, amount):
        """Recover energy by the given amount.

        Args:
            amount (int): Amount to increase energy by
        """
        self.energy = min(100, self.energy + amount)
        # Resting also slightly improves mental well-being
        self.mental = min(100, self.mental + (amount // 5))

    def take_damage(self, amount):
        """Reduce health by the given amount.

        Args:
            amount (int): Amount of damage to take
        """
        self.health = max(0, self.health - amount)
        # Damage also affects mental well-being
        self.mental = max(0, self.mental - (amount // 2))

    def improve_hygiene(self, amount):
        """Improve hygiene by the given amount.

        Args:
            amount (int): Amount to improve hygiene by
        """
        self.hygiene = min(100, self.hygiene + amount)
        # Better hygiene improves mental well-being
        self.mental = min(100, self.mental + (amount // 4))

    def add_item(self, item, quantity=1):
        """Add an item to the player's inventory.

        Args:
            item: The item to add (Item object)
            quantity (int): Quantity of the item to add (default 1)

        Returns:
            tuple: (success, message) - success is bool, message describes outcome
        """
        return self.inventory.add_item(item, quantity)

    def remove_item(self, item_id, quantity=1):
        """Remove an item from the player's inventory.

        Args:
            item_id: The ID of the item to remove
            quantity (int): Quantity to remove (default 1)

        Returns:
            tuple: (success, message, item) - success is bool, message describes outcome
        """
        return self.inventory.remove_item(item_id, quantity)

    def has_item(self, item_id, quantity=1):
        """Check if the player has a specific item.

        Args:
            item_id: ID of the item to check for
            quantity (int): Required quantity (default 1)

        Returns:
            bool: True if the player has enough of the item
        """
        item = self.inventory.get_item(item_id)
        item_quantity = self.inventory.quantities.get(item_id, 0) if item else 0
        return item is not None and item_quantity >= quantity

    def get_items_by_category(self, category):
        """Get all items in the inventory of a specific category.

        Args:
            category: The category to filter by

        Returns:
            list: List of items matching the category
        """
        return self.inventory.get_items_by_category(category)

    def use_item(self, item_id):
        """Use an item from inventory and apply its effects.

        Args:
            item_id: ID of the item to use

        Returns:
            tuple: (success, message) - success is bool, message describes outcome
        """
        item = self.inventory.get_item(item_id)
        if not item:
            return False, "You don't have that item."

        success, message = item.use(self)

        # If the item was used successfully and is consumable, remove it
        if success and item.category in [ItemCategory.FOOD, ItemCategory.DRINK, ItemCategory.MEDICINE]:
            self.inventory.remove_item(item_id, 1)

        return success, message

    def check_expired_items(self):
        """Check and remove any expired items from inventory.

        Returns:
            list: Names of expired items that were removed
        """
        return self.inventory.check_expiry()

    def craft_item(self, recipe_id, resource_manager):
        """Craft an item using the inventory resources.

        Args:
            recipe_id: ID of the recipe to craft
            resource_manager: ResourceManager instance to access recipes

        Returns:
            tuple: (success, message, item) - success is bool, message describes outcome
        """
        # Check if player has advanced crafting abilities
        has_expert = self.unlocked_abilities.get("crafting_expert", False)

        # Get the appropriate crafting skill
        craft_skill = self.skills.get("crafting", 0)

        # Get basic recipe information to check requirements
        can_craft, missing_items = resource_manager.can_craft(recipe_id, self.inventory)

        # Check skill requirements
        recipe = None
        for r in resource_manager.crafting_recipes:
            if r.get('id') == recipe_id:
                recipe = r
                break

        if recipe and recipe.get('skill_required') and recipe.get('skill_level'):
            skill_name = recipe['skill_required'].lower()
            required_level = recipe['skill_level']

            # Expert crafters have a -1 level requirement bonus
            if has_expert:
                required_level -= 1

            player_skill = self.skills.get(skill_name.lower(), 0)

            if player_skill < required_level:
                return False, f"You need {skill_name} level {required_level} to craft this item.", None

        # If we can craft it, do so with potential quality bonuses
        if can_craft:
            success, message, item = resource_manager.craft_item(recipe_id, self.inventory)

            if success:
                # Increase crafting skill XP
                self.skill_xp["Craft"] += 5

                # Increment items crafted for milestone tracking
                self.milestone_progress["items_crafted"] += 1

                # Check for milestone achievement
                milestone_message = self.check_milestones()
                if milestone_message:
                    message += f"\n{milestone_message}"

            return success, message, item
        else:
            return False, f"Cannot craft: missing {', '.join(missing_items)}", None

    def add_money(self, amount):
        """Add money to the player.

        Args:
            amount (float): Amount of money to add
        """
        self.money += amount

    def spend_money(self, amount):
        """Attempt to spend money.

        Args:
            amount (float): Amount to spend

        Returns:
            bool: True if successful, False if not enough money

        Raises:
            StateError: If amount is negative or invalid
        """
        try:
            if not isinstance(amount, (int, float)):
                raise StateError("Invalid amount type")
            if amount < 0:
                raise StateError("Cannot spend negative amount")
            if self.money < amount:
                return False

            self.money -= amount
            return True
        except Exception as e:
            error_handler.handle_error(e, {"action": "spend_money", "amount": amount})
            return False

    def find_food(self, food_availability):
        """Attempt to find food based on location availability.

        Args:
            food_availability (float): 0.0-1.0 representing food availability

        Returns:
            bool: True if food was found, False otherwise
        """
        # Food finding chance is based on availability and player's foraging skill
        base_chance = food_availability * 0.6
        skill_bonus = self.skills["foraging"] * 0.05

        return random.random() < (base_chance + skill_bonus)

    def scavenge_location(self, location, resource_manager, time_system):
        """Scavenge a location for resources."""
        items_found = []
        messages = []

        # Track skill progression
        if self.skills.get("scavenging", 0) > 0:
            self.skill_trees["Street Knowledge"].gain_xp_from_action("find_resources")
            self.skill_trees["Survival"].gain_xp_from_action("find_food")

        # Base chance modified by location and skills
        base_chance = 0.5
        scavenge_skill = self.skills.get("scavenging", 0) * 0.05

        # Time of day affects scavenging
        time_mod = 0
        if time_system.get_period() == "night":
            time_mod = -0.1  # Harder to find things at night
        elif time_system.get_period() == "morning":
            time_mod = 0.05  # Fresh items in morning

        # Weather effects
        weather_mod = 0
        if hasattr(time_system, 'weather'):
            if time_system.weather == "rain":
                weather_mod = -0.05  # Rain makes scavenging harder
            elif time_system.weather == "clear":
                weather_mod = 0.05  # Clear weather helps

        # Location danger affects quality
        danger_mod = location.danger_level / 20  # 0.05 to 0.5

        # Scavenging quality bonus from milestones
        quality_bonus = 1.0
        if self.unlocked_abilities.get("scavenging_bonus", False):
            quality_bonus = 1.1

        # Final chance calculation
        find_chance = min(0.9, base_chance + scavenge_skill + time_mod + weather_mod)

        # Number of attempts
        attempts = random.randint(1, 3)

        # Now try to find items
        for _ in range(attempts):
            if random.random() < find_chance:
                # Determine category based on location type
                categories = []

                # Different locations have different item distributions
                if "shelter" in location.name.lower():
                    categories = ["clothing", "food", "medicine", "document"]
                elif "park" in location.name.lower():
                    categories = ["food", "crafting", "misc"]
                elif "downtown" in location.name.lower():
                    categories = ["valuable", "food", "clothing", "misc"]
                elif "river" in location.name.lower():
                    categories = ["crafting", "misc", "food"]
                else:
                    # Generic distribution for any location
                    categories = ["food", "crafting", "medicine", "misc", "clothing"]

                # Select a random category with weighting
                category = random.choice(categories)

                # Get all items of this category
                category_items = []
                for item_id, item in resource_manager.items.items():
                    if item.category.value == category:
                        category_items.append(item)

                if category_items:
                    # Select an item with quality consideration
                    quality_items = []
                    poor_items = []
                    common_items = []
                    good_items = []

                    for item in category_items:
                        if item.quality.value == "poor":
                            poor_items.append(item)
                        elif item.quality.value == "common":
                            common_items.append(item)
                        elif item.quality.value == "good":
                            good_items.append(item)

                    # Higher danger = better items, but also affected by skill and milestones
                    item_quality_roll = random.random()
                    danger_quality = (danger_mod + scavenge_skill) * quality_bonus

                    selected_item = None
                    if item_quality_roll < 0.5:  # 50% poor items
                        if poor_items:
                            selected_item = random.choice(poor_items)
                    elif item_quality_roll < 0.8:  # 30% common items
                        if common_items:
                            selected_item = random.choice(common_items)
                        elif poor_items:
                            selected_item = random.choice(poor_items)
                    else:  # 20% good items
                        # Apply danger and skill bonuses
                        good_chance = danger_quality
                        if random.random() < good_chance:
                            if good_items:
                                selected_item = random.choice(good_items)
                            elif common_items:
                                selected_item = random.choice(common_items)
                            elif poor_items:
                                selected_item = random.choice(poor_items)

                    if selected_item:
                        # Create a new instance of the item
                        found_item = resource_manager.get_item_template(selected_item.item_id)

                        # Add to inventory
                        success, msg = self.inventory.add_item(found_item)
                        if success:
                            items_found.append(found_item)
                            messages.append(f"You found: {found_item.name}")

                            # Record for milestone tracking
                            self.milestone_progress["items_found"] += 1
                        else:
                            messages.append(msg)

        # If nothing found
        if not items_found:
            messages.append("You couldn't find anything useful.")

        # Check for milestone achievement
        milestone_message = self.check_milestones()
        if milestone_message:
            messages.append(milestone_message)

        # XP for scavenging
        self.skill_xp["Survival"] += 2

        return items_found, messages

    def increase_skill(self, skill, amount=1):
        """Increase a player skill.

        Args:
            skill (str): Skill name
            amount (int): Amount to increase (default 1)

        Raises:
            ValueError: If skill is invalid or amount is negative
        """
        try:
            if not isinstance(amount, (int, float)):
                raise ValueError("Amount must be a number")
            if amount < 0:
                raise ValueError("Cannot increase skill by negative amount")
            if skill not in self.skills:
                raise ValueError(f"Invalid skill: {skill}")

            self.skills[skill] = min(10, self.skills[skill] + amount)
        except Exception as e:
            error_handler.handle_error(e, {"action": "increase_skill", "skill": skill, "amount": amount})
            raise

    def improve_reputation(self, group, amount=1, context="general"):
        """Improve reputation with dynamic relationship building.

        Args:
            group (str): Group name
            amount (int): Amount to increase (default 1)
            context (str): Context of reputation change

        Returns:
            tuple: (message, unlocked_features) - Feedback about reputation change

        Raises:
            ValueError: If amount is negative or group is invalid
        """
        try:
            if not isinstance(amount, (int, float)):
                raise ValueError("Amount must be a number")
            if amount < 0:
                raise ValueError("Cannot improve reputation by negative amount")
            if group not in self.faction_reputation:
                raise ValueError(f"Invalid reputation group: {group}")
            base_amount = amount

            # Context multipliers with more impactful events
            multipliers = {
                "helped_in_crisis": 2.0,
                "kept_promise": 1.5,
                "volunteered": 1.4,
                "shared_info": 1.3,
                "showed_reliability": 1.2,
                "general": 1.0,
                "broke_trust": 0.5
            }

            # Apply relationship depth bonus
            current_rep = self.faction_reputation[group]
            depth_bonus = 1.0 + (current_rep * 0.05)  # Deeper relationships grow faster

            # Calculate final reputation change
            final_amount = base_amount * multipliers.get(context, 1.0) * depth_bonus

            # Update reputation with diminishing returns
            new_value = self.faction_reputation[group] + int(final_amount)
            if new_value > 10:
                self.faction_reputation[group] = 10
            else:
                self.faction_reputation[group] = new_value

            # Unlock special interactions at reputation thresholds
            if self.faction_reputation[group] >= 8:
                return "Trusted Ally status achieved with " + group
            elif self.faction_reputation[group] >= 5:
                return "Respected Member status with " + group

            return None
        except Exception as e:
            error_handler.handle_error(e, {"action": "improve_reputation", "group": group, "amount": amount})
            raise

    def increase_job_prospects(self, amount=1):
        """Increase job prospects.

        Args:
            amount (int): Amount to increase (default 1)

        Raises:
            ValueError: If amount is negative or invalid
        """
        try:
            if not isinstance(amount, (int, float)):
                raise ValueError("Amount must be a number")
            if amount < 0:
                raise ValueError("Cannot increase prospects by negative amount")

            self.job_prospects = min(100, self.job_prospects + amount)
        except Exception as e:
            error_handler.handle_error(e, {"action": "increase_job_prospects", "amount": amount})
            raise

    def increase_housing_prospects(self, amount=1):
        """Increase housing prospects.

        Args:
            amount (int): Amount to increase (default 1)
        """
        self.housing_prospects = min(100, self.housing_prospects + amount)

    def check_milestones(self):
        """Check and update milestone progress."""
        # Hardened Survivor check
        if self.milestone_progress["nights_outside"] >= 15 and not self.milestones["hardened_survivor"]:
            self.milestones["hardened_survivor"] =True
            self.unlocked_abilities["cold_resistance"] = True
            return "Hardened Survivor milestone achieved! You now have better resistance to cold."

        # Silver Tongued check
        if self.milestone_progress["successful_persuasions"] >= 10 and not self.milestones["silver_tongued"]:
            self.milestones["silver_tongued"] = True
            self.unlocked_abilities["better_trades"] = True
            return "Silver Tongued milestone achieved! You now get better deals in trades."

        # Master Scavenger check
        if self.milestone_progress["items_found"] >= 30 and not self.milestones["master_scavenger"]:
            self.milestones["master_scavenger"] = True
            self.unlocked_abilities["scavenging_bonus"] = True
            return "Master Scavenger milestone achieved! You find better quality items while scavenging."

        # Ghost Walker check
        if self.milestone_progress["police_evasions"] >= 5 and not self.milestones["ghost_walker"]:
            self.milestones["ghost_walker"] = True
            self.unlocked_abilities["stealth_bonus"] = True
            return "Ghost Walker milestone achieved! You generate less Heat when spotted."

        # Urban Engineer check
        if self.milestone_progress["items_crafted"] >= 10 and not self.milestones["urban_engineer"]:
            self.milestones["urban_engineer"] = True
            self.unlocked_abilities["crafting_expert"] = True
            return "Urban Engineer milestone achieved! You can now craft advanced items."

        # Street Boss check
        if self.milestone_progress["street_cred"] >= 50 and not self.milestones["street_boss"]:
            self.milestones["street_boss"] = True
            self.unlocked_abilities["gang_leader"] = True
            return "Street Boss milestone achieved! You can now recruit other homeless NPCs."

        return None

    def apply_milestone_effects(self):
        """Apply effects from unlocked milestones."""
        if self.unlocked_abilities["cold_resistance"]:
            # 50% reduction in cold damage
            return 0.5
        if self.unlocked_abilities["better_trades"]:
            # 20% better prices
            return 0.8
        if self.unlocked_abilities["scavenging_bonus"]:
            # 10% better loot quality
            return 1.1
        if self.unlocked_abilities["stealth_bonus"]:
            # 5% less Heat gain
            return 0.95

    def update_lifestyle(self):
        """Update lifestyle metrics based on current conditions."""
        # Formula to calculate lifestyle quality
        health_factor = self.health * 0.3
        hygiene_factor = self.hygiene * 0.2
        mental_factor = self.mental * 0.3
        social_factor = self.social_status * 0.2

        self.lifestyle_quality = (health_factor + hygiene_factor + mental_factor + social_factor) / 4

    def update_social(self):
        """Update social metrics and relationships."""
        # Social status is affected by hygiene, heat, money
        hygiene_factor = self.hygiene * 0.3
        heat_penalty = self.heat * 0.2
        money_factor = min(50, self.money) * 0.5

        self.social_status = hygiene_factor + money_factor - heat_penalty
        self.social_status = max(10, min(100, self.social_status))

    def has_won(self):
        """Check if player has met the victory conditions."""
        # Victory conditions:
        # 1. Housing prospects above 80
        # 2. Job prospects above 70
        # 3. Mental health above 60
        # 4. Not wanted by police
        return (self.housing_prospects >= 80 and 
                self.job_prospects >= 70 and 
                self.mental >= 60 and 
                not self.wanted)

    def add_injury(self, injury_type, severity):
        """Add an injury to the player.

        Args:
            injury_type (str): Type of injury
            severity (int): Severity level
        """
        injury_id = f"{injury_type}_{len(self.injuries)}"
        self.injuries[injury_id] = {
            'type': injury_type,
            'severity': severity,
            'healing_progress': 0,
            'healing_required': severity * 24,  # Hours to heal depends on severity
            'infection_risk': 0.01 * severity  # More severe = higher infection risk
        }

    def check_injuries(self):
        """Process injuries and their effects."""
        for injury_id, injury in list(self.injuries.items()):
            # Reduce health based on severity
            if injury['severity'] > 0:
                self.health -= injury['severity'] * 0.5

            # Natural healing with shelter bonus
            base_healing = random.uniform(0.5, 1.5)
            # Add in_shelter property with default value False
            self.in_shelter = getattr(self, 'in_shelter', False)
            shelter_bonus = 1.5 if self.in_shelter else 1.0
            injury['healing_progress'] += base_healing * shelter_bonus 

            # Check if injury is healed
            if injury['healing_progress'] >= injury['healing_required']:
                del self.injuries[injury_id]
                continue

            # Check for infection
            if random.random() < injury['infection_risk']:
                self.add_infection(f"Infected {injury['type']}")
                injury['infection_risk'] = 0  # Already infected

    def add_infection(self, infection_type):
        """Add an infection to the player."""
        if infection_type in self.infections:
            # Worsen existing infection
            self.infections[infection_type]['severity'] += random.randint(1, 3)
        else:
            self.infections[infection_type] = {
                'severity': random.randint(2, 5),
                'duration': random.randint(24, 72),  # Hours
                'treated': False
            }

    def process_infections(self):
        """Handle active infections."""
        # Update has_infection property based on infections dictionary
        self.has_infection = len(self.infections) > 0

        for infection_type, infection in list(self.infections.items()):
            # Untreated infections worsen health
            if not infection['treated']:
                damage = infection['severity'] * 0.5
                self.health -= damage

                # Mental impacts
                self.mental -= damage * 0.5

                # Small chance infection worsens
                if random.random() < 0.1:  # 10% chance
                    infection['severity'] += 1
            else:
                # Treated infections improve over time
                infection['severity'] = max(0, infection['severity'] - 0.5)

            # Update duration
            infection['duration'] -= 1

            # Check if infection is cured/gone
            if infection['duration'] <= 0 or infection['severity'] <= 0:
                del self.infections[infection_type]

        # Update has_infection property after processing
        self.has_infection = len(self.infections) > 0

    def cure_infection(self, infection_type=None):
        """Cure an infection or all infections.

        Args:
            infection_type (str, optional): Specific infection to cure, or all if None

        Returns:
            bool: True if infection(s) were cured
        """
        if infection_type:
            # Cure specific infection
            if infection_type in self.infections:
                del self.infections[infection_type]
                self.has_infection = len(self.infections) > 0
                return True
            return False
        else:
            # Cure all infections
            had_infections = len(self.infections) > 0
            self.infections.clear()
            self.has_infection = False
            return had_infections

    def increase_heat(self, amount):
        """Increase police attention."""
        base_amount = amount

        # Apply stealth skill reduction
        amount *= max(0.5, 1.0 - (self.skills.get("stealth", 0) * 0.05))

        # Apply ghost walker ability if unlocked
        if self.unlocked_abilities.get("stealth_bonus", False):
            amount *= 0.95

        self.heat = min(100, self.heat + amount)

        # Chance to become wanted if heat is high
        if self.heat > 80 and random.random() < 0.2:
            self.wanted = True

        return amount < base_amount  # Returns True if reduction was applied

    def decrease_heat(self, amount):
        """Reduce police attention."""
        self.heat = max(0, self.heat - amount)

        # Chance to lose wanted status if heat is low
        if self.heat < 20 and self.wanted and random.random() < 0.1:
            self.wanted = False
            return True

        return False

    def apply_stigma(self, amount):
        """Track discrimination/stigma faced.
        
        Args:
            amount (float): Amount of stigma to apply. Higher values represent more severe discrimination.
                          Affects dignity (reduced by amount/2) and hope (reduced by amount/4).
        """
        self.stigma += amount
        self.dignity = max(0, self.dignity - (amount / 2))
        self.hope = max(0, self.hope - (amount / 4))

    def update_mental_state(self):
        """Update mental state based on conditions."""
        # Base mental state deterioration from low dignity or hope
        if self.dignity < 20 or self.hope < 20:
            self.mental -= random.randint(3, 8)

        # Impact of social stigma
        if self.stigma > 100:
            self.mental -= random.randint(1, 5)

        # Mental illness effects
        if self.has_mental_illness:
            if not self.has_medication or self.days_without_medication > 0:
                # Stronger negative effects when not medicated
                self.mental -= random.randint(2, 6)

                # Small chance of episode
                if random.random() < 0.05:  # 5% chance per update
                    # Mental health episode
                    self.mental -= random.randint(5, 15)
                    return "You experience a mental health episode. Your mental state deteriorates."
            else:
                # Medication helps stabilize mental health
                self.mental = min(100, self.mental + random.randint(1, 3))

        return None

    def start_quest(self, quest):
        """Start a new quest."""
        self.active_quests.append(quest)
        self.quest_progress[quest.id] = 0

    def update_quest_progress(self, quest_id, amount):
        """Update progress on a quest."""
        if quest_id in self.quest_progress:
            self.quest_progress[quest_id] += amount

    def complete_quest(self, quest_id):
        """Complete a quest."""
        if quest_id in self.quest_progress:
            self.completed_quests.add(quest_id)
            self.active_quests.remove(self.get_quest(quest_id))
            del self.quest_progress[quest_id]

    def get_quest(self, quest_id):
        """Get a quest by ID."""
        for quest in self.active_quests:
            if quest.id == quest_id:
                return quest
        return None

    def get_active_quests(self):
        """Return a list of active quests."""
        return self.active_quests

    def get_completed_quests(self):
        """Return a set of completed quests."""
        return self.completed_quests

    def get_quest_progress(self, quest_id):
        """Get the progress of a specific quest."""
        return self.quest_progress.get(quest_id, 0)

    def save_quest_state(self):
        """Save current quest state and choices."""
        quest_state = {
            'active_quests': [quest.chain_id for quest in self.active_quests],
            'completed_quests': list(self.completed_quests),
            'quest_progress': self.quest_progress,
            'quest_choices': self.quest_choices,
            'quest_outcomes': self.quest_outcomes
        }
        return quest_state

    def load_quest_state(self, state):
        """Load saved quest state."""
        self.completed_quests = set(state.get('completed_quests', []))
        self.quest_progress = state.get('quest_progress', {})
        self.quest_choices = state.get('quest_choices', {})
        self.quest_outcomes = state.get('quest_outcomes', {})
        # Reload active quests from chain_ids
        self._reload_active_quests(state.get('active_quests', []))

    def record_quest_outcome(self, quest_id, choice, outcome):
        """Record quest choice and outcome for future reference."""
        if quest_id not in self.quest_outcomes:
            self.quest_outcomes[quest_id] = []
        self.quest_outcomes[quest_id].append({
            'choice': choice,
            'outcome': outcome,
            'timestamp': self.game_time
        })