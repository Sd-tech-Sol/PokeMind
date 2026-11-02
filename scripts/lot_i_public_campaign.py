"""Explicit public-only campaign entry point; dry-run unless requested."""
from pokemind.public_campaign import main

if __name__ == "__main__":
    raise SystemExit(main())
