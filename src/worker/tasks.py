"""
Celery background tasks for the Online Cinema platform.

Tasks are executed by the Celery worker and scheduled by Celery Beat.
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete

from src.database.models import (
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
)
from src.database.session import AsyncSessionLocal
from src.worker.celery_app import celery_app


async def _async_cleanup_activation_tokens():
    """
    Delete all expired tokens from the database.

    Removes records where expires_at < current UTC time from:
    - activation_tokens
    - password_reset_tokens
    - refresh_tokens
    """
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)

        delete_activation = delete(ActivationTokenModel).where(
            ActivationTokenModel.expires_at < now
        )
        delete_password_refresh = delete(PasswordResetTokenModel).where(
            PasswordResetTokenModel.expires_at < now
        )
        delete_refresh = delete(RefreshTokenModel).where(
            RefreshTokenModel.expires_at < now
        )

        await session.execute(delete_activation)
        await session.execute(delete_password_refresh)
        await session.execute(delete_refresh)

        await session.commit()


@celery_app.task(name="src.worker.tasks.cleanup_expired_tokens")
def cleanup_expired_tokens():
    """
    Celery Beat task: purge expired authentication tokens.

    **Schedule:** every 30 minutes (configured in celery_app.py).

    **Action:** Deletes expired activation, password-reset, and refresh tokens.
    """
    asyncio.run(_async_cleanup_activation_tokens())
