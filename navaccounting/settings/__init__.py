import os
import environ

env = environ.Env()
environ.Env.read_env(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

if env.bool('DEBUG', default=True):
    from .development import *  # noqa: F401, F403
else:
    from .production import *  # noqa: F401, F403
