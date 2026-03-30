import asyncio
import hashlib
import os
import shutil
import subprocess
import tempfile
from typing import Optional, Literal
from pathlib import Path
import aiohttp
from fastapi import BackgroundTasks
from core.config.settings import get_settings
from core.repositories.document_repo import DocumentRepository
from datetime import datetime
from sqlalchemy import select
from core.models.document import Document

settings = get_settings()


class LibreOfficeConverter:
    
    SUPPORTED_EXTENSIONS = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "odt": "application/vnd.oasis.opendocument.text",
        "odp": "application/vnd.oasis.opendocument.presentation",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
    }
    
    def __init__(self):
        self.libreoffice_path = settings.LIBREOFFICE_PATH or "soffice"
        self.libreoffice_online_url = settings.LIBREOFFICE_ONLINE_URL
        self.timeout_seconds = 120
    
    def _generate_cache_key(self, document_path: str, original_extension: str) -> str:
        with open(document_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return f"doc_{original_extension}_{file_hash}"
    
    async def convert_with_cli(
        self,
        input_path: str,
        output_dir: str,
    ) -> Optional[str]:
        try:
            cmd = [
                self.libreoffice_path,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                input_path,
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds,
                )
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"Конвертация превысила таймаут {self.timeout_seconds}с")
            
            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore")
                raise RuntimeError(f"LibreOffice вернул код {process.returncode}: {error_msg}")
            
            input_filename = os.path.basename(input_path)
            name_without_ext = os.path.splitext(input_filename)[0]
            output_path = os.path.join(output_dir, f"{name_without_ext}.pdf")
            
            if os.path.exists(output_path):
                return output_path
            else:
                raise FileNotFoundError(f"PDF файл не найден: {output_path}")
                
        except Exception as e:
            raise RuntimeError(f"Ошибка конвертации CLI: {str(e)}")
    
    async def convert_with_online_api(
        self,
        input_path: str,
        output_path: str,
    ) -> Optional[str]:

        if not self.libreoffice_online_url:
            raise RuntimeError("LibreOffice Online URL не настроен")
        
        try:
            async with aiohttp.ClientSession() as session:
                with open(input_path, "rb") as f:
                    file_data = f.read()
                url = f"{self.libreoffice_online_url}/lool/convert-to/pdf"
                
                async with session.post(
                    url,
                    data=file_data,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=aiohttp.ClientTimeout(total=self.timeout_seconds),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(
                            f"LibreOffice Online вернул {response.status}: {error_text}"
                        )
                    
                    pdf_content = await response.read()
                    with open(output_path, "wb") as f:
                        f.write(pdf_content)
                    
                    return output_path
                    
        except Exception as e:
            raise RuntimeError(f"Ошибка конвертации Online API: {str(e)}")
    
    async def convert(
        self,
        input_path: str,
        output_dir: str,
        method: Literal["cli", "online", "auto"] = "auto",
    ) -> tuple[Optional[str], str]:
        os.makedirs(output_dir, exist_ok=True)

        if method == "auto":
            method = "online" if self.libreoffice_online_url else "cli"
        
        if method == "online":
            try:
                input_filename = os.path.basename(input_path)
                name_without_ext = os.path.splitext(input_filename)[0]
                output_path = os.path.join(output_dir, f"{name_without_ext}.pdf")
                
                result = await self.convert_with_online_api(input_path, output_path)
                return result, "online"
            except Exception as e:
                if method == "auto":
                    print(f"Online конвертация не удалась: {e}. Пробуем CLI...")
                    method = "cli"
                else:
                    raise
        
        if method == "cli":
            result = await self.convert_with_cli(input_path, output_dir)
            return result, "cli"
        
        return None, "unknown"


class OnlyOfficeConverter:
    
    def __init__(self):
        self.onlyoffice_url = settings.ONLYOFFICE_URL
        self.jwt_secret = settings.ONLYOFFICE_JWT_SECRET
    
    async def convert(
        self,
        input_path: str,
        output_dir: str,
    ) -> Optional[str]:

        if not self.onlyoffice_url:
            raise RuntimeError("OnlyOffice URL не настроен")
        
        raise NotImplementedError(
            "OnlyOffice конвертация требует дополнительной настройки. "
            "Используйте LibreOfficeConverter."
        )


class DocumentConversionService:
    
    def __init__(self, session):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.libreoffice_converter = LibreOfficeConverter()
        self.onlyoffice_converter = OnlyOfficeConverter()
        self.pdf_output_dir = os.path.join(settings.STATIC_PATH, "document_pdf")
    
    def _get_converter(
        self,
        extension: str,
        preferred: Literal["libreoffice", "onlyoffice", "auto"] = "auto",
    ):
        if extension.lower() in LibreOfficeConverter.SUPPORTED_EXTENSIONS:
            if preferred == "onlyoffice":
                return self.onlyoffice_converter, "onlyoffice"
            return self.libreoffice_converter, "libreoffice"
        
        raise ValueError(f"Неподдерживаемое расширение: {extension}")
    
    async def convert_document(
        self,
        document_id: int,
        preferred_converter: Literal["libreoffice", "onlyoffice", "auto"] = "auto",
    ) -> tuple[bool, str, Optional[str]]:

        document = await self.doc_repo.get_by_id(document_id)
        
        if not document:
            return False, "Документ не найден", None

        if document.original_extension.lower() not in LibreOfficeConverter.SUPPORTED_EXTENSIONS:
            return False, f"Формат {document.original_extension} не поддерживается", None
        
        if (
            document.converted_path
            and document.conversion_status == "completed"
            and document.cache_expires_at
            and document.cache_expires_at > __import__("datetime").datetime.utcnow()
        ):
            return True, "Используется кэшированная версия", document.converted_path
        
        await self.doc_repo.update_conversion_status(document_id, "processing")
        
        try:
            converter, converter_name = self._get_converter(
                document.original_extension,
                preferred_converter,
            )
            result = await converter.convert(
                input_path=document.original_path,
                output_dir=self.pdf_output_dir,
            )
            
            if result and result[0]:
                converted_path = result[0]
                
                await self.doc_repo.update_converted(document_id, converted_path)
                
                return True, f"Конвертация успешна ({converter_name})", converted_path
            else:
                await self.doc_repo.update_conversion_status(
                    document_id, "failed", "Конвертация вернула пустой результат"
                )
                return False, "Ошибка конвертации: пустой результат", None
                
        except Exception as e:
            await self.doc_repo.update_conversion_status(document_id, "failed", str(e))
            return False, f"Ошибка конвертации: {str(e)}", None
    
    async def get_cache_key(self, document_id: int) -> Optional[str]:
        document = await self.doc_repo.get_by_id(document_id)
        
        if not document:
            return None
        
        if document.cache_key:
            return document.cache_key
        
        cache_key = self.libreoffice_converter._generate_cache_key(
            document.original_path,
            document.original_extension,
        )
        
        await self.doc_repo.update_cache_key(document_id, cache_key)
        return cache_key
    
    async def invalidate_cache(self, document_id: int) -> bool:
        document = await self.doc_repo.get_by_id(document_id)
        
        if not document:
            return False
        
        await self.doc_repo.invalidate_cache(document_id)
        return True
    
    async def cleanup_expired_cache(self) -> int:

        result = await self.session.execute(
            select(Document)
            .where(
                Document.cache_expires_at != None,
                Document.cache_expires_at < datetime.utcnow(),
            )
        )
        
        documents = result.scalars().all()
        count = 0
        
        for doc in documents:
            if doc.converted_path and os.path.exists(doc.converted_path):
                try:
                    os.remove(doc.converted_path)
                except OSError:
                    pass
            doc.cache_expires_at = None
            doc.converted_path = None
            doc.conversion_status = "pending"
            count += 1
        
        await self.session.commit()
        return count

