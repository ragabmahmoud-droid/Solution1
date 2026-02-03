# -*- coding: utf-8 -*-
import os
import json
import logging
import requests
from odoo.modules.module import get_module_root

_logger = logging.getLogger(__name__)

# Configuration cache
_config = None


def get_config():
    """Load and cache configuration from config.json"""
    global _config
    if _config is None:
        try:
            module_dir = get_module_root(os.path.dirname(__file__))
            config_path = os.path.join(module_dir, "config.json")
            with open(config_path, 'r') as f:
                _config = json.load(f)
            _logger.info("License client config loaded: enabled=%s, server=%s", 
                        _config.get('enabled'), _config.get('license_server'))
        except FileNotFoundError:
            _logger.warning("config.json not found, license validation disabled")
            _config = {"enabled": "False", "license_server": ""}
        except json.JSONDecodeError as e:
            _logger.error("Invalid JSON in config.json: %s", e)
            _config = {"enabled": "False", "license_server": ""}
        except Exception as e:
            _logger.error("Failed to load config.json: %s", e)
            _config = {"enabled": "False", "license_server": ""}
    return _config


def reload_config():
    """Force reload of configuration"""
    global _config
    _config = None
    return get_config()


def is_enabled():
    """Check if license validation is enabled"""
    config = get_config()
    return config.get("enabled", "False") == "True"


def get_server_url():
    """Get the license server URL"""
    config = get_config()
    return config.get("license_server", "")


def check_license(env, check_type):
    """
    Check license with the license server.
    
    Args:
        env: Odoo environment
        check_type: "users" or "modules"
    
    Returns:
        - For "users": integer (max users allowed)
        - For "modules": list of allowed module names
        - Default values if disabled or error
    """
    # Return defaults if disabled
    if not is_enabled():
        _logger.debug("License validation is disabled")
        if check_type == "modules":
            return ["all"]  # Allow all modules when disabled
        elif check_type == "users":
            return 999999  # Unlimited users when disabled
        return None
    
    license_server = get_server_url()
    
    if not license_server:
        _logger.warning("License server URL not configured")
        return None
    
    db_name = env.cr.dbname
    url = f"{license_server.rstrip('/')}/se_license/check"
    
    try:
        _logger.debug("Checking license at %s for database %s, type=%s", 
                     url, db_name, check_type)
        
        response = requests.post(
            url,
            json={"database": db_name, "check_type": check_type},
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Handle Odoo JSON-RPC wrapper
        if 'result' in result:
            result = result['result']
        
        if result.get('success'):
            _logger.debug("License check successful: %s", result.get('data'))
            return result.get('data')
        else:
            _logger.warning("License check failed: %s", result.get('message'))
            return None
            
    except requests.exceptions.ConnectionError:
        _logger.error("Could not connect to license server at %s", url)
        return None
    except requests.exceptions.Timeout:
        _logger.error("Timeout connecting to license server at %s", url)
        return None
    except requests.exceptions.HTTPError as e:
        _logger.error("HTTP error from license server: %s", e)
        return None
    except requests.exceptions.RequestException as e:
        _logger.error("License server request error: %s", e)
        return None
    except json.JSONDecodeError as e:
        _logger.error("Invalid JSON response from license server: %s", e)
        return None
    except Exception as e:
        _logger.error("Unexpected error during license check: %s", e)
        return None
