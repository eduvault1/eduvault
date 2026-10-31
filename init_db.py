import os
import sqlite3
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    """Initialize database - Creates all tables if they don't exist"""
    os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

    if DATABASE_URL:
        # --- SUPABASE / POSTGRESQL ---
        import psycopg2
        print("Connecting to Cloud Database (Supabase / PostgreSQL)...")
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                telegram_id TEXT,
                is_verified INTEGER DEFAULT 0,
                first_name TEXT,
                last_name TEXT,
                profile_photo TEXT,
                phone_number TEXT,
                email TEXT,
                student_code TEXT UNIQUE,
                account_status TEXT NOT NULL DEFAULT 'ACTIVE',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                rejected_at TIMESTAMP,
                streak_count INTEGER DEFAULT 0,
                last_activity TEXT,
                daily_goal_mins INTEGER DEFAULT 30
            );
        ''')

        # 2. Resources Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                resource_type TEXT NOT NULL CHECK (resource_type IN ('Textbook', 'Teacher Guide', 'Worksheet', 'Exam', 'Entrance Exam', 'Model Exam', 'School Exam', 'Notes')),
                subject TEXT NOT NULL,
                grade INTEGER NOT NULL,
                unit_number INTEGER,
                unit_title TEXT,
                section_number TEXT,
                section_title TEXT,
                topic_title TEXT,
                subtopic TEXT,
                file_url TEXT,
                pdf_url TEXT,
                file_name TEXT,
                description TEXT,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                status TEXT DEFAULT 'published' CHECK (status IN ('draft', 'pending', 'published', 'archived')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 3. Curriculum Tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curriculum_subjects (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curriculum_grades (
                id SERIAL PRIMARY KEY,
                number INTEGER UNIQUE NOT NULL
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curriculum_units (
                id SERIAL PRIMARY KEY,
                subject_id INTEGER REFERENCES curriculum_subjects(id) ON DELETE CASCADE,
                grade_id INTEGER REFERENCES curriculum_grades(id) ON DELETE CASCADE,
                unit_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                UNIQUE(subject_id, grade_id, unit_number)
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curriculum_sections (
                id SERIAL PRIMARY KEY,
                unit_id INTEGER REFERENCES curriculum_units(id) ON DELETE CASCADE,
                section_number TEXT NOT NULL,
                title TEXT NOT NULL,
                UNIQUE(unit_id, section_number)
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curriculum_topics (
                id SERIAL PRIMARY KEY,
                section_id INTEGER REFERENCES curriculum_sections(id) ON DELETE CASCADE,
                topic_title TEXT NOT NULL,
                subtopic TEXT,
                UNIQUE(section_id, topic_title, subtopic)
            );
        ''')

        # 4. Exams Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES resources(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                resource_type TEXT DEFAULT 'Exam',
                subject TEXT DEFAULT 'General',
                grade INTEGER DEFAULT 12,
                school_name TEXT,
                department TEXT,
                academic_year TEXT,
                instructions TEXT,
                total_marks INTEGER DEFAULT 100
            );
        ''')

        # 5. Chapters Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                id SERIAL PRIMARY KEY,
                subject TEXT NOT NULL,
                grade INTEGER DEFAULT 12,
                name TEXT NOT NULL,
                question_count INTEGER DEFAULT 0,
                estimated_time_mins INTEGER DEFAULT 45,
                difficulty TEXT DEFAULT 'Medium'
            );
        ''')

        # 6. Questions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id SERIAL PRIMARY KEY,
                exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
                chapter_id INTEGER REFERENCES chapters(id) ON DELETE SET NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT NOT NULL,
                passage_text TEXT,
                diagram_instruction TEXT,
                curriculum_unit_id INTEGER REFERENCES curriculum_units(id) ON DELETE SET NULL,
                curriculum_section_id INTEGER REFERENCES curriculum_sections(id) ON DELETE SET NULL,
                curriculum_topic_id INTEGER REFERENCES curriculum_topics(id) ON DELETE SET NULL,
                question_number INTEGER,
                source_year TEXT,
                classification_confidence TEXT CHECK (classification_confidence IN ('High', 'Medium', 'Low')),
                classification_reason TEXT
            );
        ''')

        # 7. User Results Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_results (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
                score INTEGER DEFAULT 0,
                total_questions INTEGER DEFAULT 0,
                time_used_seconds INTEGER DEFAULT 0,
                accuracy FLOAT DEFAULT 0,
                date_attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ai_recommendation TEXT
            );
        ''')

        # 8. Pending Tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_exams (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                grade INTEGER NOT NULL,
                academic_year TEXT,
                school_name TEXT,
                instructions TEXT,
                source_filename TEXT,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_questions (
                id SERIAL PRIMARY KEY,
                pending_exam_id INTEGER REFERENCES pending_exams(id) ON DELETE CASCADE,
                question_number INTEGER,
                source_year TEXT,
                question_text TEXT NOT NULL,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                correct_answer TEXT,
                explanation TEXT,
                passage_text TEXT,
                diagram_instruction TEXT,
                unit_number TEXT,
                unit_title TEXT,
                section_number TEXT,
                section_title TEXT,
                topic_title TEXT,
                subtopic TEXT,
                confidence TEXT CHECK (confidence IN ('High', 'Medium', 'Low')),
                classification_reason TEXT,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected'))
            );
        ''')

        # 9. Tutor Tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutor_threads (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                title TEXT DEFAULT 'New Conversation',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutor_messages (
                id SERIAL PRIMARY KEY,
                thread_id INTEGER REFERENCES tutor_threads(id) ON DELETE CASCADE,
                sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'ai', 'system')),
                message_text TEXT NOT NULL,
                attachment_name TEXT,
                attachment_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unified_accounts (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                student_code TEXT UNIQUE,
                phone_number TEXT,
                email TEXT,
                sex TEXT,
                age INTEGER,
                stream TEXT DEFAULT 'Natural Sc.',
                account_status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # --- Add missing columns if they don't exist ---
        pg_migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_photo TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS student_code TEXT UNIQUE;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS account_status TEXT NOT NULL DEFAULT 'ACTIVE';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP;",
            "ALTER TABLE unified_accounts ADD COLUMN IF NOT EXISTS phone_number TEXT;",
            "ALTER TABLE unified_accounts ADD COLUMN IF NOT EXISTS email TEXT;",
            "ALTER TABLE exams ADD COLUMN IF NOT EXISTS resource_id INTEGER REFERENCES resources(id) ON DELETE SET NULL;",
            "ALTER TABLE exams ADD COLUMN IF NOT EXISTS school_name TEXT;",
            "ALTER TABLE exams ADD COLUMN IF NOT EXISTS academic_year TEXT;",
            "ALTER TABLE questions ADD COLUMN IF NOT EXISTS curriculum_unit_id INTEGER;",
            "ALTER TABLE questions ADD COLUMN IF NOT EXISTS curriculum_section_id INTEGER;",
            "ALTER TABLE questions ADD COLUMN IF NOT EXISTS curriculum_topic_id INTEGER;",
            "ALTER TABLE questions ADD COLUMN IF NOT EXISTS classification_confidence TEXT;",
            "ALTER TABLE questions ADD COLUMN IF NOT EXISTS classification_reason TEXT;",
            "ALTER TABLE exams ADD COLUMN IF NOT EXISTS resource_type TEXT DEFAULT 'Exam';",
            "ALTER TABLE exams ADD COLUMN IF NOT EXISTS subject TEXT DEFAULT 'General';",
            "ALTER TABLE exams ADD COLUMN IF NOT EXISTS grade INTEGER DEFAULT 12;",
            "ALTER TABLE chapters ADD COLUMN IF NOT EXISTS grade INTEGER DEFAULT 12;",
            "ALTER TABLE chapters ADD COLUMN IF NOT EXISTS subject TEXT DEFAULT 'General';",
            "ALTER TABLE questions ADD COLUMN IF NOT EXISTS chapter_id INTEGER;"
            ,"ALTER TABLE questions ADD COLUMN IF NOT EXISTS question_number INTEGER;"
            ,"ALTER TABLE questions ADD COLUMN IF NOT EXISTS source_year TEXT;"
            ,"ALTER TABLE pending_exams ADD COLUMN IF NOT EXISTS academic_year TEXT;"
            ,"ALTER TABLE pending_exams ADD COLUMN IF NOT EXISTS school_name TEXT;"
            ,"ALTER TABLE pending_exams ADD COLUMN IF NOT EXISTS instructions TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS source_year TEXT;"
            ,"ALTER TABLE resources ADD COLUMN IF NOT EXISTS unit_number INTEGER;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS question_number INTEGER;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS option_a TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS option_b TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS option_c TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS option_d TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS correct_answer TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS explanation TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS passage_text TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS diagram_instruction TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS unit_number TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS unit_title TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS section_number TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS section_title TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS topic_title TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS subtopic TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS confidence TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS classification_reason TEXT;"
            ,"ALTER TABLE pending_questions ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';"
            ,"ALTER TABLE questions ADD COLUMN IF NOT EXISTS passage_text TEXT;"
            ,"ALTER TABLE questions ADD COLUMN IF NOT EXISTS diagram_instruction TEXT;"
            ,"ALTER TABLE questions ADD COLUMN IF NOT EXISTS curriculum_section_id INTEGER;"
            ,"ALTER TABLE questions ADD COLUMN IF NOT EXISTS curriculum_topic_id INTEGER;"
        ]
        for query in pg_migrations:
            try:
                cursor.execute(query)
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"⚠️ Migration warning: {e}")

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone_number ON users(phone_number) WHERE phone_number IS NOT NULL AND phone_number <> ''")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unified_phone_number ON unified_accounts(phone_number) WHERE phone_number IS NOT NULL AND phone_number <> ''")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(LOWER(email)) WHERE email IS NOT NULL AND email <> ''")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unified_email ON unified_accounts(LOWER(email)) WHERE email IS NOT NULL AND email <> ''")

        # Seed Default Administrator
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, is_verified) 
                VALUES (%s, %s, %s, %s)
            ''', ("admin", generate_password_hash("admin123"), "admin", 1))

        cursor.execute("SELECT 1 FROM unified_accounts WHERE username = %s", ("admin",))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO unified_accounts
                    (username, password_hash, role, first_name, last_name)
                VALUES (%s, %s, %s, %s, %s)
            ''', ("admin", generate_password_hash("admin123"), "admin", "Unified", "Admin"))

        for number in range(1, 5):
            username = f"student{number}"
            display_number = ("One", "Two", "Three", "Four")[number - 1]
            cursor.execute("SELECT 1 FROM unified_accounts WHERE username = %s", (username,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO unified_accounts
                        (username, password_hash, role, first_name, last_name, student_code)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (username, generate_password_hash("student123"), "student", "Student", display_number, f"ST{number:03d}"))

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Supabase PostgreSQL Database Initialized & Schema Altered successfully.")

    else:
        # --- LOCAL SQLITE FALLBACK ---
        print("Connecting to Local SQLite Database...")
        db_file = os.path.join(BASE_DIR, 'data', 'exams.db')
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.executescript('''
            -- Users Table
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                telegram_id TEXT,
                is_verified INTEGER DEFAULT 0,
                first_name TEXT,
                last_name TEXT,
                profile_photo TEXT,
                student_code TEXT UNIQUE,
                account_status TEXT NOT NULL DEFAULT 'ACTIVE',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                rejected_at TIMESTAMP,
                streak_count INTEGER DEFAULT 0,
                last_activity TEXT,
                daily_goal_mins INTEGER DEFAULT 30
            );

            -- Resources Table
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                resource_type TEXT NOT NULL CHECK (resource_type IN ('Textbook', 'Teacher Guide', 'Worksheet', 'Exam', 'Entrance Exam', 'Model Exam', 'School Exam', 'Notes')),
                subject TEXT NOT NULL,
                grade INTEGER NOT NULL,
                unit_number INTEGER,
                unit_title TEXT,
                section_number TEXT,
                section_title TEXT,
                topic_title TEXT,
                subtopic TEXT,
                file_url TEXT,
                pdf_url TEXT,
                file_name TEXT,
                description TEXT,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                status TEXT DEFAULT 'published' CHECK (status IN ('draft', 'pending', 'published', 'archived')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Curriculum Tables
            CREATE TABLE IF NOT EXISTS curriculum_subjects ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL );
            CREATE TABLE IF NOT EXISTS curriculum_grades ( id INTEGER PRIMARY KEY AUTOINCREMENT, number INTEGER UNIQUE NOT NULL );
            CREATE TABLE IF NOT EXISTS curriculum_units ( id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER, grade_id INTEGER, unit_number INTEGER NOT NULL, title TEXT NOT NULL, FOREIGN KEY (subject_id) REFERENCES curriculum_subjects(id) ON DELETE CASCADE, FOREIGN KEY (grade_id) REFERENCES curriculum_grades(id) ON DELETE CASCADE, UNIQUE(subject_id, grade_id, unit_number) );
            CREATE TABLE IF NOT EXISTS curriculum_sections ( id INTEGER PRIMARY KEY AUTOINCREMENT, unit_id INTEGER, section_number TEXT NOT NULL, title TEXT NOT NULL, FOREIGN KEY (unit_id) REFERENCES curriculum_units(id) ON DELETE CASCADE, UNIQUE(unit_id, section_number) );
            CREATE TABLE IF NOT EXISTS curriculum_topics ( id INTEGER PRIMARY KEY AUTOINCREMENT, section_id INTEGER, topic_title TEXT NOT NULL, subtopic TEXT, FOREIGN KEY (section_id) REFERENCES curriculum_sections(id) ON DELETE CASCADE, UNIQUE(section_id, topic_title, subtopic) );

            -- Exams Table
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER REFERENCES resources(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                resource_type TEXT DEFAULT 'Exam',
                subject TEXT DEFAULT 'General',
                grade INTEGER DEFAULT 12,
                school_name TEXT,
                department TEXT,
                academic_year TEXT,
                instructions TEXT,
                total_marks INTEGER DEFAULT 100
            );

            -- Chapters Table
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                grade INTEGER DEFAULT 12,
                name TEXT NOT NULL,
                question_count INTEGER DEFAULT 0,
                estimated_time_mins INTEGER DEFAULT 45,
                difficulty TEXT DEFAULT 'Medium'
            );

            -- Questions Table
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
                chapter_id INTEGER REFERENCES chapters(id) ON DELETE SET NULL,
                question_number INTEGER,
                source_year TEXT,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT NOT NULL,
                passage_text TEXT,
                diagram_instruction TEXT,
                curriculum_unit_id INTEGER REFERENCES curriculum_units(id) ON DELETE SET NULL,
                curriculum_section_id INTEGER REFERENCES curriculum_sections(id) ON DELETE SET NULL,
                curriculum_topic_id INTEGER REFERENCES curriculum_topics(id) ON DELETE SET NULL,
                classification_confidence TEXT CHECK (classification_confidence IN ('High', 'Medium', 'Low')),
                classification_reason TEXT
            );

            -- User Results
            CREATE TABLE IF NOT EXISTS user_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
                score INTEGER DEFAULT 0,
                total_questions INTEGER DEFAULT 0,
                time_used_seconds INTEGER DEFAULT 0,
                accuracy FLOAT DEFAULT 0,
                date_attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ai_recommendation TEXT
            );

            -- Pending Tables
            CREATE TABLE IF NOT EXISTS pending_exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                grade INTEGER NOT NULL,
                academic_year TEXT,
                school_name TEXT,
                instructions TEXT,
                source_filename TEXT,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS pending_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pending_exam_id INTEGER REFERENCES pending_exams(id) ON DELETE CASCADE,
                question_number INTEGER,
                source_year TEXT,
                question_text TEXT NOT NULL,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                correct_answer TEXT,
                explanation TEXT,
                passage_text TEXT,
                diagram_instruction TEXT,
                unit_number TEXT,
                unit_title TEXT,
                section_number TEXT,
                section_title TEXT,
                topic_title TEXT,
                subtopic TEXT,
                confidence TEXT CHECK (confidence IN ('High', 'Medium', 'Low')),
                classification_reason TEXT,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected'))
            );

            -- Tutor Tables
            CREATE TABLE IF NOT EXISTS tutor_threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                title TEXT DEFAULT 'New Conversation',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tutor_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER REFERENCES tutor_threads(id) ON DELETE CASCADE,
                sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'ai', 'system')),
                message_text TEXT NOT NULL,
                attachment_name TEXT,
                attachment_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS unified_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                student_code TEXT UNIQUE,
                sex TEXT,
                age INTEGER,
                stream TEXT DEFAULT 'Natural Sc.',
                account_status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Local SQLite Migrations
        sqlite_migrations = [
            ("users", "ADD COLUMN first_name TEXT"),
            ("users", "ADD COLUMN last_name TEXT"),
            ("users", "ADD COLUMN profile_photo TEXT"),
            ("users", "ADD COLUMN phone_number TEXT"),
            ("users", "ADD COLUMN email TEXT"),
            ("users", "ADD COLUMN student_code TEXT"),
            ("users", "ADD COLUMN account_status TEXT NOT NULL DEFAULT 'ACTIVE'"),
            ("users", "ADD COLUMN registered_at TIMESTAMP"),
            ("users", "ADD COLUMN approved_at TIMESTAMP"),
            ("users", "ADD COLUMN rejected_at TIMESTAMP"),
            ("unified_accounts", "ADD COLUMN phone_number TEXT"),
            ("unified_accounts", "ADD COLUMN email TEXT"),
            ("exams", "ADD COLUMN resource_id INTEGER REFERENCES resources(id) ON DELETE SET NULL"),
            ("exams", "ADD COLUMN school_name TEXT"),
            ("exams", "ADD COLUMN academic_year TEXT"),
            ("questions", "ADD COLUMN curriculum_unit_id INTEGER"),
            ("questions", "ADD COLUMN curriculum_section_id INTEGER"),
            ("questions", "ADD COLUMN curriculum_topic_id INTEGER"),
            ("questions", "ADD COLUMN classification_confidence TEXT"),
            ("questions", "ADD COLUMN classification_reason TEXT"),
            ("exams", "ADD COLUMN resource_type TEXT DEFAULT 'Exam'"),
            ("exams", "ADD COLUMN subject TEXT DEFAULT 'General'"),
            ("exams", "ADD COLUMN grade INTEGER DEFAULT 12"),
            ("chapters", "ADD COLUMN grade INTEGER DEFAULT 12"),
            ("chapters", "ADD COLUMN subject TEXT DEFAULT 'General'"),
            ("questions", "ADD COLUMN chapter_id INTEGER"),
            ("pending_exams", "ADD COLUMN academic_year TEXT"),
            ("pending_exams", "ADD COLUMN school_name TEXT"),
            ("pending_exams", "ADD COLUMN instructions TEXT"),
            ("pending_questions", "ADD COLUMN source_year TEXT"),
            ("pending_questions", "ADD COLUMN question_number INTEGER"),
            ("pending_questions", "ADD COLUMN option_a TEXT"),
            ("pending_questions", "ADD COLUMN option_b TEXT"),
            ("pending_questions", "ADD COLUMN option_c TEXT"),
            ("pending_questions", "ADD COLUMN option_d TEXT"),
            ("pending_questions", "ADD COLUMN correct_answer TEXT"),
            ("pending_questions", "ADD COLUMN explanation TEXT"),
            ("pending_questions", "ADD COLUMN passage_text TEXT"),
            ("pending_questions", "ADD COLUMN diagram_instruction TEXT"),
            ("pending_questions", "ADD COLUMN unit_number TEXT"),
            ("pending_questions", "ADD COLUMN unit_title TEXT"),
            ("pending_questions", "ADD COLUMN section_number TEXT"),
            ("pending_questions", "ADD COLUMN section_title TEXT"),
            ("pending_questions", "ADD COLUMN topic_title TEXT"),
            ("pending_questions", "ADD COLUMN subtopic TEXT"),
            ("pending_questions", "ADD COLUMN confidence TEXT"),
            ("pending_questions", "ADD COLUMN classification_reason TEXT"),
            ("pending_questions", "ADD COLUMN status TEXT DEFAULT 'pending'"),
            ("resources", "ADD COLUMN unit_number INTEGER"),
            ("questions", "ADD COLUMN question_number INTEGER"),
            ("questions", "ADD COLUMN source_year TEXT"),
            ("questions", "ADD COLUMN passage_text TEXT"),
            ("questions", "ADD COLUMN diagram_instruction TEXT"),
            ("questions", "ADD COLUMN curriculum_section_id INTEGER"),
            ("questions", "ADD COLUMN curriculum_topic_id INTEGER"),
        ]
        for table, action in sqlite_migrations:
            try:
                cursor.execute(f"ALTER TABLE {table} {action};")
            except sqlite3.OperationalError:
                pass

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_student_code ON users(student_code) WHERE student_code IS NOT NULL")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone_number ON users(phone_number) WHERE phone_number IS NOT NULL AND phone_number <> ''")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unified_phone_number ON unified_accounts(phone_number) WHERE phone_number IS NOT NULL AND phone_number <> ''")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(LOWER(email)) WHERE email IS NOT NULL AND email <> ''")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unified_email ON unified_accounts(LOWER(email)) WHERE email IS NOT NULL AND email <> ''")
        cursor.execute("UPDATE users SET account_status = 'ACTIVE' WHERE account_status IS NULL OR account_status = ''")
        cursor.execute("UPDATE users SET registered_at = CURRENT_TIMESTAMP WHERE registered_at IS NULL")

        # Seed Default Administrator for SQLite
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, is_verified) 
                VALUES (?, ?, ?, ?)
            ''', ("admin", generate_password_hash("admin123"), "admin", 1))

        cursor.execute("SELECT 1 FROM unified_accounts WHERE username = ?", ("admin",))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO unified_accounts
                    (username, password_hash, role, first_name, last_name)
                VALUES (?, ?, ?, ?, ?)
            ''', ("admin", generate_password_hash("admin123"), "admin", "Unified", "Admin"))

        for number in range(1, 5):
            username = f"student{number}"
            display_number = ("One", "Two", "Three", "Four")[number - 1]
            cursor.execute("SELECT 1 FROM unified_accounts WHERE username = ?", (username,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO unified_accounts
                        (username, password_hash, role, first_name, last_name, student_code)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, generate_password_hash("student123"), "student", "Student", display_number, f"ST{number:03d}"))

        conn.commit()
        conn.close()
        print("✅ SQLite Database Initialized & Schema Altered successfully.")

if __name__ == "__main__":
    init_db()
