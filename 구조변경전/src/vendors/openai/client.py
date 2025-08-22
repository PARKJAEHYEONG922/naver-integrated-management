"""
OpenAI/Claude API 직접 호출
Raw API 호출만 담당, 가공은 하지 않음
"""
from typing import Dict, Any, List, Optional
import json

from src.foundation.http_client import default_http_client, rate_limiter_manager
from src.foundation.config import config_manager
from src.foundation.exceptions import OpenAIError, ClaudeAPIError, handle_api_exception
from src.foundation.logging import get_logger


logger = get_logger("vendors.openai")


class OpenAIClient:
    """OpenAI API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.openai.com/v1"
        self.rate_limiter = rate_limiter_manager.get_limiter("openai", 0.5)  # 2초당 1회
    
    def _get_headers(self) -> Dict[str, str]:
        """API 호출용 헤더 생성"""
        api_config = config_manager.load_api_config()
        return {
            'Authorization': f'Bearer {api_config.openai_api_key}',
            'Content-Type': 'application/json'
        }
    
    def _check_config(self) -> bool:
        """API 설정 확인"""
        api_config = config_manager.load_api_config()
        return bool(api_config.openai_api_key)
    
    @handle_api_exception
    def create_completion(self,
                         messages: List[Dict[str, str]],
                         model: str = "gpt-4o-mini",
                         temperature: float = 0.7,
                         max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        채팅 완성 생성
        
        Args:
            messages: 메시지 목록
            model: 사용할 모델
            temperature: 온도 설정
            max_tokens: 최대 토큰 수
        
        Returns:
            Dict: API 응답
        """
        if not self._check_config():
            raise OpenAIError("OpenAI API 키가 설정되지 않았습니다")
        
        # 속도 제한 적용
        self.rate_limiter.wait()
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = self._get_headers()
        url = f"{self.base_url}/chat/completions"
        
        logger.info(f"OpenAI API 호출: {model}")
        
        try:
            response = default_http_client.post(url, headers=headers, json=payload)
            data = response.json()
            
            if 'error' in data:
                raise OpenAIError(f"API 에러: {data['error'].get('message', 'Unknown error')}")
            
            logger.info("OpenAI API 호출 성공")
            return data
            
        except json.JSONDecodeError as e:
            raise OpenAIError(f"API 응답 파싱 실패: {e}")
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            raise OpenAIError(f"API 호출 실패: {e}")


class ClaudeClient:
    """Claude API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.anthropic.com/v1"
        self.rate_limiter = rate_limiter_manager.get_limiter("claude", 0.2)  # 5초당 1회
    
    def _get_headers(self) -> Dict[str, str]:
        """API 호출용 헤더 생성"""
        api_config = config_manager.load_api_config()
        return {
            'x-api-key': api_config.claude_api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
    
    def _check_config(self) -> bool:
        """API 설정 확인"""
        api_config = config_manager.load_api_config()
        return bool(api_config.claude_api_key)
    
    @handle_api_exception
    def create_message(self,
                      messages: List[Dict[str, str]],
                      model: str = "claude-3-haiku-20240307",
                      max_tokens: int = 1000,
                      temperature: float = 0.7) -> Dict[str, Any]:
        """
        메시지 생성
        
        Args:
            messages: 메시지 목록
            model: 사용할 모델
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
        
        Returns:
            Dict: API 응답
        """
        if not self._check_config():
            raise ClaudeAPIError("Claude API 키가 설정되지 않았습니다")
        
        # 속도 제한 적용
        self.rate_limiter.wait()
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        headers = self._get_headers()
        url = f"{self.base_url}/messages"
        
        logger.info(f"Claude API 호출: {model}")
        
        try:
            response = default_http_client.post(url, headers=headers, json=payload)
            data = response.json()
            
            if 'error' in data:
                raise ClaudeAPIError(f"API 에러: {data['error'].get('message', 'Unknown error')}")
            
            logger.info("Claude API 호출 성공")
            return data
            
        except json.JSONDecodeError as e:
            raise ClaudeAPIError(f"API 응답 파싱 실패: {e}")
        except Exception as e:
            logger.error(f"Claude API 호출 실패: {e}")
            raise ClaudeAPIError(f"API 호출 실패: {e}")


# 전역 클라이언트 인스턴스
openai_client = OpenAIClient()
claude_client = ClaudeClient()