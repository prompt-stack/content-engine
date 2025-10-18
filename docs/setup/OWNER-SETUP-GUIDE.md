# 👑 Owner Account Setup (October 2025)

The OWNER role unlocks unlimited usage, bypasses rate limits, and grants full administrative permissions. With Clerk in place, the recommended flow is:

1. Sign in via Clerk (web) using the email you want to promote.
2. Run the owner promotion script to upgrade that database row.

---

## Why OWNER Still Matters

Even though Clerk manages authentication, the backend enforces tier- and role-based rules using the `users` table. Upgrading a user to OWNER:

- Sets `role = OWNER`, `tier = OWNER`.
- Enables `is_superuser`, `is_verified`, `is_active`.
- Bypasses monthly quota checks.
- Unlocks system management endpoints (when implemented).

---

## Step-by-Step

### 1. Sign in through Clerk

- Run the frontend locally (`npm run dev`) or visit the production site.
- Sign in using the target email address (passwordless email code or OAuth).
- This action creates the user row in PostgreSQL via JIT provisioning.

### 2. Promote the User to OWNER

```bash
cd backend
python scripts/create_owner.py
```

- Enter the same email you used with Clerk.
- If the user already exists, the script will offer:
  ```
  Upgrade existing user to OWNER? (yes/no)
  ```
  Type `yes` to promote.

The script updates `role`, `tier`, and related flags, then prints the privileges.

> **Note**: Creating a brand-new user with the script (by providing a password) is still supported for non-Clerk environments, but in production we rely on Clerk accounts.

---

## Verifying the Upgrade

```bash
# Assuming you have a valid Clerk session token
curl -X GET http://localhost:9765/api/auth/me   -H "Authorization: Bearer <token>"
```

Response snippet:

```json
{
  "email": "you@example.com",
  "role": "owner",
  "tier": "owner",
  "requests_this_month": 0,
  ...
}
```

You can also check directly in PostgreSQL:

```sql
SELECT email, role, tier, is_superuser
FROM users
WHERE email = 'you@example.com';
```

---

## Owner Privileges Overview

| Capability               | USER | ADMIN | SUPERADMIN | OWNER |
|--------------------------|:----:|:-----:|:----------:|:-----:|
| Use protected endpoints  | ✅   | ✅    | ✅         | ✅    |
| Rate limit bypass        | ❌   | ❌    | ❌         | ✅    |
| System management        | ❌   | ⚠️    | ✅         | ✅    |
| User management          | ❌   | ✅    | ✅         | ✅    |
| Feature flags / settings | ❌   | ❌    | ✅         | ✅    |

OWNER is intended for internal operators—you—and should not be granted to regular customers.

---

## Rotating Owner Accounts

If you need to revoke OWNER access:

1. Run `create_owner.py`, enter the email, and decline the upgrade prompt.
2. Manually downgrade in SQL:
   ```sql
   UPDATE users
   SET role = 'user', tier = 'free', is_superuser = false
   WHERE email = 'you@example.com';
   ```
3. Alternatively, delete the user row and let Clerk recreate it on the next login.

---

With this workflow, Clerk remains the source of truth for authentication, while the backend maintains fine-grained roles and quotas.
