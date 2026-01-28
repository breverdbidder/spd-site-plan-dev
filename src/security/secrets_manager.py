#!/usr/bin/env python3
"""
Secrets Manager for SPD Site Plan Development
Supports: HashiCorp Vault, Azure Key Vault, Environment Variables

P0 Security Requirement: Implement secrets management
Author: BidDeed.AI / Everest Capital USA
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class SecretMetadata:
    """Metadata for tracked secrets"""
    key: str
    provider: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    version: Optional[str] = None
    last_rotated: Optional[datetime] = None


class SecretsProvider(ABC):
    """Abstract base class for secrets providers"""
    
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key"""
        pass
    
    @abstractmethod
    def set_secret(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Store a secret"""
        pass
    
    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        pass
    
    @abstractmethod
    def list_secrets(self) -> list:
        """List all secret keys"""
        pass
    
    @abstractmethod
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate a secret to a new value"""
        pass


class EnvironmentSecretsProvider(SecretsProvider):
    """
    Environment variable-based secrets provider.
    Fallback when Vault/Azure not configured.
    """
    
    def __init__(self, prefix: str = "SPD_"):
        self.prefix = prefix
        self._cache: Dict[str, str] = {}
        self._load_from_env()
    
    def _load_from_env(self):
        """Load all prefixed environment variables"""
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                self._cache[key] = value
    
    def get_secret(self, key: str) -> Optional[str]:
        full_key = f"{self.prefix}{key}" if not key.startswith(self.prefix) else key
        return self._cache.get(full_key) or os.environ.get(full_key)
    
    def set_secret(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        full_key = f"{self.prefix}{key}" if not key.startswith(self.prefix) else key
        self._cache[full_key] = value
        os.environ[full_key] = value
        logger.info(f"Set environment secret: {full_key}")
        return True
    
    def delete_secret(self, key: str) -> bool:
        full_key = f"{self.prefix}{key}" if not key.startswith(self.prefix) else key
        if full_key in self._cache:
            del self._cache[full_key]
        if full_key in os.environ:
            del os.environ[full_key]
        return True
    
    def list_secrets(self) -> list:
        return list(self._cache.keys())
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        return self.set_secret(key, new_value)


class VaultSecretsProvider(SecretsProvider):
    """
    HashiCorp Vault secrets provider.
    Requires: VAULT_ADDR, VAULT_TOKEN environment variables
    """
    
    def __init__(self, mount_point: str = "secret", path_prefix: str = "spd"):
        self.mount_point = mount_point
        self.path_prefix = path_prefix
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Vault client"""
        try:
            import hvac
            
            vault_addr = os.environ.get("VAULT_ADDR")
            vault_token = os.environ.get("VAULT_TOKEN")
            
            if not vault_addr or not vault_token:
                logger.warning("Vault credentials not found, provider disabled")
                return
            
            self._client = hvac.Client(url=vault_addr, token=vault_token)
            
            if not self._client.is_authenticated():
                logger.error("Vault authentication failed")
                self._client = None
            else:
                logger.info(f"Connected to Vault at {vault_addr}")
                
        except ImportError:
            logger.warning("hvac not installed, Vault provider disabled")
        except Exception as e:
            logger.error(f"Vault initialization failed: {e}")
    
    def _full_path(self, key: str) -> str:
        return f"{self.path_prefix}/{key}"
    
    def get_secret(self, key: str) -> Optional[str]:
        if not self._client:
            return None
        
        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=self._full_path(key),
                mount_point=self.mount_point
            )
            return response["data"]["data"].get("value")
        except Exception as e:
            logger.debug(f"Vault get_secret failed for {key}: {e}")
            return None
    
    def set_secret(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        if not self._client:
            return False
        
        try:
            data = {"value": value}
            if metadata:
                data["metadata"] = metadata
            
            self._client.secrets.kv.v2.create_or_update_secret(
                path=self._full_path(key),
                secret=data,
                mount_point=self.mount_point
            )
            logger.info(f"Set Vault secret: {key}")
            return True
        except Exception as e:
            logger.error(f"Vault set_secret failed for {key}: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        if not self._client:
            return False
        
        try:
            self._client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=self._full_path(key),
                mount_point=self.mount_point
            )
            return True
        except Exception as e:
            logger.error(f"Vault delete_secret failed for {key}: {e}")
            return False
    
    def list_secrets(self) -> list:
        if not self._client:
            return []
        
        try:
            response = self._client.secrets.kv.v2.list_secrets(
                path=self.path_prefix,
                mount_point=self.mount_point
            )
            return response["data"]["keys"]
        except Exception as e:
            logger.debug(f"Vault list_secrets failed: {e}")
            return []
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate secret - Vault handles versioning automatically"""
        return self.set_secret(key, new_value, {"rotated_at": datetime.utcnow().isoformat()})


class AzureKeyVaultProvider(SecretsProvider):
    """
    Azure Key Vault secrets provider.
    Requires: AZURE_VAULT_URL environment variable
    Uses DefaultAzureCredential for auth (supports managed identity, CLI, env vars)
    """
    
    def __init__(self):
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Azure Key Vault client"""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            vault_url = os.environ.get("AZURE_VAULT_URL")
            if not vault_url:
                logger.warning("AZURE_VAULT_URL not set, Azure provider disabled")
                return
            
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=vault_url, credential=credential)
            logger.info(f"Connected to Azure Key Vault: {vault_url}")
            
        except ImportError:
            logger.warning("azure-keyvault-secrets not installed, Azure provider disabled")
        except Exception as e:
            logger.error(f"Azure Key Vault initialization failed: {e}")
    
    def _normalize_key(self, key: str) -> str:
        """Azure Key Vault doesn't allow underscores in names"""
        return key.replace("_", "-")
    
    def get_secret(self, key: str) -> Optional[str]:
        if not self._client:
            return None
        
        try:
            secret = self._client.get_secret(self._normalize_key(key))
            return secret.value
        except Exception as e:
            logger.debug(f"Azure get_secret failed for {key}: {e}")
            return None
    
    def set_secret(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        if not self._client:
            return False
        
        try:
            self._client.set_secret(self._normalize_key(key), value)
            logger.info(f"Set Azure secret: {key}")
            return True
        except Exception as e:
            logger.error(f"Azure set_secret failed for {key}: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        if not self._client:
            return False
        
        try:
            poller = self._client.begin_delete_secret(self._normalize_key(key))
            poller.wait()
            return True
        except Exception as e:
            logger.error(f"Azure delete_secret failed for {key}: {e}")
            return False
    
    def list_secrets(self) -> list:
        if not self._client:
            return []
        
        try:
            return [s.name for s in self._client.list_properties_of_secrets()]
        except Exception as e:
            logger.debug(f"Azure list_secrets failed: {e}")
            return []
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Azure Key Vault handles versioning automatically"""
        return self.set_secret(key, new_value)


class SecretsManager:
    """
    Unified secrets manager with provider chain.
    Tries providers in order: Vault -> Azure -> Environment
    """
    
    def __init__(self, providers: Optional[list] = None):
        if providers:
            self.providers = providers
        else:
            # Default provider chain
            self.providers = [
                VaultSecretsProvider(),
                AzureKeyVaultProvider(),
                EnvironmentSecretsProvider()
            ]
        
        self._rotation_schedule: Dict[str, timedelta] = {}
        self._last_rotation: Dict[str, datetime] = {}
    
    def get_secret(self, key: str, required: bool = False) -> Optional[str]:
        """
        Get secret from first available provider.
        
        Args:
            key: Secret key to retrieve
            required: If True, raises ValueError if not found
        
        Returns:
            Secret value or None
        """
        for provider in self.providers:
            value = provider.get_secret(key)
            if value is not None:
                logger.debug(f"Retrieved {key} from {provider.__class__.__name__}")
                return value
        
        if required:
            raise ValueError(f"Required secret '{key}' not found in any provider")
        
        return None
    
    def set_secret(self, key: str, value: str, provider_index: int = 0) -> bool:
        """Store secret in specified provider (default: first available)"""
        if provider_index < len(self.providers):
            return self.providers[provider_index].set_secret(key, value)
        return False
    
    def set_rotation_schedule(self, key: str, interval: timedelta):
        """Set automatic rotation schedule for a secret"""
        self._rotation_schedule[key] = interval
        self._last_rotation[key] = datetime.utcnow()
    
    def check_rotation_needed(self, key: str) -> bool:
        """Check if a secret needs rotation"""
        if key not in self._rotation_schedule:
            return False
        
        last = self._last_rotation.get(key, datetime.min)
        interval = self._rotation_schedule[key]
        return datetime.utcnow() - last > interval
    
    def get_all_keys(self) -> list:
        """Get all secret keys from all providers"""
        all_keys = set()
        for provider in self.providers:
            all_keys.update(provider.list_secrets())
        return list(all_keys)
    
    # Convenience methods for common secrets
    @property
    def supabase_url(self) -> str:
        return self.get_secret("SUPABASE_URL", required=True)
    
    @property
    def supabase_key(self) -> str:
        return self.get_secret("SUPABASE_SERVICE_ROLE_KEY", required=True)
    
    @property
    def github_token(self) -> Optional[str]:
        return self.get_secret("GITHUB_TOKEN")
    
    @property
    def anthropic_api_key(self) -> Optional[str]:
        return self.get_secret("ANTHROPIC_API_KEY")


# Global singleton instance
@lru_cache(maxsize=1)
def get_secrets_manager() -> SecretsManager:
    """Get or create global secrets manager instance"""
    return SecretsManager()


# Convenience function
def get_secret(key: str, required: bool = False) -> Optional[str]:
    """Quick access to secrets without explicit manager"""
    return get_secrets_manager().get_secret(key, required)


if __name__ == "__main__":
    # Test secrets manager
    logging.basicConfig(level=logging.DEBUG)
    
    manager = get_secrets_manager()
    
    print("Available providers:")
    for p in manager.providers:
        print(f"  - {p.__class__.__name__}")
    
    print("\nAll secret keys:")
    for key in manager.get_all_keys():
        print(f"  - {key}")
    
    # Test get/set
    manager.set_secret("TEST_SECRET", "test_value_123")
    value = manager.get_secret("TEST_SECRET")
    print(f"\nTest secret: {value}")
