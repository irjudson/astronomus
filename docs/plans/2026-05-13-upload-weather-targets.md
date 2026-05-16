The `docs/plans/` directory does not exist. Since I cannot create files or directories (read-only mode), I will deliver the complete plan as my output. Here is the full implementation plan:

---

# Implementation Plan: Upload, Weather, Targets — 2026-05-13

## Preamble

This plan covers three independent features on branch `feature/upload-weather-targets`. Tasks are ordered to front-load the two features with no DB migrations (F2, then F1) and do the migration-bearing feature (F3) after them so a failing migration never blocks other work. Every task follows TDD: write a failing test, confirm it fails, implement, confirm it passes, commit.

All commands run inside the container: `docker exec astronomus <cmd>`.
Lint: `docker exec astronomus black --line-length=120 <file> && docker exec astronomus isort --profile=black --line-length=120 <file> && docker exec astronomus ruff check --config backend/pyproject.toml <file>`.
Test suite: `docker exec astronomus pytest tests/ -q --no-cov`.

---

## Task 0: Feature Branch Setup

**Files:** none

**Steps:**

1. Create branch:
```bash
git checkout -b feature/upload-weather-targets
```

2. Confirm base is clean:
```bash
docker exec astronomus pytest tests/ -q --no-cov
```
Expected: all pass.

3. Commit:
```bash
git commit --allow-empty -m "chore: start feature/upload-weather-targets branch"
```

---

## Task 1: DailyForecast Pydantic model

**Files:**
- Modify: `backend/app/models/models.py`

The `DailyForecast` model lives alongside `WeatherForecast` in `models.py`. No DB table — this is a pure response schema.

**Steps:**

1. Write failing test at `backend/tests/unit/test_models.py` — add a new test class:

```python
class TestDailyForecast:
    def test_daily_forecast_fields_and_score_clamp(self):
        from app.models.models import DailyForecast
        f = DailyForecast(
            date="2026-05-14",
            cloud_pct=25.0,
            temp_min=8.0,
            temp_max=18.0,
            wind_mps=3.5,
            precip_mm=0.0,
            astronomy_score=75.0,
        )
        assert f.astronomy_score == 75.0

    def test_daily_forecast_score_computation_helper(self):
        from app.models.models import DailyForecast
        f = DailyForecast(
            date="2026-05-14",
            cloud_pct=110.0,  # out-of-range input, score should clamp
            temp_min=0.0, temp_max=0.0, wind_mps=0.0, precip_mm=0.0,
            astronomy_score=-10.0,  # negative, clamp to 0
        )
        assert f.astronomy_score >= 0.0
```

2. Run test, confirm `ImportError` / `AttributeError` (red):
```bash
docker exec astronomus pytest backend/tests/unit/test_models.py::TestDailyForecast -q --no-cov
```

3. Add to `backend/app/models/models.py` after the `WeatherForecast` class:

```python
class DailyForecast(BaseModel):
    """Seven-day daily forecast entry from Open-Meteo."""

    date: str = Field(description="Date in YYYY-MM-DD format")
    cloud_pct: float = Field(ge=0, le=100, description="Mean cloud cover percentage")
    temp_min: float = Field(description="Minimum temperature in Celsius")
    temp_max: float = Field(description="Maximum temperature in Celsius")
    wind_mps: float = Field(ge=0, description="Max wind speed in m/s")
    precip_mm: float = Field(ge=0, description="Total precipitation in mm")
    astronomy_score: float = Field(ge=0, le=100, description="Astronomy suitability 0-100 (100-cloud_pct, clamped)")
```

4. Run lint, then run test (green):
```bash
docker exec astronomus pytest backend/tests/unit/test_models.py::TestDailyForecast -q --no-cov
```

5. Commit:
```bash
git add backend/app/models/models.py backend/tests/unit/test_models.py
git commit -m "feat: add DailyForecast Pydantic model for Open-Meteo multi-day weather"
```

---

## Task 2: MultiDayWeatherService

**Files:**
- Create: `backend/app/services/multi_day_weather_service.py`

**Steps:**

1. Write failing test at `backend/tests/unit/services/test_multi_day_weather_service.py`:

```python
from unittest.mock import patch, MagicMock
import pytest
from app.services.multi_day_weather_service import MultiDayWeatherService
from app.models.models import Location, DailyForecast


@pytest.fixture
def location():
    return Location(
        name="Test",
        latitude=45.92,
        longitude=-111.54,
        elevation=1234.0,
        timezone="America/Denver",
    )


OPEN_METEO_RESPONSE = {
    "daily": {
        "time": ["2026-05-14", "2026-05-15"],
        "cloud_cover_mean": [20.0, 80.0],
        "temperature_2m_max": [18.0, 15.0],
        "temperature_2m_min": [8.0, 6.0],
        "wind_speed_10m_max": [3.5, 12.0],
        "precipitation_sum": [0.0, 5.0],
        "precipitation_probability_max": [5, 70],
    }
}


class TestMultiDayWeatherService:
    def test_returns_list_of_daily_forecasts(self, location):
        svc = MultiDayWeatherService()
        mock_resp = MagicMock()
        mock_resp.json.return_value = OPEN_METEO_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_resp):
            forecasts = svc.get_forecast(location)
        assert len(forecasts) == 2
        assert all(isinstance(f, DailyForecast) for f in forecasts)

    def test_astronomy_score_is_100_minus_cloud(self, location):
        svc = MultiDayWeatherService()
        mock_resp = MagicMock()
        mock_resp.json.return_value = OPEN_METEO_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_resp):
            forecasts = svc.get_forecast(location)
        assert forecasts[0].astronomy_score == pytest.approx(80.0)
        assert forecasts[1].astronomy_score == pytest.approx(20.0)

    def test_astronomy_score_clamped_0_to_100(self, location):
        resp = {
            "daily": {
                "time": ["2026-05-14"],
                "cloud_cover_mean": [110.0],  # over 100
                "temperature_2m_max": [20.0],
                "temperature_2m_min": [5.0],
                "wind_speed_10m_max": [1.0],
                "precipitation_sum": [0.0],
                "precipitation_probability_max": [0],
            }
        }
        svc = MultiDayWeatherService()
        mock_resp = MagicMock()
        mock_resp.json.return_value = resp
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_resp):
            forecasts = svc.get_forecast(location)
        assert forecasts[0].astronomy_score == 0.0

    def test_returns_empty_on_network_error(self, location):
        import requests
        svc = MultiDayWeatherService()
        with patch("requests.get", side_effect=requests.RequestException("timeout")):
            forecasts = svc.get_forecast(location)
        assert forecasts == []
```

2. Run test, confirm failure (red):
```bash
docker exec astronomus pytest backend/tests/unit/services/test_multi_day_weather_service.py -q --no-cov
```

3. Create `backend/app/services/multi_day_weather_service.py`:

```python
"""Multi-day weather forecast service using Open-Meteo (free, no auth)."""

import logging
from typing import List

import requests

from app.models.models import DailyForecast, Location

logger = logging.getLogger(__name__)

_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_DAILY_VARS = (
    "cloud_cover_mean,temperature_2m_max,temperature_2m_min,"
    "precipitation_probability_max,wind_speed_10m_max,precipitation_sum"
)


class MultiDayWeatherService:
    """Fetch 7-day daily forecast from Open-Meteo (no API key required)."""

    def get_forecast(self, location: Location, forecast_days: int = 7) -> List[DailyForecast]:
        """Return up to *forecast_days* DailyForecast objects for *location*.

        Returns an empty list on network/parse errors so callers degrade gracefully.
        """
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "daily": _DAILY_VARS,
            "forecast_days": forecast_days,
            "timezone": "auto",
        }
        try:
            resp = requests.get(_OPEN_METEO_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("Open-Meteo request failed: %s", exc)
            return []

        try:
            daily = data["daily"]
            results: List[DailyForecast] = []
            for i, date in enumerate(daily["time"]):
                cloud_pct = float(daily["cloud_cover_mean"][i] or 0)
                score = max(0.0, min(100.0, 100.0 - cloud_pct))
                results.append(
                    DailyForecast(
                        date=date,
                        cloud_pct=min(100.0, max(0.0, cloud_pct)),
                        temp_min=float(daily["temperature_2m_min"][i] or 0),
                        temp_max=float(daily["temperature_2m_max"][i] or 0),
                        wind_mps=float(daily["wind_speed_10m_max"][i] or 0),
                        precip_mm=float(daily["precipitation_sum"][i] or 0),
                        astronomy_score=score,
                    )
                )
            return results
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Open-Meteo parse error: %s", exc)
            return []
```

4. Lint and run tests (green):
```bash
docker exec astronomus pytest backend/tests/unit/services/test_multi_day_weather_service.py -q --no-cov
```

5. Commit:
```bash
git add backend/app/services/multi_day_weather_service.py backend/tests/unit/services/test_multi_day_weather_service.py
git commit -m "feat: add MultiDayWeatherService using Open-Meteo free API"
```

---

## Task 3: GET /api/weather/multiday endpoint

**Files:**
- Modify: `backend/app/api/routes.py`

The weather endpoint belongs in `routes.py` alongside `/api/weather/astronomy` pattern already in `astronomy.py`. However, `astronomy.py` uses the `astronomy` router tag. To avoid muddying that router, add this endpoint directly to `routes.py` (which owns the main `router` object) because `/api/weather/local` and the health check already live there. Alternatively, it can be added as a standalone `/weather/multiday` route in `astronomy.py` with the `astronomy` tag. Looking at `astronomy.py` — `router = APIRouter(tags=["astronomy"])` — and it already contains `/weather/astronomy` and `/weather/local`. Add `/weather/multiday` there for consistency.

**Files:**
- Modify: `backend/app/api/astronomy.py`

**Steps:**

1. Write failing test at `backend/tests/api/test_astronomy_api.py` — add to the existing file:

```python
class TestMultiDayWeather:
    def test_multiday_weather_returns_list(self, client):
        from unittest.mock import patch
        from app.models.models import DailyForecast

        mock_forecasts = [
            DailyForecast(
                date="2026-05-14",
                cloud_pct=20.0,
                temp_min=8.0,
                temp_max=18.0,
                wind_mps=3.0,
                precip_mm=0.0,
                astronomy_score=80.0,
            )
        ]
        with patch(
            "app.api.astronomy.MultiDayWeatherService.get_forecast",
            return_value=mock_forecasts,
        ):
            resp = client.get("/api/weather/multiday")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["date"] == "2026-05-14"
        assert data[0]["astronomy_score"] == 80.0

    def test_multiday_weather_no_location_returns_422_or_empty(self, client):
        # When settings has no location, expect 200 with empty list or 503
        resp = client.get("/api/weather/multiday")
        assert resp.status_code in (200, 503)
```

2. Confirm failure (red):
```bash
docker exec astronomus pytest backend/tests/api/test_astronomy_api.py::TestMultiDayWeather -q --no-cov
```

3. Add to `backend/app/api/astronomy.py` — add import at top:

```python
from app.services.multi_day_weather_service import MultiDayWeatherService
from app.models.models import DailyForecast
```

Add endpoint after the existing `/weather/astronomy` endpoint:

```python
@router.get("/weather/multiday", response_model=List[DailyForecast])
async def get_multiday_weather(db=Depends(get_db_from_request)):
    """
    Get 7-day daily astronomy forecast from Open-Meteo (free, no key).

    Reads location from the default ObservingLocation in the database.
    Returns a list of DailyForecast (one per day, up to 7 days).
    """
    from app.database import get_db as _get_db
    from app.services.settings_service import SettingsService

    # get_db_from_request is not available here — use a local session
    # Same pattern as /sky-quality: inject db via Depends
    ...
```

Actually, reviewing `astronomy.py` more carefully: it does not use `Depends(get_db)` in existing endpoints. The `/weather/astronomy` endpoint has no DB dependency. For the multiday endpoint, the location is read from settings (DB). Inject `db` using `Depends(get_db)` on this specific endpoint:

```python
from app.database import get_db

@router.get("/weather/multiday", response_model=List[DailyForecast])
async def get_multiday_weather(db=Depends(get_db)):
    """
    Get 7-day daily astronomy forecast from Open-Meteo.

    Reads observer location from the default saved location in settings.
    Returns an empty list if no location is configured.
    """
    from app.services.settings_service import SettingsService

    settings_service = SettingsService(db)
    location = settings_service.get_location()
    if not location:
        return []

    svc = MultiDayWeatherService()
    return svc.get_forecast(location)
```

4. Add necessary imports to `astronomy.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
# ... existing ...
from app.database import get_db
from app.models.models import DailyForecast
from app.services.multi_day_weather_service import MultiDayWeatherService
```

5. Lint and run tests (green):
```bash
docker exec astronomus pytest backend/tests/api/test_astronomy_api.py::TestMultiDayWeather -q --no-cov
```

6. Commit:
```bash
git add backend/app/api/astronomy.py backend/tests/api/test_astronomy_api.py
git commit -m "feat: add GET /api/weather/multiday endpoint using Open-Meteo"
```

---

## Task 4: weather.js store — multiDayForecast state and action

**Files:**
- Modify: `frontend/vue-app/src/stores/weather.js`

**Steps:**

1. Write failing test — add to `frontend/vue-app/src/stores/__tests__/weather.test.js`:

```javascript
it('fetchMultiDayForecast populates multiDayForecast', async () => {
  const mockData = [
    { date: '2026-05-14', cloud_pct: 20, temp_min: 8, temp_max: 18, wind_mps: 3, precip_mm: 0, astronomy_score: 80 }
  ]
  axios.get.mockResolvedValue({ data: mockData })
  const store = useWeatherStore()
  await store.fetchMultiDayForecast()
  expect(store.multiDayForecast).toEqual(mockData)
})

it('fetchMultiDayForecast handles error gracefully', async () => {
  axios.get.mockRejectedValue(new Error('net error'))
  const store = useWeatherStore()
  await store.fetchMultiDayForecast()
  expect(store.multiDayForecast).toEqual([])
})
```

2. Run test (red):
```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run test -- --run 2>&1 | grep -A5 "fetchMultiDay"
```

3. Add to `frontend/vue-app/src/stores/weather.js`:

In `state()`:
```javascript
multiDayForecast: [],
```

In `actions`:
```javascript
async fetchMultiDayForecast() {
  try {
    const resp = await axios.get('/api/weather/multiday')
    this.multiDayForecast = resp.data ?? []
  } catch {
    this.multiDayForecast = []
  }
},
```

4. Run tests (green).

5. Commit:
```bash
git add frontend/vue-app/src/stores/weather.js frontend/vue-app/src/stores/__tests__/weather.test.js
git commit -m "feat: add multiDayForecast state and fetchMultiDayForecast action to weather store"
```

---

## Task 5: DailyWeatherStrip.vue component

**Files:**
- Create: `frontend/vue-app/src/components/shared/DailyWeatherStrip.vue`

**Design:** 7-column responsive strip. Each column shows: abbreviated weekday + date, cloud icon + cloud%, astronomy score badge. Color-coding: green (score ≥70, cloud ≤30%), yellow (score 40–69, cloud 31–60%), red (score <40, cloud >60%). Accepts `forecasts` prop (array of DailyForecast objects from the store).

**Steps:**

1. No automated test exists for this component — it is a pure display component. The vitest suite does not include component mount tests. Skip unit test; verify via build.

2. Create `frontend/vue-app/src/components/shared/DailyWeatherStrip.vue`:

```vue
<template>
  <div class="flex gap-1 overflow-x-auto pb-1">
    <div
      v-for="day in forecasts"
      :key="day.date"
      class="flex-1 min-w-[72px] rounded-lg p-2 text-center border"
      :class="cardClass(day)"
    >
      <div class="text-xs font-medium text-gray-400 mb-1">{{ formatDay(day.date) }}</div>
      <div class="text-xs text-gray-300 mb-1">&#x2601; {{ Math.round(day.cloud_pct) }}%</div>
      <div
        class="text-xs font-semibold px-1.5 py-0.5 rounded-full inline-block"
        :class="scoreClass(day)"
      >
        {{ Math.round(day.astronomy_score) }}
      </div>
    </div>
    <div v-if="!forecasts || forecasts.length === 0" class="text-xs text-gray-600 py-2">
      No forecast data
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  forecasts: {
    type: Array,
    default: () => [],
  },
})

function formatDay(dateStr) {
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'numeric', day: 'numeric' })
}

function scoreClass(day) {
  if (day.astronomy_score >= 70) return 'bg-green-900 text-green-300'
  if (day.astronomy_score >= 40) return 'bg-yellow-900 text-yellow-300'
  return 'bg-red-900 text-red-300'
}

function cardClass(day) {
  if (day.astronomy_score >= 70) return 'bg-gray-900 border-green-800/40'
  if (day.astronomy_score >= 40) return 'bg-gray-900 border-yellow-800/40'
  return 'bg-gray-900 border-red-800/40'
}
</script>
```

3. Build verification:
```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -5
```
Expected: no errors.

4. Commit:
```bash
git add frontend/vue-app/src/components/shared/DailyWeatherStrip.vue
git commit -m "feat: add DailyWeatherStrip component with color-coded 7-day astronomy forecast"
```

---

## Task 6: Embed DailyWeatherStrip in TonightView.vue

**Files:**
- Modify: `frontend/vue-app/src/views/TonightView.vue`

**Steps:**

1. Insert between the conditions+telescope grid and the Active Plan card. The `TonightView.vue` current structure (from line 57 onward) is: conditions+telescope grid → Active Plan card → Quick links. The strip goes between conditions grid and Active Plan card.

2. Modify `TonightView.vue`:

In `<template>`, after the closing `</div>` of the 2-col conditions+telescope grid (after line ~57), add:

```html
<!-- 7-day weather strip -->
<div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
  <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">7-Day Forecast</div>
  <DailyWeatherStrip :forecasts="weatherStore.multiDayForecast" />
</div>
```

In `<script setup>`, add import:
```javascript
import DailyWeatherStrip from '@/components/shared/DailyWeatherStrip.vue'
```

In `onMounted`, add:
```javascript
await weatherStore.fetchMultiDayForecast()
```

3. Build:
```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -5
```

4. Commit:
```bash
git add frontend/vue-app/src/views/TonightView.vue
git commit -m "feat: embed DailyWeatherStrip in TonightView between conditions and active plan"
```

---

## Task 7: UserTarget SQLAlchemy model

**Files:**
- Modify: `backend/app/models/catalog_models.py`

**Steps:**

1. Write failing test at `backend/tests/unit/test_catalog_service.py` — add:

```python
class TestUserTargetModel:
    def test_user_target_tablename(self):
        from app.models.catalog_models import UserTarget
        assert UserTarget.__tablename__ == "user_targets"

    def test_user_target_catalog_id_prefix(self):
        from app.models.catalog_models import UserTarget
        from sqlalchemy import inspect
        mapper = inspect(UserTarget)
        col_names = [c.key for c in mapper.columns]
        assert "catalog_id" in col_names
        assert "name" in col_names
        assert "ra_hours" in col_names
        assert "dec_degrees" in col_names
```

2. Confirm failure (red):
```bash
docker exec astronomus pytest backend/tests/unit/test_catalog_service.py::TestUserTargetModel -q --no-cov
```

3. Add to `backend/app/models/catalog_models.py` after the existing `ImageSourceStats` class:

```python
class UserTarget(Base):
    """User-defined custom observing targets."""

    __tablename__ = "user_targets"

    id = Column(Integer, primary_key=True, index=True)
    catalog_id = Column(String(100), unique=True, nullable=False, index=True)  # "USER:<name_slug>"
    name = Column(String(200), nullable=False)
    ra_hours = Column(Float, nullable=False)
    dec_degrees = Column(Float, nullable=False)
    magnitude = Column(Float, nullable=True)
    size_arcmin = Column(Float, nullable=True)
    object_type = Column(String(50), nullable=False, default="other")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

4. Lint and run tests (green):
```bash
docker exec astronomus pytest backend/tests/unit/test_catalog_service.py::TestUserTargetModel -q --no-cov
```

5. Commit:
```bash
git add backend/app/models/catalog_models.py backend/tests/unit/test_catalog_service.py
git commit -m "feat: add UserTarget SQLAlchemy model for custom catalog targets"
```

---

## Task 8: Alembic migration for user_targets

**Files:**
- Create: `backend/alembic/versions/<rev>_add_user_targets_table.py` (auto-generated then edited)

**Steps:**

1. Generate the migration inside the container (the container has alembic on PATH and DATABASE_URL set):

```bash
docker exec -w /app astronomus alembic revision --autogenerate -m "add_user_targets_table"
```

The generated file will appear at `backend/alembic/versions/<timestamp>_add_user_targets_table.py` inside the container (mapped to the host). Verify autogenerate produced the right `create_table` call.

2. If autogenerate is not available from `/app`, use the host path:
```bash
docker exec -w /app astronomus python -m alembic revision --autogenerate -m "add_user_targets_table"
```

3. Inspect the generated file. If autogenerate missed any columns (nullable, index), edit to match:

```python
def upgrade() -> None:
    op.create_table(
        "user_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("catalog_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("ra_hours", sa.Float(), nullable=False),
        sa.Column("dec_degrees", sa.Float(), nullable=False),
        sa.Column("magnitude", sa.Float(), nullable=True),
        sa.Column("size_arcmin", sa.Float(), nullable=True),
        sa.Column("object_type", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalog_id"),
    )
    op.create_index(op.f("ix_user_targets_catalog_id"), "user_targets", ["catalog_id"], unique=True)
    op.create_index(op.f("ix_user_targets_id"), "user_targets", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_targets_catalog_id"), table_name="user_targets")
    op.drop_index(op.f("ix_user_targets_id"), table_name="user_targets")
    op.drop_table("user_targets")
```

4. Apply migration:
```bash
docker exec -w /app astronomus alembic upgrade head
```

5. Verify table exists:
```bash
docker exec astronomus python -c "from app.models.catalog_models import UserTarget; print('OK')"
```

6. Run full test suite (should still pass — migration only adds a table):
```bash
docker exec astronomus pytest tests/ -q --no-cov
```

7. Commit:
```bash
git add backend/alembic/versions/
git commit -m "feat: alembic migration to add user_targets table"
```

---

## Task 9: CatalogService — merge UserTarget into filter_targets and get_all_targets

**Files:**
- Modify: `backend/app/services/catalog_service.py`

**Steps:**

1. Write failing tests in `backend/tests/unit/services/test_catalog_service.py` — add:

```python
class TestCatalogServiceUserTargets:
    def test_filter_targets_includes_user_targets(self, db_session):
        from app.models.catalog_models import UserTarget
        from app.services.catalog_service import CatalogService

        ut = UserTarget(
            catalog_id="USER:my_nebula",
            name="My Nebula",
            ra_hours=5.0,
            dec_degrees=10.0,
            object_type="nebula",
        )
        db_session.add(ut)
        db_session.commit()

        svc = CatalogService(db_session)
        targets = svc.filter_targets()
        ids = [t.catalog_id for t in targets]
        assert "USER:my_nebula" in ids

    def test_user_target_has_custom_catalog_name(self, db_session):
        from app.models.catalog_models import UserTarget
        from app.services.catalog_service import CatalogService

        ut = UserTarget(
            catalog_id="USER:test_galaxy",
            name="Test Galaxy",
            ra_hours=3.0,
            dec_degrees=20.0,
            object_type="galaxy",
        )
        db_session.add(ut)
        db_session.commit()

        svc = CatalogService(db_session)
        targets = svc.filter_targets()
        custom = next((t for t in targets if t.catalog_id == "USER:test_galaxy"), None)
        assert custom is not None
        assert "Custom" in (custom.description or "")
```

Note: `db_session` fixture needs to come from conftest. The existing `override_get_db` fixture yields a `db` session. Add a `db_session` alias or use `override_get_db`. Since the unit tests in `services/test_catalog_service.py` use a different fixture pattern, check the existing file first.

Looking at `backend/tests/unit/services/test_catalog_service.py`, it likely uses `temp_db`. Adapt the test fixture to match what already exists there. The exact fixture name to use depends on what the existing file declares. The safe approach is to use `override_get_db` from conftest (which has the PostgreSQL test DB):

```python
def test_filter_targets_includes_user_targets(self, override_get_db):
    db = override_get_db
    ...
```

2. Confirm failure (red).

3. Add `_user_target_to_dso_target` method and modify `filter_targets` and `get_all_targets` in `catalog_service.py`:

Add method after `_db_row_to_target`:

```python
def _user_target_to_dso_target(self, ut) -> DSOTarget:
    """Convert UserTarget ORM row to DSOTarget Pydantic model."""
    from app.models.catalog_models import UserTarget as _UT  # noqa: F401

    mag = ut.magnitude if ut.magnitude is not None else 99.0
    size = ut.size_arcmin if ut.size_arcmin is not None else 1.0
    notes_str = f" — {ut.notes}" if ut.notes else ""
    description = f"Custom target{notes_str}"
    sanitized = ut.catalog_id.replace(" ", "_").replace("/", "_").replace(":", "_")
    return DSOTarget(
        name=ut.name,
        catalog_id=ut.catalog_id,
        object_type=ut.object_type or "other",
        ra_hours=ut.ra_hours,
        dec_degrees=ut.dec_degrees,
        magnitude=mag,
        size_arcmin=size,
        description=description,
        image_url=f"/api/images/targets/{sanitized}",
    )
```

Modify `filter_targets` — after building `dso_objects` list, append user targets:

```python
    dso_objects = query.all()
    base_targets = [self._db_row_to_target(dso) for dso in dso_objects]

    # Merge user-defined custom targets
    from app.models.catalog_models import UserTarget
    user_query = self.db.query(UserTarget)
    if object_types and len(object_types) > 0:
        user_query = user_query.filter(UserTarget.object_type.in_(object_types))
    user_targets = [self._user_target_to_dso_target(ut) for ut in user_query.all()]

    return base_targets + user_targets
```

Similarly modify `get_all_targets` to append user targets.

4. Lint and run tests (green).

5. Commit:
```bash
git add backend/app/services/catalog_service.py backend/tests/unit/services/test_catalog_service.py
git commit -m "feat: merge UserTarget rows into CatalogService.filter_targets and get_all_targets"
```

---

## Task 10: Custom targets API router

**Files:**
- Create: `backend/app/api/custom_targets.py`
- Modify: `backend/app/api/routes.py`

**Steps:**

1. Write failing tests at `backend/tests/api/test_custom_targets_api.py`:

```python
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


class TestCustomTargetsAPI:
    def test_list_custom_targets_empty(self, client):
        resp = client.get("/api/targets/custom")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_custom_target(self, client, override_get_db):
        payload = {
            "name": "My Nebula",
            "ra_hours": 5.0,
            "dec_degrees": 10.0,
            "object_type": "nebula",
        }
        resp = client.post("/api/targets/custom", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Nebula"
        assert data["catalog_id"].startswith("USER:")

    def test_create_custom_target_duplicate_slug_returns_400(self, client, override_get_db):
        payload = {"name": "My Nebula", "ra_hours": 5.0, "dec_degrees": 10.0, "object_type": "nebula"}
        client.post("/api/targets/custom", json=payload)
        resp = client.post("/api/targets/custom", json=payload)
        assert resp.status_code == 400

    def test_update_custom_target(self, client, override_get_db):
        payload = {"name": "Test Star", "ra_hours": 1.0, "dec_degrees": 45.0, "object_type": "other"}
        create_resp = client.post("/api/targets/custom", json=payload)
        tid = create_resp.json()["id"]
        update_resp = client.put(f"/api/targets/custom/{tid}", json={**payload, "notes": "updated"})
        assert update_resp.status_code == 200
        assert update_resp.json()["notes"] == "updated"

    def test_delete_custom_target(self, client, override_get_db):
        payload = {"name": "Delete Me", "ra_hours": 2.0, "dec_degrees": 30.0, "object_type": "galaxy"}
        create_resp = client.post("/api/targets/custom", json=payload)
        tid = create_resp.json()["id"]
        del_resp = client.delete(f"/api/targets/custom/{tid}")
        assert del_resp.status_code == 200
        list_resp = client.get("/api/targets/custom")
        ids = [t["id"] for t in list_resp.json()]
        assert tid not in ids
```

2. Confirm failure (red).

3. Create `backend/app/api/custom_targets.py`:

```python
"""API endpoints for user-defined custom catalog targets."""

import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.catalog_models import UserTarget

router = APIRouter(prefix="/targets/custom", tags=["custom-targets"])


def _name_to_slug(name: str) -> str:
    """Convert a display name to a URL-safe slug for catalog_id."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")
    return f"USER:{slug}"


class CustomTargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    ra_hours: float = Field(ge=0, lt=24)
    dec_degrees: float = Field(ge=-90, le=90)
    magnitude: Optional[float] = None
    size_arcmin: Optional[float] = None
    object_type: str = Field(default="other", max_length=50)
    notes: Optional[str] = None


class CustomTargetOut(BaseModel):
    id: int
    catalog_id: str
    name: str
    ra_hours: float
    dec_degrees: float
    magnitude: Optional[float]
    size_arcmin: Optional[float]
    object_type: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CustomTargetOut])
async def list_custom_targets(db: Session = Depends(get_db)):
    """List all user-defined custom targets."""
    return db.query(UserTarget).order_by(UserTarget.created_at.desc()).all()


@router.post("/", response_model=CustomTargetOut, status_code=201)
async def create_custom_target(payload: CustomTargetCreate, db: Session = Depends(get_db)):
    """Create a new custom target. Generates catalog_id as 'USER:<name_slug>'."""
    catalog_id = _name_to_slug(payload.name)
    existing = db.query(UserTarget).filter(UserTarget.catalog_id == catalog_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"A target with catalog_id '{catalog_id}' already exists.")
    ut = UserTarget(
        catalog_id=catalog_id,
        name=payload.name,
        ra_hours=payload.ra_hours,
        dec_degrees=payload.dec_degrees,
        magnitude=payload.magnitude,
        size_arcmin=payload.size_arcmin,
        object_type=payload.object_type,
        notes=payload.notes,
    )
    db.add(ut)
    db.commit()
    db.refresh(ut)
    return ut


@router.put("/{target_id}", response_model=CustomTargetOut)
async def update_custom_target(target_id: int, payload: CustomTargetCreate, db: Session = Depends(get_db)):
    """Update a custom target."""
    ut = db.query(UserTarget).filter(UserTarget.id == target_id).first()
    if not ut:
        raise HTTPException(status_code=404, detail=f"Custom target {target_id} not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ut, field, value)
    db.commit()
    db.refresh(ut)
    return ut


@router.delete("/{target_id}")
async def delete_custom_target(target_id: int, db: Session = Depends(get_db)):
    """Delete a custom target."""
    ut = db.query(UserTarget).filter(UserTarget.id == target_id).first()
    if not ut:
        raise HTTPException(status_code=404, detail=f"Custom target {target_id} not found.")
    db.delete(ut)
    db.commit()
    return {"message": f"Custom target {target_id} deleted."}
```

4. Register in `backend/app/api/routes.py` — add after the existing imports and `router.include_router` calls:

```python
from app.api.custom_targets import router as custom_targets_router

router.include_router(custom_targets_router)
```

5. Lint and run tests (green):
```bash
docker exec astronomus pytest backend/tests/api/test_custom_targets_api.py -q --no-cov
```

6. Commit:
```bash
git add backend/app/api/custom_targets.py backend/app/api/routes.py backend/tests/api/test_custom_targets_api.py
git commit -m "feat: add custom targets CRUD API at /api/targets/custom"
```

---

## Task 11: CustomTargetsPanel.vue and My Targets tab in DiscoveryView

**Files:**
- Create: `frontend/vue-app/src/components/discovery/CustomTargetsPanel.vue`
- Modify: `frontend/vue-app/src/views/DiscoveryView.vue`

**Steps:**

1. No automated frontend unit test for this component. Verify via build.

2. Create `frontend/vue-app/src/components/discovery/CustomTargetsPanel.vue`:

```vue
<template>
  <div class="flex flex-col h-full p-4 gap-4 overflow-y-auto">
    <!-- Add form -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Add Custom Target</div>
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div class="col-span-2">
          <label class="text-xs text-gray-400">Name *</label>
          <input v-model="form.name" class="input-dark w-full mt-1" placeholder="My Nebula" />
        </div>
        <div>
          <label class="text-xs text-gray-400">RA (hours) *</label>
          <input v-model.number="form.ra_hours" type="number" step="0.001" min="0" max="23.999" class="input-dark w-full mt-1" />
        </div>
        <div>
          <label class="text-xs text-gray-400">Dec (degrees) *</label>
          <input v-model.number="form.dec_degrees" type="number" step="0.01" min="-90" max="90" class="input-dark w-full mt-1" />
        </div>
        <div>
          <label class="text-xs text-gray-400">Type</label>
          <select v-model="form.object_type" class="input-dark w-full mt-1">
            <option value="galaxy">Galaxy</option>
            <option value="nebula">Nebula</option>
            <option value="cluster">Cluster</option>
            <option value="planetary_nebula">Planetary Nebula</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-gray-400">Magnitude (optional)</label>
          <input v-model.number="form.magnitude" type="number" step="0.1" class="input-dark w-full mt-1" placeholder="e.g. 9.5" />
        </div>
        <div class="col-span-2">
          <label class="text-xs text-gray-400">Notes (optional)</label>
          <input v-model="form.notes" class="input-dark w-full mt-1" placeholder="Observing notes..." />
        </div>
      </div>
      <button
        @click="addTarget"
        :disabled="!form.name || form.ra_hours == null || form.dec_degrees == null || saving"
        class="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
      >
        {{ saving ? 'Saving...' : 'Add Target' }}
      </button>
      <span v-if="addError" class="ml-3 text-xs text-red-400">{{ addError }}</span>
    </div>

    <!-- Target list -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
        My Targets ({{ targets.length }})
      </div>
      <div v-if="loading" class="text-xs text-gray-500">Loading...</div>
      <div v-else-if="targets.length === 0" class="text-xs text-gray-600">No custom targets yet.</div>
      <div v-else class="space-y-2">
        <div
          v-for="t in targets"
          :key="t.id"
          class="flex items-start justify-between gap-3 p-2 rounded-lg bg-gray-800/50"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-200">{{ t.name }}</span>
              <span class="text-xs px-1.5 py-0.5 rounded bg-purple-900 text-purple-300">Custom</span>
              <span class="text-xs text-gray-500">{{ t.object_type }}</span>
            </div>
            <div class="text-xs text-gray-500 mt-0.5">
              RA {{ t.ra_hours?.toFixed(3) }}h · Dec {{ t.dec_degrees?.toFixed(2) }}°
              <span v-if="t.magnitude != null"> · mag {{ t.magnitude }}</span>
            </div>
            <div v-if="t.notes" class="text-xs text-gray-600 mt-0.5 truncate">{{ t.notes }}</div>
          </div>
          <button
            @click="deleteTarget(t.id)"
            class="flex-shrink-0 text-xs text-red-500 hover:text-red-400 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const targets = ref([])
const loading = ref(false)
const saving = ref(false)
const addError = ref(null)

const form = ref({
  name: '',
  ra_hours: null,
  dec_degrees: null,
  object_type: 'other',
  magnitude: null,
  notes: '',
})

async function fetchTargets() {
  loading.value = true
  try {
    const resp = await axios.get('/api/targets/custom')
    targets.value = resp.data
  } catch {
    targets.value = []
  } finally {
    loading.value = false
  }
}

async function addTarget() {
  addError.value = null
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      ra_hours: form.value.ra_hours,
      dec_degrees: form.value.dec_degrees,
      object_type: form.value.object_type || 'other',
      magnitude: form.value.magnitude || null,
      notes: form.value.notes || null,
    }
    const resp = await axios.post('/api/targets/custom', payload)
    targets.value.unshift(resp.data)
    form.value = { name: '', ra_hours: null, dec_degrees: null, object_type: 'other', magnitude: null, notes: '' }
  } catch (err) {
    addError.value = err.response?.data?.detail || 'Failed to add target'
  } finally {
    saving.value = false
  }
}

async function deleteTarget(id) {
  try {
    await axios.delete(`/api/targets/custom/${id}`)
    targets.value = targets.value.filter(t => t.id !== id)
  } catch (err) {
    console.error('Delete failed:', err)
  }
}

onMounted(fetchTargets)
</script>

<style scoped>
.input-dark {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  color: #e5e7eb;
  padding: 0.375rem 0.5rem;
  font-size: 0.75rem;
  outline: none;
}
.input-dark:focus {
  border-color: #3b82f6;
}
</style>
```

3. Modify `DiscoveryView.vue` to add the 4th "My Targets" tab:

In `<template>`, add after the Satellites button:
```html
<button
  @click="activeDiscoveryTab = 'my-targets'"
  :class="[
    'px-4 py-1.5 rounded-t text-sm font-medium transition-colors',
    activeDiscoveryTab === 'my-targets'
      ? 'bg-blue-600 text-white'
      : 'bg-gray-800 text-gray-400 hover:text-gray-200'
  ]"
>
  My Targets
</button>
```

In the content section, add:
```html
<CustomTargetsPanel v-else-if="activeDiscoveryTab === 'my-targets'" />
```

Update the header subtitle:
```html
<p v-else-if="activeDiscoveryTab === 'my-targets'" class="text-sm text-gray-500">
  Your custom catalog targets
</p>
```

In `<script setup>`, add:
```javascript
import CustomTargetsPanel from '@/components/discovery/CustomTargetsPanel.vue'
```

4. Build:
```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -5
```

5. Commit:
```bash
git add frontend/vue-app/src/components/discovery/CustomTargetsPanel.vue frontend/vue-app/src/views/DiscoveryView.vue
git commit -m "feat: add My Targets tab to DiscoveryView with CustomTargetsPanel for user-defined targets"
```

---

## Task 12: Probe Seestar plan format (discovery spike)

**Files:**
- No production files changed in this task.

The exact JSON format for `set_plan` is unknown. The seestar-api library is bind-mounted at `/opt/seestar-api` inside the container. This task discovers the correct call signature before writing production code.

**Steps:**

1. Inspect the seestar-api library:
```bash
docker exec astronomus find /opt/seestar-api -name "*.py" | xargs grep -l "set_plan\|import_plan\|list_plan" 2>/dev/null
```

2. Read the relevant source:
```bash
docker exec astronomus grep -n "set_plan\|import_plan\|list_plan\|get_plan\|delete_plan" /opt/seestar-api/seestar/api/plans.py 2>/dev/null || docker exec astronomus grep -rn "def set_plan\|def import_plan" /opt/seestar-api/ 2>/dev/null | head -20
```

3. Based on CRITICAL-API-FINDINGS.md and docs/seestar-protocol-spec.md, check if plan format is documented:
```bash
grep -n "set_plan\|import_plan\|plan.*format\|probe" /home/irjudson/Projects/astronomus/docs/seestar-protocol-spec.md 2>/dev/null | head -30
grep -n "plan" /home/irjudson/Projects/astronomus/docs/CRITICAL-API-FINDINGS.md 2>/dev/null | head -20
```

4. Try the documented format against a live telescope connection (only if telescope is connected during development — safe to skip in CI). The format to try first per the spec:

```json
{
  "name": "TestPlan",
  "targets": [
    {
      "name": "M31",
      "ra": 0.712,
      "dec": 41.269,
      "lp_filter": false,
      "gain": 80,
      "exp_time": 10,
      "count": 180
    }
  ]
}
```

The plan must also include a "probe" step. Check `docs/seestar/VIEW-PLAN-CONFIGURATION.md` for the probe step format.

5. Document findings in a code comment at the top of the new endpoint file (see Task 13).

---

## Task 13: Plan upload backend endpoints

**Files:**
- Modify: `backend/app/api/telescope_features.py`

The three new endpoints live alongside existing telescope feature endpoints in `telescope_features.py`. They follow the established `_ok()` + `Depends(get_current_telescope)` pattern.

**Steps:**

1. Write failing tests at `backend/tests/api/test_telescope_features_plan.py`:

```python
from unittest.mock import AsyncMock, Mock, patch
import pytest
from fastapi.testclient import TestClient
from app.api import telescope
from app.clients.seestar_client import SeestarClient
from app.main import app


@pytest.fixture
def test_client_with_scope(mock_scope):
    old = telescope.seestar_client
    telescope.seestar_client = mock_scope
    yield TestClient(app)
    telescope.seestar_client = old


@pytest.fixture
def test_client_no_scope():
    old = telescope.seestar_client
    telescope.seestar_client = None
    yield TestClient(app)
    telescope.seestar_client = old


@pytest.fixture
def mock_scope():
    c = Mock(spec=SeestarClient)
    c.connected = True
    c.list_plan = AsyncMock(return_value=[{"name": "2026-05-14-plan"}])
    c.set_plan = AsyncMock(return_value=True)
    c.delete_plan = AsyncMock(return_value=True)
    return c


class TestPlanUploadEndpoints:
    def test_list_plans_on_scope(self, test_client_with_scope):
        resp = test_client_with_scope.get("/api/telescope/features/plan/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "plans" in data

    def test_list_plans_no_telescope(self, test_client_no_scope):
        resp = test_client_no_scope.get("/api/telescope/features/plan/list")
        assert resp.status_code == 503

    def test_upload_plan_no_telescope(self, test_client_no_scope):
        resp = test_client_no_scope.post("/api/telescope/features/plan/upload", json={"plan_id": 1})
        assert resp.status_code == 503

    def test_upload_plan_not_found(self, test_client_with_scope, override_get_db):
        resp = test_client_with_scope.post("/api/telescope/features/plan/upload", json={"plan_id": 99999})
        assert resp.status_code == 404

    def test_delete_plan_on_scope(self, test_client_with_scope):
        resp = test_client_with_scope.delete("/api/telescope/features/plan/TestPlan")
        assert resp.status_code == 200

    def test_upload_plan_success(self, test_client_with_scope, override_get_db):
        # First create a saved plan in the DB
        from app.models.plan_models import SavedPlan
        import json
        minimal_plan = {
            "session": {
                "observing_date": "2026-05-14",
                "sunset": "2026-05-14T21:00:00",
                "civil_twilight_end": "2026-05-14T21:30:00",
                "nautical_twilight_end": "2026-05-14T22:00:00",
                "astronomical_twilight_end": "2026-05-14T22:30:00",
                "astronomical_twilight_start": "2026-05-15T04:30:00",
                "nautical_twilight_start": "2026-05-15T05:00:00",
                "civil_twilight_start": "2026-05-15T05:30:00",
                "sunrise": "2026-05-15T06:00:00",
                "imaging_start": "2026-05-14T22:45:00",
                "imaging_end": "2026-05-15T04:15:00",
                "total_imaging_minutes": 330,
            },
            "location": {"name": "Test", "latitude": 45.9, "longitude": -111.5, "elevation": 1234.0, "timezone": "America/Denver"},
            "scheduled_targets": [
                {
                    "target": {"name": "M31", "catalog_id": "M31", "ra_hours": 0.712, "dec_degrees": 41.27, "object_type": "galaxy", "magnitude": 3.4, "size_arcmin": 190.0},
                    "start_time": "2026-05-14T22:45:00",
                    "end_time": "2026-05-15T00:45:00",
                    "duration_minutes": 120,
                    "start_altitude": 50.0, "end_altitude": 55.0,
                    "start_azimuth": 90.0, "end_azimuth": 95.0,
                    "field_rotation_rate": 0.1,
                    "recommended_exposure": 10,
                    "recommended_frames": 720,
                    "score": {"visibility_score": 0.8, "weather_score": 0.9, "object_score": 0.85, "total_score": 0.85},
                }
            ],
            "weather_forecast": [],
            "total_targets": 1,
            "coverage_percent": 85.0,
        }
        sp = SavedPlan(
            name="Test Upload Plan",
            observing_date="2026-05-14",
            location_name="Test",
            plan_data=minimal_plan,
        )
        override_get_db.add(sp)
        override_get_db.commit()
        override_get_db.refresh(sp)

        resp = test_client_with_scope.post(
            "/api/telescope/features/plan/upload",
            json={"plan_id": sp.id},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
```

2. Confirm failure (red):
```bash
docker exec astronomus pytest backend/tests/api/test_telescope_features_plan.py -q --no-cov
```

3. Add request model and three endpoints to `backend/app/api/telescope_features.py`:

Add import near the top of `telescope_features.py`:
```python
from app.database import get_db
from app.models.plan_models import SavedPlan
from app.models import ObservingPlan
from sqlalchemy.orm import Session
```

Add request model after `LocationRequest`:
```python
class PlanUploadRequest(BaseModel):
    """Request to upload a saved plan to the telescope."""
    plan_id: int = Field(description="Database ID of the SavedPlan to upload")
```

Add conversion helper function before the endpoints (not in a class):
```python
def _plan_to_seestar_format(plan: ObservingPlan) -> dict:
    """Convert an ObservingPlan to the Seestar set_plan wire format.

    Format determined from seestar-api library inspection and docs/seestar/VIEW-PLAN-CONFIGURATION.md.
    Each target becomes one plan entry. The probe step is prepended automatically.

    NOTE: If set_plan fails with this format, try import_plan with the same payload.
    Update this function once the exact wire format is confirmed against the hardware.
    """
    targets = []
    for st in plan.scheduled_targets:
        t = st.target
        targets.append(
            {
                "name": t.name,
                "ra": t.ra_hours,
                "dec": t.dec_degrees,
                "lp_filter": False,
                "gain": 80,
                "exp_time": 10,
                "count": st.recommended_frames,
            }
        )
    plan_name = plan.session.observing_date + "-plan"
    return {
        "name": plan_name,
        "targets": targets,
    }
```

Add three endpoints at the end of the `# PLAN MANAGEMENT` section (create a new section):

```python
# ==========================================
# PLAN MANAGEMENT
# ==========================================


@router.get("/plan/list")
async def list_plans_on_telescope(telescope: SeestarClient = Depends(get_current_telescope)) -> Dict[str, Any]:
    """List observation plans stored on the telescope."""
    try:
        plans = await telescope.list_plan()
        return {"plans": plans if isinstance(plans, list) else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan/upload")
async def upload_plan_to_telescope(
    request: PlanUploadRequest,
    telescope: SeestarClient = Depends(get_current_telescope),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Upload a saved plan to the telescope.

    Loads the SavedPlan by ID, converts to Seestar format, and calls set_plan().
    """
    saved = db.query(SavedPlan).filter(SavedPlan.id == request.plan_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail=f"Plan {request.plan_id} not found")
    try:
        plan = ObservingPlan(**saved.plan_data)
        seestar_payload = _plan_to_seestar_format(plan)
        success = await telescope.set_plan(**seestar_payload)
        return _ok(success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/plan/{plan_name}")
async def delete_plan_from_telescope(
    plan_name: str,
    telescope: SeestarClient = Depends(get_current_telescope),
) -> Dict[str, Any]:
    """Delete a plan from the telescope by name."""
    try:
        success = await telescope.delete_plan(plan_name)
        return _ok(success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

4. Lint and run tests (green):
```bash
docker exec astronomus pytest backend/tests/api/test_telescope_features_plan.py -q --no-cov
```

5. Commit:
```bash
git add backend/app/api/telescope_features.py backend/tests/api/test_telescope_features_plan.py
git commit -m "feat: add plan upload/list/delete endpoints to telescope features API"
```

---

## Task 14: Frontend — Send to Scope button and planningStore.sendToTelescope()

**Files:**
- Modify: `frontend/vue-app/src/stores/planning.js`
- Modify: `frontend/vue-app/src/views/PlanningView.vue`

**Steps:**

1. Write failing test in `frontend/vue-app/src/stores/__tests__/planning.test.js`:

```javascript
it('sendToTelescope posts plan_id to upload endpoint', async () => {
  axios.post.mockResolvedValue({ data: { success: true } })
  const store = usePlanningStore()
  // Simulate a saved plan with id
  store.currentPlan = { scheduled_targets: [], total_targets: 0, coverage_percent: 0, session: {}, location: {}, weather_forecast: [] }
  // Inject a saved plan reference
  store._lastSavedPlanId = 42

  await store.sendToTelescope(42)
  expect(axios.post).toHaveBeenCalledWith('/api/telescope/features/plan/upload', { plan_id: 42 })
})

it('sendToTelescope emits error on failure', async () => {
  axios.post.mockRejectedValue({ response: { data: { detail: 'scope error' } } })
  const store = usePlanningStore()
  await expect(store.sendToTelescope(1)).rejects.toBeTruthy()
})
```

2. Confirm failure (red).

3. Add `sendToTelescope` action to `frontend/vue-app/src/stores/planning.js`:

In `state()` — no new state needed.

In `actions`:
```javascript
async sendToTelescope(planId) {
  if (!planId) throw new Error('No plan ID provided')
  this.loading = true
  this.error = null
  try {
    await axios.post('/api/telescope/features/plan/upload', { plan_id: planId })
    useToastStore().success('Plan uploaded to telescope')
  } catch (err) {
    const msg = 'Failed to upload plan: ' + (err.response?.data?.detail || err.message)
    this.error = msg
    useToastStore().error(msg)
    throw err
  } finally {
    this.loading = false
  }
},
```

4. Modify `PlanningView.vue` — add "Send to Scope" button in the toolbar next to "Execute Plan":

Locate the existing button block (around line 43–63). After the `<button @click="executePlan" ...>Execute Plan</button>`, add:

```html
<button
  @click="sendToScope"
  :disabled="planningStore.loading || !executionStore.connected || !lastSavedPlanId"
  class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
  title="Upload this plan to the telescope"
>
  Send to Scope
</button>
```

In `<script setup>`, add `lastSavedPlanId` ref and `sendToScope` function:

```javascript
import { ref, computed, onMounted } from 'vue'
// ...existing imports...
const lastSavedPlanId = ref(null)

async function savePlan() {
  const saved = await planningStore.savePlan()
  if (saved?.id) lastSavedPlanId.value = saved.id
}

async function sendToScope() {
  if (!lastSavedPlanId.value) return
  await planningStore.sendToTelescope(lastSavedPlanId.value)
}
```

Also update the existing `savePlan` call in the template to use the new `savePlan` function if the view doesn't already capture the saved plan ID.

5. Build:
```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -5
```

6. Run frontend tests:
```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run test -- --run 2>&1 | tail -20
```

7. Commit:
```bash
git add frontend/vue-app/src/stores/planning.js frontend/vue-app/src/stores/__tests__/planning.test.js frontend/vue-app/src/views/PlanningView.vue
git commit -m "feat: add Send to Scope button in PlanningView and sendToTelescope action in planning store"
```

---

## Task 15: Full test suite + lint pass

**Files:** none new

**Steps:**

1. Run backend tests:
```bash
docker exec astronomus pytest tests/ -q --no-cov
```
Expected: all pass (or at most pre-existing skips).

2. Run lint on all modified/created backend files:
```bash
docker exec astronomus black --line-length=120 \
  backend/app/models/models.py \
  backend/app/services/multi_day_weather_service.py \
  backend/app/api/astronomy.py \
  backend/app/models/catalog_models.py \
  backend/app/services/catalog_service.py \
  backend/app/api/custom_targets.py \
  backend/app/api/routes.py \
  backend/app/api/telescope_features.py

docker exec astronomus isort --profile=black --line-length=120 \
  backend/app/models/models.py \
  backend/app/services/multi_day_weather_service.py \
  backend/app/api/astronomy.py \
  backend/app/models/catalog_models.py \
  backend/app/services/catalog_service.py \
  backend/app/api/custom_targets.py \
  backend/app/api/routes.py \
  backend/app/api/telescope_features.py

docker exec astronomus ruff check --config backend/pyproject.toml \
  backend/app/models/models.py \
  backend/app/services/multi_day_weather_service.py \
  backend/app/api/astronomy.py \
  backend/app/models/catalog_models.py \
  backend/app/services/catalog_service.py \
  backend/app/api/custom_targets.py \
  backend/app/api/routes.py \
  backend/app/api/telescope_features.py
```

3. Run frontend build + tests:
```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -5
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run test -- --run
```

4. Fix any lint or test failures before proceeding.

5. Commit any lint-triggered reformats:
```bash
git add -p  # stage only whitespace/format fixes
git commit -m "style: apply black/isort/ruff formatting to feature/upload-weather-targets files"
```

---

## Task 16: Create pull request

**Files:** none

**Steps:**

1. Push branch:
```bash
git push -u origin feature/upload-weather-targets
```

2. Open PR:
```bash
gh pr create \
  --title "feat: plan upload to Seestar, 7-day weather strip, custom catalog targets" \
  --body "$(cat <<'EOF'
## Summary

- **Feature 1 (Plan Upload):** `POST /api/telescope/features/plan/upload`, `GET /api/telescope/features/plan/list`, `DELETE /api/telescope/features/plan/{name}` endpoints convert a `SavedPlan` to Seestar wire format and call `set_plan()`. Frontend adds a "Send to Scope" button in `PlanningView.vue` (disabled when disconnected or no saved plan).
- **Feature 2 (Multi-day Weather):** `MultiDayWeatherService` fetches 7-day forecasts from Open-Meteo (free, no auth). `GET /api/weather/multiday` returns `DailyForecast` list. `DailyWeatherStrip.vue` renders a color-coded 7-column strip embedded in `TonightView.vue`.
- **Feature 3 (Custom Targets):** `UserTarget` SQLAlchemy model + Alembic migration. CRUD API at `/api/targets/custom`. `CatalogService.filter_targets()` merges user targets into results. `CustomTargetsPanel.vue` in `DiscoveryView.vue` My Targets tab with inline add form.

## Test plan

- [ ] `docker exec astronomus pytest tests/ -q --no-cov` — all pass
- [ ] `black --line-length=120` + `isort --profile=black` + `ruff check` — no violations
- [ ] `npm run build` in `frontend/vue-app` — no errors
- [ ] `npm run test -- --run` in `frontend/vue-app` — all pass
- [ ] `GET /api/weather/multiday` returns 7 days when location is configured
- [ ] `POST /api/targets/custom` creates a target; appears in `GET /api/targets/custom`
- [ ] `GET /api/telescope/features/plan/list` returns 503 when telescope disconnected
- [ ] Alembic: `alembic downgrade -1` then `alembic upgrade head` succeeds

EOF
)"
```

---

## Notes on Known Risks and Edge Cases

**Feature 1 — Seestar plan format:** The `set_plan` wire format is not definitively documented. The conversion in `_plan_to_seestar_format` uses the best-known format. If `set_plan(**payload)` rejects it, try `import_plan(**payload)` as fallback — the library exposes both. A 502 from the endpoint with "Telescope rejected the command" is expected until the format is confirmed against live hardware. The `ra`/`dec` field names vs `ra_hours`/`dec_degrees` may need adjustment based on what `set_plan` actually expects.

**Feature 2 — Open-Meteo timezone:** The `timezone=auto` parameter makes Open-Meteo return dates in the observer's local timezone, which is what is wanted for "tonight is good" decisions. The `cloud_cover_mean` field may return `null` for the current day if forecasting hasn't started; the service guards against this with `or 0`.

**Feature 3 — catalog_id collision:** The `USER:<slug>` scheme derived from `_name_to_slug` will collide if two targets have the same normalized name (e.g., "My Nebula" and "MY NEBULA"). The API returns HTTP 400 with a clear message in this case. A user can work around it by appending a number to the name.

**Alembic test isolation:** The `setup_test_db_schema` fixture runs `alembic upgrade head` once per session. Once Task 8's migration is in `alembic/versions/`, the test DB will pick up `user_targets` automatically on the next test run. No manual action needed.

### Critical Files for Implementation
- `/home/irjudson/Projects/astronomus/backend/app/api/telescope_features.py`
- `/home/irjudson/Projects/astronomus/backend/app/api/astronomy.py`
- `/home/irjudson/Projects/astronomus/backend/app/models/catalog_models.py`
- `/home/irjudson/Projects/astronomus/frontend/vue-app/src/views/TonightView.vue`
- `/home/irjudson/Projects/astronomus/frontend/vue-app/src/views/DiscoveryView.vue`
