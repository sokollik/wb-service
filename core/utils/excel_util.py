from datetime import datetime
from io import BytesIO
from typing import List

from pandas import DataFrame, ExcelWriter


class ExcelUtil:
    def __init__(self):
        self._buffer: BytesIO | None = None
        self._writer: ExcelWriter | None = None
        self._sheet_names: set[str] = set()

    def _normalize_sheet_name(self, name: str) -> str:
        invalid_chars = "[]:*?/\\"
        safe_name = "".join("_" if ch in invalid_chars else ch for ch in name)
        safe_name = safe_name.strip() or "Sheet"

        base = safe_name[:31]
        candidate = base
        counter = 1

        while candidate in self._sheet_names:
            suffix = f"_{counter}"
            candidate = f"{base[: 31 - len(suffix)]}{suffix}"
            counter += 1

        self._sheet_names.add(candidate)
        return candidate

    def create_writer(
        self,
    ) -> ExcelWriter:
        self._buffer = BytesIO()
        self._sheet_names = set()
        self._writer = ExcelWriter(
            self._buffer,
            engine="xlsxwriter",
        )
        return self._writer

    def close_writer(
        self,
    ) -> bytes:
        if not self._writer or not self._buffer:
            raise RuntimeError("Writer not initialized")

        self._writer.close()
        self._buffer.seek(0)
        return self._buffer.read()

    def export(
        self,
        data: List[dict],
        columns: List[str],
        sheet_name: str,
    ) -> None:
        if not self._writer:
            self._writer = self.create_writer()

        if not data:
            data = [{column: None for column in columns}]

        df = DataFrame(data, columns=columns)
        safe_sheet_name = self._normalize_sheet_name(sheet_name)

        for column in df.columns:
            df[column] = df[column].map(
                lambda value: (
                    value.replace(tzinfo=None)
                    if isinstance(value, datetime) and value.tzinfo is not None
                    else value
                )
            )

        df.to_excel(
            self._writer,
            sheet_name=safe_sheet_name,
            startrow=1,
            header=False,
            index=False,
        )

        worksheet = self._writer.sheets[safe_sheet_name]
        workbook = self._writer.book
        header_format = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "border": 1,
            }
        )

        for col_idx, column in enumerate(df.columns):
            worksheet.write(0, col_idx, str(column), header_format)

        for col_idx, column in enumerate(df.columns):
            value_max_len = df[column].map(lambda value: len(str(value))).max()
            column_width = max(
                int(value_max_len) if value_max_len is not None else 0,
                len(str(column)),
            )
            worksheet.set_column(col_idx, col_idx, column_width + 10)
