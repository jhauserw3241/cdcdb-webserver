from flask import render_template

class About:
    def index(self, request, session):
        return render_template('about/index.html')
