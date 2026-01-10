# Seestar S50 View Plan Configuration

Complete documentation for the `plan_config` object used in automated observation plans.

## Overview

View Plans are Seestar's built-in automation system for executing multi-target imaging sequences. A plan consists of a list of targets to observe, each with scheduling, imaging settings, and optional mosaic configuration.

## Top-Level Structure

```json
{
  "plan_name": "M Objects Session",
  "list": [/* array of PlanTarget objects */],
  "update_time_seestar": "2025-01-09T12:00:00Z"
}
```

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_name` | string | Optional | Human-readable name for the plan |
| `list` | array | Required | Array of PlanTarget objects (see below) |
| `update_time_seestar` | string | Required | ISO 8601 timestamp when plan was last updated |

---

## PlanTarget Object

Each target in the plan represents a single deep-sky object to image.

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `target_name` | string | Official designation or catalog name | `"M31"`, `"NGC 7000"` |
| `target_ra_dec` | array[double] | RA and Dec coordinates in decimal degrees | `[10.684, 41.269]` |
| `target_id` | long | Unique identifier for this target | `1234567890` |
| `duration_min` | integer | Total imaging duration in minutes | `60` |
| `stack_total_sec` | number | Total stacking time in seconds | `3600` |

### Optional Fields

| Field | Type | Default | Description | Valid Values |
|-------|------|---------|-------------|--------------|
| `alias_name` | string | null | Common or alternate name | `"Andromeda Galaxy"` |
| `lp_filter` | boolean | null | Use light pollution filter | `true`, `false` |
| `start_min` | integer | null | Start time offset in minutes from plan start | `0` to `1440` |
| `state` | string | null | Current execution state | See states below |
| `error` | string | null | Error message if target failed | Any string |
| `code` | integer | null | Status/error code | See codes below |
| `output_file` | object | null | Output file configuration | See PlanOutputFile below |
| `mosaic` | object | null | Mosaic imaging configuration | See PlanMosaic below |

### RA/Dec Format

The `target_ra_dec` array contains two doubles:
- **Index 0**: Right Ascension in decimal degrees (0-360)
- **Index 1**: Declination in decimal degrees (-90 to +90)

**Example conversions**:
- M31 at RA 00h 42m 44s, Dec +41° 16' 9" → `[10.684, 41.269]`
- M42 at RA 05h 35m 17s, Dec -05° 23' 28" → `[83.822, -5.391]`

### Target States

Valid values for the `state` field:

| State | Description |
|-------|-------------|
| `"idle"` | Target not yet started |
| `"slewing"` | Telescope slewing to target |
| `"focusing"` | Auto-focus in progress |
| `"imaging"` | Actively imaging/stacking |
| `"complete"` | Target successfully completed |
| `"error"` | Target failed with error |
| `"skipped"` | Target skipped (out of time window, etc.) |
| `"paused"` | Imaging paused |

### Status Codes

Common values for the `code` field:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `100` | In progress |
| `200` | Target below horizon |
| `201` | Target obstructed |
| `202` | Weather conditions poor |
| `203` | Device busy |
| `300` | Focus failed |
| `301` | Goto failed |
| `400` | User canceled |
| `500` | Unknown error |

---

## PlanOutputFile Object

Configures where and how target images are saved.

```json
{
  "path": "/sdcard/seestar/captures/M31",
  "files": [
    {
      "filename": "M31_stack.fit",
      "format": "FITS",
      "created_at": "2025-01-09T13:45:00Z"
    }
  ]
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Output directory path on telescope |
| `files` | array | List of PlanFile objects (metadata for saved files) |

### PlanFile Object

| Field | Type | Description |
|-------|------|-------------|
| `filename` | string | Output filename |
| `format` | string | File format: `"FITS"`, `"JPEG"`, `"PNG"` |
| `created_at` | string | ISO 8601 timestamp when file was created |

---

## PlanMosaic Object

Configures mosaic imaging mode for wide-field targets.

```json
{
  "scale": 1.5,
  "angle": 45.0,
  "star_map_angle": 0.0
}
```

### Fields

| Field | Type | Description | Valid Range |
|-------|------|-------------|-------------|
| `scale` | double | Mosaic scale factor | `0.5` to `3.0` (1.0 = 100%) |
| `angle` | double | Rotation angle in degrees | `0.0` to `360.0` |
| `star_map_angle` | double | Star map alignment angle in degrees | `0.0` to `360.0` |

---

## Complete Example

Here's a complete 3-target view plan:

```json
{
  "plan_name": "Autumn Galaxies",
  "update_time_seestar": "2025-01-09T20:00:00Z",
  "list": [
    {
      "target_id": 1001,
      "target_name": "M31",
      "target_ra_dec": [10.684, 41.269],
      "alias_name": "Andromeda Galaxy",
      "lp_filter": true,
      "start_min": 0,
      "duration_min": 90,
      "stack_total_sec": 5400,
      "state": "idle",
      "code": null,
      "error": null,
      "mosaic": {
        "scale": 1.5,
        "angle": 0.0,
        "star_map_angle": 0.0
      },
      "output_file": {
        "path": "/sdcard/seestar/M31",
        "files": []
      }
    },
    {
      "target_id": 1002,
      "target_name": "M33",
      "target_ra_dec": [23.462, 30.660],
      "alias_name": "Triangulum Galaxy",
      "lp_filter": true,
      "start_min": 90,
      "duration_min": 60,
      "stack_total_sec": 3600,
      "state": "idle",
      "code": null,
      "error": null,
      "output_file": {
        "path": "/sdcard/seestar/M33",
        "files": []
      }
    },
    {
      "target_id": 1003,
      "target_name": "NGC 7000",
      "target_ra_dec": [312.944, 44.515],
      "alias_name": "North America Nebula",
      "lp_filter": false,
      "start_min": 150,
      "duration_min": 120,
      "stack_total_sec": 7200,
      "state": "idle",
      "code": null,
      "error": null,
      "mosaic": {
        "scale": 2.0,
        "angle": 90.0,
        "star_map_angle": 0.0
      },
      "output_file": {
        "path": "/sdcard/seestar/NGC7000",
        "files": []
      }
    }
  ]
}
```

---

## Minimal Example

Minimum required fields for a single-target plan:

```json
{
  "update_time_seestar": "2025-01-09T20:00:00Z",
  "list": [
    {
      "target_id": 1001,
      "target_name": "M42",
      "target_ra_dec": [83.822, -5.391],
      "duration_min": 30,
      "stack_total_sec": 1800
    }
  ]
}
```

---

## Usage in API

### Start a View Plan

```bash
POST /api/telescope/plan/start
Content-Type: application/json

{
  "plan_name": "Tonight's Session",
  "update_time_seestar": "2025-01-09T20:00:00Z",
  "list": [/* targets */]
}
```

### Monitor Plan Progress

```bash
GET /api/telescope/plan/state
```

Returns:
```json
{
  "current_target": "M31",
  "current_target_index": 0,
  "total_targets": 3,
  "progress": 35.5,
  "state": "imaging",
  "elapsed_seconds": 1920,
  "estimated_remaining_seconds": 3480
}
```

### Stop Plan

```bash
POST /api/telescope/plan/stop
```

---

## Coordinate Conversion Formulas

### RA: Hours to Decimal Degrees
```
decimal_degrees = hours * 15
```

Example: RA 10h 30m 00s
```
10.5 hours × 15 = 157.5°
```

### RA: HH:MM:SS to Decimal Degrees
```
hours = HH + (MM / 60) + (SS / 3600)
decimal_degrees = hours * 15
```

### Dec: DD:MM:SS to Decimal Degrees
```
decimal_degrees = DD + (MM / 60) + (SS / 3600)
# For negative declinations, apply negative to entire value
```

---

## Best Practices

### 1. Scheduling Targets
- Order targets by altitude (highest first) for optimal image quality
- Leave 5-10 minute gaps between targets for slewing and focusing
- Total `duration_min` should account for focus time (~3-5 min per target)

### 2. Stacking Time
- `stack_total_sec` should be slightly less than `duration_min * 60`
- Example: 60 min duration → 3300-3400 sec stacking (leaves time for focus)

### 3. Light Pollution Filter
- Enable `lp_filter: true` for emission nebulae (H-alpha targets)
- Disable `lp_filter: false` for galaxies and broadband targets
- Mixed-target plans: group by filter requirements

### 4. Mosaic Imaging
- Use `scale > 1.0` for targets larger than field of view
- Test mosaic settings on bright targets first
- `angle` should match target orientation for best results

### 5. Error Handling
- Always check `state` and `code` fields when monitoring progress
- Implement retry logic for transient errors (codes 200-203)
- Log `error` field contents for troubleshooting

---

## Notes from Android App Analysis

Based on decompiled Seestar v3.0.0 Android app:

1. **Plan Storage**: Plans are stored locally and synced to telescope
2. **State Management**: Telescope updates `state` and `code` fields automatically
3. **Time Synchronization**: Telescope uses internal clock; sync time before plan execution
4. **Output Files**: Files are written incrementally during stacking
5. **Plan Interruption**: Stopping a plan mid-target preserves partial stack

---

## Related Documentation

- [Seestar API Commands](../seestar-api-commands.md) - Full command reference
- [Command to UX Mapping](../COMMAND-TO-UX-MAPPING.md) - Frontend integration guide
- [Testing Telescope](TESTING-TELESCOPE.md) - Testing strategies
