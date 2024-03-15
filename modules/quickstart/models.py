from typing import List

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.model_base import BaseModel


class Department(BaseModel):
    __tablename__ = "department"
    __table_args__ = ({'comment': '部门表'})

    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False, comment="部门名称")

    employees: Mapped[List["Employee"]] = relationship(back_populates="department")

    def __repr__(self):
        return f"id: {self.id}, name:{self.name}"


class Employee(BaseModel):
    __tablename__ = "employee"
    __table_args__ = ({'comment': '员工表'})

    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False, comment="姓名")
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="昵称")
    dep_id: Mapped[int] = mapped_column(ForeignKey("department.id", ondelete='CASCADE'))

    department: Mapped[Department] = relationship(back_populates="employees")

    def __repr__(self):
        return f"id: {self.id}, dep_id: {self.dep_id}, name:{self.name}"
