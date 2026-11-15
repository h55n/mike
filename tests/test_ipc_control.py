import os
import unittest
from unittest.mock import patch

from src.engine import MikeEngine
from src.ipc_control import ControlMessageCodec


class ControlMessageCodecTests(unittest.TestCase):
    def setUp(self):
        self.secret = bytes(range(32))
        self.sender = ControlMessageCodec(self.secret)
        self.receiver = ControlMessageCodec(self.secret)

    def test_authenticated_commands_round_trip_once(self):
        for command in (b"KILL_MIC", b"WAKE_MIC"):
            with self.subTest(command=command):
                receiver = ControlMessageCodec(self.secret)
                message = self.sender.encode(command)

                self.assertEqual(receiver.decode(message), command)
                self.assertIsNone(receiver.decode(message))

    def test_wrong_secret_does_not_authorize_a_command(self):
        message = self.sender.encode(b"WAKE_MIC")
        receiver = ControlMessageCodec(b"x" * 32)

        self.assertIsNone(receiver.decode(message))

    def test_tampered_command_or_signature_is_rejected(self):
        message = self.sender.encode(b"KILL_MIC")
        parts = message.split(b" ")
        parts[1] = b"WAKE_MIC"
        self.assertIsNone(self.receiver.decode(b" ".join(parts)))

        parts = message.split(b" ")
        parts[3] = b"0" * 64
        self.assertIsNone(self.receiver.decode(b" ".join(parts)))

    def test_malformed_messages_are_rejected(self):
        message = self.sender.encode(b"KILL_MIC")
        _, _, _, signature = message.split(b" ")
        malformed_messages = (
            b"",
            b"MIKE/2 KILL_MIC " + b"0" * 32 + b" " + signature,
            b"MIKE/1 KILL_MIC not-hex " + signature,
            b"MIKE/1 KILL_MIC " + b"0" * 32 + b" " + b"0" * 63,
            message + b" extra",
            "MIKE/1 KILL_MIC",
        )

        for malformed in malformed_messages:
            with self.subTest(malformed=malformed):
                self.assertIsNone(self.receiver.decode(malformed))

    def test_replayed_nonce_stays_rejected_after_many_commands(self):
        replayed_message = self.sender.encode(b"KILL_MIC")
        self.assertEqual(self.receiver.decode(replayed_message), b"KILL_MIC")

        for _ in range(600):
            self.assertEqual(
                self.receiver.decode(self.sender.encode(b"WAKE_MIC")), b"WAKE_MIC"
            )

        self.assertIsNone(self.receiver.decode(replayed_message))

    def test_unsigned_sensitive_commands_are_rejected(self):
        self.assertIsNone(self.receiver.decode(b"KILL_MIC"))
        self.assertIsNone(self.receiver.decode(b"WAKE_MIC"))

    def test_dashboard_opening_remains_outside_sensitive_command_codec(self):
        self.assertIsNone(self.receiver.decode(b"OPEN_DASHBOARD"))

    def test_dashboard_child_receives_control_secret_without_parent_leak(self):
        secret = bytes(range(32))
        engine = MikeEngine.__new__(MikeEngine)
        engine.control_secret = secret

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MIKE_CONTROL_SECRET", None)
            with patch("subprocess.Popen") as popen:
                engine.open_dashboard()

            child_env = popen.call_args.kwargs["env"]
            self.assertEqual(child_env["MIKE_CONTROL_SECRET"], secret.hex())
            self.assertNotIn("MIKE_CONTROL_SECRET", os.environ)

    def test_dashboard_child_does_not_inherit_a_stale_control_secret(self):
        engine = MikeEngine.__new__(MikeEngine)
        engine.control_secret = None

        with patch.dict(os.environ, {"MIKE_CONTROL_SECRET": "stale"}):
            with patch("subprocess.Popen") as popen:
                engine.open_dashboard()

            child_env = popen.call_args.kwargs["env"]
            self.assertNotIn("MIKE_CONTROL_SECRET", child_env)

    def test_unsupported_commands_and_short_secrets_are_rejected(self):
        for command in (b"OPEN_DASHBOARD", b"UNKNOWN"):
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    self.sender.encode(command)

        with self.assertRaises(ValueError):
            ControlMessageCodec(b"short")

        with self.assertRaises(ValueError):
            self.sender.encode(bytearray(b"KILL_MIC"))


if __name__ == "__main__":
    unittest.main()
