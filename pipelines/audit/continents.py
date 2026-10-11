"""Continental analyst desks — the regional structure of the AI audit.

Six desks, one per continent. Each desk deploys a panel of six analyst
agents (distinct analytical lenses) over its region's current reporting
digest. Panels are advisory: they add doubt and reviewer context, never
verification. Concerns raised independently by >=2 panelists are marked
panel consensus (aggregation of same-direction opinions).
"""

# ISO2 -> continent desk. Pilot countries first; extend as coverage grows.
COUNTRY_DESK: dict[str, str] = {
    # Africa
    **{c: "africa" for c in (
        "SD TD SS CD NG ET KE UG CM CF NE ML BF MR LY EG DZ MA TN SO ER DJ RW BI TZ ZM ZW MZ AO GH CI SN GM GN GW SL LR TG BJ GA CG GQ BW NA SZ LS MW MG KM SC MU CV ST ZA".split()
    )},
    # Asia
    **{c: "asia" for c in (
        "AF PK IN BD LK NP MM TH KH LA VN MY SG ID PH CN JP KP KR MN KZ KG TJ TM UZ IR IQ SY LB JO IL PS SA YE OM AE QA BH KW TR AZ AM GE".split()
    )},
    # Europe
    **{c: "europe" for c in (
        "UA RU BY MD RO BG RS BA XK MK AL ME HR SI HU SK CZ PL DE FR GB IE ES PT IT GR CY MT AT CH BE NL LU DK SE NO FI EE LV LT IS".split()
    )},
    # North America (incl. Central America & Caribbean)
    **{c: "north_america" for c in "US CA MX GT HN SV NI CR PA CU HT DO JM TT BS BZ".split()},
    # South America
    **{c: "south_america" for c in "CO VE EC PE BO BR PY UY AR CL GY SR".split()},
    # Oceania
    **{c: "oceania" for c in "AU NZ PG FJ SB VU WS TO".split()},
}

DESKS = ("africa", "asia", "europe", "north_america", "south_america", "oceania")

# The six analyst lenses deployed per desk. Diversity of lens, same rules:
# doubt only, cross-checks named, methodology respected.
LENSES: list[tuple[str, str]] = [
    ("source_criticism",
     "Scrutinise WHO reported each claim: originating vs citing source, institutional "
     "distance from the events, known editorial constraints. A credible publisher citing "
     "another dataset verifies nothing."),
    ("methodology",
     "Scrutinise HOW figures were produced: dataset methodologies (ACLED 'affected people', "
     "IPC phases, UNHCR registration vs estimates), unit confusion, double counting."),
    ("regional_context",
     "Scrutinise regional plausibility: does the claim fit known geography, actors, access "
     "constraints and seasonal patterns of this continent? Flag what only local sources could confirm."),
    ("corroboration",
     "Scrutinise independence of corroboration: do supporting reports trace back to a single "
     "upstream source? Name which PRIMARY dataset a human must check."),
    ("temporal_consistency",
     "Scrutinise timing: coverage periods vs publication dates, stale figures re-reported as "
     "current, trend claims built on incomparable windows."),
    ("humanitarian_impact",
     "Scrutinise impact claims: displacement, casualties and access figures against the "
     "methodology of their source; distinguish 'affected' from 'displaced' from 'targeted'."),
]


def desk_for(country_iso2: str) -> str | None:
    return COUNTRY_DESK.get(country_iso2.upper())


def group_by_desk(events: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for ev in events:
        desk = desk_for(ev.get("country", "")) or "unassigned"
        groups.setdefault(desk, []).append(ev)
    return groups
