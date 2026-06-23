"""Unit tests for config.py — .env path resolution. Run with: python -m pytest test_config_path.py -v"""
from pathlib import Path

import config


def test_env_file_path_is_absolute():
    """_ENV_FILE must be an absolute path so it works regardless of CWD."""
    assert config._ENV_FILE.is_absolute()


def test_env_file_ends_with_dotenv():
    """_ENV_FILE must point to a file named .env."""
    assert config._ENV_FILE.name == ".env"


def test_env_file_parent_is_script_dir():
    """_ENV_FILE must be in the same directory as config.py, not CWD."""
    assert config._ENV_FILE.parent == Path(config.__file__).resolve().parent


def test_secrets_dir_unchanged():
    """secrets_dir must remain /run/secrets for Docker compatibility."""
    assert config.Settings.model_config["secrets_dir"] == "/run/secrets"
