import os
import subprocess
import time
from playwright.sync_api import sync_playwright

def main():
    print("Starting backend...")
    backend_process = subprocess.Popen(["python", "RBackend.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    
    html_path = f"file:///{os.path.abspath('WebUI.HTML').replace(chr(92), '/')}"
    os.makedirs("docs/images", exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        print(f"Opening {html_path}")
        page.goto(html_path)
        
        page.wait_for_timeout(2000)
        
        tabs = [
            ("overview", "tab_0_overview"),
            ("dialogs", "tab_1_dialogs"),
            ("glossary", "tab_2_glossary"),
            ("publish", "tab_3_publish"),
            ("characters", "tab_4_characters"),
            ("adult", "tab_5_adult"),
            ("editor", "tab_6_editor"),
            ("results", "tab_7_results")
        ]
        
        for tab_id, filename in tabs:
            print(f"Clicking tab: {tab_id}")
            try:
                page.click(f'.tab-button[data-tab="{tab_id}"]')
                page.wait_for_timeout(1000)
                screenshot_path = f"docs/images/{filename}.png"
                page.screenshot(path=screenshot_path)
                print(f"Saved {screenshot_path}")
            except Exception as e:
                print(f"Failed on tab {tab_id}: {e}")
            
        browser.close()
        
    print("Terminating backend...")
    backend_process.terminate()

if __name__ == "__main__":
    main()
