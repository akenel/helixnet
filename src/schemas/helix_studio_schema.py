# File: src/schemas/helix_studio_schema.py
"""
HELIX STUDIO — The Media Empire Schema

260 episodes. 5 years. BitChute first.
Looney Tunes meets Swiss Reality meets YAGNI Philosophy.

"Rabbit holes = Worm holes = Same diff. Land safe."

The Production Pipeline:
  IDEA → SCRIPTED → RECORDED → EDITED → PUBLISHED → LEGENDARY

The Cast: Every CRACK in the system is a potential star.
The Stories: Every KB is a potential episode.
The Philosophy: Be water, my friend.
"""
from enum import Enum
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


# ================================================================
# EPISODE STATUS — The Pipeline
# ================================================================
class EpisodeStatus(str, Enum):
    """Where is this episode in the pipeline?"""
    IDEA = "idea"                    # Spark in someone's head
    OUTLINED = "outlined"            # Basic structure exists
    SCRIPTED = "scripted"            # Full script written
    CAST_READY = "cast_ready"        # Actors/voices assigned
    RECORDING = "recording"          # In the booth
    RECORDED = "recorded"            # Raw footage/audio done
    EDITING = "editing"              # Post-production
    REVIEW = "review"                # Final check before publish
    PUBLISHED = "published"          # LIVE on BitChute
    LEGENDARY = "legendary"          # Hall of fame status


class EpisodeCategory(str, Enum):
    """What kind of episode is this?"""
    HELLS_SAP_KITCHEN = "hells_sap_kitchen"      # The GIMP series
    TIGER_TALES = "tiger_tales"                  # Thommy, workers, real life
    SALAD_BAR_SESSIONS = "salad_bar_sessions"    # Tony Boz, CBD, food
    SPACE_ODYSSEY = "space_odyssey"              # 9001, rabbit holes, philosophy
    FIELD_NOTES = "field_notes"                  # Real conversations, raw
    CRACK_SPOTLIGHT = "crack_spotlight"          # Character deep dives
    TECH_TIGGLES = "tech_tiggles"                # YAGNI, BLQ, coding wisdom
    LOST_SOULS = "lost_souls"                    # Gessler, Burt, the street
    FOUNDERS_CORNER = "founders_corner"          # SAL, FELIX, BORRIS, TONY


class Platform(str, Enum):
    """Where does this go? (BitChute FIRST, always)"""
    BITCHUTE = "bitchute"            # Primary — FUCK YouTube
    RUMBLE = "rumble"                # Backup 1
    ODYSEE = "odysee"                # Backup 2
    ARCHIVE_ORG = "archive_org"      # Permanent backup
    HELIX_SELF = "helix_self"        # Self-hosted on HelixNET


# ================================================================
# SCENE — The building blocks
# ================================================================
class SceneCreate(BaseModel):
    """A single scene within an episode"""
    scene_number: int = Field(..., ge=1, description="Scene order (1, 2, 3...)")
    title: str = Field(..., max_length=200, description="Scene title")
    location: Optional[str] = Field(None, max_length=200, description="Where does this happen?")
    description: str = Field(..., description="What happens in this scene?")
    characters: list[str] = Field(default_factory=list, description="Who's in this scene? (handles)")
    dialogue_notes: Optional[str] = Field(None, description="Key dialogue or beats")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Estimated duration")
    kb_reference: Optional[str] = Field(None, description="Related KB article ID")

    class Config:
        json_schema_extra = {
            "example": {
                "scene_number": 1,
                "title": "The Taxman Fear",
                "location": "HAIRY FISH Restaurant",
                "description": "SAL explains why he's scared of the health department. Molly's sauce, 3/20 bad batches.",
                "characters": ["SAL", "FELIX", "ANGEL"],
                "dialogue_notes": "SAL: 'The taxman doesn't care about flavor, only paperwork.'",
                "duration_seconds": 180,
                "kb_reference": "KB-014"
            }
        }


class SceneRead(SceneCreate):
    """Scene with read-only fields"""
    id: str
    episode_id: str


# ================================================================
# EPISODE — The main unit
# ================================================================
class EpisodeCreate(BaseModel):
    """Create a new episode in the pipeline"""
    # Identity
    episode_code: str = Field(..., max_length=20, description="Unique code (S01E01, HK-001, etc.)")
    title: str = Field(..., max_length=300, description="Episode title")
    subtitle: Optional[str] = Field(None, max_length=300, description="Episode subtitle")

    # Classification
    category: EpisodeCategory = Field(..., description="Which series?")
    season: int = Field(1, ge=1, le=10, description="Season number")
    episode_number: int = Field(..., ge=1, description="Episode number in season")

    # Status
    status: EpisodeStatus = Field(EpisodeStatus.IDEA, description="Pipeline status")

    # Content
    logline: str = Field(..., max_length=500, description="One-line summary (the hook)")
    synopsis: Optional[str] = Field(None, description="Full episode description")

    # Cast
    primary_cast: list[str] = Field(default_factory=list, description="Main characters (handles)")
    guest_cast: list[str] = Field(default_factory=list, description="Guest appearances")
    narrator: Optional[str] = Field(None, description="Who narrates? (if any)")

    # Production
    writer: Optional[str] = Field(None, description="Who wrote this?")
    director: Optional[str] = Field(None, description="Who's directing?")
    editor: Optional[str] = Field(None, description="Who's editing?")

    # Technical
    target_duration_minutes: int = Field(15, ge=1, le=120, description="Target runtime")
    actual_duration_minutes: Optional[int] = Field(None, description="Actual runtime after edit")

    # Schedule
    target_record_date: Optional[date] = Field(None, description="When to record")
    target_publish_date: Optional[date] = Field(None, description="When to publish")
    actual_publish_date: Optional[date] = Field(None, description="When actually published")

    # Links (after publish)
    bitchute_url: Optional[str] = Field(None, description="BitChute link (primary)")
    backup_urls: list[str] = Field(default_factory=list, description="Backup platform links")

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    related_kbs: list[str] = Field(default_factory=list, description="Related KB article IDs")
    related_episodes: list[str] = Field(default_factory=list, description="Related episode codes")

    # Notes
    production_notes: Optional[str] = Field(None, description="Internal production notes")

    class Config:
        json_schema_extra = {
            "example": {
                "episode_code": "HK-001",
                "title": "Plant Maintenance",
                "subtitle": "We Need IoT Sensors!",
                "category": "hells_sap_kitchen",
                "season": 1,
                "episode_number": 1,
                "status": "scripted",
                "logline": "The GIMPS demand IoT sensors for a simple plant. Window opens.",
                "synopsis": "SAP consultant insists on $2M IoT implementation for watering office plants. Chuck has other ideas.",
                "primary_cast": ["MASTER_GIMP", "SUCKER_1", "SUCKER_2"],
                "guest_cast": ["CHUCK", "JC"],
                "writer": "ANGEL",
                "target_duration_minutes": 12,
                "tags": ["sap", "consulting", "comedy", "yagni"],
                "related_kbs": ["KB-HELLS-SAP-001"]
            }
        }


class EpisodeRead(EpisodeCreate):
    """Episode with read-only fields"""
    id: str
    created_at: str
    updated_at: str
    scenes: list[SceneRead] = Field(default_factory=list)
    scene_count: int = 0
    is_published: bool = False
    days_in_pipeline: int = 0


class EpisodeUpdate(BaseModel):
    """Update an existing episode"""
    title: Optional[str] = None
    subtitle: Optional[str] = None
    status: Optional[EpisodeStatus] = None
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    primary_cast: Optional[list[str]] = None
    guest_cast: Optional[list[str]] = None
    narrator: Optional[str] = None
    writer: Optional[str] = None
    director: Optional[str] = None
    editor: Optional[str] = None
    target_duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None
    target_record_date: Optional[date] = None
    target_publish_date: Optional[date] = None
    actual_publish_date: Optional[date] = None
    bitchute_url: Optional[str] = None
    backup_urls: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    related_kbs: Optional[list[str]] = None
    related_episodes: Optional[list[str]] = None
    production_notes: Optional[str] = None


# ================================================================
# SERIES — The container
# ================================================================
class SeriesCreate(BaseModel):
    """A series (collection of episodes)"""
    code: str = Field(..., max_length=20, description="Series code (HK, TT, SS, etc.)")
    name: str = Field(..., max_length=200, description="Series name")
    category: EpisodeCategory = Field(..., description="Category this series belongs to")
    description: str = Field(..., description="What's this series about?")

    # Planning
    planned_seasons: int = Field(1, ge=1, description="How many seasons planned?")
    episodes_per_season: int = Field(12, ge=1, description="Target episodes per season")

    # Style
    tone: str = Field("comedy", description="Overall tone (comedy, drama, documentary, etc.)")
    aesthetic: str = Field("looney_tunes", description="Visual/audio style")

    # Team
    showrunner: Optional[str] = Field(None, description="Who runs this series?")
    regular_cast: list[str] = Field(default_factory=list, description="Recurring cast members")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "HK",
                "name": "Hell's SAP Kitchen",
                "category": "hells_sap_kitchen",
                "description": "Dark comedy exposing enterprise consulting madness. GIMPS, SUCKERS, and the occasional roundhouse kick.",
                "planned_seasons": 3,
                "episodes_per_season": 12,
                "tone": "dark_comedy",
                "aesthetic": "looney_tunes",
                "showrunner": "ANGEL",
                "regular_cast": ["MASTER_GIMP", "SUCKER_1", "SUCKER_2", "CHUCK", "JC", "BRUCE"]
            }
        }


class SeriesRead(SeriesCreate):
    """Series with computed fields"""
    id: str
    created_at: str
    total_episodes: int = 0
    published_episodes: int = 0
    completion_percent: float = 0.0


# ================================================================
# PRODUCTION DASHBOARD — The overview
# ================================================================
class ProductionStats(BaseModel):
    """Studio-wide production statistics"""
    # Totals
    total_series: int = 0
    total_episodes: int = 0
    total_scenes: int = 0

    # By status
    ideas: int = 0
    in_production: int = 0
    published: int = 0
    legendary: int = 0

    # By category
    episodes_by_category: dict[str, int] = Field(default_factory=dict)

    # Timeline
    episodes_this_month: int = 0
    episodes_this_year: int = 0

    # Cast stats
    most_featured_cast: list[tuple[str, int]] = Field(default_factory=list)

    # Content hours
    total_published_minutes: int = 0
    total_planned_minutes: int = 0


class PipelineView(BaseModel):
    """View of episodes by pipeline stage"""
    ideas: list[EpisodeRead] = Field(default_factory=list)
    outlined: list[EpisodeRead] = Field(default_factory=list)
    scripted: list[EpisodeRead] = Field(default_factory=list)
    in_production: list[EpisodeRead] = Field(default_factory=list)
    ready_to_publish: list[EpisodeRead] = Field(default_factory=list)
    published: list[EpisodeRead] = Field(default_factory=list)
    legendary: list[EpisodeRead] = Field(default_factory=list)


# ================================================================
# THE PHILOSOPHY
# ================================================================
"""
WHY THIS STRUCTURE?

1. EPISODE is the atomic unit
   - Everything flows from episodes
   - Scenes are optional detail
   - Can track with just episode_code + status

2. SERIES is organizational
   - Groups episodes by theme
   - Helps with planning
   - Optional — episodes can exist without series

3. STATUS is the pipeline
   - Simple linear progression
   - LEGENDARY is the goal
   - Every episode can get there

4. CAST links to CUSTOMERS
   - Every character is a CRACK in the system
   - Real people, real stories
   - The ecosystem connects

5. KB links to EPISODES
   - Knowledge becomes content
   - Content becomes knowledge
   - The circle completes

YAGNI NOTES:
- No complex scheduling system (use target dates)
- No approval workflows (use status)
- No budget tracking (separate concern)
- No asset management (use MinIO directly)

BE WATER:
- Start with IDEA
- Flow through pipeline
- Become LEGENDARY
"""
