"""
Account field validators used by UserModel.

Password policy (enforced on registration and password change):
- Minimum 8 characters
- At least one uppercase letter (A–Z)
- At least one digit (0–9)
"""

import re


def validate_password(password: str):
    """Validate password complexity. Raises ValueError if policy is not met."""
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    return password


def validate_email(email: str):
    """Validate email format. Raises ValueError if format is invalid."""
    if not re.search(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        raise ValueError("Email has wrong format")
    return email
