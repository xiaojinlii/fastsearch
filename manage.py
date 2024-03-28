import os


def main():
    """Run administrative tasks."""
    os.environ.setdefault('XIAOAPI_SETTINGS_MODULE', 'application.settings')
    os.environ.setdefault('XIAOAPI_ROUTES_MODULE', 'application.routes.register_routes')
    try:
        from xiaoapi.management import manage_typer
        from modules.fastsearch.commands import sqlalchemy_typer
    except ImportError as exc:
        raise ImportError(
            "Couldn't import xiaoapi. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    manage_typer.add_typer(sqlalchemy_typer, name="sqlalchemy", help="sqlalchemy命令")
    manage_typer()


if __name__ == '__main__':
    main()
