"""
    File Name: settings.py
    Description: Some parameters that runs the tornado
    server needed.
"""


class DevelopConfig(object):
    """
    """
    POSTGRES_URI = "postgresql://postgres:postgres@localhost:5432/to_ubiwifi"
    DEBUG = True


class ProductConfig(DevelopConfig):
    """
    """
    DEBUG = False


config = {
    "develop": DevelopConfig,
    "product": ProductConfig
}


def check_env():
    if True:
        return config['develop']
    return config['product']
