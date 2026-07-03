import asyncio
import datetime
from datetime import datetime, timezone
from sqlalchemy import delete
from src.worker.celery_app import celery_app

from src.database.models import ActivationTokenModel, PasswordResetTokenModel, RefreshTokenModel
from src.database.session import AsyncSessionLocal



async def _async_cleanup_activation_tokens():
    """This internal helper function handles the actual async database queries."""
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)

        delete_activation = delete(ActivationTokenModel).where(ActivationTokenModel.expires_at < now)
        delete_password_refresh = delete(PasswordResetTokenModel).where(PasswordResetTokenModel.expires_at < now)
        delete_refresh = delete(RefreshTokenModel).where(RefreshTokenModel.expires_at < now)

        await session.execute(delete_activation)
        await session.execute(delete_password_refresh)
        await session.execute(delete_refresh)

        await session.commit()


@celery_app.task
def cleanup_expired_tokens():
    """Main synchronous entrypoint that Celery Beat calls on its schedule."""
    asyncio.run(_async_cleanup_activation_tokens())

