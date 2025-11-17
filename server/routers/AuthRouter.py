"""
AuthRouter.py
-------------
API routes for WorkOS authentication.
"""

import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from core.workos_client import workos_client
from core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
async def login():
    """
    Redirect to WorkOS AuthKit for authentication.
    Automatically assigns users to the configured organization.
    """
    authorization_url = workos_client.user_management.get_authorization_url(
        provider="authkit",
        redirect_uri=os.getenv("WORKOS_REDIRECT_URI"),
        organization_id=os.getenv("WORKOS_ORG_ID")  # Auto-assign to hris-system org
    )
    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def callback(code: str):
    """
    Handle OAuth callback from WorkOS.
    Exchange authorization code for user session and set secure cookie.
    """
    # Exchange authorization code for authenticated user session
    auth_response = workos_client.user_management.authenticate_with_code(
        code=code,
        session={
            "seal_session": True,
            "cookie_password": os.getenv("WORKOS_COOKIE_PASSWORD")
        }
    )

    # Create redirect response
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    redirect_response = RedirectResponse(url=f"{frontend_url}/dashboard")

    # Set encrypted session cookie on the redirect response
    redirect_response.set_cookie(
        key="workos_session",
        value=auth_response.sealed_session,
        path="/",            # Available across entire domain
        httponly=True,       # Prevents JavaScript access (XSS protection)
        secure=False,        # Set to True in production (HTTPS only), False for local dev
        samesite="lax",      # CSRF protection
        max_age=604800       # 7 days
    )

    return redirect_response


@router.get("/logout")
async def logout(request: Request):
    """
    Log out user by terminating WorkOS session and clearing cookie.
    Redirects to WorkOS logout endpoint, which then redirects back to app.
    """
    sealed_session = request.cookies.get("workos_session")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    if not sealed_session:
        # No session to logout, just redirect
        return RedirectResponse(url=f"{frontend_url}/login")

    try:
        # Load the sealed session
        session = workos_client.user_management.load_sealed_session(
            sealed_session=sealed_session,
            cookie_password=os.getenv("WORKOS_COOKIE_PASSWORD")
        )

        # Get WorkOS logout URL (terminates session on their servers)
        logout_url = session.get_logout_url(return_to=f"{frontend_url}/login")

        # Clear cookie and redirect to WorkOS logout
        response = RedirectResponse(url=logout_url)
        response.delete_cookie(key="workos_session", path="/")
        return response

    except Exception as e:
        # Fallback: clear cookie and redirect if session loading fails
        print(f"DEBUG: Logout fallback due to error: {e}")
        response = RedirectResponse(url=f"{frontend_url}/login")
        response.delete_cookie(key="workos_session", path="/")
        return response


@router.get("/me")
async def get_current_user_info(user = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires valid WorkOS session cookie.
    """
    return {
        "workos_user_id": user.workos_user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "organization_id": user.organization_id,
        "employee_id": str(user.employee_id) if user.employee_id else None
    }
