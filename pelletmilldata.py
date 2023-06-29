
from statistics import mean




resp = [{'CurrentTime': '', 'PelletMill': '5', 'Bin': '551', 'Run': '', 'Item': '', 'Description': '', 'Lbs': '', 'DieSpeed': 110, 'FeederSpeed': 60, 'SteamPct': 37, 'ConditionerTemp': 186.60000610351562, 'ConditionerSpeed': 100, 'ConditionerLoad': 60, 'PelletMillLoad': 72, 'DoorClosed': True, 'SlideGateOpen': True, 'BatchingDestination': 553, 'Bagger2SlideGateOpen': False, 'M45020ON': 1, 'M45020RUNNING': True, 'M45022ON': 1, 'M45022RUNNING': True}, {'CurrentTime': '', 'PelletMill': '5', 'Bin': '552', 'Run': '', 'Item': '', 'Description': '', 'Lbs': '', 'DieSpeed': 110, 'FeederSpeed': 60, 'SteamPct': 37, 'ConditionerTemp': 186.60000610351562, 'ConditionerSpeed': 100, 'ConditionerLoad': 60, 'PelletMillLoad': 72, 'DoorClosed': True, 'SlideGateOpen': False, 'BatchingDestination': 553}, {'CurrentTime': '', 'PelletMill': '5', 'Bin': '553', 'Run': '', 'Item': '', 'Description': '', 'Lbs': '', 'DieSpeed': 110, 'FeederSpeed': 60, 'SteamPct': 37, 'ConditionerTemp': 186.60000610351562, 'ConditionerSpeed': 100, 'ConditionerLoad': 60, 'PelletMillLoad': 72, 'DoorClosed': True, 'SlideGateOpen': False, 'BatchingDestination': 553}, {'CurrentTime': '', 'PelletMill': '5', 'Bin': '554', 'Run': '', 'Item': '', 'Description': '', 'Lbs': '', 'DieSpeed': 110, 'FeederSpeed': 60, 'SteamPct': 37, 'ConditionerTemp': 186.60000610351562, 'ConditionerSpeed': 100, 'ConditionerLoad': 60, 'PelletMillLoad': 72, 'DoorClosed': True, 'SlideGateOpen': False, 'BatchingDestination': 553}]

data = [('515', 89561, '70112', '12% All Stock Pellets', 16034.1), ('516', 89553, '70112', '12% All Stock Pellets', 16858.1), ('517', 89541, '36220', 'Quail & Gamebird Layer an', 20060.0), ('518', 89559, '36220', 'Quail & Gamebird Layer an', 19990.0), ('531/533', 89540, '21516', 'NatureCrest Rabbit Feed', 40022.0), ('532/534', 89556, '31522', 'Show Flock Layer 22 Mini', 40027.0), ('551', 89501, '111P', 'Deer Corn Premix Pellet', 56020.0), ('552', 89535, '70112', '12% All Stock Pellets', 32066.0), ('553', 89564, '70112', '12% All Stock Pellets', 4020.1)]

tags = [90.0, 155.6999969482422, 35.0, 90.0, 48.36065673828125, 75.0, 64.0, True, False, True, True, False, 201, True, True, True, False, 100.0, 141.6999969482422, 20.0, 40.0, 52.295082092285156, 40.0, 69.0, False, True, True, True, True, None, True, True, False, True, 100.0, 110.0, 119.80000305175781, 157.90000915527344, 5.0, 12.0, 40.0, 30.0, 0.0, 49.918033599853516, 20.0, 13.0, 0.0, 83.0, True, True, False, False, True, False, True, 0.0, 2.0]

data_list_of_dictionaries = []
for i in range(len(data)):
    if i in [0,1]:
        pelletmill = '1'
        diespeed = tags[0]
        feederspeed = tags[5]
        steampct = tags[2]
        conditionertemp = tags[1]
        conditionerspeed = tags[3]
        conditionerload = tags[4]
        pelletmillload = tags[6]
        doorclosed = tags[9]
        if i in [0]:
            slidegateopen = tags[15]
            binactive = tags[7]
        elif i in [1]:
            slidegateopen = tags[16]
            binactive = tags[8]
    elif i in [2, 3]:
        pelletmill = '2'
        diespeed = tags[17]
        feederspeed = tags[22]
        steampct = tags[19]
        conditionertemp = tags[18]
        conditionerspeed = tags[20]
        conditionerload = tags[21]
        pelletmillload = tags[23]
        doorclosed = tags[26]
        if i in [2]:
            slidegateopen = tags[31]
            binactive = tags[24]
        elif i in [3]:
            slidegateopen = tags[33]
            binactive = tags[25]
    elif i in [4, 5]:
        pelletmill = '3/4'
        diespeed = mean([tags[34],tags[35]])
        feederspeed = mean([tags[44],tags[45]])
        steampct = mean([tags[38],tags[39]])
        conditionertemp = mean([tags[36],tags[37]])
        conditionerspeed = mean([tags[40],tags[41]])
        conditionerload = mean([tags[42],tags[43]])
        pelletmillload = mean([tags[46],tags[47]])
        doorclosed = False if tags[48] == False or tags[49] == False else True
        if i in [4]:
            slidegateopen = tags[53]
            binactive = True if tags[55] == 2.0 else False
        elif i in [5]:
            slidegateopen = tags[54]
            binactive = True if tags[56] == 2.0 else False
    elif i in [6, 7, 8, 9]:
        pelletmill = '5'
        diespeed = resp[0]['DieSpeed']
        feederspeed = resp[0]['FeederSpeed']
        steampct = resp[0]['SteamPct']
        conditionertemp = resp[0]['DieSpeed']
        conditionerspeed = resp[0]['ConditionerSpeed']
        conditionerload = resp[0]['ConditionerLoad']
        pelletmillload = resp[0]['PelletMillLoad']
        doorclosed = resp[0]['DoorClosed']
        if i in [6]:
            slidegateopen = resp[0]['SlideGateOpen']
            binactive = resp[0]['SlideGateOpen']
        elif i in [7]:
            slidegateopen =  resp[1]['SlideGateOpen']
            binactive =  resp[1]['SlideGateOpen']
        elif i in [8]:
            slidegateopen =  resp[2]['SlideGateOpen']
            binactive =  resp[2]['SlideGateOpen'] 
        elif i in [9]:
            slidegateopen =  resp[3]['SlideGateOpen']
            binactive =  resp[3]['SlideGateOpen']
    data_list_of_dictionaries.append(data_dict)
for data_dict in data_list_of_dictionaries:
    for key, value in data_dict.items():
        print(f'{key}: {value}')
    print()
