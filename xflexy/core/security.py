from fastapi import Header, HTTPException, Request, status


def require_admin_api_key(
    request: Request,
    x_admin_api_key: str | None = Header(default=None),
) -> None:
    expected = request.app.state.settings.admin_api_key
    if not expected or x_admin_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key.",
        )
