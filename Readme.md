# INFLUENCER SPONSORSHIP PLATFORM

Project developed by Nithesh Kanna S [21F2001271](mailto:21f2001271@ds.study.iitm.ac.in)

## Project Structure:

### **/instance/**

- `db.sqlite3` - Database folder and database automatically created by the code.

### **/routes/**

- [auth.py](routes/auth.py)  
  Contains the `AuthAPI` implementation, responsible for handling authentication-related functionalities such as login, token management, and user profile management.

- [admin.py](routes/admin.py)  
  Contains the `AdminAPI`, which provides endpoints for admin-specific functionalities like managing users and overseeing the platform's operations.

- [adminOperationsAPI.py](routes/adminOperationsAPI.py)  
  Implements `AdminOperationAPI`, which includes APIs for performing administrative actions like sponsor approvals and reviewing flagged content.

- [adRequestAPI.py](routes/adRequestAPI.py)  
  Manages ad request operations, enabling sponsors to create, update, and delete ad requests while tracking the status of ongoing requests.

- [blueprint.py](routes/blueprint.py)  
  Registers all the API endpoints and blueprints with the Flask application.

- [campaigns.py](routes/campaigns.py)  
  Implements the campaign-related APIs, allowing sponsors to create, edit, and manage campaigns, including details like budgets, dates, and categorization.

- [decorators.py](routes/decorators.py)  
  Contains reusable decorators for functionalities like role-based access control and token validation.

- [emailAPI.py](routes/emailAPI.py)  
  Provides APIs for email functionalities, such as sending verification emails and campaign notifications using the Google Mail API.

- [enum.py](routes/enum.py)  
  Defines enumerations used across the application, such as user roles, campaign statuses, and ad request statuses.

- [influencer.py](routes/influencer.py)  
  Contains APIs for influencer-related functionalities, such as profile management, campaign participation, and revenue tracking.

- [passwordChange.py](routes/passwordChange.py)  
  Implements the API for password reset and update functionalities.

- [Reports.py](routes/Reports.py)  
  Provides endpoints for generating and exporting reports for admins, sponsors, and influencers.

- [search.py](routes/search.py)  
  Handles APIs for search functionalities, enabling users to find campaigns, influencers, and sponsors based on specific filters.

- [sponsor.py](routes/sponsor.py)  
  Contains APIs for sponsor-specific functionalities like profile management, creating campaigns, and reviewing ad requests.

- [statistics.py](routes/statistics.py)  
  Provides APIs for fetching statistical data and analytics, such as campaign performance and engagement metrics.

- [user.py](routes/user.py)  
  Implements user-related APIs, including account creation, profile updates, and retrieving user-specific data.

### **/application/**

- [__init__.py](application/__init__.py)  
  Initializes the application module and sets up configurations, imports, and initial setups for the Flask app.

- [database.py](application/database.py)  
  Handles the database connection and session management for the application using SQLite.

- [event_listeners.py](application/event_listeners.py)  
  Defines event listeners to handle actions triggered during database events, such as pre-save or post-save operations.

- [models.py](application/models.py)  
  Contains database schemas and ORM models for the application, representing entities like users, campaigns, and ad requests.

- [PreProcess.py](application/PreProcess.py)  
  Implements preprocessing logic, such as validating data or transforming inputs before they are processed by the application.

- [response.py](application/response.py)  
  Contains helper functions and utilities for standardizing API responses across the application.

- [tokens.py](application/tokens.py)  
  Manages token generation, validation, and blacklisting logic for the application’s authentication system.

- [utils.py](application/utils.py)  
  Provides utility functions used throughout the application, such as formatters, common validations, and reusable helpers.

### **/services/**

- [celery_app.py](services/celery_app.py)  
  Configures and initializes the Celery application with the Flask app context for handling asynchronous tasks.

- [tasks.py](services/tasks.py)  
  Defines Celery tasks for background jobs like sending emails, generating reports, and exporting campaign data.

- [trigger.py](services/trigger.py)  
  Provides functions to trigger and schedule specific Celery tasks, such as periodic reminders or report generation.

### **/templates/**

- [monthly_report.html](templates/monthly_report.html)  
  HTML template used for generating monthly reports, including campaign analytics, user engagement, and performance summaries.

- [registration.html](templates/registration.html)  
  HTML template for email verification or confirmation during user registration.

### **/validations/**

- [RoleValidations.py](validations/RoleValidations.py)  
  Contains validation logic to ensure role-based restrictions and assignments are consistent, such as preventing conflicting roles.

- [UserValidation.py](validations/UserValidation.py)  
  Implements user input validations for operations like registration, login, and profile updates.

### **Root Directory**

- [.gitignore](.gitignore)  
  Specifies files and directories to be ignored by Git, such as virtual environments, compiled files, and sensitive credentials.

- [app.py](app.py)  
  The main entry point of the Flask application. It initializes the app, registers blueprints, and starts the server.

---

## To run this API

1. **Create a Virtual Environment**

   For Mac/Linux:  
   ```bash
   python -m venv env
   ```
   For Windows:
    ```bash
    python -m venv env
    ```

2. **Activate the Virtual Environment**  
   For Mac/Linux:
   ```bash
   source env/bin/activate
   ```
   For Windows:
   ```bash
   .\env\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the API**
   ```bash
   python app.py
   ```

> **Note**: The database (`db.sqlite3`) will be automatically created when the app is first run.

---