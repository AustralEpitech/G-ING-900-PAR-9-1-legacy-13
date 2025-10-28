"""Example plugin for geneweb_py.

This plugin demonstrates the minimal contract: it registers a route and
optionally can serve static assets or templates in a real plugin.
"""
from fastapi import APIRouter, Request


def register(app=None, storage=None, config=None, templates=None):
    router = APIRouter()

    @router.get("/hello-plugin", response_class=None)
    def hello_plugin(request: Request):
        # If templates were provided by the host, render a template; otherwise return JSON
        if templates is not None:
            return templates.TemplateResponse(
                "example_plugin/hello.html",
                {"request": request, "persons": len(list(storage.list_persons()))},
            )
        return {"msg": "Hello from example_plugin", "persons": len(list(storage.list_persons()))}

    app.include_router(router)


def on_startup(app=None):
    # example startup hook: log plugin activation
    print("example_plugin: on_startup called")


def on_shutdown(app=None):
    print("example_plugin: on_shutdown called")
