"""Shared serialization for commands that mutate player state."""

from functools import wraps


def serialized(callback):
    """Run a command under the Adventure cog's shared profile/database lock."""
    @wraps(callback)
    async def wrapped(self, ctx, *args, **kwargs):
        game = self.bot.get_cog("Adventure")
        if game is None:
            return await callback(self, ctx, *args, **kwargs)
        async with game.lock:
            return await callback(self, ctx, *args, **kwargs)
    return wrapped
