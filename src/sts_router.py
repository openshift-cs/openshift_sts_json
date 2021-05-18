import io
import zipfile
from enum import Enum
from pathlib import Path
from typing import Optional

import jinja2
from fastapi import APIRouter
from fastapi import Path as APIPath
from fastapi import Query
from fastapi.responses import PlainTextResponse
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

router = APIRouter()
TEMPLATE_DIRECTORY = Path.cwd() / "templates"


class OutputOptions(str, Enum):
    """Available output options."""

    download: str = "download"
    browser: str = "browser"


@router.get("/generate/{version}")
async def generate_json_policies(
    version: str = APIPath(..., title="The OpenShift minor version", max_length=4, regex="^4.[0-9]+$", example="4.7"),
    prefix: str = Query(
        ...,
        title="A string prefix to prepend to the AWS Policy/Role Name",
        max_length=50,
        regex="^[a-zA-Z0-9._-]+$",
        example="my-openshift-cluster",
    ),
    aws_account_id: str = Query(
        ...,
        title="The AWS account ID that owns the registered OpenID Connect provider",
        regex="^[0-9]{12}$",
        example="123456789012",
    ),
    oidc_provider: str = Query(
        ...,
        title="OpenID Connect provider endpoint registered with the AWS account",
        max_length=63,
        regex="^[a-zA-Z0-9._-]+$",
        example="my-oidc.s3.us-east-1.amazonaws.com",
    ),
    output: Optional[OutputOptions] = Query(OutputOptions.browser, title="Specify the desired output format"),
):
    """Fill in all policy JSON templates for a given OpenShift minor version."""

    loader = jinja2.FileSystemLoader(TEMPLATE_DIRECTORY / version)
    template_env = jinja2.Environment(loader=loader, autoescape=True)
    context = {"prefix": prefix, "aws_account_id": aws_account_id, "oidc_provider": oidc_provider}
    if output == OutputOptions.download:
        headers = {"Content-Disposition": f'attachment; filename="{version.replace(".", "-")}-sts.zip"'}
        bytes_object = await generate_zip_output(template_env, context)
        task = BackgroundTask(close_bytes_object, bytes_object)
        return StreamingResponse(bytes_object, media_type="application/zip", headers=headers, background=task)

    return PlainTextResponse(await generate_str_output(template_env, context))


async def generate_zip_output(env: jinja2.Environment, tpl_context: dict):
    """Iterate over a list of Jinja templates and return a zip-compressed file-like object"""
    zip_object = io.BytesIO()
    with zipfile.ZipFile(zip_object, mode="a") as container:
        for tpl_path in env.list_templates():
            tpl = env.get_template(tpl_path)
            container.writestr(tpl_path, tpl.render(tpl_context))
    zip_object.seek(0)
    return zip_object


async def generate_str_output(env: jinja2.Environment, tpl_context: dict):
    """Iterate over a list of Jinja templates and return a concatenated string"""
    string_content = ""
    for tpl_path in env.list_templates():
        tpl = env.get_template(tpl_path)
        string_content += f'{tpl_path}:\n\n{tpl.render(tpl_context)}\n\n{"-" * 64}\n\n'
    return string_content


async def close_bytes_object(bytes_object: io.BytesIO):
    """Close a BytesIO object"""
    bytes_object.close()
