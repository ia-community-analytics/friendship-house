import firebase_admin
import io
import json
from non_app_specific import (today, intg, races, genders, get_all_client_keys, generate_csv,
                              capitalize, month, create_user_id, appointment_description, appointment_type,
                              service_uos, program_status, supportive_service_provided, generate_random_url,
                              display_name, process_name, old_data_for_dashboard, data_for_dashboard)
from functools import wraps
from firebase_admin import db
from firebase_admin import auth
from flask import Flask, render_template, jsonify, request, redirect, url_for, Response, flash, session, abort
from flask_basicauth import BasicAuth

# TODO serve https and not http since we are using basic auth.

app = Flask(__name__)

# TODO: use an environment variable for this app secret!
app.secret_key = b'some46fu23yp/;:/sjdh'

app.config['BASIC_AUTH_USERNAME'] = 'someguy@domain.com'
app.config['BASIC_AUTH_PASSWORD'] = 'Inconnu1'

firebase_admin.initialize_app()
database = db.reference()
basic_auth = BasicAuth(app)


# TODO: have a decorator and an authenticate page where a token or id is provided.
def reset_data_post_url():
    session.pop('data_posting_url')
    session['data_posting_url'] = generate_random_url(20)
    return None


# if not authenticated then do not do anything
def authentication_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('fire_token', None) is None:
            return redirect(url_for('authenticate', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def hide(f):
    @wraps(f)
    def a_function(*args, **kwargs):
        resp = f(*args, **kwargs)
        reset_data_post_url()
        return resp

    return a_function

def error_handler(f):
    @wraps(f)
    def return_function(*args, **kwargs):
        # this is the idea. if the function fails, provide a better view
        # TODO: depending on the type of error, maybe one view is better
        # TODO: create a logger that actuall trakcs the name of f,  the function that failed
        try:
            resp = f(*args, **kwargs)
            return resp
        except Exception as e:
            return jsonify(e)
            # return "Sorry - Please Come Back in A second"

    return return_function


# real routes
@app.route('/authenticate', methods=["GET", "POST"])
# @basic_auth.required
# TODO: in multi select, https://stackoverflow.com/questions/12502646/access-multiselect-form-field-in-flask
@error_handler
def authenticate():
    if request.method == 'POST' and session.get('fire_token', None) is None:
        form = request.form
        email = form.get('email', '')
        uid = form.get('uid', '')
        try:
            user = auth.get_user_by_email(email)
        except:
            user = None
        if user is not None:
            user_uid = user.uid
            if uid == user_uid:
                session['fire_token'] = 'fire_verified'
                session['data_posting_url'] = generate_random_url(20)
                return redirect(url_for("home_page"))
            else:
                return render_template("authenticate.html", logged_in=0)
        else:
            return render_template("authenticate.html", logged_in=0)
    elif request.method == 'POST' and session.get('fire_token', None) is not None:
        session.pop('fire_token', None)
        if 'data_posting_url' in session:
            session.pop('data_posting_url')
        return redirect('https://www.friendship.house/')  # TODO make this a variable
    elif request.method == 'GET' and session.get('fire_token', None) is not None:
        return render_template("authenticate.html", email='somestuff@none.com', uid='friendship', logged_in=1)
    else:
        return render_template("authenticate.html", logged_in=0)


@app.route('/')
# @basic_auth.required
@authentication_required
@error_handler
def homepage():
    return redirect(url_for('home_page'))


@app.route('/admin', methods=["POST"])
# @basic_auth.required
@authentication_required
@error_handler
def service_log_admin():
    record = request.form.get('record')
    return redirect(url_for('service_log_add', record=record))


@app.route('/admin/<record>')
# @basic_auth.required
@authentication_required
@error_handler
def service_log_add(record):
    data = database.child('clients/' + record + '/information').get()
    return render_template('client_service_log.html', data=data, date=today.strftime("%Y-%m-%d"),
                           appointment_type=appointment_type, program_status=program_status,
                           appointment_description=appointment_description, service_uos=service_uos,
                           supportive_service_provided=supportive_service_provided)


@app.route('/admin/<record>', methods=["POST"])
# @basic_auth.required
@authentication_required
@error_handler
def service_log_post(record):
    form = request.form
    service_date = form.get('Date')
    log_month = month(service_date)

    push = database.child('service_logs').child(log_month).child(record).push(form)  # set data

    # we need to add to paths
    paths = database.child('clients/%s/paths' % record).get()  # the array or None
    if paths is None:
        database.child('clients/%s/paths' % record).set(['service_logs/' + log_month + '/' + record + '/' + push.key])
    else:
        ner_paths = len(paths)
        database.child('clients/%s/paths/%s' % (record, str(ner_paths))).set(
            'service_logs/' + log_month + '/' + record + '/' + push.key)

    # we need to add service dates
    service_dates = database.child('clients/%s/service_dates' % record).get()
    if service_dates is None:
        database.child('clients/%s/service_dates' % record).set([service_date])
    else:
        nber_srvc_dts = len(service_dates)
        database.child('clients/%s/service_dates/%s' % (record, str(nber_srvc_dts))).set(service_date)

    # TODO add log path to client
    # TODO add service date
    return redirect(url_for('home_page'))


# for export! use start_at and end_at since we now have months as keys in service log!
@app.route('/admin/export')
# @basic_auth.required
@authentication_required
@error_handler
def date_select():
    start = str(today.year) + '-01-01'
    end = str(today.year) + '-12-31'
    header = "Service Log Summary from %s to %s." % (start, end)
    data_post_url = session.get('data_posting_url', '')
    return render_template('export_client_logs.html', id_check=data_post_url, header=header,
                           date=today.strftime("%Y-%m-%d"))


@app.route('/admin/export', methods=["POST"])
# @basic_auth.required
@authentication_required
@error_handler
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

    return Response(content, mimetype="test/csv", headers={"Content-disposition":
                                                               "attachment; filename=export%sto%s.csv" % (start, end)})


@app.route('/dashboards')
# @basic_auth.required
@authentication_required
@error_handler
def dashboards():
    data_post_url = session.get('data_posting_url', '')
    return render_template('dashboards.html', id_check=data_post_url)


@app.route('/home', methods=["GET", "POST"])
@authentication_required
@error_handler
def home_page():
    if request.method == 'GET':
        return render_template("homepage.html")
    else:
        form = request.form
        form = dict((a, b.strip() if isinstance(b, str) else b) for a, b in form.items())  # strip spaces
        if 'thesearchform' in form.keys():
            last_name = process_name(form.get('lname_search', '')).lower()
            first_name = process_name(form.get('fname_search', '')).lower()
            dob = form.get('dob_search', '').lower()

            if last_name == '' and first_name == '' and dob == '':
                return render_template("homepage.html", redirected='At least one of these fields should be populated!')

            # the can search first names, last names or date of births
            if last_name.strip() == '' or first_name.strip() == '' or dob == '':
                all_keys = get_all_client_keys(database)
                all_keys = [el.split('_') for el in all_keys]  # these are keys as they appear on the db

                if last_name != '':
                    all_keys = [el for el in all_keys if last_name in el]
                if first_name != '':
                    all_keys = [el for el in all_keys if first_name in el]
                if dob != '':
                    all_keys = [el for el in all_keys if dob in el]

                if len(all_keys) == 0:
                    exists = []  # this will directly send you to the add page
                elif len(all_keys) == 1:
                    element = all_keys[0]
                    user_id = create_user_id(last_name=element[0], first_name=element[1], dob=element[2])
                    exists = 'Yes'
                else:
                    all_clients = [[capitalize(el[0]), capitalize(el[1]), el[2]]
                                   for el in all_keys]
                    values = [create_user_id(last_name=el[0], first_name=el[1], dob=el[2]) for el in all_keys]

                    return render_template("homepage.html", multiple_clients=all_clients, values=values,
                                           redirected=None)
            else:
                user_id = create_user_id(last_name, first_name, dob)
                exists = database.child('clients').order_by_key().start_at(user_id).end_at(user_id).get()

            # if the key already exists we have to warn user
            if len(exists) > 0:
                message = "We found a matching record! Do you wish to update or delete the record?"
                info = database.child('clients/%s/information' % user_id).get()
                race = info.get('race')  # selected race
                gender = info.get('gender')  # selected gender
                return render_template("update_and_delete.html", flash_message=message, data=info,
                                       allow_log='YES',
                                       races_nd_selected=[dict(race=a, selected='YES' if race == a else 'NO') for a in
                                                          races],
                                       genders_nd_selected=[dict(gender=a, selected='YES' if gender == a else 'NO') for
                                                            a in genders])
            else:
                message = "There is no record for such client. Please Add a new record"
                return render_template("update_and_delete.html", flash_message=message,
                                       data=dict(last_name=last_name, first_name=first_name, dob=dob),
                                       allow_log='NO',
                                       races_nd_selected=[dict(race=a, selected='NO') for a in races],
                                       genders_nd_selected=[dict(gender=a, selected='NO') for a in genders])

        elif 'client_select_one' in form.keys():
            # if a client is selected
            user_id = form.get('client_select_one').lower()
            info = database.child('clients/%s/information' % user_id).get()
            # because these are multiple choice
            race = info.get('race')  # selected race
            gender = info.get('gender')  # selected gender
            return render_template("update_and_delete.html", data=info, allow_log='YES',
                                   races_nd_selected=[dict(race=a, selected='YES' if race == a else 'NO') for a in
                                                      races],
                                   genders_nd_selected=[dict(gender=a, selected='YES' if gender == a else 'NO') for a in
                                                        genders])

        elif 'thecrudform' in form.keys():
            # note that if delete was seleected we would not need to get this info
            last_name = form.get('lastname', '')
            first_name = form.get('firstname', '')
            dob = form.get('dob', '')
            user_id = create_user_id(last_name, first_name, dob)
            gender = form.get('gender', '')
            phone = form.get('phone', '')
            nber_adults = form.get('adults', '')
            nber_under_18 = form.get('under18', '')
            race = form.get('race', '')
            address = form.get('street_address', '')
            city = form.get('city', '')
            state = form.get('state', '')
            zipcode = form.get('zipcode', '')
            total = intg(nber_adults) + intg(nber_under_18)

            # make data json. easy with name and dob separate
            # service_log should be a child with dates or something
            data = dict(last_name=capitalize(last_name, sep=' '), first_name=capitalize(first_name, sep=' '), dob=dob,
                        gender=gender,
                        phone=phone,
                        nber_adults=nber_adults, nber_under_18=nber_under_18, total_in_home=total,
                        race=race, address=address, city=city, state=state, zipcode=zipcode,
                        last_updt_dt=today.strftime('%Y-%m-%d'))

            # TODO - update confirmation to take type of action i.e. deleted, pushed added
            if "create_record" in form.keys():
                # using set makes sure that we only have one value for information
                # if they need to add a client that was once deleted, we can bring their paths back
                # but reset information. Even created date
                data['created_dt'] = today.strftime('%Y-%m-%d')  # day it was created
                database.child('clients/' + user_id + '/information').set(data)

                # check if user_id exists in archives
                in_archive = database.child('archived_clients').order_by_key().start_at(user_id).end_at(user_id).get()
                if in_archive is not None:
                    paths_to_restore = database.child('archived_clients').child(user_id).child('paths').get()
                    if paths_to_restore is not None:
                        database.child('clients').child(user_id).child('paths').set(paths_to_restore)
                    database.child('archived_clients').child(user_id).delete()  # delete it from archive

                return render_template("confirmation.html")
            elif "update_record" in form.keys():
                # using set makes sure that we only have one value for information - if created dt is already there
                created_dt = database.child('clients/' + user_id + '/information').get()  # cannot be None here
                created_dt = '' if created_dt is None or created_dt.get('created_dt') is None else created_dt.get(
                    'created_dt')
                data['created_dt'] = created_dt  # If it is already there, keep it

                database.child('clients/' + user_id + '/information').update(data)  # using update instead of set
                return render_template("confirmation.html")
            elif "delete_record" in form.keys():
                # TODO clicking cancel on confirm dialog does not stop
                confirmation = form.get('delete_confirmation', 'NO')
                if confirmation == 'YES':
                    # we would archive it
                    paths = database.child('clients').child(user_id).child('paths').get()  # an array
                    if paths is not None:
                        database.child('archived_clients').child(user_id).child('paths').set(
                            paths)  # set it in archived clients

                    service_dates = database.child('clients').child(user_id).child('service_dates').get()  # an array
                    if service_dates is not None:
                        database.child('archived_clients').child(user_id).child('service_dates').set(service_dates)

                    client_info = database.child('clients/' + user_id + '/information').get()  # cannot be None here

                    created_dt = '' if client_info is None or client_info.get(
                        'created_dt') is None else client_info.get('created_dt')

                    # let's keep gender, dob and race
                    arch_gender = client_info.get('gender', '')
                    arc_dob = client_info.get('dob', '')
                    arch_race = client_info.get('race', '')

                    data_to_archive = dict(created_dt=created_dt, deleted_dt=today.strftime('%Y-%m-%d'),
                                           gender=arch_gender, dob=arc_dob, race=arch_race)

                    database.child('archived_clients').child(user_id).child('information').set(data_to_archive)

                    database.child('clients/' + user_id).delete()
                    return render_template("confirmation.html")

                else:
                    info = database.child('clients/%s/information' % user_id).get()
                    # because these are multiple choice
                    race = info.get('race')  # selected race
                    gender = info.get('gender')  # selected gender
                    return render_template("update_and_delete.html", data=info, allow_log='YES',
                                           races_nd_selected=[dict(race=a, selected='YES' if race == a else 'NO') for a
                                                              in
                                                              races],
                                           genders_nd_selected=[dict(gender=a, selected='YES' if gender == a else 'NO')
                                                                for
                                                                a in genders])
            elif "add_client_log_for_record" in form.keys():
                return redirect(url_for('service_log_add', record=user_id))
            else:
                return redirect(url_for('home_page'))
        else:
            return redirect(url_for('home_page'))



@app.route('/test')
@error_handler
def testing():
    return 1/0

@app.route('/get_data/<id>/<type>', methods=['GET'])
@authentication_required
@error_handler
@hide
def get_data(id, type):
    if id == session.get('data_posting_url', ''):
        if type == 'dashboard':
            df = data_for_dashboard(database)
            return jsonify(data=df.to_csv(index=False))

        elif type == 'export':
            start = str(today.year) + '-01-01'
            end = str(today.year) + '-12-31'
            data = database.child('service_logs').order_by_key().start_at(start).end_at(end).get()
            df = generate_csv(data)
            cols = [dict(id=el, label=el, type="string") for el in df.columns]
            rows = [dict(c=[dict(v=el) for el in s]) for s in df.values]
            return jsonify(dict(cols=cols, rows=rows))

        else:
            return abort(404)
    else:
        return abort(403)


if __name__ == '__main__':
    app.run(debug=True)
