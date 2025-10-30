from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, condecimal
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.services.credit_service import CreditService
from app.services.membership_service import MembershipService
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.services.credit_math import to_float

router = APIRouter()
credit_service = CreditService()
membership_service = MembershipService()


class CreditTransferRequest(BaseModel):
    recipient_email: EmailStr
    amount: condecimal(gt=0, decimal_places=2)
    message: Optional[str] = None


@router.get("/balance")
async def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取积分余额"""
    try:
        balance_info = await credit_service.get_user_balance(db, current_user.id)
        
        return SuccessResponse(
            data=balance_info,
            message="获取积分余额成功"
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
    """获取积分消耗记录"""
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
                "amount": to_float(txn.amount),
                "balance": to_float(txn.balance_after),
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
    """积分转赠"""
    try:
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
                "amount": to_float(transfer.amount),
                "recipientEmail": transfer_data.recipient_email,
                "senderBalance": to_float(current_user.credits),
                "status": transfer.status,
                "createdAt": transfer.created_at
            },
            message="积分转赠成功"
        )
        
    except Exception as e:
        if "不存在" in str(e) or "不能向自己" in str(e) or "积分" in str(e):
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
                "amount": to_float(transfer.amount),
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
    """获取积分统计"""
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
async def get_pricing(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取积分价格表"""
    try:
        services = await membership_service.get_service_prices(db)
        return SuccessResponse(
            data={
                "services": services,
                "lastUpdated": datetime.utcnow().isoformat()
            },
            message="获取价格表成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
