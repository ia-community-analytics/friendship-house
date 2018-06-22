import pandas as pd
import random
import string

today = pd.datetime.today()
races = [
    "African American/Black",
    "American Indian/Alaskan Native",
    "Asian",
    "Bi-racial",
    "Caucasian/White",
    "Hawaiian/Pacific Islander",
    "Multi-racial",
    "Other"
]
genders = [
    "Female",
    "Male",
    "Transgender",
    "Other"
]

program_status = [
    'ACES MEMBER',
    'Housing Services',
    'S.W.H.P. Participant',
    'Youth Ed. Family',
    'Senior Support',
    'Adult Education',
    'FOC Services',
    'Other'
]

appointment_type = [
    'Indirect Service',
    'Phone Call',
    'Walk In/Group',
    'Scheduled Appointment',
    'In Office',
    'Out of Office'
]

appointment_description = [
    'Orientation/Pre Enrollment',
    'Initial Intake/Assessment/Plan',
    'General CM/Coaching/Follow-up',
    'Finance Coaching',
    'Employment Coaching',
    'Re-Assessment/New Plan',
    'Case Staffing',
    'Case Closure'
]

service_uos = [
    dict(display='15 Minutes', value=15),
    dict(display='30 Minutes', value=30),
    dict(display='45 Minutes', value=45),
    dict(display='1 Hour', value=1),
    dict(display='Other', value='other')
]

supportive_service_provided = dict(
    Food=[
        '1-2 Day Supply',
        '3-5 Day Supply',
        'Dog Food',
        'Cat Food'
    ],
    Clothing=[
        'Single Item',
        'Outfit',
        'Multiple Items',
        'Multiple Outfits'
    ],
    Hygiene=[
        'Single Item',
        'Basic Pack',
        'Family Pack'
    ],
    Baby_Items=[
        'Diaper/Wipes',
        'Formula',
        'Baby Food',
        'Layette'
    ],
    Financial=[
        'RR: Deposit',
        'RR: Rent',
        'Rent Arrears',
        'Utility Arrears'
    ],
    Legal=[
        'PSL',
        'Immigration',
        'Other'
    ],
    HouseHold=[
        'Single Item',
        'Basic Pack',
        'Family Pack'
    ])

name_processing_separator = '<*>'


# this will be used in javascript as well - see homepage. to make everything simple, only userids are processed
def process_name(name: str):
    return name.strip().replace(' ', name_processing_separator)


def display_name(name: str):
    return name.strip().replace(name_processing_separator, ' ')


def intg(x):
    try:
        return int(x)
    except ValueError:
        return 0


def capitalize(word: str, sep=name_processing_separator):
    if sep not in word.strip():
        if '-' in word:
            temp = word.strip().split('-')
            return '-'.join([el[0].upper() + el[1:].lower() for el in temp])
        else:
            return word[0].upper() + word[1:].lower()
    else:
        elements = word.split(sep)
        return ' '.join([capitalize(el) for el in elements])


def month(date):
    return '-'.join(date.split('-')[0:2] + ['01'])


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
    return process_name(last_name).lower() + '_' + process_name(first_name).lower() + '_' + dob


def user_id_to_name(user_id):
    temp = user_id.split('_')
    return (capitalize(display_name(temp[1]), ' '), capitalize(display_name(temp[0]), ' '))  # first name, last name


def initials(full_name):
    # TODO: strip non acii characters?
    full_name = str(full_name)
    if full_name == '':
        return ''
    return ''.join([el[0].upper() if len(el) > 0 else '' for el in full_name.split(' ')])


def get_all_client_keys(database_reference):
    all_clients = database_reference.child('clients').order_by_key().get()
    if all_clients is None:
        all_clients = []
    else:
        all_clients = list(all_clients.keys())

    return all_clients


def get_archived_client_keys(database_reference):
    archived_clients = database_reference.child('archived_clients').order_by_key().get()
    if archived_clients is None:
        archived_clients = []
    else:
        archived_clients = list(archived_clients.keys())

    return archived_clients


# TOO: move this and the function to static?
dtype = {'Last Name': "string", 'First Name': "string", 'DOB': "string", 'SEX M/F': "string",
         'Race': "string", '#In Home': "string", 'Zip': "string", 'Phone': "string", 'Service Date': "string",
         'SRF Done (1=Yes, 0=No)': "string", 'Service Requested/Provided': "string", 'Staff (Initials)': "string",
         'Need Met (Y,N,P)': "string", 'UOS (.25, .5, .75, 1)': "number", 'Notes': "string"}

fields_to_keep = ['lastname', 'firstname', 'dob', 'gender', 'race', 'inhome', 'zipcode', 'phone', 'Date',
                  'staff_completing_csl_fname', 'staff_completing_csl_lname', 'uos', 'staff_notes',
                  'need_met', 'other_service_txt']

old_fields = ['lastname', 'firstname', 'dob', 'gender', 'race', 'inhome', 'zipcode', 'phone', 'Date',
              'staff_completing_csl', 'uos', 'staff_notes', 'need_met', 'other_service_txt']

csv_columns = ['Last Name', 'First Name', 'DOB', 'SEX M/F', 'Race', '#In Home', 'Zip', 'Phone', 'Service Date',
               'SRF Done (1=Yes, 0=No)', 'Service Requested/Provided', 'Staff (Initials)',
               'Need Met (Y,N,P)', 'UOS (.25, .5, .75, 1)', 'Notes']

column_rename = {'lastname': 'Last Name',
                 'firstname': 'First Name',
                 'dob': 'DOB',
                 'inhome': '#In Home',
                 'zipcode': 'Zip',
                 'phone': 'Phone',
                 'Date': 'Service Date',
                 'staff_notes': 'Notes',
                 'need_met': 'Need Met (Y,N,P)'}


# TODO check field names again
def generate_random_url(N):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))


def generate_csv(json_data):
    # this may vary based on the way the data is represented.
    df = pd.DataFrame(columns=csv_columns)

    for key in json_data.keys():
        for child_key in json_data.get(key).keys():
            temp = pd.DataFrame.from_dict(json_data.get(key).get(child_key), orient='index').fillna('')
            # for compatibility with the old form
            if 'staff_completing_csl_lname' in temp.columns:
                temp = temp[fields_to_keep]
                temp['staff_completing_csl'] = [' '.join([str(el[0]).strip(), str(el[1]).strip()]) for el in
                                                zip(temp['staff_completing_csl_fname'].apply(
                                                    display_name).values.astype(str),
                                                    temp['staff_completing_csl_lname'].apply(
                                                        display_name).values.astype(str))]
            else:
                temp = temp[old_fields]

            temp['phone'] = [format_tel(tel) for tel in temp['phone'].values]
            other_indices = temp['uos'] == 'other'
            temp.loc[other_indices, 'uos'] = temp.loc[
                other_indices, 'other_service_txt']  # if other then there should be an entry
            uos_map = {'15': '.25', '30': '.5', '45': '.75', '1': '1'}
            temp['UOS (.25, .5, .75, 1)'] = [uos_map.get(el, el) for el in temp['uos'].values]

            # TODO use a gender to sex function . put race
            temp['SEX M/F'] = list(map(lambda x: x[0] if len(x) > 0 else x, temp['gender'].values))
            temp['Race'] = [el[0] if len(el) > 0 else el for el in
                            temp['race'].values]  # TODO - maybe display full race or have an abbreviations
            temp['Staff (Initials)'] = temp['staff_completing_csl'].apply(initials)
            temp['SRF Done (1=Yes, 0=No)'] = ''
            temp['Service Requested/Provided'] = ''

            #
            temp['firstname'] = temp['firstname'].apply(display_name)
            temp['lastname'] = temp['lastname'].apply(display_name)

            temp.rename(index=str, columns=column_rename, inplace=True)
            df = df.append(temp[csv_columns].copy())

    return df.astype(str)


def generate_csv_from_path(log):
    if isinstance(log, list):
        df = pd.DataFrame(log)
    else:
        df = pd.DataFrame(log, index=[0])  # the dataframe

    # there may be subsets with the old log format

    if 'staff_completing_csl_lname' in df.columns:
        if 'staff_completing_csl' in df.columns:
            df_new_format = df[pd.isnull(df['staff_completing_csl'])].copy()
            df_old_format = df[~pd.isnull(df['staff_completing_csl'])].copy()
            df_old_format = df_old_format[old_fields]

            df_new_format = df_new_format[fields_to_keep]
            df_new_format['staff_completing_csl'] = [' '.join([str(el[0]).strip(), str(el[1]).strip()]) for el in
                                                     zip(df_new_format['staff_completing_csl_fname'].apply(
                                                         display_name).values.astype(str),
                                                         df_new_format['staff_completing_csl_lname'].apply(
                                                             display_name).values.astype(
                                                             str))]

            df = df_new_format.append(df_old_format)  # now they both have staff_completing_csl field
        else:
            df['staff_completing_csl'] = [' '.join([str(el[0]).strip(), str(el[1]).strip()]) for el in
                                          zip(df['staff_completing_csl_fname'].apply(display_name).values.astype(str),
                                              df['staff_completing_csl_lname'].apply(display_name).values.astype(str))]
    else:
        df = df[old_fields]

    df['phone'] = [format_tel(tel) for tel in df['phone'].values]
    other_indices = df['uos'] == 'other'
    df.loc[other_indices, 'uos'] = df.loc[
        other_indices, 'other_service_txt']  # if other then there should be an entry
    uos_map = {'15': '.25', '30': '.5', '45': '.75', '1': '1'}
    df['UOS (.25, .5, .75, 1)'] = [uos_map.get(el, el) for el in df['uos'].values]

    # TODO use a gender to sex function . put race as is, no abbreviation
    df['SEX M/F'] = list(map(lambda x: x[0] if len(x) > 0 else x, df['gender'].values))
    df['Race'] = [el[0] if len(el) > 0 else el for el in
                  df['race'].values]  # TODO - maybe display full race or have an abbreviations
    df['Staff (Initials)'] = df['staff_completing_csl'].apply(initials)
    df['SRF Done (1=Yes, 0=No)'] = ''
    df['Service Requested/Provided'] = ''

    df['firstname'] = df['firstname'].apply(display_name)
    df['lastname'] = df['lastname'].apply(display_name)
    df.rename(index=str, columns=column_rename, inplace=True)
    df['user_id'] = list(map(create_user_id, df['Last Name'].values, df['First Name'].values, df['DOB'].values))

    return df[csv_columns + ['user_id']].astype(str)


# data for clients
def old_data_for_dashboard(database_reference, specific_users=None):
    data_frame = pd.DataFrame(columns=csv_columns + ['created_dt', 'isActive', 'deleted_dt'])

    all_clients = get_all_client_keys(database_reference)  # the list of clients - the user ids.
    archived_clients = get_archived_client_keys(database_reference)

    if specific_users is not None:
        specific_users = [specific_users] if isinstance(specific_users, str) else specific_users  # must be a list
        # TODo - try except etc...

        all_clients = [user for user in specific_users if user in all_clients]
        archived_clients = [user for user in specific_users if user in archived_clients]

    if len(all_clients) == 0 and len(archived_clients) == 0:
        return data_frame

    # active client logs
    all_clients_paths = [database_reference.child('clients').child(client).child('paths').get() for client in
                         all_clients]
    all_clients_paths = [path for path in all_clients_paths if path is not None]
    all_clients_paths = [path for path_list in all_clients_paths for path in path_list if path is not None]

    # archive client logs
    arch_clients_paths = [database_reference.child('archived_clients').child(client).child('paths').get() for client in
                          archived_clients]
    arch_clients_paths = [path for path in arch_clients_paths if path is not None]
    arch_clients_paths = [path for path_list in arch_clients_paths for path in path_list if path is not None]

    # combined the paths and get a list of all logs
    all_paths = all_clients_paths + arch_clients_paths
    if len(all_paths) == 0:
        return data_frame

    logs = [database_reference.child(path).get() for path in all_paths]
    logs = [log for log in logs if log is not None]  # we do not need None

    if len(logs) == 0:
        return data_frame

    # get the full data
    log_data = generate_csv_from_path(logs)

    # do it for the first. then for all others and append.
    created_dts = []
    deleted_dts = []
    active_sttus = []
    for client in all_clients + archived_clients:
        if client in archived_clients:
            reference = database_reference.child('archived_clients')
        else:
            reference = database_reference.child('clients')

        # get the created dt and deleted dt
        created_dt = reference.child(client).child('information').get()
        created_dt = '' if created_dt is None or created_dt.get('created_dt') is None else created_dt.get(
            'created_dt')

        deleted_dt = reference.child(client).child('information').get()
        deleted_dt = '' if deleted_dt is None or deleted_dt.get('deleted_dt') is None else deleted_dt.get(
            'deleted_dt')

        created_dts.append(created_dt)
        deleted_dts.append(deleted_dt)
        active_sttus.append(1 if client in all_clients else 0)

    # create data from this - could use numpy
    active_sttus_data = pd.DataFrame(columns=['user_id', 'created_dt', 'isActive', 'deleted_dt'])

    active_sttus_data['user_id'] = all_clients + archived_clients
    active_sttus_data['created_dt'] = created_dts
    active_sttus_data['isActive'] = active_sttus
    active_sttus_data['deleted_dt'] = deleted_dts

    data_frame = log_data.merge(active_sttus_data, how='left', on='user_id')
    data_frame.fillna('')
    # TODO; drop user_id?
    return data_frame.astype(str)


def data_for_dashboard(database_reference):
    df = pd.DataFrame(
        columns=['service_dates', 'created_dt', 'deleted_dt', 'gender', 'race', 'dob', 'last_name', 'first_name',
                 'join_in', 'activity'])

    active_clients = database_reference.child('clients').get()
    archived_clients = database_reference.child('archived_clients').get()
    if active_clients is not None:
        active_clients = [(el[0], el[1].get('information', ['']), el[1].get('service_dates', [''])) for el in
                          active_clients.items()]
    else:
        active_clients = []
    if archived_clients is not None:
        archived_clients = [(el[0], el[1].get('information', ['']), el[1].get('service_dates', [''])) for el in
                            archived_clients.items()]
    else:
        archived_clients = []

    if len(active_clients) == 0 and len(archived_clients) == 0:
        return df

    gender, race, dob, created, deleted, service_date, first_name, last_name, join_in, activity = [], [], [], [], [], [], [], [], [], []

    for el in active_clients + archived_clients:
        name = user_id_to_name(el[0])
        cur_fname = [name[0]]
        cur_lname = [name[1]]
        cur_gender = [el[1].get('gender', '')]
        cur_race = [el[1].get('race', '')]
        cur_dob = [el[1].get('dob', '')]
        cur_crtdt = [el[1].get('created_dt', '')]
        cur_dltdt = [el[1].get('deleted_dt', '')] # should be '' for active users so I will use this instead of el in archive_clients

        n = len(el[2]) + 1 if el[2] != [''] else 1

        last_name.extend(cur_lname * (n+1))
        first_name.extend(cur_fname * (n+1))
        gender.extend(cur_gender * (n+1))
        race.extend(cur_race * (n+1))
        dob.extend(cur_dob * (n+1))
        created.extend(cur_crtdt * (n+1))
        deleted.extend(cur_dltdt * (n+1))
        join_in.extend([1] + [0] * (n))
        if cur_dltdt == ['']:
            # they did not leave
            activity.extend(['join'] + ['service'] * (n-1) + [''])
            service_date.extend(cur_crtdt + (el[2] if el[2] != [''] else []) + [''])
        else:
            # they left
            activity.extend(['join'] + ['service'] * (n - 1) + ['left'])
            service_date.extend(cur_crtdt + (el[2] if el[2] != [''] else []) + cur_dltdt)

    df['service_dates'] = service_date
    df['created_dt'] = created
    df['deleted_dt'] = deleted
    df['gender'] = gender
    df['race'] = race
    df['dob'] = dob
    df['last_name'] = last_name
    df['first_name'] = first_name
    df['join_in'] = join_in
    df['activity'] = activity

    return df[(df['service_dates'] != '') & (df['activity'] != '')]

# TODO: create a function that provides a way to have joining date as a 1 when joining


if __name__ == '__main__':
    print("--")
