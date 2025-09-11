from typing import List, Dict, Optional

class Storage:
    async def init(self) -> None: ...
    async def seed_pois(self, pois: List[Dict]) -> None: ...
    async def save_location(self, user_id: str, lat: float, lon: float,
                            ttl_days: int, profile_type: Optional[str],
                            has_mobility_issues: bool, age_range: Optional[str]) -> None: ...
    async def top_pois(self, lat: float, lon: float, radius_m:int,
                       pmr:bool, age_range:Optional[str], k:int) -> List[Dict]: ...
    async def summary(self) -> Dict: ...
    async def prune_expired(self) -> None: ...

    async def ensure_user(self, user_id: str,
                          profile_type: Optional[str] = None,
                          has_mobility_issues: Optional[bool] = None,
                          age_range: Optional[str] = None) -> None:
        raise NotImplementedError

    async def save_chat_turn(self, user_id: str, prompt: str, response: str,
                             model: Optional[str] = None) -> str:
        raise NotImplementedError

    async def get_chat_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        raise NotImplementedError

    async def get_chat_turn(self, turn_id: str) -> Optional[Dict]:
        raise NotImplementedError
