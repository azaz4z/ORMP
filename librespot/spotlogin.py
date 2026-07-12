from librespot.core import Session
import webbrowser

# This will pass the auth url to the method

def auth_url_callback(url):
    webbrowser.open(url)

# This is the response sent to the browser once the flow has been completed successfully
success_page = "<html><body><h1>Login Successful</h1><p>You can close this window now.</p><script>setTimeout(() => {window.close()}, 100);</script></body></html>"

session = Session.Builder() \
    .oauth(auth_url_callback, success_page) \
    .create()