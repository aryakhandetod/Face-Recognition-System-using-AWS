from flask import Flask, request, render_template_string, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
import boto3
import io
import os
import base64
from PIL import Image
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

s3 = boto3.resource('s3')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Boto3 clients
rekognition = boto3.client('rekognition', region_name='us-east-1')
dynamodb = boto3.client('dynamodb', region_name='us-east-1')

# Flask-WTF forms
class PhotoForm(FlaskForm):
    photo = FileField('Upload Image', validators=[FileRequired()])

class NewPersonForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    photo = FileField('Upload Image', validators=[FileRequired()])
    submit = SubmitField('Upload')

@app.route("/", methods=['GET', 'POST'])
def upload_image():
    form = PhotoForm()
    new_person_form = NewPersonForm()
    message = None

    if 'webcam_image' in request.form:
        # Decode the base64 image data
        image_data = request.form['webcam_image'].split(',')[1]
        image_binary = base64.b64decode(image_data)

        # Call Rekognition to search for faces
        response = rekognition.search_faces_by_image(
            CollectionId='famouspersons',
            Image={'Bytes': image_binary}
        )

        found = False
        messages = []
        for match in response['FaceMatches']:
            face_id = match['Face']['FaceId']
            confidence = match['Face']['Confidence']
            messages.append(f"Match Found: FaceId={face_id}, Confidence={confidence}%")

            face = dynamodb.get_item(
                TableName='face_recognition',
                Key={'RekognitionId': {'S': face_id}}
            )

            if 'Item' in face:
                fullname = face['Item']['FullName']['S']
                messages.append(f"Found Person: {fullname}")
                found = True

        if not found:
            messages.append("Person cannot be recognized")
            return render_template_string('''
                <!doctype html>
                <html lang="en">
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
                    <title>Image Upload and Recognition</title>
                </head>
                <body>
                    <nav class="navbar navbar-expand-lg navbar-light bg-light">
                        <a class="navbar-brand" href="#">Image Recognition</a>
                    </nav>
                    <div class="container">
                        <div class="row">
                            <div class="col-md-6 offset-md-3">
                                <h1 class="text-center">Add New Person</h1>
                                <form method="POST" enctype="multipart/form-data">
                                    {{ new_person_form.hidden_tag() }}
                                    <div class="form-group">
                                        {{ new_person_form.name.label(class="form-label") }}
                                        {{ new_person_form.name(class="form-control") }}
                                    </div>
                                    <div class="form-group">
                                        {{ new_person_form.photo.label(class="form-label") }}
                                        {{ new_person_form.photo(class="form-control-file") }}
                                    </div>
                                    {{ new_person_form.submit(class="btn btn-primary btn-block") }}
                                </form>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
            ''', new_person_form=new_person_form)

        message = "<br>".join(messages)

    elif form.validate_on_submit():
        photo = form.photo.data
        filename = secure_filename(photo.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)

        # Process the image
        with Image.open(filepath) as image:
            stream = io.BytesIO()
            image.save(stream, format="JPEG")
            image_binary = stream.getvalue()

        # Call Rekognition to search for faces
        response = rekognition.search_faces_by_image(
            CollectionId='famouspersons',
            Image={'Bytes': image_binary}
        )

        found = False
        messages = []
        for match in response['FaceMatches']:
            face_id = match['Face']['FaceId']
            confidence = match['Face']['Confidence']
            messages.append(f"Match Found: FaceId={face_id}, Confidence={confidence}%")

            face = dynamodb.get_item(
                TableName='face_recognition',
                Key={'RekognitionId': {'S': face_id}}
            )

            if 'Item' in face:
                fullname = face['Item']['FullName']['S']
                messages.append(f"Found Person: {fullname}")
                found = True

        if not found:
            messages.append("Person cannot be recognized")
            return render_template_string('''
                <!doctype html>
                <html lang="en">
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
                    <title>Image Upload and Recognition</title>
                </head>
                <body>
                    <nav class="navbar navbar-expand-lg navbar-light bg-light">
                        <a class="navbar-brand" href="#">Image Recognition</a>
                    </nav>
                    <div class="container">
                        <div class="row">
                            <div class="col-md-6 offset-md-3">
                                <h1 class="text-center">Add New Person</h1>
                                <form method="POST" enctype="multipart/form-data">
                                    {{ new_person_form.hidden_tag() }}
                                    <div class="form-group">
                                        {{ new_person_form.name.label(class="form-label") }}
                                        {{ new_person_form.name(class="form-control") }}
                                    </div>
                                    <div class="form-group">
                                        {{ new_person_form.photo.label(class="form-label") }}
                                        {{ new_person_form.photo(class="form-control-file") }}
                                    </div>
                                    {{ new_person_form.submit(class="btn btn-primary btn-block") }}
                                </form>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
            ''', new_person_form=new_person_form)

        message = "<br>".join(messages)

    elif new_person_form.validate_on_submit():
        name = new_person_form.name.data
        photo = new_person_form.photo.data
        filename = secure_filename(photo.filename)
       
        filename = secure_filename(photo.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)

        # Upload the image to S3
        with open(filepath, 'rb') as file:
            s3_object = s3.Object('cc-project-images', filename)  # Replace 'your_bucket_name' with your S3 bucket name
            s3_object.put(Body=file, Metadata={'FullName': name})
            print(f"Uploaded {filename} to S3 bucket with name {name}")

        # Optionally add the face to Rekognition collection
        with Image.open(filepath) as image:
            stream = io.BytesIO()
            image.save(stream, format="JPEG")
            image_binary = stream.getvalue()

        rekognition.index_faces(
            CollectionId='famouspersons',
            Image={'Bytes': image_binary},
            ExternalImageId=name,
            DetectionAttributes=['ALL']
        )

        message = "New person added successfully!"

    return render_template_string('''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
            <title>Image Upload and Recognition</title>
            <style>
                .container {
                    margin-top: 30px;
                }
                .video-container {
                    display: flex;
                    justify-content: center;
                    margin-top: 20px;
                }
                #snap {
                    display: block;
                    margin: 20px auto;
                }
                .results {
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-light bg-light">
                <a class="navbar-brand" href="#">Image Recognition</a>
            </nav>
            <div class="container">
                <div class="row">
                    <div class="col-md-6 offset-md-3">
                        <h1 class="text-center">Upload Image for Recognition</h1>
                        <form method="POST" enctype="multipart/form-data" class="mt-4">
                            {{ form.csrf_token }}
                            <div class="form-group">
                                {{ form.photo.label(class="form-label") }}
                                {{ form.photo(class="form-control-file") }}
                            </div>
                            <button type="submit" class="btn btn-primary btn-block">Upload</button>
                        </form>
                        
                        <h2 class="text-center mt-4">OR</h2>
                        
                        <h1 class="text-center">Capture Image from Webcam</h1>
                        <div class="video-container">
                            <video id="video" width="640" height="480" autoplay></video>
                        </div>
                        <button id="snap" class="btn btn-secondary">Capture Photo</button>
                        <canvas id="canvas" width="640" height="480" style="display:none;"></canvas>
                        <form id="webcamForm" method="POST">
                            <input type="hidden" name="webcam_image" id="webcam_image">
                            <button type="submit" class="btn btn-success btn-block">Upload Captured Photo</button>
                        </form>
                        
                        {% if message %}
                        <div class="results">
                            <h2 class="text-center">Results:</h2>
                            <p>{{ message|safe }}</p>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
            
            <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
            <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
            <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const snap = document.getElementById('snap');
            const webcamForm = document.getElementById('webcamForm');
            const webcamImage = document.getElementById('webcam_image');

            // Get access to the camera
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ video: true }).then(function(stream) {
                    video.srcObject = stream;
                    video.play();
                });
            }

            // Capture the image
            snap.addEventListener('click', function() {
                const context = canvas.getContext('2d');
                context.drawImage(video, 0, 0, 640, 480);
                const dataURL = canvas.toDataURL('image/jpeg');
                webcamImage.value = dataURL;
                
                // Hide the video and show the canvas
                video.style.display = 'none';
                canvas.style.display = 'block';
                
                // After 3 seconds, hide the canvas and show the video
                setTimeout(function() {
                    canvas.style.display = 'none';
                    video.style.display = 'block';
                }, 3000);
            });
            </script>
        </body>
        </html>
    ''', form=form, new_person_form=new_person_form, message=message)

if __name__ == "__main__":
    app.run(debug=True)
