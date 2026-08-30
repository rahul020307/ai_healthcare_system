from fastapi import APIRouter, Depends, Request, BackgroundTasks, Body
import datetime

from app.auth import get_current_identity
from app.services.email_service import send_security_login_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me")
def get_authenticated_identity(identity: dict = Depends(get_current_identity)):
    return {
        "status": "success",
        "authenticated": True,
        "user": {
            "id": identity["sub"],
            "email": identity["email"],
            "role": identity.get("role"),
        },
    }


@router.post("/notify-login")
def notify_user_login(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: dict = Body(default={}),
    identity: dict = Depends(get_current_identity),
):
    """Trigger an asynchronous security notification email to the user upon sign-in."""
    recipient_email = payload.get("email") or identity.get("email")
    user_name = payload.get("userName") or identity.get("claims", {}).get("name") or "User"
    user_agent = payload.get("userAgent") or request.headers.get("user-agent") or "Web Browser"
    client_ip = request.client.host if request.client else "127.0.0.1"
    now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    if recipient_email:
        print(f"[Auth] Queueing login security alert to recipient: {recipient_email}")
        background_tasks.add_task(
            send_security_login_email,
            recipient_email=recipient_email,
            user_name=user_name,
            ip_address=client_ip,
            user_agent=user_agent,
            timestamp=now_str,
        )

    return {
        "status": "success",
        "message": "Security login notification queued",
        "recipient": recipient_email,
    }
