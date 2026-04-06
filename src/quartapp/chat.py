import json
import os

from azure.identity.aio import AzureDeveloperCliCredential, ManagedIdentityCredential, get_bearer_token_provider
from openai import AsyncOpenAI
from quart import (
    Blueprint,
    Response,
    current_app,
    render_template,
    request,
    stream_with_context,
)

bp = Blueprint("chat", __name__, template_folder="templates", static_folder="static")


@bp.before_app_serving
async def configure_openai():
    bp.model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    openai_host = os.getenv("OPENAI_HOST", "azure")

    if openai_host == "local":
        bp.openai_client = AsyncOpenAI(api_key="no-key-required", base_url=os.getenv("LOCAL_OPENAI_ENDPOINT"))
        current_app.logger.info("Using local OpenAI-compatible API service with no key")
    elif os.getenv("AZURE_OPENAI_KEY_FOR_CHATVISION"):
        # Authenticate using an Azure OpenAI API key
        # This is generally discouraged, but is provided for developers
        # that want to develop locally inside the Docker container.
        bp.openai_client = AsyncOpenAI(
            base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1",
            api_key=os.getenv("AZURE_OPENAI_KEY_FOR_CHATVISION"),
        )
        current_app.logger.info("Using Azure OpenAI with key")
    elif os.getenv("RUNNING_IN_PRODUCTION"):
        client_id = os.environ["AZURE_CLIENT_ID"]
        azure_credential = ManagedIdentityCredential(client_id=client_id)
        token_provider = get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
        bp.openai_client = AsyncOpenAI(
            base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1",
            api_key=token_provider,
        )
        current_app.logger.info("Using Azure OpenAI with managed identity credential for client ID %s", client_id)
    else:
        tenant_id = os.environ["AZURE_TENANT_ID"]
        azure_credential = AzureDeveloperCliCredential(tenant_id=tenant_id)
        token_provider = get_bearer_token_provider(azure_credential, "https://cognitiveservices.azure.com/.default")
        bp.openai_client = AsyncOpenAI(
            base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1",
            api_key=token_provider,
        )
        current_app.logger.info("Using Azure OpenAI with az CLI credential for tenant ID: %s", tenant_id)
    current_app.logger.info("Using model %s", bp.model_name)


@bp.after_app_serving
async def shutdown_openai():
    await bp.openai_client.close()


@bp.get("/")
async def index():
    return await render_template("index.html")


@bp.post("/chat/stream")
async def chat_handler():
    request_json = await request.get_json()
    request_messages = request_json["messages"]
    # get the base64 encoded image from the request
    image = request_json["context"]["file"]

    @stream_with_context
    async def response_stream():
        # This sends all messages, so API request may exceed token limits
        # Convert previous messages to Responses API format
        all_input = []
        for msg in request_messages[0:-1]:
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, str):
                content_type = "output_text" if role == "assistant" else "input_text"
                all_input.append({"role": role, "content": [{"type": content_type, "text": content}]})
            else:
                all_input.append({"role": role, "content": content})

        # Add the current user message
        if image:
            user_content = [
                {"type": "input_text", "text": request_messages[-1]["content"]},
                {"type": "input_image", "image_url": image},
            ]
            all_input.append({"role": "user", "content": user_content})
        else:
            last_content = request_messages[-1]["content"]
            if isinstance(last_content, str):
                all_input.append({"role": "user", "content": [{"type": "input_text", "text": last_content}]})
            else:
                all_input.append({"role": "user", "content": last_content})

        openai_stream = await bp.openai_client.responses.create(
            # Azure Open AI takes the deployment name as the model name
            model=bp.model_name,
            input=all_input,
            stream=True,
            temperature=request_json.get("temperature", 0.5),
            store=False,
        )
        try:
            async for event in openai_stream:
                if event.type == "response.output_text.delta":
                    yield json.dumps({"delta": {"content": event.delta, "role": None}}, ensure_ascii=False) + "\n"
                elif event.type == "response.completed":
                    yield (
                        json.dumps(
                            {"delta": {"content": None, "role": None}, "finish_reason": "stop"},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                elif event.type == "response.failed":
                    error_msg = getattr(event, "error", {})
                    current_app.logger.error("Response failed: %s", error_msg)
                    yield json.dumps({"error": str(error_msg)}, ensure_ascii=False) + "\n"
                elif event.type == "error":
                    current_app.logger.error("Error event: %s", event)
                    yield json.dumps({"error": str(event)}, ensure_ascii=False) + "\n"
        except Exception as e:
            current_app.logger.exception("Error in response stream")
            yield json.dumps({"error": str(e)}, ensure_ascii=False) + "\n"

    return Response(response_stream())
