# Strategic Architecture Review V2

This document evaluates the architectural design of the Mosque Discovery & Prayer Information platform, highlighting structural strengths, weaknesses, risks, and scaling recommendations.

---

## 1. Architectural Overview & Strengths

The system uses a clean, decoupled layout with a Django/DRF backend and a Next.js frontend.

* **Domain Isolation**: Code is separated into self-contained applications under `backend/apps/`. This structure prevents cross-domain pollution.
* **ORM Performance**: The database queries are N+1 clean. By using `select_related()` and `prefetch_related()`, Mosque listing queries are limited to **4 database operations**.
* **Engine Separation**: The `MosqueAvailabilityEngine` encapsulates timezone calculations, status checks, and congregation rollovers, separating calculation engines from API views.
* **Tenant Security**: Cross-mosque security is enforced at the controller layer via custom permissions, ensuring database isolation.

---

## 2. Identified Weaknesses

* **Database Normalization Deficit**: `Mosque.city` is mapped as a `CharField` instead of a `ForeignKey` to the `City` model. This compromises referential integrity and prevents relational queries.
* **Synchronous Web Requests**: Google Maps redirects are resolved synchronously within Django save transactions, making database saves vulnerable to network latency.
* **Lack of API Pagination**: The `/api/v1/mosques/` endpoint returns all matching active mosques in a single payload. If thousands of mosques exist within a filtered viewport, payload sizes will expand.
* **Lack of Marker Clustering**: The Leaflet map renders every mosque pin in the DOM. High marker densities will cause browser rendering lags.

---

## 3. Risk Assessment

| Risk Domain | Risk / Scaling Bottleneck | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Database Design** | Text city field values can drift (spelling mistakes, trailing spaces), failing to match `City` timezone rows. | High | Normalization of `Mosque` to `City` via a ForeignKey relationship (Phase 7). |
| **API Design** | Return of un-paginated mosque listings in viewport searches. | Medium | Enforce pagination (limit/offset) on listing endpoints, returning counts and page links. |
| **Frontend Map** | DOM performance lag when rendering thousands of vector pins in Leaflet. | Medium | Integrate `react-leaflet-markercluster` on the client to cluster near markers. |
| **Deployment** | Synchronous Google redirect parser can exhaust Django application worker threads under high load. | Medium | Move URL resolution tasks to Celery task queues. |

---

## 4. Architectural Recommendations

1. **Phase 7 Normalize City Mapping (High Priority)**: Refactor `Mosque.city` into a relational model mapping to `City`.
2. **Implement API Pagination (Medium Priority)**: Introduce query pagination on public list endpoints.
3. **Integrate Background Task Queues (Medium Priority)**: Install Celery or django-q to handle redirect resolution and calendar imports.
4. **Setup Marker Clustering on Map (Low Priority)**: Use React Marker Cluster to group high densities of map pins.
5. **PostgreSQL GIS Extensions (Low Priority)**: For massive datasets, migrate float coordinates to PostGIS geometry columns to use native spatial index range operations.
