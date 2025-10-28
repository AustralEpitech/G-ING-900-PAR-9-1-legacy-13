from geneweb_py.web.app import app
from fastapi.openapi.docs import get_swagger_ui_html


def test_openapi_schema_callable():
    schema = app.openapi()
    assert isinstance(schema, dict)
    assert "openapi" in schema
    assert "paths" in schema


def test_docs_renderer_returns_html_response():
    # Use the same helper FastAPI uses to produce the docs HTML
    resp = get_swagger_ui_html(openapi_url=app.openapi_url, title=f"{app.title} - Swagger UI")
    # Should be an HTML response
    assert hasattr(resp, "media_type")
    assert "html" in resp.media_type


def test_routes_include_plugin_and_root():
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/" in paths
    # plugin route should be present
    assert "/hello-plugin" in paths
