#!/usr/bin/env python3
"""
LoomAI Backend API 测试脚本
"""

import asyncio
import sys
from pathlib import Path

import httpx

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))


class LoomAITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None

    async def test_health(self):
        """测试健康检查"""
        print("🔍 测试健康检查...")

        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=10.0, trust_env=False
        ) as client:
            response = await client.get("/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()

    async def test_register(self):
        """测试用户注册"""
        print("👤 测试用户注册...")

        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "nickname": "测试用户",
        }

        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=10.0, trust_env=False
        ) as client:
            response = await client.post("/v1/auth/register", json=user_data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()

    async def test_login(self):
        """测试用户登录"""
        print("🔐 测试用户登录...")

        login_data = {"email": "test@example.com", "password": "password123"}

        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=10.0, trust_env=False
        ) as client:
            response = await client.post("/v1/auth/login", json=login_data)

            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Response: {result}")

            if response.status_code == 200 and result.get("success"):
                self.token = result["data"]["accessToken"]
                print("✅ 登录成功，获取到Token")

            print()

    async def test_profile(self):
        """测试获取用户信息"""
        if not self.token:
            print("❌ 需要先登录")
            return

        print("👤 测试获取用户信息...")

        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=10.0, trust_env=False
        ) as client:
            response = await client.get("/v1/user/profile", headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()

    async def test_credits_balance(self):
    """测试积分余额查询"""
        if not self.token:
            print("❌ 需要先登录")
            return

    print("💰 测试积分余额查询...")

        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=10.0, trust_env=False
        ) as client:
            response = await client.get("/v1/credits/balance", headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()

    async def test_processing_estimate(self):
    """测试积分预估"""
        if not self.token:
            print("❌ 需要先登录")
            return

    print("🎯 测试积分预估...")

        # 创建一个测试图片
        import io

        from PIL import Image

        # 创建一个简单的测试图片
        img = Image.new("RGB", (512, 512), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        headers = {"Authorization": f"Bearer {self.token}"}
        files = {"image": ("test.png", img_bytes.getvalue(), "image/png")}
        data = {"task_type": "seamless"}

        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=10.0, trust_env=False
        ) as client:
            response = await client.post(
                "/v1/processing/estimate", headers=headers, files=files, data=data
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()

    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始API测试...\n")

        await self.test_health()
        await self.test_register()
        await self.test_login()
        await self.test_profile()
        await self.test_credits_balance()
        await self.test_processing_estimate()

        print("✅ 所有测试完成!")


async def main():
    """主函数"""
    tester = LoomAITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())