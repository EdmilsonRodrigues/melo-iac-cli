from typing import Any, Final

import httpx

from melo_iac_cli.auth.token_store import TokenStore

LOGIN_PATH: Final = "/api/v1/auth/login"
LOGOUT_PATH: Final = "/api/v1/auth/logout"


class AuthError(Exception):
    """Base class for every auth failure the CLI reports to the user."""


class InvalidCredentialsError(AuthError):
    pass


class ServerError(AuthError):
    pass


class ServerUnreachableError(AuthError):
    pass


class AuthService:
    def __init__(self, token_store: TokenStore, client: httpx.Client) -> None:
        self._token_store = token_store
        self._client = client

    def login(self, username: str, password: str) -> None:
        response = self._post(
            LOGIN_PATH, json={"username": username, "password": password}
        )
        if response.status_code == httpx.codes.UNAUTHORIZED:
            raise InvalidCredentialsError
        _raise_for_status(response)

        try:
            token = response.json()["token"]
        except (ValueError, KeyError, TypeError) as e:
            raise ServerError("server response has no token") from e
        self._token_store.save(token)

    def logout(self) -> None:
        token = self._token_store.load()
        if token is None:
            return
        try:
            response = self._post(
                LOGOUT_PATH, headers={"Authorization": f"Bearer {token}"}
            )
            _raise_for_status(response)
        finally:
            # Local logout must always succeed, even if revocation fails.
            self._token_store.clear()

    def _post(
        self,
        path: str,
        *,
        json: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        try:
            return self._client.post(path, json=json, headers=headers)
        except httpx.RequestError as e:
            raise ServerUnreachableError(
                f"could not reach server at {self._client.base_url}"
            ) from e


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_error:
        raise ServerError(f"server returned {response.status_code}")
