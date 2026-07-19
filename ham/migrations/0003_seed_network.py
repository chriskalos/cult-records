import datetime
from decimal import Decimal

from django.db import migrations


ASSETS = [
    {
        "asset_code": "HAM-ATH-042",
        "name": "Adrian Voss",
        "alias": "Latchkey",
        "status": "active",
        "location_label": "Athens, Greece",
        "latitude": Decimal("37.983800"),
        "longitude": Decimal("23.727500"),
        "portrait": "ham/images/assets/adrian-voss.webp",
        "network_role": "Maintains short-range dead drops and very long receipts",
        "civilian_cover": "Emergency locksmith for doors that were already open",
        "joined_on": datetime.date(2018, 4, 2),
        "last_contact": datetime.date(2026, 7, 17),
        "consensus": "majority",
        "exposure": "low",
        "summary": "A patient logistics node with an unusual ability to arrive after an event but before anybody notices it happened.",
        "network_notes": "Voss keeps three left gloves in separate municipal lockers. The network voted twice not to ask about the corresponding hands.",
        "known_irregularity": "Every key copied by this node opens one additional, unrelated cupboard.",
    },
    {
        "asset_code": "HAM-DUB-017",
        "name": "Milo Quarry",
        "alias": "Best Man",
        "status": "active",
        "location_label": "Dublin, Ireland",
        "latitude": Decimal("53.349800"),
        "longitude": Decimal("-6.260300"),
        "portrait": "ham/images/assets/milo-quarry.webp",
        "network_role": "Resolves inter-node disputes by inventing a third position",
        "civilian_cover": "Wedding DJ specializing in ceremonies with no confirmed couple",
        "joined_on": datetime.date(2021, 9, 19),
        "last_contact": datetime.date(2026, 7, 16),
        "consensus": "split",
        "exposure": "moderate",
        "summary": "A cheerful mediator whose proposed compromises are normally worse than either original problem.",
        "network_notes": "Maintains a portable fog machine for negotiations. Claims it helps everyone see the issue more clearly.",
        "known_irregularity": "Has attended 63 weddings. Records indicate only 11 marriages.",
    },
    {
        "asset_code": "HAM-TYO-006",
        "name": "Kenji Mori",
        "alias": "Exact Change",
        "status": "silent",
        "location_label": "Tokyo, Japan",
        "latitude": Decimal("35.676200"),
        "longitude": Decimal("139.650300"),
        "portrait": "ham/images/assets/kenji-mori.webp",
        "network_role": "Transfers sealed messages through unattended vending machines",
        "civilian_cover": "Freelance vending machine taxonomist",
        "joined_on": datetime.date(2020, 2, 29),
        "last_contact": datetime.date(2026, 7, 9),
        "consensus": "unanimous",
        "exposure": "paperwork",
        "summary": "A silent courier trusted by every node except the beverage procurement circle, which no longer recognizes HAM authority.",
        "network_notes": "Mori classifies machines by temperament rather than contents. Category VI machines are not to be approached while humming.",
        "known_irregularity": "Always receives exact change, including from machines that do not accept cash.",
    },
    {
        "asset_code": "HAM-PRG-088",
        "name": "Tomasz Bell",
        "alias": "Carbon Copy",
        "status": "active",
        "location_label": "Prague, Czechia",
        "latitude": Decimal("50.075500"),
        "longitude": Decimal("14.437800"),
        "portrait": "ham/images/assets/tomasz-bell.webp",
        "network_role": "Produces convincing paper trails for events that remain undecided",
        "civilian_cover": "Municipal archive humidity consultant",
        "joined_on": datetime.date(2016, 11, 8),
        "last_contact": datetime.date(2026, 7, 18),
        "consensus": "majority",
        "exposure": "low",
        "summary": "A documentary specialist who treats bureaucracy as both shield and competitive sport.",
        "network_notes": "Bell owns 44 rubber stamps. Thirty-nine say NO. The other five also say NO but in a friendlier typeface.",
        "known_irregularity": "His carbon copies occasionally precede the original by several days.",
    },
    {
        "asset_code": "HAM-LON-031",
        "name": "Mara Lorne",
        "alias": "Switchboard",
        "status": "misplaced",
        "location_label": "London, United Kingdom",
        "latitude": Decimal("51.507400"),
        "longitude": Decimal("-0.127800"),
        "portrait": "ham/images/assets/mara-lorne.webp",
        "network_role": "Routes low-bandwidth signals between nodes that refuse to speak",
        "civilian_cover": "Wholesale buyer for an aquarium gift shop",
        "joined_on": datetime.date(2019, 6, 14),
        "last_contact": datetime.date(2026, 7, 1),
        "consensus": "one_guy",
        "exposure": "severe",
        "summary": "An analogue communications specialist last observed entering a telephone exchange that has been a sandwich shop since 1998.",
        "network_notes": "Claims to have trained one eel to recognize fax tones. No node has been willing to verify the eel's employment status.",
        "known_irregularity": "Outgoing calls from her desk are answered by the same sandwich shop, regardless of number dialled.",
    },
    {
        "asset_code": "HAM-MEX-073",
        "name": "Nadia Serrano",
        "alias": "Four Centimetres",
        "status": "active",
        "location_label": "Mexico City, Mexico",
        "latitude": Decimal("19.432600"),
        "longitude": Decimal("-99.133200"),
        "portrait": "ham/images/assets/nadia-serrano.webp",
        "network_role": "Acquires ordinary objects in operationally unreasonable quantities",
        "civilian_cover": "Independent chair ergonomics consultant",
        "joined_on": datetime.date(2022, 3, 4),
        "last_contact": datetime.date(2026, 7, 18),
        "consensus": "unanimous",
        "exposure": "moderate",
        "summary": "A procurement node responsible for umbrellas, extension leads, and most of the network's unexplained folding chairs.",
        "network_notes": "Every chair in Serrano's vicinity is moved exactly four centimetres to the left. Compass direction appears irrelevant.",
        "known_irregularity": "Invoices list a delivery address that translates to 'behind you.'",
    },
    {
        "asset_code": "HAM-SIN-014",
        "name": "Leena Rao",
        "alias": "Checksum",
        "status": "active",
        "location_label": "Singapore",
        "latitude": Decimal("1.352100"),
        "longitude": Decimal("103.819800"),
        "portrait": "ham/images/assets/leena-rao.webp",
        "network_role": "Verifies whether network messages have remained mostly themselves",
        "civilian_cover": "Night manager at a hotel with an indoor botanical garden",
        "joined_on": datetime.date(2017, 8, 21),
        "last_contact": datetime.date(2026, 7, 18),
        "consensus": "majority",
        "exposure": "low",
        "summary": "A verification node with an excellent memory for altered details and no patience for cryptographic enthusiasm.",
        "network_notes": "Rao authenticates urgent messages by comparing the temperature of two soups. The method has never failed and cannot be explained.",
        "known_irregularity": "Hotel guests sometimes check out three minutes before they check in.",
    },
    {
        "asset_code": "HAM-SAO-055",
        "name": "Mateo Cairn",
        "alias": "The Audience",
        "status": "disputed",
        "location_label": "São Paulo, Brazil",
        "latitude": Decimal("-23.550500"),
        "longitude": Decimal("-46.633300"),
        "portrait": "ham/images/assets/mateo-cairn.webp",
        "network_role": "Operates decoys, counter-decoys, and one decoy for the decoys",
        "civilian_cover": "Examiner for municipal mime licences",
        "joined_on": datetime.date(2015, 5, 5),
        "last_contact": datetime.date(2025, 12, 31),
        "consensus": "split",
        "exposure": "paperwork",
        "summary": "A counter-observation specialist whose existence is supported by photographs, invoices, and several emphatic pigeons.",
        "network_notes": "Half the network believes Cairn is three people sharing one coat. The other half disputes the existence of the coat.",
        "known_irregularity": "His shadow has repeatedly been observed leaving performances early.",
    },
    {
        "asset_code": "HAM-LAG-029",
        "name": "Amara Okafor",
        "alias": "Soft Sector",
        "status": "active",
        "location_label": "Lagos, Nigeria",
        "latitude": Decimal("6.524400"),
        "longitude": Decimal("3.379200"),
        "portrait": "ham/images/assets/amara-okafor.webp",
        "network_role": "Maintains digital dead drops on obsolete physical media",
        "civilian_cover": "Composer of legally distinct elevator music",
        "joined_on": datetime.date(2018, 10, 12),
        "last_contact": datetime.date(2026, 7, 18),
        "consensus": "unanimous",
        "exposure": "moderate",
        "summary": "A storage specialist who distributes sensitive files on formats most investigators are too young to recognize.",
        "network_notes": "Okafor labels every floppy disk 'holiday photos.' This remains convincing because nobody has found a compatible drive.",
        "known_irregularity": "Her compositions are audible only between the second and third floors.",
    },
    {
        "asset_code": "HAM-REK-009",
        "name": "Ingrid Morrow",
        "alias": "Fair Weather",
        "status": "silent",
        "location_label": "Reykjavík, Iceland",
        "latitude": Decimal("64.146600"),
        "longitude": Decimal("-21.942600"),
        "portrait": "ham/images/assets/ingrid-morrow.webp",
        "network_role": "Provides meteorological deniability for outdoor operations",
        "civilian_cover": "Lighthouse inventory auditor",
        "joined_on": datetime.date(2014, 1, 23),
        "last_contact": datetime.date(2026, 6, 30),
        "consensus": "majority",
        "exposure": "low",
        "summary": "A weather observer whose reports prioritize operational morale over atmospheric accuracy.",
        "network_notes": "Morrow has reported clear skies during nine storms and one indoor plumbing failure. Forecast success remains statistically contested.",
        "known_irregularity": "Rain stops directly above her clipboard and resumes underneath it.",
    },
    {
        "asset_code": "HAM-VAN-001",
        "name": "Edith Pike",
        "alias": "Tuesday",
        "status": "disputed",
        "location_label": "Vancouver, Canada",
        "latitude": Decimal("49.282700"),
        "longitude": Decimal("-123.120700"),
        "portrait": "ham/images/assets/edith-pike.webp",
        "network_role": "Retains institutional memory after institutions deny being involved",
        "civilian_cover": "Retired, according to four incompatible pension systems",
        "joined_on": datetime.date(1987, 7, 7),
        "last_contact": datetime.date(2026, 7, 15),
        "consensus": "one_guy",
        "exposure": "severe",
        "summary": "The network's oldest documented node, although Pike contests both 'oldest' and 'documented.'",
        "network_notes": "Pike refuses to recognize Tuesdays. Network calendars skip directly from Monday evening to Wednesday lunch when she is connected.",
        "known_irregularity": "Appears in meeting minutes from six years before her recorded birth.",
    },
    {
        "asset_code": "HAM-MEL-064",
        "name": "Jules Tan",
        "alias": "Stationery Emergency",
        "status": "on_break",
        "location_label": "Melbourne, Australia",
        "latitude": Decimal("-37.813600"),
        "longitude": Decimal("144.963100"),
        "portrait": "ham/images/assets/jules-tan.webp",
        "network_role": "Supplies emergency office materials during non-office emergencies",
        "civilian_cover": "Regional buyer for a stationery cooperative",
        "joined_on": datetime.date(2023, 4, 1),
        "last_contact": datetime.date(2026, 7, 18),
        "consensus": "unanimous",
        "exposure": "paperwork",
        "summary": "A rapid-response supply node responsible for twelve staplers, one laminator, and an event nobody will describe.",
        "network_notes": "Tan's break began 47 minutes ago and is expected to end retroactively. Operational continuity is unaffected.",
        "known_irregularity": "Stapled documents gain a blank page that was not present beforehand.",
    },
]


OBSERVATIONS = [
    ("OBS-2026-0718-A", "HAM-PRG-088", datetime.date(2026, 7, 18), "routine", "Received 300 correctly filed denials for requests the network has not made yet."),
    ("OBS-2026-0718-B", "HAM-MEX-073", datetime.date(2026, 7, 18), "admin", "Fourteen chairs adjusted. Room still appears centred. Further measurements suspended."),
    ("OBS-2026-0718-C", "HAM-LAG-029", datetime.date(2026, 7, 18), "routine", "Package received on one 3.5-inch disk and a smaller disk nobody recognizes."),
    ("OBS-2026-0717-A", "HAM-ATH-042", datetime.date(2026, 7, 17), "warning", "Locker 19 contained four left gloves. Consensus protocol permits three."),
    ("OBS-2026-0716-A", "HAM-DUB-017", datetime.date(2026, 7, 16), "admin", "Dispute resolved. All three resulting parties are unhappy, indicating procedural success."),
    ("OBS-2026-0715-A", "HAM-VAN-001", datetime.date(2026, 7, 15), "disputed", "Node rejected the date supplied by the network. The network has provisionally rejected Tuesday."),
    ("OBS-2026-0709-A", "HAM-TYO-006", datetime.date(2026, 7, 9), "warning", "Category VI vending unit observed humming in B-flat. Exact Change has suspended contact."),
    ("OBS-2026-0701-A", "HAM-LON-031", datetime.date(2026, 7, 1), "warning", "Asset entered former telephone exchange carrying one sandwich and no visible eel."),
    ("OBS-2026-0630-A", "HAM-REK-009", datetime.date(2026, 6, 30), "routine", "Forecast reported as pleasant. Three boats subsequently found in a car park."),
    ("OBS-2025-1231-A", "HAM-SAO-055", datetime.date(2025, 12, 31), "disputed", "Photograph contains Cairn, two plausible substitutes, and a shadow facing the wrong direction."),
]


DIRECTIVES = [
    {
        "code": "DIR-004CM",
        "priority": "important",
        "instruction": "Move the nearest unoccupied chair four centimetres to the left.",
        "rationale": "No reason has achieved network consensus. This is not the same as having no reason.",
        "status_line": "Compliance estimated at 61%. Furniture remains evasive.",
        "position": 1,
    },
    {
        "code": "DIR-UMBR-7",
        "priority": "routine",
        "instruction": "Acquire seven identical black umbrellas. Open only the sixth.",
        "rationale": "The seventh umbrella is a control umbrella. The first five are emotional support umbrellas.",
        "status_line": "Procurement delegated to nobody in particular.",
        "position": 2,
    },
    {
        "code": "DIR-PGN-04",
        "priority": "absolute",
        "instruction": "Verify that pigeon number four remains a pigeon.",
        "rationale": "Previous verification used circular reasoning and a breadcrumb conflict of interest.",
        "status_line": "Species confirmation overdue by 19 days.",
        "position": 3,
    },
    {
        "code": "DIR-SPN-00",
        "priority": "whenever",
        "instruction": "If a teaspoon is found standing upright, leave the room in a professional manner.",
        "rationale": "Running created unnecessary questions during Incident CUTLERY-9.",
        "status_line": "No upright teaspoons currently acknowledged.",
        "position": 4,
    },
]


ARCHIVE = [
    {
        "code": "ARC-SPOON-9",
        "title": "The Spoon Protocol",
        "classification": "Utensil-sensitive",
        "filed_on": datetime.date(2024, 2, 29),
        "summary": "Standing guidance for cutlery displaying initiative.",
        "excerpt": "At 09:14 the teaspoon achieved a vertical posture without visible support. The room responded inconsistently but with excellent punctuality.",
        "redaction_level": 2,
    },
    {
        "code": "ARC-MTG-NULL",
        "title": "Minutes from the Meeting Nobody Hosted",
        "classification": "Consensus-adjacent",
        "filed_on": datetime.date(2023, 11, 6),
        "summary": "A complete record of attendance, motions, and biscuits from an unacknowledged meeting.",
        "excerpt": "All seventeen absent members voted in favour. The motion failed due to insufficient chairs.",
        "redaction_level": 4,
    },
    {
        "code": "ARC-GOAT-12",
        "title": "Unscheduled Goat Containment Review",
        "classification": "Agricultural-ish",
        "filed_on": datetime.date(2022, 8, 12),
        "summary": "Review of containment performance despite no approved goat operation.",
        "excerpt": "The goat was contained in the sense that all observers agreed it was somewhere on Earth. Stricter definitions remain under review.",
        "redaction_level": 1,
    },
    {
        "code": "ARC-FAX-ALIVE",
        "title": "Can a Fax Machine Hold a Grudge?",
        "classification": "Technically inconclusive",
        "filed_on": datetime.date(2019, 4, 17),
        "summary": "Longitudinal study of one office machine and its escalating personal correspondence.",
        "excerpt": "The machine printed 'I KNOW' for the fifth consecutive morning. Toner replacement did not improve its disposition.",
        "redaction_level": 3,
    },
]


def seed_network(apps, schema_editor):
    HumanAsset = apps.get_model("ham", "HumanAsset")
    AssetObservation = apps.get_model("ham", "AssetObservation")
    Directive = apps.get_model("ham", "Directive")
    ArchiveDocument = apps.get_model("ham", "ArchiveDocument")

    HumanAsset.objects.bulk_create(HumanAsset(**asset) for asset in ASSETS)
    assets = HumanAsset.objects.in_bulk(field_name="asset_code")
    AssetObservation.objects.bulk_create(
        AssetObservation(
            reference=reference,
            asset=assets[asset_code],
            observed_on=observed_on,
            kind=kind,
            summary=summary,
        )
        for reference, asset_code, observed_on, kind, summary in OBSERVATIONS
    )
    Directive.objects.bulk_create(Directive(**directive) for directive in DIRECTIVES)
    ArchiveDocument.objects.bulk_create(
        ArchiveDocument(**document) for document in ARCHIVE
    )


def remove_network(apps, schema_editor):
    apps.get_model("ham", "AssetObservation").objects.filter(
        reference__in=[item[0] for item in OBSERVATIONS]
    ).delete()
    apps.get_model("ham", "HumanAsset").objects.filter(
        asset_code__in=[item["asset_code"] for item in ASSETS]
    ).delete()
    apps.get_model("ham", "Directive").objects.filter(
        code__in=[item["code"] for item in DIRECTIVES]
    ).delete()
    apps.get_model("ham", "ArchiveDocument").objects.filter(
        code__in=[item["code"] for item in ARCHIVE]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("ham", "0002_network_records")]

    operations = [migrations.RunPython(seed_network, remove_network)]
