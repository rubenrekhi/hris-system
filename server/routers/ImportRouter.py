"""
ImportRouter.py
---------------
API routes for bulk CSV import operations.
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any
import openpyxl
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session

from services.ImportService import ImportService
from schemas.ImportSchemas import BulkImportResult
from core.dependencies import require_roles, get_db, get_import_service


router = APIRouter(prefix="/imports", tags=["imports"])


def parse_excel_to_dict_list(contents: bytes) -> List[Dict[str, Any]]:
    """
    Parse Excel file and return list of dicts matching CSV format.

    Uses the first sheet only. Converts all data types to strings for
    consistency with CSV import format:
    - Dates → ISO format strings (YYYY-MM-DD)
    - Numbers → strings
    - None/empty cells → empty strings
    - Formulas → evaluated cached values

    Args:
        contents: Excel file bytes

    Returns:
        List of dictionaries with column headers as keys

    Raises:
        ValueError: If file is invalid, empty, or has no header row
    """
    try:
        # Load workbook (data_only=True reads formula values, not formulas)
        workbook = openpyxl.load_workbook(
            io.BytesIO(contents),
            data_only=True
        )

        # Use first sheet (as per user preference)
        if not workbook.worksheets:
            raise ValueError("Workbook has no sheets")

        sheet = workbook.worksheets[0]

        # Get all rows
        rows = list(sheet.iter_rows(values_only=True))

        if not rows:
            raise ValueError("Sheet is empty")

        # First row is headers
        headers = rows[0]

        if not headers or all(h is None or str(h).strip() == "" for h in headers):
            raise ValueError("No header row found")

        # Convert remaining rows to dicts
        data = []
        for row in rows[1:]:
            row_dict = {}
            for header, value in zip(headers, row):
                # Normalize value to string (matching CSV format)
                if value is None:
                    normalized_value = ""
                elif isinstance(value, datetime):
                    # Convert datetime to ISO format string
                    normalized_value = value.strftime('%Y-%m-%d')
                elif isinstance(value, (int, float)):
                    # Convert numbers to strings
                    # For integers or whole floats, remove decimal point
                    if isinstance(value, float) and value.is_integer():
                        normalized_value = str(int(value))
                    else:
                        normalized_value = str(value)
                else:
                    # Already a string or other type
                    normalized_value = str(value)

                row_dict[str(header)] = normalized_value

            # Skip completely empty rows
            if any(v for v in row_dict.values()):
                data.append(row_dict)

        return data

    except openpyxl.utils.exceptions.InvalidFileException as e:
        raise ValueError(f"Invalid Excel file format: {str(e)}")
    except Exception as e:
        # Catch any other openpyxl-specific errors
        if "openpyxl" in str(type(e).__module__):
            raise ValueError(f"Excel file processing error: {str(e)}")
        raise


@router.post("/employees", response_model=BulkImportResult)
async def import_employees_csv(
    response: Response,
    file: UploadFile = File(..., description="CSV or Excel file with employee data"),
    user = Depends(require_roles("admin")),
    import_service: ImportService = Depends(get_import_service),
    db: Session = Depends(get_db),
):
    """
    Bulk import employees from CSV or Excel file.

    Requires admin role.

    Supported Formats:
    - CSV (.csv)
    - Excel (.xlsx)

    For Excel files:
    - Only the first sheet is processed
    - First row must contain column headers
    - Formulas are evaluated to their cached values
    - Dates are converted to YYYY-MM-DD format
    - Numbers are converted to strings

    CSV/Excel Format:
    - Required columns: name, email
    - Optional columns: title, hired_on, salary, status, manager_email, department_name, team_name

    Example CSV:
    ```
    name,email,title,hired_on,salary,status,manager_email,department_name,team_name
    John Doe,john@example.com,CEO,2020-01-01,200000,ACTIVE,,Engineering,
    Jane Smith,jane@example.com,CTO,2020-02-01,180000,ACTIVE,john@example.com,Engineering,Platform
    ```

    Features:
    - Validates all rows before any database writes (all-or-nothing)
    - Handles manager dependencies within CSV using topological sort
    - Detects circular dependencies
    - Efficiently processes large files (bulk operations)
    - Links employees to existing users by email
    - Creates audit logs for all changes

    Returns:
    - BulkImportResult with success/failure details
    - If any validation fails, no employees are imported
    - Detailed error messages for failed rows
    """
    # Detect file type and parse accordingly
    filename = file.filename.lower()

    try:
        contents = await file.read()

        if filename.endswith('.csv'):
            # CSV parsing
            try:
                decoded = contents.decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(decoded))
                file_data = list(csv_reader)

                if not file_data:
                    raise HTTPException(
                        status_code=400,
                        detail="CSV file is empty"
                    )

            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file encoding. CSV must be UTF-8 encoded."
                )
            except csv.Error as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"CSV parsing error: {str(e)}"
                )

        elif filename.endswith('.xlsx'):
            # Excel parsing
            try:
                file_data = parse_excel_to_dict_list(contents)

                if not file_data:
                    raise HTTPException(
                        status_code=400,
                        detail="Excel file is empty or contains no data rows"
                    )

            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=str(e)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Excel parsing error: {str(e)}"
                )

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Supported formats: CSV (.csv), Excel (.xlsx)"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"File processing error: {str(e)}"
        )

    # Perform bulk import
    try:
        result = import_service.import_employees(
            file_data,
            changed_by_user_id=user.id,
        )

        # If there were validation errors, don't commit
        if result.failed_rows:
            db.rollback()
            # Return 200 with error info (not 201 since nothing created)
            # But don't raise exception so client gets detailed error info
            response.status_code = 200
            return result

        # All validations passed, commit the transaction
        db.commit()
        response.status_code = 201

        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )
