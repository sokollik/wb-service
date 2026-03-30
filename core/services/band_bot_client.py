import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import httpx
from core.config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class BandMessageResponse:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[int] = None


@dataclass
class BandUserInfo:
    user_id: str
    chat_id: str
    display_name: Optional[str] = None
    is_bot_blocked: bool = False


class BandBotAPIClient:
    
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.BAND_BOT_URL or "https://band.bot.corпоративный/api/v1"
        self.api_token = settings.BAND_BOT_TOKEN
        self.timeout = settings.BAND_BOT_TIMEOUT or 30
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                },
            )
        return self._client
    
    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def send_message(
        self,
        chat_id: str,
        title: str,
        message: str,
        buttons: Optional[List[Dict[str, Any]]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> BandMessageResponse:

        client = await self.get_client()
        
        data = {
            "chat_id": chat_id,
            "title": title,
            "text": message,
        }
        
        if buttons:
            data["inline_keyboard"] = buttons
        
        if payload:
            data["payload"] = payload
        
        try:
            response = await client.post("/messages/send", json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                logger.info(f"Сообщение успешно отправлено в chat_id={chat_id}")
                return BandMessageResponse(
                    success=True,
                    message_id=result.get("message_id"),
                )
            else:
                error_msg = result.get("error", "Неизвестная ошибка")
                logger.warning(f"Ошибка отправки сообщения: {error_msg}")
                return BandMessageResponse(
                    success=False,
                    error=error_msg,
                    error_code=result.get("error_code"),
                )
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при отправке: {e.response.status_code}")
            return BandMessageResponse(
                success=False,
                error=str(e),
                error_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error(f"Ошибка запроса: {e}")
            return BandMessageResponse(
                success=False,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return BandMessageResponse(
                success=False,
                error=str(e),
            )
    
    async def get_user_info(self, chat_id: str) -> Optional[BandUserInfo]:

        client = await self.get_client()
        
        try:
            response = await client.get(f"/users/{chat_id}")
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                user_data = result.get("user", {})
                return BandUserInfo(
                    user_id=user_data.get("user_id", ""),
                    chat_id=chat_id,
                    display_name=user_data.get("display_name"),
                    is_bot_blocked=user_data.get("is_bot_blocked", False),
                )
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {e}")
            return None
    
    async def send_document_notification(
        self,
        chat_id: str,
        document_name: str,
        document_id: int,
        action: str = "acknowledge",
    ) -> BandMessageResponse:

        buttons = [
            [
                {
                    "text": "📖 Ознакомиться",
                    "url": f"{self.base_url}/documents/{document_id}/acknowledge",
                },
                {
                    "text": "👁️ Просмотреть",
                    "url": f"{self.base_url}/documents/{document_id}",
                },
            ]
        ]
        
        message = f"Вам назначено ознакомление с документом: {document_name}"
        
        return await self.send_message(
            chat_id=chat_id,
            title="📄 Новый документ",
            message=message,
            buttons=buttons,
            payload={
                "document_id": document_id,
                "action": action,
            },
        )
    
    async def send_news_notification(
        self,
        chat_id: str,
        news_title: str,
        news_id: int,
        is_mandatory: bool = False,
    ) -> BandMessageResponse:

        buttons = [
            [
                {
                    "text": "📰 Читать",
                    "url": f"{self.base_url}/news/{news_id}",
                },
            ]
        ]
        
        if is_mandatory:
            buttons[0].append({
                "text": "✅ Ознакомлен",
                "url": f"{self.base_url}/news/{news_id}/acknowledge",
            })
        
        message = f"Опубликована новая новость: {news_title}"
        if is_mandatory:
            message += "\n⚠️ Требуется обязательное ознакомление"
        
        return await self.send_message(
            chat_id=chat_id,
            title="📢 Новая новость" if not is_mandatory else "⚠️ Важное уведомление",
            message=message,
            buttons=buttons,
            payload={
                "news_id": news_id,
                "is_mandatory": is_mandatory,
            },
        )
    
    async def send_birthday_notification(
        self,
        chat_id: str,
        birthday_person_name: str,
        birthday_person_eid: str,
    ) -> BandMessageResponse:

        buttons = [
            [
                {
                    "text": "🎁 Поздравить",
                    "url": f"{self.base_url}/profiles/{birthday_person_eid}",
                },
            ]
        ]
        
        message = f"🎂 У {birthday_person_name} сегодня день рождения!"
        
        return await self.send_message(
            chat_id=chat_id,
            title="🎉 День рождения коллеги",
            message=message,
            buttons=buttons,
            payload={
                "birthday_person_eid": birthday_person_eid,
            },
        )

band_bot_client = BandBotAPIClient()
