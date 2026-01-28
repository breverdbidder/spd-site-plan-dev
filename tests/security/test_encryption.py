#!/usr/bin/env python3
"""
Comprehensive Encryption Testing Suite
P5 Security: Encryption validation tests

Tests for data-at-rest encryption, key rotation, and field-level encryption.

Author: BidDeed.AI / Everest Capital USA
"""

import pytest
import os
from datetime import datetime


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def encryption_manager():
    """Create encryption manager instance"""
    # Import here to allow tests to run even if module has issues
    from src.security.encryption_manager import EncryptionManager
    return EncryptionManager(master_key="test_master_key_12345")


@pytest.fixture
def sample_sensitive_data():
    """Sample sensitive data for testing"""
    return {
        "api_key": "sk_live_abc123xyz789",
        "password": "super_secret_password",
        "ssn": "123-45-6789",
        "credit_card": "4111111111111111",
        "bank_account": "9876543210",
    }


# =============================================================================
# ENCRYPTION MANAGER TESTS
# =============================================================================

class TestEncryptionManager:
    """Test suite for EncryptionManager"""
    
    def test_encrypt_decrypt_cycle(self, encryption_manager):
        """Test basic encrypt/decrypt cycle"""
        original = "sensitive_api_key_12345"
        
        encrypted = encryption_manager.encrypt(original)
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted.ciphertext != original
    
    def test_encrypt_different_outputs(self, encryption_manager):
        """Test that same input produces consistent encrypted output"""
        original = "test_data"
        
        encrypted1 = encryption_manager.encrypt(original)
        encrypted2 = encryption_manager.encrypt(original)
        
        # Both should decrypt to same value
        assert encryption_manager.decrypt(encrypted1) == original
        assert encryption_manager.decrypt(encrypted2) == original
    
    def test_empty_string_raises_error(self, encryption_manager):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="Cannot encrypt empty data"):
            encryption_manager.encrypt("")
    
    def test_encryption_metadata(self, encryption_manager):
        """Test encrypted data contains proper metadata"""
        from src.security.encryption_manager import DataClassification
        
        encrypted = encryption_manager.encrypt(
            "test_data", 
            classification=DataClassification.RESTRICTED
        )
        
        assert encrypted.key_id is not None
        assert encrypted.encrypted_at is not None
        assert encrypted.classification == DataClassification.RESTRICTED
    
    def test_key_mismatch_raises_error(self, encryption_manager):
        """Test decryption with wrong key raises error"""
        from src.security.encryption_manager import EncryptionManager, EncryptedData, DataClassification, EncryptionLevel
        
        encrypted = encryption_manager.encrypt("test_data")
        
        # Create new manager with different key
        other_manager = EncryptionManager(master_key="different_key_67890")
        
        # Create EncryptedData with mismatched key_id
        wrong_key_data = EncryptedData(
            ciphertext=encrypted.ciphertext,
            classification=DataClassification.CONFIDENTIAL,
            encryption_level=EncryptionLevel.HIGH,
            encrypted_at=encrypted.encrypted_at,
            key_id="wrong_key_id"
        )
        
        with pytest.raises(ValueError, match="Key mismatch"):
            other_manager.decrypt(wrong_key_data)
    
    def test_long_data_encryption(self, encryption_manager):
        """Test encryption of large data"""
        large_data = "A" * 100000  # 100KB of data
        
        encrypted = encryption_manager.encrypt(large_data)
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == large_data
    
    def test_special_characters(self, encryption_manager):
        """Test encryption of special characters"""
        special = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~\n\t\r"
        
        encrypted = encryption_manager.encrypt(special)
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == special
    
    def test_unicode_data(self, encryption_manager):
        """Test encryption of unicode characters"""
        unicode_data = "Hello 世界 🌍 مرحبا שלום"
        
        encrypted = encryption_manager.encrypt(unicode_data)
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == unicode_data


class TestDictEncryption:
    """Test suite for dictionary field encryption"""
    
    def test_encrypt_dict_fields(self, encryption_manager, sample_sensitive_data):
        """Test encrypting specific dictionary fields"""
        data = {
            "name": "John Doe",
            "api_key": "sk_live_abc123",
            "role": "admin"
        }
        
        encrypted_dict = encryption_manager.encrypt_dict(
            data,
            sensitive_fields=["api_key"]
        )
        
        # Non-sensitive field unchanged
        assert encrypted_dict["name"] == "John Doe"
        assert encrypted_dict["role"] == "admin"
        
        # Sensitive field encrypted
        assert encrypted_dict["api_key"]["_encrypted"] == True
        assert "ciphertext" in encrypted_dict["api_key"]
    
    def test_decrypt_dict_fields(self, encryption_manager):
        """Test decrypting dictionary with encrypted fields"""
        original = {"api_key": "sk_live_test123", "name": "Test"}
        
        encrypted_dict = encryption_manager.encrypt_dict(
            original,
            sensitive_fields=["api_key"]
        )
        
        decrypted_dict = encryption_manager.decrypt_dict(encrypted_dict)
        
        assert decrypted_dict["api_key"] == original["api_key"]
        assert decrypted_dict["name"] == original["name"]
    
    def test_encrypt_multiple_fields(self, encryption_manager):
        """Test encrypting multiple fields"""
        data = {
            "user_id": "123",
            "api_key": "key123",
            "password": "pass456",
            "email": "test@test.com"
        }
        
        encrypted = encryption_manager.encrypt_dict(
            data,
            sensitive_fields=["api_key", "password"]
        )
        
        assert encrypted["user_id"] == "123"
        assert encrypted["email"] == "test@test.com"
        assert encrypted["api_key"]["_encrypted"] == True
        assert encrypted["password"]["_encrypted"] == True


class TestKeyRotation:
    """Test suite for key rotation"""
    
    def test_key_rotation(self, encryption_manager):
        """Test key rotation updates key_id"""
        old_key_id = encryption_manager.key_id
        
        result = encryption_manager.rotate_key("new_master_key_67890")
        
        assert result["old_key_id"] == old_key_id
        assert result["new_key_id"] != old_key_id
        assert result["status"] == "SUCCESS"
        assert encryption_manager.key_id == result["new_key_id"]
    
    def test_data_encrypted_after_rotation(self, encryption_manager):
        """Test data can be encrypted/decrypted after rotation"""
        encryption_manager.rotate_key("rotated_key_12345")
        
        original = "post_rotation_data"
        encrypted = encryption_manager.encrypt(original)
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == original


class TestHashForLookup:
    """Test suite for deterministic hashing"""
    
    def test_hash_consistency(self, encryption_manager):
        """Test hash is consistent for same input"""
        value = "test_value"
        
        hash1 = encryption_manager.hash_for_lookup(value)
        hash2 = encryption_manager.hash_for_lookup(value)
        
        assert hash1 == hash2
    
    def test_hash_different_for_different_values(self, encryption_manager):
        """Test different values produce different hashes"""
        hash1 = encryption_manager.hash_for_lookup("value1")
        hash2 = encryption_manager.hash_for_lookup("value2")
        
        assert hash1 != hash2


class TestSensitiveFieldDetection:
    """Test suite for sensitive field detection"""
    
    def test_detect_sensitive_fields(self):
        """Test detection of sensitive field names"""
        from src.security.encryption_manager import is_field_sensitive
        
        sensitive = ["api_key", "password", "ssn", "credit_card", "email"]
        non_sensitive = ["name", "id", "created_at", "status"]
        
        for field in sensitive:
            assert is_field_sensitive(field) == True, f"{field} should be sensitive"
        
        for field in non_sensitive:
            assert is_field_sensitive(field) == False, f"{field} should not be sensitive"


class TestEncryptionStats:
    """Test suite for encryption statistics"""
    
    def test_stats_tracking(self, encryption_manager):
        """Test encryption/decryption stats are tracked"""
        # Perform operations
        for i in range(5):
            encrypted = encryption_manager.encrypt(f"data_{i}")
            encryption_manager.decrypt(encrypted)
        
        stats = encryption_manager.get_stats()
        
        assert stats["encryption_count"] == 5
        assert stats["decryption_count"] == 5
        assert "key_id" in stats


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestEncryptionPerformance:
    """Performance tests for encryption"""
    
    def test_bulk_encryption_performance(self, encryption_manager):
        """Test bulk encryption completes in reasonable time"""
        import time
        
        data_items = [f"sensitive_data_{i}" for i in range(100)]
        
        start = time.perf_counter()
        encrypted_items = [encryption_manager.encrypt(d) for d in data_items]
        encrypt_duration = time.perf_counter() - start
        
        start = time.perf_counter()
        decrypted_items = [encryption_manager.decrypt(e) for e in encrypted_items]
        decrypt_duration = time.perf_counter() - start
        
        # Should complete 100 items in under 1 second each
        assert encrypt_duration < 1.0, f"Encryption too slow: {encrypt_duration}s"
        assert decrypt_duration < 1.0, f"Decryption too slow: {decrypt_duration}s"
        
        # Verify correctness
        for original, decrypted in zip(data_items, decrypted_items):
            assert original == decrypted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
