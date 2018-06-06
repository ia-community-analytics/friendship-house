import firebase_admin
import pandas as pd
import io
from functools import wraps
from firebase_admin import db
from firebase_admin import auth
from flask import Flask, render_template, request, redirect, url_for, Response, flash, session
from flask_basicauth import BasicAuth

# TODO serve https and not http since we are using basic auth.

app = Flask(__name__)
# TODO: use an environment variable for this app secret!
app.secret_key = b'some46fu23yp/;:/sjdh'

today = pd.datetime.today()

app.config['BASIC_AUTH_USERNAME'] = 'someguy@domain.com'
app.config['BASIC_AUTH_PASSWORD'] = 'Inconnu1'

firebase_admin.initialize_app()
database = db.reference()
basic_auth = BasicAuth(app)

def intg(x):
    try:
        return int(x)
    except ValueError:
        return 0

def month(date):
    return '-'.join(date.split('-')[0:2]+['01'])

def format_tel(tel):
    if tel is None:
        return ''

    tel = str(tel)
    # length should be this and that
    if len(tel) == 10:
        return tel[0:3] + '-' + tel[3:6] + '-' + tel[6:]
    else:
        return tel

def create_user_id(last_name, first_name, dob):
    return last_name.lower() + '_' + first_name.lower() + '_' + dob

def initials(full_name):
    # TODO: strip non acii characters?
    if full_name == '':
        return ''
    return ''.join([el[0] for el in full_name.split(' ')])

# TOO: move this and the function to static?
dtype = {'Last Name':"string", 'First Name':"string", 'DOB':"string", 'SEX M/F':"string",
         'Race':"string", '#In Home':"string", 'Zip':"string", 'Phone':"string", 'Service Date':"string",
         'SRF Done (1=Yes, 0=No)':"string", 'Service Requested/Provided':"string", 'Staff (Initials)':"string",
         'Need Met (Y,N,P)':"string", 'UOS (.25, .5, .75, 1)':"number", 'Notes':"string"}


def generate_csv(json_data):
    # this may vary based on the way the data is represented.
    columns = ['Last Name', 'First Name', 'DOB', 'SEX M/F', 'Race', '#In Home', 'Zip', 'Phone', 'Service Date',
               'SRF Done (1=Yes, 0=No)', 'Service Requested/Provided', 'Staff (Initials)',
               'Need Met (Y,N,P)', 'UOS (.25, .5, .75, 1)', 'Notes']
    df = pd.DataFrame(columns=columns)

    for key in json_data.keys():
        for child_key in json_data.get(key).keys():
            temp = pd.DataFrame.from_dict(json_data.get(key).get(child_key), orient='index')
            temp = temp[['lastname','firstname', 'dob', 'gender', 'race', 'inhome', 'zipcode', 'phone', 'Date',
                        'staff_completing_csl', 'uos', 'staff_notes', 'need_met', 'other_service_txt']]
            temp['phone'] = [format_tel(tel) for tel in temp['phone'].values]
            other_indices = temp['uos'] == 'other'
            temp.loc[other_indices,'uos'] = temp.loc[other_indices,'other_service_txt'] # if other then there should be an entry
            uos_map = {'15':'.25', '30':'.5', '45':'.75', '1':1}
            temp['UOS (.25, .5, .75, 1)'] = [uos_map.get(el, el) for el in temp['uos'].values]

            # TODO use a gender to sex function . put race
            temp['SEX M/F'] = list(map(lambda x: x[0], temp['gender'].values))
            temp['Race'] = [el[0] for el in temp['race'].values]
            temp['Staff (Initials)'] = temp['staff_completing_csl'].apply(initials)
            temp['SRF Done (1=Yes, 0=No)'] = ''
            temp['Service Requested/Provided'] = ''

            temp.rename(index=str, columns={'lastname':'Last Name',
                                            'firstname':'First Name',
                                            'dob':'DOB',
                                            'inhome':'#In Home',
                                            'zipcode':'Zip',
                                            'phone':'Phone',
                                            'Date':'Service Date',
                                            'staff_notes':'Notes',
                                            'need_met':'Need Met (Y,N,P)'},
                        inplace=True)
            df = df.append(temp[columns].copy())

    return df.astype(str)


# TODO: have a decorator and an authenticate page where a token or id is provided.
# if not authenticated then do not do anything
def authentication_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('fire_token', None) is None:
            return redirect(url_for('authenticate', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# real routes
@app.route('/authenticate', methods=["GET", "POST"])
# @basic_auth.required
def authenticate():
    if request.method == 'POST' and session.get('fire_token', None) is None:
        form = request.form
        email = form.get('email', '')
        uid = form.get('uid','')
        try:
            user = auth.get_user_by_email(email)
        except:
            user = None
        if user is not None:
            user_uid = user.uid
            if uid == user_uid:
                session['fire_token'] = 'fire_verified'
                return redirect(url_for("homepage"))
            else:
                return render_template("authenticate.html")
        else:
            return render_template("authenticate.html")
    elif request.method == 'POST' and session.get('fire_token', None) is not None:
        session.pop('fire_token', None)
        return redirect('https://www.friendship.house/') # TODO make this a variable
    elif request.method == 'GET' and session.get('fire_token', None) is not None:
        return render_template("authenticate.html", email = 'somestuff@none.com', uid = 'friendship')
    else:
        return render_template("authenticate.html")


@app.route('/')
# @basic_auth.required
@authentication_required
def homepage():
    return redirect(url_for('home_page'))


@app.route('/admin', methods=["POST"])
# @basic_auth.required
@authentication_required
def service_log_admin():
    record = request.form.get('record')
    return redirect(url_for('service_log_add', record=record))


@app.route('/admin/<record>')
# @basic_auth.required
@authentication_required
def service_log_add(record):
    data = database.child('clients/'+record+'/information').get()
    return render_template('client_service_log.html', data=data, date=today.strftime("%Y-%m-%d"))


@app.route('/admin/<record>', methods=["POST"])
# @basic_auth.required
@authentication_required
def service_log_post(record):
    form = request.form
    log_month = month(form.get('Date'))
    database.child('service_logs/'+log_month+'/'+record).push(form) # set data
    # TODO add log path to client
    return redirect(url_for('select_client'))


# for export! use start_at and end_at since we now have months as keys in service log!
@app.route('/admin/export')
# @basic_auth.required
@authentication_required
def date_select():
    start = str(today.year) + '-01-01'
    end = str(today.year) + '-12-31'
    header = "Service Log Summary from %s to %s." % (start, end)
    data = database.child('service_logs').order_by_key().start_at(start).end_at(end).get()
    df = generate_csv(data)
    columns = list(df.columns)
    data_list = df.values.tolist()
    return render_template('export_client_logs.html', columns=columns, data_list = data_list,
                           ncol=len(columns), nrow=len(data_list), dtype=dtype, header=header,
                           date=today.strftime("%Y-%m-%d"))


@app.route('/admin/export', methods=["POST"])
# @basic_auth.required
@authentication_required
def export():
    form = request.form
    start = month(form.get('start'))
    end = month(form.get('end'))
    if start == '-01' or end == '-01':
        data = database.child('service_logs').order_by_key().get()
    else:
        data = database.child('service_logs').order_by_key().start_at(start).end_at(end).get()
    csv = generate_csv(data)
    buffer = io.StringIO()
    csv.to_csv(buffer, index=False)
    content = buffer.getvalue()
    buffer.close()

    return Response(content,mimetype="test/csv", headers={"Content-disposition":
                                                          "attachment; filename=export%sto%s.csv" % (start, end)})

@app.route('/dashboards')
@basic_auth.required
@authentication_required
def dashboards():
    return render_template('dashboards.html')


@app.route('/home', methods=["GET", "POST"])
@authentication_required
def home_page():
    if request.method == 'GET':
        return render_template("homepage.html")
    else:
        form = request.form
        if 'thesearchform' in form.keys():
            last_name = form.get('lname_search')
            first_name = form.get('fname_search')
            dob = form.get('dob_search')

            user_id = create_user_id(last_name, first_name, dob)
            exists = database.child('clients').order_by_key().start_at(user_id).end_at(user_id).get()

            # if the key already exists we have to warn user
            if len(exists) > 0:
                message="This User Already Exists! Do you wish to update or delete the record"
                info = database.child('clients/%s/information' % user_id).get()
                return render_template("update_and_delete.html", flash_message=message,data=info,
                                       allow_log='YES')
            else:
                message = "There is no record for such client. Please Add a new record"
                return render_template("update_and_delete.html", flash_message=message,
                                       data=dict(last_name=last_name, first_name=first_name, dob=dob),
                                       allow_log='NO')
        elif 'thecrudform' in form.keys():
            last_name = form.get('lastname')
            first_name = form.get('firstname')
            dob = form.get('dob')
            user_id = create_user_id(last_name, first_name, dob)
            gender = form.get('gender')
            phone = form.get('phone')
            nber_adults = form.get('adults')
            nber_under_18 = form.get('under18')
            race = form.get('race')
            address = form.get('street_address')
            city = form.get('city')
            state = form.get('state')
            zipcode = form.get('zipcode')
            total = intg(nber_adults) + intg(nber_under_18)

            # make data json. easy with name and dob separate
            # service_log should be a child with dates or something
            data = dict(last_name=last_name, first_name=first_name, dob=dob, gender=gender, phone=phone,
                        nber_adults=nber_adults, nber_under_18=nber_under_18, total_in_home=total,
                        race=race, address=address, city=city, state=state, zipcode=zipcode)

            if "create_record" in form.keys():
                # using set makes sure that we only have one value for information
                database.child('clients/' + user_id + '/information').set(data)
                return render_template("confirmation.html")
            elif "update_record" in form.keys():
                # using set makes sure that we only have one value for information
                database.child('clients/' + user_id + '/information').set(data)
                return render_template("confirmation.html")
            elif "delete_record" in form.keys():
                database.child('clients/' + user_id + '/information').delete()
                return render_template("confirmation.html")
            elif "add_client_log_for_record" in form.keys():
                return redirect(url_for('service_log_add', record=user_id))
            else:
                return redirect(url_for(home_page))
        else:
            return redirect(url_for(home_page))


if __name__ == '__main__':
    app.run(debug=True)
