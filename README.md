# Anyday Fitness Management System

**Course:** MKT322 – Advanced Business Intelligence  
**Academic Task:** 2 – Live Management System with Real Data  
**Application:** Python, Streamlit and MySQL

## 1. Project overview

This project extends the Anyday Fitness member-analysis work prepared for CA1. It uses the supplied CA1 CSV dataset as the initial business dataset and provides a Streamlit application for viewing and managing member records stored in MySQL.

The application includes a management dashboard, member search, and the four database operations: Create, Read, Update and Delete (CRUD). Changes made through the management pages are committed to MySQL and are available when the application reloads its data.

## 2. Project structure

```text
Anyday_Fitness_CA2/
├── app.py
├── import_data.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   └── ANYDAY_FITNESS.csv
├── database/
│   ├── schema.sql
│   └── business_analysis_queries.sql
└── docs/
    ├── DATABASE_DESIGN.md
    ├── USER_GUIDE.md
    └── CA2_REQUIREMENTS.md
```

## 3. Software requirements

- Python 3.10 or later
- MySQL Server 8.0 or later
- MySQL Workbench
- Visual Studio Code or another Python editor

## 4. Local installation and setup

### Step 1 – Create a Python environment

Open a terminal in the project directory and run:

```bash
python -m venv .venv
```

On Windows, activate it with:

```bat
.venv\Scripts\activate
```

Install the required packages:

```bash
python -m pip install -r requirements.txt
```

### Step 2 – Create the MySQL database

1. Start MySQL Server and open MySQL Workbench.
2. Connect to the local MySQL instance.
3. Open `database/schema.sql` in the SQL editor.
4. Execute the complete script.
5. Confirm that the `gym_data` database and its four tables are visible.

### Step 3 – Configure the database connection

The application reads credentials from environment variables during local use. In Windows Command Prompt, set the values for the current terminal session. Replace the example values with the connection details configured on your computer.

```bat
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root
set DB_PASSWORD=YOUR_MYSQL_PASSWORD
set DB_NAME=gym_data
```

Do not place a real database password in the source code or commit it to GitHub.

### Step 4 – Import the CA1 dataset

Run:

```bash
python import_data.py
```

The script reads `data/ANYDAY_FITNESS.csv`, validates the expected columns and imports member records and their multi-value preferences into the related MySQL tables.

**Important:** The import script replaces the existing rows in the project tables with the original CA1 dataset. Run it before entering new live records. Do not rerun it after making management changes unless you intend to restore the original dataset.

Verify the member count in MySQL Workbench:

```sql
USE gym_data;
SELECT COUNT(*) AS total_members FROM members;
```

The supplied CA1 dataset contains 1,000 member records. The query should return 1,000 after a successful initial import.

### Step 5 – Run the application

In the same terminal where the environment variables are configured, run:

```bash
streamlit run app.py
```

Streamlit will provide a local address, normally `http://localhost:8501`.

## 5. Application modules

| Module | Purpose |
|---|---|
| Dashboard | Displays member KPIs and interactive charts with filters. |
| View Members | Displays, searches and exports member records. |
| Add Member | Creates a member record and related preferences. |
| Update Member | Updates an existing member and its preferences. |
| Delete Member | Deletes a selected member and associated preference records. |

## 6. Key performance indicators

- Total members
- Average member age
- Average gym visits per week
- Average gym visit duration
- Share of Premium memberships
- Participation in optional services such as personal training, group lessons, drink add-ons and sauna use

The dashboard indicators are calculated from the records currently stored in MySQL and are affected by the selected filters.

## 7. Database analysis queries

The file `database/business_analysis_queries.sql` contains queries for membership distribution, average gym time and visits, personal-training adoption, sauna usage, group-lesson participation, popular gym days and favourite group lessons.

## 8. GitHub publication

1. Create a repository in your GitHub account.
2. Add the project files and commit the changes.
3. Do not upload `.venv`, passwords, local configuration files or private credentials.
4. Check that `app.py`, `import_data.py`, `requirements.txt`, `database/`, `data/` and this README are present.

## 9. Deployment

The Streamlit interface can be deployed through Streamlit Community Cloud after the code is published to GitHub. The MySQL database must also be hosted on a service that accepts secure connections from the deployed application. A database running only on a personal computer at `localhost` cannot be reached by a cloud-hosted Streamlit application.

For deployment:

1. Provision a hosted MySQL database and execute `database/schema.sql` on it.
2. Import the CA1 data into the hosted database using the connection details provided by the database host.
3. Publish the project to GitHub.
4. Create an application at Streamlit Community Cloud and select `app.py` as the main file.
5. Add the hosted database credentials in the application's Secrets settings:

```toml
[mysql]
host = "YOUR_DATABASE_HOST"
port = 3306
user = "YOUR_DATABASE_USER"
password = "YOUR_DATABASE_PASSWORD"
database = "gym_data"
```

6. Deploy and verify the application using the live URL.

Never commit real credentials to the repository.

## 10. Verification status

The project files and setup instructions are prepared. The following activities must be completed and verified in the user's environment before they can be reported as successful:

- MySQL database creation and Python connection
- Initial import of all 1,000 CA1 member records
- Testing Create, Read, Update and Delete operations against MySQL
- GitHub publication
- Hosted database configuration and live deployment
- Testing the deployed application

Use the verification checklist in `docs/USER_GUIDE.md` to record the outcome of each test.
