from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:4200"])

@app.route('/test')
def test():
    return {'message': 'Flask server with CORS is working!'}

@app.route('/api/user/register', methods=['OPTIONS', 'POST'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    return {'message': 'Registration endpoint'}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)