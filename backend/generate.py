
import os
from getpass import getpass

from kiteconnect import KiteConnect
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("KITE_API_KEY")
api_secret = os.getenv("KITE_API_SECRET")

if not api_key:
    api_key = input("Kite API key: ").strip()

if not api_secret:
    api_secret = getpass("Kite API secret: ").strip()

kite = KiteConnect(api_key=api_key)

print("\nOpen this URL and log in to Zerodha:")
print(kite.login_url())

request_token = input(
    "\nPaste the request_token from the redirect URL: "
).strip()

session = kite.generate_session(
    request_token,
    api_secret=api_secret,
)

access_token = session["access_token"]

print("\nYour access token has been generated.")
print("Add this line to your backend .env file:")
print(f"KITE_ACCESS_TOKEN={access_token}")
