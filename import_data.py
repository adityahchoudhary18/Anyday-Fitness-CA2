"""Load the supplied Anyday Fitness CA1 CSV dataset into MySQL."""

import os
import sys
from pathlib import Path

import pandas as pd
import mysql.connector
from mysql.connector import Error

CSV_PATH = Path(__file__).resolve().parent / "data" / "ANYDAY_FITNESS.csv"
REQUIRED_COLUMNS = {
    "member_id", "member_name", "gender", "birthday", "Age",
    "membership_type", "visit_per_week", "days_per_week",
    "attend_group_lesson", "fav_group_lesson", "check_in_time",
    "check_out_time", "avg_time_in_gym_min", "drink_addon",
    "fav_drink", "personal_training", "trainer_name", "uses_sauna",
}


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gym_data"),
    )


def split_values(value):
    if pd.isna(value) or str(value).strip() == "":
        return []
    return list(dict.fromkeys(part.strip() for part in str(value).split(",") if part.strip()))


def as_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Invalid Boolean value in source data: {value!r}")


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    data = pd.read_csv(CSV_PATH)
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(f"The CSV is missing required columns: {', '.join(sorted(missing))}")
    if data["member_id"].duplicated().any():
        raise ValueError("The CSV contains duplicate member IDs. Resolve duplicates before importing.")

    connection = get_connection()
    cursor = connection.cursor()
    try:
        # This reset is intentional: the source CSV becomes the initial CA2 dataset.
        # Run this script before entering new records; rerunning it replaces current data.
        cursor.execute("DELETE FROM member_days")
        cursor.execute("DELETE FROM member_favorite_lessons")
        cursor.execute("DELETE FROM member_favorite_drinks")
        cursor.execute("DELETE FROM members")

        member_sql = """
            INSERT INTO members
            (member_id, member_name, gender, birthday, age, membership_type,
             visit_per_week, attend_group_lesson, check_in_time, check_out_time,
             avg_time_in_gym_min, drink_addon, personal_training, trainer_name, uses_sauna)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        day_sql = "INSERT INTO member_days (member_id, day_name) VALUES (%s, %s)"
        lesson_sql = "INSERT INTO member_favorite_lessons (member_id, lesson_name) VALUES (%s, %s)"
        drink_sql = "INSERT INTO member_favorite_drinks (member_id, drink_name) VALUES (%s, %s)"

        for _, row in data.iterrows():
            member_id = int(row["member_id"])
            cursor.execute(member_sql, (
                member_id,
                str(row["member_name"]).strip(),
                str(row["gender"]).strip(),
                pd.to_datetime(row["birthday"], errors="raise").date(),
                int(row["Age"]),
                str(row["membership_type"]).strip(),
                int(row["visit_per_week"]),
                as_bool(row["attend_group_lesson"]),
                str(row["check_in_time"]),
                str(row["check_out_time"]),
                int(row["avg_time_in_gym_min"]),
                as_bool(row["drink_addon"]),
                as_bool(row["personal_training"]),
                None if pd.isna(row["trainer_name"]) else str(row["trainer_name"]).strip(),
                as_bool(row["uses_sauna"]),
            ))
            cursor.executemany(day_sql, [(member_id, value) for value in split_values(row["days_per_week"])])
            cursor.executemany(lesson_sql, [(member_id, value) for value in split_values(row["fav_group_lesson"])])
            cursor.executemany(drink_sql, [(member_id, value) for value in split_values(row["fav_drink"])])

        connection.commit()
        cursor.execute("SELECT COUNT(*) FROM members")
        imported_count = cursor.fetchone()[0]
        print(f"Import completed. Member records in gym_data.members: {imported_count}.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except (Error, Exception) as error:
        print(f"Import failed: {error}")
        sys.exit(1)
