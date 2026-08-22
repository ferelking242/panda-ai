"""
Profile scraper — extracts user info from AI provider web UIs.

Each provider has a different UI structure for user profile display.
This module provides provider-specific scraping via browser JS evaluation.
"""

from __future__ import annotations

from patchright.async_api import Page
from src.log import setup_logging

log = setup_logging("profile")


async def scrape_chatgpt_profile(page: Page) -> dict:
    """Extract ChatGPT user profile from the sidebar/account menu."""
    try:
        # Click the user menu button to reveal profile info
        menu_selectors = [
            "button[data-testid='profile-button']",
            "button[aria-label='User menu']",
            "button[aria-label='Profile']",
            "#profile-button",
        ]
        for sel in menu_selectors:
            try:
                btn = await page.query_selector(sel)
                if btn and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    break
            except Exception:
                continue

        # Extract profile data from the opened menu
        profile = await page.evaluate(
            """
            () => {
                const result = { name: '', email: '', avatar_url: '', plan: '' };

                // Avatar
                const avatar = document.querySelector(
                    'img[data-testid="profile-button"] img, ' +
                    'img[alt*="User"], img[alt*="Profile"], ' +
                    'nav img[class*="avatar"], [class*="profile"] img'
                );
                if (avatar) result.avatar_url = avatar.src || '';

                // Name — look in the menu dropdown
                const menuItems = document.querySelectorAll(
                    '[role="menuitem"], [data-state="open"] div, [class*="dropdown"] div'
                );
                for (const item of menuItems) {
                    const text = (item.innerText || '').trim();
                    // Email pattern
                    if (text.includes('@') && text.includes('.') && text.length < 100) {
                        result.email = text;
                    }
                    // Plan detection
                    if (text.toLowerCase().includes('plus')) result.plan = 'Plus';
                    if (text.toLowerCase().includes('pro')) result.plan = 'Pro';
                    if (text.toLowerCase().includes('free')) result.plan = 'Free';
                    if (text.toLowerCase().includes('team')) result.plan = 'Team';
                    if (text.toLowerCase().includes('enterprise')) result.plan = 'Enterprise';
                }

                // Name from page title or account section
                const nameEl = document.querySelector(
                    '[class*="profile"] [class*="name"], ' +
                    '[data-testid*="name"], h3[class*="user"]'
                );
                if (nameEl) result.name = nameEl.innerText.trim();

                // Close menu by pressing Escape
                return result;
            }
            """
        )

        # Press Escape to close any opened menu
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)

        profile["provider"] = "chatgpt"
        log.info(f"ChatGPT profile: {profile}")
        return profile

    except Exception as e:
        log.error(f"Failed to scrape ChatGPT profile: {e}")
        return {"name": "", "email": "", "avatar_url": "", "plan": "", "provider": "chatgpt"}


async def scrape_claude_profile(page: Page) -> dict:
    """Extract Claude user profile from the sidebar."""
    try:
        profile = await page.evaluate(
            """
            () => {
                const result = { name: '', email: '', avatar_url: '', plan: '' };

                // Avatar
                const avatar = document.querySelector(
                    'img[data-testid*="avatar"], img[alt*="avatar"], ' +
                    'button[data-testid*="user"] img, [class*="avatar"] img'
                );
                if (avatar) result.avatar_url = avatar.src || '';

                // Look for account menu
                const menuBtn = document.querySelector(
                    'button[data-testid="user-menu"], button[aria-label="Account"]'
                );
                if (menuBtn) menuBtn.click();

                // Email from account dropdown
                const allText = document.body.innerText;
                const emailMatch = allText.match(/[\\w.-]+@[\\w.-]+\\.\\w+/);
                if (emailMatch) result.email = emailMatch[0];

                // Plan detection
                if (allText.includes('Claude Pro') || allText.includes('Pro plan')) result.plan = 'Pro';
                if (allText.includes('Claude Free') || allText.includes('Free plan')) result.plan = 'Free';
                if (allText.includes('Claude Team')) result.plan = 'Team';
                if (allText.includes('Claude Enterprise')) result.plan = 'Enterprise';

                return result;
            }
            """
        )

        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)

        profile["provider"] = "claude"
        log.info(f"Claude profile: {profile}")
        return profile

    except Exception as e:
        log.error(f"Failed to scrape Claude profile: {e}")
        return {"name": "", "email": "", "avatar_url": "", "plan": "", "provider": "claude"}


async def scrape_gemini_profile(page: Page) -> dict:
    """Extract Gemini/AI Studio user profile."""
    try:
        profile = await page.evaluate(
            """
            () => {
                const result = { name: '', email: '', avatar_url: '', plan: '' };

                // Google account avatar (circular image in top-right)
                const avatar = document.querySelector(
                    'img[data-profile-identifier], img[aria-label*="Account"], ' +
                    'a[aria-label*="Account"] img, img[class*="gb_A"]'
                );
                if (avatar) result.avatar_url = avatar.src || '';

                // Email from account chip
                const emailEl = document.querySelector(
                    '[data-email], [aria-label*="@"], .gb_Dg'
                );
                if (emailEl) {
                    result.email = emailEl.getAttribute('data-email') ||
                                   emailEl.getAttribute('aria-label') || '';
                }

                // Name
                const nameEl = document.querySelector(
                    '[data-name], .gb_Fg, [aria-label*="Account"]'
                );
                if (nameEl) result.name = nameEl.getAttribute('data-name') ||
                                           nameEl.innerText?.trim() || '';

                return result;
            }
            """
        )

        profile["provider"] = "gemini"
        profile["plan"] = "Google AI"  # Gemini doesn't have visible plans
        log.info(f"Gemini profile: {profile}")
        return profile

    except Exception as e:
        log.error(f"Failed to scrape Gemini profile: {e}")
        return {"name": "", "email": "", "avatar_url": "", "plan": "", "provider": "gemini"}


async def scrape_deepseek_profile(page: Page) -> dict:
    """Extract DeepSeek user profile."""
    try:
        profile = await page.evaluate(
            """
            () => {
                const result = { name: '', email: '', avatar_url: '', plan: '' };
                const avatar = document.querySelector('img[class*="avatar"], img[alt*="avatar"]');
                if (avatar) result.avatar_url = avatar.src || '';
                const allText = document.body.innerText;
                const emailMatch = allText.match(/[\\w.-]+@[\\w.-]+\\.\\w+/);
                if (emailMatch) result.email = emailMatch[0];
                if (allText.includes('DeepSeek Pro')) result.plan = 'Pro';
                if (allText.includes('DeepSeek Free')) result.plan = 'Free';
                return result;
            }
            """
        )
        profile["provider"] = "deepseek"
        return profile
    except Exception as e:
        return {"name": "", "email": "", "avatar_url": "", "plan": "", "provider": "deepseek"}


async def scrape_grok_profile(page: Page) -> dict:
    """Extract Grok user profile."""
    try:
        profile = await page.evaluate(
            """
            () => {
                const result = { name: '', email: '', avatar_url: '', plan: '' };
                const avatar = document.querySelector('img[class*="avatar"], img[alt*="profile"]');
                if (avatar) result.avatar_url = avatar.src || '';
                const allText = document.body.innerText;
                const emailMatch = allText.match(/[\\w.-]+@[\\w.-]+\\.\\w+/);
                if (emailMatch) result.email = emailMatch[0];
                return result;
            }
            """
        )
        profile["provider"] = "grok"
        return profile
    except Exception as e:
        return {"name": "", "email": "", "avatar_url": "", "plan": "", "provider": "grok"}


async def scrape_mistral_profile(page: Page) -> dict:
    """Extract Mistral user profile."""
    try:
        profile = await page.evaluate(
            """
            () => {
                const result = { name: '', email: '', avatar_url: '', plan: '' };
                const avatar = document.querySelector('img[class*="avatar"], img[alt*="avatar"]');
                if (avatar) result.avatar_url = avatar.src || '';
                const allText = document.body.innerText;
                const emailMatch = allText.match(/[\\w.-]+@[\\w.-]+\\.\\w+/);
                if (emailMatch) result.email = emailMatch[0];
                return result;
            }
            """
        )
        profile["provider"] = "mistral"
        return profile
    except Exception as e:
        return {"name": "", "email": "", "avatar_url": "", "plan": "", "provider": "mistral"}


async def scrape_qwen_profile(page: Page) -> dict:
    """Extract Qwen user profile."""
    try:
        profile = await page.evaluate(
            """
            () => {
                const result = { name: '', email: '', avatar_url: '', plan: '' };
                const avatar = document.querySelector('img[class*="avatar"], img[alt*="avatar"]');
                if (avatar) result.avatar_url = avatar.src || '';
                const allText = document.body.innerText;
                const emailMatch = allText.match(/[\\w.-]+@[\\w.-]+\\.\\w+/);
                if (emailMatch) result.email = emailMatch[0];
                return result;
            }
            """
        )
        profile["provider"] = "qwen"
        return profile
    except Exception as e:
        return {"name": "", "email": "", "avatar_url": "", "plan": "", "provider": "qwen"}


async def scrape_kimi_profile(page: Page) -> dict:
    """Extract Kimi user profile."""
    try:
        profile = await page.evaluate(
            """
            () => {
                const result = { name: '', email: '', avatar_url: '', plan: '' };
                const avatar = document.querySelector('img[class*="avatar"], img[alt*="avatar"]');
                if (avatar) result.avatar_url = avatar.src || '';
                const allText = document.body.innerText;
                const emailMatch = allText.match(/[\\w.-]+@[\\w.-]+\\.\\w+/);
                if (emailMatch) result.email = emailMatch[0];
                return result;
            }
            """
        )
        profile["provider"] = "kimi"
        return profile
    except Exception as e:
        return {"name": "", "email": "", "avatar_url": "", "plan": "", "provider": "kimi"}


# Provider → scraper mapping
_PROFILE_SCRAPERS = {
    "chatgpt": scrape_chatgpt_profile,
    "claude": scrape_claude_profile,
    "gemini": scrape_gemini_profile,
    "deepseek": scrape_deepseek_profile,
    "grok": scrape_grok_profile,
    "mistral": scrape_mistral_profile,
    "qwen": scrape_qwen_profile,
    "kimi": scrape_kimi_profile,
}


async def get_profile(page: Page, provider: str) -> dict:
    """
    Get the current user's profile from any supported provider.

    Returns dict with: name, email, avatar_url, plan, provider
    """
    scraper = _PROFILE_SCRAPERS.get(provider)
    if not scraper:
        log.warning(f"No profile scraper for provider: {provider}")
        return {"name": "", "email": "", "avatar_url": "", "plan": "", "provider": provider}
    return await scraper(page)
