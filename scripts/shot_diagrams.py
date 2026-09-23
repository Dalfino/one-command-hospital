"""Screenshot diagram HTMLs at 2x device scale factor for 300dpi print quality."""
import asyncio
from playwright.async_api import async_playwright

JOBS = [
    ("/home/z/my-project/scripts/diagram_arch.html", "/home/z/my-project/scripts/assets/diagram_arch.png", 1000),
    ("/home/z/my-project/scripts/diagram_fhir.html", "/home/z/my-project/scripts/assets/diagram_fhir.png", 1120),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for html, png, width in JOBS:
            page = await browser.new_page(viewport={"width": width, "height": 400}, device_scale_factor=2)
            await page.goto(f"file://{html}")
            await page.wait_for_timeout(300)
            body = await page.evaluate("document.body.scrollHeight")
            await page.set_viewport_size({"width": width, "height": body})
            await page.screenshot(path=png, full_page=True)
            print(f"OK {png} ({width}x{body} @2x)")
            await page.close()
        await browser.close()

asyncio.run(main())
