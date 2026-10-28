"""Unit tests for AuthService — all external I/O is mocked."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest


def _make_user(
    role="reader",
    is_active=True,
    is_email_verified=True,
    hashed_password=None,
    is_first_login=True,
):
    user = MagicMock()
    user.id = 1
    user.uuid = str(uuid.uuid4())
    user.email = "test@example.com"
    user.role = role
    user.is_active = is_active
    user.is_email_verified = is_email_verified
    user.is_first_login = is_first_login
    user.hashed_password = hashed_password or "$2b$12$hash"
    user.reader_profile = None
    user.publisher_profile = None
    return user


@pytest.fixture
def service(mock_db, mock_redis, mock_auth_provider):
    return AuthService(db=mock_db, redis=mock_redis, auth_provider=mock_auth_provider)


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------
class TestRegister:
    @pytest.mark.asyncio
    async def test_duplicate_email_raises_400(self, service, mock_db):
        existing = _make_user()
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=existing)

        with pytest.raises(HTTPException) as exc_info:
            await service.register(
                RegisterRequest(
                    email="test@example.com",
                    password="Secret123!",
                    confirm_password="Secret123!",
                    role="reader",
                    first_name="John",
                    last_name="Doe",
                )
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_new_reader_created(self, service, mock_db, mock_redis):
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=None)
        mock_redis.incr.return_value = 1

        fake_uuid = str(uuid.uuid4())

        async def flush_side_effect():
            # Simulate DB flush assigning uuid and id to the User object
            # The service keeps a reference to 'user' in local scope; we
            # reach it by inspecting the add() calls made so far.
            for call in mock_db.add.call_args_list:
                obj = call.args[0]
                if hasattr(obj, "uuid") and obj.uuid is None:
                    obj.uuid = fake_uuid
                    obj.id = 1

        mock_db.flush = AsyncMock(side_effect=flush_side_effect)

        with (
            patch(
                "app.services.auth_service.hash_password",
                return_value="$2b$12$hashed",
            ),
            patch(
                "app.services.auth_service.generate_and_store_otp",
                new_callable=AsyncMock,
                return_value="123456",
            ),
            patch("app.tasks.email_tasks.send_otp_email") as mock_task,
        ):
            mock_task.delay = MagicMock()

            result = await service.register(
                RegisterRequest(
                    email="new@example.com",
                    password="Secret123!",
                    confirm_password="Secret123!",
                    role="reader",
                    first_name="Jane",
                    last_name="Smith",
                )
            )

        assert result.email == "new@example.com"
        assert result.role == "reader"
        assert result.is_email_verified is False
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_new_publisher_creates_kyc(self, service, mock_db, mock_redis):
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=None)
        mock_redis.incr.side_effect = [1, 2, 3]  # user, publisher, kyc counters

        fake_uuid = str(uuid.uuid4())
        flush_call_count = 0

        async def flush_side_effect():
            nonlocal flush_call_count
            flush_call_count += 1
            for call in mock_db.add.call_args_list:
                obj = call.args[0]
                if hasattr(obj, "uuid") and obj.uuid is None:
                    obj.uuid = fake_uuid
                    obj.id = flush_call_count

        mock_db.flush = AsyncMock(side_effect=flush_side_effect)

        with (
            patch(
                "app.services.auth_service.hash_password",
                return_value="$2b$12$hashed",
            ),
            patch(
                "app.services.auth_service.generate_and_store_otp",
                new_callable=AsyncMock,
                return_value="654321",
            ),
            patch("app.tasks.email_tasks.send_otp_email") as mock_task,
        ):
            mock_task.delay = MagicMock()

            result = await service.register(
                RegisterRequest(
                    email="pub@example.com",
                    password="Secret123!",
                    confirm_password="Secret123!",
                    role="publisher",
                    first_name="Alice",
                    last_name="Books",
                )
            )

        assert result.role == "publisher"
        # add called for user, publisher_profile, kyc_app
        assert mock_db.add.call_count >= 3


# ---------------------------------------------------------------------------
# send_email_otp
# ---------------------------------------------------------------------------
class TestSendEmailOTP:
    @pytest.mark.asyncio
    async def test_user_not_found_raises_404(self, service, mock_db):
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service.send_email_otp("nobody@example.com", "email_verify")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_otp_generated_and_task_fired(self, service, mock_db, mock_redis):
        user = _make_user(is_email_verified=False)
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=user)

        with (
            patch(
                "app.services.auth_service.generate_and_store_otp",
                new_callable=AsyncMock,
                return_value="111222",
            ),
            patch("app.tasks.email_tasks.send_otp_email") as mock_task,
        ):
            mock_task.delay = MagicMock()
            await service.send_email_otp("test@example.com", "email_verify")
            mock_task.delay.assert_called_once_with(
                "test@example.com", "111222", "email_verify"
            )


# ---------------------------------------------------------------------------
# verify_email
# ---------------------------------------------------------------------------
class TestVerifyEmail:
    @pytest.mark.asyncio
    async def test_verify_marks_user_verified(self, service, mock_db, mock_redis):
        user = _make_user(is_email_verified=False)
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=user)

        with (
            patch(
                "app.services.auth_service.verify_otp",
                new_callable=AsyncMock,
            ),
            patch("app.tasks.email_tasks.send_welcome_email") as mock_task,
        ):
            mock_task.delay = MagicMock()
            result = await service.verify_email("test@example.com", "123456")

        assert user.is_email_verified is True
        assert result.next_step == "login"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_publisher_next_step_is_kyc(self, service, mock_db, mock_redis):
        user = _make_user(role="publisher", is_email_verified=False)
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=user)

        with (
            patch("app.services.auth_service.verify_otp", new_callable=AsyncMock),
            patch("app.tasks.email_tasks.send_welcome_email") as mock_task,
        ):
            mock_task.delay = MagicMock()
            result = await service.verify_email("pub@example.com", "999999")

        assert result.next_step == "kyc_required"


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------
class TestLogin:
    @pytest.mark.asyncio
    async def test_unknown_email_raises_401(self, service, mock_db, mock_response):
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service.login("nobody@example.com", "pass", mock_response)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_raises_403(self, service, mock_db, mock_response):
        user = _make_user(is_active=False)
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=user)

        with pytest.raises(HTTPException) as exc_info:
            await service.login("test@example.com", "pass", mock_response)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_unverified_email_raises_403(
        self, service, mock_db, mock_response
    ):
        user = _make_user(is_email_verified=False)
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=user)

        with pytest.raises(HTTPException) as exc_info:
            await service.login("test@example.com", "pass", mock_response)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_wrong_password_raises_401(
        self, service, mock_db, mock_response
    ):
        user = _make_user()
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=user)

        with patch(
            "app.services.auth_service.verify_password", return_value=False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await service.login("test@example.com", "wrong", mock_response)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_successful_login_sets_cookie_returns_token(
        self, service, mock_db, mock_redis, mock_response
    ):
        user = _make_user()
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=user)

        with patch(
            "app.services.auth_service.verify_password", return_value=True
        ):
            result = await service.login("test@example.com", "Secret123!", mock_response)

        assert result.access_token
        assert result.user.email == "test@example.com"
        mock_response.set_cookie.assert_called_once()
        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------
class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_blacklists_token_and_deletes_cookie(
        self, service, mock_redis, mock_response
    ):
        with patch(
            "app.services.auth_service.decode_token",
            return_value={"sub": "some-uuid", "type": "refresh"},
        ):
            await service.logout("fake.refresh.token", mock_response)

        mock_redis.set.assert_called_once()
        mock_response.delete_cookie.assert_called_once()


# ---------------------------------------------------------------------------
# refresh_access_token
# ---------------------------------------------------------------------------
class TestRefreshAccessToken:
    @pytest.mark.asyncio
    async def test_blacklisted_token_raises_401(self, service, mock_redis):
        mock_redis.get.return_value = "some-uuid"

        with pytest.raises(HTTPException) as exc_info:
            await service.refresh_access_token("blacklisted.token.here")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_refresh_returns_new_access_token(
        self, service, mock_db, mock_redis
    ):
        mock_redis.get.return_value = None
        user = _make_user()
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=user)

        with patch(
            "app.services.auth_service.decode_token",
            return_value={"sub": user.uuid, "type": "refresh"},
        ):
            result = await service.refresh_access_token("valid.refresh.token")

        assert result.access_token


# ---------------------------------------------------------------------------
# verify_reset_otp
# ---------------------------------------------------------------------------
class TestVerifyResetOTP:
    @pytest.mark.asyncio
    async def test_returns_session_token_on_valid_otp(
        self, service, mock_redis
    ):
        with patch(
            "app.services.auth_service.verify_otp", new_callable=AsyncMock
        ):
            result = await service.verify_reset_otp("test@example.com", "123456")

        assert result.reset_session_token
        assert result.expires_in == 600
        mock_redis.set.assert_called_once()


# ---------------------------------------------------------------------------
# reset_password
# ---------------------------------------------------------------------------
class TestResetPassword:
    @pytest.mark.asyncio
    async def test_expired_session_raises_400(self, service, mock_redis):
        mock_redis.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.reset_password("expired_token", "NewPass123!")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_valid_session_updates_password(
        self, service, mock_db, mock_redis
    ):
        mock_redis.get.return_value = "test@example.com"
        user = _make_user()
        mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=user)

        with patch(
            "app.services.auth_service.hash_password", return_value="$2b$12$new"
        ):
            await service.reset_password("valid_session_token", "NewPass123!")

        assert user.hashed_password == "$2b$12$new"
        mock_redis.delete.assert_called_once()
        mock_db.commit.assert_called_once()
