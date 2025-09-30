from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.services.credit_service import CreditService
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse

router = APIRouter()
credit_service = CreditService()


class CreditTransferRequest(BaseModel):
    recipient_email: EmailStr
    amount: int
    message: Optional[str] = None


@router.get("/balance")
async def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取算力余额"""
    try:
        balance_info = await credit_service.get_user_balance(db, current_user.id)
        
        return SuccessResponse(
            data=balance_info,
            message="获取算力余额成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions")
async def get_transactions(
    type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取算力消耗记录"""
    try:
        # 解析日期
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        result = await credit_service.get_transaction_history(
            db=db,
            user_id=current_user.id,
            transaction_type=type,
            start_date=start_dt,
            end_date=end_dt,
            page=page,
            limit=limit
        )
        
        # 格式化交易记录
        formatted_transactions = []
        for txn in result["transactions"]:
            formatted_txn = {
                "transactionId": txn.transaction_id,
                "type": txn.type,
                "amount": txn.amount,
                "balance": txn.balance_after,
                "description": txn.description,
                "relatedTaskId": txn.related_task_id,
                "relatedOrderId": txn.related_order_id,
                "createdAt": txn.created_at
            }
            formatted_transactions.append(formatted_txn)
        
        return SuccessResponse(
            data={
                "transactions": formatted_transactions,
                "summary": result["summary"],
                "pagination": result["pagination"]
            },
            message="获取交易记录成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfer")
async def transfer_credits(
    transfer_data: CreditTransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """算力转赠"""
    try:
        if transfer_data.amount <= 0:
            raise HTTPException(status_code=400, detail="转赠数量必须大于0")
        
        if transfer_data.amount > 1000:
            raise HTTPException(status_code=400, detail="单次转赠不能超过1000算力")
        
        transfer = await credit_service.transfer_credits(
            db=db,
            sender_id=current_user.id,
            recipient_email=transfer_data.recipient_email,
            amount=transfer_data.amount,
            message=transfer_data.message
        )
        
        return SuccessResponse(
            data={
                "transferId": transfer.transfer_id,
                "amount": transfer.amount,
                "recipientEmail": transfer_data.recipient_email,
                "senderBalance": current_user.credits,
                "status": transfer.status,
                "createdAt": transfer.created_at
            },
            message="算力转赠成功"
        )
        
    except Exception as e:
        if "不存在" in str(e) or "不能向自己" in str(e) or "余额不足" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transfers")
async def get_transfers(
    type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取转赠记录"""
    try:
        result = await credit_service.get_transfer_history(
            db=db,
            user_id=current_user.id,
            transfer_type=type,
            page=page,
            limit=limit
        )
        
        # 格式化转赠记录
        formatted_transfers = []
        for transfer in result["transfers"]:
            transfer_type = "sent" if transfer.sender_id == current_user.id else "received"
            
            formatted_transfer = {
                "transferId": transfer.transfer_id,
                "type": transfer_type,
                "amount": transfer.amount,
                "recipientEmail": transfer.recipient.email if transfer_type == "sent" else None,
                "senderEmail": transfer.sender.email if transfer_type == "received" else None,
                "message": transfer.message,
                "status": transfer.status,
                "createdAt": transfer.created_at
            }
            formatted_transfers.append(formatted_transfer)
        
        return SuccessResponse(
            data={
                "transfers": formatted_transfers,
                "pagination": result["pagination"]
            },
            message="获取转赠记录成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    period: str = "daily",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取算力统计"""
    try:
        if period not in ["daily", "weekly", "monthly", "yearly"]:
            raise HTTPException(status_code=400, detail="无效的统计周期")
        
        stats = await credit_service.get_credit_statistics(
            db=db,
            user_id=current_user.id,
            period=period
        )
        
        return SuccessResponse(
            data=stats,
            message="获取统计信息成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pricing")
async def get_pricing():
    """获取算力价格表"""
    try:
        pricing_data = {
            "processing": {
                "seamless": {
                    "name": "AI四方连续转换",
                    "baseCredits": 60,
                    "description": "对独幅矩形图转换成可四方连续的打印图"
                },
                "vectorize": {
                    "name": "AI矢量化(转SVG)",
                    "baseCredits": 100,
                    "description": "使用AI一键将图片变成矢量图"
                },
                "extractPattern": {
                    "name": "AI提取花型",
                    "baseCredits": 100,
                    "description": "提取图案中的花型元素"
                },
                "removeWatermark": {
                    "name": "AI智能去水印",
                    "baseCredits": 70,
                    "description": "去除文字和Logo水印"
                },
                "denoise": {
                    "name": "AI布纹去噪",
                    "baseCredits": 80,
                    "description": "去除噪点和布纹"
                },
                "embroidery": {
                    "name": "AI毛线刺绣增强",
                    "baseCredits": 90,
                    "description": "毛线刺绣效果处理"
                }
            },
            "modifiers": {
                "highResolution": {
                    "threshold": 2048,
                    "multiplier": 1.5,
                    "description": "高分辨率处理"
                },
                "largeFile": {
                    "threshold": 10485760,
                    "additionalCredits": 20,
                    "description": "大文件处理"
                }
            },
            "discounts": {
                "premium": {
                    "membershipType": "premium",
                    "discount": 0.1,
                    "description": "高级会员折扣"
                },
                "enterprise": {
                    "membershipType": "enterprise",
                    "discount": 0.2,
                    "description": "企业会员折扣"
                }
            },
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
        return SuccessResponse(
            data=pricing_data,
            message="获取价格表成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
