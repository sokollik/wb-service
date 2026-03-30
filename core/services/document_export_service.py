from datetime import datetime
from io import BytesIO
from typing import List

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from core.schemas.document_schema import DocumentAcknowledgmentExportSchema


class DocumentExportService:
    """Сервис для экспорта документов и ознакомлений в Excel"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_acknowledgment_excel(
        self,
        data: List[DocumentAcknowledgmentExportSchema],
    ) -> bytes:
        """
        Создать Excel файл со списком ознакомлений.
        
        Args:
            data: Список записей для экспорта
            
        Returns:
            Байты Excel файла
        """
        # Преобразуем данные в список словарей
        records = []
        for item in data:
            records.append({
                "ID": item.id,
                "ID документа": item.document_id,
                "Название документа": item.document_name,
                "EID сотрудника": item.employee_eid,
                "ФИО сотрудника": item.employee_full_name or "N/A",
                "Требуется до": self._format_datetime(item.required_at),
                "Ознакомлен": self._format_datetime(item.acknowledged_at) if item.acknowledged_at else "Не ознакомлен",
                "Ознакомил (EID)": item.acknowledged_by or "N/A",
                "Статус": self._translate_status(item.status),
                "Просрочено": "Да" if item.is_overdue else "Нет",
            })

        # Создаём DataFrame
        df = pd.DataFrame(records)

        # Создаём Excel файл в памяти
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Ознакомления", index=False)
            
            # Получаем workbook и worksheet
            workbook = writer.book
            worksheet = writer.sheets["Ознакомления"]
            
            # Форматы
            header_format = workbook.add_format({
                "bold": True,
                "text_wrap": True,
                "valign": "top",
                "fg_color": "#4472C4",
                "font_color": "white",
                "border": 1,
            })
            
            cell_format = workbook.add_format({
                "text_wrap": True,
                "valign": "top",
                "border": 1,
            })
            
            # Формат для просроченных
            overdue_format = workbook.add_format({
                "text_wrap": True,
                "valign": "top",
                "border": 1,
                "fg_color": "#FFC7CE",
                "font_color": "#9C0006",
            })
            
            # Формат для ознакомленных
            acknowledged_format = workbook.add_format({
                "text_wrap": True,
                "valign": "top",
                "border": 1,
                "fg_color": "#C6EFCE",
                "font_color": "#006100",
            })
            
            # Применяем форматы
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Применяем условное форматирование
            for row_num in range(len(df)):
                is_overdue = data[row_num].is_overdue
                is_acknowledged = data[row_num].status == "acknowledged"
                
                if is_overdue:
                    format_to_use = overdue_format
                elif is_acknowledged:
                    format_to_use = acknowledged_format
                else:
                    format_to_use = cell_format
                
                for col_num in range(len(df.columns)):
                    worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num], format_to_use)
            
            # Автоширина колонок
            for i, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                ) + 2
                worksheet.set_column(i, i, min(max_length, 50))
        
        output.seek(0)
        return output.read()

    def _format_datetime(self, dt: datetime) -> str:
        """Форматирование даты/времени"""
        if dt is None:
            return ""
        return dt.strftime("%d.%m.%Y %H:%M")

    def _translate_status(self, status: str) -> str:
        """Перевод статуса"""
        status_map = {
            "pending": "Ожидается",
            "acknowledged": "Ознакомлен",
            "overdue": "Просрочен",
        }
        return status_map.get(status, status)
