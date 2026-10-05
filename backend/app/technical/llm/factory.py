from app.technical.llm.providers.gpt_oss import GPTOSSProvider
from app.config import config


def _create_provider():
    match config.llm_provider:
        case "gpt-oss" | "openai" | "claude":
            return GPTOSSProvider()
        case _:
            return GPTOSSProvider()


llm_provider = _create_provider()
