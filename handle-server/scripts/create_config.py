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
        "SERVER_ADMINS": format_admin_list(getenv("SERVER_ADMINS")),
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
