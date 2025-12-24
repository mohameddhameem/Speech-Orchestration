from enum import Enum

class GetAvailableVoicesResponse200VoicesItemGender(str, Enum):
    FEMALE = "female"
    MALE = "male"
    NEUTRAL = "neutral"

    def __str__(self) -> str:
        return str(self.value)
