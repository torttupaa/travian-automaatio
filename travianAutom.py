from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import time
import random
import copy
import threading
import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

from flask import render_template, session, request, redirect,url_for, flash
from forms import RegistrationForm, LoginForm, CommandForm

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///joku.db'
app.config['SECRET_KEY'] = 'ui546h4jhio46oi46ioj45'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(180), unique=False, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

db.create_all()

@app.route('/')
def index():
    return "HELLO"

#@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hash_password)
        db.session.add(user)
        db.session.commit()
        flash('Hoe ' +str(form.username.data) +' kullia imet')
        return redirect(url_for('index'))
    return render_template('register.html', title="REGUSER", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        user = User.query.filter_by(username = form.username.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            flash("yo logged biatch")
            session['username'] = form.username.data
            return redirect(url_for('admin'))
        else:
            flash("wrong!")
    return render_template('login.html', form=form, title="Login Page")


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global pause
    global command
    global RESUT
    global TUOTANNOT
    global REAL_TUOTANNOT
    global TAVOITTEET
    global NEXT_TO_BUILDS
    global LOCAL_PAUSES
    global AUTORAIDS
    global RESUFIELDIT
    global NUIJAPRODUCTIONS
    try:
        if 'Admin' not in session['username']:
            return redirect(url_for('login'))
    except:
        print("nobodys session")
        return redirect(url_for('login'))
    form = CommandForm(request.form)
    lock_pause.acquire()
    resu = RESUT
    tuotannot = TUOTANNOT
    real_tutannot = REAL_TUOTANNOT
    tavoitteet = TAVOITTEET
    ntb = NEXT_TO_BUILDS
    locpaus = LOCAL_PAUSES

    araid = AUTORAIDS
    rfields = RESUFIELDIT
    nprod = NUIJAPRODUCTIONS
    if pause:
        pau = "PAUSED"
    else:
        pau = "UNPAUSED"
    lock_pause.release()
    if request.method == "POST":
        lock_pause.acquire()
        command = form.command.data
        flash(str(command))
        lock_pause.release()
        return redirect(url_for("admin"))
    return render_template('joku.html', title='Admin Page',form=form, resu=resu,tuotannot=tuotannot,real_tutannot=real_tutannot,tavoitteet=tavoitteet,pau=pau,ntb=ntb, locpaus=locpaus,araid=araid,rfields=rfields,nprod=nprod )

@app.route('/paussi', methods=['POST'])
def paussi():
    global pause
    try:
        if 'Admin' not in session['username']:
            return redirect(url_for('login'))
    except:
        print("nobodys session")
        return redirect(url_for('login'))

    if request.method == 'POST':
        lock_pause.acquire()
        pause = True
        lock_pause.release()
        flash("paused")
        return redirect(url_for("admin"))
    return redirect(url_for("admin"))

@app.route('/unpause', methods=['POST'])
def unpause():
    global pause
    try:
        if 'Admin' not in session['username']:
            return redirect(url_for('login'))
    except:
        print("nobodys session")
        return redirect(url_for('login'))


    if request.method == 'POST':
        lock_pause.acquire()
        pause = False
        lock_pause.release()
        flash("unpaused")
        return redirect(url_for("admin"))
    return redirect(url_for("admin"))


def commandhandler():
    while True:
        global pause
        lock_pause.acquire()
        print(pause)
        lock_pause.release()
        time.sleep(1)

def kato_resurssit(resurssit,driver,wait):
    try:
        search = driver.find_element_by_id('l1')
        resurssit[0] = int(search.text.replace(" ", ""))
        search = driver.find_element_by_id('l2')
        resurssit[1] = int(search.text.replace(" ", ""))
        search = driver.find_element_by_id('l3')
        resurssit[2] = int(search.text.replace(" ", ""))
        search = driver.find_element_by_id('l4')
        resurssit[3] = int(search.text.replace(" ", ""))
        return resurssit
    except Exception as e:
        print(e)
        return [0,0,0,0]

def tuotanto_ja_sotilaat(Nuijasoturit, tuotanto, real_tuotanto, viime_tuotanto, driver, wait):
    try:
        search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navigation"]/a[1]')))
        time.sleep((random.randint(10,30)/10))
        search.click()
        search = driver.find_element_by_id('troops')
        asd = search.text.split("\n")
        for osa in asd:
            if osa[2:] == "Nuijasoturia":
                print(osa)
                Nuijasoturit = int(osa.split(" ")[0]);
        search = driver.find_element_by_id('production')
        prod = search.text.split("\n")
        del prod[0]
        for i in range(len(prod)):
            tuotanto[i] = int(prod[i].split("\u202d")[1].split("\u202c")[0])
        search = driver.find_element_by_id('stockBarFreeCrop')
        tuotanto[4] = int(search.text.split("\u202d")[1].split("\u202c")[0])
        #miten saadaan realtuotanto
        #print(viime_tuotanto,tuotanto)
        if viime_tuotanto != tuotanto:
            search = wait.until(EC.element_to_be_clickable((By.ID,'heroImageButton')))
            time.sleep((random.randint(10,30)/10))
            search.click()

            search = driver.find_element_by_class_name('resourcePick')
            ylituotto = search.text.split("\n")[:2]
            #print(ylituotto)

            search = driver.find_element_by_id('resourceHero0')
            try:
                if search.get_attribute("checked"):
                    for x in range(4):
                        real_tuotanto[x] = tuotanto[x]-int(ylituotto[0])
            except:
                pass
            search = driver.find_element_by_id('resourceHero1')
            try:
                if search.get_attribute("checked"):
                    real_tuotanto = copy.copy(tuotanto)
                    real_tuotanto[0] -= int(ylituotto[1])
            except:
                pass
            search = driver.find_element_by_id('resourceHero2')
            try:
                if search.get_attribute("checked"):
                    real_tuotanto = copy.copy(tuotanto)
                    real_tuotanto[1] -= int(ylituotto[1])
            except:
                pass
            search = driver.find_element_by_id('resourceHero3')
            try:
                if search.get_attribute("checked"):
                    real_tuotanto = copy.copy(tuotanto)
                    real_tuotanto[2] -= int(ylituotto[1])
            except:
                pass
            search = driver.find_element_by_id('resourceHero4')
            try:
                if search.get_attribute("checked"):
                    real_tuotanto = copy.copy(tuotanto)
                    real_tuotanto[3] -= int(ylituotto[1])
            except:
                pass

            search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navigation"]/a[1]')))
            time.sleep((random.randint(10,30)/10))
            search.click()
            real_tuotanto[4] = tuotanto[4]

        return Nuijasoturit, tuotanto, real_tuotanto
    except Exception as e:
        print(e)
        return Nuijasoturit, tuotanto, real_tuotanto

def mita_tuotantoo_rakennetaan(tuotanto,tavote,resurssit):
    if tuotanto[4] < 4:
        return 3;
    else:
        suurin_ind = 0
        suurin = -9999
        for i in range(len(tavote)):
            tuotanto_suhde = tuotanto[i]/tuotanto[0]
            tavote_suhde = tavote[i]/tavote[0]
            if(tavote_suhde - tuotanto_suhde>suurin):
                suurin = tavote_suhde-tuotanto_suhde
                suurin_ind = i
        return suurin_ind

def Tee_nuijamies(resurssit,nuija_valmis_time,driver,wait,ac): #testataan ku resuja
    if nuija_valmis_time < datetime.datetime.now():
        if (resurssit[0] >= 95) and (resurssit[1] >= 75) and(resurssit[2] >= 40) and(resurssit[3] >= 40):
            try:
                search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navigation"]/a[2]')))
                time.sleep((random.randint(10,30)/10))
                search.click()
                search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="village_map"]/div[32]')))
                time.sleep((random.randint(10,30)/10))
                search.click()

                search = driver.find_element_by_class_name('cta')
                avail_nuija = int(search.text.split(" ")[2].split("\n")[0])
                print(avail_nuija)

                search = driver.find_elements_by_class_name('desc')
                print(len(search))
                if len(search) > 0:
                    search = driver.find_element_by_class_name('fin')
                    d2 = datetime.date.today()
                    nuija_valmis_time = datetime.datetime.strptime(str(d2)+" "+str(search.text),"%Y-%m-%d %H:%M")
                    hours = 1
                    hours_added = datetime.timedelta(hours = hours)
                    nuija_valmis_time = nuija_valmis_time + hours_added
                    print(nuija_valmis_time)
                    print(datetime.datetime.now())
                    return nuija_valmis_time

                elif avail_nuija > 0:

                    search = driver.find_element_by_name('t1')
                    search.clear()
                    time.sleep((random.randint(10,30)/10))
                    search.send_keys(str(1))
                    time.sleep((random.randint(5,15)/10))
                    search.send_keys(Keys.ENTER)

                    #search = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='textButtonV1 green startTraining']")))
                    #search = driver.find_element_by_id('s1')
                    #time.sleep((random.randint(10,30)/10))
                    #ac.move_to_element(search).move_by_offset(0, 0).click().perform()
                    nuija_valmis_time = datetime.datetime.now()
                    return nuija_valmis_time
                nuija_valmis_time = datetime.datetime.now()
                return nuija_valmis_time
            except Exception as e:
                print(e)
                nuija_valmis_time = datetime.datetime.now()
                return nuija_valmis_time
    else:
        return nuija_valmis_time

def seuraava_paikka_rakentaa(cheapest_buildprice_for_reso, kaupunki_reso_slotit, buildnext_slotit, driver,wait):
    try:
        for i in range(len(buildnext_slotit)):
            if(1 not in buildnext_slotit[i]):
                lowest = 999999999
                needed_reso = []
                lowest_index = 0
                for j in range(len(kaupunki_reso_slotit[i])):
                    search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navigation"]/a[1]')))
                    time.sleep((random.randint(10,30)/10))
                    search.click()
                    search = wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'buildingSlot'+str(kaupunki_reso_slotit[i][j]))))
                    time.sleep((random.randint(10,30)/10))
                    search.click()
                    search = wait.until(EC.element_to_be_clickable((By.ID,'contract')))
                    resovaatimus = search.text.split("\n")[:4]
                    print(resovaatimus)

                    if(int(resovaatimus[0])<lowest):
                        needed_reso = [int(resovaatimus[0]),int(resovaatimus[1]),int(resovaatimus[2]),int(resovaatimus[3])]
                        lowest = needed_reso[0]
                        lowest_index = j
                buildnext_slotit[i][lowest_index] = 1
                cheapest_buildprice_for_reso[i] = needed_reso
        search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navigation"]/a[1]')))
        time.sleep((random.randint(7,20)/10))
        search.click()
        return cheapest_buildprice_for_reso,buildnext_slotit
    except Exception as e:
        print(e)
        return [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]

def rakenna_resuja(resurssit, kaupunki_reso_slotit, tuotanto_buid_valinta, cheapest_buildprice_for_reso ,buildnext_slotit , driver, wait):
    try:
        try:
            search = driver.find_element_by_class_name('buildingList')
            ddd = search.text.split("\n")
            print(ddd[0],ddd[2],ddd[3])
            return buildnext_slotit
        except:
            if(resurssit[0] >= cheapest_buildprice_for_reso[tuotanto_buid_valinta][0])and(resurssit[1] >= cheapest_buildprice_for_reso[tuotanto_buid_valinta][1])and(resurssit[2] >= cheapest_buildprice_for_reso[tuotanto_buid_valinta][2])and(resurssit[3] >= cheapest_buildprice_for_reso[tuotanto_buid_valinta][3]):
                search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navigation"]/a[1]')))
                time.sleep((random.randint(10,30)/10))
                search.click()
                for i in range(len(buildnext_slotit[tuotanto_buid_valinta])):
                    if buildnext_slotit[tuotanto_buid_valinta][i] == 1:
                        search = wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'buildingSlot'+str(kaupunki_reso_slotit[tuotanto_buid_valinta][i]))))
                        time.sleep((random.randint(10,30)/10))
                        search.click()

                        #search = wait.until(EC.element_to_be_clickable((By.CLASS_NAME,'contractWrapper')))
                        #print(search.text)


                        search = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='textButtonV1 green build']")))
                        time.sleep((random.randint(10,30)/10))
                        search.click()
                        buildnext_slotit[tuotanto_buid_valinta][i] = 0
            return buildnext_slotit
    except Exception as e:
        print(e)
        return [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]

def genraidilista(kyla_id):
    raidilista = []
    temp = []
    with open("raidilista"+str(kyla_id)+".txt","r") as f:
        for line in f:
            temp = line.split(",")
            raidilista.append([int(temp[0]),int(temp[1]),int(temp[2])])
    return raidilista

def Raidi(raidilista,Nuijasoturit,driver,wait,ac):
    for i in range(len(raidilista)):
        if len(raidilista[i]) == 3:
            #append with datetime
            raidilista[i].append(datetime.datetime.now())

            #check viime raidi tilastot
            search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navigation"]/a[3]')))
            time.sleep((random.randint(10,30)/10))
            search.click()
            search = wait.until(EC.element_to_be_clickable((By.ID,'xCoordInputMap')))
            search.clear()
            time.sleep((random.randint(5,13)/10))
            search.send_keys(raidilista[i][0])
            search = wait.until(EC.element_to_be_clickable((By.ID,'yCoordInputMap')))
            search.clear()
            time.sleep((random.randint(5,13)/10))
            search.send_keys(raidilista[i][1])
            search = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='textButtonV1 green small']")))
            time.sleep((random.randint(5,13)/10))
            search.click()
            search = wait.until(EC.element_to_be_clickable((By.ID,'mapContainer')))
            time.sleep((random.randint(5,13)/10))
            search.click()
            time.sleep((random.randint(5,13)/10))
            ac.send_keys(Keys.ESCAPE).perform()
        elif len(raidilista[i]) == 4:
            mins_added = datetime.timedelta(minutes = 1)
            nextraid = raidilista[i][3] + mins_added
            if datetime.datetime.now() > nextraid:
                print("uus raidi")
                raidilista[i][3] = datetime.datetime.now()
                search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navigation"]/a[3]')))
                time.sleep((random.randint(10,30)/10))
                search.click()
                search = wait.until(EC.element_to_be_clickable((By.ID,'xCoordInputMap')))
                search.clear()
                time.sleep((random.randint(5,13)/10))
                search.send_keys(raidilista[i][0])
                search = wait.until(EC.element_to_be_clickable((By.ID,'yCoordInputMap')))
                search.clear()
                time.sleep((random.randint(5,13)/10))
                search.send_keys(raidilista[i][1])
                search = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='textButtonV1 green small']")))
                time.sleep((random.randint(5,13)/10))
                search.click()
                search = wait.until(EC.element_to_be_clickable((By.ID,'mapContainer')))
                time.sleep((random.randint(5,13)/10))
                search.click()
                time.sleep((random.randint(5,13)/10))
                ac.send_keys(Keys.ESCAPE).perform()
            #print("asd")
    return raidilista

def autokyla(kyla_id,pathi):
    nuija_valmis_time = datetime.datetime.now()
    tuotanto_buid_valinta = 0
    resurssit = [0,0,0,0]
    tuotanto = [0,0,0,0,0]
    real_tuotanto = [0,0,0,0,0]
    viime_tuotanto = [0,0,0,0,0]
    Nuijasoturit = 0

    nuijia_kerralla = 1

    ######### SETUPIT ##############
    kylan_xpath = pathi
    Autoraid = True
    Tee_sotajoukkoja = False
    Tee_tuotantoa = True
    local_pause = False

    tavoite_tuotanto_suhteet = [0.9,1.0,0.8,0.3]
    kaupunki_reso_slotit = [[1,3,14,17],[5,6,16,18],[4,7,10,11],[2,8,9,12,13,15]]

    #ei pakolliset setupit
    buildnext_slotit = [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0, 1, 0]]
    cheapest_buildprice_for_reso = [[310, 780, 390, 465], [1040, 520, 1040, 650], [780, 620, 235, 465], [325, 420, 325, 95]]

    raidilista = genraidilista(kyla_id)
    print(raidilista)
    ###############################

    #init selenium stuff
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 5)
    ac = ActionChains(driver)

    #sisaankirjautuminen
    driver.get("https://ts5.nordics.travian.com/dorf1.php")
    search = driver.find_element_by_name('name')
    search.send_keys("Hypistelija")
    search = driver.find_element_by_name('password')
    search.send_keys("kudjoi123")
    search = wait.until(EC.element_to_be_clickable((By.NAME,'s1')))
    search.click()

    #helevetin accept coocies
    try:
        search = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')))
        search.click()
    except Exception as e:
        print(e)
    search = wait.until(EC.element_to_be_clickable((By.XPATH,kylan_xpath)))
    search.click()

    first_run = True
    while True:
        #joukot ja tuotanto
        #if (random.randint(0,10) >= 0) or (first_run): #muuttaa todennakosyytta checkata hommat

        viime_tuotanto = copy.copy(tuotanto)
        Nuijasoturit,tuotanto,real_tuotanto = tuotanto_ja_sotilaat(Nuijasoturit, tuotanto, real_tuotanto, viime_tuotanto, driver, wait)
        #print(real_tuotanto,tuotanto)
        #resucheck
        resurssit = kato_resurssit(resurssit,driver,wait)

        #tuotannon lisaaminen :::: pitaa sit resetoida kaynnistaessa
        if Tee_tuotantoa:
            tuotanto_buid_valinta = mita_tuotantoo_rakennetaan(real_tuotanto,tavoite_tuotanto_suhteet,resurssit)
            cheapest_buildprice_for_reso, buildnext_slotit = seuraava_paikka_rakentaa(cheapest_buildprice_for_reso,kaupunki_reso_slotit,buildnext_slotit,driver,wait)
            buildnext_slotit = rakenna_resuja(resurssit, kaupunki_reso_slotit, tuotanto_buid_valinta, cheapest_buildprice_for_reso ,buildnext_slotit , driver, wait)

        if Tee_sotajoukkoja:
            nuija_valmis_time = Tee_nuijamies(resurssit,nuija_valmis_time,driver,wait,ac)

        if Autoraid:
            raidilista=Raidi(raidilista,Nuijasoturit,driver,wait,ac)
            print(raidilista)

        time.sleep((random.randint(50,120)/10))
        first_run = False

        try:
            print("valinta mita rakennetaan", tuotanto_buid_valinta)
            print("halvimman resurssikentan hinnat",cheapest_buildprice_for_reso)
            print("seuraava kentta jota rakennetaan",buildnext_slotit)
            print("resurssit",resurssit)
            print("tuotanto",tuotanto)
            print("real tuotanto",real_tuotanto)
        except Exception as e:
            print(e)
            first_run = True
            buildnext_slotit = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]
            cheapest_buildprice_for_reso = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

        global RESUT
        global TUOTANNOT
        global REAL_TUOTANNOT
        global TAVOITTEET
        global NEXT_TO_BUILDS
        global LOCAL_PAUSES
        global AUTORAIDS
        global RESUFIELDIT
        global NUIJAPRODUCTIONS

        lock_pause.acquire()
        RESUT[kyla_id] = resurssit
        TUOTANNOT[kyla_id] = tuotanto
        REAL_TUOTANNOT[kyla_id] = real_tuotanto
        TAVOITTEET[kyla_id] = tavoite_tuotanto_suhteet
        NEXT_TO_BUILDS[kyla_id] = tuotanto_buid_valinta
        LOCAL_PAUSES[kyla_id] = local_pause
        AUTORAIDS[kyla_id] = Autoraid
        RESUFIELDIT[kyla_id] = Tee_tuotantoa
        NUIJAPRODUCTIONS[kyla_id] = Tee_sotajoukkoja

        lock_pause.release()


        global pause
        global command


        while pause or local_pause:
            lock_pause.acquire()
            if command[:1] == str(kyla_id):
                if command[1:4] == "unp":
                    local_pause = False
            LOCAL_PAUSES[kyla_id] = local_pause
            lock_pause.release()
            time.sleep(1)

        #commandien kasittely
        lock_pause.acquire()
        if command[:1] == str(kyla_id):
            if command[1:3] == "TT":
                try:
                    TTaihio = command[3:].split(",")
                    tavoite_tuotanto_suhteet[0] = float(TTaihio[0])
                    tavoite_tuotanto_suhteet[1] = float(TTaihio[1])
                    tavoite_tuotanto_suhteet[2] = float(TTaihio[2])
                    tavoite_tuotanto_suhteet[3] = float(TTaihio[3])
                    command = ""
                except:
                    command = ""
            elif command[1:4] == "pau":
                local_pause = True
                command = ""
            elif command[1:4] == "RST":
                tuotanto = [0,0,0,0,0]
                buildnext_slotit = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]
                cheapest_buildprice_for_reso = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
                command = ""
            elif command[1:4] == "NMT":
                try:
                    if command[4:] == "0":
                        Tee_sotajoukkoja = False
                    elif command[4:] == "1":
                        Tee_sotajoukkoja = True
                    command = ""
                except:
                    command = ""
            elif command[1:4] == "ARA":
                try:
                    if command[4:] == "0":
                        Autoraid = False
                        print("autoraid off")
                    elif command[4:] == "1":
                        Autoraid = True
                        print("autoraid on")
                    command = ""
                except:
                    command = ""
            elif command[1:4] == "RFP":
                try:
                    if command[4:] == "0":
                        Tee_tuotantoa = False
                        print("autoraid off")
                    elif command[4:] == "1":
                        Tee_tuotantoa = True
                        print("autoraid on")
                    command = ""
                except:
                    command = ""
        lock_pause.release()

if __name__ == "__main__":
    global pause
    global command
    global RESUT
    global TUOTANNOT
    global REAL_TUOTANNOT
    global TAVOITTEET
    global NEXT_TO_BUILDS
    global LOCAL_PAUSES
    global AUTORAIDS
    global RESUFIELDIT
    global NUIJAPRODUCTIONS

    lock_pause = threading.Lock()
    #NÄÄ PITÄÄ SÄÄTÄÄ SIT KYLIEN MÄÄRÄN MUKAA
    lock_pause.acquire()
    pause = False
    command  = ""
    RESUT = [[0,0,0,0]]
    TUOTANNOT = [[0,0,0,0,0]]
    REAL_TUOTANNOT = [[0,0,0,0,0]]
    TAVOITTEET = [[0,0,0,0]]
    NEXT_TO_BUILDS = [0]
    LOCAL_PAUSES = [0]
    AUTORAIDS = [0]
    RESUFIELDIT = [0]
    NUIJAPRODUCTIONS = [0]
    lock_pause.release()

    t1 = threading.Thread(target=autokyla, args=[0,'//*[@id="sidebarBoxVillagelist"]/div[2]/ul/li/a/span[1]/span'])
    t1.start()
    app.run(host='localhost', port=6969)
