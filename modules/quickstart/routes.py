from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from utils.response import SuccessResponse
from db.database import db_getter
from db.dependencies import IdList
from . import schemas, models, crud
from .dependencies import EmployeeParams, DepartmentParams

router = APIRouter()


@router.get("/test", summary="测试接口")
def test():
    return SuccessResponse(data="hello world!")


@router.get("/employees", summary="获取员工列表")
async def get_employees(
        params: EmployeeParams = Depends(),
        db: AsyncSession = Depends(db_getter)
):
    model = models.Employee
    options = [joinedload(model.department)]
    schema = schemas.EmployeeOut
    datas, count = await crud.EmployeeDal(db).get_datas(
        **params.dict(),
        v_options=options,
        v_schema=schema,
        v_return_count=True
    )
    return SuccessResponse(datas, count=count)


@router.post("/employees", summary="创建员工")
async def create_employee(data: schemas.EmployeeIn, db: AsyncSession = Depends(db_getter)):
    return SuccessResponse(await crud.EmployeeDal(db).create_data(data=data))


@router.delete("/employees", summary="批量删除员工", description="软删除，删除后清空所关联的部门")
async def delete_employee(ids: IdList = Depends(), db: AsyncSession = Depends(db_getter)):
    await crud.EmployeeDal(db).delete_datas(ids=ids.ids)
    return SuccessResponse("删除成功")


@router.put("/employees/{data_id}", summary="更新员工信息")
async def put_employee(
        data_id: int,
        data: schemas.EmployeeUpdate,
        db: AsyncSession = Depends(db_getter)
):
    return SuccessResponse(await crud.EmployeeDal(db).put_data(data_id, data))


@router.get("/employees/{data_id}", summary="获取员工信息")
async def get_employee(data_id: int, db: AsyncSession = Depends(db_getter)):
    return SuccessResponse(await crud.EmployeeDal(db).get_data(data_id, v_schema=schemas.EmployeeOut))


@router.get("/departments", summary="获取部门列表")
async def get_departments(
        params: DepartmentParams = Depends(),
        db: AsyncSession = Depends(db_getter)
):
    model = models.Department
    options = [joinedload(model.employees)]
    schema = schemas.DepartmentOut
    datas, count = await crud.DepartmentDal(db).get_datas(
        **params.dict(),
        v_options=options,
        v_schema=schema,
        v_return_count=True
    )
    return SuccessResponse(datas, count=count)


@router.post("/departments", summary="创建部门")
async def create_department(data: schemas.Department, db: AsyncSession = Depends(db_getter)):
    return SuccessResponse(await crud.DepartmentDal(db).create_data(data=data))


@router.delete("/departments", summary="批量删除部门")
async def delete_department(ids: IdList = Depends(), db: AsyncSession = Depends(db_getter)):
    await crud.DepartmentDal(db).delete_datas(ids=ids.ids)
    return SuccessResponse("删除成功")


@router.get("/departments/{data_id}", summary="获取部门信息")
async def get_department(data_id: int, db: AsyncSession = Depends(db_getter)):
    model = models.Department
    options = [joinedload(model.employees)]
    schema = schemas.DepartmentOut
    return SuccessResponse(await crud.DepartmentDal(db).get_data(data_id, v_options=options, v_schema=schema))
