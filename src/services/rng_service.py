import hashlib
import hmac
import secrets
from typing import List, Optional, Tuple
import os
from ..utils.crypto import encrypt_seed, decrypt_seed
from ..utils.convert import bytes_to_digits_unbiased
from sqlalchemy.orm import Session
from ..db.models import ProvableSeed

class RNGService:
    def __init__(self, encryption_key: str):
        self.encryption_key = encryption_key

    def generate_server_seed(self) -> Tuple[str, str]:
        """Generate a cryptographically secure server seed and its commitment."""
        server_seed = secrets.token_hex(32)  # 256-bit entropy
        commitment = hashlib.sha256(server_seed.encode()).hexdigest()
        return server_seed, commitment

    def encrypt_and_store_seed(self, db: Session, round_id: str, server_seed: str, 
                             commitment: str, period_tag: Optional[str] = None) -> ProvableSeed:
        """Encrypt and store the server seed in database."""
        encrypted_seed = encrypt_seed(server_seed, self.encryption_key)
        
        seed_record = ProvableSeed(
            round_id=round_id,
            commitment=commitment,
            encrypted_seed=encrypted_seed,
            period_tag=period_tag,
            client_seed_allowed=True
        )
        
        db.add(seed_record)
        db.commit()
        return seed_record

    def compute_digits(self, server_seed: str, round_id: str, 
                      client_seed: Optional[str] = None) -> List[int]:
        """
        Compute 6 digits using HMAC-SHA256 with rejection sampling to avoid bias.
        """
        # Prepare the message: round_id + client_seed (if provided)
        message = round_id.encode()
        if client_seed:
            message += client_seed.encode()

        # Use server_seed as HMAC key
        hmac_key = server_seed.encode()
        
        digits = []
        counter = 0
        
        while len(digits) < 6:
            # Generate HMAC with counter to get more bytes if needed
            hmac_msg = message + counter.to_bytes(4, 'big')
            mac = hmac.new(hmac_key, hmac_msg, hashlib.sha256).digest()
            
            # Process each byte in the MAC
            for byte in mac:
                if len(digits) >= 6:
                    break
                    
                # Rejection sampling: only accept bytes 0-249 for uniform distribution
                if byte < 250:
                    digit = byte % 10
                    digits.append(digit)
            
            counter += 1
        
        return digits

    def get_seed_for_round(self, db: Session, round_id: str) -> Optional[ProvableSeed]:
        """Retrieve seed record for a round."""
        return db.query(ProvableSeed).filter(ProvableSeed.round_id == round_id).first()

    def reveal_seed(self, db: Session, round_id: str) -> Optional[str]:
        """Reveal the server seed for a round."""
        seed_record = self.get_seed_for_round(db, round_id)
        if not seed_record:
            return None
            
        if seed_record.revealed_at is not None:
            # Already revealed
            server_seed = decrypt_seed(seed_record.encrypted_seed, self.encryption_key)
            return server_seed
            
        # Decrypt and verify
        server_seed = decrypt_seed(seed_record.encrypted_seed, self.encryption_key)
        computed_commitment = hashlib.sha256(server_seed.encode()).hexdigest()
        
        if computed_commitment != seed_record.commitment:
            raise ValueError("Commitment verification failed!")
            
        # Update record
        seed_record.revealed_at = db.execute('SELECT NOW()').scalar()
        seed_record.revealed_seed_hash = hashlib.sha256(server_seed.encode()).hexdigest()
        db.commit()
        
        return server_seed

    def verify_round(self, server_seed: str, round_id: str, 
                    client_seed: Optional[str] = None, 
                    expected_digits: Optional[List[int]] = None) -> Tuple[bool, List[int], str]:
        """
        Verify a round's results.
        Returns (is_valid, computed_digits, computed_commitment)
        """
        computed_commitment = hashlib.sha256(server_seed.encode()).hexdigest()
        computed_digits = self.compute_digits(server_seed, round_id, client_seed)
        
        if expected_digits:
            is_valid = computed_digits == expected_digits
        else:
            is_valid = True
            
        return is_valid, computed_digits, computed_commitment

    def generate_forced_seed(self, round_id: str, forced_value: str, 
                           max_attempts: int = 100000) -> Optional[Tuple[str, str]]:
        """
        Generate a server seed that will produce a specific outcome.
        This is used for admin forced outcomes.
        """
        attempts = 0
        
        while attempts < max_attempts:
            server_seed = secrets.token_hex(32)
            digits = self.compute_digits(server_seed, round_id)
            last_digit = digits[-1]
            
            # Check if this seed produces the forced outcome
            if forced_value == 'small' and last_digit in [0, 1, 2, 3, 4]:
                commitment = hashlib.sha256(server_seed.encode()).hexdigest()
                return server_seed, commitment
            elif forced_value == 'big' and last_digit in [5, 6, 7, 8, 9]:
                commitment = hashlib.sha256(server_seed.encode()).hexdigest()
                return server_seed, commitment
            elif forced_value == 'even' and last_digit % 2 == 0:
                commitment = hashlib.sha256(server_seed.encode()).hexdigest()
                return server_seed, commitment
            elif forced_value == 'odd' and last_digit % 2 == 1:
                commitment = hashlib.sha256(server_seed.encode()).hexdigest()
                return server_seed, commitment
                
            attempts += 1
            
        return None
