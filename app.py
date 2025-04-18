from flask import Flask, render_template, session, redirect, url_for, request, flash, jsonify
import json
import sqlite3
import os
import time
from markupsafe import Markup
from mindmaps import extract_text, clean_text, generate_mindmaps, process_mindmaps
from streaks import generate_study_plan_and_quizzes
from openai import OpenAI

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_here'  # Change this in production
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Initialize database
def init_db():
    conn = sqlite3.connect('study_plan.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT
        );
    ''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_tokens (
        user_id INTEGER PRIMARY KEY,
        tokens INTEGER DEFAULT 0
    );''')
    conn.commit()
    conn.close()


init_db()


def get_db_connection():
    conn = sqlite3.connect('study_plan.db')
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# --- Main Routes ---
@app.route('/')
def home():
    return render_template('home.html')


# --- Mindmaps Routes ---
@app.route('/mindmaps', methods=['GET', 'POST'])
def mindmaps_upload():
    if request.method == 'POST':
        if file := request.files.get('file'):
            if not allowed_file(file.filename):
                flash('Invalid file type. Please upload a PDF file.')
                return redirect(request.url)

            start_time = time.time()

            try:
                # Process PDF
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp.pdf")
                file.save(pdf_path)
                text = extract_text(pdf_path)
                cleaned_text = clean_text(text)

                # Generate and process mindmaps
                ai_output = generate_mindmaps(cleaned_text)
                mindmaps = process_mindmaps(ai_output)

                # Store mindmaps in session for potential study plan creation
                session['current_mindmaps'] = mindmaps
                session['pdf_filename'] = file.filename

                # Clean up the temporary file
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

                return render_template('mindmaps_result.html',
                                       mindmaps=mindmaps,
                                       filename=file.filename,
                                       time=time.time() - start_time)

            except Exception as e:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                return render_template('error.html',
                                       error=str(e),
                                       time=time.time() - start_time)

    return render_template('mindmaps_upload.html')


# --- Streaks Routes ---
@app.route('/streaks/study-plan', methods=['GET'])
def study_plan_landing():
    """Handle study plan access - either show existing or redirect to upload"""
    if 'current_mindmaps' in session:
        # If we have mindmaps, proceed to initialize study plan
        return redirect(url_for('initialize_study'))
    else:
        # No mindmaps exist, redirect to upload
        flash('Please upload a PDF to generate mindmaps first')
        return redirect(url_for('mindmaps_upload'))

# Update the initialize_study route
@app.route('/streaks/initialize', methods=['GET', 'POST'])
def initialize_study():
    """Initialize study plan with timeout handling"""
    if 'current_mindmaps' not in session:
        flash('No mindmap data found. Please upload a PDF first.')
        return redirect(url_for('mindmaps_upload'))

    try:
        mindmap_data = session['current_mindmaps']

        try:
            study_data = generate_study_plan_and_quizzes(mindmap_data)
        except Exception as e:
            flash(f'AI service timeout. Please try again with smaller content.')
            app.logger.error(f"AI Service Error: {str(e)}")
            return redirect(url_for('mindmaps_upload'))

        if not study_data or 'study_plan' not in study_data:
            flash('Failed to generate study plan from mindmaps')
            return redirect(url_for('mindmaps_upload'))

        # Store the study plan in database
        conn = get_db_connection()
        conn.execute('INSERT INTO study_plans (data) VALUES (?)',
                     (json.dumps(study_data),))
        conn.commit()
        study_plan_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        # Set up session variables
        session['study_plan_id'] = study_plan_id
        session['quiz_progress'] = {
            'completed': {},
            'scores': {}
        }

        return redirect(url_for('view_study_plan'))

    except Exception as e:
        flash('Error creating study plan. Please try again.')
        app.logger.error(f"Study Plan Creation Error: {str(e)}")
        return redirect(url_for('mindmaps_upload'))


@app.route('/streaks/view-study-plan')
def view_study_plan():
    """Display the actual study plan content"""
    if 'study_plan_id' not in session:
        return redirect(url_for('study_plan_landing'))

    conn = get_db_connection()
    study_plan_data = conn.execute(
        'SELECT data FROM study_plans WHERE id = ?',
        (session['study_plan_id'],)
    ).fetchone()

    user_id = session.get('user_id', 1)  # Default user ID for demo
    tokens_data = conn.execute(
        'SELECT tokens FROM user_tokens WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    conn.close()

    if study_plan_data:
        study_plan = json.loads(study_plan_data['data'])['study_plan']

        # Preprocess the study plan to include indices
        study_plan_with_indices = []
        for topic_index, topic in enumerate(study_plan):
            topic_with_indices = {
                'topic': topic['topic'],
                'duration_minutes': topic['duration_minutes'],
                'subtopics': []
            }
            for subtopic_index, subtopic in enumerate(topic['subtopics']):
                topic_with_indices['subtopics'].append({
                    'name': subtopic['name'],
                    'duration_minutes': subtopic['duration_minutes'],
                    'quiz': subtopic['quiz'],
                    'topic_index': topic_index,
                    'subtopic_index': subtopic_index
                })
            study_plan_with_indices.append(topic_with_indices)

        tokens = tokens_data['tokens'] if tokens_data else 0
        return render_template('study_plan.html',
                               study_plan=study_plan_with_indices,
                               quiz_progress=session.get('quiz_progress', {}),
                               tokens=tokens,
                               source_file=session.get('pdf_filename', 'Generated Content'))
    else:
        flash('Study plan not found')
        return redirect(url_for('initialize_study'))


@app.route('/streaks/quiz/<int:topic_index>/<int:subtopic_index>')
def view_quiz(topic_index, subtopic_index):
    """Display a quiz"""
    if 'study_plan_id' not in session:
        return redirect(url_for('initialize_study'))

    conn = get_db_connection()
    study_plan_data = conn.execute(
        'SELECT data FROM study_plans WHERE id = ?',
        (session['study_plan_id'],)
    ).fetchone()
    conn.close()

    if study_plan_data:
        study_plan = json.loads(study_plan_data['data'])['study_plan']

        if 0 <= topic_index < len(study_plan):
            topic = study_plan[topic_index]
            subtopics = topic.get('subtopics', [])
            if 0 <= subtopic_index < len(subtopics):
                subtopic = subtopics[subtopic_index]
                return render_template('quiz.html',
                                       questions=subtopic.get('quiz', []),
                                       topic_name=topic.get('topic', ''),
                                       subtopic_name=subtopic.get('name', ''),
                                       topic_index=topic_index,
                                       subtopic_index=subtopic_index)
        flash('Quiz not found')
    else:
        flash('Study plan not found')
    return redirect(url_for('study_plan_view'))


@app.route('/streaks/submit-quiz/<int:topic_index>/<int:subtopic_index>', methods=['POST'])
def submit_quiz(topic_index, subtopic_index):
    """Process quiz submission and track progress"""
    if 'study_plan_id' not in session or 'quiz_progress' not in session:
        return redirect(url_for('initialize_study'))

    conn = get_db_connection()
    study_plan_data = conn.execute(
        'SELECT data FROM study_plans WHERE id = ?',
        (session['study_plan_id'],)
    ).fetchone()
    conn.close()

    if study_plan_data:
        study_plan = json.loads(study_plan_data['data'])['study_plan']

        if 0 <= topic_index < len(study_plan):
            topic = study_plan[topic_index]
            subtopics = topic.get('subtopics', [])
            if 0 <= subtopic_index < len(subtopics):
                subtopic = subtopics[subtopic_index]
                questions = subtopic.get('quiz', [])

                # Calculate score
                user_answers = request.form
                score = 0
                total = len(questions)
                for i, q in enumerate(questions):
                    if 'answer' in q and user_answers.get(f'q{i}') == q['answer']:
                        score += 1

                # Calculate tokens (10 for passing, 20 for perfect score)
                tokens = 0
                if score / total >= 0.7:  # Passing threshold
                    tokens = 20 if score == total else 10

                # Update progress
                key = f"{topic_index}_{subtopic_index}"
                session['quiz_progress']['completed'][key] = True
                session['quiz_progress']['scores'][key] = {
                    'score': score,
                    'total': total,
                    'percentage': (score / total) * 100,
                    'tokens': tokens
                }
                session.modified = True

                # Update tokens in database if passed
                if tokens > 0:
                    conn = get_db_connection()
                    user_id = session.get('user_id', 1)
                    current_tokens = conn.execute(
                        'SELECT tokens FROM user_tokens WHERE user_id = ?',
                        (user_id,)
                    ).fetchone()

                    if current_tokens:
                        new_tokens = current_tokens['tokens'] + tokens
                        conn.execute(
                            'UPDATE user_tokens SET tokens = ? WHERE user_id = ?',
                            (new_tokens, user_id)
                        )
                    else:
                        conn.execute(
                            'INSERT INTO user_tokens (user_id, tokens) VALUES (?, ?)',
                            (user_id, tokens)
                        )
                    conn.commit()
                    conn.close()

                return render_template('quiz_result.html',
                                       score=score,
                                       total=total,
                                       percentage=(score / total) * 100,
                                       passed=score / total >= 0.7,
                                       tokens=tokens,
                                       topic_name=topic.get('topic', ''),
                                       subtopic_name=subtopic.get('name', ''),
                                       topic_index=topic_index,
                                       subtopic_index=subtopic_index)
        flash('Quiz not found')
    else:
        flash('Study plan not found')
    return redirect(url_for('study_plan_view'))


if __name__ == '__main__':
    app.run(debug=True)