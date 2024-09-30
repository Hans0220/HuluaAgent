from typing import Any, Dict, Optional, Tuple, Type, Union

from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from pydantic import Field

from hulua.agents_services.zhipu import ChatZhipuAI
from hulua.schema.agent import LLM_Model, ModelSettings
from hulua.settings import Settings


class WrappedChatglm(ChatZhipuAI):
    client: Any = Field(
        default=None,
        description="Meta private value but mypy will complain its missing",
    )
    max_tokens: int
    model_name: LLM_Model = Field(alias="model")


Wrappedchatglm = Union[WrappedChatglm]


def create_model_glm(
    settings: Settings,
    model_settings: ModelSettings,
    streaming: bool = False,
    force_model: Optional[LLM_Model] = None,
) -> Wrappedchatglm:
    llm_model = force_model or model_settings.model
    model: Type[Wrappedchatglm] = WrappedChatglm
    base, headers = get_base_and_headers_glm(settings, model_settings)
    kwargs = {
        "zhipuai_api_base": base,
        "zhipuai_api_key": model_settings.custom_api_key or settings.openai_api_key,
        "temperature": model_settings.temperature,
        "model": llm_model,
        "max_tokens": model_settings.max_tokens,
        "streaming": streaming,
        "max_retries": 5,
        "model_kwargs": {"headers": headers},
    }

    return model(**kwargs)  # type: ignore


def get_base_and_headers_glm(
    settings_: Settings, model_settings: ModelSettings
) -> Tuple[str, Optional[Dict[str, str]], bool]:
    base = (
        "https://open.bigmodel.cn/api/paas/v4"
        if model_settings.custom_api_key
        else settings_.openai_api_base
    )

    headers = None

    return base, headers


class WrappedChatOpenAI(ChatOpenAI):
    client: Any = Field(
        default=None,
        description="Meta private value but mypy will complain its missing",
    )
    max_tokens: int
    model_name: LLM_Model = Field(alias="model")


class WrappedAzureChatOpenAI(WrappedChatOpenAI):
    openai_api_base: str
    openai_api_version: str
    deployment_name: str


WrappedChatopenai = Union[WrappedAzureChatOpenAI, WrappedChatOpenAI]


def create_model(
    settings: Settings,
    model_settings: ModelSettings,
    streaming: bool = False,
    force_model: Optional[LLM_Model] = None,
) -> WrappedChatopenai:
    use_azure = (
        not model_settings.custom_api_key and "azure" in settings.openai_api_base
    )

    llm_model = force_model or model_settings.model
    model: Type[WrappedChatopenai] = WrappedChatOpenAI
    base, headers, use_helicone = get_base_and_headers(settings, model_settings)
    kwargs = {
        "openai_api_base": base,
        "openai_api_key": model_settings.custom_api_key or settings.openai_api_key,
        "temperature": model_settings.temperature,
        "model": llm_model,
        "max_tokens": model_settings.max_tokens,
        "streaming": streaming,
        "max_retries": 5,
        "model_kwargs": {"headers": headers},
    }

    if use_azure:
        model = WrappedAzureChatOpenAI
        deployment_name = llm_model.replace(".", "")
        kwargs.update(
            {
                "openai_api_version": settings.openai_api_version,
                "deployment_name": deployment_name,
                "openai_api_type": "azure",
                "openai_api_base": base.rstrip("v1"),
            }
        )

        if use_helicone:
            kwargs["model"] = deployment_name

    return model(**kwargs)  # type: ignore


def get_base_and_headers(
    settings_: Settings, model_settings: ModelSettings
) -> Tuple[str, Optional[Dict[str, str]], bool]:
    use_helicone = settings_.helicone_enabled and not model_settings.custom_api_key
    base = (
        settings_.helicone_api_base
        if use_helicone
        else (
            "https://open.bigmodel.cn/api/paas/v4"
            if model_settings.custom_api_key
            else settings_.openai_api_base
        )
    )

    headers = (
        {
            "Helicone-Auth": f"Bearer {settings_.helicone_api_key}",
            "Helicone-Cache-Enabled": "true",
            "Helicone-User-Id": user.id,
            "Helicone-OpenAI-Api-Base": settings_.openai_api_base,
        }
        if use_helicone
        else None
    )

    return base, headers, use_helicone