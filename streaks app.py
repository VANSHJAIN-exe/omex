from flask import Flask, render_template, session, redirect, url_for, request, flash
import json
from streaks import generate_study_plan_and_quizzes
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

MINDMAP_DATA = [{'title': 'Historiography: Development in the West', 'code': 'mindmap\nroot((Historiography: Development in the West))\n  Tradition of Historiography\n    Writing of critical historical narrative known as historiography\n    Historian\'s inclusion depends on conceptual framework\n    Ancient societies used cave paintings, storytelling, songs, ballads\n    Traditional means as sources of history in modern historiography\n  Modern Historiography\n    Four main characteristics\n      Based on scientific principles starting with relevant questions\n      Anthropocentric questions about deeds of ancient human societies\n      Answers supported by reliable evidence\n      Presents mankind\'s journey through past human deeds\n    Roots in ancient Greek writings\n    Herodotus, Greek historian, first used term "History"\n  Development of Scientific Perspective in Europe and Historiography\n    Progress in Philosophy and Science by 18th century\n    Belief in studying social and historical truths scientifically\n    Shift from Divine phenomena to objective history\n    1737: Gottingen University founded with independent history department\n  Notable Scholars\n    René Descartes 1596-1650\n      Emphasized verifying reliability of historical documents\n      Rule: accept nothing true until all doubt excluded\n    Voltaire 1694-1778\n      Included social traditions, trade, economy, agriculture in history\n      Founder of modern historiography\n    Georg Wilhelm Friedrich Hegel 1770-1831\n      Historical reality presented logically\n      Timeline indicates progress\n      History presentation changes with new evidence\n      Developed Dialectics: Thesis, Antithesis, Synthesis\n    Leopold von Ranké 1795-1886\n      Critical method of historical research\n      Emphasis on original documents and careful examination\n      Criticized imaginative narration\n    Karl Marx 1818-1883\n      History as history of class struggle\n      Human relationships shaped by means of production and class inequality\n      "Das Kapital" as key work\n    Annales School\n      Emerged early 20th century France\n      Expanded history beyond politics to climate, agriculture, trade, social divisions\n    Feminist Historiography\n      Restructuring history from women\'s perspective\n      Influenced by Simone de Beauvoir\n      Focus on women\'s employment, family life, social roles\n      Women portrayed as independent social class post-1990\n    Michel Foucault 1926-1984\n      Argued against chronological ordering of history\n      Focused on explaining transitions in history\n      Introduced "archaeology of knowledge"\n      Analyzed neglected areas: psychological disorders, medicine, prisons\n  Historical Research Method\n    Formulating relevant questions\n    Anthropocentric focus on human deeds\n    Supported by reliable evidence\n    Use of interdisciplinary methods: Archaeology, Epigraphy, Linguistics, Numismatics, Genealogy\n    Critical examination of sources\n    Writing historical narrative\n    Comparative analysis and understanding conceptual frameworks\n    Formulating hypotheses'}, {'title': 'Exercises and Questions on Historiography', 'code': 'mindmap\nroot((Exercises and Questions on Historiography))\n  Multiple Choice Questions\n    Founder of modern historiography: Voltaire\n    Author of "Archaeology of Knowledge": Michel Foucault\n  Identify Wrong Pair\n    Hegel - "Reason in History"\n    Ranké - "The Theory and Practice of History"\n    Herodotus - "The Histories"\n    Karl Marx - "Discourse on the Method" Wrong\n  Explain Concepts\n    Dialectics\n      Understanding events through opposites: Thesis, Antithesis, Synthesis\n    Annales School\n      History includes politics, climate, agriculture, trade, social psychology\n  Explain with Reason\n    Focus on women\'s life in historical research\n      Feminist historiography rethinks male-dominated history, includes women\'s roles\n    Foucault\'s "archaeology of knowledge"\n      Emphasizes explaining historical transitions over chronological truth\n  Concept Chart\n    Notable Scholars in Europe\n      René Descartes\n      Voltaire\n      Hegel\n      Leopold von Ranké\n      Karl Marx\n      Annales School\n      Feminist Historiography\n      Michel Foucault\n  Detailed Answers\n    Karl Marx\'s Class Theory\n      History is class struggle due to unequal access to means of production\n    Four Characteristics of Modern Historiography\n      Scientific principles, anthropocentric questions, evidence-based answers, human deeds graph\n    Feminist Historiography\n      Restructuring history from women\'s perspective, inclusion and rethinking male bias\n    Leopold von Ranké’s Perspective\n      Critical method, original documents, rejection of imaginative narration\n  Project Ideas\n    Write history of a favorite subject\n      Examples: History of Pen, Printing Technology, Computers'}, {'title': 'Historical Research Method and Its Features', 'code': "mindmap\nroot((Historical Research Method and Its Features))\n  Scientific Principles\n    Begins with formation of relevant questions\n    Questions are anthropocentric about human deeds\n    Answers supported by reliable evidence\n    Presents mankind's journey graphically\n  Interdisciplinary Methods Used\n    Archaeology\n    Archival Science\n    Manuscriptology\n    Epigraphy study of inscriptions\n    Lettering style analysis\n    Linguistics\n    Numismatics study of coins\n    Genealogy study of lineage\n  Process of Historical Research\n    Collect historical information\n    Highlight processes leading to historical transitions\n    Carry out comparative analysis\n    Understand time, space, and conceptual frameworks\n    Formulate relevant questions and hypotheses\n    Critically examine sources\n    Write historical narrative"}, {'title': 'Tradition and Modern Historiography', 'code': "mindmap\nroot((Tradition and Modern Historiography))\n  Tradition of Historiography\n    Writing of critical historical narrative\n    Historian's conceptual framework influences narrative\n    Ancient societies lacked formal historiography\n    Used cave paintings, storytelling, songs as history sources\n  Modern Historiography Characteristics\n    Scientific method based\n    Anthropocentric questions\n    Evidence-based answers\n    Human deeds as history graph\n    Rooted in ancient Greek writings Herodotus"}]


def get_db_connection():
    conn = sqlite3.connect('study_plan.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/initialize_study', methods=['GET'])
def initialize_study():
    """Initialize the study plan and store it in the database"""
    study_data = generate_study_plan_and_quizzes(MINDMAP_DATA)
    if study_data and 'study_plan' in study_data:
        conn = get_db_connection()
        conn.execute('INSERT INTO study_plans (data) VALUES (?)', (json.dumps(study_data),))
        conn.commit()
        study_plan_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        session['study_plan_id'] = study_plan_id
        session['quiz_progress'] = {
            'completed': {},
            'scores': {}
        }
        print("Study plan initialized successfully.")
        return redirect(url_for('study_plan_view'))
    else:
        flash("Failed to generate study plan.")
        print("Failed to generate study plan.")
        return redirect(url_for('home'))


@app.route('/study_plan')
def study_plan_view():
    """Display the study plan with all quizzes available"""
    if 'study_plan_id' not in session:
        print("Study plan not found in session, redirecting to initialize_study.")
        return redirect(url_for('initialize_study'))

    conn = get_db_connection()
    study_plan_data = conn.execute('SELECT data FROM study_plans WHERE id = ?', (session['study_plan_id'],)).fetchone()
    user_id = session.get('user_id', 1)  # Assuming user_id is stored in session
    tokens_data = conn.execute('SELECT tokens FROM user_tokens WHERE user_id = ?', (user_id,)).fetchone()
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
                               tokens=tokens)
    else:
        flash("Study plan not found.")
        return redirect(url_for('initialize_study'))


@app.route('/quiz/<int:topic_index>/<int:subtopic_index>')
def view_quiz(topic_index, subtopic_index):
    """Display a quiz"""
    if 'study_plan_id' not in session:
        return redirect(url_for('initialize_study'))

    conn = get_db_connection()
    study_plan_data = conn.execute('SELECT data FROM study_plans WHERE id = ?', (session['study_plan_id'],)).fetchone()
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
        flash("Quiz not found.")
    else:
        flash("Study plan not found.")
    return redirect(url_for('study_plan_view'))


@app.route('/submit_quiz/<int:topic_index>/<int:subtopic_index>', methods=['POST'])
def submit_quiz(topic_index, subtopic_index):
    """Process quiz submission and track progress"""
    if 'study_plan_id' not in session or 'quiz_progress' not in session:
        return redirect(url_for('initialize_study'))

    conn = get_db_connection()
    study_plan_data = conn.execute('SELECT data FROM study_plans WHERE id = ?', (session['study_plan_id'],)).fetchone()
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

                # Calculate tokens
                def calculate_tokens(score, total):
                    if score >= 0.9 * total:
                        return 20
                    elif score >= 0.7 * total:
                        return 10
                    elif score >= 0.4 * total:
                        return 5
                    else:
                        return 0

                tokens = calculate_tokens(score, total)

                # Update progress
                key = f"{topic_index}_{subtopic_index}"
                session['quiz_progress']['completed'][key] = True
                session['quiz_progress']['scores'][key] = {
                    'score': score,
                    'total': total,
                    'percentage': (score / total) * 100,
                    'tokens': tokens if score / total >= 0.7 else 0  # Award tokens only if passed
                }
                session.modified = True

                # Store tokens in the database
                if score / total >= 0.7:
                    conn = get_db_connection()
                    user_id = session.get('user_id', 1)  # Assuming user_id is stored in session
                    current_tokens = conn.execute('SELECT tokens FROM user_tokens WHERE user_id = ?',
                                                  (user_id,)).fetchone()
                    if current_tokens:
                        new_tokens = current_tokens['tokens'] + tokens
                        conn.execute('UPDATE user_tokens SET tokens = ? WHERE user_id = ?', (new_tokens, user_id))
                    else:
                        conn.execute('INSERT INTO user_tokens (user_id, tokens) VALUES (?, ?)', (user_id, tokens))
                    conn.commit()
                    conn.close()

                return render_template('quiz_result.html',
                                       score=score,
                                       total=total,
                                       percentage=(score / total) * 100,
                                       passed=score / total >= 0.7,
                                       tokens=tokens if score / total >= 0.7 else 0,
                                       topic_name=topic.get('topic', ''),
                                       subtopic_name=subtopic.get('name', ''),
                                       topic_index=topic_index,
                                       subtopic_index=subtopic_index)
        flash("Quiz not found.")
    else:
        flash("Study plan not found.")
    return redirect(url_for('study_plan_view'))


@app.route('/')
def home():
    return redirect(url_for('study_plan_view'))


if __name__ == '__main__':
    app.run(debug=True)