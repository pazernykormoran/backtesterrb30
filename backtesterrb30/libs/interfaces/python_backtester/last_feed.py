from typing import List

from pydantic import BaseModel


class LastFeed(BaseModel):
    last_feed: List
