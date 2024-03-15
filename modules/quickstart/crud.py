from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import DalBase
from . import models, schemas


class DepartmentDal(DalBase):
    def __init__(self, db: AsyncSession):
        super(DepartmentDal, self).__init__()
        self.db = db
        self.model = models.Department
        self.schema = schemas.DepartmentSimpleOut


class EmployeeDal(DalBase):
    def __init__(self, db: AsyncSession):
        super(EmployeeDal, self).__init__()
        self.db = db
        self.model = models.Employee
        self.schema = schemas.EmployeeSimpleOut
