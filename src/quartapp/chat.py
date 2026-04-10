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
        all_input = list(request_messages[0:-1])

        # Add the current user message, appending image if provided
        if image:
            user_content = request_messages[-1]["content"] + [{"type": "input_image", "image_url": image}]
            all_input.append({"role": "user", "content": user_content})
        else:
            all_input.append(request_messages[-1])

        openai_stream = await bp.openai_client.responses.create(
            # Azure Open AI takes the deployment name as the model name
            model=bp.model_name,
            input=all_input,
            stream=True,
            # temperature is not compatible with reasoning models with effort > none
            temperature=0.3,
            # Instructs the Responses API to be stateless, so that it doesn't store responses on server
            store=False,
        )
        try:
            async for event in openai_stream:
                # Responses API emits other events: https://developers.openai.com/api/reference/resources/responses
                # This event is the only one needed for streaming the generated text response
                if event.type == "response.output_text.delta":
                    yield json.dumps({"type": event.type, "delta": event.delta}, ensure_ascii=False) + "\n"
                elif event.type in ("response.failed", "error"):
                    current_app.logger.error("Responses API error: %s", event)
                    yield json.dumps({"type": event.type}, ensure_ascii=False) + "\n"
        except Exception as e:
            current_app.logger.exception("Error in response stream")
            yield json.dumps({"error": str(e)}, ensure_ascii=False) + "\n"

    return Response(response_stream())
