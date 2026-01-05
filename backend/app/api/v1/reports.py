from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
import os

from app.api.deps import get_db
from app.services.report.generator import ReportGenerator

router = APIRouter()


@router.post("/generate")
async def generate_report(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db)
):
    """レポートを生成"""
    generator = ReportGenerator()
    filepath = await generator.generate(db, start_date, end_date)
    
    return {
        "message": "Report generated successfully",
        "filepath": filepath,
        "filename": os.path.basename(filepath),
    }


@router.get("/download/{filename}")
async def download_report(filename: str):
    """レポートをダウンロード"""
    filepath = f"/app/reports/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        filepath,
        media_type="text/markdown",
        filename=filename,
    )


@router.get("")
async def list_reports():
    """レポート一覧を取得"""
    report_dir = "/app/reports"
    
    if not os.path.exists(report_dir):
        return {"reports": []}
    
    files = []
    for f in os.listdir(report_dir):
        if f.endswith(".md"):
            filepath = os.path.join(report_dir, f)
            files.append({
                "filename": f,
                "size": os.path.getsize(filepath),
                "created_at": os.path.getctime(filepath),
            })
    
    files.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"reports": files}
