import firebase_admin
import pandas as pd
import io
import json
from firebase_admin import credentials
from firebase_admin import db
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response

app = Flask(__name__)
today = pd.datetime.today()

cred = credentials.Certificate(r'C:\Users\hounyja\Documents\friendshiphouse\credentials\friendshiphouse-82cbf-firebase-adminsdk-8uqt4-e39d70a976.json')
firebase_admin.initialize_app(cred, options={'databaseURL':'https://friendshiphouse-82cbf.firebaseio.com/'})

database = db.reference()


def intg(x):
    try:
        return int(x)
    except ValueError:
        return 0

def month(date):
    return '-'.join(date.split('-')[0:2]+['01'])

def initials(full_name):
    # TODO: strip non acii characters?
    if full_name == '':
        return ''
    return ''.join([el[0] for el in full_name.split(' ')])


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

    return df

@app.route('/')
def homepage():
    return render_template('client_information.html', date=today.strftime("%Y-%m-%d"))

@app.route('/', methods=["POST"])
def dataPost():
    form = request.form
    last_name = form.get('lastname')
    first_name = form.get('firstname')
    dob = form.get('dob')
    user_id = last_name + '_' + first_name + '_' + dob
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

    # using set makes sure that we only have one value for information
    database.child('clients/'+ user_id+'/information').set(data)
    # TODO: return simple html
    return render_template('confirmation.html')

# TODO: create route for admin to get data. This will require login credentials
@app.route('/login')
def login():
    # figure this out. The rules and the simulator clearly works
    pass

@app.route('/admin')
def select_client():
    # make use of real time editing
    # TODO: Create a table instead - easily have last name, first name, dob and click on button to go to page
    records = database.child('clients').get(shallow=True)

    if records is None:
        records = []
    else:
        records = list(records)

    return render_template('add_service_log.html', options=records)

@app.route('/admin', methods=["POST"])
def service_log_admin():
    record = request.form.get('record')
    return redirect(url_for('service_log_add', record=record))

@app.route('/admin/<record>')
def service_log_add(record):
    data = database.child('clients/'+record+'/information').get()
    return render_template('client_service_log.html', data=data, date=today.strftime("%Y-%m-%d"))

@app.route('/admin/<record>', methods=["POST"])
def service_log_post(record):
    form = request.form
    log_month = month(form.get('Date'))
    database.child('service_logs/'+log_month+'/'+record).push(form) # set data
    return redirect(url_for('select_client'))

# for export! use start_at and end_at since we now have months as keys in service log!
@app.route('/admin/export')
def date_select():
    return render_template('export_client_logs.html')

@app.route('/admin/export', methods=["POST"])
def export():
    form = request.form
    start = month(form.get('start'))
    end = month(form.get('end'))
    data = database.child('service_logs').order_by_key().start_at(start).end_at(end).get()
    csv = generate_csv(data)
    buffer = io.StringIO()
    csv.to_csv(buffer, index=False)
    content = buffer.getvalue()
    buffer.close()

    return Response(content,mimetype="test/csv", headers={"Content-disposition":
                                                          "attachment; filename=export%sto%s.csv" % (start, end)})

if __name__ == '__main__':
    app.run(debug=True)
