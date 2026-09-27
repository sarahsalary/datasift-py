from typing import List, Optional, TypedDict
from datasift import Data

class User(TypedDict):
    name: str
    age: int
    email: Optional[str]

(
    Data("users.json")
    .expect(List[User])
    .filter(age__gt=30)
    .to("adults.csv")
)