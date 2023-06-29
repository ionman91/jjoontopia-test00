from datetime import datetime

from sqlalchemy import Column, BIGINT, DateTime
from sqlalchemy.orm import as_declarative


@as_declarative()
class Base:
    id = Column(BIGINT, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
