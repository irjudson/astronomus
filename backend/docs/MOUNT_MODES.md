# Seestar S50 Mount Modes

## Overview

The Seestar S50 operates in two coordinate system modes:

1. **Alt/Az Mode** (Default) - Altitude/Azimuth coordinates
2. **Equatorial Mode** - Right Ascension/Declination coordinates (requires initialization)

## Alt/Az Mode (Default)

**Characteristics:**
- No initialization required
- Uses horizon coordinates (Azimuth, Altitude)
- Telescope points to fixed Alt/Az position
- Simple but target coordinates change over time due to Earth's rotation

**Usage:**
```python
client = SeestarClient()
await client.connect("192.168.2.47", 4700)

# goto_target automatically converts RA/Dec to Alt/Az
await client.goto_target(ra_hours=18.615, dec_degrees=38.783, target_name="Vega")
```

**How it works:**
1. Client converts RA/Dec to current Alt/Az coordinates
2. Sends `scope_move_to_horizon(az, alt)` command
3. Telescope moves to that horizon position
4. Good for quick slews, but target drifts over time

## Equatorial Mode (Requires Initialization)

**Characteristics:**
- Requires mount homing/initialization sequence
- Uses celestial coordinates (RA, Dec)
- Telescope tracks objects as Earth rotates
- More complex but better for long-term tracking

**Initialization Sequence:**
```python
client = SeestarClient()
await client.connect("192.168.2.47", 4700)

# Initialize equatorial mode (runs go_home sequence)
await client.initialize_equatorial_mode()

# Set mode to equatorial
await client.set_mount_mode(MountMode.EQUATORIAL)

# Now goto_target will use iscope_start_view with RA/Dec directly
await client.goto_target(ra_hours=18.615, dec_degrees=38.783, target_name="Vega")
```

**How it works:**
1. `mount_go_home` establishes reference point
2. Mount knows its orientation in RA/Dec space
3. `iscope_start_view` command handles continuous tracking
4. Telescope automatically compensates for Earth's rotation

## Choosing the Right Mode

### Use Alt/Az Mode when:
- Quick observations or testing
- Moving between targets frequently
- Don't need precise long-term tracking
- Want simplest setup

### Use Equatorial Mode when:
- Long exposure imaging
- Precise tracking required
- Following object over extended period
- Using official Seestar app behavior

## API Reference

### MountMode Enum
```python
class MountMode(Enum):
    ALTAZ = "altaz"              # Default mode
    EQUATORIAL = "equatorial"     # Initialized mode
    UNKNOWN = "unknown"
```

### Status Fields
```python
client.status.mount_mode              # Current mode (MountMode enum)
client.status.equatorial_initialized  # True if equatorial init complete
```

### Methods

**initialize_equatorial_mode()**
- Runs mount homing sequence (`mount_go_home`)
- Takes 30-60 seconds
- Sets `equatorial_initialized = True`
- Required before using equatorial mode

**set_mount_mode(mode: MountMode)**
- Switches between Alt/Az and Equatorial modes
- Validates equatorial mode is initialized
- Updates `status.mount_mode`

**goto_target(ra, dec, target_name)**
- Automatically uses correct method based on `status.mount_mode`
- Alt/Az: Converts coordinates → `move_to_horizon`
- Equatorial: Uses `iscope_start_view` directly

## Error Codes

**Error 207: "fail to operate"**
- Means mount not ready for equatorial operations
- Solutions:
  1. Use Alt/Az mode (default)
  2. Or run `initialize_equatorial_mode()` first

## Implementation Notes

### Why Two Modes?

The Seestar S50 is an alt/az mount that can simulate equatorial tracking:
- **Physically**: Mount moves in altitude and azimuth axes
- **Logically**: Firmware can track using RA/Dec coordinates
- **Requirement**: Must establish reference point first (go_home)

### Official App Behavior

The official Seestar app uses `iscope_start_view` with RA/Dec coordinates, implying it initializes the mount properly on startup.

### Future Enhancements

- Auto-detect mount mode on connection
- Persist initialization state
- Alignment using known stars
- Plate solving for precise pointing
