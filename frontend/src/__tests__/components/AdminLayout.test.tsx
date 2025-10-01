import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AdminLayout from '@/components/AdminLayout'
import { AdminAuthProvider } from '@/contexts/AdminAuthContext'
import { createMockAdminUser } from '../utils/test-utils'

// Mock Next.js router
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/admin/dashboard',
}))

// Mock admin auth context
const mockLogout = jest.fn()

jest.mock('@/contexts/AdminAuthContext', () => ({
  ...jest.requireActual('@/contexts/AdminAuthContext'),
  useAdminAuth: () => ({
    logout: mockLogout,
    state: { status: 'authenticated' }
  }),
  useAdminUser: () => ({
    user: createMockAdminUser(),
    accessToken: 'mock-token',
    refreshToken: 'mock-refresh-token'
  })
}))

describe('AdminLayout', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  const renderWithProviders = (children: React.ReactNode) => {
    return render(
      <AdminAuthProvider>
        {children}
      </AdminAuthProvider>
    )
  }

  it('should render the admin layout correctly', () => {
    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    expect(screen.getByText('LoomAI 管理后台')).toBeInTheDocument()
    expect(screen.getByText('仪表板')).toBeInTheDocument()
    expect(screen.getByText('用户管理')).toBeInTheDocument()
    expect(screen.getByText('订阅管理')).toBeInTheDocument()
    expect(screen.getByText('订单管理')).toBeInTheDocument()
    expect(screen.getByText('退款管理')).toBeInTheDocument()
    expect(screen.getByText('统计分析')).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('should highlight the current page in navigation', () => {
    jest.mocked(require('next/navigation').usePathname).mockReturnValue('/admin/users')
    
    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    const usersLink = screen.getByText('用户管理')
    expect(usersLink.closest('button')).toHaveClass('bg-blue-100', 'text-blue-900')
  })

  it('should navigate to correct page when navigation item is clicked', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    const ordersLink = screen.getByText('订单管理')
    await user.click(ordersLink)

    expect(mockPush).toHaveBeenCalledWith('/admin/orders')
  })

  it('should show user information in sidebar', () => {
    const mockUser = createMockAdminUser()
    
    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    expect(screen.getByText(mockUser.nickname)).toBeInTheDocument()
    expect(screen.getByText(mockUser.email)).toBeInTheDocument()
    expect(screen.getByText(mockUser.nickname.charAt(0))).toBeInTheDocument()
  })

  it('should handle logout when logout button is clicked', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    const logoutButton = screen.getByText('退出登录')
    await user.click(logoutButton)

    expect(mockLogout).toHaveBeenCalledTimes(1)
    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('should toggle mobile sidebar when menu button is clicked', async () => {
    const user = userEvent.setup()
    
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    })

    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    const menuButton = screen.getByRole('button', { name: /menu/i })
    await user.click(menuButton)

    // Mobile sidebar should be visible
    const sidebar = screen.getByText('LoomAI 管理后台').closest('.translate-x-0')
    expect(sidebar).toBeInTheDocument()
  })

  it('should close mobile sidebar when close button is clicked', async () => {
    const user = userEvent.setup()
    
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    })

    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    // Open sidebar first
    const menuButton = screen.getByRole('button', { name: /menu/i })
    await user.click(menuButton)

    // Then close it
    const closeButton = screen.getByRole('button', { name: /close/i })
    await user.click(closeButton)

    // Sidebar should be hidden
    const sidebar = screen.getByText('LoomAI 管理后台').closest('.-translate-x-full')
    expect(sidebar).toBeInTheDocument()
  })

  it('should close mobile sidebar when navigation item is clicked', async () => {
    const user = userEvent.setup()
    
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    })

    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    // Open sidebar first
    const menuButton = screen.getByRole('button', { name: /menu/i })
    await user.click(menuButton)

    // Click navigation item
    const usersLink = screen.getByText('用户管理')
    await user.click(usersLink)

    expect(mockPush).toHaveBeenCalledWith('/admin/users')
    
    // Sidebar should be closed
    const sidebar = screen.getByText('LoomAI 管理后台').closest('.-translate-x-full')
    expect(sidebar).toBeInTheDocument()
  })

  it('should display fallback avatar when user has no nickname', () => {
    jest.mocked(require('@/contexts/AdminAuthContext').useAdminUser).mockReturnValue({
      user: {
        ...createMockAdminUser(),
        nickname: undefined,
      },
      accessToken: 'mock-token',
      refreshToken: 'mock-refresh-token'
    })

    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    // Should display first character of email
    expect(screen.getByText('a')).toBeInTheDocument()
  })

  it('should display fallback text when user has no nickname or email', () => {
    jest.mocked(require('@/contexts/AdminAuthContext').useAdminUser).mockReturnValue({
      user: {
        ...createMockAdminUser(),
        nickname: undefined,
        email: undefined,
      },
      accessToken: 'mock-token',
      refreshToken: 'mock-refresh-token'
    })

    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    // Should display "A" as fallback
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('should display "管理员" as fallback nickname', () => {
    jest.mocked(require('@/contexts/AdminAuthContext').useAdminUser).mockReturnValue({
      user: {
        ...createMockAdminUser(),
        nickname: undefined,
      },
      accessToken: 'mock-token',
      refreshToken: 'mock-refresh-token'
    })

    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    expect(screen.getByText('管理员')).toBeInTheDocument()
  })

  it('should highlight nested routes correctly', () => {
    jest.mocked(require('next/navigation').usePathname).mockReturnValue('/admin/users/123')
    
    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    const usersLink = screen.getByText('用户管理')
    expect(usersLink.closest('button')).toHaveClass('bg-blue-100', 'text-blue-900')
  })

  it('should highlight order detail routes correctly', () => {
    jest.mocked(require('next/navigation').usePathname).mockReturnValue('/admin/orders/order-123')
    
    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    const ordersLink = screen.getByText('订单管理')
    expect(ordersLink.closest('button')).toHaveClass('bg-blue-100', 'text-blue-900')
  })

  it('should highlight refund detail routes correctly', () => {
    jest.mocked(require('next/navigation').usePathname).mockReturnValue('/admin/refunds/refund-123')
    
    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    const refundsLink = screen.getByText('退款管理')
    expect(refundsLink.closest('button')).toHaveClass('bg-blue-100', 'text-blue-900')
  })

  it('should not highlight non-matching routes', () => {
    jest.mocked(require('next/navigation').usePathname).mockReturnValue('/admin/dashboard')
    
    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    const usersLink = screen.getByText('用户管理')
    expect(usersLink.closest('button')).not.toHaveClass('bg-blue-100', 'text-blue-900')
    expect(usersLink.closest('button')).toHaveClass('text-gray-600')
  })

  it('should show mobile header only on mobile screens', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    })

    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    // Mobile header should be visible
    expect(screen.getByText('LoomAI 管理后台')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /menu/i })).toBeInTheDocument()
  })

  it('should hide mobile header on desktop screens', () => {
    // Mock desktop viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    })

    renderWithProviders(
      <AdminLayout>
        <div>Test Content</div>
      </AdminLayout>
    )

    // Mobile header should not be visible
    const mobileHeader = screen.queryByText('LoomAI 管理后台')?.closest('.md\\:hidden')
    expect(mobileHeader).not.toBeInTheDocument()
  })
})