"""
ExportRouter.py
---------------
API routes for exporting employee data in various formats.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from services.ExportService import ExportService
from schemas.ExportSchemas import ExportFilterSchema
from core.dependencies import require_roles, get_export_service

router = APIRouter(prefix="/exports", tags=["exports"])


# ============================================================================
# Directory Export Endpoints (Flat List)
# ============================================================================

@router.get("/directory/csv")
def export_directory_csv(
    filters: ExportFilterSchema = Depends(),
    user=Depends(require_roles("member")),
    export_service: ExportService = Depends(get_export_service),
):
    """
    Export employee directory as CSV file.

    Returns a flat list of all employees with their details.

    Filters:
    - department_id: Filter by department
    - team_id: Filter by team
    - status: Filter by employee status (ACTIVE, ON_LEAVE)
    - hired_from: Filter employees hired on or after this date
    - hired_to: Filter employees hired on or before this date
    """
    csv_data = export_service.export_directory_csv(filters)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"employee_directory_{timestamp}.csv"

    return StreamingResponse(
        csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/directory/excel")
def export_directory_excel(
    filters: ExportFilterSchema = Depends(),
    user=Depends(require_roles("member")),
    export_service: ExportService = Depends(get_export_service),
):
    """
    Export employee directory as Excel file.

    Returns a flat list of all employees with their details.

    Filters:
    - department_id: Filter by department
    - team_id: Filter by team
    - status: Filter by employee status (ACTIVE, ON_LEAVE)
    - hired_from: Filter employees hired on or after this date
    - hired_to: Filter employees hired on or before this date
    """
    excel_data = export_service.export_directory_excel(filters)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"employee_directory_{timestamp}.xlsx"

    return StreamingResponse(
        excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/directory/pdf")
def export_directory_pdf(
    filters: ExportFilterSchema = Depends(),
    user=Depends(require_roles("member")),
    export_service: ExportService = Depends(get_export_service),
):
    """
    Export employee directory as PDF file.

    Returns a flat list of all employees with their details in a table format.

    Filters:
    - department_id: Filter by department
    - team_id: Filter by team
    - status: Filter by employee status (ACTIVE, ON_LEAVE)
    - hired_from: Filter employees hired on or after this date
    - hired_to: Filter employees hired on or before this date
    """
    pdf_data = export_service.export_directory_pdf(filters)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"employee_directory_{timestamp}.pdf"

    return StreamingResponse(
        pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# Org Chart Export Endpoints (Hierarchical)
# ============================================================================

@router.get("/org-chart/csv")
def export_org_chart_csv(
    filters: ExportFilterSchema = Depends(),
    user=Depends(require_roles("member")),
    export_service: ExportService = Depends(get_export_service),
):
    """
    Export organizational chart as CSV file with hierarchy.

    Returns employees in hierarchical order with level indicators showing
    the reporting structure.

    Filters:
    - department_id: Filter by department
    - team_id: Filter by team
    - status: Filter by employee status (ACTIVE, ON_LEAVE)
    - hired_from: Filter employees hired on or after this date
    - hired_to: Filter employees hired on or before this date
    """
    csv_data = export_service.export_org_chart_csv(filters)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"org_chart_{timestamp}.csv"

    return StreamingResponse(
        csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/org-chart/excel")
def export_org_chart_excel(
    filters: ExportFilterSchema = Depends(),
    user=Depends(require_roles("member")),
    export_service: ExportService = Depends(get_export_service),
):
    """
    Export organizational chart as Excel file with visual hierarchy.

    Returns employees in hierarchical order with indentation and color coding
    to show the reporting structure.

    Filters:
    - department_id: Filter by department
    - team_id: Filter by team
    - status: Filter by employee status (ACTIVE, ON_LEAVE)
    - hired_from: Filter employees hired on or after this date
    - hired_to: Filter employees hired on or before this date
    """
    excel_data = export_service.export_org_chart_excel(filters)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"org_chart_{timestamp}.xlsx"

    return StreamingResponse(
        excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/org-chart/pdf")
def export_org_chart_pdf(
    filters: ExportFilterSchema = Depends(),
    user=Depends(require_roles("member")),
    export_service: ExportService = Depends(get_export_service),
):
    """
    Export organizational chart as visual PDF diagram.

    Returns a visual organizational chart with boxes and indentation
    showing the reporting structure.

    Filters:
    - department_id: Filter by department
    - team_id: Filter by team
    - status: Filter by employee status (ACTIVE, ON_LEAVE)
    - hired_from: Filter employees hired on or after this date
    - hired_to: Filter employees hired on or before this date
    """
    pdf_data = export_service.export_org_chart_pdf(filters)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"org_chart_{timestamp}.pdf"

    return StreamingResponse(
        pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
