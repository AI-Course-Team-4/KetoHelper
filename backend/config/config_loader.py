"""
개인 설정 로더
.personal_config.py 파일이 있으면 개인 설정을 로드하고,
없으면 기본 설정을 사용
"""

import importlib
import importlib.util
import os
from typing import Dict, Any, Optional

def load_personal_config() -> Optional[Dict[str, Any]]:
    """
    개인 설정 파일 로드
    
    우선순위:
    1. .personal_config.py (개인 설정)
    2. personal_config.py (기본 설정)
    
    Returns:
        개인 설정 딕셔너리 또는 None
    """
    
    # 현재 파일의 디렉토리 (config 폴더)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    config_files = [
        ".personal_config.py",  # 개인 설정 (우선)
        "personal_config.py"    # 기본 설정
    ]
    
    for config_file in config_files:
        file_path = os.path.join(current_dir, config_file)
        
        if os.path.exists(file_path):
            try:
                # 파일을 직접 로드
                spec = importlib.util.spec_from_file_location("personal_config", file_path)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                
                # USE_PERSONAL_CONFIG가 True인 경우에만 설정 사용
                if hasattr(config_module, 'USE_PERSONAL_CONFIG') and config_module.USE_PERSONAL_CONFIG:
                    if hasattr(config_module, 'AGENT_CONFIGS'):
                        print(f"개인 설정 로드됨: {config_file}")
                        return config_module.AGENT_CONFIGS
                
            except Exception as e:
                print(f"설정 파일 로드 실패 ({config_file}): {e}")
                continue
    
    print("개인 설정을 찾을 수 없거나 비활성화됨. 기본 설정 사용.")
    return None

def get_agent_config(agent_type: str, personal_configs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    특정 에이전트의 설정 가져오기
    
    Args:
        agent_type: 에이전트 유형 (meal_planner, restaurant_agent, chat_agent)
        personal_configs: 개인 설정 딕셔너리
    
    Returns:
        에이전트별 설정 딕셔너리
    """
    
    if personal_configs and agent_type in personal_configs:
        return personal_configs[agent_type]
    
    # 기본 설정 반환
    return {}

# 전역 개인 설정 캐시
_personal_configs = None

def get_personal_configs() -> Optional[Dict[str, Any]]:
    """전역 개인 설정 가져오기 (캐시됨)"""
    global _personal_configs
    
    if _personal_configs is None:
        _personal_configs = load_personal_config()
    
    return _personal_configs

def reload_personal_configs():
    """개인 설정 재로드"""
    global _personal_configs
    _personal_configs = None
    return get_personal_configs()
