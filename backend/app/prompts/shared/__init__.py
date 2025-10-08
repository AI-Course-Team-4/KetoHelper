"""
공통 프롬프트 템플릿 모듈
"""

from .common_templates import (
    MARKDOWN_FORMATTING_RULES,
    DEFAULT_RESPONSE_GUIDELINES,
    KETO_EXPERT_ROLE,
    FRIENDLY_TONE_GUIDE,
    add_markdown_formatting,
    add_response_guidelines,
    add_keto_expert_role,
    add_friendly_tone,
    create_standard_prompt
)

__all__ = [
    'MARKDOWN_FORMATTING_RULES',
    'DEFAULT_RESPONSE_GUIDELINES', 
    'KETO_EXPERT_ROLE',
    'FRIENDLY_TONE_GUIDE',
    'add_markdown_formatting',
    'add_response_guidelines',
    'add_keto_expert_role',
    'add_friendly_tone',
    'create_standard_prompt'
]