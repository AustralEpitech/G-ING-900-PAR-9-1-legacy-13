"""Simple plugin loader for geneweb_py.

Plugin contract:
- A plugin is a Python package placed under the top-level `plugins/` directory.
- The package should expose a `register(app, storage, config)` function which will
  be called at application startup. Plugins may also expose `on_startup(app)` and
  `on_shutdown(app)` optional hooks.

This loader discovers plugin packages by scanning the repository `plugins/` dir
and importing `plugins.<name>` modules.
"""
from __future__ import annotations
from importlib import import_module
from pathlib import Path
from typing import Any, Optional
from functools import partial
import logging

# jinja loader helpers and static file mounting
from jinja2 import ChoiceLoader, FileSystemLoader
from fastapi.staticfiles import StaticFiles


def discover_plugins(root: Path) -> list[str]:
    p = Path(root) / "plugins"
    if not p.exists():
        return []
    names = []
    for child in sorted(p.iterdir()):
        if child.is_dir() and (child / "__init__.py").exists():
            names.append(child.name)
    return names


def load_plugins(app: Any, storage: Any, config: Any, repo_root: Path = Path("."), templates: Optional[Any] = None) -> None:
    names = discover_plugins(repo_root)
    logging.info("plugin loader: discovered plugins=%s", names)
    for name in names:
        mod_name = f"plugins.{name}"
        try:
            mod = import_module(mod_name)
        except Exception:
            logging.exception("Failed to import plugin %s", mod_name)
            continue
        # If the plugin package ships templates, add them to the Jinja2 Templates
        try:
            if templates is not None:
                pkg_dir = Path(mod.__file__).parent
                tpl_dir = pkg_dir / "templates"
                if tpl_dir.exists() and tpl_dir.is_dir():
                    logging.info("Adding plugin templates for %s -> %s", name, str(tpl_dir))
                    # Ensure templates.env.loader is a ChoiceLoader
                    current_loader = templates.env.loader
                    file_loader = FileSystemLoader(str(tpl_dir))
                    if isinstance(current_loader, ChoiceLoader):
                        # append so core templates win over plugin unless plugin wants to override
                        current_loader.loaders.append(file_loader)
                        templates.env.loader = current_loader
                    else:
                        templates.env.loader = ChoiceLoader([current_loader, file_loader])
        except Exception:
            logging.exception("Error registering plugin templates for %s", mod_name)
        # If the plugin package has a static dir, mount it under /plugins/<name>/static
        try:
            pkg_dir = Path(mod.__file__).parent
            static_dir = pkg_dir / "static"
            if static_dir.exists() and static_dir.is_dir():
                mount_path = f"/plugins/{name}/static"
                logging.info("Mounting plugin static for %s at %s -> %s", name, mount_path, str(static_dir))
                app.mount(mount_path, StaticFiles(directory=str(static_dir)), name=f"plugin_{name}_static")
        except Exception:
            logging.exception("Error mounting static files for plugin %s", mod_name)
        # call register if present
        try:
            if hasattr(mod, "register"):
                # pass templates through so plugins can use the shared Jinja environment
                if templates is not None:
                    mod.register(app=app, storage=storage, config=config, templates=templates)
                else:
                    mod.register(app=app, storage=storage, config=config)
                logging.info("plugin %s registered", mod_name)
        except Exception:
            logging.exception("Error registering plugin %s", mod_name)
        # lifecycle hooks: if plugin exposes on_startup/on_shutdown, register them
        try:
            if hasattr(mod, "on_startup"):
                # wrap to pass app into the plugin hook when called
                app.add_event_handler("startup", partial(mod.on_startup, app))
            if hasattr(mod, "on_shutdown"):
                app.add_event_handler("shutdown", partial(mod.on_shutdown, app))
        except Exception:
            logging.exception("Error registering lifecycle hooks for plugin %s", mod_name)
