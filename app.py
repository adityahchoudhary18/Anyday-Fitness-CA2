"""Anyday Fitness Management System | MKT322 CA2
Streamlit frontend connected to a MySQL database.
"""

import os
from datetime import date, time, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
import mysql.connector
from mysql.connector import Error

st.set_page_config(
    page_title="Anyday Fitness | Management System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)



# -----------------------------------------------------------------------------
# Database connection and data access
# -----------------------------------------------------------------------------

def database_config():
    """Read database credentials from Streamlit secrets or environment values."""
    try:
        config = st.secrets["mysql"]
        return {
            "host": config["host"],
            "port": int(config.get("port", 4000)),
            "user": config["user"],
            "password": config["password"],
            "database": config.get("database", "gym_data"),
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
        }
    except (KeyError, FileNotFoundError, AttributeError):
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "gym_data"),
        }

def get_connection():
    return mysql.connector.connect(**database_config())

def check_database_server():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE(), VERSION()")
        result = cursor.fetchone()
        cursor.close()
        return result
    finally:
        connection.close()


def read_query(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description] if cursor.description else []
        return pd.DataFrame(rows, columns=columns)
    finally:
        cursor.close()
        connection.close()


def execute_transaction(member_query, member_values, member_id=None,
                         days=None, lessons=None, drinks=None, insert=False):
    """Save a member and related preference records in one transaction."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(member_query, member_values)
        saved_id = cursor.lastrowid if insert else member_id
        if not insert:
            for table in ("member_days", "member_favorite_lessons", "member_favorite_drinks"):
                cursor.execute(f"DELETE FROM {table} WHERE member_id = %s", (saved_id,))

        cursor.executemany(
            "INSERT INTO member_days (member_id, day_name) VALUES (%s, %s)",
            [(saved_id, value) for value in (days or [])],
        )
        cursor.executemany(
            "INSERT INTO member_favorite_lessons (member_id, lesson_name) VALUES (%s, %s)",
            [(saved_id, value) for value in (lessons or [])],
        )
        cursor.executemany(
            "INSERT INTO member_favorite_drinks (member_id, drink_name) VALUES (%s, %s)",
            [(saved_id, value) for value in (drinks or [])],
        )
        connection.commit()
        return saved_id
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_member(member_id):
    result = read_query("""
        SELECT m.*,
            (SELECT GROUP_CONCAT(day_name ORDER BY FIELD(day_name,'Mon','Tue','Wed','Thu','Fri','Sat','Sun') SEPARATOR ', ')
             FROM member_days d WHERE d.member_id = m.member_id) AS days_per_week,
            (SELECT GROUP_CONCAT(lesson_name ORDER BY lesson_name SEPARATOR ', ')
             FROM member_favorite_lessons l WHERE l.member_id = m.member_id) AS fav_group_lesson,
            (SELECT GROUP_CONCAT(drink_name ORDER BY drink_name SEPARATOR ', ')
             FROM member_favorite_drinks f WHERE f.member_id = m.member_id) AS fav_drink
        FROM members m
        WHERE m.member_id = %s
    """, (member_id,))
    return None if result.empty else result.iloc[0].to_dict()


def load_members():
    return read_query("""
        SELECT m.*,
            (SELECT GROUP_CONCAT(day_name ORDER BY FIELD(day_name,'Mon','Tue','Wed','Thu','Fri','Sat','Sun') SEPARATOR ', ')
             FROM member_days d WHERE d.member_id = m.member_id) AS days_per_week,
            (SELECT GROUP_CONCAT(lesson_name ORDER BY lesson_name SEPARATOR ', ')
             FROM member_favorite_lessons l WHERE l.member_id = m.member_id) AS fav_group_lesson,
            (SELECT GROUP_CONCAT(drink_name ORDER BY drink_name SEPARATOR ', ')
             FROM member_favorite_drinks f WHERE f.member_id = m.member_id) AS fav_drink
        FROM members m
        ORDER BY m.member_id
    """)


def split_values(value):
    if value is None or pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def mysql_time_to_time(value):
    """Convert MySQL TIME values (which may arrive as timedeltas) to datetime.time."""
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        seconds = int(value.total_seconds()) % 86400
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return time(hours, minutes, seconds)
    if value is None or pd.isna(value):
        return time(18, 0)
    text = str(value)
    if "day" in text:
        value = pd.to_timedelta(text)
        return mysql_time_to_time(value)
    return pd.to_datetime(text).time()


def clean_optional_text(value):
    return value.strip() or None


def validate_member(name, age, visits, duration):
    if not name.strip():
        raise ValueError("Enter the member's name.")
    if not 1 <= int(age) <= 120:
        raise ValueError("Age must be between 1 and 120.")
    if not 0 <= int(visits) <= 7:
        raise ValueError("Visits per week must be between 0 and 7.")
    if not 0 <= int(duration) <= 600:
        raise ValueError("Average gym time must be between 0 and 600 minutes.")


def member_values(name, gender, birthday, age, membership, visits, attends_lessons,
                  check_in, check_out, duration, drink_addon, personal_training,
                  trainer, sauna):
    validate_member(name, age, visits, duration)
    return (
        name.strip(), gender, birthday, int(age), membership, int(visits),
        bool(attends_lessons), check_in, check_out, int(duration),
        bool(drink_addon), bool(personal_training), clean_optional_text(trainer),
        bool(sauna),
    )


def create_member(values, days, lessons, drinks):
    query = """
        INSERT INTO members
        (member_name, gender, birthday, age, membership_type, visit_per_week,
         attend_group_lesson, check_in_time, check_out_time, avg_time_in_gym_min,
         drink_addon, personal_training, trainer_name, uses_sauna)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    return execute_transaction(query, values, days=days, lessons=lessons,
                               drinks=drinks, insert=True)


def update_member(member_id, values, days, lessons, drinks):
    query = """
        UPDATE members SET
            member_name=%s, gender=%s, birthday=%s, age=%s,
            membership_type=%s, visit_per_week=%s, attend_group_lesson=%s,
            check_in_time=%s, check_out_time=%s, avg_time_in_gym_min=%s,
            drink_addon=%s, personal_training=%s, trainer_name=%s, uses_sauna=%s
        WHERE member_id=%s
    """
    execute_transaction(query, values + (member_id,), member_id=member_id,
                        days=days, lessons=lessons, drinks=drinks)


def delete_member(member_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM members WHERE member_id = %s", (member_id,))
        if cursor.rowcount == 0:
            raise ValueError("No member record was found for the selected ID.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


# -----------------------------------------------------------------------------
# User interface
# -----------------------------------------------------------------------------

st.title("Anyday Fitness Management System")
st.caption("Member records, operational indicators and management tools")
st.divider()

try:
    members = load_members()
    navigation = st.sidebar.radio(
        "Main menu",
        ["Dashboard", "View Members", "Add Member", "Update Member", "Delete Member"],
    )
    st.sidebar.divider()
    st.sidebar.caption(f"Database: {database_config()['database']}")

    if navigation == "Dashboard":
        st.subheader("Management Dashboard")
        if members.empty:
            st.info("No member records are available. Use Add Member to create the first record, or run the data import script to load the CA1 dataset.")
        else:
            filter_a, filter_b, filter_c = st.columns(3)
            gender_options = sorted(members["gender"].dropna().unique().tolist())
            membership_options = sorted(members["membership_type"].dropna().unique().tolist())
            selected_genders = filter_a.multiselect("Gender", gender_options, default=gender_options)
            selected_memberships = filter_b.multiselect("Membership type", membership_options, default=membership_options)
            sauna_filter = filter_c.selectbox("Sauna usage", ["All", "Yes", "No"])

            filtered = members[
                members["gender"].isin(selected_genders)
                & members["membership_type"].isin(selected_memberships)
            ].copy()
            if sauna_filter != "All":
                filtered = filtered[filtered["uses_sauna"] == (sauna_filter == "Yes")]

            total = len(filtered)
            average_age = filtered["age"].mean() if total else 0
            average_visits = filtered["visit_per_week"].mean() if total else 0
            average_duration = filtered["avg_time_in_gym_min"].mean() if total else 0
            premium_share = (filtered["membership_type"].eq("Premium").mean() * 100) if total else 0

            st.caption(f"Showing results for {total:,} member records based on the selected filters.")
            metric_cols = st.columns(5)
            metric_cols[0].metric("Total members", f"{total:,}")
            metric_cols[1].metric("Average age", f"{average_age:.1f} years")
            metric_cols[2].metric("Average visits", f"{average_visits:.1f} per week")
            metric_cols[3].metric("Average gym time", f"{average_duration:.0f} minutes")
            metric_cols[4].metric("Premium membership", f"{premium_share:.1f}%")

            st.divider()
            tab_overview, tab_membership, tab_services, tab_attendance = st.tabs(
                ["Overview", "Membership", "Services", "Attendance"]
            )
            with tab_overview:
                left, right = st.columns(2)
                with left:
                    gender_data = filtered["gender"].value_counts().rename_axis("Gender").reset_index(name="Members")
                    st.plotly_chart(px.pie(gender_data, names="Gender", values="Members", hole=0.42,
                                           title="Member Distribution by Gender"), use_container_width=True)
                with right:
                    st.plotly_chart(px.histogram(filtered, x="age", nbins=20,
                                                 title="Member Age Distribution",
                                                 labels={"age": "Age (years)"}), use_container_width=True)
                left, right = st.columns(2)
                with left:
                    visit_data = filtered["visit_per_week"].value_counts().sort_index().rename_axis("Visits per Week").reset_index(name="Members")
                    st.plotly_chart(px.bar(visit_data, x="Visits per Week", y="Members",
                                           title="Weekly Visit Frequency"), use_container_width=True)
                with right:
                    st.plotly_chart(px.box(filtered, y="avg_time_in_gym_min",
                                           title="Gym Visit Duration",
                                           labels={"avg_time_in_gym_min": "Minutes"}), use_container_width=True)

            with tab_membership:
                left, right = st.columns(2)
                with left:
                    mix = filtered["membership_type"].value_counts().rename_axis("Membership Type").reset_index(name="Members")
                    st.plotly_chart(px.bar(mix, x="Membership Type", y="Members",
                                           title="Membership Type Distribution"), use_container_width=True)
                with right:
                    cross = filtered.groupby(["membership_type", "gender"]).size().reset_index(name="Members")
                    st.plotly_chart(px.bar(cross, x="membership_type", y="Members", color="gender",
                                           barmode="group", title="Membership by Gender",
                                           labels={"membership_type": "Membership Type", "gender": "Gender"}),
                                     use_container_width=True)

            with tab_services:
                left, right = st.columns(2)
                with left:
                    service_data = pd.DataFrame({
                        "Service": ["Personal training", "Group lessons", "Drink add-on", "Sauna"],
                        "Participation (%)": [
                            filtered["personal_training"].mean() * 100,
                            filtered["attend_group_lesson"].mean() * 100,
                            filtered["drink_addon"].mean() * 100,
                            filtered["uses_sauna"].mean() * 100,
                        ],
                    }) if total else pd.DataFrame(columns=["Service", "Participation (%)"])
                    st.plotly_chart(px.bar(service_data, x="Service", y="Participation (%)",
                                           title="Optional Service Participation", range_y=[0, 100]),
                                     use_container_width=True)
                with right:
                    trainer_data = filtered[filtered["trainer_name"].notna()]["trainer_name"].value_counts().head(10).rename_axis("Trainer").reset_index(name="Members")
                    st.plotly_chart(px.bar(trainer_data, x="Trainer", y="Members",
                                           title="Members by Trainer"), use_container_width=True)

                lesson_rows = [lesson for value in filtered["fav_group_lesson"] for lesson in split_values(value)]
                if lesson_rows:
                    lesson_data = pd.Series(lesson_rows).value_counts().rename_axis("Group Lesson").reset_index(name="Selections")
                    st.plotly_chart(px.bar(lesson_data, x="Selections", y="Group Lesson", orientation="h",
                                           title="Favourite Group Lessons"), use_container_width=True)

            with tab_attendance:
                day_rows = [day for value in filtered["days_per_week"] for day in split_values(value)]
                if day_rows:
                    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    day_data = pd.Series(day_rows).value_counts().reindex(day_order, fill_value=0).rename_axis("Day").reset_index(name="Member Selections")
                    st.plotly_chart(px.bar(day_data, x="Day", y="Member Selections",
                                           title="Selected Gym Days"), use_container_width=True)
                else:
                    st.info("No gym-day selections are available for the selected records.")

            with st.expander("View dashboard data"):
                st.dataframe(filtered, use_container_width=True, hide_index=True)

        if st.button("Refresh data"):
            st.rerun()

    elif navigation == "View Members":
        st.subheader("Member Records")
        if members.empty:
            st.info("No member records are currently available.")
        else:
            search = st.text_input("Search by member name or member ID")
            view = members.copy()
            if search.strip():
                if search.strip().isdigit():
                    view = view[view["member_id"].astype(str) == search.strip()]
                else:
                    view = view[view["member_name"].str.contains(search.strip(), case=False, na=False)]
            st.caption(f"{len(view):,} record(s) found")
            st.dataframe(view, use_container_width=True, hide_index=True)
            st.download_button("Download displayed records (CSV)", view.to_csv(index=False).encode("utf-8"),
                               file_name="anyday_fitness_members.csv", mime="text/csv")

    elif navigation == "Add Member":
        st.subheader("Register a Member")
        with st.form("add_member_form", clear_on_submit=True):
            name = st.text_input("Member name")
            col1, col2, col3 = st.columns(3)
            gender = col1.selectbox("Gender", ["Female", "Male", "Other"])
            birthday = col2.date_input("Date of birth", value=date(2000, 1, 1), max_value=date.today())
            age = col3.number_input("Age", min_value=1, max_value=120, value=25, step=1)
            col1, col2, col3 = st.columns(3)
            membership = col1.selectbox("Membership type", ["Standard", "Premium"])
            visits = col2.number_input("Visits per week", min_value=0, max_value=7, value=3, step=1)
            duration = col3.number_input("Average gym time (minutes)", min_value=0, max_value=600, value=60, step=5)
            days = st.multiselect("Selected gym days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
            attends_lessons = st.checkbox("Attends group lessons")
            lessons = st.text_input("Favourite group lessons (separate multiple entries with commas)")
            drink_addon = st.checkbox("Uses drink add-on")
            drinks = st.text_input("Favourite drinks (separate multiple entries with commas)")
            personal_training = st.checkbox("Uses personal training")
            trainer = st.text_input("Trainer name")
            sauna = st.checkbox("Uses sauna")
            col1, col2 = st.columns(2)
            check_in = col1.time_input("Usual check-in time", value=time(18, 0))
            check_out = col2.time_input("Usual check-out time", value=time(19, 0))
            submitted = st.form_submit_button("Save member record", type="primary")
        if submitted:
            try:
                values = member_values(name, gender, birthday, age, membership, visits,
                                       attends_lessons, check_in, check_out, duration,
                                       drink_addon, personal_training, trainer, sauna)
                new_id = create_member(values, days, split_values(lessons), split_values(drinks))
                st.success(f"Member record created. Assigned member ID: {new_id}.")
                st.rerun()
            except Exception as exc:
                st.error(f"The member record could not be created: {exc}")

    elif navigation == "Update Member":
        st.subheader("Update a Member Record")
        if members.empty:
            st.info("There are no member records to update.")
        else:
            selected_id = st.selectbox("Select member ID", members["member_id"].astype(int).tolist())
            record = get_member(int(selected_id))
            if record:
                with st.form("update_member_form"):
                    name = st.text_input("Member name", value=str(record["member_name"]))
                    col1, col2, col3 = st.columns(3)
                    genders = ["Female", "Male", "Other"]
                    gender_value = record["gender"] if record["gender"] in genders else "Other"
                    gender = col1.selectbox("Gender", genders, index=genders.index(gender_value))
                    birthday_value = pd.to_datetime(record["birthday"]).date()
                    birthday = col2.date_input("Date of birth", value=birthday_value, max_value=date.today())
                    age = col3.number_input("Age", min_value=1, max_value=120, value=int(record["age"]), step=1)
                    col1, col2, col3 = st.columns(3)
                    memberships = ["Standard", "Premium"]
                    membership_value = record["membership_type"] if record["membership_type"] in memberships else "Standard"
                    membership = col1.selectbox("Membership type", memberships, index=memberships.index(membership_value))
                    visits = col2.number_input("Visits per week", min_value=0, max_value=7, value=int(record["visit_per_week"]), step=1)
                    duration = col3.number_input("Average gym time (minutes)", min_value=0, max_value=600, value=int(record["avg_time_in_gym_min"]), step=5)
                    days = st.multiselect("Selected gym days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], default=split_values(record.get("days_per_week")))
                    attends_lessons = st.checkbox("Attends group lessons", value=bool(record["attend_group_lesson"]))
                    lessons = st.text_input("Favourite group lessons (comma-separated)", value=record.get("fav_group_lesson") or "")
                    drink_addon = st.checkbox("Uses drink add-on", value=bool(record["drink_addon"]))
                    drinks = st.text_input("Favourite drinks (comma-separated)", value=record.get("fav_drink") or "")
                    personal_training = st.checkbox("Uses personal training", value=bool(record["personal_training"]))
                    trainer = st.text_input("Trainer name", value=record.get("trainer_name") or "")
                    sauna = st.checkbox("Uses sauna", value=bool(record["uses_sauna"]))
                    col1, col2 = st.columns(2)
                    check_in = col1.time_input("Usual check-in time", value=mysql_time_to_time(record["check_in_time"]))
                    check_out = col2.time_input("Usual check-out time", value=mysql_time_to_time(record["check_out_time"]))
                    submitted = st.form_submit_button("Save changes", type="primary")
                if submitted:
                    try:
                        values = member_values(name, gender, birthday, age, membership, visits,
                                               attends_lessons, check_in, check_out, duration,
                                               drink_addon, personal_training, trainer, sauna)
                        update_member(int(selected_id), values, days, split_values(lessons), split_values(drinks))
                        st.success("Member record updated successfully.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"The member record could not be updated: {exc}")

    elif navigation == "Delete Member":
        st.subheader("Delete a Member Record")
        if members.empty:
            st.info("There are no member records to delete.")
        else:
            name_by_id = members.set_index("member_id")["member_name"].to_dict()
            selected_id = st.selectbox(
                "Select member record",
                members["member_id"].astype(int).tolist(),
                format_func=lambda value: f"{value} — {name_by_id[value]}",
            )
            st.warning("Deleting a member also removes the associated gym-day, favourite-lesson and favourite-drink records.")
            confirm = st.checkbox("I confirm that this member record should be deleted.")
            if st.button("Delete selected member", type="primary", disabled=not confirm):
                try:
                    delete_member(int(selected_id))
                    st.success(f"Member record {selected_id} was deleted.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"The member record could not be deleted: {exc}")

except Error as exc:
    st.error("A connection to the MySQL database could not be established.")
    st.code(str(exc))
    st.markdown("""
    **Connection checklist**
    1. Confirm that the MySQL Server service is running.
    2. Execute `database/schema.sql` in MySQL Workbench.
    3. Configure the database connection using the environment variables in the README.
    4. Run `python import_data.py` to load the CA1 dataset.
    5. Restart the application using `streamlit run app.py`.
    """)
except Exception as exc:
    st.error(f"The application encountered an error: {exc}")
