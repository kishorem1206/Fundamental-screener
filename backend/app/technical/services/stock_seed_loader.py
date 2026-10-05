import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import text
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock, Universe, UniverseMembership
from app.logger import logger


class StockSeedLoader:
    def load_from_file(self, seed_path: str) -> dict:
        seed = json.loads(Path(seed_path).read_text(encoding="utf-8"))
        return self.load(seed)

    def load(self, seed: dict) -> dict:
        db = get_db()
        now = datetime.now(timezone.utc)

        try:
            # 1. Upsert universe definitions
            for u in seed["universes"]:
                existing = db.get(Universe, u["id"])
                if existing:
                    existing.name = u["name"]
                    existing.description = u.get("description")
                    existing.is_built_in = u.get("isBuiltIn", False)
                    existing.updated_at = now
                else:
                    db.add(Universe(
                        id=u["id"],
                        name=u["name"],
                        description=u.get("description"),
                        is_built_in=u.get("isBuiltIn", False),
                        stock_count=0,
                        created_at=now,
                        updated_at=now,
                    ))

            db.flush()

            # 2. Upsert stocks and memberships
            for s in seed["stocks"]:
                stock_id = f"{s['exchange']}:{s['symbol']}"
                existing = db.get(Stock, stock_id)
                if existing:
                    existing.company_name = s["companyName"]
                    existing.isin = s.get("isin")
                    existing.sector = s.get("sector")
                    existing.industry = s.get("industry")
                    existing.basic_industry = s.get("basicIndustry")
                    existing.macro_sector = s.get("macroSector")
                    existing.market_cap_category = s.get("marketCapCategory")
                    existing.updated_at = now
                else:
                    db.add(Stock(
                        id=stock_id,
                        symbol=s["symbol"],
                        exchange=s["exchange"],
                        company_name=s["companyName"],
                        isin=s.get("isin"),
                        kite_instrument_token=s.get("kiteInstrumentToken"),
                        tradingview_symbol=s.get("tradingviewSymbol"),
                        sector=s.get("sector"),
                        industry=s.get("industry"),
                        basic_industry=s.get("basicIndustry"),
                        macro_sector=s.get("macroSector"),
                        market_cap_category=s.get("marketCapCategory"),
                        is_active=True,
                        created_at=now,
                        updated_at=now,
                    ))

                db.flush()

                # Upsert memberships (insert if not present)
                for universe_id in s.get("universes", []):
                    existing_m = db.get(UniverseMembership, {"universe_id": universe_id, "stock_id": stock_id})
                    if not existing_m:
                        db.add(UniverseMembership(
                            universe_id=universe_id,
                            stock_id=stock_id,
                            added_at=now,
                        ))

            db.flush()

            # 3. Refresh stock_count on each universe
            for u in seed["universes"]:
                db.execute(text("""
                    UPDATE universes
                    SET stock_count    = (SELECT COUNT(*) FROM universe_memberships WHERE universe_id = :uid),
                        last_synced_at = NOW(),
                        updated_at     = NOW()
                    WHERE id = :uid
                """), {"uid": u["id"]})

            db.commit()

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        result = {"processed": len(seed["stocks"]), "universes": len(seed["universes"])}
        logger.info("Stock seed complete", **result)
        return result


stock_seed_loader = StockSeedLoader()
