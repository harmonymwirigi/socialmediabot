# run.py
from app import create_app
from flask import render_template
import datetime

app = create_app()

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)