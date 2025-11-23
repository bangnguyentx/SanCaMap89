import hmac
import hashlib
from typing import List

def bytes_to_digits_unbiased(byte_array: bytes, num_digits: int = 6) -> List[int]:
    """
    Convert bytes to digits using rejection sampling to avoid modulo bias.
    Only accepts bytes in range 0-249 for uniform distribution modulo 10.
    """
    digits = []
    index = 0
    extended_data = byte_array
    
    while len(digits) < num_digits:
        # If we've exhausted our bytes, extend with SHA256 hash
        if index >= len(extended_data):
            extended_data = hashlib.sha256(extended_data).digest()
            index = 0
            
        byte_val = extended_data[index]
        index += 1
        
        # Rejection sampling: only accept bytes 0-249
        if byte_val < 250:
            digit = byte_val % 10
            digits.append(digit)
    
    return digits

def hmac_to_digits(server_seed: str, message: bytes, num_digits: int = 6) -> List[int]:
    """
    Convert HMAC-SHA256 output to unbiased digits.
    """
    hmac_key = server_seed.encode()
    mac = hmac.new(hmac_key, message, hashlib.sha256).digest()
    return bytes_to_digits_unbiased(mac, num_digits)
