"""Compute the salted hash the backend stores for a phone number, so you can confirm caller-variable provenance
(does Sarvam's User Identifier equal the number you actually called from?) without storing plaintext.
Usage: PHONE_HASH_SALT=... python scripts/hash_phone.py +9198XXXXXXXX   (try the forms Sarvam might send)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.privacy import salted_hash

salt = os.environ.get("PHONE_HASH_SALT") or sys.exit("set PHONE_HASH_SALT (same as the backend)")
for raw in sys.argv[1:]:
    digits = "".join(c for c in raw if c.isdigit())
    for form in {raw, digits, "+" + digits, digits[-10:], "0" + digits[-10:], "+91" + digits[-10:]}:
        print(f"{form:>16s}  {salted_hash(form, salt)}")
