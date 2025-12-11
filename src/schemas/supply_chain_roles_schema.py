# File: src/schemas/supply_chain_roles_schema.py
"""
Supply Chain Roles - The Cast & Their Domains

THE HELIX SUPPLY CHAIN CAST:
Scene 43-44: Rotterdam Port + Bath House Partnership

"We ride WITH the equipment." - YUKI
"I see what others miss." - CHARLIE
"Papers are TIGHT." - Ka-MAKI
"""

from typing import Literal
from pydantic import BaseModel, Field


# =============================================================================
# THE SUPPLY CHAIN CAST
# =============================================================================

class SupplyChainRole(BaseModel):
    """A role in the supply chain"""
    code: str = Field(..., description="Role code (e.g., YUKI, CHARLIE)")
    name: str = Field(..., description="Full name")
    title: str = Field(..., description="Job title")
    domain: str = Field(..., description="Area of responsibility")
    actor_type: str = Field(..., description="Maps to ActorType enum")
    motto: str | None = Field(None, description="Character motto")

    # Responsibilities
    primary_duties: list[str] = Field(default_factory=list)
    authority_level: Literal["execute", "approve", "final"] = "execute"
    reports_to: str | None = None

    # Systems access
    helix_modules: list[str] = Field(default_factory=list, description="Which HELIX modules they use")
    can_sign_off: list[str] = Field(default_factory=list, description="What they can approve")


class SupplyChainTeam(BaseModel):
    """A team of supply chain roles"""
    name: str
    lead: str
    members: list[SupplyChainRole]
    coverage: str = Field(..., description="What part of chain they cover")


# =============================================================================
# THE FREIGHT TEAM (YUKI's Domain)
# =============================================================================

YUKI = SupplyChainRole(
    code="YUKI",
    name="YUKI",
    title="Freight Coordinator",
    domain="International Logistics",
    actor_type="freight_coordinator",
    motto="We ride WITH the equipment.",
    primary_duties=[
        "Coordinate all international shipments",
        "Manage supplier relationships (Japan, Switzerland)",
        "Track containers from origin to destination",
        "Ensure equipment arrives safely and on time",
        "Final approval on freight decisions",
    ],
    authority_level="final",
    reports_to="SAL",
    helix_modules=["equipment", "shipments", "purchase_orders", "suppliers"],
    can_sign_off=["shipment_approval", "supplier_selection", "freight_route"]
)

CHARLIE = SupplyChainRole(
    code="CHARLIE",
    name="CHARLIE",
    title="Freight Security Specialist",
    domain="Shipment Security & Inspection",
    actor_type="freight_security",
    motto="I see what others miss.",
    primary_duties=[
        "Physical inspection of all shipments",
        "Verify seals and container integrity",
        "Document any damage or anomalies",
        "Night shift monitoring at ports",
        "Hidden cargo verification (rides IN the container)",
        "Eyes and ears for YUKI",
    ],
    authority_level="execute",
    reports_to="YUKI",
    helix_modules=["shipments", "trace_events", "customs"],
    can_sign_off=["physical_inspection", "seal_verification", "anomaly_report"]
)

# =============================================================================
# THE PORT TEAM (Rotterdam)
# =============================================================================

HANK = SupplyChainRole(
    code="HANK",
    name="HANK 'The Hankster'",
    title="Port Authority Controller",
    domain="Rotterdam Port Operations",
    actor_type="port_authority",
    motto="No stamp, no move.",
    primary_duties=[
        "Final authority on container release",
        "Sign off on all port documentation",
        "Coordinate with customs for inspections",
        "Night shift disco engineering",
        "The STAMP - nothing moves without Hank's approval",
    ],
    authority_level="final",
    reports_to="Port Authority Rotterdam",
    helix_modules=["shipments", "customs_clearances"],
    can_sign_off=["port_release", "container_clearance", "final_documentation"]
)

DIRK = SupplyChainRole(
    code="DIRK",
    name="DIRK 'Dirty Dirk'",
    title="Port Operations Specialist",
    domain="Container Handling",
    actor_type="port_worker",
    motto="These hands move mountains.",
    primary_duties=[
        "Physical container movement",
        "Seal inspection and verification",
        "Loading/unloading coordination",
        "Forklift and crane operations",
        "The HANDS - gets things done",
    ],
    authority_level="execute",
    reports_to="HANK",
    helix_modules=["shipments", "trace_events"],
    can_sign_off=["container_moved", "seal_verified", "unloading_complete"]
)

# =============================================================================
# THE CUSTOMS TEAM
# =============================================================================

KA_MAKI = SupplyChainRole(
    code="KA_MAKI",
    name="Ka-MAKI",
    title="Customs Clearance Specialist",
    domain="Swiss-Japanese Customs",
    actor_type="customs_agent",
    motto="Papers are TIGHT.",
    primary_duties=[
        "All customs documentation",
        "Duty calculations and payments",
        "HS code classification",
        "Inspection coordination",
        "Swiss-Japanese regulatory compliance",
        "THE PAPERS - nothing passes without Ka-MAKI",
    ],
    authority_level="approve",
    reports_to="YUKI",
    helix_modules=["customs_clearances", "shipments", "equipment"],
    can_sign_off=["customs_declaration", "duty_payment", "clearance_approved"]
)

# =============================================================================
# THE BUILD TEAM
# =============================================================================

MARCO = SupplyChainRole(
    code="MARCO",
    name="MARCO",
    title="Equipment Assembly Specialist",
    domain="Equipment Installation & Maintenance",
    actor_type="equipment_tech",
    motto="Build it right, build it once.",
    primary_duties=[
        "Equipment assembly and installation",
        "Custom fabrication coordination (with BORRIS)",
        "Maintenance scheduling",
        "Spare parts management",
        "THE BUILDER - makes it work",
    ],
    authority_level="execute",
    reports_to="SAL",
    helix_modules=["equipment", "maintenance_events", "purchase_orders"],
    can_sign_off=["installation_complete", "maintenance_done", "equipment_operational"]
)

BORRIS = SupplyChainRole(
    code="BORRIS",
    name="BORRIS",
    title="Custom Fabricator",
    domain="Custom Equipment Design",
    actor_type="equipment_tech",
    motto="I build what nobody else can.",
    primary_duties=[
        "Custom salad bar design",
        "CBD dispenser integration",
        "Refrigeration systems",
        "One-off equipment builds",
        "THE ARTIST - custom is his game",
    ],
    authority_level="approve",
    reports_to="SAL",
    helix_modules=["equipment", "suppliers"],
    can_sign_off=["custom_design", "fabrication_complete", "quality_check"]
)


# =============================================================================
# TEAM DEFINITIONS
# =============================================================================

FREIGHT_TEAM = SupplyChainTeam(
    name="Freight Operations",
    lead="YUKI",
    members=[YUKI, CHARLIE],
    coverage="International shipments, supplier coordination"
)

PORT_TEAM = SupplyChainTeam(
    name="Rotterdam Port",
    lead="HANK",
    members=[HANK, DIRK],
    coverage="Container handling, port clearance"
)

CUSTOMS_TEAM = SupplyChainTeam(
    name="Customs & Compliance",
    lead="KA_MAKI",
    members=[KA_MAKI],
    coverage="Duties, documentation, regulatory"
)

BUILD_TEAM = SupplyChainTeam(
    name="Equipment Build",
    lead="MARCO",
    members=[MARCO, BORRIS],
    coverage="Assembly, installation, custom fabrication"
)


# =============================================================================
# THE FULL CAST (Export for use)
# =============================================================================

SUPPLY_CHAIN_CAST = {
    "YUKI": YUKI,
    "CHARLIE": CHARLIE,
    "HANK": HANK,
    "DIRK": DIRK,
    "KA_MAKI": KA_MAKI,
    "MARCO": MARCO,
    "BORRIS": BORRIS,
}

SUPPLY_CHAIN_TEAMS = {
    "freight": FREIGHT_TEAM,
    "port": PORT_TEAM,
    "customs": CUSTOMS_TEAM,
    "build": BUILD_TEAM,
}


# =============================================================================
# WORKFLOW: Equipment Journey (COOLIE Example)
# =============================================================================

COOLIE_JOURNEY = """
THE COOLIE JOURNEY - Yokohama to HAIRY FISH

1. SUPPLIER (JURA-CH / MOSEY-JP)
   - YUKI negotiates with JURA
   - MOSEY-JP handles Japan logistics
   - PO created in HELIX

2. SHIPMENT CREATED
   - Container: MSCU-7749-COOLIE (20ft)
   - YUKI: Freight Coordinator
   - CHARLIE: Rides IN the container (shhh)

3. AT PORT - YOKOHAMA
   - Japanese customs clearance
   - Container sealed
   - CHARLIE verifies seal

4. IN TRANSIT - SEA (45 days)
   - Vessel: MSC AURORA
   - CHARLIE: Monitoring, hidden in container
   - Temperature controlled

5. AT PORT - ROTTERDAM
   - HANK: Port authority sign-off
   - DIRK: Moves container to inspection area
   - Ka-MAKI: Customs clearance (papers TIGHT)

6. CUSTOMS CLEARED
   - Ka-MAKI: All duties paid
   - HANK: Final stamp
   - Container released

7. LAST MILE - TO ZURICH
   - CHARLIE: Accompanies shipment
   - Driver: Final delivery

8. DELIVERED - HAIRY FISH
   - MARCO: Receives and inspects
   - MARCO: Installation begins

9. INSTALLED - OPERATIONAL
   - MARCO: Sign-off on installation
   - SAL: Final acceptance
   - COOLIE: "Good morning, SAL"
"""


# =============================================================================
# SIGN-OFF CHAIN (Who approves what)
# =============================================================================

SIGN_OFF_CHAIN = {
    "purchase_order": ["YUKI", "SAL"],
    "shipment_departure": ["YUKI"],
    "physical_inspection": ["CHARLIE"],
    "port_release": ["HANK"],
    "customs_clearance": ["KA_MAKI"],
    "container_moved": ["DIRK"],
    "delivery_received": ["MARCO"],
    "installation_complete": ["MARCO"],
    "final_acceptance": ["SAL"],
}


# =============================================================================
# SCENE 43-44: Rotterdam + Bath House
# =============================================================================

SCENE_43_44_SUMMARY = """
SCENE 43: ROTTERDAM PORT - NIGHT

YUKI and CHARLIE at Rotterdam port. Night shift.
HANK runs the show - the Disco Engineering controller.
DIRK moves the containers.

The COOLIE container arrives. CHARLIE steps out.
"Papers are TIGHT." - Ka-MAKI approves everything.
HANK stamps the release.

CHARLIE: "I rode the whole way. Nobody touched it."
YUKI: "That's why I trust you."

---

SCENE 44: BATH HOUSE - THE PARTNERSHIP

Japanese bath house. YUKI and CHARLIE.
This is where the deal is made.

YUKI: "You see what others miss."
CHARLIE: "And you know who to trust."

The flashback shows the port - HANK and DIRK at work.
CHARLIE's eyes catching the details others miss.
A seal slightly off. A manifest error. Fixed before it mattered.

YUKI: "You're not just security. You're my eyes."
CHARLIE: "I'm in."

The partnership is sealed. Not with a contract.
With trust. With a handshake in the steam.

"We ride WITH the equipment." - YUKI
"Every time." - CHARLIE
"""


if __name__ == "__main__":
    print("=" * 60)
    print("HELIX SUPPLY CHAIN CAST")
    print("=" * 60)

    for code, role in SUPPLY_CHAIN_CAST.items():
        print(f"\n{role.name} - {role.title}")
        print(f"  Domain: {role.domain}")
        print(f"  Motto: {role.motto}")
        print(f"  Authority: {role.authority_level}")
        print(f"  Reports to: {role.reports_to}")

    print("\n" + "=" * 60)
    print("THE COOLIE JOURNEY")
    print("=" * 60)
    print(COOLIE_JOURNEY)
