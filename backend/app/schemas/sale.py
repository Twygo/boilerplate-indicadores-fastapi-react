from datetime import date

from pydantic import BaseModel, ConfigDict


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    date: date
    category: str
    region: str
    channel: str
    revenue: float
    units: int


class FilterOptions(BaseModel):
    categories: list[str]
    regions: list[str]
    channels: list[str]
    date_min: date | None
    date_max: date | None


class SeriesPoint(BaseModel):
    label: str
    revenue: float
    units: int


class SummaryOut(BaseModel):
    total_revenue: float
    total_units: int
    total_sales: int
    average_ticket: float
    by_month: list[SeriesPoint]
    by_category: list[SeriesPoint]
    by_region: list[SeriesPoint]
    by_channel: list[SeriesPoint]
