def get_env_variable(var_name):
    import os
    """Get the environment variable or return exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        raise Exception(f"Set the {var_name} environment variable") from None

def is_valid_email(email):
    import re
    """Validate the email format."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def generate_random_string(length=8):
    import random
    import string
    """Generate a random string of fixed length."""
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))