from fastapi import APIRouter
from app.services.llm.prompt_templates import PromptTemplates

router = APIRouter()


@router.get("/prompts")
async def get_prompts():
    """Get LLM classification and summarization prompts

    全てのプロンプトは app.services.llm.prompt_templates で一元管理されており、
    このAPIは設定画面で表示するためにそれを返すだけです。
    """
    return {
        "classifier": {
            "system_prompt": PromptTemplates.CLASSIFIER_SYSTEM_PROMPT,
            "user_prompt_template": PromptTemplates.get_classifier_user_prompt_template(),
            "categories": PromptTemplates.CATEGORIES,
            "business_areas": PromptTemplates.BUSINESS_AREAS,
            "temperature": PromptTemplates.CLASSIFIER_TEMPERATURE,
        },
        "summarizer": {
            "system_prompt": PromptTemplates.SUMMARIZER_SYSTEM_PROMPT,
            "user_prompt_template": PromptTemplates.SUMMARIZER_USER_PROMPT_TEMPLATE,
            "temperature": PromptTemplates.SUMMARIZER_TEMPERATURE,
        },
        "ai_relevance": {
            "system_prompt": PromptTemplates.AI_RELEVANCE_SYSTEM_PROMPT,
            "content_prompt_template": PromptTemplates.AI_RELEVANCE_CONTENT_PROMPT_TEMPLATE,
            "text_prompt_template": PromptTemplates.AI_RELEVANCE_TEXT_PROMPT_TEMPLATE,
            "temperature": PromptTemplates.AI_RELEVANCE_TEMPERATURE,
        }
    }
