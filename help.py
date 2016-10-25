from flask import render_template

class Help:
    def index(self, request, session):
        return render_template('help/index.html')
