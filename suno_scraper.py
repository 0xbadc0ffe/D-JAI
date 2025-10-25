"""
Suno.com scraper using Playwright with session authentication
"""
import asyncio
from playwright.async_api import async_playwright
import json


# Your session cookies
COOKIES = """_cfuvid=L6R_8Kw4h6QslS2PARIC8A0s3bFwTVdeNiz6qHzr8Go-1761399097042-0.0.1.1-604800000; singular_device_id=4c7a4775-4034-4438-b7fb-8784519e242d; _gcl_aw=GCL.1761399098.CjwKCAjw6vHHBhBwEiwAq4zvA0bAqYQ-QaetvNzEFYYR8bEcC1lKGGnRkVfUjjwRnfJ-Qu-hcOlA1BoCpYUQAvD_BwE; _gcl_gs=2.1.k1$i1761399094$u150337716; _gcl_au=1.1.2120159482.1761399098; _ga=GA1.1.272810979.1761399098; ajs_anonymous_id=574d0c16-2250-4180-baf4-dfa2bb7bfe0b; _axwrt=02e751ee-df3f-47c3-90fe-9893810b474e; _sp_ses.e685=*; _fbp=fb.1.1761399101056.464764066710241212; _tt_enable_cookie=1; _ttp=01K8DS2NT4FS99TRH4KQCFJXCN_.tt.1; _clck=1et9f5c%5E2%5Eg0g%5E0%5E2124; afUserId=c3a3d0e1-0eec-4016-a75a-51904f3fbfdc-p; AF_SYNC=1761399103232; __stripe_mid=3f5b4888-750a-4393-a7f6-9d8116e28d8d918368; __stripe_sid=de95e1b3-6f22-471a-be33-5a721c11c010b59458; _clsk=lsgafb%5E1761399116876%5E1%5E0%5Ez.clarity.ms%2Fcollect; __client=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImNsaWVudF8zNFltdG9RVzlGc3FQQlpOelMxeE9yY3IxTXUiLCJyb3RhdGluZ190b2tlbiI6InUxZzR0YWdtbWg4OHB3Mm5tOHJucmY4NGw0aXcweHJ2Ymp2ZDVqNmMifQ.vCxzKuADi_vgr3dyd-Ufexh_3ZcsKzhUTh6cSpOIZeZ5sRcAXeECnQ11amBnQQPBwGRr3WDoQIlaybqTSojpTULWjimydYFDv1pnKbmgk1PddZ-iLiVdxy5m3sZQVS8AVPS7P989gAtK-Rfwc2wp4-nXsI70yMfQNv8HjkrGZ8YJ5WizUfdePCaxfcyiBTiXxxrOtjYbW_0ByT5-Uvo9Fl_3LfmRL41PxWJRr93HbnllJWdlLicu306Wm18L3GvPb3R4jNgYYEEp4JLGHc1z0eSoM_dBgYCxi9QQ3vIJHyf07MCtWhOEV_KnN73DCkCuoAJ9MYihKf2-Iu72WkM6Mg; __client_uat=1761399130; __client_uat_U9tcbTPE=1761399130; __cf_bm=zUG.EHbH.TCyMNki9eBmrYW7kizOiY4UgodnIs3jZLs-1761400652-1.0.1.1-B3IqVsp2s_03GB4mFIkI.KWSmU5enIVFIpE8Ex9J0mxZxkeatsnSWIu5wT_EtpuJBaqZrwNQish7eo.6YpGV8CO5OAqOw4GGoTbullN71zc; _sp_id.e685=acd607cd-6e55-483a-9309-e6d1cb459a6b.1761399099.1.1761400838..cbd3a74c-f719-4249-b253-676474ca5a92..47bf6e5b-3c0c-4e6a-8b40-5ad686d8bf88.1761399099495.4; _ga_7B0KEDD7XP=GS2.1.s1761399098$o1$g1$t1761400838$j58$l0$h0; ttcsid=1761399101259::WUkQEZZjeriyJQoat-qW.1.1761400839000.0; ttcsid_CT67HURC77UB52N3JFBG=1761399101258::28o9tRTsZHf-Ep7n40Wc.1.1761400839001.0; ax_visitor=%7B%22firstVisitTs%22%3A1761399099489%2C%22lastVisitTs%22%3Anull%2C%22currentVisitStartTs%22%3A1761399099489%2C%22ts%22%3A1761400975506%2C%22visitCount%22%3A1%7D"""


def parse_cookies(cookie_string):
    """Parse cookie string into Playwright cookie format"""
    cookies = []
    for cookie in cookie_string.split('; '):
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            cookies.append({
                'name': name,
                'value': value,
                'domain': '.suno.com',
                'path': '/'
            })
    return cookies


async def scrape_suno():
    """Scrape Suno create page with authentication"""
    
    async with async_playwright() as p:
        # Launch browser (set headless=False to see what's happening)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Add cookies
        await context.add_cookies(parse_cookies(COOKIES))
        
        # Create page and navigate
        page = await context.new_page()
        
        # Set up network monitoring to capture API calls
        api_requests = []
        api_responses = []
        
        async def handle_request(request):
            if '/api/' in request.url or 'suno.com' in request.url:
                api_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers
                })
        
        async def handle_response(response):
            if '/api/' in response.url:
                try:
                    body = await response.json()
                    api_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'body': body
                    })
                except:
                    pass
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        print("Navigating to Suno create page...")
        await page.goto('https://suno.com/create?signup_source=splashpage&referrer=%2Fhome&redirected_from=signin')
        
        # Wait for page to load
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)  # Additional wait for dynamic content
        
        # Extract page content
        print("\nExtracting page content...")
        
        # Get page title
        title = await page.title()
        print(f"Page Title: {title}")
        
        # Get main content
        content = await page.content()
        
        # Try to find specific elements (adjust selectors based on actual page)
        try:
            # Look for input fields, buttons, song data, etc.
            text_content = await page.evaluate('''() => {
                return {
                    body_text: document.body.innerText,
                    inputs: Array.from(document.querySelectorAll('input')).map(i => ({
                        type: i.type,
                        placeholder: i.placeholder,
                        name: i.name
                    })),
                    buttons: Array.from(document.querySelectorAll('button')).map(b => b.innerText),
                    headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.innerText)
                }
            }''')
            
            print("\n=== Page Elements ===")
            print(f"Headings: {text_content['headings']}")
            print(f"Buttons: {text_content['buttons']}")
            print(f"Inputs: {text_content['inputs']}")
            
        except Exception as e:
            print(f"Error extracting elements: {e}")
        
        # Save API calls to file
        if api_responses:
            print(f"\n=== Captured {len(api_responses)} API Responses ===")
            with open('suno_api_responses.json', 'w', encoding='utf-8') as f:
                json.dump(api_responses, f, indent=2, ensure_ascii=False)
            print("API responses saved to suno_api_responses.json")
        
        # Save page HTML
        with open('suno_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("\nPage HTML saved to suno_page.html")
        
        # Take screenshot
        await page.screenshot(path='suno_screenshot.png', full_page=True)
        print("Screenshot saved to suno_screenshot.png")
        
        # Keep browser open for inspection (optional)
        print("\nPress Ctrl+C to close browser...")
        try:
await asyncio.sleep(60)  # Wait 60 seconds before closing

# Run playwright install to download the necessary browsers
# playwright install
        except KeyboardInterrupt:
            print("\nClosing browser...")
        
        await browser.close()


async def main():
    await scrape_suno()

if __name__ == '__main__':
    asyncio.run(main())
