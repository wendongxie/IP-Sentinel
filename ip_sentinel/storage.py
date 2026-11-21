"""SQLite history and consistent per-family change tracking."""
from dataclasses import asdict

from sqlalchemy import JSON, Column, Integer, MetaData, String, Table, create_engine, func, select

schema = MetaData()
history = Table(
    "history", schema,
    Column("id", Integer, primary_key=True),
    Column("observed_at", String, nullable=False, index=True),
    Column("family", Integer, nullable=False, index=True),
    Column("ip", String, nullable=False, index=True),
    Column("previous", String, nullable=False),
    Column("evidence", JSON, nullable=False),
)


class History:
    def __init__(self, path):
        self.engine = create_engine("sqlite://", creator=lambda: self._connect(path))
        schema.create_all(self.engine)

    @staticmethod
    def _connect(path):
        import sqlite3
        return sqlite3.connect(path, timeout=15, check_same_thread=False)

    def record(self, timestamp, observations):
        with self.engine.begin() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            for obs in observations:
                previous = connection.scalar(
                    select(history.c.ip)
                    .where(history.c.family == obs.family, history.c.ip != "")
                    .order_by(history.c.id.desc()).limit(1)
                )
                obs.previous = previous if previous and obs.ip and obs.ip != previous else ""
                connection.execute(history.insert().values(
                    observed_at=timestamp.isoformat(), family=obs.family, ip=obs.ip,
                    previous=obs.previous, evidence=asdict(obs),
                ))

    def query(self, search="", page=0, size=100):
        query = select(history).where(history.c.ip.contains(search, autoescape=True))
        with self.engine.connect() as connection:
            total, changes, unique = connection.execute(select(
                func.count(), func.count().filter(history.c.previous != ""),
                func.count(func.distinct(func.nullif(history.c.ip, ""))),
            ).where(history.c.ip.contains(search, autoescape=True))).one()
            rows = connection.execute(
                query.order_by(history.c.id.desc()).limit(size).offset(page * size)
            ).mappings().all()
        return rows, (total, changes, unique)

    def export(self, path, search=""):
        import csv
        import json
        with self.engine.connect() as connection, open(path, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(("UTC", "协议", "出口 IP", "原 IP", "证据 JSON"))
            for row in connection.execute(select(history).where(
                history.c.ip.contains(search, autoescape=True)
            ).order_by(history.c.id.desc())):
                writer.writerow((row.observed_at, f"IPv{row.family}", row.ip, row.previous,
                                 json.dumps(row.evidence, ensure_ascii=False)))
