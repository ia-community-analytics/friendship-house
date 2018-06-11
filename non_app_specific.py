import pandas as pd

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
    '(In Office)',
    '(Out of Office)',
    'Location'
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
        'Signle Item',
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
        'Signle Item',
        'Basic Pack',
        'Family Pack'
    ])


def intg(x):
    try:
        return int(x)
    except ValueError:
        return 0


def capitalize(word):
    return word[0].upper() + word[1:].lower()


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
    return last_name.lower() + '_' + first_name.lower() + '_' + dob


def initials(full_name):
    # TODO: strip non acii characters?
    if full_name == '':
        return ''
    return ''.join([el[0] for el in full_name.split(' ')])


def get_all_client_keys(database_reference):
    all_clients = database_reference.child('clients').order_by_key().get()
    if all_clients is None:
        all_clients = []
    else:
        all_clients = list(all_clients.keys())

    return all_clients


# TOO: move this and the function to static?
dtype = {'Last Name': "string", 'First Name': "string", 'DOB': "string", 'SEX M/F': "string",
         'Race': "string", '#In Home': "string", 'Zip': "string", 'Phone': "string", 'Service Date': "string",
         'SRF Done (1=Yes, 0=No)': "string", 'Service Requested/Provided': "string", 'Staff (Initials)': "string",
         'Need Met (Y,N,P)': "string", 'UOS (.25, .5, .75, 1)': "number", 'Notes': "string"}


# TODO check field names again
def generate_csv(json_data):
    # this may vary based on the way the data is represented.
    columns = ['Last Name', 'First Name', 'DOB', 'SEX M/F', 'Race', '#In Home', 'Zip', 'Phone', 'Service Date',
               'SRF Done (1=Yes, 0=No)', 'Service Requested/Provided', 'Staff (Initials)',
               'Need Met (Y,N,P)', 'UOS (.25, .5, .75, 1)', 'Notes']
    df = pd.DataFrame(columns=columns)

    for key in json_data.keys():
        for child_key in json_data.get(key).keys():
            temp = pd.DataFrame.from_dict(json_data.get(key).get(child_key), orient='index')
            # for compatibility with the old form
            if 'staff_completing_csl_lname' in temp.columns:
                temp = temp[['lastname', 'firstname', 'dob', 'gender', 'race', 'inhome', 'zipcode', 'phone', 'Date',
                             'staff_completing_csl_fname', 'staff_completing_csl_lname', 'uos', 'staff_notes',
                             'need_met', 'other_service_txt']]
                temp['staff_completing_csl'] = [' '.join(el) for el in
                                                zip(temp['staff_completing_csl_fname'],
                                                    temp['staff_completing_csl_lname'])]
            else:
                temp = temp[['lastname', 'firstname', 'dob', 'gender', 'race', 'inhome', 'zipcode', 'phone', 'Date',
                             'staff_completing_csl', 'uos', 'staff_notes', 'need_met', 'other_service_txt']]

            temp['phone'] = [format_tel(tel) for tel in temp['phone'].values]
            other_indices = temp['uos'] == 'other'
            temp.loc[other_indices, 'uos'] = temp.loc[
                other_indices, 'other_service_txt']  # if other then there should be an entry
            uos_map = {'15': '.25', '30': '.5', '45': '.75', '1': 1}
            temp['UOS (.25, .5, .75, 1)'] = [uos_map.get(el, el) for el in temp['uos'].values]

            # TODO use a gender to sex function . put race
            temp['SEX M/F'] = list(map(lambda x: x[0], temp['gender'].values))
            temp['Race'] = [el[0] for el in
                            temp['race'].values]  # TODO - maybe display full race or have an abbreviations
            temp['Staff (Initials)'] = temp['staff_completing_csl'].apply(initials)
            temp['SRF Done (1=Yes, 0=No)'] = ''
            temp['Service Requested/Provided'] = ''

            temp.rename(index=str, columns={'lastname': 'Last Name',
                                            'firstname': 'First Name',
                                            'dob': 'DOB',
                                            'inhome': '#In Home',
                                            'zipcode': 'Zip',
                                            'phone': 'Phone',
                                            'Date': 'Service Date',
                                            'staff_notes': 'Notes',
                                            'need_met': 'Need Met (Y,N,P)'},
                        inplace=True)
            df = df.append(temp[columns].copy())

    return df.astype(str)


if __name__ == '__main__':
    print("--")
