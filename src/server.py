import sentry_sdk
import uvicorn
from fastapi import FastAPI
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.config import Config

from src import sts_router


###
# Configuration setup
###
config = Config(".env.local")
# This enables stacktraces to show in the UI when hitting errors
DEBUG = config("DEBUG", cast=bool, default=False)
# Connection string for Sentry.io log management
SENTRY_DSN = config("SENTRY_DSN", cast=str, default="")


###
# Server setup
###
app = FastAPI(
    debug=DEBUG,
    title="OpenShift STS Generation",
    description="Static JSON generator for OpenShift STS policies",
    version="v1",
    docs_url="/",
    redoc_url=None,
)

# Add app routers
app.include_router(sts_router.router)


###
# Health endpoint
###
@app.get("/health", include_in_schema=False)
def get_health():
    """Provide static endpoint for health checks"""
    return {"msg": "OK"}


# Wrap the ASGI app with a Sentry watcher
sentry_sdk.init(dsn=SENTRY_DSN)
app = SentryAsgiMiddleware(app)


###
# Development entrypoint
###
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8080, use_colors=True, reload=DEBUG, debug=DEBUG)
