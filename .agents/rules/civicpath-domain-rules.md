# CivicPath Domain & GIS Hierarchy Rules

## Description
Enforces mandatory constraints for CivicPath geographic hierarchy layers, DataMeet GeoJSON WGS84 coordinate projections, PostGIS spatial indexing, election candidate profile verification, civic issue state machine immutability, zero `any` policy, and pnpm package manager usage.

## Constraints

### 1. Mandatory 3-Layer Geographic Boundary Hierarchy
- All geographic boundaries MUST be strictly tagged with their exact layer type and level:
  - **Administrative**: `State` -> `District` -> `Taluk` -> `Block` -> (`Urban`/`Rural`)
  - **Political**: `Parliament (PC)` -> `Assembly (AC)`
  - **Local Body Urban**: `Municipal Corporation` -> `Municipality` -> `Town Panchayat` -> `Ward`
  - **Local Body Rural**: `District Panchayat` -> `Panchayat Union` -> `Village Panchayat`
- Boundary entities MUST NOT mix layers or bypass hierarchical parent links (`districtId`, `stateId`).

### 2. DataMeet Spatial WGS84 Constraint (`SRID 4326`)
- All DataMeet GeoJSON geometry polygons MUST be stored in PostGIS using `SRID 4326` (WGS84 lat/lng).
- Spatial queries (`ST_Contains`, `ST_Within`, `ST_DWithin`) MUST enforce `ST_SetSRID` with 4326 to prevent invalid coordinate projection errors.
- GIST spatial indexes (`USING GIST(geom)`) MUST be created on all spatial boundary tables.

### 3. User Location Point-in-Polygon Query Rule
- Location lookup endpoints (`/api/v1/constituencies/detect`) MUST accept valid `lat` ($-90 \le \text{lat} \le 90$) and `lng` ($-180 \le \text{lng} \le 180$).
- If no boundary polygon matches user coordinates, the API MUST return an empty boundary payload with an informative metadata status message, rather than throwing a server error.

### 4. Election Candidate Profile Verification Rule
- Every candidate profile linked to an Assembly or Parliamentary constituency MUST include verified election metadata (`party`, `electionYear`, `constituencyCode`).
- Affidavit PDF URLs and asset/liability disclosures MUST be sanitized and verified before public rendering.

### 5. Civic Issue State Machine Boundary Rule
- Status updates MUST NOT bypass state machine steps (`SUBMITTED` ➔ `UNDER_REVIEW` ➔ `ASSIGNED` ➔ `IN_PROGRESS` ➔ `RESOLVED` ➔ `VERIFIED`).
- Transitioning to `RESOLVED` REQUIRES mandatory resolution proof image URL and explanation notes.

### 6. Strict Type Safety & Package Manager Rule
- Using `any` type in Angular components, NestJS controllers, or GIS services is STRICTLY FORBIDDEN.
- Package installations MUST strictly use `pnpm`.
