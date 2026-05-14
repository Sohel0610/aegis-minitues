from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.falconebiz_service import trigger_mca_refresh

router = APIRouter(prefix="/api/mca", tags=["MCA Sync"])

@router.post("/request-update")
async def request_mca_update(
    din: Optional[str] = Query(None, description="Director DIN to refresh"),
    cin: Optional[str] = Query(None, description="Company CIN/LLPIN to refresh")
):
    """
    Triggers an asynchronous refresh of MCA data for a specific Director or Company.
    Note: Data takes ~2-5 minutes to actually update in the Falconebiz database.
    """
    if not din and not cin:
        raise HTTPException(status_code=400, detail="Either DIN or CIN must be provided.")
    
    success, message = trigger_mca_refresh(din=din, cin=cin)
    
    if not success:
        raise HTTPException(status_code=502, detail=message)
        
    return {"status": "success", "message": message}
