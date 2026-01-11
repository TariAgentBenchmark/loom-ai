from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional

from app.core.database import get_db
from app.models.user import User
from app.models.notification import Notification, UserNotification
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse, PaginationMeta

router = APIRouter()


class NotificationResponse(BaseModel):
    notificationId: str
    title: str
    content: str
    type: str
    isRead: bool
    createdAt: str
    updatedAt: str


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unreadCount: int
    pagination: PaginationMeta


@router.get("/notifications")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        query = (
            db.query(Notification, UserNotification)
            .join(UserNotification, Notification.id == UserNotification.notification_id)
            .filter(
                UserNotification.user_id == current_user.id, Notification.active == True
            )
        )

        if unread_only:
            query = query.filter(UserNotification.is_read == False)

        total = query.count()

        results = (
            query.order_by(desc(Notification.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        notifications = []
        for notification, user_notification in results:
            notifications.append(
                NotificationResponse(
                    notificationId=notification.notification_id,
                    title=notification.title,
                    content=notification.content,
                    type=notification.type,
                    isRead=user_notification.is_read,
                    createdAt=notification.created_at.isoformat(),
                    updatedAt=notification.updated_at.isoformat(),
                ).model_dump()
            )

        unread_count = (
            db.query(UserNotification)
            .join(Notification, Notification.id == UserNotification.notification_id)
            .filter(
                UserNotification.user_id == current_user.id,
                UserNotification.is_read == False,
                Notification.active == True,
            )
            .count()
        )

        return SuccessResponse(
            data={
                "notifications": notifications,
                "unreadCount": unread_count,
                "pagination": PaginationMeta(
                    page=page,
                    limit=page_size,
                    total=total,
                    total_pages=(total + page_size - 1) // page_size,
                ).model_dump(by_alias=True),
            },
            message="获取通知列表成功",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        notification = (
            db.query(Notification)
            .filter(
                Notification.notification_id == notification_id,
                Notification.active == True,
            )
            .first()
        )

        if not notification:
            raise HTTPException(status_code=404, detail="通知不存在")

        user_notification = (
            db.query(UserNotification)
            .filter(
                UserNotification.user_id == current_user.id,
                UserNotification.notification_id == notification.id,
            )
            .first()
        )

        if not user_notification:
            raise HTTPException(status_code=404, detail="通知不存在")

        user_notification.is_read = True
        db.commit()

        return SuccessResponse(data={}, message="标记已读成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/mark-all-read")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # 获取需要更新的通知ID
        notification_ids = (
            db.query(Notification.id).filter(Notification.active == True).all()
        )
        notification_ids_list = [n.id for n in notification_ids]

        # 更新用户通知
        db.query(UserNotification).filter(
            UserNotification.user_id == current_user.id,
            UserNotification.notification_id.in_(notification_ids_list),
            UserNotification.is_read == False,
        ).update({"is_read": True}, synchronize_session=False)

        db.commit()

        return SuccessResponse(data={}, message="全部标记已读成功")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
