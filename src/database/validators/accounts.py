import re


def validate_password(password: str):
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    return password


def validate_email(email: str):
    if not re.search(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        raise ValueError("Email has wrong format")
    return email
