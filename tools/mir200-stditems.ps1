param(
    [string]$DbPath = 'Mud2\DB\GEEM2.db',

    [switch]$Apply,

    [switch]$Check,

    [switch]$NoBackup,

    [string[]]$Names = @(),

    [string]$SpecPath
)

Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not [IO.Path]::IsPathRooted($DbPath)) {
    $DbPath = Join-Path $repoRoot $DbPath
}
$DbPath = (Resolve-Path -LiteralPath $DbPath).Path

if ($SpecPath) {
    if (-not [IO.Path]::IsPathRooted($SpecPath)) {
        $SpecPath = Join-Path $repoRoot $SpecPath
    }
    $SpecPath = (Resolve-Path -LiteralPath $SpecPath).Path
}

$python = @'
import argparse
import csv
import os
import shutil
import sqlite3
import sys
from datetime import datetime

LATE_PERSONAL_QUEST_ITEMS = [
    {"name": "雪域魂器残片", "template": "冰核", "note": "雪域章节剧情凭据"},
    {"name": "狐月引路符", "template": "火龙凭证", "note": "火龙章节完成后的狐月引路凭据"},
    {"name": "雪域寻魂", "template": "火龙勇士", "note": "雪域章节完成称号"},
    {"name": "火龙余烬", "template": "火龙勇士", "note": "火龙章节完成称号"},
    {"name": "狐月问道", "template": "登峰造极", "note": "后期个人奇遇终章称号"},
]

def load_items(spec_path):
    if not spec_path:
        return LATE_PERSONAL_QUEST_ITEMS

    items = []
    with open(spec_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"Name", "Template"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Spec missing columns: {', '.join(sorted(missing))}")
        for row in reader:
            name = (row.get("Name") or "").strip()
            template = (row.get("Template") or "").strip()
            note = (row.get("Note") or "").strip()
            if not name or not template:
                continue
            items.append({"name": name, "template": template, "note": note})
    if not items:
        raise SystemExit(f"Spec has no items: {spec_path}")
    return items

def connect(db_path):
    if not os.path.exists(db_path):
        raise SystemExit(f"DB not found: {db_path}")
    return sqlite3.connect(db_path)

def table_columns(conn):
    rows = conn.execute("PRAGMA table_info(StdItems)").fetchall()
    if not rows:
        raise SystemExit("StdItems table not found")
    return [row[1] for row in rows]

def row_by_name(conn, name, columns):
    row = conn.execute("SELECT * FROM StdItems WHERE Name=?", (name,)).fetchone()
    if row is None:
        return None
    return dict(zip(columns, row))

def print_rows(rows, columns):
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row.get(col, "") for col in columns])

def preview_or_apply(conn, db_path, items, apply, no_backup):
    columns = table_columns(conn)
    max_idx = conn.execute("SELECT COALESCE(MAX(Idx), 0) FROM StdItems").fetchone()[0]
    next_idx = max_idx + 1
    planned = []
    errors = []

    for item in items:
        target = row_by_name(conn, item["name"], columns)
        template = row_by_name(conn, item["template"], columns)
        if target is not None:
            planned.append({
                "status": "exists",
                "idx": target["Idx"],
                "name": item["name"],
                "template": item["template"],
                "note": item["note"],
            })
            continue
        if template is None:
            errors.append(f"missing template: {item['template']} for {item['name']}")
            continue
        planned.append({
            "status": "insert",
            "idx": next_idx,
            "name": item["name"],
            "template": item["template"],
            "note": item["note"],
        })
        next_idx += 1

    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["status", "idx", "name", "template", "note"])
    for row in planned:
        writer.writerow([row["status"], row["idx"], row["name"], row["template"], row["note"]])

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)

    inserts = [row for row in planned if row["status"] == "insert"]
    if not apply:
        print(f"PREVIEW only. Missing items to insert: {len(inserts)}")
        return

    if not inserts:
        print("No missing StdItems to insert.")
        return

    if not no_backup:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = f"{db_path}.bak-before-stditems-{timestamp}"
        shutil.copy2(db_path, backup_path)
        print(f"Backup: {backup_path}")

    placeholders = ",".join(["?"] * len(columns))
    sql = f"INSERT INTO StdItems ({','.join(columns)}) VALUES ({placeholders})"
    try:
        conn.execute("BEGIN")
        for row in inserts:
            template = row_by_name(conn, row["template"], columns)
            values = [template[col] for col in columns]
            values[columns.index("Idx")] = row["idx"]
            values[columns.index("Name")] = row["name"]
            conn.execute(sql, values)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    print(f"Inserted StdItems: {len(inserts)}")

def check(conn, items):
    columns = table_columns(conn)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["name", "exists", "idx", "stdmode", "looks", "template"])
    ok = True
    for item in items:
        row = row_by_name(conn, item["name"], columns)
        exists = row is not None
        ok = ok and exists
        writer.writerow([
            item["name"],
            "yes" if exists else "no",
            "" if row is None else row.get("Idx", ""),
            "" if row is None else row.get("StdMode", ""),
            "" if row is None else row.get("Looks", ""),
            item["template"],
        ])
    if not ok:
        raise SystemExit(2)

def list_names(conn, names):
    columns = table_columns(conn)
    rows = []
    for name in names:
        row = row_by_name(conn, name, columns)
        if row is not None:
            rows.append(row)
    basic = ["Idx", "Name", "StdMode", "Shape", "Weight", "Looks", "DuraMax", "Need", "NeedLevel", "Price", "Stock", "Color", "OverLap"]
    print_rows(rows, [col for col in basic if col in columns])
    if len(rows) != len(names):
        found = {row["Name"] for row in rows}
        for name in names:
            if name not in found:
                print(f"missing: {name}", file=sys.stderr)
        raise SystemExit(2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--name", action="append", default=[])
    parser.add_argument("--spec")
    args = parser.parse_args()

    conn = connect(args.db)
    try:
        items = load_items(args.spec)
        if args.name:
            list_names(conn, args.name)
        elif args.check:
            check(conn, items)
        else:
            preview_or_apply(conn, args.db, items, args.apply, args.no_backup)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
'@

$argsList = @('--db', $DbPath)
if ($Apply) { $argsList += '--apply' }
if ($Check) { $argsList += '--check' }
if ($NoBackup) { $argsList += '--no-backup' }
if ($SpecPath) {
    $argsList += '--spec'
    $argsList += $SpecPath
}
foreach ($name in $Names) {
    $argsList += '--name'
    $argsList += $name
}

& python -c $python @argsList
