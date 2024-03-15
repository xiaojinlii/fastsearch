from pydantic import BaseModel, ConfigDict


class Department(BaseModel):
    name: str


class DepartmentSimpleOut(Department):
    model_config = ConfigDict(from_attributes=True)

    id: int


class Employee(BaseModel):
    name: str
    nickname: str | None = None


class EmployeeSimpleOut(Employee):
    model_config = ConfigDict(from_attributes=True)

    id: int


class EmployeeIn(Employee):
    """
    创建员工
    """
    dep_id: int


class EmployeeUpdate(BaseModel):
    """
    更新用户详细信息
    """
    name: str | None = None
    nickname: str | None = None


class DepartmentOut(DepartmentSimpleOut):
    model_config = ConfigDict(from_attributes=True)

    employees: list[EmployeeSimpleOut] = []


class EmployeeOut(EmployeeSimpleOut):
    model_config = ConfigDict(from_attributes=True)

    department: DepartmentSimpleOut
