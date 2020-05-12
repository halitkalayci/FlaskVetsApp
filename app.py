from flask import Flask,render_template,flash,redirect,url_for,session,logging,request,Markup,jsonify
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,FloatField
from passlib.handlers.sha2_crypt import sha256_crypt
from math import cos, asin, sqrt, radians,atan2,sin
import json
from geopy.distance import geodesic
from decimal import Decimal



import email_validator

# Kullanıcı kayıt formu modülü
class RegisterForm(Form):
    name = StringField("İsminiz",validators=[validators.DataRequired('İsim alanı boş olamaz.')])
    surname = StringField("Soyisminiz",validators=[validators.DataRequired('Soyisim alanı boş olamaz.')])
    email = StringField("E-posta Adresiniz",validators=[validators.DataRequired('Eposta alanı boş olamaz.'),validators.Email("Geçersiz bir eposta girdiniz.")])
    password = PasswordField("Şifreniz",validators=[validators.DataRequired('Şifre alanı boş olamaz.'), validators.EqualTo(fieldname="confirmpassword",message="Parolalar uyuşmuyor.")])
    confirmpassword = PasswordField("Şifrenizi onaylayın",validators=[validators.DataRequired('Şifre alanı boş olamaz.'), validators.EqualTo(fieldname="password",message="Parolalar uyuşmuyor.")])

#Kullanıcı giriş formu modülü
class LoginForm(Form):
    email = StringField("E-posta adresiniz",validators=[validators.DataRequired("E-posta boş olamaz."),validators.Email("E-posta adresi düzgün girilmedi.")])    
    password = PasswordField("Şifreniz" , validators=[validators.DataRequired("Şifre boş olamaz.")])

#Veteriner ekle/düzenle formu modülü
class VetForm(Form):
    fullName = StringField("Veteriner adını giriniz..", validators=[validators.DataRequired("Veteriner adı boş olamaz.")])
    adress = TextAreaField("Adres giriniz.." ,validators=[validators.DataRequired("Adres boş olamaz.")])
    lattitude = FloatField("Enlem giriniz..")
    longitude = FloatField("Boylam giriniz..")
    city = StringField("Şehir giriniz..",validators=[validators.DataRequired("Şehir adı boş olamaz.")])
    phone = StringField("Telefon numarası giriniz",validators=[validators.DataRequired("Telefon boş olamaz.")])

app = Flask(__name__)
app.secret_key="SAKARYA_UNIVERSITY_YBS"
app.config["MYSQL_HOST"] = "sql7.freemysqlhosting.net"
app.config["MYSQL_USER"] = "sql7339728"
app.config["MYSQL_PASSWORD"] = "xJBrz194Rx"
app.config['MYSQL_PORT'] = 3306
app.config["MYSQL_DB"] = "sql7339728"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

#Ana sayfa modülü
@app.route("/index")
@app.route('/')
def index():
    return render_template("index.html")

#Kayıt olma sayfası modülü
@app.route('/register',methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        password = sha256_crypt.hash( form.password.data )
        cursor = mysql.connection.cursor()
        emailSorgu = "Select * from Users Where Email=%s"
        result = cursor.execute(emailSorgu,(email,))
        if result>0:
            flash("Bu e-posta adresi daha önce kullanılmış.","danger")
            return redirect(url_for("register"))
        sorgu = "INSERT INTO users (Name,Surname,Email,Password,IsAdmin) values(%s,%s,%s,%s,0)"
        cursor.execute(sorgu,(name,surname,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("Kaydınız başarıyla gerçekleşti.","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)


#Giriş sayfası modülü
@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        email = form.email.data
        password = form.password.data
        
        cursor = mysql.connection.cursor()
        sql = "Select * from Users WHERE Email=%s"
        result = cursor.execute(sql,(email,))
        if result>0:
            data = cursor.fetchone()
            real_pw = data["Password"]
            if sha256_crypt.verify(password,real_pw):
                flash("Giriş başarılı.","success")
                session["IsAdmin"] = data["IsAdmin"]
                session["LoggedIn"] = True
                session["Name"] = data["Name"]
                session["Surname"] = data["Surname"]
                return redirect(url_for('index'))
            else:
                flash("Şifreniz yanlış. Sıfırlamak için aşağıdaki şifremi unuttum linkini kullanabilirsiniz.","danger")
                return redirect(url_for('login'))
        else:
            flash("Bu e-posta adresine kayıtlı bir kullanıcı bulunamadı.","danger")
            return redirect(url_for('login'))

    else:
        return render_template("login.html",form=form)


#Çıkış yapma modülü
@app.route('/logout',methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("login"))

#Yönetim paneli sayfası modülü
@app.route('/yonetim')
def yonetim():
    cursor = mysql.connection.cursor()
    sql = "Select * from Vets"
    result = cursor.execute(sql)
    if result>0:
        data=cursor.fetchall()
        return render_template("yonetim.html",vets=data)
    return render_template("yonetim.html")


#Veteriner bilgi düzenleme modülü
@app.route('/editvet/<int:id>',methods=["GET","POST"])
def editvet(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sql = f"Select * from Vets Where Id={id}"
        result = cursor.execute(sql)
        if result>0:
            data=cursor.fetchone()
            form = VetForm()
            form.fullName.data = data["FullName"]
            form.city.data = data["City"]
            form.adress.data = data["Adress"]
            form.lattitude.data = data["Latitude"]
            form.longitude.data = data["Longitude"]
            form.phone.data = data["Phone"]
            return render_template('editvet.html',form=form)
        else:
            return redirect(url_for('yonetim'))
    else:
        form = VetForm(request.form)
        if form.validate():
            newName = form.fullName.data
            newCity = form.city.data
            newAdress = form.adress.data
            newLatitude = form.lattitude.data
            newLongitude = form.longitude.data
            newPhone = form.phone.data
            sorgu = f"Update Vets Set FullName='{newName}',City='{newCity}',Adress='{newAdress}',Latitude={newLatitude},Longitude={newLongitude},Phone='{newPhone}' Where Id={id}"
            cursor = mysql.connection.cursor()
            cursor.execute(sorgu)
            mysql.connection.commit()
            flash(f"{newName} başarıyla güncellendi","success")
            return redirect(url_for("yonetim"))
        else:
            flash(f"Güncelleme sırasında hata oluştu.","danger")
            return redirect(url_for("yonetim"))

       
#Veteriner silme modülü
@app.route('/deletevet/<int:id>')
def deletevet(id):
    cursor = mysql.connection.cursor()
    sorgu = f"Delete from Vets Where Id={id}"
    cursor.execute(sorgu)
    mysql.connection.commit()
    flash(f"{id} numaralı veteriner silindi","success")
    return redirect(url_for("yonetim"))

#Veteriner ekleme modülü
@app.route('/addvet',methods=["GET","POST"])
def addvet():
    if request.method=="GET":
        form = VetForm()
        return render_template("addvet.html",form=form)
    else:
        form = VetForm(request.form)
        if form.validate():
            newName = form.fullName.data
            newCity = form.city.data
            newAdress = form.adress.data
            newLatitude = form.lattitude.data
            newLongitude = form.longitude.data
            newPhone = form.phone.data
            sorgu = "Insert Into Vets (FullName,City,Adress,Latitude,Longitude,Phone) Values(%s,%s,%s,%s,%s,%s)"
            cursor = mysql.connection.cursor()
            cursor.execute(sorgu,(newName,newCity,newAdress,newLatitude,newLongitude,newPhone))
            mysql.connection.commit()
            flash(f"{newName} başarıyla eklendi","success")
            return redirect(url_for("yonetim"))
        else:
            flash(f"Ekleme sırasında hata oluştu.","danger")
            return redirect(url_for("addvet"))

#Acil yardım modülü
@app.route("/urgentcall")
def urgentcall():
     sorgu = "Select Latitude as lat,Longitude as lon from Vets"
     cursor = mysql.connection.cursor()
     cursor.execute(sorgu)
     data =[]
     for res in cursor:
        data.append({"lat":float(res["lat"]),"lon":float(res["lon"])})
     userCoordinates = {"lat":float(request.args.get('lat')),"lon":float(request.args.get('lon'))}
     closestOne = closest(data,userCoordinates)
     origin = (float(request.args.get('lat')),float(request.args.get('lon')))
     distanceLocation = ( closestOne["lat"] , closestOne["lon"] )
     distance = float("{:.2f}".format(calculateDistance(origin,distanceLocation)))
     vetSorgu = 'Select * from Vets Where Longitude=%s and Latitude=%s'
     cursor = mysql.connection.cursor()
     result = cursor.execute(vetSorgu,(closestOne["lon"],closestOne["lat"]))
     if result>0:
         data = cursor.fetchone()
         message = Markup(f"Size en yakın veteriner bulundu ve çağrınız iletildi. <br> Veteriner Bilgileri <br> Veteriner Adı : {data['FullName']}<br> Tam Adresi : {data['Adress']} <br>Aranızdaki Mesafe (ortalama): {distance} KM.")
         flash(message,"success")
         return redirect(url_for("index"))


# Veterinerler (kullanıcı görünümü) modeli
@app.route("/vets")
def vets():
    cursor = mysql.connection.cursor()
    sql = "Select * from Vets"
    result = cursor.execute(sql)
    if result>0:
        data=cursor.fetchall()
        return render_template("vets.html",vets=data)
    return render_template("index.html")


def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)

def distance(lat1, lon1, lat2, lon2):
    lat1 = float(lat1)
    lat2= float(lat2)
    lon1 = float(lon1)
    lon2 = float(lon2)
    p = 0.017453292519943295
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
    return 12742 * asin(sqrt(a))

def closest(data, v):
    return min(data, key=lambda p: distance(float(v['lat']),float(v['lon']),float(p['lat']),float(p['lon'])))

def calculateDistance(origin,dist):
    return geodesic(origin, dist).kilometers


      
if __name__ == "__main__":
    app.run(debug=True)