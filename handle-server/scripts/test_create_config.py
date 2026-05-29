#!/usr/bin/env python3

"""Unit tests for create_config.py

Run tests locally with:
    python -m unittest test_create_config.py
    or
    python test_create_config.py
"""

import unittest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
import subprocess
import base64

# Import functions from create_config
from create_config import (
    format_admin_list,
    format_auto_homed_prefixes,
    build_config,
    convert_pem_to_dsa,
    parse_jdbc_url,
    provision_client_pubkey,
    render_template,
    main
)


class TestFormatFunctions(unittest.TestCase):
    """Test pure formatting functions"""

    def test_format_admin_list_empty(self):
        """Test formatting empty admin list"""
        self.assertEqual(format_admin_list(""), "")
        self.assertEqual(format_admin_list(None), "")

    def test_format_admin_list_single(self):
        """Test formatting single admin"""
        result = format_admin_list("300:TEST/ADMIN")
        self.assertEqual(result, '"300:TEST/ADMIN"')

    def test_format_admin_list_multiple(self):
        """Test formatting multiple admins"""
        result = format_admin_list("300:TEST/ADMIN1 300:TEST/ADMIN2")
        self.assertEqual(result, '"300:TEST/ADMIN1" "300:TEST/ADMIN2"')

    def test_format_admin_list_with_spaces(self):
        """Test formatting with extra spaces"""
        result = format_admin_list("  300:TEST/ADMIN1   300:TEST/ADMIN2  ")
        self.assertEqual(result, '"300:TEST/ADMIN1" "300:TEST/ADMIN2"')

    def test_format_auto_homed_prefixes_empty(self):
        """Test formatting empty prefixes returns None"""
        self.assertIsNone(format_auto_homed_prefixes(""))
        self.assertIsNone(format_auto_homed_prefixes(None))

    def test_format_auto_homed_prefixes_single(self):
        """Test formatting single prefix"""
        result = format_auto_homed_prefixes("TEST")
        self.assertEqual(result, '"TEST"')

    def test_format_auto_homed_prefixes_multiple(self):
        """Test formatting multiple prefixes"""
        result = format_auto_homed_prefixes("TEST PREFIX2 0.NA/TEST")
        self.assertEqual(result, '"TEST" "PREFIX2" "0.NA/TEST"')


class TestBuildConfig(unittest.TestCase):
    """Test configuration building logic"""

    def test_build_config_defaults(self):
        """Test building config with default values"""
        env_vars = {}
        config = build_config(env_vars)

        # Test some key defaults
        self.assertEqual(config["BIND_ADDRESS"], "0.0.0.0")
        self.assertEqual(config["NUM_THREADS"], "15")
        self.assertEqual(config["BIND_PORT"], "2641")
        self.assertEqual(config["LOG_ACCESSES"], "yes")
        self.assertEqual(config["MAX_SESSION_TIME"], "86400000")
        self.assertEqual(config["NO_UDP_RESOLUTION"], "yes")
        self.assertEqual(config["SQL_DRIVER"], "org.postgresql.Driver")
        self.assertEqual(config["SQL_LOGIN"], "postgres")

    def test_build_config_custom_values(self):
        """Test building config with custom environment values"""
        env_vars = {
            "BIND_ADDRESS": "127.0.0.1",
            "NUM_THREADS": "20",
            "SERVER_ADMINS": "300:TEST/ADMIN1 300:TEST/ADMIN2",
            "NO_UDP_RESOLUTION": "no",
            "SITE_DESCRIPTION": "My Test Server"
        }
        config = build_config(env_vars)

        self.assertEqual(config["BIND_ADDRESS"], "127.0.0.1")
        self.assertEqual(config["NUM_THREADS"], "20")
        self.assertEqual(config["SERVER_ADMINS"], '"300:TEST/ADMIN1" "300:TEST/ADMIN2"')
        self.assertEqual(config["NO_UDP_RESOLUTION"], "no")
        self.assertEqual(config["SITE_DESCRIPTION"], "My Test Server")

    def test_build_config_auto_homed_prefixes_default(self):
        """Test AUTO_HOMED_PREFIXES defaults to TEST"""
        env_vars = {}
        config = build_config(env_vars)
        self.assertEqual(config["AUTO_HOMED_PREFIXES"], '"TEST"')

    def test_build_config_auto_homed_prefixes_custom(self):
        """Test custom AUTO_HOMED_PREFIXES"""
        env_vars = {"AUTO_HOMED_PREFIXES": "PREFIX1 PREFIX2"}
        config = build_config(env_vars)
        self.assertEqual(config["AUTO_HOMED_PREFIXES"], '"PREFIX1" "PREFIX2"')

    def test_build_config_auto_homed_prefixes_empty(self):
        """Test empty AUTO_HOMED_PREFIXES"""
        env_vars = {"AUTO_HOMED_PREFIXES": ""}
        config = build_config(env_vars)
        self.assertIsNone(config["AUTO_HOMED_PREFIXES"])

    def test_build_config_key_encoding(self):
        """Test that PEM keys are properly encoded as bytes"""
        env_vars = {
            "SERVER_PRIVATE_KEY_PEM": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            "SERVER_PUBLIC_KEY_PEM": "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----"
        }
        config = build_config(env_vars)

        self.assertIsInstance(config["SERVER_PRIVATE_KEY_PEM"], bytes)
        self.assertIsInstance(config["SERVER_PUBLIC_KEY_PEM"], bytes)
        self.assertEqual(config["SERVER_PRIVATE_KEY_PEM"].decode("ASCII"), env_vars["SERVER_PRIVATE_KEY_PEM"])


class TestConvertPemToDsa(unittest.TestCase):
    """Test PEM to DSA conversion function"""

    @patch('subprocess.Popen')
    def test_convert_pem_to_dsa_success(self, mock_popen):
        """Test successful key conversion"""
        # Mock successful subprocess execution
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'dsa_key_data', b'')
        mock_process.returncode = 0
        mock_popen.return_value.__enter__.return_value = mock_process

        result = convert_pem_to_dsa(b'pem_data', '/path/to/hdl-convert-key')

        self.assertEqual(result, b'dsa_key_data')
        mock_popen.assert_called_once_with(
            ['/path/to/hdl-convert-key'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        mock_process.communicate.assert_called_once_with(input=b'pem_data')

    @patch('subprocess.Popen')
    def test_convert_pem_to_dsa_failure(self, mock_popen):
        """Test key conversion failure raises exception"""
        # Mock failed subprocess execution
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b'', b'conversion failed')
        mock_process.returncode = 1
        mock_popen.return_value.__enter__.return_value = mock_process

        with self.assertRaises(subprocess.CalledProcessError):
            convert_pem_to_dsa(b'invalid_pem', '/path/to/hdl-convert-key')


class TestRenderTemplate(unittest.TestCase):
    """Test template rendering function"""

    @patch('builtins.open', mock_open())
    def test_render_template(self):
        """Test template rendering to file"""
        # Mock Jinja2 environment and template
        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_template.render.return_value = "rendered content"
        mock_env.get_template.return_value = mock_template

        config = {"TEST_VAR": "test_value"}

        render_template("test.jinja", "/path/to/output", config, mock_env)

        # Verify template was loaded and rendered
        mock_env.get_template.assert_called_once_with("test.jinja")
        mock_template.render.assert_called_once_with(config)

        # Verify file was opened for writing and content written
        open.assert_called_once_with("/path/to/output", "w")
        open().write.assert_called_once_with("rendered content")


class TestMainFunction(unittest.TestCase):
    """Test main orchestration function"""

    @patch('jinja2.Environment')
    @patch('create_config.build_config')
    @patch('create_config.convert_pem_to_dsa')
    @patch('builtins.open', mock_open())
    @patch('create_config.render_template')
    def test_main_success(self, mock_render, mock_convert, mock_build_config, mock_jinja_env):
        """Test successful main execution"""
        # Mock config building
        mock_config = {
            "SERVER_PRIVATE_KEY_PEM": b"private_pem",
            "SERVER_PUBLIC_KEY_PEM": b"public_pem"
        }
        mock_build_config.return_value = mock_config

        # Mock key conversion
        mock_convert.side_effect = [b"private_dsa", b"public_dsa"]

        # Mock Jinja environment
        mock_env_instance = MagicMock()
        mock_jinja_env.return_value = mock_env_instance

        # Run main function
        with tempfile.TemporaryDirectory() as tmpdir:
            main("/handle/bin", tmpdir, "/config")

        # Verify config was built
        mock_build_config.assert_called_once()

        # Verify keys were converted
        self.assertEqual(mock_convert.call_count, 2)

        # Verify templates were rendered
        self.assertEqual(mock_render.call_count, 2)

    @patch('create_config.convert_pem_to_dsa')
    @patch('create_config.build_config')
    @patch('sys.exit')
    def test_main_key_conversion_failure(self, mock_exit, mock_build_config, mock_convert):
        """Test main handles key conversion failures"""
        mock_config = {
            "SERVER_PRIVATE_KEY_PEM": b"invalid_pem",
            "SERVER_PUBLIC_KEY_PEM": b"public_pem"
        }
        mock_build_config.return_value = mock_config

        # Mock key conversion failure on first call (private key)
        mock_convert.side_effect = subprocess.CalledProcessError(1, 'hdl-convert-key')

        with tempfile.TemporaryDirectory() as tmpdir:
            main("/handle/bin", tmpdir)

        # Verify sys.exit was called (should be called once for the key error)
        mock_exit.assert_called_with(1)


class TestIntegration(unittest.TestCase):
    """Integration tests with minimal mocking"""

    def test_build_config_integration(self):
        """Test complete config building with realistic environment"""
        env_vars = {
            "BIND_ADDRESS": "0.0.0.0",
            "SERVER_ADMINS": "300:TEST/ADMIN",
            "REPLICATION_ADMINS": "300:TEST/ADMIN",
            "AUTO_HOMED_PREFIXES": "TEST",
            "SERVER_PRIVATE_KEY_PEM": "-----BEGIN PRIVATE KEY-----\nMIIEvQI...\n-----END PRIVATE KEY-----",
            "SERVER_PUBLIC_KEY_PEM": "-----BEGIN PUBLIC KEY-----\nMIIBIjA...\n-----END PUBLIC KEY-----",
            "SQL_URL": "jdbc:postgresql://postgres:5432/handledb",
            "SITE_DESCRIPTION": "Test Handle Server"
        }

        config = build_config(env_vars)

        # Verify all expected keys exist
        required_keys = [
            "BIND_ADDRESS", "NUM_THREADS", "SERVER_ADMINS",
            "AUTO_HOMED_PREFIXES", "SQL_URL", "SITE_DESCRIPTION"
        ]
        for key in required_keys:
            self.assertIn(key, config)

        # Verify specific values
        self.assertEqual(config["SERVER_ADMINS"], '"300:TEST/ADMIN"')
        self.assertEqual(config["AUTO_HOMED_PREFIXES"], '"TEST"')
        self.assertEqual(config["SQL_URL"], "jdbc:postgresql://postgres:5432/handledb")


class TestClientAdminConfig(unittest.TestCase):
    """Test optional client admin HS_PUBKEY (signature auth) configuration"""

    def test_client_admin_appended_to_server_admins(self):
        """Client admin id is added to SERVER_ADMINS when a pubkey is set"""
        env_vars = {
            "SERVER_ADMINS": "300:TEST/ADMIN",
            "CLIENT_ADMIN_PUBLIC_KEY_PEM":
                "-----BEGIN PUBLIC KEY-----\nx\n-----END PUBLIC KEY-----",
        }
        config = build_config(env_vars)
        self.assertEqual(
            config["SERVER_ADMINS"], '"300:TEST/ADMIN" "301:TEST/ADMIN"'
        )
        self.assertEqual(config["CLIENT_ADMIN_HANDLE"], "301:TEST/ADMIN")
        self.assertIsInstance(config["CLIENT_ADMIN_PUBLIC_KEY_PEM"], bytes)

    def test_custom_client_admin_handle(self):
        """A custom CLIENT_ADMIN_HANDLE controls the added admin id"""
        env_vars = {
            "SERVER_ADMINS": "300:TEST/ADMIN",
            "CLIENT_ADMIN_PUBLIC_KEY_PEM": "pem",
            "CLIENT_ADMIN_HANDLE": "302:TEST/ADMIN",
        }
        config = build_config(env_vars)
        self.assertEqual(
            config["SERVER_ADMINS"], '"300:TEST/ADMIN" "302:TEST/ADMIN"'
        )

    def test_no_client_admin_leaves_server_admins(self):
        """Without a client pubkey, SERVER_ADMINS is unchanged and PEM empty"""
        env_vars = {"SERVER_ADMINS": "300:TEST/ADMIN"}
        config = build_config(env_vars)
        self.assertEqual(config["SERVER_ADMINS"], '"300:TEST/ADMIN"')
        self.assertEqual(config["CLIENT_ADMIN_PUBLIC_KEY_PEM"], b"")

    def test_client_admin_not_duplicated(self):
        """An already-listed client admin id is not added twice"""
        env_vars = {
            "SERVER_ADMINS": "300:TEST/ADMIN 301:TEST/ADMIN",
            "CLIENT_ADMIN_PUBLIC_KEY_PEM": "pem",
        }
        config = build_config(env_vars)
        self.assertEqual(
            config["SERVER_ADMINS"], '"300:TEST/ADMIN" "301:TEST/ADMIN"'
        )

    def test_literal_escapes_in_pubkey_become_newlines(self):
        """Literal \\r\\n escapes (from the compose default) become newlines"""
        env_vars = {
            "SERVER_ADMINS": "300:TEST/ADMIN",
            "CLIENT_ADMIN_PUBLIC_KEY_PEM":
                "-----BEGIN PUBLIC KEY-----\\r\\nBODY\\r\\n"
                "-----END PUBLIC KEY-----",
        }
        config = build_config(env_vars)
        self.assertEqual(
            config["CLIENT_ADMIN_PUBLIC_KEY_PEM"],
            b"-----BEGIN PUBLIC KEY-----\nBODY\n-----END PUBLIC KEY-----",
        )

    def test_real_newlines_in_pubkey_preserved(self):
        """A PEM already using real newlines is passed through unchanged"""
        env_vars = {
            "SERVER_ADMINS": "300:TEST/ADMIN",
            "CLIENT_ADMIN_PUBLIC_KEY_PEM":
                "-----BEGIN PUBLIC KEY-----\nBODY\n-----END PUBLIC KEY-----",
        }
        config = build_config(env_vars)
        self.assertEqual(
            config["CLIENT_ADMIN_PUBLIC_KEY_PEM"],
            b"-----BEGIN PUBLIC KEY-----\nBODY\n-----END PUBLIC KEY-----",
        )


class TestParseJdbcUrl(unittest.TestCase):
    """Test JDBC URL parsing"""

    def test_parse_full_url(self):
        self.assertEqual(
            parse_jdbc_url("jdbc:postgresql://postgres:5432/handledb"),
            ("postgres", 5432, "handledb"),
        )

    def test_parse_default_port(self):
        self.assertEqual(
            parse_jdbc_url("jdbc:postgresql://db/handledb"),
            ("db", 5432, "handledb"),
        )


class TestProvisionClientPubkey(unittest.TestCase):
    """Test HS_PUBKEY provisioning into the SQL storage backend"""

    @patch("create_config.convert_pem_to_dsa")
    def test_provision_upserts_hs_pubkey(self, mock_convert):
        """The converted key blob is upserted at the parsed index/handle"""
        mock_convert.return_value = b"BLOB"

        mock_psycopg2 = MagicMock()
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        # Make Binary identifiable while preserving the wrapped value
        mock_psycopg2.Binary.side_effect = lambda b: ("BIN", b)

        env_vars = {
            "SQL_URL": "jdbc:postgresql://postgres:5432/handledb",
            "SQL_LOGIN": "handleuser",
            "SQL_PASSWD": "handlepass",
        }

        with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
            provision_client_pubkey(
                b"PEM", "301:TEST/ADMIN", "/bin/hdl-convert-key", env_vars
            )

        mock_convert.assert_called_once_with(b"PEM", "/bin/hdl-convert-key")
        mock_psycopg2.connect.assert_called_once_with(
            host="postgres", port=5432, dbname="handledb",
            user="handleuser", password="handlepass",
        )
        _, params = mock_cur.execute.call_args[0]
        self.assertEqual(params[0], ("BIN", b"TEST/ADMIN"))
        self.assertEqual(params[1], 301)
        self.assertEqual(params[2], ("BIN", b"HS_PUBKEY"))
        self.assertEqual(params[3], ("BIN", b"BLOB"))
        mock_conn.close.assert_called_once()


class TestMainClientProvisioning(unittest.TestCase):
    """Test that main wires up client admin provisioning correctly"""

    @patch("create_config.provision_client_pubkey")
    @patch("create_config.render_template")
    @patch("builtins.open", mock_open())
    @patch("create_config.convert_pem_to_dsa")
    @patch("create_config.build_config")
    def test_main_provisions_when_client_key_set(
        self, mock_build, mock_convert, mock_render, mock_provision
    ):
        """provision_client_pubkey is called when a client pubkey is present"""
        mock_build.return_value = {
            "SERVER_PRIVATE_KEY_PEM": b"priv",
            "SERVER_PUBLIC_KEY_PEM": b"pub",
            "CLIENT_ADMIN_PUBLIC_KEY_PEM": b"clientpub",
            "CLIENT_ADMIN_HANDLE": "301:TEST/ADMIN",
        }
        mock_convert.side_effect = [b"privdsa", b"pubdsa"]

        with tempfile.TemporaryDirectory() as tmpdir:
            main("/handle/bin", tmpdir, "/config")

        mock_provision.assert_called_once()
        args = mock_provision.call_args[0]
        self.assertEqual(args[0], b"clientpub")
        self.assertEqual(args[1], "301:TEST/ADMIN")

    @patch("create_config.provision_client_pubkey")
    @patch("create_config.render_template")
    @patch("builtins.open", mock_open())
    @patch("create_config.convert_pem_to_dsa")
    @patch("create_config.build_config")
    def test_main_skips_provision_without_client_key(
        self, mock_build, mock_convert, mock_render, mock_provision
    ):
        """provision_client_pubkey is not called when no client pubkey is set"""
        mock_build.return_value = {
            "SERVER_PRIVATE_KEY_PEM": b"priv",
            "SERVER_PUBLIC_KEY_PEM": b"pub",
            "CLIENT_ADMIN_PUBLIC_KEY_PEM": b"",
            "CLIENT_ADMIN_HANDLE": "301:TEST/ADMIN",
        }
        mock_convert.side_effect = [b"privdsa", b"pubdsa"]

        with tempfile.TemporaryDirectory() as tmpdir:
            main("/handle/bin", tmpdir, "/config")

        mock_provision.assert_not_called()


if __name__ == '__main__':
    unittest.main()
