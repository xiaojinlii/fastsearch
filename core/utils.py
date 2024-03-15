import importlib
from core.logger import logger


def import_modules(modules: list, desc: str):
    for module in modules:
        if not module:
            continue
        try:
            # 动态导入模块
            importlib.import_module(module[0:module.rindex(".")])
        except ModuleNotFoundError:
            logger.error(f"AttributeError：导入{desc}失败，未找到该模块：{module}")


async def import_modules_async(modules: list, desc: str):
    for module in modules:
        if not module:
            continue
        try:
            # 动态导入模块
            module_pag = importlib.import_module(module[0:module.rindex(".")])
        except ModuleNotFoundError:
            logger.error(f"ModuleNotFoundError：导入{desc}失败，未找到该模块：{module}")


def import_functions(modules: list, desc: str, **kwargs):
    for module in modules:
        if not module:
            continue
        try:
            # 动态导入模块
            module_pag = importlib.import_module(module[0:module.rindex(".")])
            getattr(module_pag, module[module.rindex(".") + 1:])(**kwargs)
        except ModuleNotFoundError:
            logger.error(f"ModuleNotFoundError：导入{desc}失败，未找到该模块：{module}")
        except AttributeError:
            logger.error(f"AttributeError：导入{desc}失败，未找到该模块下的方法：{module}")


async def import_functions_async(modules: list, desc: str, **kwargs):
    for module in modules:
        if not module:
            continue
        try:
            # 动态导入模块
            module_pag = importlib.import_module(module[0:module.rindex(".")])
            await getattr(module_pag, module[module.rindex(".") + 1:])(**kwargs)
        except ModuleNotFoundError:
            logger.error(f"ModuleNotFoundError：导入{desc}失败，未找到该模块：{module}")
        except AttributeError:
            logger.error(f"AttributeError：导入{desc}失败，未找到该模块下的方法：{module}")
