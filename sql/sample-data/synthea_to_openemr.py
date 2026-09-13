#!/usr/bin/env python3
"""Convert Synthea's CSV export into OpenEMR seed SQL files.

Input: a Synthea `output/csv` directory (patients/encounters/conditions/
medications/allergies/immunizations .csv, from a run with
exporter.csv.export=true).

Output: numbered *.sql files written into this directory. They are loaded
automatically on a fresh install by the flex docker image's SQL_DATA_DRIVE
mechanism (docker/flex/utilities/devtoolsLibrary.source, sqlDataDrive()),
which imports every *.sql file here, alphabetically, against an empty
database on first boot. The numeric prefixes enforce load order: patients
before the tables that reference their pid, encounters before the tables
that reference an encounter number.

All identifying data originates from Synthea's synthetic population
generator (https://github.com/synthetichealth/synthea) — no real patient
data is used. SSNs are additionally remapped to the 900-xx-xxxx block
(never issued by SSA) as a belt-and-suspenders safety measure.

Regenerate with:
    docker run --rm -v "$PWD:/work" -w /work eclipse-temurin:17-jre \\
        java -jar synthea-with-dependencies.jar -c synthea.properties \\
        -p 100 --exporter.baseDirectory=/work/output Massachusetts
    python3 synthea_to_openemr.py output/csv
"""
import csv
import random
import re
import sys
from pathlib import Path

BATCH_SIZE = 200
DEFAULT_PROVIDER_SQL = "(SELECT id FROM users WHERE username = 'admin' LIMIT 1)"
DEFAULT_FACILITY_ID = 3  # seeded by sql/database.sql: 'Your Clinic Name Here'

OCCUPATIONS = [
    "Teacher", "Nurse", "Software Engineer", "Retired", "Accountant",
    "Electrician", "Sales Associate", "Chef", "Mechanic", "Manager",
    "Plumber", "Driver", "Consultant", "", "",
]
RACE_MAP = {
    "white": "white",
    "black": "black_or_afri_amer",
    "asian": "Asian",
    "native": "amer_ind_or_alaska_native",
    "other": "decline_to_specify",
}
ETHNICITY_MAP = {
    "hispanic": "hisp_or_latin",
    "nonhispanic": "not_hisp_or_latin",
}
MARITAL_MAP = {"M": "married", "S": "single", "D": "divorced", "W": "widowed", "": ""}
CLASS_CODE_MAP = {
    "ambulatory": "AMB", "wellness": "AMB", "outpatient": "AMB",
    "urgentcare": "AMB", "emergency": "EMER", "inpatient": "IMP",
    "snf": "IMP", "hospice": "IMP", "home": "HH", "virtual": "VR",
}

NAME_SUFFIX_RE = re.compile(r"\d+$")


def esc(value) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def esc_or_null(value):
    if value is None or value == "":
        return "NULL"
    return esc(value)


def clean_name(name: str) -> str:
    return NAME_SUFFIX_RE.sub("", name or "")


def iso_dt(value: str):
    """'2016-10-10T04:26:42Z' -> '2016-10-10 04:26:42'; '' -> None."""
    if not value:
        return None
    return value.rstrip("Z").replace("T", " ")


def iso_date(value: str):
    return value or None


def rand_phone(rng: random.Random) -> str:
    return f"({rng.randint(200, 989)}) 555-{rng.randint(0, 9999):04d}"


def fake_ssn(rng: random.Random) -> str:
    return f"900-{rng.randint(0, 99):02d}-{rng.randint(0, 9999):04d}"


def write_batched_insert(out, table: str, columns: str, rows: list[str]) -> None:
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i:i + BATCH_SIZE]
        out.write(f"INSERT INTO `{table}` ({columns}) VALUES\n")
        out.write(",\n".join(chunk) + ";\n")


def load_patients(csv_dir: Path):
    """Returns (pid_map, rows) where pid_map: synthea Id -> int pid."""
    pid_map = {}
    rows = []
    with open(csv_dir / "patients.csv", newline="", encoding="utf-8") as f:
        for i, rec in enumerate(csv.DictReader(f), start=1):
            pid_map[rec["Id"]] = i
            rows.append((i, rec))
    return pid_map, rows


def load_encounters(csv_dir: Path):
    """Returns (encounter_map, rows) where encounter_map: synthea Id -> int encounter#."""
    encounter_map = {}
    rows = []
    with open(csv_dir / "encounters.csv", newline="", encoding="utf-8") as f:
        for i, rec in enumerate(csv.DictReader(f), start=1):
            encounter_map[rec["Id"]] = i
            rows.append((i, rec))
    return encounter_map, rows


def gen_patients(csv_dir: Path, pid_map, patient_rows, out_path: Path) -> None:
    columns = (
        "`title`, `language`, `financial`, `fname`, `lname`, `mname`, `DOB`, `street`, "
        "`postal_code`, `city`, `state`, `ss`, `occupation`, `phone_home`, `phone_biz`, "
        "`phone_contact`, `phone_cell`, `status`, `date`, `sex`, `providerID`, `email`, "
        "`race`, `ethnicity`, `pubpid`, `pid`"
    )
    rows = []
    for pid, rec in patient_rows:
        rng = random.Random(20260913 + pid)
        fname = clean_name(rec["FIRST"])
        lname = clean_name(rec["LAST"])
        mname = clean_name(rec.get("MIDDLE", ""))
        sex = "Male" if rec["GENDER"] == "M" else "Female"
        occupation = "" if rec["BIRTHDATE"] >= "2008" else rng.choice(OCCUPATIONS)
        values = [
            esc(rec.get("PREFIX") or ""),
            esc("english"),
            esc(""),
            esc(fname),
            esc(lname),
            esc(mname),
            esc(rec["BIRTHDATE"]),
            esc(rec["ADDRESS"]),
            esc(rec["ZIP"]),
            esc(rec["CITY"]),
            esc("MA"),
            esc(fake_ssn(rng)),
            esc(occupation),
            esc(rand_phone(rng)),
            esc(rand_phone(rng)),
            esc(rand_phone(rng)),
            esc(rand_phone(rng)),
            esc(MARITAL_MAP.get(rec["MARITAL"], "")),
            esc("2024-06-01 00:00:00"),
            esc(sex),
            DEFAULT_PROVIDER_SQL,
            esc(f"{fname.lower()}.{lname.lower()}{pid}@example.test"),
            esc(RACE_MAP.get(rec["RACE"], "decline_to_specify")),
            esc(ETHNICITY_MAP.get(rec["ETHNICITY"], "not_hisp_or_latin")),
            esc(str(pid)),
            str(pid),
        ]
        rows.append("(" + ", ".join(values) + ")")

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(
            "-- Auto-generated from Synthea synthetic patient data. Do not edit by\n"
            "-- hand; regenerate with synthea_to_openemr.py. All names/DOBs/addresses\n"
            "-- are Synthea-fabricated; SSNs are remapped to the unissued 900-xx-xxxx\n"
            "-- block. No real person's information is used or referenced.\n"
        )
        out.write("SET FOREIGN_KEY_CHECKS=0;\n")
        write_batched_insert(out, "patient_data", columns, rows)
        out.write("SET FOREIGN_KEY_CHECKS=1;\n")


def gen_encounters(pid_map, encounter_rows, out_path: Path) -> None:
    fe_columns = (
        "`date`, `date_end`, `reason`, `facility`, `facility_id`, `pid`, `encounter`, "
        "`provider_id`, `pc_catid`, `class_code`, `encounter_type_description`"
    )
    forms_columns = "`date`, `encounter`, `form_name`, `form_id`, `pid`, `formdir`, `authorized`"

    fe_rows = []
    forms_rows = []
    skipped = 0
    for enc_num, rec in encounter_rows:
        pid = pid_map.get(rec["PATIENT"])
        if pid is None:
            skipped += 1
            continue
        reason = rec.get("REASONDESCRIPTION") or rec["DESCRIPTION"]
        class_code = CLASS_CODE_MAP.get(rec["ENCOUNTERCLASS"], "AMB")
        values = [
            esc(iso_dt(rec["START"])),
            esc_or_null(iso_dt(rec["STOP"])),
            esc(reason),
            esc("Your Clinic Name Here"),
            str(DEFAULT_FACILITY_ID),
            str(pid),
            str(enc_num),
            DEFAULT_PROVIDER_SQL,
            "5",
            esc(class_code),
            esc(rec["DESCRIPTION"]),
        ]
        fe_rows.append("(" + ", ".join(values) + ")")

        form_values = [
            esc(iso_dt(rec["START"])),
            str(enc_num),
            esc("New Encounter Form"),
            f"(SELECT id FROM form_encounter WHERE pid = {pid} AND encounter = {enc_num} LIMIT 1)",
            str(pid),
            esc("newpatient"),
            "1",
        ]
        forms_rows.append("(" + ", ".join(form_values) + ")")

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(
            "-- Auto-generated from Synthea synthetic encounter data. Do not edit by\n"
            "-- hand; regenerate with synthea_to_openemr.py.\n"
        )
        if skipped:
            out.write(f"-- Note: {skipped} encounter(s) skipped (unmapped patient).\n")
        out.write("SET FOREIGN_KEY_CHECKS=0;\n")
        write_batched_insert(out, "form_encounter", fe_columns, fe_rows)
        write_batched_insert(out, "forms", forms_columns, forms_rows)
        out.write("SET FOREIGN_KEY_CHECKS=1;\n")


def gen_problems(csv_dir: Path, pid_map, encounter_map, out_path: Path) -> None:
    columns = (
        "`date`, `type`, `title`, `diagnosis`, `begdate`, `enddate`, `activity`, `pid`"
    )
    rows = []
    with open(csv_dir / "conditions.csv", newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            pid = pid_map.get(rec["PATIENT"])
            if pid is None:
                continue
            active = 0 if rec["STOP"] else 1
            values = [
                esc(rec["START"]),
                esc("medical_problem"),
                esc(rec["DESCRIPTION"]),
                esc(f"SNOMED-CT:{rec['CODE']}"),
                esc(rec["START"]),
                esc_or_null(rec["STOP"]),
                str(active),
                str(pid),
            ]
            rows.append("(" + ", ".join(values) + ")")

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(
            "-- Auto-generated from Synthea synthetic condition data. Do not edit by\n"
            "-- hand; regenerate with synthea_to_openemr.py.\n"
        )
        out.write("SET FOREIGN_KEY_CHECKS=0;\n")
        write_batched_insert(out, "lists", columns, rows)
        out.write("SET FOREIGN_KEY_CHECKS=1;\n")


def gen_allergies(csv_dir: Path, pid_map, out_path: Path) -> None:
    columns = (
        "`date`, `type`, `title`, `diagnosis`, `begdate`, `enddate`, `activity`, "
        "`reaction`, `severity_al`, `pid`"
    )
    rows = []
    with open(csv_dir / "allergies.csv", newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            pid = pid_map.get(rec["PATIENT"])
            if pid is None:
                continue
            active = 0 if rec["STOP"] else 1
            reaction = rec.get("DESCRIPTION1") or ""
            severity = (rec.get("SEVERITY1") or "").capitalize()
            values = [
                esc(rec["START"]),
                esc("allergy"),
                esc(rec["DESCRIPTION"]),
                esc(f"SNOMED-CT:{rec['CODE']}"),
                esc(rec["START"]),
                esc_or_null(rec["STOP"]),
                str(active),
                esc(reaction),
                esc_or_null(severity),
                str(pid),
            ]
            rows.append("(" + ", ".join(values) + ")")

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(
            "-- Auto-generated from Synthea synthetic allergy data. Do not edit by\n"
            "-- hand; regenerate with synthea_to_openemr.py.\n"
        )
        out.write("SET FOREIGN_KEY_CHECKS=0;\n")
        write_batched_insert(out, "lists", columns, rows)
        out.write("SET FOREIGN_KEY_CHECKS=1;\n")


def gen_medications(csv_dir: Path, pid_map, encounter_map, out_path: Path) -> None:
    columns = (
        "`patient_id`, `provider_id`, `encounter`, `start_date`, `end_date`, `drug`, "
        "`rxnorm_drugcode`, `active`, `txDate`, `usage_category_title`, `request_intent_title`"
    )
    rows = []
    with open(csv_dir / "medications.csv", newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            pid = pid_map.get(rec["PATIENT"])
            if pid is None:
                continue
            encounter = encounter_map.get(rec["ENCOUNTER"])
            start_date = (rec["START"] or "")[:10]
            end_date = (rec["STOP"] or "")[:10]
            active = 0 if end_date else 1
            values = [
                str(pid),
                DEFAULT_PROVIDER_SQL,
                esc_or_null(encounter),
                esc(start_date),
                esc_or_null(end_date),
                esc(rec["DESCRIPTION"][:150]),
                esc(rec["CODE"]),
                str(active),
                esc(start_date),
                esc(""),
                esc(""),
            ]
            rows.append("(" + ", ".join(values) + ")")

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(
            "-- Auto-generated from Synthea synthetic medication data. Do not edit by\n"
            "-- hand; regenerate with synthea_to_openemr.py.\n"
        )
        out.write("SET FOREIGN_KEY_CHECKS=0;\n")
        write_batched_insert(out, "prescriptions", columns, rows)
        out.write("SET FOREIGN_KEY_CHECKS=1;\n")


def gen_immunizations(csv_dir: Path, pid_map, encounter_map, out_path: Path) -> None:
    columns = (
        "`patient_id`, `administered_date`, `cvx_code`, `note`, `create_date`, "
        "`update_date`, `encounter_id`"
    )
    rows = []
    with open(csv_dir / "immunizations.csv", newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            pid = pid_map.get(rec["PATIENT"])
            if pid is None:
                continue
            encounter = encounter_map.get(rec["ENCOUNTER"])
            administered = iso_dt(rec["DATE"])
            values = [
                str(pid),
                esc(administered),
                esc(rec["CODE"]),
                esc(rec["DESCRIPTION"]),
                esc(administered),
                esc("2024-06-01 00:00:00"),  # update_date is TIMESTAMP; avoid pre-1970 overflow
                esc_or_null(encounter),
            ]
            rows.append("(" + ", ".join(values) + ")")

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(
            "-- Auto-generated from Synthea synthetic immunization data. Do not edit by\n"
            "-- hand; regenerate with synthea_to_openemr.py.\n"
        )
        out.write("SET FOREIGN_KEY_CHECKS=0;\n")
        write_batched_insert(out, "immunizations", columns, rows)
        out.write("SET FOREIGN_KEY_CHECKS=1;\n")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <synthea-output/csv-dir>", file=sys.stderr)
        sys.exit(1)

    csv_dir = Path(sys.argv[1])
    out_dir = Path(__file__).parent

    pid_map, patient_rows = load_patients(csv_dir)
    encounter_map, encounter_rows = load_encounters(csv_dir)

    gen_patients(csv_dir, pid_map, patient_rows, out_dir / "0001_patients.sql")
    gen_encounters(pid_map, encounter_rows, out_dir / "0002_encounters.sql")
    gen_problems(csv_dir, pid_map, encounter_map, out_dir / "0003_problems.sql")
    gen_allergies(csv_dir, pid_map, out_dir / "0004_allergies.sql")
    gen_medications(csv_dir, pid_map, encounter_map, out_dir / "0005_medications.sql")
    gen_immunizations(csv_dir, pid_map, encounter_map, out_dir / "0006_immunizations.sql")

    print(f"{len(patient_rows)} patients, {len(encounter_rows)} encounters written.")


if __name__ == "__main__":
    main()
