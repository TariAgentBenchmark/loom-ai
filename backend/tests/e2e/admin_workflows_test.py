"""
End-to-end tests for admin workflows using Playwright
"""

import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import Generator, Dict, Any
import time

from tests.conftest import test_admin_user, test_normal_user
from tests.utils import TestDataGenerator


pytestmark = pytest.mark.e2e


class TestAdminLoginWorkflow:
    """Test admin login workflow end-to-end."""
    
    @pytest.fixture(scope="function")
    async def browser_context(self):
        """Create browser context for E2E testing."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            yield context
            await context.close()
            await browser.close()
    
    @pytest.fixture(scope="function")
    async def page(self, browser_context: BrowserContext):
        """Create page for E2E testing."""
        page = await browser_context.new_page()
        yield page
        await page.close()
    
    async def test_admin_login_success(self, page: Page):
        """Test successful admin login workflow."""
        # Navigate to admin login page
        await page.goto("http://localhost:3000/admin/login")
        
        # Wait for page to load
        await page.wait_for_selector('text=管理员登录')
        
        # Fill in login form
        await page.fill('input[name="email"]', "admin@test.com")
        await page.fill('input[name="password"]', "admin123456")
        
        # Click login button
        await page.click('button:has-text("登录")')
        
        # Wait for navigation to dashboard
        await page.wait_for_url("**/admin/dashboard")
        
        # Verify dashboard is loaded
        await page.wait_for_selector('text=仪表板')
        
        # Verify admin user info is displayed
        await page.wait_for_selector('text=admin@test.com')
    
    async def test_admin_login_invalid_credentials(self, page: Page):
        """Test admin login with invalid credentials."""
        # Navigate to admin login page
        await page.goto("http://localhost:3000/admin/login")
        
        # Wait for page to load
        await page.wait_for_selector('text=管理员登录')
        
        # Fill in invalid credentials
        await page.fill('input[name="email"]', "admin@test.com")
        await page.fill('input[name="password"]', "wrongpassword")
        
        # Click login button
        await page.click('button:has-text("登录")')
        
        # Wait for error message
        await page.wait_for_selector('text=Invalid credentials')
        
        # Verify still on login page
        assert page.url.endswith('/admin/login')
    
    async def test_admin_login_redirect_after_timeout(self, page: Page):
        """Test admin login redirect after session timeout."""
        # Navigate to admin login page
        await page.goto("http://localhost:3000/admin/login")
        
        # Wait for page to load
        await page.wait_for_selector('text=管理员登录')
        
        # Fill in login form
        await page.fill('input[name="email"]', "admin@test.com")
        await page.fill('input[name="password"]', "admin123456")
        
        # Click login button
        await page.click('button:has-text("登录")')
        
        # Wait for navigation to dashboard
        await page.wait_for_url("**/admin/dashboard")
        
        # Simulate session timeout by clearing cookies/localStorage
        await page.evaluate("localStorage.clear()")
        await page.context.clear_cookies()
        
        # Try to access admin page
        await page.goto("http://localhost:3000/admin/users")
        
        # Should redirect to login page
        await page.wait_for_url("**/admin/login")
    
    async def test_admin_login_form_validation(self, page: Page):
        """Test admin login form validation."""
        # Navigate to admin login page
        await page.goto("http://localhost:3000/admin/login")
        
        # Wait for page to load
        await page.wait_for_selector('text=管理员登录')
        
        # Try to submit empty form
        await page.click('button:has-text("登录")')
        
        # HTML5 validation should prevent submission
        # Check if email field is invalid
        email_input = page.locator('input[name="email"]')
        assert await email_input.evaluate('el => el.validity.valid') is False
        
        # Fill only email
        await page.fill('input[name="email"]', "admin@test.com")
        await page.click('button:has-text("登录")')
        
        # Check if password field is invalid
        password_input = page.locator('input[name="password"]')
        assert await password_input.evaluate('el => el.validity.valid') is False


class TestAdminUserManagementWorkflow:
    """Test admin user management workflow end-to-end."""
    
    @pytest.fixture(scope="function")
    async def authenticated_page(self, browser_context: BrowserContext):
        """Create authenticated page for testing."""
        page = await browser_context.new_page()
        
        # Navigate to admin login page
        await page.goto("http://localhost:3000/admin/login")
        
        # Login as admin
        await page.fill('input[name="email"]', "admin@test.com")
        await page.fill('input[name="password"]', "admin123456")
        await page.click('button:has-text("登录")')
        
        # Wait for dashboard
        await page.wait_for_url("**/admin/dashboard")
        
        yield page
        await page.close()
    
    async def test_view_users_list(self, authenticated_page: Page):
        """Test viewing users list."""
        # Navigate to users page
        await authenticated_page.click('text=用户管理')
        await authenticated_page.wait_for_url("**/admin/users")
        
        # Wait for users list to load
        await authenticated_page.wait_for_selector('text=用户列表')
        
        # Verify table headers
        await authenticated_page.wait_for_selector('text=邮箱')
        await authenticated_page.wait_for_selector('text=昵称')
        await authenticated_page.wait_for_selector('text=积分')
        await authenticated_page.wait_for_selector('text=会员类型')
        await authenticated_page.wait_for_selector('text=状态')
        
        # Verify pagination controls
        await authenticated_page.wait_for_selector('text=上一页')
        await authenticated_page.wait_for_selector('text=下一页')
    
    async def test_search_users(self, authenticated_page: Page):
        """Test searching users."""
        # Navigate to users page
        await authenticated_page.click('text=用户管理')
        await authenticated_page.wait_for_url("**/admin/users")
        
        # Wait for users list to load
        await authenticated_page.wait_for_selector('text=用户列表')
        
        # Enter search term
        await authenticated_page.fill('input[placeholder*="搜索"]', "test")
        
        # Click search button
        await authenticated_page.click('button:has-text("搜索")')
        
        # Wait for search results
        await authenticated_page.wait_for_timeout(1000)
        
        # Verify search results are displayed
        # (Specific assertions depend on actual implementation)
    
    async def test_filter_users_by_status(self, authenticated_page: Page):
        """Test filtering users by status."""
        # Navigate to users page
        await authenticated_page.click('text=用户管理')
        await authenticated_page.wait_for_url("**/admin/users")
        
        # Wait for users list to load
        await authenticated_page.wait_for_selector('text=用户列表')
        
        # Click status filter dropdown
        await authenticated_page.click('select[name="status"]')
        
        # Select "Active" status
        await authenticated_page.select_option('select[name="status"]', "active")
        
        # Wait for filtered results
        await authenticated_page.wait_for_timeout(1000)
        
        # Verify filtered results
        # (Specific assertions depend on actual implementation)
    
    async def test_view_user_details(self, authenticated_page: Page):
        """Test viewing user details."""
        # Navigate to users page
        await authenticated_page.click('text=用户管理')
        await authenticated_page.wait_for_url("**/admin/users")
        
        # Wait for users list to load
        await authenticated_page.wait_for_selector('text=用户列表')
        
        # Click on first user details button
        await authenticated_page.click('button:has-text("详情")')
        
        # Wait for user details page
        await authenticated_page.wait_for_url("**/admin/users/*")
        
        # Verify user details are displayed
        await authenticated_page.wait_for_selector('text=用户详情')
        await authenticated_page.wait_for_selector('text=基本信息')
        await authenticated_page.wait_for_selector('text=交易记录')
    
    async def test_update_user_status(self, authenticated_page: Page):
        """Test updating user status."""
        # Navigate to users page
        await authenticated_page.click('text=用户管理')
        await authenticated_page.wait_for_url("**/admin/users")
        
        # Wait for users list to load
        await authenticated_page.wait_for_selector('text=用户列表')
        
        # Click on first user details button
        await authenticated_page.click('button:has-text("详情")')
        
        # Wait for user details page
        await authenticated_page.wait_for_url("**/admin/users/*")
        
        # Click status update button
        await authenticated_page.click('button:has-text("更新状态")')
        
        # Wait for status modal
        await authenticated_page.wait_for_selector('text=更新用户状态')
        
        # Select new status
        await authenticated_page.select_option('select[name="status"]', "suspended")
        
        # Enter reason
        await authenticated_page.fill('textarea[name="reason"]', "Test suspension")
        
        # Confirm update
        await authenticated_page.click('button:has-text("确认")')
        
        # Wait for success message
        await authenticated_page.wait_for_selector('text=状态更新成功')
        
        # Verify status is updated
        await authenticated_page.wait_for_selector('text=已暂停')
    
    async def test_adjust_user_credits(self, authenticated_page: Page):
        """Test adjusting user credits."""
        # Navigate to users page
        await authenticated_page.click('text=用户管理')
        await authenticated_page.wait_for_url("**/admin/users")
        
        # Wait for users list to load
        await authenticated_page.wait_for_selector('text=用户列表')
        
        # Click on first user details button
        await authenticated_page.click('button:has-text("详情")')
        
        # Wait for user details page
        await authenticated_page.wait_for_url("**/admin/users/*")
        
        # Click credit adjustment button
        await authenticated_page.click('button:has-text("调整积分")')
        
        # Wait for credit adjustment modal
        await authenticated_page.wait_for_selector('text=调整用户积分')
        
        # Enter adjustment amount
        await authenticated_page.fill('input[name="amount"]', "100")
        
        # Enter reason
        await authenticated_page.fill('textarea[name="reason"]', "Test credit adjustment")
        
        # Confirm adjustment
        await authenticated_page.click('button:has-text("确认")')
        
        # Wait for success message
        await authenticated_page.wait_for_selector('text=积分调整成功')


class TestAdminOrderManagementWorkflow:
    """Test admin order management workflow end-to-end."""
    
    @pytest.fixture(scope="function")
    async def authenticated_page(self, browser_context: BrowserContext):
        """Create authenticated page for testing."""
        page = await browser_context.new_page()
        
        # Navigate to admin login page
        await page.goto("http://localhost:3000/admin/login")
        
        # Login as admin
        await page.fill('input[name="email"]', "admin@test.com")
        await page.fill('input[name="password"]', "admin123456")
        await page.click('button:has-text("登录")')
        
        # Wait for dashboard
        await page.wait_for_url("**/admin/dashboard")
        
        yield page
        await page.close()
    
    async def test_view_orders_list(self, authenticated_page: Page):
        """Test viewing orders list."""
        # Navigate to orders page
        await authenticated_page.click('text=订单管理')
        await authenticated_page.wait_for_url("**/admin/orders")
        
        # Wait for orders list to load
        await authenticated_page.wait_for_selector('text=订单列表')
        
        # Verify table headers
        await authenticated_page.wait_for_selector('text=订单ID')
        await authenticated_page.wait_for_selector('text=用户')
        await authenticated_page.wait_for_selector('text=套餐')
        await authenticated_page.wait_for_selector('text=金额')
        await authenticated_page.wait_for_selector('text=状态')
        
        # Verify pagination controls
        await authenticated_page.wait_for_selector('text=上一页')
        await authenticated_page.wait_for_selector('text=下一页')
    
    async def test_filter_orders_by_status(self, authenticated_page: Page):
        """Test filtering orders by status."""
        # Navigate to orders page
        await authenticated_page.click('text=订单管理')
        await authenticated_page.wait_for_url("**/admin/orders")
        
        # Wait for orders list to load
        await authenticated_page.wait_for_selector('text=订单列表')
        
        # Click status filter dropdown
        await authenticated_page.click('select[name="status"]')
        
        # Select "Paid" status
        await authenticated_page.select_option('select[name="status"]', "paid")
        
        # Wait for filtered results
        await authenticated_page.wait_for_timeout(1000)
        
        # Verify filtered results
        # (Specific assertions depend on actual implementation)
    
    async def test_view_order_details(self, authenticated_page: Page):
        """Test viewing order details."""
        # Navigate to orders page
        await authenticated_page.click('text=订单管理')
        await authenticated_page.wait_for_url("**/admin/orders")
        
        # Wait for orders list to load
        await authenticated_page.wait_for_selector('text=订单列表')
        
        # Click on first order details button
        await authenticated_page.click('button:has-text("详情")')
        
        # Wait for order details page
        await authenticated_page.wait_for_url("**/admin/orders/*")
        
        # Verify order details are displayed
        await authenticated_page.wait_for_selector('text=订单详情')
        await authenticated_page.wait_for_selector('text=基本信息')
        await authenticated_page.wait_for_selector('text=支付信息')
    
    async def test_update_order_status(self, authenticated_page: Page):
        """Test updating order status."""
        # Navigate to orders page
        await authenticated_page.click('text=订单管理')
        await authenticated_page.wait_for_url("**/admin/orders")
        
        # Wait for orders list to load
        await authenticated_page.wait_for_selector('text=订单列表')
        
        # Click on first order details button
        await authenticated_page.click('button:has-text("详情")')
        
        # Wait for order details page
        await authenticated_page.wait_for_url("**/admin/orders/*")
        
        # Click status update button
        await authenticated_page.click('button:has-text("更新状态")')
        
        # Wait for status modal
        await authenticated_page.wait_for_selector('text=更新订单状态')
        
        # Select new status
        await authenticated_page.select_option('select[name="status"]', "paid")
        
        # Enter reason
        await authenticated_page.fill('textarea[name="reason"]', "Test payment confirmation")
        
        # Confirm update
        await authenticated_page.click('button:has-text("确认")')
        
        # Wait for success message
        await authenticated_page.wait_for_selector('text=状态更新成功')
        
        # Verify status is updated
        await authenticated_page.wait_for_selector('text=已支付')


class TestAdminRefundManagementWorkflow:
    """Test admin refund management workflow end-to-end."""
    
    @pytest.fixture(scope="function")
    async def authenticated_page(self, browser_context: BrowserContext):
        """Create authenticated page for testing."""
        page = await browser_context.new_page()
        
        # Navigate to admin login page
        await page.goto("http://localhost:3000/admin/login")
        
        # Login as admin
        await page.fill('input[name="email"]', "admin@test.com")
        await page.fill('input[name="password"]', "admin123456")
        await page.click('button:has-text("登录")')
        
        # Wait for dashboard
        await page.wait_for_url("**/admin/dashboard")
        
        yield page
        await page.close()
    
    async def test_view_refunds_list(self, authenticated_page: Page):
        """Test viewing refunds list."""
        # Navigate to refunds page
        await authenticated_page.click('text=退款管理')
        await authenticated_page.wait_for_url("**/admin/refunds")
        
        # Wait for refunds list to load
        await authenticated_page.wait_for_selector('text=退款申请列表')
        
        # Verify table headers
        await authenticated_page.wait_for_selector('text=退款ID')
        await authenticated_page.wait_for_selector('text=订单')
        await authenticated_page.wait_for_selector('text=用户')
        await authenticated_page.wait_for_selector('text=金额')
        await authenticated_page.wait_for_selector('text=状态')
        
        # Verify pagination controls
        await authenticated_page.wait_for_selector('text=上一页')
        await authenticated_page.wait_for_selector('text=下一页')
    
    async def test_process_refund_approval(self, authenticated_page: Page):
        """Test processing refund approval."""
        # Navigate to refunds page
        await authenticated_page.click('text=退款管理')
        await authenticated_page.wait_for_url("**/admin/refunds")
        
        # Wait for refunds list to load
        await authenticated_page.wait_for_selector('text=退款申请列表')
        
        # Click on first refund process button
        await authenticated_page.click('button:has-text("处理")')
        
        # Wait for refund process modal
        await authenticated_page.wait_for_selector('text=处理退款申请')
        
        # Select approve action
        await authenticated_page.click('input[name="action"][value="approve"]')
        
        # Enter admin notes
        await authenticated_page.fill('textarea[name="adminNotes"]', "Test refund approval")
        
        # Confirm approval
        await authenticated_page.click('button:has-text("确认")')
        
        # Wait for success message
        await authenticated_page.wait_for_selector('text=退款处理成功')
        
        # Verify status is updated
        await authenticated_page.wait_for_selector('text=已批准')
    
    async def test_process_refund_rejection(self, authenticated_page: Page):
        """Test processing refund rejection."""
        # Navigate to refunds page
        await authenticated_page.click('text=退款管理')
        await authenticated_page.wait_for_url("**/admin/refunds")
        
        # Wait for refunds list to load
        await authenticated_page.wait_for_selector('text=退款申请列表')
        
        # Click on second refund process button
        await authenticated_page.click('button:has-text("处理")')
        
        # Wait for refund process modal
        await authenticated_page.wait_for_selector('text=处理退款申请')
        
        # Select reject action
        await authenticated_page.click('input[name="action"][value="reject"]')
        
        # Enter rejection reason
        await authenticated_page.fill('textarea[name="reason"]', "Test refund rejection")
        
        # Confirm rejection
        await authenticated_page.click('button:has-text("确认")')
        
        # Wait for success message
        await authenticated_page.wait_for_selector('text=退款处理成功')
        
        # Verify status is updated
        await authenticated_page.wait_for_selector('text=已拒绝')


class TestAdminDashboardWorkflow:
    """Test admin dashboard workflow end-to-end."""
    
    @pytest.fixture(scope="function")
    async def authenticated_page(self, browser_context: BrowserContext):
        """Create authenticated page for testing."""
        page = await browser_context.new_page()
        
        # Navigate to admin login page
        await page.goto("http://localhost:3000/admin/login")
        
        # Login as admin
        await page.fill('input[name="email"]', "admin@test.com")
        await page.fill('input[name="password"]', "admin123456")
        await page.click('button:has-text("登录")')
        
        # Wait for dashboard
        await page.wait_for_url("**/admin/dashboard")
        
        yield page
        await page.close()
    
    async def test_view_dashboard_stats(self, authenticated_page: Page):
        """Test viewing dashboard statistics."""
        # Wait for dashboard to load
        await authenticated_page.wait_for_selector('text=仪表板')
        
        # Verify user stats
        await authenticated_page.wait_for_selector('text=用户统计')
        await authenticated_page.wait_for_selector('text=总用户数')
        await authenticated_page.wait_for_selector('text=活跃用户')
        await authenticated_page.wait_for_selector('text=新用户')
        
        # Verify order stats
        await authenticated_page.wait_for_selector('text=订单统计')
        await authenticated_page.wait_for_selector('text=总订单数')
        await authenticated_page.wait_for_selector('text=已支付订单')
        await authenticated_page.wait_for_selector('text=待处理订单')
        
        # Verify revenue stats
        await authenticated_page.wait_for_selector('text=收入统计')
        await authenticated_page.wait_for_selector('text=总收入')
        await authenticated_page.wait_for_selector('text=今日收入')
        
        # Verify recent activity
        await authenticated_page.wait_for_selector('text=最近活动')
    
    async def test_navigate_between_sections(self, authenticated_page: Page):
        """Test navigation between admin sections."""
        # Start at dashboard
        await authenticated_page.wait_for_selector('text=仪表板')
        
        # Navigate to users
        await authenticated_page.click('text=用户管理')
        await authenticated_page.wait_for_url("**/admin/users")
        await authenticated_page.wait_for_selector('text=用户列表')
        
        # Navigate to orders
        await authenticated_page.click('text=订单管理')
        await authenticated_page.wait_for_url("**/admin/orders")
        await authenticated_page.wait_for_selector('text=订单列表')
        
        # Navigate to refunds
        await authenticated_page.click('text=退款管理')
        await authenticated_page.wait_for_url("**/admin/refunds")
        await authenticated_page.wait_for_selector('text=退款申请列表')
        
        # Navigate back to dashboard
        await authenticated_page.click('text=仪表板')
        await authenticated_page.wait_for_url("**/admin/dashboard")
        await authenticated_page.wait_for_selector('text=仪表板')
    
    async def test_logout_workflow(self, authenticated_page: Page):
        """Test admin logout workflow."""
        # Wait for dashboard to load
        await authenticated_page.wait_for_selector('text=仪表板')
        
        # Click logout button
        await authenticated_page.click('text=退出登录')
        
        # Wait for redirect to home page
        await authenticated_page.wait_for_url("**/")
        
        # Try to access admin page
        await authenticated_page.goto("http://localhost:3000/admin/dashboard")
        
        # Should redirect to login page
        await authenticated_page.wait_for_url("**/admin/login")
        
        # Verify login page is displayed
        await authenticated_page.wait_for_selector('text=管理员登录')


class TestAdminSecurityWorkflow:
    """Test admin security workflows end-to-end."""
    
    @pytest.fixture(scope="function")
    async def browser_context(self):
        """Create browser context for E2E testing."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            yield context
            await context.close()
            await browser.close()
    
    @pytest.fixture(scope="function")
    async def page(self, browser_context: BrowserContext):
        """Create page for E2E testing."""
        page = await browser_context.new_page()
        yield page
        await page.close()
    
    async def test_session_timeout_handling(self, page: Page):
        """Test session timeout handling."""
        # Navigate to admin login page
        await page.goto("http://localhost:3000/admin/login")
        
        # Login as admin
        await page.fill('input[name="email"]', "admin@test.com")
        await page.fill('input[name="password"]', "admin123456")
        await page.click('button:has-text("登录")')
        
        # Wait for dashboard
        await page.wait_for_url("**/admin/dashboard")
        
        # Simulate session timeout by clearing storage
        await page.evaluate("localStorage.clear()")
        await page.context.clear_cookies()
        
        # Try to access admin page
        await page.goto("http://localhost:3000/admin/users")
        
        # Should redirect to login page
        await page.wait_for_url("**/admin/login")
        
        # Verify session timeout message
        await page.wait_for_selector('text=会话已过期')
    
    async def test_unauthorized_access_prevention(self, page: Page):
        """Test prevention of unauthorized access."""
        # Try to access admin page directly without login
        await page.goto("http://localhost:3000/admin/users")
        
        # Should redirect to login page
        await page.wait_for_url("**/admin/login")
        
        # Verify login page is displayed
        await page.wait_for_selector('text=管理员登录')
        
        # Try to access API endpoints directly
        response = await page.goto("http://localhost:8000/api/v1/admin/users")
        
        # Should return 401 or redirect
        assert response is None or page.url.includes("/admin/login")
    
    async def test_concurrent_session_handling(self, page: Page):
        """Test concurrent session handling."""
        # Create two browser contexts
        context1 = await page.context.browser.new_context()
        context2 = await page.context.browser.new_context()
        
        page1 = await context1.new_page()
        page2 = await context2.new_page()
        
        try:
            # Login in first session
            await page1.goto("http://localhost:3000/admin/login")
            await page1.fill('input[name="email"]', "admin@test.com")
            await page1.fill('input[name="password"]', "admin123456")
            await page1.click('button:has-text("登录")')
            await page1.wait_for_url("**/admin/dashboard")
            
            # Login in second session
            await page2.goto("http://localhost:3000/admin/login")
            await page2.fill('input[name="email"]', "admin@test.com")
            await page2.fill('input[name="password"]', "admin123456")
            await page2.click('button:has-text("登录")')
            await page2.wait_for_url("**/admin/dashboard")
            
            # Both sessions should be active
            await page1.wait_for_selector('text=仪表板')
            await page2.wait_for_selector('text=仪表板')
            
            # Logout from first session
            await page1.click('text=退出登录')
            await page1.wait_for_url("**/")
            
            # Second session should still be active
            await page2.wait_for_selector('text=仪表板')
            
            # First session should be redirected to login if trying to access admin
            await page1.goto("http://localhost:3000/admin/users")
            await page1.wait_for_url("**/admin/login")
            
        finally:
            await page1.close()
            await page2.close()
            await context1.close()
            await context2.close()