
"""h import Dict, List, Optional
import random
from datetime import datetime, timedelta

class HousingSystem:
    def __init__(self):
        self.shelter_stays = {}
        self.housing_applications = {}
        self.eviction_notices = {}
        
        self.housing_tiers = {
            "emergency_shelter": {
                "cost": 0,
                "quality": 1,
                "stability": 0.2,
                "requirements": {}
            },
            "transitional_housing": {
                "cost": 200,
                "quality": 2,
                "stability": 0.5,
                "requirements": {
                    "housing_prospects": 30,
                    "days_sober": 5
                }
            },
            "shared_housing": {
                "cost": 400,
                "quality": 3,
                "stability": 0.7,
                "requirements": {
                    "housing_prospects": 50,
                    "income": 800,
                    "references": 1
                }
            },
            "subsidized_apartment": {
                "cost": 300,
                "quality": 4,
                "stability": 0.9,
                "requirements": {
                    "housing_prospects": 70,
                    "waiting_time": 30,
                    "clean_record": True
                }
            },
            "private_rental": {
                "cost": 800,
                "quality": 5,
                "stability": 1.0,
                "requirements": {
                    "housing_prospects": 90,
                    "income": 2400,
                    "credit_check": True
                }
            }
        }
        
    def check_shelter_availability(self, shelter_name: str, quality: str) -> bool:
        """Check if shelter has space available."""
        base_chance = {
            "high": 0.3,
            "medium": 0.5,
            "low": 0.8
        }.get(quality, 0.5)
        
        if datetime.now().month in [11, 12, 1, 2]:
            base_chance *= 0.5
            
        return random.random() < base_chance
        
    def get_available_housing_options(self, player) -> List[Dict]:
        """Get list of housing options player qualifies for."""
        available_options = []
        
        for tier_name, tier_data in self.housing_tiers.items():
            if self._meets_requirements(player, tier_data["requirements"]):
                available_options.append({
                    "name": tier_name,
                    "cost": tier_data["cost"],
                    "quality": tier_data["quality"],
                    "stability": tier_data["stability"]
                })
                
        return available_options
        
    def _meets_requirements(self, player, requirements: Dict) -> bool:
        """Check if player meets housing requirements."""
        if "housing_prospects" in requirements:
            if player.housing_prospects < requirements["housing_prospects"]:
                return False
                
        if "income" in requirements:
            if not player.job["salary"] or player.job["salary"] < requirements["income"]:
                return False
                
        if "days_sober" in requirements:
            if player.addiction > 0:
                return False
                
        if "clean_record" in requirements:
            if player.heat > 20 or player.wanted:
                return False
                
        if "references" in requirements:
            valid_references = sum(1 for rep in player.faction_reputation.values() if rep > 5)
            if valid_references < requirements["references"]:
                return False
                
        return True
        
    def apply_for_housing(self, player, housing_type: str) -> tuple[bool, str]:
        """Apply for housing program."""
        if housing_type not in self.housing_tiers:
            return False, "Invalid housing type"
            
        tier_data = self.housing_tiers[housing_type]
        
        if not self._meets_requirements(player, tier_data["requirements"]):
            return False, "You don't meet the requirements for this housing type"
            
        if housing_type in self.housing_applications:
            return False, "Already have a pending application"
            
        # Calculate approval chance
        base_chance = 0.2
        
        # Positive factors
        if player.has_item("id_card"):
            base_chance += 0.2
        if player.job["title"]:
            base_chance += 0.2
        if player.hygiene > 60:
            base_chance += 0.1
        if player.reputation["services"] > 5:
            base_chance += 0.2
            
        # Negative factors
        if player.has_infection:
            base_chance -= 0.1
        if player.heat > 50:
            base_chance -= 0.2
            
        self.housing_applications[housing_type] = {
            "submitted_date": datetime.now(),
            "review_period": 14,
            "approval_chance": base_chance,
            "status": "pending",
            "tier_data": tier_data
        }
        
        return True, f"Application submitted. Check back in {14} days"
        
    def check_applications(self, player) -> List[str]:
        """Process pending housing applications."""
        messages = []
        
        for program, application in list(self.housing_applications.items()):
            if application["status"] == "pending":
                days_pending = (datetime.now() - application["submitted_date"]).days
                
                if days_pending >= application["review_period"]:
                    if random.random() < application["approval_chance"]:
                        application["status"] = "approved"
                        player.housing_prospects += 25
                        player.housing_status = program
                        
                        # Apply housing quality effects
                        tier_data = application["tier_data"]
                        quality_bonus = tier_data["quality"] * 5
                        player.mental += quality_bonus
                        player.hygiene += quality_bonus
                        
                        messages.append(f"Your application for {program} has been approved!")
                    else:
                        application["status"] = "rejected"
                        messages.append(f"Your application for {program} was rejected.")
                        
        return messages
        
    def process_eviction(self, player, reason: str) -> str:
        """Handle eviction process."""
        if reason == "rent_unpaid" and player.money >= 500:
            return "Paid outstanding rent to avoid eviction"
            
        player.housing_prospects -= 20
        player.mental -= 15
        player.dignity -= 10
        player.housing_status = "homeless"
        
        # Add to eviction record
        self.eviction_notices[datetime.now()] = reason
        
        return "You have been evicted. You'll need to find somewhere else to stay."
        
    def get_housing_status_effects(self, player) -> Dict:
        """Calculate effects of current housing status."""
        if player.housing_status == "homeless":
            return {
                "health_mod": 0.8,
                "mental_mod": 0.7,
                "energy_recovery": 0.5,
                "hygiene_decay": 2.0
            }
            
        tier_data = self.housing_tiers.get(player.housing_status)
        if tier_data:
            quality = tier_data["quality"]
            return {
                "health_mod": 1.0 + (quality * 0.1),
                "mental_mod": 1.0 + (quality * 0.1),
                "energy_recovery": 1.0 + (quality * 0.2),
                "hygiene_decay": 1.0 - (quality * 0.1)
            }
            
        return {
            "health_mod": 1.0,
            "mental_mod": 1.0,
            "energy_recovery": 1.0,
            "hygiene_decay": 1.0
        }
