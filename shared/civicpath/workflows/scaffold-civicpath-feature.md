---
description: "Workflow to scaffold CivicPath feature modules (3-layer GIS boundary detection, DataMeet GeoJSON ingestion, Election Candidate profiles, and Angular Leaflet map signals). Triggered by 'civicpath:', 'civic:', or '/scaffold-civicpath-feature'."
trigger: manual
---

# Scaffold CivicPath Feature Module Workflow

This workflow guides the AI agent and software engineer through scaffolding an enterprise-grade CivicPath feature module (e.g., Lat/Lng Boundary Detector, Election Candidate Profiles, DataMeet GeoJSON Seeder, Map Polygon Renderer).

## Step 1: Feature Scope Analysis

Select target module type:
1. **GIS Boundary Detector**: Detect Assembly (AC) & Parliament (PC) polygons for user `lat`, `lng`.
2. **Election Candidate Profile**: Candidate affidavits, party affiliations, and election statistics for a detected constituency.
3. **DataMeet Ingestion**: Command-line script to ingest DataMeet GeoJSON shapefiles into PostgreSQL/PostGIS.
4. **Civic Issue Reporting**: Location-tagged issue reporting linked to local bodies.

---

## Step 2: Scaffold NestJS GIS & Candidate Microservice (`civicpath-backend`)

### 1. Spatial Boundary Detector Service
```typescript
@Injectable()
export class BoundaryDetectorService {
  constructor(private readonly prisma: PrismaService) {}

  /**
   * Detects Assembly and Parliamentary boundaries for user coordinates
   */
  async detectBoundaries(latitude: number, longitude: number): Promise<DetectedBoundariesDto> {
    const query = `
      SELECT id, code, name, layer_type AS "layerType", level, ST_AsGeoJSON(geom) AS polygon
      FROM spatial_boundaries
      WHERE ST_Contains(
        geom,
        ST_SetSRID(ST_MakePoint($1, $2), 4326)
      );
    `;
    const boundaries = await this.prisma.$queryRawUnsafe<BoundaryRow[]>(query, longitude, latitude);
    return this.mapToDto(boundaries);
  }
}
```

### 2. Candidate Controller Endpoint
```typescript
@Controller('api/v1/candidates')
export class CandidateController {
  constructor(private readonly candidateService: CandidateService) {}

  @Get('constituency/:code')
  async getCandidatesByConstituency(@Param('code') code: string): Promise<Candidate[]> {
    return this.candidateService.findByConstituencyCode(code);
  }
}
```

---

## Step 3: Scaffold Angular Leaflet Map Signal Component (`civicpath-frontend`)

```typescript
@Component({
  selector: 'app-constituency-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './constituency-map.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConstituencyMapComponent {
  readonly userLocation = input.required<{ lat: number; lng: number }>();
  readonly constituencyPolygon = input<GeoJSON.Geometry | null>(null);

  // Reactive computed status for current Assembly & Parliament names
  readonly boundaryLabel = computed(() => {
    const polygon = this.constituencyPolygon();
    return polygon ? 'Constituency Active' : 'Select Location on Map';
  });
}
```

---

## Step 4: Run Verification & DataMeet Ingestion Tests

1. Run DataMeet ingestion seeder test: `pnpm run seed:datameet`.
2. Run PostGIS spatial query unit tests (`pnpm test`).
3. Verify Leaflet GeoJSON polygon rendering in browser.
