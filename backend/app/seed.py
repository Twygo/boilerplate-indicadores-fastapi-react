"""Popula o banco com dados fake de vendas pra ter indicador pra mostrar de cara.

Uso: python -m app.seed
"""

import random
from datetime import date, timedelta

from faker import Faker

from app.core.database import Base, SessionLocal, engine
from app.models.sale import Sale

fake = Faker("pt_BR")

CATEGORIES = ["Eletrônicos", "Moda", "Casa", "Livros", "Esporte"]
REGIONS = ["Sudeste", "Sul", "Nordeste", "Norte", "Centro-Oeste"]
CHANNELS = ["Site", "App", "Loja física", "Marketplace"]


def run(n: int = 1200):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Sale).first():
            print("Já tem dados, pulando seed.")
            return

        today = date.today()
        start = today - timedelta(days=365)
        rows = []
        for _ in range(n):
            d = start + timedelta(days=random.randint(0, 365))
            units = random.randint(1, 20)
            unit_price = round(random.uniform(15, 800), 2)
            rows.append(
                Sale(
                    date=d,
                    category=random.choice(CATEGORIES),
                    region=random.choice(REGIONS),
                    channel=random.choice(CHANNELS),
                    revenue=round(units * unit_price, 2),
                    units=units,
                )
            )
        db.bulk_save_objects(rows)
        db.commit()
        print(f"Seed ok: {n} registros de venda criados.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
