EDU-VAULT — UNIFIED EXAM SYSTEM DATABASE UPDATE

Unified Exam System now stores its online records in the same SQL database used by the main Edu-Vault Flask application.
postgresql://<username>:<password>@<host>:<port>/<database>
Database selection:
- Production: set DATABASE_URL to the existing PostgreSQL/Supabase connection string.
- Local development: when DATABASE_URL is not set, the app uses data/exams.db (SQLite).
- The table unified_exam_records is created automatically on first API use. It stores examPackages, examSchedules, examFiles, students and results records.
- Uploaded exam PDFs are stored as binary data in the same SQL database and served by the Flask app, so cross-device access does not depend on an ephemeral local uploads folder.

Run locally:
1. Install requirements.txt.
2. Configure environment variables in your own .env file (see .env.example).
3. Run: python app.py
4. Open /eduvault-system.
5. Check GET /api/unified-exam/health to confirm the database connection.

Important migration note:
This update removes the previous external cloud database integration. It does not automatically fetch historical cloud records because no data export or service credentials were provided. Export the old collections before shutting down the old service, then import those records into the new SQL table if you need the historical cloud data. New and updated exam records will use Edu-Vault SQL going forward.

Security note: before public production use, ensure the existing admin/student authorization is enforced server-side for Unified Exam System write APIs and apply appropriate upload access controls.


EDUVAULT CURRICULUM UPGRADE
===========================

New student portals:
- /exam-generator: creates a practice exam from eligible existing multiple-choice questions.
- /video-learning: displays published curriculum video links.
- /learning-notes: displays published read-only revision notes.
- /learning-analytics: shows the student's saved exam history and available Bloom-category analysis.
- /admin/bloom-taxonomy: administrator tool for searching questions and reviewing Bloom's taxonomy tags.

Data and taxonomy:
- Existing Databasejson files and curriculum tables remain the source for the grade/subject/unit/section/topic browser.
- Bloom categories: Remember, Understand, Apply, Analyze, Evaluate, Create.
- Categories are not automatically treated as verified. Administrators should review question tags before using them for category-focused exams.
- New tables are created additively at app startup: question_bloom_tags, tutorial_videos, revision_notes, and user_answer_details.
- Existing exams receive a nullable duration_minutes field. Generated practice exams store and enforce the requested duration; older exams retain the previous timer behavior.

Admin API:
- PUT /api/admin/questions/<question_id>/bloom-tags
- POST /api/learning/videos
- PUT or DELETE /api/learning/videos/<video_id>
- POST /api/learning/notes
- PUT or DELETE /api/learning/notes/<note_id>
- GET /api/admin/learning/content

Important current data limitation:
The included SQLite database contains curriculum structure but no existing exam/question records. The generator will report that no eligible questions are available until an administrator imports or approves question-bank content. The included Databasejson files describe curriculum structure; they do not themselves provide a question bank.

Run locally on Windows:
1. Create and activate a virtual environment using a supported Python version.
2. Install packages: pip install -r requirements.txt
3. Configure a local .env file with your own SECRET_KEY and any required service credentials. Never commit .env.
4. Run: python app.py
5. Open: http://127.0.0.1:5000

Deployment:
- Configure DATABASE_URL, SECRET_KEY, and required API/service variables in the hosting provider's environment settings.
- Use a reachable PostgreSQL/Supabase connection string where cloud persistence is required.
- EduVault now refuses to silently switch to a separate SQLite database if DATABASE_URL is set but PostgreSQL cannot be reached.
- Back up the database before deployment or migration.

Student code delivery:
- Set SMS_MODE=live to deliver a code. SMS_MODE=test deliberately sends no SMS or email and only returns a test code to an administrator.
- SMS_PROVIDER=afromessage uses AFROMESSAGE_TOKEN, AFROMESSAGE_IDENTIFIER_ID, and AFROMESSAGE_SENDER.
- SMS_PROVIDER=smsethiopia uses SMSETHIOPIA_API_KEY. The provider advertises 100 free test messages to whitelisted numbers; regular delivery may require a paid balance.
- SMS_PROVIDER=email sends through the configured SMTP account. SMTP_HOST, SMTP_PORT, SMTP_USE_TLS, SMTP_USE_SSL, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL are shown in .env.example.
- When an SMS provider fails, EduVault uses email if the student has an email address and SMTP is configured.
- Use a private .env file for credentials. Do not put live provider or database credentials in this README.
