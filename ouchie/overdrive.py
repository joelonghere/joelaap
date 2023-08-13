from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from tensorflow import keras
import tensorflow as tf
from PIL import Image
import numpy as np
import sqlalchemy
import uuid
import sqlalchemy_utils
import matplotlib.pyplot as plt
from classes import Face
from base64 import b64encode
from io import BytesIO
app = Flask(__name__)




def cdatabase():
    engine = sqlalchemy.create_engine('sqlite:///mine.sqlite') #Create test.sqlite automatically
    connection = engine.connect()
    metadata = sqlalchemy.MetaData()

    facesdb = sqlalchemy.Table('faces', metadata,
              sqlalchemy.Column('id', sqlalchemy.Integer(), primary_key=True),
              sqlalchemy.Column('session', sqlalchemy.Text(length=36), nullable=False,default=uuid.uuid4),
              sqlalchemy.Column('image', sqlalchemy.String(), nullable=False),
              sqlalchemy.Column('pred', sqlalchemy.Boolean(), nullable=False),
              sqlalchemy.Column('final', sqlalchemy.Boolean(), nullable=False)
              )
    metadata.create_all(engine)
def addrows(faces):
    engine = sqlalchemy.create_engine('sqlite:///mine.sqlite') #Create test.sqlite automatically
    connection = engine.connect()
    if not engine.dialect.has_table(connection, "faces"):
        cdatabase()
    metadata = sqlalchemy.MetaData()
    facesdb = sqlalchemy.Table('faces', metadata,autoload_with=connection)
    query = sqlalchemy.insert(facesdb)
    newrows = []
    if not session.get('uid'):
        session["uid"] = str(uuid.uuid4())
    for i in faces:
        newrow = {"session":session["uid"],"image":i.image, "pred":i.prediction, "final":i.final}
        newrows.append(newrow)
    connection.execute(query,newrows)
    connection.commit()
    connection.close()
def getrows():
    if not session.get('uid'):
        session["uid"] = str(uuid.uuid4())
    engine = sqlalchemy.create_engine('sqlite:///mine.sqlite') #Create test.sqlite automatically
    connection = engine.connect()
    if not engine.dialect.has_table(connection, "faces"):
        cdatabase()
    metadata = sqlalchemy.MetaData()
    facesdb = sqlalchemy.Table('faces', metadata,autoload_with=connection)
    # facesdb = sqlalchemy.Table('faces', metadata, autoload=True, autoload_with=engine)
    equery = sqlalchemy.select(facesdb.columns["image"],facesdb.columns["pred"],facesdb.columns["final"],facesdb.columns["id"]).where(sqlalchemy.sql.column('session') == session["uid"]).where(sqlalchemy.sql.column('final')==True)
    print(sqlalchemy.sql.column('final'))
    nequery = sqlalchemy.select(facesdb.columns["image"],facesdb.columns["pred"],facesdb.columns["final"],facesdb.columns["id"]).where(sqlalchemy.sql.column('session') == session["uid"]).where(sqlalchemy.sql.column('final')==False)
    return connection.execute(equery).fetchall(), connection.execute(nequery).fetchall()
def getmistakes():
    engine = sqlalchemy.create_engine('sqlite:///mine.sqlite') #Create test.sqlite automatically
    connection = engine.connect()
    if not engine.dialect.has_table(connection, "faces"):
        cdatabase()
    metadata = sqlalchemy.MetaData()
    facesdb = sqlalchemy.Table('faces', metadata,autoload_with=connection)
    equery = sqlalchemy.select(facesdb.columns["image"],facesdb.columns["pred"],facesdb.columns["final"],facesdb.columns["id"]).where(sqlalchemy.sql.column('final')!=sqlalchemy.sql.column('pred'))
    return connection.execute(equery).fetchall()
def newfinal(id,final):
    engine = sqlalchemy.create_engine('sqlite:///mine.sqlite') #Create test.sqlite automatically
    connection = engine.connect()
    if not engine.dialect.has_table(connection, "faces"):
        cdatabase()
    metadata = sqlalchemy.MetaData()
    facesdb = sqlalchemy.Table('faces', metadata,autoload_with=connection)
    print(final)
    print(connection.execute(sqlalchemy.select(facesdb).where(facesdb.columns["id"] == id)).fetchall())
    query = sqlalchemy.update(facesdb).values({'final': final}).where(facesdb.columns["id"] == id)
    
    connection.execute(query)
    print(connection.execute(sqlalchemy.select(facesdb).where(facesdb.columns["id"] == id)).fetchall())
    connection.commit()
    connection.close()
def rowstofaces(rows):
    faces = []
    for i in rows:
        face = Face(i[0],i[1],i[2],i[3])
        faces.append(face)
    return faces
class elderlyidentifier():
    def __init__(self, model):
        self.model = keras.models.load_model(model)
    def savefile(self,img):
        data = BytesIO()
        img.save(data, "JPEG")
        data64 = b64encode(data.getvalue())
        return data64.decode('utf-8')
        return u'data:img/jpeg;base64,'+data64.decode('utf-8')
    def predimg(self,img):
        return self.model.predict(img)
    def tonparray(self,img):
        # data1 = img.read()
        data2 = BytesIO(img)
        data3 = Image.open(data2)
        data3 = data3.resize((128,128))
        data4 = np.array(data3)
        data5 = tf.expand_dims(data4, 0)
        return data5
    def predarray(self,imgs):
        outs = []
        for i in imgs:
            outs.append(self.predimg(self.tonparray(i)))
        return outs
    def classifier(self,imgs):
        faces = []
        for i in imgs:
            i = i.read()
            skills = self.tonparray(i)

            
            image = self.savefile(tf.keras.preprocessing.image.array_to_img(skills[0]))
            faces.append(Face(image,(self.predimg(skills)[0]<0.5)[0]))
            # if self.predimg(skills)[0]>0.5:
            #     elder.append(image)
            # else:
            #     staff.append(b64encode((imgs[i].read())))
        return faces

@app.route("/")
def home():
    return render_template("maintemplate.html")
@app.route("/ageid")
def additional():
    return render_template("uploadfaces.html")

@app.route("/ageid", methods=["post"])
def saving():
    data = request.files.getlist("toys")
    model = elderlyidentifier("model.h5")
    faces = model.classifier(data)
    addrows(faces)
    return redirect("/ageid/selection")
# @app.route("/ageid/selection")
# def showoff():
#     elder, nonelder = getrows()
#     elder = rowstofaces(elder)
#     nonelder = rowstofaces(nonelder)
#     return render_template("viewfaces.html",elder=elder,nonelder=nonelder)
@app.route("/ageid/selection")
def changing():
    id =request.args.get('id')
    final =request.args.get('final')=="True"
    if id!=None:
        newfinal(id,final)
    elder, nonelder = getrows()
    elder = rowstofaces(elder)
    nonelder = rowstofaces(nonelder)
    print("pain")
    return render_template("viewfaces.html",elder=elder,nonelder=nonelder)
@app.route("/management")
def messups():
    mistakes = getmistakes()
    mistakes = rowstofaces(mistakes)
    print(mistakes)
    return render_template("messups.html",mistakes=mistakes)










if __name__=='__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True
    app.run(debug = True)
