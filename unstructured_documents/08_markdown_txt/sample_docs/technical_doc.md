# Building REST APIs: A Comprehensive Guide

## Introduction

REST (Representational State Transfer) is an architectural style for designing networked applications. RESTful APIs have become the standard way for web services to communicate, powering everything from mobile apps to microservices architectures. This guide covers the essential concepts, best practices, and implementation patterns for building robust REST APIs.

## Core Principles

REST is built on several fundamental principles that guide API design:

- **Statelessness**: Each request contains all the information needed to process it. The server does not store client session state between requests.
- **Client-Server Separation**: The client and server are independent. The client does not need to know about data storage, and the server does not need to know about the user interface.
- **Uniform Interface**: Resources are identified by URIs, manipulated through representations, and self-descriptive messages.
- **Cacheability**: Responses must define themselves as cacheable or non-cacheable to improve performance.
- **Layered System**: The architecture can be composed of hierarchical layers, with each layer only knowing about the layer it interacts with.

## HTTP Methods

RESTful APIs use standard HTTP methods to perform operations on resources:

| Method | Purpose | Idempotent | Safe | Example |
|--------|---------|------------|------|---------|
| GET | Retrieve a resource | Yes | Yes | `GET /api/users/123` |
| POST | Create a new resource | No | No | `POST /api/users` |
| PUT | Replace a resource entirely | Yes | No | `PUT /api/users/123` |
| PATCH | Partially update a resource | No | No | `PATCH /api/users/123` |
| DELETE | Remove a resource | Yes | No | `DELETE /api/users/123` |

### Idempotency

An operation is **idempotent** if performing it multiple times produces the same result as performing it once. GET, PUT, and DELETE are idempotent by design. POST is not, because calling it twice creates two resources.

## Resource Design

### URL Structure

Follow these conventions for clean, intuitive URLs:

1. Use nouns, not verbs: `/api/users` not `/api/getUsers`
2. Use plural names: `/api/users` not `/api/user`
3. Use hyphens for readability: `/api/user-profiles` not `/api/userProfiles`
4. Nest resources for relationships: `/api/users/123/orders`
5. Keep URLs shallow (max 2-3 levels deep)

### Request and Response Format

JSON is the standard format for REST API request and response bodies:

```json
{
    "id": 123,
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "role": "admin",
    "created_at": "2025-01-15T10:30:00Z"
}
```

## Authentication and Authorization

### Common Authentication Methods

There are several approaches to securing REST APIs:

1. **API Keys**: Simple but limited. Pass a key in the header or query parameter.
2. **OAuth 2.0**: Industry standard for delegated authorization. Supports multiple grant types.
3. **JWT (JSON Web Tokens)**: Stateless tokens containing encoded claims. Popular for microservices.

```python
# Example: JWT authentication middleware
import jwt
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = payload
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401
        return f(*args, **kwargs)
    return decorated
```

## Error Handling

### Standard Error Response Format

Consistent error responses make APIs easier to consume:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "The request body contains invalid fields.",
        "details": [
            {
                "field": "email",
                "message": "Must be a valid email address"
            }
        ]
    }
}
```

### HTTP Status Codes

Use appropriate status codes to communicate the result:

- **200 OK**: Successful GET, PUT, PATCH, or DELETE
- **201 Created**: Successful POST that created a resource
- **204 No Content**: Successful DELETE with no response body
- **400 Bad Request**: Invalid request syntax or parameters
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Authenticated but not authorized
- **404 Not Found**: Resource does not exist
- **409 Conflict**: Request conflicts with current state
- **422 Unprocessable Entity**: Valid syntax but semantic errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected server failure

## Pagination

### Offset-Based Pagination

The simplest approach, using `page` and `per_page` parameters:

```
GET /api/users?page=2&per_page=20
```

### Cursor-Based Pagination

More efficient for large datasets. Uses an opaque cursor to mark position:

```
GET /api/users?cursor=eyJpZCI6MTIzfQ&limit=20
```

## Best Practices Summary

1. Use consistent naming conventions across all endpoints
2. Version your API from day one (e.g., `/api/v1/users`)
3. Implement rate limiting to protect your service
4. Return appropriate HTTP status codes
5. Provide comprehensive error messages
6. Support filtering, sorting, and pagination for list endpoints
7. Use HATEOAS links to make the API discoverable
8. Document your API with OpenAPI/Swagger specifications
9. Implement request validation at the API boundary
10. Log all requests for debugging and auditing
