import asyncio
import os
from playwright.async_api import async_playwright

async def debug_creator():
    user_data_dir = "/Users/frankie/.playwright-user-data"
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        print(f"Opening creator dashboard...")
        await page.goto("https://creator.xiaohongshu.com/publish/publish")
        await asyncio.sleep(10)
        
        url = page.url
        print(f"Current URL: {url}")
        
        await page.screenshot(path="creator_debug.png")
        
        # Look for the specific elements
        items = await page.query_selector_all("div.publish-type-item")
        print(f"Found {len(items)} publish type items.")
        for i, item in enumerate(items):
            text = await item.inner_text()
            print(f"Item {i}: {text}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_creator())
