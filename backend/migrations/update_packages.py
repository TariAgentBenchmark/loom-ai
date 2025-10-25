"""
更新套餐数据 - 移除退款政策显示文字

执行命令：
python -m migrations.update_packages
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.membership_package import MembershipPackage


def update_packages():
    """更新套餐数据，移除退款政策显示文字"""
    db = next(get_db())

    try:
        # 获取所有套餐
        packages = db.query(MembershipPackage).all()

        updated_count = 0
        for package in packages:
            # 检查 privileges 是否包含退款政策文字
            if package.privileges:
                new_privileges = []
                for privilege in package.privileges:
                    # 移除退款政策相关文字
                    if "可退款" not in privilege and "退款" not in privilege:
                        new_privileges.append(privilege)

                # 如果 privileges 有变化，则更新
                if new_privileges != package.privileges:
                    package.privileges = new_privileges
                    updated_count += 1
                    print(f"更新套餐: {package.name} - 特权: {new_privileges}")

        if updated_count > 0:
            db.commit()
            print(f"成功更新 {updated_count} 个套餐的权限数据")
        else:
            print("没有需要更新的套餐数据")

    except Exception as e:
        db.rollback()
        print(f"更新失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("开始更新套餐数据...")
    update_packages()
    print("套餐数据更新完成！")