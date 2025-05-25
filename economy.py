
"""
Economy system for Hard Times: Ottawa.
Handles shops, trading, and job system.
"""
import random
from typing import Dict, List, Optional

class Shop:
    def __init__(self, name: str, location: str, base_prices: Dict[str, float]):
        self.name = name
        self.location = location
        self.base_prices = base_prices
        self.current_prices = base_prices.copy()
        self.price_volatility = 0.2  # 20% max price fluctuation
        
    def update_prices(self, local_demand: float, global_economy: float):
        """Update prices based on demand and economic factors."""
        for item_id in self.current_prices:
            modifier = 1.0
            # Local demand affects prices (0.8 to 1.2 range)
            modifier *= (0.8 + (local_demand * 0.4))
            # Global economy affects prices (0.9 to 1.1 range)
            modifier *= (0.9 + (global_economy * 0.2))
            # Random daily fluctuation
            modifier *= random.uniform(1 - self.price_volatility, 1 + self.price_volatility)
            
            self.current_prices[item_id] = round(self.base_prices[item_id] * modifier, 2)

class BlackMarket:
    def __init__(self):
        self.traders: Dict[str, Dict] = {}
        self.contraband_items: Dict[str, float] = {}
        self.heat_level = 0  # Police attention
        
    def add_trader(self, trader_id: str, name: str, specialty: str, trustworthiness: float):
        self.traders[trader_id] = {
            "name": name,
            "specialty": specialty,
            "trustworthiness": trustworthiness,
            "inventory": {}
        }
        
    def get_deal(self, item_id: str, trader_id: str) -> tuple[float, str]:
        """Get price and risk for a black market deal."""
        trader = self.traders.get(trader_id)
        if not trader:
            return 0, "Trader not found"
            
        base_price = self.contraband_items.get(item_id, 0)
        if base_price == 0:
            return 0, "Item not available"
            
        risk_factor = (1 - trader["trustworthiness"]) * random.uniform(0.8, 1.2)
        final_price = base_price * (1 + risk_factor)
        
        return round(final_price, 2), "Deal available"

class JobSystem:
    def __init__(self):
        self.available_jobs: Dict[str, Dict] = {}
        self.job_requirements: Dict[str, Dict] = {}
        self.pay_rates: Dict[str, float] = {
            "day_labor": 15.0,
            "temp_work": 17.0,
            "skilled_labor": 22.0
        }
        
    def add_job(self, job_id: str, title: str, type_: str, duration: int, requirements: Dict):
        """Add a new job opportunity."""
        self.available_jobs[job_id] = {
            "title": title,
            "type": type_,
            "duration": duration,  # Hours
            "pay_rate": self.pay_rates.get(type_, 15.0),
            "requirements": requirements
        }
        
    def check_eligibility(self, player, job_id: str) -> tuple[bool, str]:
        """Check if player meets job requirements."""
        job = self.available_jobs.get(job_id)
        if not job:
            return False, "Job not found"
            
        reqs = job["requirements"]
        
        if reqs.get("min_hygiene", 0) > player.hygiene:
            return False, "Must improve hygiene"
            
        if reqs.get("skill_requirement"):
            skill_name = reqs["skill_requirement"]["name"]
            skill_level = reqs["skill_requirement"]["level"]
            if player.skills.get(skill_name, 0) < skill_level:
                return False, f"Need {skill_name} level {skill_level}"
                
        return True, "Eligible for job"
        
    def complete_job(self, player, job_id: str) -> tuple[bool, float, str]:
        """Complete a job and receive payment."""
        job = self.available_jobs.get(job_id)
        if not job:
            return False, 0, "Job not found"
            
        eligible, reason = self.check_eligibility(player, job_id)
        if not eligible:
            return False, 0, reason
            
        # Calculate payment
        hours = job["duration"]
        base_pay = job["pay_rate"] * hours
        
        # Performance bonus based on relevant skills
        skill_bonus = 1.0
        if job["type"] == "skilled_labor":
            relevant_skill = player.skills.get(job["requirements"].get("skill_requirement", {}).get("name", ""), 0)
            skill_bonus += (relevant_skill * 0.1)  # 10% bonus per skill level
            
        final_pay = round(base_pay * skill_bonus, 2)
        
        # Apply job effects
        player.energy -= hours * 5  # Energy cost per hour
        player.satiety -= hours * 3  # Lose satiety from working
        player.job_prospects += 2  # Improve job prospects
        
        return True, final_pay, "Job completed successfully"
