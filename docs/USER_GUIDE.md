# User Guide and Test Plan

## 1. Accessing the application

Start the MySQL Server service, activate the project's Python environment, configure the database connection variables, and run `streamlit run app.py`. Open the local address shown in the terminal.

## 2. Navigation

Use the Main menu in the sidebar to open the required module.

### Dashboard

The dashboard presents summary indicators and interactive charts. Use the filters to view selected gender, membership types and sauna usage. Select **Refresh data** to reload records from MySQL.

### View Members

Use the search field to find a member by name or member ID. The displayed records can be exported as a CSV file.

### Add Member

Complete the member details and submit the form. The application validates required fields and saves the member and related preference records in a database transaction. The database generates the member ID.

### Update Member

Select a member ID, edit the displayed details and submit the changes. The application updates the member and replaces the associated gym-day, favourite-lesson and favourite-drink preferences in one transaction.

### Delete Member

Select a member record and confirm the deletion. The database's foreign-key cascade removes related preference records automatically.

## 3. Functional test plan

Use a clearly identified test record. Do not delete or modify an actual business record during testing without authorization.

| Test ID | Action | Expected result | Actual result |
|---|---|---|---|
| T01 | Open View Members | Existing database records are displayed. | To be completed |
| T02 | Search by member ID | The matching member is displayed. | To be completed |
| T03 | Add a test member | A new record is saved and receives a member ID. | To be completed |
| T04 | Update the test member | Updated values appear in the member list. | To be completed |
| T05 | Delete the test member | The member and related preferences are removed. | To be completed |
| T06 | Refresh the dashboard | KPIs and charts reflect the current database records. | To be completed |
| T07 | Restart the application | Previously saved records remain available. | To be completed |

## 4. Completion checklist

- [ ] Database and tables created in MySQL.
- [ ] Python successfully connects to MySQL.
- [ ] CA1 dataset imported and 1,000 member records verified.
- [ ] Read and search operations tested.
- [ ] Create operation tested.
- [ ] Update operation tested.
- [ ] Delete operation tested.
- [ ] Dashboard reflects database changes after refresh.
- [ ] GitHub repository published.
- [ ] Hosted database configured for deployment.
- [ ] Live application deployed and tested.

Record test results only after performing each test.
