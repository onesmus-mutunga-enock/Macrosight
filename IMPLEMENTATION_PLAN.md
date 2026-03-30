# MacroSight Backend Implementation Plan

## Overview
This document outlines the implementation plan for completing the MacroSight Django REST backend based on the V1 API contract.

## Current State Analysis

### Existing Models (✅ Already Implemented)
- **User** (apps/users/models.py) - Extended AbstractUser with roles, MFA, audit fields
- **Role** (apps/governance/models.py) - System roles with permissions
- **Permission** (apps/governance/models.py) - Permission definitions
- **RolePermission** (apps/governance/models.py) - Role-permission mappings
- **AuditLog** (apps/audit/models.py) - Centralized audit logging
- **Sector** (apps/sectors/models.py) - Economic sector registry
- **SectorPolicyMapping** (apps/sectors/models.py) - Policy-sector relationships
- **Indicator** (apps/indicators/models.py) - External economic indicators
- **IndicatorVersion** (apps/indicators/models.py) - Versioned indicator data
- **IndicatorValue** (apps/indicators/models.py) - Time series indicator values
- **Policy** (apps/policies/models.py) - Policy definitions
- **PolicyVersion** (apps/policies/models.py) - Financial-year policy configurations
- **PolicyParameter** (apps/policies/models.py) - Policy parameter definitions
- **PolicyParameterValue** (apps/policies/models.py) - Parameter values by financial year
- **InputCost** (apps/costs/models.py) - Input cost drivers for sectors
- **InputCostValue** (apps/costs/models.py) - Time series cost values
- **Forecast** (apps/forecasts/models.py) - Forecast entities with governance
- **ForecastSchedule** (apps/forecasts/models.py) - Scheduled forecast jobs
- **SystemConfig** (apps/system/models.py) - System configuration
- **DataSnapshot** (apps/system/models.py) - Immutable data snapshots
- **SystemJob** (apps/system/models.py) - Background job monitoring
- **Alert** (apps/system/models.py) - Alerts and thresholds

### Missing Models (❌ Need Implementation)
- **LoginHistory** - Login history tracking
- **MFADevice** - MFA device management
- **Product** - Product registry
- **Sale** - Sales data model
- **GovernmentNotice** - Government notices
- **Scenario** - Scenario simulation results

### Missing Components (❌ Need Implementation)
- **Views** - All API endpoints
- **Serializers** - Missing many serializers
- **Permissions** - Role-based permission system
- **Authentication** - JWT authentication
- **URLs** - API URL configurations
- **Admin** - Django admin configurations
- **Tests** - Unit and integration tests

## Implementation Phases

### Phase 1: Authentication & Access Control (Priority: HIGH)
**Models to Complete:**
- LoginHistory
- MFADevice

**Endpoints to Implement:**
- POST /api/v1/auth/login/
- POST /api/v1/auth/refresh/
- POST /api/v1/auth/logout/
- GET /api/v1/auth/me/
- POST /api/v1/auth/change-password/
- POST /api/v1/auth/mfa/verify/

**Admin Endpoints:**
- GET /api/v1/admin/auth/login-history/
- POST /api/v1/admin/auth/force-logout/{user_id}/

**Tasks:**
1. Complete LoginHistory and MFADevice models
2. Implement JWT authentication views
3. Create authentication serializers
4. Set up URL routing
5. Add role-based permissions

### Phase 2: Users, Roles, Permissions (Priority: HIGH)
**Endpoints to Implement:**
- GET /api/v1/admin/users/
- POST /api/v1/admin/users/
- GET /api/v1/admin/users/{id}/
- PUT /api/v1/admin/users/{id}/
- DELETE /api/v1/admin/users/{id}/
- PUT /api/v1/admin/users/{id}/disable/
- PUT /api/v1/admin/users/{id}/enable/
- PUT /api/v1/admin/users/{id}/reset-credentials/

**Role Management:**
- GET /api/v1/admin/roles/
- POST /api/v1/admin/roles/
- PUT /api/v1/admin/roles/{id}/
- DELETE /api/v1/admin/roles/{id}/
- PUT /api/v1/admin/users/{id}/role/

**Permission Management:**
- GET /api/v1/admin/permissions/

**Tasks:**
1. Create user management views
2. Implement role management views
3. Create permission management views
4. Add comprehensive permissions system

### Phase 3: Product & Sector Registry (Priority: MEDIUM)
**Models to Complete:**
- Product

**Endpoints to Implement:**
- GET /api/v1/sectors/
- POST /api/v1/sectors/
- GET /api/v1/sectors/{id}/
- PUT /api/v1/sectors/{id}/
- DELETE /api/v1/sectors/{id}/

- GET /api/v1/products/
- POST /api/v1/products/
- PUT /api/v1/products/{id}/
- DELETE /api/v1/products/{id}/

**Auditor Endpoints:**
- GET /api/v1/products/history/

**Tasks:**
1. Complete Product model
2. Create sector management views
3. Create product management views
4. Add audit trail for products

### Phase 4: Sales Data Ingestion (Priority: MEDIUM)
**Endpoints to Implement:**
- POST /api/v1/sales/upload/
- GET /api/v1/sales/upload/status/

**Analyst Endpoints:**
- GET /api/v1/sales/
- GET /api/v1/sales/{id}/
- GET /api/v1/sales/export/

**Admin Endpoints:**
- DELETE /api/v1/sales/{id}/
- PUT /api/v1/admin/sales/{id}/lock/
- GET /api/v1/admin/sales/ingestion-logs/
- GET /api/v1/admin/sales/data-quality/

**Tasks:**
1. Create CSV ingestion service
2. Implement sales management views
3. Add data quality monitoring
4. Create export functionality

### Phase 5: Indicators & Macro Parameters (Priority: MEDIUM)
**Endpoints to Implement:**
- GET /api/v1/indicators/
- POST /api/v1/indicators/
- PUT /api/v1/indicators/{id}/
- DELETE /api/v1/indicators/{id}/

**Admin Endpoints:**
- POST /api/v1/admin/indicators/sync/
- PUT /api/v1/admin/indicators/source/
- GET /api/v1/admin/indicators/quality-report/
- GET /api/v1/admin/indicators/ingestion-log/

**Manual Macro Parameters:**
- GET /api/v1/macro/parameters/
- POST /api/v1/macro/parameters/
- PUT /api/v1/macro/parameters/{id}/
- DELETE /api/v1/macro/parameters/{id}/

**Versioning:**
- POST /api/v1/macro/parameters/{id}/version/
- PUT /api/v1/macro/parameters/{vid}/activate/

**Tasks:**
1. Create indicator management views
2. Implement macro parameter management
3. Add versioning system
4. Create sync and quality monitoring

### Phase 6: Policy & Legislation Management (Priority: MEDIUM)
**Endpoints to Implement:**
- POST /api/v1/policies/
- GET /api/v1/policies/
- PUT /api/v1/policies/{id}/
- DELETE /api/v1/policies/{id}/

**Impact Analysis:**
- POST /api/v1/policies/{id}/impact/

**Auditor Endpoints:**
- GET /api/v1/policies/history/

**Tasks:**
1. Create policy management views
2. Implement impact analysis
3. Add audit trail for policies

### Phase 7: Policy Parameters (Versioned) (Priority: LOW)
