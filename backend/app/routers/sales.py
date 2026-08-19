from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sale import Sale
from app.schemas.sale import FilterOptions, SaleOut, SeriesPoint, SummaryOut

router = APIRouter(prefix="/api/sales", tags=["sales"])


def _apply_filters(
    stmt,
    date_from: date | None,
    date_to: date | None,
    category: str | None,
    region: str | None,
    channel: str | None,
):
    if date_from:
        stmt = stmt.where(Sale.date >= date_from)
    if date_to:
        stmt = stmt.where(Sale.date <= date_to)
    if category:
        stmt = stmt.where(Sale.category == category)
    if region:
        stmt = stmt.where(Sale.region == region)
    if channel:
        stmt = stmt.where(Sale.channel == channel)
    return stmt


@router.get("", response_model=list[SaleOut])
def list_sales(
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
    region: str | None = None,
    channel: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = select(Sale).order_by(Sale.date.desc())
    stmt = _apply_filters(stmt, date_from, date_to, category, region, channel)
    stmt = stmt.limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@router.get("/filters/options", response_model=FilterOptions)
def filter_options(db: Session = Depends(get_db)):
    categories = db.execute(select(Sale.category).distinct().order_by(Sale.category)).scalars().all()
    regions = db.execute(select(Sale.region).distinct().order_by(Sale.region)).scalars().all()
    channels = db.execute(select(Sale.channel).distinct().order_by(Sale.channel)).scalars().all()
    date_min, date_max = db.execute(select(func.min(Sale.date), func.max(Sale.date))).one()
    return FilterOptions(
        categories=categories, regions=regions, channels=channels,
        date_min=date_min, date_max=date_max,
    )


def _group_series(db: Session, group_col, filters) -> list[SeriesPoint]:
    stmt = select(group_col.label("label"), func.sum(Sale.revenue), func.sum(Sale.units))
    stmt = _apply_filters(stmt, *filters).group_by(group_col).order_by(group_col)
    rows = db.execute(stmt).all()
    return [SeriesPoint(label=str(r[0]), revenue=float(r[1] or 0), units=int(r[2] or 0)) for r in rows]


@router.get("/summary", response_model=SummaryOut)
def summary(
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
    region: str | None = None,
    channel: str | None = None,
    db: Session = Depends(get_db),
):
    filters = (date_from, date_to, category, region, channel)

    totals_stmt = select(
        func.coalesce(func.sum(Sale.revenue), 0),
        func.coalesce(func.sum(Sale.units), 0),
        func.count(Sale.id),
    )
    totals_stmt = _apply_filters(totals_stmt, *filters)
    total_revenue, total_units, total_sales = db.execute(totals_stmt).one()

    month_expr = func.to_char(Sale.date, "YYYY-MM")
    by_month = _group_series(db, month_expr, filters)
    by_category = _group_series(db, Sale.category, filters)
    by_region = _group_series(db, Sale.region, filters)
    by_channel = _group_series(db, Sale.channel, filters)

    average_ticket = float(total_revenue) / total_sales if total_sales else 0.0

    return SummaryOut(
        total_revenue=float(total_revenue),
        total_units=int(total_units),
        total_sales=int(total_sales),
        average_ticket=round(average_ticket, 2),
        by_month=by_month,
        by_category=by_category,
        by_region=by_region,
        by_channel=by_channel,
    )
