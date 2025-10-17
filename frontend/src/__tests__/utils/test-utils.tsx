import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { AdminAuthProvider } from '@/contexts/AdminAuthContext'

// Mock data generators
export const createMockAdminUser = () => ({
  userId: 'admin_001',
  email: 'admin@test.com',
  nickname: 'Test Admin',
  credits: 999999,
  isAdmin: true,
})

export const createMockNormalUser = () => ({
  userId: 'user_001',
  email: 'user@test.com',
  nickname: 'Test User',
  credits: 100,
  isAdmin: false,
})

export const createMockUsersList = (count: number = 5) => {
  return Array.from({ length: count }, (_, i) => ({
    userId: `user_${String(i + 1).padStart(3, '0')}`,
    email: `user${i + 1}@test.com`,
    nickname: `Test User ${i + 1}`,
    credits: Math.floor(Math.random() * 1000),
    status: 'active',
    isAdmin: false,
    createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    lastLoginAt: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
  }))
}

export const createMockOrdersList = (count: number = 5) => {
  return Array.from({ length: count }, (_, i) => ({
    orderId: `order_${String(i + 1).padStart(3, '0')}`,
    userId: `user_${String(i + 1).padStart(3, '0')}`,
    userEmail: `user${i + 1}@test.com`,
    packageId: `pkg_${String(i + 1).padStart(3, '0')}`,
    packageName: `Test Package ${i + 1}`,
    packageType: ['credits', 'membership'][Math.floor(Math.random() * 2)],
    originalAmount: Math.floor(Math.random() * 10000) + 1000,
    discountAmount: Math.floor(Math.random() * 1000),
    finalAmount: Math.floor(Math.random() * 10000) + 1000,
    paymentMethod: ['stripe', 'paypal'][Math.floor(Math.random() * 2)],
    status: ['pending', 'paid', 'failed', 'cancelled'][Math.floor(Math.random() * 4)],
    createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    paidAt: Math.random() > 0.5 ? new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString() : null,
    expiresAt: new Date(Date.now() + Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    creditsAmount: Math.floor(Math.random() * 1000) + 100,
    membershipDuration: Math.floor(Math.random() * 365) + 30,
  }))
}


export const createMockDashboardStats = () => ({
  users: {
    total: 1250,
    active: 1180,
    admin: 5,
    newToday: 12,
  },
  credits: {
    total: 250000,
    transactionsToday: 45,
  },
  orders: {
    total: 3200,
    paid: 2900,
    pending: 150,
    conversionRate: 90.6,
  },
  revenue: {
    total: 125000,
    today: 2500,
    averageOrderValue: 43.1,
  },
  recentActivity: [
    {
      type: 'order',
      id: 'order_001',
      user: 'user1@test.com',
      description: 'Created order: Basic Credits',
      amount: 10.0,
      status: 'paid',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
  ],
})

export const createMockPagination = (total: number = 100, page: number = 1, limit: number = 20) => ({
  page,
  limit,
  total,
  totalPages: Math.ceil(total / limit),
})

// Custom render function with providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <AdminAuthProvider>
      {children}
    </AdminAuthProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything from testing-library
export * from '@testing-library/react'
export { customRender as render }

// Mock API responses
export const createMockApiResponse = <T,>(data: T, message: string = 'Success') => ({
  success: true,
  data,
  message,
  timestamp: new Date().toISOString(),
})

export const createMockPaginatedResponse = <T,>(
  items: T[],
  total: number = items.length,
  page: number = 1,
  limit: number = 20,
) => ({
  success: true,
  data: {
    items,
    pagination: createMockPagination(total, page, limit),
  },
  message: 'Success',
  timestamp: new Date().toISOString(),
})

// Mock API functions
export const mockAdminLogin = jest.fn()
export const mockAdminGetUsers = jest.fn()
export const mockAdminGetOrders = jest.fn()
export const mockAdminGetDashboardStats = jest.fn()
export const mockAdminUpdateUserStatus = jest.fn()
export const mockAdminAdjustUserCredits = jest.fn()

// Helper functions for testing
export const waitForLoadingToFinish = () => new Promise(resolve => setTimeout(resolve, 0))

export const fillForm = (form: HTMLElement, data: Record<string, string>) => {
  Object.entries(data).forEach(([name, value]) => {
    const input = form.querySelector(`[name="${name}"]`) as HTMLInputElement
    if (input) {
      input.value = value
      input.dispatchEvent(new Event('change', { bubbles: true }))
    }
  })
}

export const submitForm = (form: HTMLElement) => {
  const submitButton = form.querySelector('button[type="submit"]') as HTMLButtonElement
  if (submitButton) {
    submitButton.click()
  }
}

export const clickButton = (text: string) => {
  const button = document.querySelector(`button:contains("${text}")`) as HTMLButtonElement
  if (button) {
    button.click()
  }
}

// Custom matchers
expect.extend({
  toBeInTheDocument: (received) => {
    const pass = received && document.body.contains(received)
    return {
      message: () =>
        `expected element ${pass ? 'not ' : ''}to be in the document`,
      pass,
    }
  },
})

// Mock IntersectionObserver for components that use it
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver for components that use it
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}