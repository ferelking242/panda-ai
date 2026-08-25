try:
    from src.browser.manager import BrowserManager as Browser
except (ImportError, ModuleNotFoundError):
    # patchright/playwright not available (e.g. ARM64 Alpine)
    Browser = None
