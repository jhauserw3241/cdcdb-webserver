from flask import render_template

#handles routes to the about page
class About:
    #returns a rendered "about" index page
	def index(self, request, session):
        return render_template('about/index.html')
