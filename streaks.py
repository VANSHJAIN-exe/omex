import requests
import json
from mindmaps import *

# --- Configuration ---
AI_API_ENDPOINT = 'https://beta.sree.shop/v1'  # Replace with your AI API endpoint
AI_API_KEY = 'ddc-beta-302qn0hvai-cSFWYwzhNxSqiqpoEU5BCGYpNgZpJjguBSO'  # Replace with your AI API key
AI_MODEL_NAME = 'Provider-5/gpt-4o'  # Or the name of the model you are using

# --- Example Mindmap Data (Replace with your actual data) ---
MINDMAP_DATA = [{'title': 'Historiography: Development in the West', 'code': 'mindmap\nroot((Historiography: Development in the West))\n  Tradition of Historiography\n    Writing of critical historical narrative known as historiography\n    Historian\'s inclusion depends on conceptual framework\n    Ancient societies used cave paintings, storytelling, songs, ballads\n    Traditional means as sources of history in modern historiography\n  Modern Historiography\n    Four main characteristics\n      Based on scientific principles starting with relevant questions\n      Anthropocentric questions about deeds of ancient human societies\n      Answers supported by reliable evidence\n      Presents mankind\'s journey through past human deeds\n    Roots in ancient Greek writings\n    Herodotus, Greek historian, first used term "History"\n  Development of Scientific Perspective in Europe and Historiography\n    Progress in Philosophy and Science by 18th century\n    Belief in studying social and historical truths scientifically\n    Shift from Divine phenomena to objective history\n    1737: Gottingen University founded with independent history department\n  Notable Scholars\n    René Descartes 1596-1650\n      Emphasized verifying reliability of historical documents\n      Rule: accept nothing true until all doubt excluded\n    Voltaire 1694-1778\n      Included social traditions, trade, economy, agriculture in history\n      Founder of modern historiography\n    Georg Wilhelm Friedrich Hegel 1770-1831\n      Historical reality presented logically\n      Timeline indicates progress\n      History presentation changes with new evidence\n      Developed Dialectics: Thesis, Antithesis, Synthesis\n    Leopold von Ranké 1795-1886\n      Critical method of historical research\n      Emphasis on original documents and careful examination\n      Criticized imaginative narration\n    Karl Marx 1818-1883\n      History as history of class struggle\n      Human relationships shaped by means of production and class inequality\n      "Das Kapital" as key work\n    Annales School\n      Emerged early 20th century France\n      Expanded history beyond politics to climate, agriculture, trade, social divisions\n    Feminist Historiography\n      Restructuring history from women\'s perspective\n      Influenced by Simone de Beauvoir\n      Focus on women\'s employment, family life, social roles\n      Women portrayed as independent social class post-1990\n    Michel Foucault 1926-1984\n      Argued against chronological ordering of history\n      Focused on explaining transitions in history\n      Introduced "archaeology of knowledge"\n      Analyzed neglected areas: psychological disorders, medicine, prisons\n  Historical Research Method\n    Formulating relevant questions\n    Anthropocentric focus on human deeds\n    Supported by reliable evidence\n    Use of interdisciplinary methods: Archaeology, Epigraphy, Linguistics, Numismatics, Genealogy\n    Critical examination of sources\n    Writing historical narrative\n    Comparative analysis and understanding conceptual frameworks\n    Formulating hypotheses'}, {'title': 'Exercises and Questions on Historiography', 'code': 'mindmap\nroot((Exercises and Questions on Historiography))\n  Multiple Choice Questions\n    Founder of modern historiography: Voltaire\n    Author of "Archaeology of Knowledge": Michel Foucault\n  Identify Wrong Pair\n    Hegel - "Reason in History"\n    Ranké - "The Theory and Practice of History"\n    Herodotus - "The Histories"\n    Karl Marx - "Discourse on the Method" Wrong\n  Explain Concepts\n    Dialectics\n      Understanding events through opposites: Thesis, Antithesis, Synthesis\n    Annales School\n      History includes politics, climate, agriculture, trade, social psychology\n  Explain with Reason\n    Focus on women\'s life in historical research\n      Feminist historiography rethinks male-dominated history, includes women\'s roles\n    Foucault\'s "archaeology of knowledge"\n      Emphasizes explaining historical transitions over chronological truth\n  Concept Chart\n    Notable Scholars in Europe\n      René Descartes\n      Voltaire\n      Hegel\n      Leopold von Ranké\n      Karl Marx\n      Annales School\n      Feminist Historiography\n      Michel Foucault\n  Detailed Answers\n    Karl Marx\'s Class Theory\n      History is class struggle due to unequal access to means of production\n    Four Characteristics of Modern Historiography\n      Scientific principles, anthropocentric questions, evidence-based answers, human deeds graph\n    Feminist Historiography\n      Restructuring history from women\'s perspective, inclusion and rethinking male bias\n    Leopold von Ranké’s Perspective\n      Critical method, original documents, rejection of imaginative narration\n  Project Ideas\n    Write history of a favorite subject\n      Examples: History of Pen, Printing Technology, Computers'}, {'title': 'Historical Research Method and Its Features', 'code': "mindmap\nroot((Historical Research Method and Its Features))\n  Scientific Principles\n    Begins with formation of relevant questions\n    Questions are anthropocentric about human deeds\n    Answers supported by reliable evidence\n    Presents mankind's journey graphically\n  Interdisciplinary Methods Used\n    Archaeology\n    Archival Science\n    Manuscriptology\n    Epigraphy study of inscriptions\n    Lettering style analysis\n    Linguistics\n    Numismatics study of coins\n    Genealogy study of lineage\n  Process of Historical Research\n    Collect historical information\n    Highlight processes leading to historical transitions\n    Carry out comparative analysis\n    Understand time, space, and conceptual frameworks\n    Formulate relevant questions and hypotheses\n    Critically examine sources\n    Write historical narrative"}, {'title': 'Tradition and Modern Historiography', 'code': "mindmap\nroot((Tradition and Modern Historiography))\n  Tradition of Historiography\n    Writing of critical historical narrative\n    Historian's conceptual framework influences narrative\n    Ancient societies lacked formal historiography\n    Used cave paintings, storytelling, songs as history sources\n  Modern Historiography Characteristics\n    Scientific method based\n    Anthropocentric questions\n    Evidence-based answers\n    Human deeds as history graph\n    Rooted in ancient Greek writings Herodotus"}]

def generate_study_plan_and_quizzes(mindmap_data=None):
    """Generate a study plan with topics, subtopics, and quizzes without timing constraints"""
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )

    try:
        prompt = """Generate a comprehensive study plan based on the following mindmap data. 
        The study plan should list the main topics (from the 'title' of each mindmap) and the subtopics 
        (from the structure within the 'code'). For each main topic and subtopic, provide an estimated 
        time for study in minutes (but this will be only for reference, not enforced).

        For each subtopic, create 10 multiple-choice quiz questions. Each question should have four 
        options (A, B, C, D) and clearly indicate the correct answer.

        The output should be a JSON object with this structure:
        {
          "study_plan": [
            {
              "topic": "[Topic Name]",
              "duration_minutes": [Recommended Time],
              "subtopics": [
                {
                  "name": "[Subtopic Name]",
                  "duration_minutes": [Recommended Time],
                  "quiz": [quiz questions...]
                }
              ]
            }
          ]
        }
        """ + json.dumps(mindmap_data)

        response = client.chat.completions.create(
            model="Provider-5/gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("Error during study plan generation:", e)
        return None


if __name__ == "__main__":
        study_data = generate_study_plan_and_quizzes(MINDMAP_DATA)
        if study_data:
            print("\n--- Generated Study Data ---")
            print(study_data)
        else:
            print("Failed to generate")
