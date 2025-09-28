from datetime import datetime
from typing import Annotated

from sqlalchemy import String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry

str_1 = Annotated[str, 1]
str_50 = Annotated[str, 50]
str_100 = Annotated[str, 100]


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    registry = registry(
        type_annotation_map={
            str_1: String(1),
            str_50: String(50),
            str_100: String(100),
        }
    )
