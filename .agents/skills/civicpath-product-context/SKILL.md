---
name: civicpath-product-context
description: Domain architecture, 3-layer administrative/political/local body boundary hierarchy, DataMeet GeoJSON integration, user location point-in-polygon detection, election candidate profiling, civic issue lifecycle state machine, Angular Signal GIS UI components, and NestJS PostGIS microservices for CivicPath enterprise platform.
---

# CivicPath Product Domain & Architectural Specification

## Overview

**CivicPath** (`civicpath.seyalicraft.com`) is Seyalicraft's comprehensive civic infrastructure, electoral intelligence, and community issue tracking platform.

It combines real-time citizen issue reporting with **3-layer GIS spatial boundary mapping** (sourced from DataMeet) to automatically determine a user's exact Administrative District, Political Constituency (MP/MLA), and Local Body (Urban/Rural). It also provides transparent **Election Candidate & Representative Profiling** alongside civic issue management.

---

## Ecosystem Repositories & Subdomains

- **Subdomain**: `https://civicpath.seyalicraft.com`
- **API Endpoint**: `https://api.civicpath.seyalicraft.com`
- **Repositories**:
  - `civicpath-frontend`: Angular 21 Signal-driven Web SPA (`muralitharan805/civicpath-frontend`)
  - `civicpath-backend`: NestJS REST/PostGIS Backend Engine (`muralitharan805/civicpath-backend`)

---

## 3-Layer Geographic & Administrative Hierarchy System

CivicPath organizes geographic data into 3 distinct, strictly-typed boundary layers:

```
CivicPath Geographic Hierarchy
├── 1. Administrative Boundaries
│   └── State ──► District ──► Taluk ──► Block ──► (Urban / Rural classification)
│
├── 2. Political Constituencies (Electoral)
│   └── Parliament (PC) ──► Assembly (AC)
│
└── 3. Local Body Boundaries
    ├── 3.1 Urban Local Bodies (ULB)
    │   └── Municipal Corporation ──► Municipality ──► Town Panchayat ──► Ward
    │
    └── 3.2 Rural Local Bodies (RLB)
        └── District Panchayat ──► Panchayat Union (Block) ──► Village Panchayat
```

### TypeScript Data Models for Hierarchy & GIS

```typescript
export enum BoundaryLayerType {
  ADMINISTRATIVE = 'ADMINISTRATIVE',
  POLITICAL = 'POLITICAL',
  LOCAL_BODY_URBAN = 'LOCAL_BODY_URBAN',
  LOCAL_BODY_RURAL = 'LOCAL_BODY_RURAL',
}

export enum AdminLevel {
  STATE = 'STATE',
  DISTRICT = 'DISTRICT',
  TALUK = 'TALUK',
  BLOCK = 'BLOCK',
}

export enum PoliticalLevel {
  PARLIAMENT = 'PARLIAMENT', // Lok Sabha (PC)
  ASSEMBLY = 'ASSEMBLY',     // Vidhan Sabha (AC)
}

export enum UrbanLocalBodyType {
  MUNICIPAL_CORPORATION = 'MUNICIPAL_CORPORATION',
  MUNICIPALITY = 'MUNICIPALITY',
  TOWN_PANCHAYAT = 'TOWN_PANCHAYAT',
  WARD = 'WARD',
}

export enum RuralLocalBodyType {
  DISTRICT_PANCHAYAT = 'DISTRICT_PANCHAYAT',
  PANCHAYAT_UNION = 'PANCHAYAT_UNION',
  VILLAGE_PANCHAYAT = 'VILLAGE_PANCHAYAT',
}

export interface PolygonBoundary {
  id: string;
  code: string; // e.g. AC-142, PC-39
  name: string;
  stateName: string;
  districtName?: string;
  layerType: BoundaryLayerType;
  level: AdminLevel | PoliticalLevel | UrbanLocalBodyType | RuralLocalBodyType;
  geojsonPolygon: GeoJSON.Geometry; // MultiPolygon / Polygon (WGS84 SRID 4326)
  metadata?: Record<string, unknown>;
}
```

---

## DataMeet GeoJSON Integration & Point-in-Polygon Lookup

### DataMeet Integration (`datameet/maps`)
Boundary polygon shapefiles are ingested from open-source **DataMeet** repositories (`datameet/maps` - India Assembly & Parliamentary Constituencies, District Boundaries).

### Spatial Point-in-Polygon Query Protocol
When a user opens CivicPath or grants location access (`lat`, `lng`), the NestJS backend executes spatial PostGIS queries to return all matching boundaries and candidates:

```sql
-- Find Parliamentary (PC) and Assembly (AC) Constituencies for user lat/lng
SELECT id, code, name, layer_type, level, ST_AsGeoJSON(geom) AS polygon
FROM spatial_boundaries
WHERE ST_Contains(
  geom,
  ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
);
```

---

## Election Candidate & Representative Entity (`Candidate`)

Citizens can view current incumbents (MP, MLA, Councillor) and contesting election candidates for their detected Assembly/Parliamentary boundary.

```typescript
export enum PoliticalParty {
  INC = 'INC',
  BJP = 'BJP',
  DMK = 'DMK',
  AIADMK = 'AIADMK',
  NTK = 'NTK',
  INDEPENDENT = 'INDEPENDENT',
  OTHER = 'OTHER',
}

export interface Candidate {
  id: string;
  name: string;
  constituencyCode: string; // References Assembly or Parliament boundary code
  constituencyType: PoliticalLevel; // ASSEMBLY or PARLIAMENT
  party: PoliticalParty;
  partySymbolUrl?: string;
  isIncumbent: boolean;
  electionYear: number;
  education: string;
  assetsTotal?: number;
  liabilitiesTotal?: number;
  criminalCasesCount: number;
  affidavitPdfUrl?: string;
  contactEmail?: string;
  socialLinks?: Record<string, string>;
  createdAt: Date;
}
```

---

## Civic Issue Entity & State Machine

In addition to constituency mapping, citizens can report and track civic issues tied to specific local bodies:

```typescript
export enum CivicIssueCategory {
  ROADS_PAVEMENT = 'ROADS_PAVEMENT',
  WATER_DRAINAGE = 'WATER_DRAINAGE',
  STREET_LIGHTING = 'STREET_LIGHTING',
  WASTE_MANAGEMENT = 'WASTE_MANAGEMENT',
  PUBLIC_SAFETY = 'PUBLIC_SAFETY',
  PARKS_ENVIRONMENT = 'PARKS_ENVIRONMENT',
}

export enum CivicIssueStatus {
  SUBMITTED = 'SUBMITTED',
  UNDER_REVIEW = 'UNDER_REVIEW',
  ASSIGNED = 'ASSIGNED',
  IN_PROGRESS = 'IN_PROGRESS',
  RESOLVED = 'RESOLVED',
  REJECTED = 'REJECTED',
  VERIFIED = 'VERIFIED',
}

export interface CivicIssue {
  id: string;
  trackingNumber: string; // e.g. CIV-2026-00892
  title: string;
  description: string;
  category: CivicIssueCategory;
  status: CivicIssueStatus;
  location: {
    type: 'Point';
    coordinates: [number, number];
    address: string;
  };
  constituencyCode: string; // Links issue directly to Assembly/Parliament constituency
  localBodyCode?: string;   // Links issue to Municipal Corporation / Village Panchayat
  reporterId: string;
  isAnonymous: boolean;
  upvoteCount: number;
  imageUrls: string[];
  createdAt: Date;
}
```

---

## Technical Architecture & GIS Rendering Guidelines

### Frontend (`civicpath-frontend`)
- **Map Renderer**: Leaflet / MapLibre GL rendering GeoJSON Polygons for AC and PC boundaries with dynamic color highlights on hover.
- **Signals State**:
  - `userLocation = signal<{ lat: number; lng: number } | null>(null);`
  - `detectedConstituency = computed(() => ...);`
  - `candidatesList = signal<Candidate[]>([]);`

### Backend (`civicpath-backend`)
- **Database**: PostgreSQL + PostGIS (`geometry(MultiPolygon, 4326)`).
- **Indexing**: GIST spatial indexes (`CREATE INDEX idx_boundaries_geom ON spatial_boundaries USING GIST(geom);`).
- **Data Pipeline**: Ingestion scripts for DataMeet GeoJSON maps (`pnpm run seed:datameet`).
