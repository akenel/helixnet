# File: src/services/helix_studio_seeding.py
"""
HELIX STUDIO Seeding — The First Episodes

260 planned. Let's start with the BANGERS.

"The show must go on." — Every artist ever
"The window must open." — Every SAP consultant's nightmare
"""
import logging

logger = logging.getLogger(__name__)


# ================================================================
# THE SERIES
# ================================================================
SERIES = [
    {
        "code": "HK",
        "name": "Hell's SAP Kitchen",
        "category": "hells_sap_kitchen",
        "description": "Dark comedy exposing enterprise consulting madness. GIMPS strapped in, tongues out. SUCKERS bent over. Windows opening.",
        "planned_seasons": 3,
        "episodes_per_season": 12,
        "tone": "dark_comedy",
        "aesthetic": "looney_tunes",
        "showrunner": "ANGEL",
        "regular_cast": ["MASTER_GIMP", "SUCKER_1", "SUCKER_2", "CHUCK", "JC", "BRUCE", "TIGER"]
    },
    {
        "code": "TT",
        "name": "Tiger Tales",
        "category": "tiger_tales",
        "description": "Real workers, real problems, real solutions. Thommy the Gypsy and the highway robbery of gas station lunches.",
        "planned_seasons": 5,
        "episodes_per_season": 52,  # Weekly!
        "tone": "heartfelt_comedy",
        "aesthetic": "documentary_style",
        "showrunner": "ANGEL",
        "regular_cast": ["THOMMY", "DONNY", "MOLLY", "FELIX", "WORKERS"]
    },
    {
        "code": "SS",
        "name": "Salad Bar Sessions",
        "category": "salad_bar_sessions",
        "description": "Tony Boz CBD, Molly's kitchen, farm to table to soul. The Lion's Vision made edible.",
        "planned_seasons": 2,
        "episodes_per_season": 24,
        "tone": "warm_educational",
        "aesthetic": "cooking_show",
        "showrunner": "TONY",
        "regular_cast": ["TONY_BOZ", "MOLLY", "SAL", "FELIX", "BORRIS"]
    },
    {
        "code": "SO",
        "name": "Space Odyssey 9001",
        "category": "space_odyssey",
        "description": "Rabbit holes = Worm holes. Philosophy through Looney Tunes lens. Above or below — same diff — land safe.",
        "planned_seasons": 3,
        "episodes_per_season": 12,
        "tone": "philosophical_absurdist",
        "aesthetic": "looney_tunes_scifi",
        "showrunner": "ANGEL",
        "regular_cast": ["PAUL", "MAX", "SMAGOR_BORG", "BUGS", "FLYING_TIGER_CREW"]
    },
    {
        "code": "FN",
        "name": "Field Notes",
        "category": "field_notes",
        "description": "Raw conversations. Unscripted moments. The real stories behind the network.",
        "planned_seasons": 10,
        "episodes_per_season": 26,
        "tone": "raw_authentic",
        "aesthetic": "podcast_visual",
        "showrunner": "ANGEL",
        "regular_cast": ["ANGEL", "LEO", "GUESTS"]
    },
    {
        "code": "LS",
        "name": "Lost Souls Department",
        "category": "lost_souls",
        "description": "The street. The struggle. The humanity. Gessler's 25 years. Free lockers for those who need them.",
        "planned_seasons": 2,
        "episodes_per_season": 12,
        "tone": "documentary_compassionate",
        "aesthetic": "cinema_verite",
        "showrunner": "SAL",
        "regular_cast": ["GESSLER", "BURT", "FABIO", "DIRK", "SAL"]
    },
]


# ================================================================
# THE FIRST EPISODES — The Pilot Season
# ================================================================
EPISODES = [
    # ============ HELL'S SAP KITCHEN ============
    {
        "episode_code": "HK-001",
        "title": "Plant Maintenance",
        "subtitle": "We Need IoT Sensors!",
        "category": "hells_sap_kitchen",
        "season": 1,
        "episode_number": 1,
        "status": "scripted",
        "logline": "SAP consultant demands $2M IoT implementation for watering office plants. A 2-year-old knows better.",
        "synopsis": "The GIMPS are strapped in, ready to consult. SUCKER_1 just wants to water the office plant. MASTER_GIMP insists on IoT sensors, real-time dashboards, and a 6-month implementation timeline. Chuck walks in. Window opens.",
        "primary_cast": ["MASTER_GIMP", "SUCKER_1", "SUCKER_2"],
        "guest_cast": ["CHUCK"],
        "writer": "ANGEL",
        "target_duration_minutes": 12,
        "tags": ["sap", "iot", "consulting", "plants", "window"],
    },
    {
        "episode_code": "HK-002",
        "title": "Project Planning",
        "subtitle": "Where's Your WBS?",
        "category": "hells_sap_kitchen",
        "season": 1,
        "episode_number": 2,
        "status": "outlined",
        "logline": "They want a Work Breakdown Structure for making coffee. 47 sub-tasks. 3 approval gates.",
        "primary_cast": ["MASTER_GIMP", "SUCKER_1"],
        "guest_cast": ["JC"],
        "writer": "ANGEL",
        "target_duration_minutes": 12,
        "tags": ["wbs", "project", "coffee", "bureaucracy"],
    },
    {
        "episode_code": "HK-003",
        "title": "BBQ Steak Meter",
        "subtitle": "Bluetooth Thermometer Dashboard!",
        "category": "hells_sap_kitchen",
        "season": 1,
        "episode_number": 3,
        "status": "idea",
        "logline": "Felix wants to grill a steak. The consultants want a Bluetooth thermometer integrated with SAP S/4HANA.",
        "primary_cast": ["MASTER_GIMP", "FELIX"],
        "guest_cast": ["BRUCE"],
        "writer": "ANGEL",
        "target_duration_minutes": 15,
        "tags": ["bbq", "steak", "bluetooth", "s4hana"],
    },
    {
        "episode_code": "HK-004",
        "title": "Fishing with Dynamite",
        "subtitle": "The Fuse Is Burning",
        "category": "hells_sap_kitchen",
        "season": 1,
        "episode_number": 4,
        "status": "idea",
        "logline": "Fuse is burning. Still discussing requirements. TIGER arrives with a fishing rod.",
        "primary_cast": ["SUCKER_1", "SUCKER_2"],
        "guest_cast": ["TIGER"],
        "writer": "ANGEL",
        "target_duration_minutes": 10,
        "tags": ["dynamite", "fishing", "deadline", "tiger"],
    },
    {
        "episode_code": "HK-005",
        "title": "Smoky and the SAP-IT",
        "subtitle": "Consultant Out the Window",
        "category": "hells_sap_kitchen",
        "season": 1,
        "episode_number": 5,
        "status": "scripted",
        "logline": "The window finally opens. Not everyone makes it to the meeting.",
        "synopsis": "After 6 months of delays, budget overruns, and scope creep, the SUCKERS have had enough. A mysterious truck appears. CB radios crackle. Smoky is not the police. The consultant discovers gravity.",
        "primary_cast": ["MASTER_GIMP", "SUCKER_1", "SUCKER_2"],
        "guest_cast": ["SMOKY", "BANDIT"],
        "writer": "ANGEL",
        "target_duration_minutes": 15,
        "tags": ["smoky", "bandit", "window", "gravity"],
    },

    # ============ TIGER TALES ============
    {
        "episode_code": "TT-001",
        "title": "Highway Robbery",
        "subtitle": "Thommy's Gas Station Problem",
        "category": "tiger_tales",
        "season": 1,
        "episode_number": 1,
        "status": "scripted",
        "logline": "7 CHF for ZERO nutrients. Grade F. The workers deserve better.",
        "synopsis": "Thommy the Gypsy eats gas station food every day. 7 CHF, no vitamins, no energy. By 2pm he's dead. Molly's Box arrives: 12.50 CHF, 1200 calories, Grade A. 'Oh what a beautiful day!'",
        "primary_cast": ["THOMMY"],
        "guest_cast": ["MOLLY", "DONNY"],
        "writer": "ANGEL",
        "target_duration_minutes": 15,
        "tags": ["workers", "lunch", "nutrition", "highway"],
    },
    {
        "episode_code": "TT-002",
        "title": "5 Sheets of Drywall",
        "subtitle": "The Tiger Byte",
        "category": "tiger_tales",
        "season": 1,
        "episode_number": 2,
        "status": "outlined",
        "logline": "5 francs. Full fuel. Carry 5 sheets of drywall up stairs. The math works.",
        "primary_cast": ["THOMMY", "CREW"],
        "guest_cast": ["FELIX"],
        "writer": "ANGEL",
        "target_duration_minutes": 12,
        "tags": ["drywall", "energy", "tiger_byte", "construction"],
    },
    {
        "episode_code": "TT-003",
        "title": "The 10:30 Ritual",
        "subtitle": "Coffee Break Revolution",
        "category": "tiger_tales",
        "season": 1,
        "episode_number": 3,
        "status": "idea",
        "logline": "Red Bull is poison. Coffee Mate is magic. The 10:30 break changes everything.",
        "primary_cast": ["CREW"],
        "guest_cast": ["PAUL"],
        "writer": "ANGEL",
        "target_duration_minutes": 10,
        "tags": ["coffee", "break", "energy", "ritual"],
    },

    # ============ SALAD BAR SESSIONS ============
    {
        "episode_code": "SS-001",
        "title": "The Lion's Vision",
        "subtitle": "Tony Boz Reveals the Plan",
        "category": "salad_bar_sessions",
        "season": 1,
        "episode_number": 1,
        "status": "outlined",
        "logline": "6 bar types. 5 membership tiers. Farm to fork to soul. Tony Boz explains.",
        "primary_cast": ["TONY_BOZ"],
        "guest_cast": ["SAL", "FELIX", "BORRIS"],
        "writer": "TONY",
        "target_duration_minutes": 20,
        "tags": ["salad", "cbd", "vision", "network"],
    },
    {
        "episode_code": "SS-002",
        "title": "CBD Creme My Pants",
        "subtitle": "The Dressing That Changes Everything",
        "category": "salad_bar_sessions",
        "season": 1,
        "episode_number": 2,
        "status": "idea",
        "logline": "Tony's secret CBD salad dressing. One taste and you understand.",
        "primary_cast": ["TONY_BOZ", "MOLLY"],
        "writer": "TONY",
        "target_duration_minutes": 15,
        "tags": ["cbd", "dressing", "recipe", "secret"],
    },

    # ============ SPACE ODYSSEY 9001 ============
    {
        "episode_code": "SO-001",
        "title": "Rabbit Holes = Worm Holes",
        "subtitle": "Above or Below, Same Diff",
        "category": "space_odyssey",
        "season": 1,
        "episode_number": 1,
        "status": "scripted",
        "logline": "Bugs knew. Wrong turn at Albuquerque led somewhere better. Check the diff later.",
        "synopsis": "PAUL explains quantum navigation through Looney Tunes logic. Every rabbit hole is a wormhole. Every wrong turn is a right turn in a different universe. The destination is always: SAFE.",
        "primary_cast": ["PAUL"],
        "guest_cast": ["MAX", "BUGS_BUNNY_SPIRIT"],
        "writer": "ANGEL",
        "target_duration_minutes": 18,
        "tags": ["philosophy", "quantum", "bugs", "navigation"],
    },
    {
        "episode_code": "SO-002",
        "title": "Flying Tiger One",
        "subtitle": "ACME Parts, Duct Tape, Hope",
        "category": "space_odyssey",
        "season": 1,
        "episode_number": 2,
        "status": "idea",
        "logline": "The ship runs on ACME parts. The crew runs on hope. Somehow it works.",
        "primary_cast": ["FLYING_TIGER_CREW"],
        "guest_cast": ["WILE_E_SPIRIT"],
        "writer": "ANGEL",
        "target_duration_minutes": 15,
        "tags": ["acme", "spaceship", "hope", "duct_tape"],
    },

    # ============ FIELD NOTES ============
    {
        "episode_code": "FN-001",
        "title": "Session 1 — SAL Tells All",
        "subtitle": "The Beginning",
        "category": "field_notes",
        "season": 1,
        "episode_number": 1,
        "status": "recorded",
        "logline": "December 5th. HAIRY FISH. SAL opens up. The network reveals itself.",
        "synopsis": "Raw recording from the field. SAL explains the whole vision. Felix nods. The future becomes clear.",
        "primary_cast": ["SAL", "ANGEL"],
        "guest_cast": ["FELIX"],
        "writer": "REALITY",
        "actual_duration_minutes": 45,
        "target_duration_minutes": 45,
        "tags": ["raw", "origin", "hairy_fish", "december"],
    },
    {
        "episode_code": "FN-002",
        "title": "Session 2 — The Coolie Invention",
        "subtitle": "15,000 Parts",
        "category": "field_notes",
        "season": 1,
        "episode_number": 2,
        "status": "recorded",
        "logline": "3 months. 500 slides. Japan craft meets Swiss precision. The COOLIE is born.",
        "primary_cast": ["SAL", "ANGEL"],
        "writer": "REALITY",
        "actual_duration_minutes": 30,
        "target_duration_minutes": 30,
        "tags": ["coolie", "invention", "japan", "craft"],
    },
    {
        "episode_code": "FN-003",
        "title": "Session 3 — The Broken Glass",
        "subtitle": "Felix on His Knees",
        "category": "field_notes",
        "season": 1,
        "episode_number": 3,
        "status": "recorded",
        "logline": "It's not about the glass. It's about everything. SAL begs him to stop.",
        "primary_cast": ["SAL", "FELIX", "ANGEL"],
        "writer": "REALITY",
        "actual_duration_minutes": 25,
        "target_duration_minutes": 25,
        "tags": ["emotion", "glass", "partnership", "tears"],
    },

    # ============ LOST SOULS ============
    {
        "episode_code": "LS-001",
        "title": "25 Years on the Street",
        "subtitle": "Sir Gessler's Story",
        "category": "lost_souls",
        "season": 1,
        "episode_number": 1,
        "status": "outlined",
        "logline": "25 years homeless. Multiple rehabs. 23 Rappen in his pocket. Still human.",
        "synopsis": "Documentary style. Gessler shares his journey. No judgment. The free locker program. A sandwich. Dignity.",
        "primary_cast": ["GESSLER"],
        "guest_cast": ["SAL"],
        "writer": "SAL",
        "target_duration_minutes": 30,
        "tags": ["homeless", "dignity", "story", "humanity"],
    },
    {
        "episode_code": "LS-002",
        "title": "The Secret Stash Can",
        "subtitle": "Dirk's Invention",
        "category": "lost_souls",
        "season": 1,
        "episode_number": 2,
        "status": "idea",
        "logline": "Two dog food cans. A Swiss pocket knife. Dirk's genius for survival.",
        "primary_cast": ["DIRK"],
        "guest_cast": ["GESSLER"],
        "writer": "ANGEL",
        "target_duration_minutes": 15,
        "tags": ["invention", "survival", "stash", "genius"],
    },
]


def get_series():
    """Get all planned series"""
    return SERIES


def get_episodes():
    """Get all seeded episodes"""
    return EPISODES


def get_stats():
    """Get production statistics"""
    total = len(EPISODES)
    by_status = {}
    by_category = {}

    for ep in EPISODES:
        status = ep.get("status", "idea")
        category = ep.get("category", "unknown")

        by_status[status] = by_status.get(status, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1

    return {
        "total_series": len(SERIES),
        "total_episodes": total,
        "by_status": by_status,
        "by_category": by_category,
        "planned_total": sum(s["planned_seasons"] * s["episodes_per_season"] for s in SERIES),
    }


# Quick test
if __name__ == "__main__":
    stats = get_stats()
    print(f"""
HELIX STUDIO — Production Status
================================
Series: {stats['total_series']}
Episodes (seeded): {stats['total_episodes']}
Episodes (planned): {stats['planned_total']}

By Status:
{chr(10).join(f"  {k}: {v}" for k, v in stats['by_status'].items())}

By Category:
{chr(10).join(f"  {k}: {v}" for k, v in stats['by_category'].items())}

LET'S MAKE SOME CONTENT!
    """)
