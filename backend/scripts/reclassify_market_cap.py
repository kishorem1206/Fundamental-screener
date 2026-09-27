"""Rank-based market-cap tiers: 1-100 LARGE, 101-250 MID,
rest (251+) SMALL. Writes stocks.market_cap_rank + market_cap_category.
Re-run after market caps are refreshed."""
from sqlalchemy import text

from app.infrastructure.database.client import get_session_factory

db = get_session_factory()()
db.execute(text("update stocks set market_cap_rank=null, market_cap_category=null"))
db.execute(text("""update stocks s set market_cap_rank=r.rk, market_cap_category = case
  when r.rk<=100 then 'LARGE_CAP' when r.rk<=250 then 'MID_CAP' else 'SMALL_CAP' end
  from (select id, row_number() over (order by market_cap desc, id) rk from stocks where market_cap is not null) r
  where r.id=s.id"""))
db.commit()
for row in db.execute(text("select market_cap_category,count(*),round(max(market_cap)/1e7),round(min(market_cap)/1e7) from stocks group by 1 order by 3 desc nulls last")):
    print(row)
print(db.execute(text("select market_cap_rank,market_cap_category from stocks where id='NSE:JSLL'")).fetchall())
