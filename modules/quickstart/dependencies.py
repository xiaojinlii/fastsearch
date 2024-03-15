from fastapi import Depends, Query
from db.dependencies import Paging, QueryParams


class DepartmentParams(QueryParams):
    """
    列表分页
    """

    def __init__(
            self,
            name: str | None = Query(None, title="部门名称"),
            params: Paging = Depends()
    ):
        super().__init__(params)
        self.name = ("like", name)


class EmployeeParams(QueryParams):
    """
    列表分页
    """

    def __init__(
            self,
            name: str | None = Query(None, title="员工姓名"),
            nickname: str | None = Query(None, title="员工姓名"),
            params: Paging = Depends()
    ):
        super().__init__(params)
        self.name = ("like", name)
        self.nickname = ("like", nickname)
