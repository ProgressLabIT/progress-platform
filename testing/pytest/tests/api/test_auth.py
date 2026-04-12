"""Auth API migration tests.

Migrated from:
- testing/test-reqres-api/helloTest.js (MOCHA-02)
- testing/test-reqres-api/userTest.js (MOCHA-01)
- testing/robot-test/tests/authentication/login.robot (ROBOT-01)
"""
import pytest


class TestHelloEndpoint:
    """GET /api/hello smoke test — migrated from: helloTest.js (MOCHA-02)."""

    @pytest.mark.asyncio
    async def test_hello_returns_hi(self, client):
        """Given the API is running, when GET /api/hello is called, then it returns 200 with body 'Hi!'."""
        response = await client.get("/api/hello")
        assert response.status_code == 200
        assert response.json() == "Hi!"


class TestAuthLifecycle:
    """Full auth lifecycle — migrated from: userTest.js (MOCHA-01), login.robot (ROBOT-01).

    Each test is self-contained due to per-function truncate_collections autouse fixture.
    Helper methods perform common auth setup within each test.
    """

    @staticmethod
    async def _authenticate(client, username, password="test"):
        """Perform POST /api/auth and return (status_code, body, access_token)."""
        response = await client.post(
            "/api/auth",
            data={"username": username, "password": password},
        )
        body = response.json()
        access_token = body.get("access_token")
        return response.status_code, body, access_token

    @staticmethod
    async def _start_session(client, user_key, access_token):
        """Perform POST /api/session and return (status_code, body, session_key)."""
        response = await client.post(
            "/api/session",
            json={"user_key": user_key},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        body = response.json()
        session_key = body.get("detail", {}).get("session_key") if response.status_code == 200 else None
        return response.status_code, body, session_key

    @pytest.mark.asyncio
    async def test_01_no_token_returns_401(self, client):
        """Given no auth token, when GET /api/whoami is called, then it returns 401.
        Migrated from: userTest.js 'should not recognize without a token', login.robot 'No one is authenticated at startup'.
        """
        response = await client.get("/api/whoami")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_02_successful_auth(self, client, create_user):
        """Given valid credentials, when POST /api/auth is called, then it returns 200 with action 'start_session'.
        Migrated from: userTest.js 'should successfully authenticate with auth post', login.robot 'A valid user can authenticate on API'.
        """
        user = create_user()
        status_code, body, access_token = await self._authenticate(client, user["username"])

        assert status_code == 200
        assert body["status"] == 200
        assert body["detail"]["action"] == "start_session"
        assert access_token is not None

    @pytest.mark.asyncio
    async def test_03_start_session(self, client, create_user):
        """Given a valid auth token, when POST /api/session is called with user_key, then it returns 200 with session data.
        Migrated from: userTest.js 'should be able to start a session', login.robot 'A valid user can start a session'.
        """
        user = create_user()
        _, _, access_token = await self._authenticate(client, user["username"])

        status_code, body, session_key = await self._start_session(client, user["_key"], access_token)

        assert status_code == 200
        assert body["status"] == 200
        assert body["detail"]["scope"] is not None
        assert session_key is not None

    @pytest.mark.asyncio
    async def test_04_whoami_with_token(self, client, create_user):
        """Given a valid auth token, when GET /api/whoami is called, then it returns 200 with 'cookie is valid'.
        Migrated from: userTest.js 'should be able to recognize the token'.
        """
        user = create_user()
        _, _, access_token = await self._authenticate(client, user["username"])

        response = await client.get(
            "/api/whoami",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "cookie is valid"

    @pytest.mark.asyncio
    async def test_05_job_assignment(self, client, create_user):
        """Given an authenticated session, when GET /api/job-assignment is called, then it returns 200.
        Migrated from: userTest.js 'should be able to retrieve job assignment'.
        """
        user = create_user()
        _, _, access_token = await self._authenticate(client, user["username"])
        await self._start_session(client, user["_key"], access_token)

        response = await client.get(
            "/api/job-assignment",
            params={"user_key": user["_key"]},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == 200

    @pytest.mark.asyncio
    async def test_06_close_session(self, client, create_user):
        """Given an active session, when DELETE /api/session/{key} is called, then it returns 200 'Session closed successfully'.
        Migrated from: userTest.js 'should be able to close the session'.
        """
        user = create_user()
        _, _, access_token = await self._authenticate(client, user["username"])
        _, _, session_key = await self._start_session(client, user["_key"], access_token)

        response = await client.request(
            "DELETE",
            f"/api/session/{session_key}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["detail"] == "Session closed successfully"

    @pytest.mark.asyncio
    async def test_07_expired_session_cannot_start(self, client, create_user):
        """Given a closed/revoked session, when POST /api/session is called with the old token, then it returns 401.
        Migrated from: userTest.js 'should not be able to start a session again'.
        """
        user = create_user()
        _, _, access_token = await self._authenticate(client, user["username"])
        _, _, session_key = await self._start_session(client, user["_key"], access_token)

        # Close the session (this revokes the token)
        await client.request(
            "DELETE",
            f"/api/session/{session_key}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Try to start a new session with the revoked token
        status_code, _, _ = await self._start_session(client, user["_key"], access_token)
        assert status_code == 401

    @pytest.mark.asyncio
    async def test_08_wrong_credentials(self, client):
        """Given wrong credentials, when POST /api/auth is called, then it returns 401.
        Migrated from: userTest.js 'should not be able to authenticate with wrong credential'.
        """
        response = await client.post(
            "/api/auth",
            data={"username": "nonexistent_user", "password": "wrong_password"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_09_re_auth_after_close(self, client, create_user):
        """Given a previously closed session, when POST /api/auth is called with valid creds, then it returns 200 with action 'start_session'.
        Migrated from: userTest.js 'should be able to authenticate again'.
        """
        user = create_user()
        # First auth + session + close
        _, _, access_token = await self._authenticate(client, user["username"])
        _, _, session_key = await self._start_session(client, user["_key"], access_token)
        await client.request(
            "DELETE",
            f"/api/session/{session_key}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Re-authenticate
        status_code, body, new_token = await self._authenticate(client, user["username"])
        assert status_code == 200
        assert body["status"] == 200
        assert body["detail"]["action"] == "start_session"
        assert new_token is not None

    @pytest.mark.asyncio
    async def test_10_double_auth_issues_new_token(self, client, create_user):
        """Given an already-authenticated user, when POST /api/auth is called a second time, then both return 200 and the second token is valid.
        Migrated from: userTest.js 'should be able to authenticate twice' + 'second cookie should be valid'.
        """
        user = create_user()
        # First auth
        status1, _, token1 = await self._authenticate(client, user["username"])
        assert status1 == 200

        # Second auth — endpoint closes any existing active sessions for this user
        status2, _, token2 = await self._authenticate(client, user["username"])
        assert status2 == 200
        assert token2 != token1  # New token issued

        # Second token should be valid for whoami
        whoami_resp = await client.get(
            "/api/whoami",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert whoami_resp.status_code == 200
        assert whoami_resp.json()["message"] == "cookie is valid"

    @pytest.mark.asyncio
    async def test_11_first_token_revoked_on_re_auth(self, client, create_user):
        """Given a user who authenticates twice, when whoami is called with the first token, then it returns 401.
        Investigates the commented-out userTest.js 'first cookie should not be valid anymore' scenario.
        The auth endpoint closes active sessions on re-auth (auth.py:59-66), revoking the first token.
        """
        user = create_user()
        # First auth
        _, _, token1 = await self._authenticate(client, user["username"])

        # Second auth — revokes first token via close_session
        _, _, token2 = await self._authenticate(client, user["username"])

        # First token should now be revoked
        whoami_resp = await client.get(
            "/api/whoami",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert whoami_resp.status_code == 401
