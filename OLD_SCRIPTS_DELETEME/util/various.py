import tempfile
import webbrowser

def browser_open(html, link=None):
    chrome_path = '/usr/bin/google-chrome %s' # does not work with snap-installed firefox and chromium >.<
    browser = webbrowser.get(chrome_path)
    if link is None:
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
            url = 'file://' + f.name
            f.write(html)
            f.flush()
            print(f"Opening in Browser: {url}")
            browser.open(url)
    else:
        browser.open(link)