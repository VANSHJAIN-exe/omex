from flask import Flask, render_template, request, redirect, url_for
import os
from mindmaps import *
import time
from markupsafe import Markup


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if file := request.files.get('file'):
            start_time = time.time()

            try:
                # Process PDF
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp.pdf")
                file.save(pdf_path)
                text = extract_text(pdf_path)

                # Generate and process mindmaps
                ai_output = generate_mindmaps(text)
                print(ai_output)
                mindmaps = process_mindmaps(ai_output)
                print(mindmaps)

                return render_template('mindmaps_result.html',
                                       mindmaps=mindmaps,
                                       time=time.time() - start_time)

            except Exception as e:
                return render_template('error.html',
                                       error=str(e),
                                       time=time.time() - start_time)

    return render_template('mindmaps_upload.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

