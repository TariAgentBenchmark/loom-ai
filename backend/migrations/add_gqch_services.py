"""添加/更新 GQCH 相关服务价格

执行命令：
python -m migrations.add_gqch_services
"""

import sys
import os
from decimal import Decimal


# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db  # noqa: E402
from app.models.membership_package import ServicePrice  # noqa: E402


def _ensure_service(
    db,
    *,
    service_id: str,
    service_name: str,
    service_key: str,
    description: str,
    price: Decimal,
) -> None:
    service = (
        db.query(ServicePrice)
        .filter(ServicePrice.service_id == service_id)
        .first()
    )

    if service:
        updated = False
        if service.service_name != service_name:
            service.service_name = service_name
            updated = True
        if service.service_key != service_key:
            service.service_key = service_key
            updated = True
        if service.description != description:
            service.description = description
            updated = True
        if service.price_credits != price:
            service.price_credits = price
            updated = True
        if not service.active:
            service.active = True
            updated = True

        if updated:
            print(f"更新服务价格: {service_id}")
        else:
            print(f"服务已存在且无需更新: {service_id}")
    else:
        service = ServicePrice(
            service_id=service_id,
            service_name=service_name,
            service_key=service_key,
            description=description,
            price_credits=price,
            active=True,
        )
        db.add(service)
        print(f"新增服务价格: {service_id}")


def add_gqch_services() -> None:
    db = next(get_db())

    try:
        price = Decimal("1.00")
        _ensure_service(
            db,
            service_id="expand_image",
            service_name="扩图",
            service_key="expand_image",
            description="AI扩图",
            price=price,
        )
        _ensure_service(
            db,
            service_id="seamless_loop",
            service_name="接循环",
            service_key="seamless_loop",
            description="AI接循环",
            price=price,
        )
        db.commit()
        print("GQCH 服务价格更新完成")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"更新失败: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_gqch_services()

