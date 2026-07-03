from datetime import datetime, timezone, timedelta

import pytest
from mypy.typeops import true_only
from sqlalchemy import select
from src.database.models import ActivationTokenModel, UserModel, RefreshTokenModel


@pytest.mark.asyncio
async def test_register_user_success(client):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}

    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == payload["email"]
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_activate_invalid_token(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}

    await client.post("/auth/register", json=payload)
    await db_session.commit()

    response = await client.get("/auth/activate?token=fake-token-123")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_activate_expired_token(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}

    response = await client.post("/auth/register", json=payload)

    user_id = response.json()["id"]

    result = await db_session.execute(
        select(ActivationTokenModel).where(ActivationTokenModel.user_id == user_id)
    )
    db_token = result.scalar_one()

    db_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

    token_string = db_token.token

    await db_session.commit()
    db_session.expunge_all()

    response = await client.get(f"/auth/activate?token={token_string}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Activation token has expired"


@pytest.mark.asyncio
async def test_login_unactivated_user(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}

    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/login", json=payload)

    await db_session.commit()

    assert response.status_code == 401
    assert (
        response.json()["detail"] == "Account not activated. Please verify your email."
    )


@pytest.mark.asyncio
async def test_login_wrong_password(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}

    register = await client.post("/auth/register", json=payload)

    user_id = register.json()["id"]
    result = await db_session.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = result.scalar_one()

    db_user.is_active = True

    await db_session.commit()

    payload["password"] = "WRONG_PASSWORD"

    login = await client.post("/auth/login", json=payload)

    assert login.status_code == 401


@pytest.mark.asyncio
async def test_login_success(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}
    register = await client.post("/auth/register", json=payload)
    user_id = register.json()["id"]
    result = await db_session.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = result.scalar_one()

    db_user.is_active = True

    await db_session.commit()

    response = await client.post("/auth/login", json=payload)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


@pytest.mark.asyncio
async def test_activate_user_success(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}
    register = await client.post("/auth/register", json=payload)
    user_id = register.json()["id"]

    users = await db_session.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = users.scalar_one()

    tokens = await db_session.execute(
        select(ActivationTokenModel).where(ActivationTokenModel.user_id == user_id)
    )
    db_token = tokens.scalar_one()

    response = await client.get(f"/auth/activate?token={db_token.token}")

    await db_session.refresh(db_user)
    db_session.expunge_all()

    assert response.status_code == 200
    assert db_user.is_active is True


@pytest.mark.asyncio
async def test_refresh_token_success(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}
    register = await client.post("/auth/register", json=payload)
    user_id = register.json()["id"]

    users = await db_session.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = users.scalar_one()
    db_user.is_active = True

    await db_session.commit()
    db_session.expunge_all()

    login_response = await client.post("/auth/login", json=payload)

    my_refresh_token = login_response.json()["refresh_token"]

    refresh_payload = {"refresh_token": my_refresh_token}

    response = await client.post("/auth/refresh", json=refresh_payload)

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_refresh_token_invalid(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}
    register = await client.post("/auth/register", json=payload)
    user_id = register.json()["id"]

    users = await db_session.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = users.scalar_one()
    db_user.is_active = True

    await db_session.commit()

    response = await client.post(
        "/auth/refresh", json={"refresh_token": "false_refresh_token"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token"


@pytest.mark.asyncio
async def test_logout_success(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}
    register = await client.post("/auth/register", json=payload)
    user_id = register.json()["id"]

    users = await db_session.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = users.scalar_one()
    db_user.is_active = True

    await db_session.commit()

    login_response = await client.post("/auth/login", json=payload)
    my_access = login_response.json()["access_token"]
    my_refresh = login_response.json()["refresh_token"]

    headers = {"Authorization": f"Bearer {my_access}"}
    response = await client.post(
        f"/auth/logout?refresh_token={my_refresh}", headers=headers
    )

    assert response.status_code == 204

    refresh = await db_session.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.token == my_refresh)
    )
    db_refresh = refresh.scalar_one_or_none()
    assert db_refresh is None


@pytest.mark.asyncio
async def test_logout_unauthorized(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}
    register = await client.post("/auth/register", json=payload)
    user_id = register.json()["id"]

    users = await db_session.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = users.scalar_one()
    db_user.is_active = True

    await db_session.commit()

    headers = {"Authorization": "Bearer fake_token"}
    response = await client.post(
        "/auth/logout?refresh_token=fake_token", headers=headers
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_success(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}
    register = await client.post("/auth/register", json=payload)
    user_id = register.json()["id"]

    users = await db_session.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = users.scalar_one()
    db_user.is_active = True

    await db_session.commit()

    login_response = await client.post("/auth/login", json=payload)
    my_access = login_response.json()["access_token"]
    new_pass_payload = {
        "old_password": "StrongPassword123!",
        "new_password": "EvenStrongerPassword999!",
    }

    headers = {"Authorization": f"Bearer {my_access}"}
    response = await client.post(
        "/auth/change-password?old_password=", json=new_pass_payload, headers=headers
    )

    assert response.status_code == 200

    payload["password"] = "EvenStrongerPassword999!"
    response = await client.post("/auth/login", json=payload)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old_password(client, db_session):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}
    register = await client.post("/auth/register", json=payload)
    user_id = register.json()["id"]

    users = await db_session.execute(select(UserModel).where(UserModel.id == user_id))
    db_user = users.scalar_one()
    db_user.is_active = True

    await db_session.commit()

    login_response = await client.post("/auth/login", json=payload)
    my_access = login_response.json()["access_token"]
    new_pass_payload = {
        "old_password": "WRONG_OLD_PASSWORD!",
        "new_password": "EvenStrongerPassword999!",
    }

    headers = {"Authorization": f"Bearer {my_access}"}
    response = await client.post(
        "/auth/change-password", json=new_pass_payload, headers=headers
    )

    assert response.status_code == 401
