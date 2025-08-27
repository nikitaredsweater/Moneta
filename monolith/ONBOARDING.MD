# Onboarding
This file will help you to quickly understand some core ideas that are a part of this service. If you do not need to investigate the code, and rather just understand the communication patterns, refer to [this MD file](README.MD).




## Authentication Middleware
By default all of the endpoints will be protected by JWT. Calling any of them will automatically extract the user information and add it to the request. That information is needed for 2 things
1. Verify user has logged in
2. Used in endpoints where permission is required to perform an action (most of the endpoints)

That middleware can be found at [app/security/middleware/jwt_parsing.py](app/security/middleware/jwt_parsing.py).

### Whitelisting Routes
If you find that additional routes need to be available regardless of whether client is logged in or not, in the same file you can find a whitelist. It looks like this:
```python
EXCLUDED_PATH_PATTERNS = ['/', '/v1/auth/login', '/openapi.json', '/docs']
```

This whitelist supports wildcards and exact routes. For example, adding `/` route will only allow the home route to be accessed without a JWT token, but adding `/*` will whitelist all routes in the monolith service.

## Endpoint Permissions
Most of the endpoints are protected by the JWT token. These tokens contain information about the userID, which is then used to set the user object in context. Most of the routes can only be accessed when a user has sufficient permissions. Permissions mapping is static, and currently supports the following roles of users:
```python
class UserRole(str, Enum):
    ADMIN = 'ADMIN'
    BUYER = 'BUYER'
    SELLER = 'SELLER'
    ISSUER = 'ISSUER'
```
The definition of supported roles can be found in [app/enums/roles.py](app/enums/roles.py).

### Permissions Mapping
The list of permissions each role has is defined inside of [app/security/permissions.py](app/security/permissions.py). Here is that mapping:

```python
# Note:
#
# Current implementation limits the ability of 'dynamic' user permissions.
# Once you are assigned to a role, only way to get expanded permissions on the
# Platform for a specific user is to allow the whole role more permissions
# This may be the inteded behavior, but I am not sure.

ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        # Global data access
        (Verb.VIEW, Entity.ALL_DATA),
        # User management
        (Verb.VIEW, Entity.ALL_USERS),
        (Verb.CREATE, Entity.USER),
        (Verb.UPDATE, Entity.USER),
        (Verb.DELETE, Entity.ALL_USERS),
        # Role management
        (Verb.VIEW, Entity.ALL_ROLES),
        (Verb.ASSIGN, Entity.ROLE),
        # Company
        (Verb.VIEW, Entity.COMPANY),
        (Verb.CREATE, Entity.COMPANY),
        (Verb.UPDATE, Entity.COMPANY),
        (Verb.DELETE, Entity.COMPANY),
        # Company address
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
        (Verb.CREATE, Entity.COMPANY_ADDRESS),
        (Verb.UPDATE, Entity.COMPANY_ADDRESS),
        (Verb.DELETE, Entity.COMPANY_ADDRESS),
    },
    UserRole.BUYER: {
        (Verb.VIEW, Entity.COMPANY),
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
    },
    UserRole.SELLER: {
        (Verb.VIEW, Entity.COMPANY),
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
    },
    UserRole.ISSUER: {
        (Verb.VIEW, Entity.COMPANY),
        (Verb.UPDATE, Entity.COMPANY),
        (Verb.VIEW, Entity.COMPANY_ADDRESS),
        (Verb.CREATE, Entity.COMPANY_ADDRESS),
        (Verb.UPDATE, Entity.COMPANY_ADDRESS),
        (Verb.DELETE, Entity.COMPANY_ADDRESS),
    },
}
```
### has_permission() Dependency Injection in Endpoints
Whenever adding a new endpoint, ensure to include the permission necessary via a dependency injection available at [app/security/permissions.py has_permission()](app/security/permissions.py).
This dependency requires the route to be JWT-protected.
