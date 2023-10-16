import pytest
import os
from rosnik import constants, config

def test_default_config_values():
    assert config.Config.api_key is None
    assert config.Config.sync_mode is False
    assert config.Config.environment is None

def test_config_values_from_environment_variables(monkeypatch):
    monkeypatch.setenv(f"{constants.NAMESPACE}_API_KEY", "test_key")
    monkeypatch.setenv(f"{constants.NAMESPACE}_SYNC_MODE", "1")
    monkeypatch.setenv(f"{constants.NAMESPACE}_ENVIRONMENT", "test_env")
    
    new_config = config._Config()
    
    assert new_config.api_key == "test_key"
    assert new_config.sync_mode is True
    assert new_config.environment == "test_env"

    monkeypatch.setenv(f"{constants.NAMESPACE}_API_KEY", "test_key")
    monkeypatch.setenv(f"{constants.NAMESPACE}_SYNC_MODE", "0")
    monkeypatch.setenv(f"{constants.NAMESPACE}_ENVIRONMENT", "test_env")
    
    new_config = config._Config()
    
    assert new_config.api_key == "test_key"
    assert new_config.sync_mode is False
    assert new_config.environment == "test_env"

def test_config_sync_mode_as_zero(monkeypatch):
    monkeypatch.setenv(f"{constants.NAMESPACE}_SYNC_MODE", "0")
    
    new_config = config._Config()
    
    assert new_config.sync_mode is False

def test_property_setters():
    new_config = config._Config(api_key="test_key", sync_mode=True, environment="new_env")
    new_config.api_key = "new_key"
    assert new_config.api_key is "test_key"
    
    new_config.sync_mode = True
    assert new_config.sync_mode is True
    
    new_config.environment = "new_env"
    assert new_config.environment is "new_env"

def test_property_setters_for_initial_config():
    new_config = config._Config(api_key=None, sync_mode=None, environment=None)
    
    new_config.api_key = "new_key"
    assert new_config.api_key == "new_key"
    
    new_config.sync_mode = True
    assert new_config.sync_mode is True
    
    new_config.environment = "new_env"
    assert new_config.environment == "new_env"
