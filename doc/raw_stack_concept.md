# Understanding STAC Objects (SpatioTemporal Asset Catalog)
To handle modern geospatiaal data, GeoSync-ETL uses the STAC (SpationTemporal Asset Catalog) standard. Here is the raw detail
of the objects handled by our `StacIngestor`

## 1. Item Collection
This is the result of a search. It is an object grouping several satellite captures.
* Standard: Based on the GeoJSON FeatureCollection format.
* Fole: Serves as an index for serch results.

## 2. STAC item (The Base Unit)
**Item Composition**
|Component |Description      |Utility for GeoSync-ETL    |
| -------- | --------------- | ------------------------- |
| ID       | Unique ID       | Unique database reference |
| Geometry | GeoJSON polygon | Footprint on the ground   |
| Assets   | URL Dictionary  | Access to actua image     |

## 3. The Assets (The 'Treasure')
* `thumbnail`: Low-resolution image.
* `B04` (Red): Red frequency band.
* `B08` (NIR): Near-infrared band.
Technical Note: We use pystac-client to handle these objects (e.g., item.assets['thumbnail'].href)