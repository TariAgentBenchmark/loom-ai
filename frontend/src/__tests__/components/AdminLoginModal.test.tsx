import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AdminLoginModal } from '@/components/AdminLoginModal'
import { AdminAuthProvider } from '@/contexts/AdminAuthContext'
import { createMockAdminUser } from '../utils/test-utils'

// Mock the admin auth context
const mockLogin = jest.fn()
const mockOnClose = jest.fn()

// Mock component with providers
const MockAdminLoginModal = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
  <AdminAuthProvider>
    <AdminLoginModal isOpen={isOpen} onClose={onClose} />
  </AdminAuthProvider>
)

// Mock the admin auth context
jest.mock('@/contexts/AdminAuthContext', () => ({
  ...jest.requireActual('@/contexts/AdminAuthContext'),
  useAdminAuth: () => ({
    login: mockLogin,
    state: { status: 'loggedOut' }
  })
}))

describe('AdminLoginModal', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should not render when isOpen is false', () => {
    render(<MockAdminLoginModal isOpen={false} onClose={mockOnClose} />)
    
    expect(screen.queryByText('管理员登录')).not.toBeInTheDocument()
  })

  it('should render when isOpen is true', () => {
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    expect(screen.getByText('管理员登录')).toBeInTheDocument()
    expect(screen.getByLabelText('邮箱')).toBeInTheDocument()
    expect(screen.getByLabelText('密码')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument()
  })

  it('should close modal when close button is clicked', async () => {
    const user = userEvent.setup()
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const closeButton = screen.getByRole('button', { name: /close/i })
    await user.click(closeButton)
    
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('should close modal when backdrop is clicked', async () => {
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const backdrop = screen.getByText('管理员登录').closest('[role="dialog"]')?.parentElement
    if (backdrop) {
      fireEvent.click(backdrop)
      expect(mockOnClose).toHaveBeenCalledTimes(1)
    }
  })

  it('should update email and password fields when typed', async () => {
    const user = userEvent.setup()
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const emailInput = screen.getByLabelText('邮箱')
    const passwordInput = screen.getByLabelText('密码')
    
    await user.type(emailInput, 'admin@test.com')
    await user.type(passwordInput, 'password123')
    
    expect(emailInput).toHaveValue('admin@test.com')
    expect(passwordInput).toHaveValue('password123')
  })

  it('should call login with correct credentials when form is submitted', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValue(undefined)
    
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const emailInput = screen.getByLabelText('邮箱')
    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '登录' })
    
    await user.type(emailInput, 'admin@test.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    expect(mockLogin).toHaveBeenCalledWith('admin@test.com', 'password123')
  })

  it('should show loading state during login', async () => {
    const user = userEvent.setup()
    mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const emailInput = screen.getByLabelText('邮箱')
    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '登录' })
    
    await user.type(emailInput, 'admin@test.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    expect(screen.getByText('登录中...')).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
    expect(emailInput).toBeDisabled()
    expect(passwordInput).toBeDisabled()
  })

  it('should close modal and reset form on successful login', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValue(undefined)
    
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const emailInput = screen.getByLabelText('邮箱')
    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '登录' })
    
    await user.type(emailInput, 'admin@test.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })
  })

  it('should display error message on login failure', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Invalid credentials'
    mockLogin.mockRejectedValue(new Error(errorMessage))
    
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const emailInput = screen.getByLabelText('邮箱')
    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '登录' })
    
    await user.type(emailInput, 'admin@test.com')
    await user.type(passwordInput, 'wrongpassword')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('should clear error message when user starts typing', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Invalid credentials'
    mockLogin.mockRejectedValue(new Error(errorMessage))
    
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const emailInput = screen.getByLabelText('邮箱')
    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '登录' })
    
    await user.type(emailInput, 'admin@test.com')
    await user.type(passwordInput, 'wrongpassword')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
    
    // Start typing in email field
    await user.type(emailInput, 'a')
    
    // Error should be cleared
    expect(screen.queryByText(errorMessage)).not.toBeInTheDocument()
  })

  it('should not close modal when loading and close button is clicked', async () => {
    const user = userEvent.setup()
    mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const emailInput = screen.getByLabelText('邮箱')
    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '登录' })
    
    await user.type(emailInput, 'admin@test.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    const closeButton = screen.getByRole('button', { name: /close/i })
    await user.click(closeButton)
    
    expect(mockOnClose).not.toHaveBeenCalled()
  })

  it('should validate form fields', async () => {
    const user = userEvent.setup()
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const submitButton = screen.getByRole('button', { name: '登录' })
    await user.click(submitButton)
    
    // HTML5 validation should prevent submission
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('should handle non-Error objects in login failure', async () => {
    const user = userEvent.setup()
    mockLogin.mockRejectedValue('Login failed')
    
    render(<MockAdminLoginModal isOpen={true} onClose={mockOnClose} />)
    
    const emailInput = screen.getByLabelText('邮箱')
    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '登录' })
    
    await user.type(emailInput, 'admin@test.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('登录失败，请重试')).toBeInTheDocument()
    })
  })
})