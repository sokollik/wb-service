import os
import stat
from typing import Optional, AsyncGenerator
from fastapi import Request
from fastapi.responses import StreamingResponse
from datetime import datetime
from core.repositories.document_repo import DocumentRepository, DocumentDownloadLogRepository
from core.models.document import Document
from fastapi import BackgroundTasks


class ChunkedStreamingService:
    
    CHUNK_SIZE = 8 * 1024
    
    def __init__(self, session, request: Optional[Request] = None):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.log_repo = DocumentDownloadLogRepository(session)
        self.request = request
    
    async def _get_file_info(
        self,
        document_id: int,
        file_type: str = "converted",
    ) -> Optional[dict]:

        document = await self.doc_repo.get_by_id(document_id)
        
        if not document:
            return None
        
        if file_type == "converted" and document.converted_path:
            file_path = document.converted_path
            mime_type = "application/pdf"
            actual_file_type = "converted"
        elif document.original_path:
            file_path = document.original_path
            mime_type = document.original_mime_type
            actual_file_type = "original"
        else:
            return None
        
        if not os.path.exists(file_path):
            return None
        
        file_size = os.path.getsize(file_path)
        
        return {
            "document": document,
            "file_path": file_path,
            "file_name": document.name,
            "file_size": file_size,
            "mime_type": mime_type,
            "file_type": actual_file_type,
        }
    
    async def _stream_file_chunked(
        self,
        file_path: str,
        start: int = 0,
        end: Optional[int] = None,
    ) -> AsyncGenerator[bytes, None]:

        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = (end - start + 1) if end is not None else None
            
            while True:
                chunk_size = self.CHUNK_SIZE
                if remaining is not None:
                    chunk_size = min(chunk_size, remaining)
                
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                yield chunk
                
                if remaining is not None:
                    remaining -= len(chunk)
                    if remaining <= 0:
                        break
    
    def _get_range_header(self) -> Optional[tuple[int, Optional[int]]]:

        if not self.request:
            return None
        
        range_header = self.request.headers.get("range")
        if not range_header:
            return None
        
        try:
            range_spec = range_header.replace("bytes=", "").strip()
            
            if "-" in range_spec:
                parts = range_spec.split("-")
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if parts[1] else None
                return (start, end)
            else:
                return None
                
        except (ValueError, IndexError):
            return None
    
    async def stream_document(
        self,
        document_id: int,
        file_type: str = "converted",
        log_download: bool = True,
    ) -> StreamingResponse:
        file_info = await self._get_file_info(document_id, file_type)
        
        if not file_info:
            from core.common.common_exc import NotFoundHttpException
            raise NotFoundHttpException(lang="ru", name="файл")
        
        document = file_info["document"]
        file_path = file_info["file_path"]
        file_size = file_info["file_size"]
        mime_type = file_info["mime_type"]
        file_name = f"{file_info['file_name']}.{document.original_extension}"
        
        if file_type == "converted":
            file_name = f"{file_info['file_name']}.pdf"

        range_info = self._get_range_header()
        
        if range_info:
            start, end = range_info
            
            if start < 0:
                start = 0
            if start >= file_size:
                from fastapi.responses import Response
                from fastapi import status
                return Response(
                    status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
                    headers={"Content-Range": f"bytes */{file_size}"},
                )
            
            if end is None or end >= file_size:
                end = file_size - 1
            
            content_length = end - start + 1
            
            response = StreamingResponse(
                self._stream_file_chunked(file_path, start, end),
                status_code=206,
                media_type=mime_type,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(content_length),
                    "Content-Disposition": f'inline; filename="{file_name}"',
                },
            )
        else:
            response = StreamingResponse(
                self._stream_file_chunked(file_path, 0, None),
                media_type=mime_type,
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(file_size),
                    "Content-Disposition": f'inline; filename="{file_name}"',
                },
            )
        
        if log_download and self.request:
            user_id = getattr(self.request.state, "user_id", "anonymous")
            user_email = getattr(self.request.state, "user_email", None)
            user_username = getattr(self.request.state, "user_username", None)

            ip_address = self.request.client.host if self.request.client else None
            user_agent = self.request.headers.get("user-agent")
            
        return response
    
    async def log_download_async(
        self,
        document_id: int,
        user_id: str,
        file_type: str,
        file_size: int,
        user_email: Optional[str] = None,
        user_username: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        try:
            await self.log_repo.log_download(
                document_id=document_id,
                user_id=user_id,
                user_email=user_email,
                user_username=user_username,
                file_type=file_type,
                file_size=file_size,
                user_agent=user_agent,
                ip_address=ip_address,
            )
        except Exception as e:
            print(f"[DownloadLog] Ошибка логирования: {e}")
    
    async def get_download_stats(
        self,
        document_id: int,
    ) -> dict:
        logs, total = await self.log_repo.get_logs_by_document(document_id, limit=1, offset=0)
        
        from sqlalchemy import select, func
        from core.models.document import DocumentDownloadLog
        
        total_result = await self.session.execute(
            select(func.count()).where(DocumentDownloadLog.document_id == document_id)
        )
        total_downloads = total_result.scalar()
        
        today = datetime.utcnow().date()
        today_result = await self.session.execute(
            select(func.count()).where(
                DocumentDownloadLog.document_id == document_id,
                func.date(DocumentDownloadLog.downloaded_at) == today,
            )
        )
        today_downloads = today_result.scalar()
        
        unique_users_result = await self.session.execute(
            select(func.count(func.distinct(DocumentDownloadLog.user_id))).where(
                DocumentDownloadLog.document_id == document_id,
            )
        )
        unique_users = unique_users_result.scalar()
        
        last_download_result = await self.session.execute(
            select(DocumentDownloadLog)
            .where(DocumentDownloadLog.document_id == document_id)
            .order_by(DocumentDownloadLog.downloaded_at.desc())
            .limit(1)
        )
        last_download = last_download_result.scalar_one_or_none()
        
        return {
            "total_downloads": total_downloads,
            "today_downloads": today_downloads,
            "unique_users": unique_users,
            "last_download_at": last_download.downloaded_at if last_download else None,
            "last_download_by": last_download.user_id if last_download else None,
        }
