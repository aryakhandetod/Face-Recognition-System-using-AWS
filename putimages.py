import boto3

s3 = boto3.resource('s3')

# Get list of objects for indexing
images=[('image1.jpg','Elon Musk'),
      ('image2.jpg','Elon Musk'),
      ('image3.jpg','Bill Gates'),
      ('image4.jpg','Bill Gates'),
      ('image5.jpg','Sundar Pichai'),
      ('image6.jpeg','Sumedh Kate'),
      ('image7.jpeg','Dipkul Khandelwal'),
      ('image8.jpeg','Arya Khandetod'),
      ('image9.jpeg','Aishwarya Kharade')
      ]

# Iterate through list to upload objects to S3   
for image in images:
    file = open(image[0],'rb') #rb represents binary read mode
    object = s3.Object('cc-project-images','index/'+ image[0])
    ret = object.put(Body=file,
                    Metadata={'FullName':image[1]})