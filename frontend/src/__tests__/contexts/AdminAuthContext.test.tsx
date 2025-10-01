import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AdminAuthProvider, useAdminAuth, useAdminIsAuthenticated, useAdminUser } from '@/contexts/AdminAuthContext'
import { createMockAdminUser } from '../utils/test-utils'

// Mock the admin-auth module
const mockAuthenticateAdmin = jest.fn()
const mockRestoreAdminSession = jest.fn()
const mockPersistAdminSession = jest.fn()
const mockClearPersistedAdminSession = jest.fn()

jest.mock('@/lib/admin-auth', () => ({
  authenticateAdmin: mockAuthenticateAdmin,
  restoreAdminSession: mockRestoreAdminSession,
  persistAdminSession: mockPersistAdminSession,
  clearPersistedAdminSession: mockClearPersistedAdminSession,
  createAdminLoggedOutState: () => ({ status: 'loggedOut' }),
  createAdminAuthenticatingState: () => ({ status: 'authenticating' }),
  createAdminAuthenticatedState: (user: any, tokens: any) => ({
    status: 'authenticated',
    user,
    accessToken: tokens.accessToken,
    refreshToken: tokens.refreshToken
  }),
  isAdminAuthenticated: (state: any) => state.status === 'authenticated',
  isAdminAuthenticating: (state: any) => state.status === 'authenticating',
  isAdminLoggedOut: (state: any) => state.status === 'loggedOut'
}))

// Test component to consume the context
const TestComponent = () => {
  const { login, logout, state } = useAdminAuth()
  const isAuthenticated = useAdminIsAuthenticated()
  const adminUser = useAdminUser()

  return (
    <div>
      <div data-testid="auth-status">{state.status}</div>
      <div data-testid="is-authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="user-email">{adminUser?.user.email || 'no-user'}</div>
      <button onClick={() => login('test@test.com', 'password')}>
        Login
      </button>
      <button onClick={logout}>
        Logout
      </button>
    </div>
  )
}

describe('AdminAuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  it('should provide default logged out state', () => {
    mockRestoreAdminSession.mockReturnValue(null)

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    expect(screen.getByTestId('auth-status')).toHaveTextContent('loggedOut')
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
    expect(screen.getByTestId('user-email')).toHaveTextContent('no-user')
  })

  it('should restore existing session on mount', () => {
    const mockUser = createMockAdminUser()
    const mockSession = {
      user: mockUser,
      accessToken: 'mock-token',
      refreshToken: 'mock-refresh-token'
    }

    mockRestoreAdminSession.mockReturnValue(mockSession)

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
    expect(screen.getByTestId('user-email')).toHaveTextContent(mockUser.email)
  })

  it('should handle login process correctly', async () => {
    const user = userEvent.setup()
    const mockUser = createMockAdminUser()
    const mockTokens = {
      accessToken: 'new-access-token',
      refreshToken: 'new-refresh-token'
    }

    mockAuthenticateAdmin.mockResolvedValue({
      user: mockUser,
      ...mockTokens
    })

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    const loginButton = screen.getByText('Login')
    await user.click(loginButton)

    expect(mockAuthenticateAdmin).toHaveBeenCalledWith('test@test.com', 'password')
    expect(mockPersistAdminSession).toHaveBeenCalledWith({
      user: mockUser,
      ...mockTokens
    })

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
      expect(screen.getByTestId('user-email')).toHaveTextContent(mockUser.email)
    })
  })

  it('should show authenticating state during login', async () => {
    const user = userEvent.setup()
    
    mockAuthenticateAdmin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    const loginButton = screen.getByText('Login')
    await user.click(loginButton)

    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticating')
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
  })

  it('should handle login failure correctly', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Invalid credentials'
    
    mockAuthenticateAdmin.mockRejectedValue(new Error(errorMessage))

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    const loginButton = screen.getByText('Login')
    
    // Expect the login function to throw an error
    await expect(user.click(loginButton)).rejects.toThrow(errorMessage)

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('loggedOut')
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
    })
  })

  it('should handle logout correctly', async () => {
    const user = userEvent.setup()
    const mockUser = createMockAdminUser()
    const mockSession = {
      user: mockUser,
      accessToken: 'mock-token',
      refreshToken: 'mock-refresh-token'
    }

    mockRestoreAdminSession.mockReturnValue(mockSession)

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    // Verify initial authenticated state
    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')

    const logoutButton = screen.getByText('Logout')
    await user.click(logoutButton)

    expect(mockClearPersistedAdminSession).toHaveBeenCalled()

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('loggedOut')
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
      expect(screen.getByTestId('user-email')).toHaveTextContent('no-user')
    })
  })

  it('should throw error when useAdminAuth is used outside provider', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      render(<TestComponent />)
    }).toThrow('useAdminAuth must be used within an AdminAuthProvider')

    consoleError.mockRestore()
  })

  it('should handle session restoration with partial data', () => {
    const mockSession = {
      user: createMockAdminUser(),
      accessToken: 'mock-token',
      refreshToken: null // Missing refresh token
    }

    mockRestoreAdminSession.mockReturnValue(mockSession)

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    // Should still authenticate even with partial data
    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
  })

  it('should handle multiple login attempts', async () => {
    const user = userEvent.setup()
    const mockUser = createMockAdminUser()
    const mockTokens = {
      accessToken: 'new-access-token',
      refreshToken: 'new-refresh-token'
    }

    mockAuthenticateAdmin.mockResolvedValue({
      user: mockUser,
      ...mockTokens
    })

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    const loginButton = screen.getByText('Login')
    
    // First login
    await user.click(loginButton)
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
    })

    // Logout
    const logoutButton = screen.getByText('Logout')
    await user.click(logoutButton)
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('loggedOut')
    })

    // Second login
    await user.click(loginButton)
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
    })

    expect(mockAuthenticateAdmin).toHaveBeenCalledTimes(2)
    expect(mockPersistAdminSession).toHaveBeenCalledTimes(2)
    expect(mockClearPersistedAdminSession).toHaveBeenCalledTimes(1)
  })

  it('should handle rapid login attempts', async () => {
    const user = userEvent.setup()
    const mockUser = createMockAdminUser()
    const mockTokens = {
      accessToken: 'new-access-token',
      refreshToken: 'new-refresh-token'
    }

    mockAuthenticateAdmin.mockResolvedValue({
      user: mockUser,
      ...mockTokens
    })

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    const loginButton = screen.getByText('Login')
    
    // Rapid clicks
    await user.dblClick(loginButton)

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
    })

    // Should only call authenticate once due to state management
    expect(mockAuthenticateAdmin).toHaveBeenCalledTimes(1)
  })

  it('should handle login with different credentials', async () => {
    const user = userEvent.setup()
    
    // Test component with dynamic credentials
    const DynamicTestComponent = () => {
      const { login, state } = useAdminAuth()
      
      return (
        <div>
          <div data-testid="auth-status">{state.status}</div>
          <button onClick={() => login('user1@test.com', 'password1')}>
            Login User 1
          </button>
          <button onClick={() => login('user2@test.com', 'password2')}>
            Login User 2
          </button>
        </div>
      )
    }

    const mockUser1 = { ...createMockAdminUser(), email: 'user1@test.com' }
    const mockUser2 = { ...createMockAdminUser(), email: 'user2@test.com' }

    mockAuthenticateAdmin
      .mockResolvedValueOnce({
        user: mockUser1,
        accessToken: 'token1',
        refreshToken: 'refresh1'
      })
      .mockResolvedValueOnce({
        user: mockUser2,
        accessToken: 'token2',
        refreshToken: 'refresh2'
      })

    render(
      <AdminAuthProvider>
        <DynamicTestComponent />
      </AdminAuthProvider>
    )

    const loginButton1 = screen.getByText('Login User 1')
    await user.click(loginButton1)

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
    })

    expect(mockAuthenticateAdmin).toHaveBeenCalledWith('user1@test.com', 'password1')

    // Logout and login with different user
    const logoutButton = screen.getByText('Logout')
    await user.click(logoutButton)

    const loginButton2 = screen.getByText('Login User 2')
    await user.click(loginButton2)

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated')
    })

    expect(mockAuthenticateAdmin).toHaveBeenCalledWith('user2@test.com', 'password2')
  })

  it('should handle localStorage errors gracefully', () => {
    // Mock localStorage to throw an error
    const originalGetItem = localStorage.getItem
    localStorage.getItem = jest.fn(() => {
      throw new Error('localStorage error')
    })

    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <AdminAuthProvider>
        <TestComponent />
      </AdminAuthProvider>
    )

    // Should still render with default state
    expect(screen.getByTestId('auth-status')).toHaveTextContent('loggedOut')

    localStorage.getItem = originalGetItem
    consoleError.mockRestore()
  })
})