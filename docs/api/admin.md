# Admin API Documentation

## Overview

The Admin API provides comprehensive endpoints for managing users, subscriptions, credit transactions, orders, and refunds. All endpoints require admin authentication and include comprehensive audit logging.

## Authentication

All admin endpoints require a valid admin JWT token. Include the token in the Authorization header:

```
Authorization: Bearer <your_admin_token>
```

## Base URL

```
/api/v1/admin
```

## Response Format

All responses follow the standard format:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    // Response data
  },
  "timestamp": "2023-10-01T12:00:00.000Z"
}
```

## Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1, min: 1)
- `page_size`: Items per page (default: 20, min: 1, max: 100)

Pagination metadata is included in the response:

```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

## Endpoints

### User Management

#### Get All Users

Retrieve a paginated list of all users with optional filtering.

**Endpoint:** `GET /users`

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `status_filter`: Filter by user status (active, suspended, inactive)
- `membership_filter`: Filter by membership type (free, basic, premium, enterprise)
- `email_filter`: Filter by email (contains)
- `sort_by`: Sort field (default: created_at)
- `sort_order`: Sort order (asc, desc, default: desc)

**Response:**
```json
{
  "success": true,
  "message": "获取用户列表成功",
  "data": {
    "users": [
      {
        "userId": "user123",
        "email": "user@example.com",
        "nickname": "John Doe",
        "credits": 1000,
        "membershipType": "premium",
        "status": "active",
        "isAdmin": false,
        "createdAt": "2023-10-01T12:00:00.000Z",
        "lastLoginAt": "2023-10-01T15:30:00.000Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

#### Get User Detail

Retrieve detailed information about a specific user.

**Endpoint:** `GET /users/{user_id}`

**Path Parameters:**
- `user_id`: The unique identifier of the user

**Response:**
```json
{
  "success": true,
  "message": "获取用户详情成功",
  "data": {
    "userId": "user123",
    "email": "user@example.com",
    "nickname": "John Doe",
    "credits": 1000,
    "membershipType": "premium",
    "status": "active",
    "isAdmin": false,
    "createdAt": "2023-10-01T12:00:00.000Z",
    "lastLoginAt": "2023-10-01T15:30:00.000Z"
  }
}
```

#### Update User Status

Update the status of a user.

**Endpoint:** `PUT /users/{user_id}/status`

**Path Parameters:**
- `user_id`: The unique identifier of the user

**Request Body:**
```json
{
  "status": "suspended",
  "reason": "Violation of terms of service"
}
```

**Response:**
```json
{
  "success": true,
  "message": "用户状态已更新为: suspended",
  "data": {
    "userId": "user123",
    "status": "suspended",
    "reason": "Violation of terms of service"
  }
}
```

#### Update User Subscription

Update a user's subscription/membership.

**Endpoint:** `PUT /users/{user_id}/subscription`

**Path Parameters:**
- `user_id`: The unique identifier of the user

**Request Body:**
```json
{
  "membershipType": "premium",
  "duration": 30,
  "reason": "User requested upgrade"
}
```

**Response:**
```json
{
  "success": true,
  "message": "用户订阅已更新",
  "data": {
    "userId": "user123",
    "email": "user@example.com",
    "currentMembership": "basic",
    "newMembership": "premium",
    "membershipExpiry": "2023-11-01T12:00:00.000Z",
    "changedBy": "admin@example.com",
    "changedAt": "2023-10-01T16:00:00.000Z",
    "reason": "User requested upgrade"
  }
}
```

### Credit Management

#### Get User Credit Transactions

Retrieve a paginated list of a user's credit transactions.

**Endpoint:** `GET /users/{user_id}/transactions`

**Path Parameters:**
- `user_id`: The unique identifier of the user

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `transaction_type`: Filter by transaction type (earn, spend)
- `source_filter`: Filter by transaction source
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "message": "获取用户交易记录成功",
  "data": {
    "transactions": [
      {
        "transactionId": "txn_abc123",
        "userId": "user123",
        "userEmail": "user@example.com",
        "type": "earn",
        "amount": 1000,
        "balanceAfter": 1500,
        "source": "purchase",
        "description": "Premium package purchase",
        "createdAt": "2023-10-01T12:00:00.000Z",
        "relatedTaskId": null,
        "relatedOrderId": "order_456"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 50,
      "total_pages": 3
    },
    "summary": {
      "totalEarned": 5000,
      "totalSpent": 3500,
      "netChange": 1500,
      "currentBalance": 1500
    }
  }
}
```

#### Adjust User Credits

Adjust a user's credit balance with audit logging.

**Endpoint:** `POST /users/{user_id}/credits/adjust`

**Path Parameters:**
- `user_id`: The unique identifier of the user

**Request Body:**
```json
{
  "amount": 500,
  "reason": "Compensation for service outage",
  "sendNotification": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "用户算力已调整",
  "data": {
    "userId": "user123",
    "oldCredits": 1000,
    "newCredits": 1500,
    "adjustment": 500,
    "reason": "Compensation for service outage"
  }
}
```

### Order Management

#### Get All Orders

Retrieve a paginated list of all orders with optional filtering.

**Endpoint:** `GET /orders`

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `status_filter`: Filter by order status (pending, paid, failed, cancelled, refunded)
- `user_filter`: Filter by user email or ID
- `package_type_filter`: Filter by package type (membership, credits)
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "message": "获取订单列表成功",
  "data": {
    "orders": [
      {
        "orderId": "order_456",
        "userId": "user123",
        "userEmail": "user@example.com",
        "packageId": "premium_monthly",
        "packageName": "Premium Monthly",
        "packageType": "membership",
        "originalAmount": 9900,
        "discountAmount": 0,
        "finalAmount": 9900,
        "paymentMethod": "alipay",
        "status": "paid",
        "createdAt": "2023-10-01T12:00:00.000Z",
        "paidAt": "2023-10-01T12:05:00.000Z",
        "expiresAt": "2023-10-01T13:00:00.000Z",
        "creditsAmount": null,
        "membershipDuration": 30
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "total_pages": 5
    },
    "summary": {
      "totalRevenue": 990000,
      "pendingOrders": 5,
      "conversionRate": 95.0
    }
  }
}
```

#### Get Order Detail

Retrieve detailed information about a specific order.

**Endpoint:** `GET /orders/{order_id}`

**Path Parameters:**
- `order_id`: The unique identifier of the order

**Response:**
```json
{
  "success": true,
  "message": "获取订单详情成功",
  "data": {
    "orderId": "order_456",
    "userId": "user123",
    "userEmail": "user@example.com",
    "packageId": "premium_monthly",
    "packageName": "Premium Monthly",
    "packageType": "membership",
    "originalAmount": 9900,
    "discountAmount": 0,
    "finalAmount": 9900,
    "paymentMethod": "alipay",
    "status": "paid",
    "createdAt": "2023-10-01T12:00:00.000Z",
    "paidAt": "2023-10-01T12:05:00.000Z",
    "expiresAt": "2023-10-01T13:00:00.000Z",
    "creditsAmount": null,
    "membershipDuration": 30
  }
}
```

#### Update Order Status

Update the status of an order.

**Endpoint:** `PUT /orders/{order_id}/status`

**Path Parameters:**
- `order_id`: The unique identifier of the order

**Request Body:**
```json
{
  "status": "paid",
  "reason": "Payment confirmed manually",
  "adminNotes": "User provided payment proof"
}
```

**Response:**
```json
{
  "success": true,
  "message": "订单状态已更新",
  "data": {
    "orderId": "order_456",
    "oldStatus": "pending",
    "newStatus": "paid",
    "reason": "Payment confirmed manually",
    "adminNotes": "User provided payment proof"
  }
}
```

### Refund Management

#### Get All Refunds

Retrieve a paginated list of all refund requests with optional filtering.

**Endpoint:** `GET /refunds`

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `status_filter`: Filter by refund status (processing, approved, rejected, completed)
- `user_filter`: Filter by user email or ID
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "message": "获取退款申请列表成功",
  "data": {
    "refunds": [
      {
        "refundId": "refund_789",
        "orderId": "order_456",
        "userId": "user123",
        "userEmail": "user@example.com",
        "amount": 9900,
        "reason": "Service not as described",
        "status": "processing",
        "createdAt": "2023-10-01T14:00:00.000Z",
        "processedAt": null,
        "completedAt": null,
        "processedBy": null,
        "adminNotes": null
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 10,
      "total_pages": 1
    },
    "summary": {
      "pendingRefunds": 3,
      "approvedRefunds": 5,
      "totalRefundAmount": 29700
    }
  }
}
```

#### Process Refund Action

Process a refund request (approve, reject, or complete).

**Endpoint:** `POST /refunds/{refund_id}/action`

**Path Parameters:**
- `refund_id`: The unique identifier of the refund

**Request Body:**
```json
{
  "action": "approve",
  "reason": "Valid complaint",
  "adminNotes": "User provided evidence",
  "externalRefundId": null
}
```

**Response:**
```json
{
  "success": true,
  "message": "退款申请已approve",
  "data": {
    "refundId": "refund_789",
    "action": "approve",
    "oldStatus": "processing",
    "newStatus": "approved",
    "reason": "Valid complaint",
    "adminNotes": "User provided evidence"
  }
}
```

### Dashboard Statistics

#### Get Dashboard Stats

Retrieve comprehensive dashboard statistics.

**Endpoint:** `GET /dashboard/stats`

**Response:**
```json
{
  "success": true,
  "message": "获取仪表板统计成功",
  "data": {
    "users": {
      "total": 1000,
      "active": 950,
      "admin": 5,
      "newToday": 10,
      "membershipBreakdown": {
        "free": 700,
        "basic": 200,
        "premium": 90,
        "enterprise": 10
      }
    },
    "credits": {
      "total": 500000,
      "transactionsToday": 150
    },
    "orders": {
      "total": 2000,
      "paid": 1900,
      "pending": 50,
      "conversionRate": 95.0
    },
    "revenue": {
      "total": 1990000,
      "today": 99000,
      "averageOrderValue": 1047.37
    },
    "subscriptions": {
      "pendingRefunds": 3,
      "totalRefundAmount": 29700
    },
    "recentActivity": [
      {
        "type": "order",
        "id": "order_456",
        "user": "user@example.com",
        "description": "创建订单: Premium Monthly",
        "amount": 99.00,
        "status": "paid",
        "timestamp": "2023-10-01T12:00:00.000Z"
      },
      {
        "type": "refund",
        "id": "refund_789",
        "user": "user2@example.com",
        "description": "申请退款: Service not as described",
        "amount": 99.00,
        "status": "processing",
        "timestamp": "2023-10-01T14:00:00.000Z"
      }
    ]
  }
}
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid input parameters
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient permissions (not an admin)
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "success": false,
  "message": "Error description",
  "error": {
    "code": "ERROR_CODE",
    "details": "Additional error details"
  },
  "timestamp": "2023-10-01T12:00:00.000Z"
}
```

## Audit Logging

All admin actions are logged for security and compliance. The audit log includes:

- Admin user ID and email
- Action performed
- Target resource type and ID
- Action details
- Timestamp
- IP address and user agent (when available)

## Rate Limiting

API endpoints may be subject to rate limiting to prevent abuse. Check the `X-RateLimit-*` headers in responses for current limits.

## Data Validation

All input data is validated according to the models defined in the API documentation. Invalid data will result in a 400 Bad Request response with details about the validation errors.