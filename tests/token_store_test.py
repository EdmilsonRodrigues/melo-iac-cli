import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from melo_iac_cli.auth.token_store import TokenStore


class TokenStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "credentials"
        self.token = "abcd1234"

    def test_load_returns_saved_token(self) -> None:
        TokenStore(path=self.path).save(self.token)
        loaded_token = TokenStore(path=self.path).load()

        self.assertEqual(loaded_token, self.token)

    def test_load_returns_none_when_no_token_saved(self) -> None:
        loaded_token = TokenStore(path=self.path).load()

        self.assertIsNone(loaded_token)

    def test_load_returns_none_after_clear(self) -> None:
        TokenStore(path=self.path).save(self.token)
        TokenStore(path=self.path).clear()
        loaded_token = TokenStore(path=self.path).load()

        self.assertIsNone(loaded_token)

    def test_clear_does_not_fail_when_no_token_saved(self) -> None:
        TokenStore(path=self.path).clear()
        loaded_token = TokenStore(path=self.path).load()

        self.assertIsNone(loaded_token)

    def test_save_creates_file_readable_only_by_owner(self) -> None:
        TokenStore(path=self.path).save(self.token)

        mode = stat.S_IMODE(self.path.stat().st_mode)
        self.assertEqual(mode, 0o600)

    def test_save_creates_missing_parent_directory(self) -> None:
        path = self.path.parent / "melo-iac" / "credentials"

        TokenStore(path=path).save(self.token)

        self.assertEqual(TokenStore(path=path).load(), self.token)

    def test_save_never_exposes_token_with_wider_permissions(self) -> None:
        # Records the file mode whenever a chmod is about to run: if the
        # token is already on disk at that point, it was exposed until then.
        exposed: list[int] = []
        real_chmod = Path.chmod

        def spy_chmod(path: Path, mode: int, **kwargs: bool) -> None:
            if path.exists() and path.read_text(encoding="utf-8"):
                current = stat.S_IMODE(path.stat().st_mode)
                if current != 0o600:
                    exposed.append(current)
            real_chmod(path, mode, **kwargs)

        old_umask = os.umask(0o022)
        self.addCleanup(os.umask, old_umask)

        with mock.patch.object(Path, "chmod", spy_chmod):
            TokenStore(path=self.path).save(self.token)

        self.assertEqual(exposed, [], "token was readable by others")
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)

    def test_save_replaces_existing_token(self) -> None:
        self.path.write_text("old-token", encoding="utf-8")
        self.path.chmod(0o644)

        TokenStore(path=self.path).save(self.token)

        self.assertEqual(TokenStore(path=self.path).load(), self.token)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
