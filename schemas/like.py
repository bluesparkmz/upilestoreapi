from pydantic import BaseModel


class LikeResponse(BaseModel):
    likes_count: int
    liked_by_me: bool


class LikeActionResponse(BaseModel):
    message: str
    likes_count: int
    liked_by_me: bool
