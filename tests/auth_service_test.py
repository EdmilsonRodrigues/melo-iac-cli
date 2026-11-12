import json
import tempfile
import unittest
from pathlib import Path

import httpx

from melo_iac_cli.auth.auth_service import (
    AuthService,
    InvalidCredentialsError,
    ServerError,
    ServerUnreachableError,
)
from melo_iac_cli.auth.token_store import TokenStore


class AuthServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.token_store = TokenStore(path=Path(tmp.name) / "credentials")
        self.requests: list[httpx.Request] = []

    def make_service(self, response: httpx.Response) -> AuthService:
        def fake_server(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return response

        client = httpx.Client(
            transport=httpx.MockTransport(fake_server),
            base_url="http://melo.test",
        )

        self.addCleanup(client.close)
        return AuthService(token_store=self.token_store, client=client)

    def make_unreachable_service(self) -> AuthService:
        def down_server(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        client = httpx.Client(
            transport=httpx.MockTransport(down_server),
            base_url="http://melo.test",
        )
        self.addCleanup(client.close)
        return AuthService(token_store=self.token_store, client=client)

    def test_logout_removes_saved_token(self) -> None:
        self.token_store.save("abcd1234")

        self.make_service(httpx.Response(200)).logout()

        self.assertIsNone(self.token_store.load())

    def test_logout_revokes_token_on_server(self) -> None:
        self.token_store.save("abcd1234")

        self.make_service(httpx.Response(204)).logout()

        request = self.requests[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url.path, "/api/v1/auth/logout")
        self.assertEqual(request.headers["Authorization"], "Bearer abcd1234")

    def test_logout_removes_token_even_when_server_fails(self) -> None:
        self.token_store.save("abcd1234")

        with self.assertRaises(ServerError):
            self.make_service(httpx.Response(500)).logout()

        self.assertIsNone(self.token_store.load())

    def test_logout_removes_token_even_when_server_is_unreachable(
        self,
    ) -> None:
        self.token_store.save("abcd1234")

        with self.assertRaises(ServerUnreachableError):
            self.make_unreachable_service().logout()

        self.assertIsNone(self.token_store.load())

    def test_logout_without_saved_token_does_not_call_server(self) -> None:
        self.make_service(httpx.Response(204)).logout()

        self.assertEqual(self.requests, [])

    def test_login_saves_token_returned_by_server(self) -> None:
        service = self.make_service(
            httpx.Response(200, json={"token": "abcd1234"})
        )

        service.login(username="ed", password="secret")

        self.assertEqual(self.token_store.load(), "abcd1234")
        request = self.requests[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url.path, "/api/v1/auth/login")
        self.assertEqual(
            json.loads(request.content),
            {"username": "ed", "password": "secret"},
        )

    def test_login_raises_when_credentials_are_invalid(self) -> None:
        service = self.make_service(httpx.Response(401))

        with self.assertRaises(InvalidCredentialsError):
            service.login(username="ed", password="wrong")

        self.assertIsNone(self.token_store.load())

    def test_login_raises_server_error_on_unexpected_status(self) -> None:
        service = self.make_service(
            httpx.Response(500, json={"error": "internal error"})
        )

        with self.assertRaisesRegex(ServerError, "500"):
            service.login(username="ed", password="secret")

        self.assertIsNone(self.token_store.load())

    def test_login_raises_server_error_when_token_is_missing(self) -> None:
        service = self.make_service(httpx.Response(200, json={}))

        with self.assertRaises(ServerError):
            service.login(username="ed", password="secret")

    def test_login_raises_when_server_is_unreachable(self) -> None:
        with self.assertRaisesRegex(ServerUnreachableError, "melo.test"):
            self.make_unreachable_service().login(
                username="ed", password="secret"
            )
