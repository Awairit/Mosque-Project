"""String utility functions."""

import re

# Supported country codes and their valid local (national) digit lengths
COUNTRY_LOCAL_LENGTHS = {
    "91": {10},         # India
    "966": {9},         # Saudi Arabia
    "971": {9},         # UAE
    "974": {8},         # Qatar
    "965": {8},         # Kuwait
    "968": {8},         # Oman
    "44": {10},         # UK
    "1": {10},          # USA / Canada
}

def normalize_phone_number(phone_str: str, default_country_code: str = "+91") -> str:
    """
    Normalizes a phone number to E.164 format.
    - If it already starts with '+', it is treated as E.164 (removes non-digits except leading '+').
    - If it does not start with '+', strips non-digits and prepends default_country_code.
    - Raises ValueError if the input is empty or invalid.
    """
    if not phone_str or not isinstance(phone_str, str):
        raise ValueError("Phone number must be a non-empty string.")
        
    cleaned = phone_str.strip()
    
    # Clean all non-digits except leading '+'
    if cleaned.startswith("+"):
        normalized = "+" + re.sub(r'\D', '', cleaned[1:])
    else:
        digits = re.sub(r'\D', '', cleaned)
        if not digits:
            raise ValueError("Phone number must contain digits.")
            
        if not default_country_code.startswith("+"):
            default_country_code = "+" + default_country_code
            
        cc_digits = default_country_code[1:]
        
        # If digits already starts with the country code digits
        if digits.startswith(cc_digits):
            remaining = digits[len(cc_digits):]
            # Verify if remaining digits match the expected local length for this country
            expected_lengths = COUNTRY_LOCAL_LENGTHS.get(cc_digits, set(range(7, 12)))
            if len(remaining) in expected_lengths:
                normalized = "+" + digits
            else:
                # Prepend country code anyway (e.g. if the local number happened to start with the same digits)
                normalized = default_country_code + digits
        else:
            normalized = default_country_code + digits
            
    # E.164 validation
    digits_only = normalized[1:]
    if not (7 <= len(digits_only) <= 15):
        raise ValueError("Invalid phone number length.")
        
    # Find country code prefix and validate local digits length
    found_cc = None
    for cc in sorted(COUNTRY_LOCAL_LENGTHS.keys(), key=len, reverse=True):
        if digits_only.startswith(cc):
            found_cc = cc
            break
            
    if found_cc:
        local_digits = digits_only[len(found_cc):]
        expected_lengths = COUNTRY_LOCAL_LENGTHS[found_cc]
        if len(local_digits) not in expected_lengths:
            raise ValueError(
                f"Invalid local number length for country code +{found_cc}. "
                f"Expected {list(expected_lengths)[0]} digits, got {len(local_digits)}."
            )
    else:
        # Fallback validation for other countries not explicitly in map
        if len(digits_only) < 7:
            raise ValueError("Phone number is too short.")
            
    return normalized

