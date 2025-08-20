from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class UserResponse(BaseModel):
    id: str
    is_subscribed: bool
    guesses_left: int
    last_guess_date: Optional[datetime] = None
    last_time_guessed_right: Optional[datetime] = None
    guesses: Dict[str, int] = {} 
    subscription_start_date: Optional[datetime] = None
    subscription_end_date_net: Optional[datetime] = None
    subscription_end_date_gross: Optional[datetime] = None
    agree_to_conditions_and_terms: Optional[datetime] = None
    subscription_id: Optional[str] = None
    monthly_payment: Optional[float] = None
    payment_history: List[Dict[str, Any]] = []

class UserUpdateRequest(BaseModel):
    is_subscribed: Optional[bool] = None
    guesses_left: Optional[int] = None
    last_guess_date: Optional[datetime] = None
    last_time_guessed_right: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date_net: Optional[datetime] = None
    subscription_end_date_gross: Optional[datetime] = None
    agree_to_conditions_and_terms: Optional[datetime] = None
    subscription_id: Optional[str] = None
    monthly_payment: Optional[float] = None
    payment_history: Optional[List[Dict[str, Any]]] = None