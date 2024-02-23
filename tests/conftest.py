def pytest_configure(config):
    """ https://stackoverflow.com/a/35394239/15637940 """
    import sys
    from tests import test_config
    sys.modules['config'] = test_config
