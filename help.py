from flask import render_template

#Handles requests for the help page
class Help:
  
  #Returns a rendered help page
    def index(self, request, session):
        return render_template('help/index.html')
