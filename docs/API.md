# API Documentation Guide

This document supplements the interactive **Swagger UI** (`/docs`) and **OpenAPI 3.x** schema (`/openapi.json`).

Per project requirements, every custom endpoint documents:
- what the action does
- which parameters to pass
- whether authentication is required
- possible responses and errors

---

## Authentication (`/auth`)

### `POST /auth/register`

| | |
|---|---|
| **Auth** | Not required |
| **Purpose** | Create a new user account |

**Request body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string (email) | Yes | Unique login email |
| `password` | string | Yes | Min 8 chars, uppercase + digit |

**Success (201):** Returns `id`, `email`, `is_active` (false), `created_at`.  
An activation token valid for 24 hours is created server-side.

**Errors:** `409` duplicate email · `422` validation failure

---

### `GET /auth/activate`

| | |
|---|---|
| **Auth** | Not required |
| **Purpose** | Activate account using email token |

**Query parameter:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | string | Yes | Activation token from registration email |

**Success (200):** `{"message": "Account activated successfully."}`  
**Errors:** `400` expired token · `404` token not found

---

### `POST /auth/activate/resend`

| | |
|---|---|
| **Auth** | Not required |
| **Purpose** | Issue a new activation token for an inactive account |

**Request body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string (email) | Yes | Email of inactive account |

**Success (200):** `{"message": "A new activation token has been generated."}`  
**Errors:** `400` user not found or already active · `422` invalid email

---

### `POST /auth/login`

| | |
|---|---|
| **Auth** | Not required |
| **Purpose** | Authenticate and receive JWT token pair |

**Request body:** `email`, `password`

**Success (200):** `access_token`, `refresh_token`, `token_type` (`bearer`)

**Errors:** `401` wrong credentials or inactive account

---

### `POST /auth/refresh`

| | |
|---|---|
| **Auth** | Not required |
| **Purpose** | Exchange refresh token for new access + refresh tokens |

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh_token` | string | Yes | Token from login |

**Success (200):** New `access_token`, `refresh_token`, `token_type`  
**Errors:** `401` invalid/expired token or deactivated user

---

### `POST /auth/logout`

| | |
|---|---|
| **Auth** | Bearer access token required |
| **Purpose** | Revoke a refresh token |

**Query parameter:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh_token` | string | Yes | Refresh token to revoke |

**Success (204):** No content  
**Errors:** `401` missing/invalid Bearer token

---

### `POST /auth/change-password`

| | |
|---|---|
| **Auth** | Bearer access token required |
| **Purpose** | Change account password |

**Request body:** `old_password`, `new_password`

**Success (200):** Password updated successfully  
**Errors:** `401` invalid old password or unauthorized session

---

### `POST /auth/forgot-password`

| | |
|---|---|
| **Auth** | Not required |
| **Purpose** | Request a password reset token |

**Request body:** `email`

**Success (200):** Ambiguous success confirmation (sent reset link if registered)

---

### `POST /auth/reset-password`

| | |
|---|---|
| **Auth** | Not required |
| **Purpose** | Complete password reset using token |

**Request body:** `token`, `new_password`

**Success (200):** Credentials updated; user can now log in  
**Errors:** `400` token has expired · `404` token string not found

---

## Movies (`/movies`)

### `GET /movies/`

List all movies. No auth required.

### `GET /movies/{movie_id}`

Get one movie by ID. No auth required.

**Path param:** `movie_id` (integer)

### `POST /movies/`

Create a movie. Bearer token required.

**Request body:** `title`, `description`, `duration_minutes`, `release_year`

---

## Shopping Cart (`/cart`)

All cart endpoints require Bearer access token.

### `GET /cart/`

Returns the user's cart and items. Auto-creates empty cart if missing.

### `POST /cart/items`

Add a movie to cart.

**Request body:** `movie_id` (integer)

**Errors:** `404` duplicate item in cart

### `DELETE /cart/items/{item_id}`

Remove one cart item by item ID.

### `DELETE /cart/`

Clear all items from cart (keeps empty cart container).

---

## Orders (`/orders`)

### `POST /orders/checkout`

| | |
|---|---|
| **Auth** | Bearer access token required |
| **Purpose** | Convert cart to pending order |

**Action:**
1. Reads cart items
2. Creates order with status `pending`
3. Snapshots `price_at_order` per movie
4. Sets `total_amount`
5. Clears cart

**Errors:** `400` empty cart · `401` unauthorized

---

## Password policy

Enforced on registration (and future password-change endpoints):

- Minimum 8 characters
- At least one uppercase letter
- At least one digit

---

## Background tasks (Celery Beat)

| Task | Schedule | Action |
|------|----------|--------|
| `cleanup_expired_tokens` | Every 30 min | Deletes expired activation, password-reset, and refresh tokens |

---

## Swagger access control

| `OPENAPI_DOCS_ENABLED` | Behavior |
|------------------------|----------|
| `true` (default) | `/docs`, `/redoc`, `/openapi.json` available |
| `false` | Documentation endpoints return disabled message |

Set in `.env` for production deployments.
