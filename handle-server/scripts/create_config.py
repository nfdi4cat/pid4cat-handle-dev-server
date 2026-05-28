#!/usr/bin/env python3

"""This script takes the configuration templates and creates new ones for the
handle server based upon environment variables using Jinja2 templates"""

import sys
import os
import subprocess
import base64
from jinja2 import Environment, FileSystemLoader, select_autoescape


def format_admin_list(admin_string):
    """Format space-separated admin list into quoted format for config"""
    if not admin_string:
        return ""
    return " ".join(['"%s"' % s for s in admin_string.split(" ") if s])


def format_auto_homed_prefixes(prefixes_string):
    """Format auto-homed prefixes, returning None if empty"""
    if not prefixes_string:
        return None
    return " ".join(['"%s"' % s for s in prefixes_string.split(" ") if s])


def build_config(env_vars=None):
    """Build configuration dictionary from environment variables

    Args:
        env_vars: Optional dict of environment variables (defaults to os.environ)

    Returns:
        dict: Configuration dictionary for template rendering
    """
    if env_vars is None:
        env_vars = os.environ

    def getenv(key, default=""):
        return env_vars.get(key, default)

    # An optional client admin public key (HS_PUBKEY) enables signature
    # (challenge-response) auth alongside the default HS_SECKEY basic auth.
    # Its identity must be a server admin to be authorized for writes, so it
    # is appended to SERVER_ADMINS automatically when provided.
    server_admins = getenv("SERVER_ADMINS")
    client_admin_pubkey_pem = getenv("CLIENT_ADMIN_PUBLIC_KEY_PEM")
    client_admin_handle = getenv("CLIENT_ADMIN_HANDLE", "301:TEST/ADMIN")
    if client_admin_pubkey_pem and client_admin_handle not in server_admins.split():
        server_admins = (server_admins + " " + client_admin_handle).strip()

    # Build base configuration
    config = {
        # Interface Configuration
        "BIND_ADDRESS": getenv("BIND_ADDRESS", "0.0.0.0"),
        "NUM_THREADS": getenv("NUM_THREADS", "15"),
        "BIND_PORT": getenv("BIND_PORT", "2641"),
        "LOG_ACCESSES": getenv("LOG_ACCESSES", "yes"),
        "HTTP_BIND_PORT": getenv("HTTP_BIND_PORT", "8000"),
        "HTTP_NUM_THREADS": getenv("HTTP_NUM_THREADS", "15"),
        "BACKLOG": getenv("BACKLOG"),
        "BIND_ADDRESS_V6": getenv("BIND_ADDRESS_V6"),
        "LISTEN_ADDRESS": getenv("LISTEN_ADDRESS"),
        "ALLOW_RECURSION": getenv("ALLOW_RECURSION"),

        # Server Configuration
        "SERVER_ADMINS": format_admin_list(server_admins),
        "REPLICATION_ADMINS": format_admin_list(getenv("REPLICATION_ADMINS")),
        "MAX_SESSION_TIME": getenv("MAX_SESSION_TIME", "86400000"),
        "THIS_SERVER_ID": getenv("THIS_SERVER_ID", "1"),
        "MAX_AUTH_TIME": getenv("MAX_AUTH_TIME", "60000"),
        "SERVER_ADMIN_FULL_ACCESS": getenv("SERVER_ADMIN_FULL_ACCESS", "yes"),
        "ALLOW_NA_ADMINS": getenv("ALLOW_NA_ADMINS", "no"),
        "TEMPLATE_NS_OVERRIDE": getenv("TEMPLATE_NS_OVERRIDE", "yes"),
        "CASE_SENSITIVE": getenv("CASE_SENSITIVE", "no"),
        "MAX_HANDLES": getenv("MAX_HANDLES"),
        "MAX_VALUES": getenv("MAX_VALUES"),
        "TRACE_RESOLUTION": getenv("TRACE_RESOLUTION"),
        "ALLOW_LIST_HDLS": getenv("ALLOW_LIST_HDLS"),

        # Protocol Settings
        "NO_UDP_RESOLUTION": getenv("NO_UDP_RESOLUTION", "yes"),

        # Logging Configuration
        "LOG_SAVE_INTERVAL": getenv("LOG_SAVE_INTERVAL", "Never"),
        "LOG_SAVE_DIRECTORY": getenv("LOG_SAVE_DIRECTORY", "logs"),

        # Site Information
        "HANDLE_HOST_IP": getenv("HANDLE_HOST_IP", "0.0.0.0"),
        "SITE_DESCRIPTION": getenv("SITE_DESCRIPTION", "Handle Server"),

        # Security Keys (encoded as bytes for subprocess)
        "SERVER_PRIVATE_KEY_PEM": getenv("SERVER_PRIVATE_KEY_PEM").encode("ASCII"),
        "SERVER_PUBLIC_KEY_PEM": getenv("SERVER_PUBLIC_KEY_PEM").encode("ASCII"),
        # Optional client admin public key for signature (challenge-response)
        # auth, provisioned as an HS_PUBKEY value (see provision_client_pubkey)
        "CLIENT_ADMIN_PUBLIC_KEY_PEM": (
            client_admin_pubkey_pem.encode("ASCII")
            if client_admin_pubkey_pem
            else b""
        ),
        "CLIENT_ADMIN_HANDLE": client_admin_handle,

        # Storage Configuration
        "STORAGE_TYPE": getenv("STORAGE_TYPE"),
        "SQL_URL": getenv("SQL_URL"),
        "SQL_DRIVER": getenv("SQL_DRIVER", "org.postgresql.Driver"),
        "SQL_LOGIN": getenv("SQL_LOGIN", "postgres"),
        "SQL_PASSWD": getenv("SQL_PASSWD"),
        "SQL_READ_ONLY": getenv("SQL_READ_ONLY", "no"),

        # HTTP Configuration
        "ALLOW_CORS": getenv("ALLOW_CORS"),
        "CORS_ORIGINS": getenv("CORS_ORIGINS"),
        "HTTPS_ENABLED": getenv("HTTPS_ENABLED"),
        "HTTPS_PORT": getenv("HTTPS_PORT"),
        "HTTP_LOG_FORMAT": getenv("HTTP_LOG_FORMAT"),
        "MAX_REQUEST_SIZE": getenv("MAX_REQUEST_SIZE"),
        "SESSION_TIMEOUT": getenv("SESSION_TIMEOUT"),
        "ADMIN_PATH": getenv("ADMIN_PATH"),
    }

    # Handle AUTO_HOMED_PREFIXES with TEST as default for docker test server
    auto_homed_prefixes = getenv("AUTO_HOMED_PREFIXES", "TEST")
    config["AUTO_HOMED_PREFIXES"] = format_auto_homed_prefixes(auto_homed_prefixes)

    return config


def convert_pem_to_dsa(pem_data, hdl_convert_cmd):
    """Convert PEM key data to DSA format using hdl-convert-key tool

    Args:
        pem_data: PEM key data as bytes
        hdl_convert_cmd: Path to hdl-convert-key executable

    Returns:
        bytes: DSA key data

    Raises:
        subprocess.CalledProcessError: If key conversion fails
    """
    with subprocess.Popen(
        [hdl_convert_cmd],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ) as p:
        dsa_data, stderr = p.communicate(input=pem_data)
        if p.returncode != 0:
            raise subprocess.CalledProcessError(
                p.returncode, hdl_convert_cmd, output=dsa_data, stderr=stderr
            )
        return dsa_data


def parse_jdbc_url(sql_url):
    """Parse a jdbc:postgresql://host:port/dbname URL into (host, port, dbname).

    Args:
        sql_url: JDBC PostgreSQL URL, e.g. jdbc:postgresql://postgres:5432/handledb

    Returns:
        tuple: (host, port, dbname); port defaults to 5432 when absent.
    """
    netloc = sql_url.split("://", 1)[-1]
    hostport, _, dbname = netloc.partition("/")
    host, _, port = hostport.partition(":")
    return host, int(port) if port else 5432, dbname


def provision_client_pubkey(pubkey_pem, client_admin_handle, hdl_convert_cmd,
                            env_vars):
    """Upsert the client admin public key as an HS_PUBKEY handle value.

    Converts the PEM to the Handle binary public-key format with
    hdl-convert-key and writes it into the SQL storage backend at the
    index:handle given by client_admin_handle (e.g. "301:TEST/ADMIN"), so a
    client holding the matching private key can authenticate via the CNRI
    signature challenge-response flow. The existing HS_SECKEY (basic auth) is
    left untouched.

    Args:
        pubkey_pem: Client admin public key PEM as bytes.
        client_admin_handle: Target value as "{index}:{handle}".
        hdl_convert_cmd: Path to the hdl-convert-key executable.
        env_vars: Environment mapping providing SQL_URL/SQL_LOGIN/SQL_PASSWD.
    """
    blob = convert_pem_to_dsa(pubkey_pem, hdl_convert_cmd)
    index_str, _, handle = client_admin_handle.partition(":")
    host, port, dbname = parse_jdbc_url(env_vars.get("SQL_URL", ""))

    import psycopg2  # noqa: PLC0415 - optional dep, only used when provisioning

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=env_vars.get("SQL_LOGIN", "postgres"),
        password=env_vars.get("SQL_PASSWD", ""),
    )
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO handles (
                    handle, idx, type, data, ttl_type, ttl, timestamp,
                    admin_read, admin_write, pub_read, pub_write
                )
                VALUES (%s, %s, %s, %s, 0, 86400,
                        EXTRACT(epoch FROM now())::int,
                        true, true, true, false)
                ON CONFLICT (handle, idx) DO UPDATE
                SET type = EXCLUDED.type,
                    data = EXCLUDED.data,
                    pub_read = EXCLUDED.pub_read;
                """,
                (
                    psycopg2.Binary(handle.encode("UTF-8")),
                    int(index_str),
                    psycopg2.Binary(b"HS_PUBKEY"),
                    psycopg2.Binary(blob),
                ),
            )
    finally:
        conn.close()


def render_template(template_name, output_path, config, jinja_env):
    """Render a Jinja2 template to file

    Args:
        template_name: Name of template file
        output_path: Path to write rendered output
        config: Configuration dict for template variables
        jinja_env: Jinja2 Environment object
    """
    template = jinja_env.get_template(template_name)
    rendered = template.render(config)

    with open(output_path, "w") as f:
        f.write(rendered)


def main(handle_bin, out_dir, config_dir=None):
    """Main function to orchestrate config generation

    Args:
        handle_bin: Path to handle server bin directory
        out_dir: Output directory for generated configs
        config_dir: Config template directory (auto-detected if None)
    """
    if config_dir is None:
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")

    # Build configuration from environment
    config = build_config()

    # Convert PEM keys to DSA format
    handle_convert_cmd = os.path.join(handle_bin, "hdl-convert-key")

    try:
        # Convert private key
        private_key_dsa = convert_pem_to_dsa(
            config["SERVER_PRIVATE_KEY_PEM"], handle_convert_cmd
        )
        with open(os.path.join(out_dir, "privkey.bin"), "wb") as f:
            f.write(private_key_dsa)

        # Convert public key
        public_key_dsa = convert_pem_to_dsa(
            config["SERVER_PUBLIC_KEY_PEM"], handle_convert_cmd
        )
        with open(os.path.join(out_dir, "pubkey.bin"), "wb") as f:
            f.write(public_key_dsa)

        # Add base64 encoded public key for siteinfo
        config["SERVER_PUBLIC_KEY_DSA_BASE64"] = base64.b64encode(public_key_dsa).decode("ASCII")

        # Optionally provision a client admin HS_PUBKEY for signature auth
        if config.get("CLIENT_ADMIN_PUBLIC_KEY_PEM"):
            provision_client_pubkey(
                config["CLIENT_ADMIN_PUBLIC_KEY_PEM"],
                config["CLIENT_ADMIN_HANDLE"],
                handle_convert_cmd,
                os.environ,
            )

    except subprocess.CalledProcessError as e:
        print(f"Error converting keys: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing keys: {e}", file=sys.stderr)
        sys.exit(1)

    # Set up Jinja2 environment
    jinja_env = Environment(
        loader=FileSystemLoader(config_dir),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Render templates
    try:
        render_template("config.dct.jinja", os.path.join(out_dir, "config.dct"), config, jinja_env)
        render_template("siteinfo.json.jinja", os.path.join(out_dir, "siteinfo.json"), config, jinja_env)
    except Exception as e:
        print(f"Error rendering templates: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: create_config.py <handle_bin_dir> <output_dir>", file=sys.stderr)
        sys.exit(1)

    handle_bin = sys.argv[1]
    out_dir = sys.argv[2]
    main(handle_bin, out_dir)
