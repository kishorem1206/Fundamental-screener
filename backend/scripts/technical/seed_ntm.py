#!/usr/bin/env python3
"""Seed the database with Nifty Total Market stocks from scripts/seeds/nifty_total_market.json."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from app.technical.services.stock_seed_loader import stock_seed_loader
from app.infrastructure.database.client import close_database

SEED_FILE = Path(__file__).parent / "seeds" / "nifty_total_market.json"


def main() -> None:
    print(f"Seeding NTM stocks from: {SEED_FILE}")
    try:
        result = stock_seed_loader.load_from_file(str(SEED_FILE))
        print(f"✓ Seed complete — processed {result['processed']} stocks across {result['universes']} universes")
    finally:
        close_database()


if __name__ == "__main__":
    main()
