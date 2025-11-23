import pytest
from src.services.rng_service import RNGService
from src.utils.convert import bytes_to_digits_unbiased

class TestRNGService:
    def setup_method(self):
        self.rng_service = RNGService("test-encryption-key")
    
    def test_generate_server_seed(self):
        seed, commitment = self.rng_service.generate_server_seed()
        
        assert len(seed) == 64  # 32 bytes in hex
        assert len(commitment) == 64  # SHA256 hex digest
    
    def test_compute_digits_deterministic(self):
        server_seed = "a" * 64
        round_id = "test_round_1"
        
        digits1 = self.rng_service.compute_digits(server_seed, round_id)
        digits2 = self.rng_service.compute_digits(server_seed, round_id)
        
        assert digits1 == digits2
        assert len(digits1) == 6
        assert all(0 <= d <= 9 for d in digits1)
    
    def test_compute_digits_with_client_seed(self):
        server_seed = "b" * 64
        round_id = "test_round_2"
        client_seed = "user_seed_123"
        
        digits1 = self.rng_service.compute_digits(server_seed, round_id, client_seed)
        digits2 = self.rng_service.compute_digits(server_seed, round_id, client_seed)
        
        assert digits1 == digits2
        assert len(digits1) == 6
    
    def test_verify_round(self):
        server_seed = "c" * 64
        round_id = "test_round_3"
        
        digits = self.rng_service.compute_digits(server_seed, round_id)
        is_valid, computed_digits, commitment = self.rng_service.verify_round(
            server_seed, round_id, expected_digits=digits
        )
        
        assert is_valid
        assert computed_digits == digits
    
    def test_bytes_to_digits_unbiased(self):
        # Test with known byte sequence
        test_bytes = bytes([1, 251, 2, 252, 3, 253, 4, 254, 5, 255, 6, 0])
        digits = bytes_to_digits_unbiased(test_bytes, 6)
        
        # Should skip bytes >= 250 and use valid ones
        assert digits == [1, 2, 3, 4, 5, 6]
        assert all(0 <= d <= 9 for d in digits)

if __name__ == '__main__':
    pytest.main([__file__])
