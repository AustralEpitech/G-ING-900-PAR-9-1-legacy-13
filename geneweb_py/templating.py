from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Any, Dict


def get_env(templates_dir: str | Path) -> Environment:
    templates_dir = str(templates_dir)
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml", "txt"]),
    )


def render_template(templates_dir: str | Path, template_name: str, ctx: Dict[str, Any]) -> str:
    env = get_env(templates_dir)
    tmpl = env.get_template(template_name)
    return tmpl.render(**ctx)
