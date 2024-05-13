import os
import flask
import flask_sqlalchemy
import flask_praetorian
import flask_cors
from flask import jsonify
from werkzeug.utils import secure_filename
from phoneme_to_viseme import viseme_char_map
from phoneme_decoder import timit_index_map
from tensorflow import keras
import numpy as np
from python_speech_features import mfcc
from librosa import load, resample
import time
import traceback


# Backend database, cors initalization
print("Initializing Flask app")  # Add this line

db = flask_sqlalchemy.SQLAlchemy()
guard = flask_praetorian.Praetorian()
# cors = flask_cors.CORS()
cors = flask_cors.CORS(supports_credentials=True, expose_headers=["Access-Control-Allow-Origin", "Access-Control-Allow-Headers", "Access-Control-Allow-Methods"])



# A generic user model that might be used by an app powered by flask-praetorian
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    roles = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, server_default='true')

    @property
    def rolenames(self):
        try:
            return self.roles.split(',')
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

    def is_valid(self):
        return self.is_active


# Initialize flask app for the example
app = flask.Flask(__name__, static_folder='../build', static_url_path=None)
# flask_cors.CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

app.debug = True
app.config['SECRET_KEY'] = 'top secret'
app.config['JWT_ACCESS_LIFESPAN'] = {'hours': 24}
app.config['JWT_REFRESH_LIFESPAN'] = {'days': 30}
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['UPLOAD_EXTENSIONS'] = ['.wav', '.mp3','.webm']
app.config['STATIC_SOURCE'] = 'static'

try:
    model = keras.models.load_model(os.path.join(
        app.config['STATIC_SOURCE'], 'BI_LSTM_512_30epochs_dropout01.h5'))
except OSError as e:
    model = None

SAMPLE_RATE = 16000

# Initialize the flask-praetorian instance for the app
guard.init_app(app, User)

# Initialize a local database for the example
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.getcwd(), 'database.db')}"
db.init_app(app)

# Initializes CORS so that the api_tool can talk to the example app
cors.init_app(app)

# Add users for the example
with app.app_context():
    db.create_all()
    if db.session.query(User).filter_by(username='1').count() < 1:
        db.session.add(User(
            username='1',
            password=guard.hash_password('1'),
            roles='admin'
        ))
    db.session.commit()


# Set up some routes for the example
@app.route('/api/')
def home():
    print("Yesyrsaihf")
    return {"Hello": "World"}, 200


@app.route('/api/time')
def get_current_time():
    return{'time': time.time()}


@app.route('/api/login', methods=['POST'])
def login():
    """
    Logs a user in by parsing a POST request containing user credentials and
    issuing a JWT token.
    .. example::
       $ curl http://localhost:5001/api/login -X POST \
         -d '{"username":"1","password":"1"}'
    """
    req = flask.request.get_json(force=True)
    username = req.get('username', None)
    password = req.get('password', None)
    user = guard.authenticate(username, password)
    ret = {'access_token': guard.encode_jwt_token(user)}
    return ret, 200


@app.route('/api/refresh', methods=['POST'])
def refresh():
    """
    Refreshes an existing JWT by creating a new one that is a copy of the old
    except that it has a refrehsed access expiration.
    .. example::
       $ curl http://localhost:5001/refresh -X GET \
         -H "Authorization: Bearer <your_token>"
    """
    print("refresh request")
    old_token = flask.request.get_data()
    new_token = guard.refresh_jwt_token(old_token)
    ret = {'access_token': new_token}
    return ret, 200


@app.route('/api/protected')
# @flask_praetorian.auth_required
def protected():
    """
    A protected endpoint. The auth_required decorator will require a header
    containing a valid JWT
    .. example::
       $ curl http://localhost:5001/api/protected -X GET \
         -H "Authorization: Bearer <your_token>"
    """
    return {"message": f'protected endpoint (allowed user {flask_praetorian.current_user().username})'}


# @app.route('/api/upload', methods=['POST'])
# # @flask_praetorian.auth_required
# def file_upload():

# @app.route('/api/upload', methods=['POST'])
# def file_upload(): 
#     print('Received file upload request')
#     try:
#         # Retrieve the file from the request
#         print('hi')
#         file = flask.request.files['file']
#         print('uploaded file is',file)

#         # Check if the file exists
#         if not file:
#             return jsonify(status=400, message='No file provided')

#         # Check if the file has a valid extension
#         filename = secure_filename(file.filename)
#         print('filename',filename)
#         print('allowed extensions:', app.config['UPLOAD_EXTENSIONS'])
#         viseme_result = None
#         if not allowed_file(filename):
#             print("not working")
#             return jsonify(status=400, message='Invalid file extension')
#         print('reached line 180')
#         # Save the file to the UPLOAD_FOLDER
#         destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         print('destination is: ',destination)
#         file.save(destination)
#         print('successfull')

#         # Check if the machine learning model is loaded
#         if model is None:
#             return jsonify(status=500, message='Model not loaded')

#         # Perform file processing using the loaded model
#         # (insert your model processing code here)

#         # Return a successful response with the result
#         return jsonify(status=200, result=viseme_result)

#     except Exception as e:
#         # Log the exception for debugging
#         traceback.print_exc()

#         # Return an error response
#         return jsonify(status=500, message='Internal Server Error')

# def allowed_file(filename):
#     # Check if the file extension is allowed
#     # print('allowed file',filename.rsplit('.', 1))
#     # return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['UPLOAD_EXTENSIONS']
#     # return '.' in filename and filename.rsplit('.', 1)[1].lower().strip() in app.config['UPLOAD_EXTENSIONS']
#     exti = filename.rsplit('.', 1)[1].lower()
#     print(filename.rsplit('.', 1))
#     ext = '.'+exti
#     print('Extension:', ext)
#     print('Allowed Extensions:', app.config['UPLOAD_EXTENSIONS'])
#     print('Comparison Result:', ext in app.config['UPLOAD_EXTENSIONS'])

#     return '.' in filename and ext in app.config['UPLOAD_EXTENSIONS']

#     """
#     Endpoint for receiving the uploaded file and returning the mapped model prediction
#     """
#     file = flask.request.files['file']
#     filename = secure_filename(file.filename)
#     print(file)
#     print(filename)

#     if filename != '':
#         file_ext = os.path.splitext(filename)[1]
#         print(file_ext)
#         if file_ext not in app.config['UPLOAD_EXTENSIONS']:
#             return flask.jsonify(status=404, message='Extension')

#     destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     file.save(destination)

#     if model == None:
#         return flask.jsonify(status=404, message='Model')

#     # Pass the file to the ml model
#     audio_file, loaded_sample_rate = load(destination)
#     # Change the frequency
#     audio_file = resample(audio_file, loaded_sample_rate, SAMPLE_RATE)
#     # Extract mfcc
#     mfcc_coeff = mfcc(audio_file, SAMPLE_RATE)
#     # Use the model
#     prediction = model.predict(mfcc_coeff[np.newaxis, :, :])
#     # Map from model encoding to phones
#     phone_result = [timit_index_map[np.argmax(ph)] for ph in prediction[0]]
#     # Map from phones to visemes
#     viseme_result = [viseme_char_map[ph] for ph in phone_result]

#     return flask.jsonify(status=200, result=viseme_result)


# @app.route('/api/upload', methods=['OPTIONS'])
# def handle_options():
#     return '', 200, {
#         'Access-Control-Allow-Origin': 'http://localhost:3000',
#         'Access-Control-Allow-Headers': 'Content-Type, Authorization',
#         'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE'
#     }

@app.route('/api/upload', methods=['POST'])
# @flask_praetorian.auth_required
def file_upload():
    """
    Endpoint for receiving the uploaded file and returning the mapped model prediction
    """
    print("ji")
    file = flask.request.files['file']
    filename = secure_filename(file.filename)
    print(file)
    print(filename)

    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        print(file_ext)
        print(app.config['UPLOAD_EXTENSIONS'])
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            return flask.jsonify(status=404, message='Extension')
        

    destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print("destination is",destination)
    file.save(destination)

    if model == None:
        return flask.jsonify(status=404, message='Model')

        # Check if the file is a webm file and convert it to wav
    if file_ext == '.webm':
        audio_file, loaded_sample_rate = load(destination)
        # Convert webm to wav format
        destination = destination.replace('.webm', '.wav')
        os.system(f"ffmpeg -i {destination} {destination.replace('.webm', '.wav')}")
    else:
        audio_file, loaded_sample_rate = load(destination)
    print('loaded_sample_rate', loaded_sample_rate)
    print('audio_file',audio_file)
    # Change the frequency
    # audio_file = resample(audio_file, loaded_sample_rate, SAMPLE_RATE)
    audio_file=resample(audio_file, orig_sr=loaded_sample_rate, target_sr=SAMPLE_RATE)
    # Extract mfcc
    mfcc_coeff = mfcc(audio_file, SAMPLE_RATE)
    # Use the model
    prediction = model.predict(mfcc_coeff[np.newaxis, :, :])
    # Map from model encoding to phones
    phone_result = [timit_index_map[np.argmax(ph)] for ph in prediction[0]]
    # Map from phones to visemes
    viseme_result = [viseme_char_map[ph] for ph in phone_result]

    return flask.jsonify(status=200, result=viseme_result)

    



@app.route('/<path:path>')
def catch_all(path):
    print("Hello from catch all")
    if path != "" and os.path.exists(os.path.join('..', 'build', path)):
        return app.send_static_file(path)
    else:
        return app.send_static_file('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)