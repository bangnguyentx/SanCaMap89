#!/usr/bin/env python3
import sys
import hashlib
from src.services.rng_service import RNGService
from src.utils.crypto import decrypt_seed

def main():
    if len(sys.argv) < 4:
        print("Usage: python verify_cli.py <round_id> <revealed_seed> <published_commitment> [client_seed]")
        print("Example: python verify_cli.py chat123_1 abc123... a1b2c3... my_client_seed")
        sys.exit(1)
    
    round_id = sys.argv[1]
    revealed_seed = sys.argv[2]
    published_commitment = sys.argv[3]
    client_seed = sys.argv[4] if len(sys.argv) > 4 else None
    
    rng_service = RNGService("dummy-key")  # Key not needed for verification
    
    try:
        # Verify commitment matches revealed seed
        computed_commitment = hashlib.sha256(revealed_seed.encode()).hexdigest()
        
        if computed_commitment != published_commitment:
            print("❌ COMMITMENT VERIFICATION FAILED!")
            print(f"Expected: {published_commitment}")
            print(f"Computed: {computed_commitment}")
            sys.exit(1)
        
        print("✅ Commitment verification passed")
        
        # Compute digits
        digits = rng_service.compute_digits(revealed_seed, round_id, client_seed)
        
        print(f"📊 Round ID: {round_id}")
        print(f"🔢 Computed digits: {''.join(map(str, digits))}")
        print(f"🎯 Last digit: {digits[-1]}")
        
        # Determine outcome
        last_digit = digits[-1]
        if last_digit in [0, 1, 2, 3, 4]:
            size = "SMALL"
        else:
            size = "BIG"
            
        if last_digit % 2 == 0:
            parity = "EVEN"
        else:
            parity = "ODD"
            
        print(f"📈 Result: {size} ({parity})")
        print("✅ Verification completed successfully")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
