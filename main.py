from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

@app.route('/')
def hello_world():
  return """
  <html>
    <body>
        <p> Hello There!</p>
    </body>
  </html>
  """
  
@app.route('/cats/')
def hello_world2():
  return 'Hello, Cats!'

if __name__ == '__main__':
  app.run()
