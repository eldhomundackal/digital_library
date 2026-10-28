import bcrypt
from passlib.context import CryptContext

# passlib reads bcrypt.__about__.__version__ which no longer exists in bcrypt 4.x+
if not hasattr(bcrypt, "__about__"):
    import types

    about = types.ModuleType("bcrypt.__about__")
    about.__version__ = bcrypt.__version__
    bcrypt.__about__ = about

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain password matches the stored hash."""
    return _pwd_context.verify(plain_password, hashed_password)
