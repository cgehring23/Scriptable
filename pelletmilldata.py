import pyodbc
import datetime
from datetime import datetime
from pylogix import PLC
from statistics import mean
import time
import pandas as pd
import paramiko
import threading
import inspect

def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

def timed_execution():
    hostname='192.168.1.204'
    port=22
    username='tucker'
    password='TuckMill2552$'

    cmd= "py Documents\pelletmill5.py"
    try:
        ssh=paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname,port,username,password)
        stdin,stdout,stderr=ssh.exec_command(cmd)
        outlines=stdout.readlines()
        resp=''.join(outlines)
        resp=eval(resp)
    finally:
        if ssh:
            ssh.close()
    currentTime = datetime.now()
    print(resp, "and this is line", lineno())
    s41Dest = resp[0]['BatchingDestination']
     
    server = r"TM-SQL1\BESTMIX" 
    database = r"Batching" 
    username = "curran" 
    password = "SuperLay22" 
    cnxn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER="+server+"; DATABASE="+database+";UID="+username+";PWD="+ password,autocommit=True)
    cursor = cnxn.cursor()

        
    if (resp[0]["M45020ON"] == True
    and resp[0]["M45020RUNNING"] == 1 and resp[0]["M45022ON"] == True
    and resp[0]["M45022RUNNING"] == 1):
        print("S41 Route is Pellet Mill 5 Bins", "and this is line", lineno())
        cursor.execute("""INSERT INTO [Batching].[dbo].[PM5BinDestinations] 
        SELECT * FROM [Batching].[dbo].[S41];
         
        UPDATE [Batching].[dbo].[PM5BinDestinations]
        SET Dest1 = ?
        WHERE rnk = 1 AND Dest1 = 'S41'
        """, s41Dest)
    else:
        print("S41 Route is Bagger2", "and this is line", lineno())

    x = 30

    for i in range(x):
        print(f"\rSleeping for {x} seconds: {i+1} seconds", end="")
        time.sleep(1)
    print()

    sql = """
SELECT TOP (1000) [Dest1]
      ,[Run]
      ,[Recipe]
      ,[ProductDescription]
      ,[Actual]
  FROM [Batching].[dbo].[PelletMillBinAssignments]
  """
    cursor.execute(sql)

    data = cursor.fetchall()
    for index, element in enumerate(data):
        print(f'{index}: {element}')

    tag_list = ["PM_HMI_FLOAT2[7]","PM_HMI_FLOAT[1]","PM_HMI_FLOAT[3]","PM_HMI_FLOAT[16]","PM_HMI_FLOAT[18]","PM_HMI_FLOAT[2]"
,"PM_HMI_FLOAT[0]","PM_HMI_BOOL[50]","PM_HMI_BOOL[51]","PM1_2_IO:I.Data[17].1","PM_HMI_BOOL[30]","PM_HMI_BOOL[54]", "PM_1_BIN_SELECTED"
,"PM1_2_IO:I.Data[6].2","PM_HMI_BOOL[32]","PM_HMI_BOOL[42]","PM_HMI_BOOL[44]",

"PM_HMI_FLOAT2[8]","PM_HMI_FLOAT[5]","PM_HMI_FLOAT[7]","PM_HMI_FLOAT[17]","PM_HMI_FLOAT[19]","PM_HMI_FLOAT[6]","PM_HMI_FLOAT[4]",
"PM_HMI_BOOL[52]","PM_HMI_BOOL[53]","PM1_2_IO:I.Data[7].3","PM_HMI_BOOL[31]","PM_HMI_BOOL[55]","PM_2_BIN_SELECTED","PM1_2_IO:I.Data[6].2",
"PM_HMI_BOOL[33]","PM_HMI_BOOL[46]","PM_HMI_BOOL[48]",

"PM34_HMI_FLOAT[2]","PM34_HMI_FLOAT[3]","PM34_HMI_FLOAT[13]","PM34_HMI_FLOAT[15]","PM34_HMI_FLOAT[6]","PM34_HMI_FLOAT[7]","PM34_HMI_FLOAT[8]",
"PM34_HMI_FLOAT[10]","PM34_HMI_FLOAT[9]","PM34_HMI_FLOAT[11]","PM34_HMI_FLOAT[4]","PM34_HMI_FLOAT[5]","PM34_HMI_FLOAT[0]","PM34_HMI_FLOAT[1]",
"PM_34_IO:13:I.0","PM_34_IO:14:I.0","PM3_BIN_LL","PM4_BIN_LL","PM1_2_IO:I.Data[6].2","PM34_HMI_BIT[18]","PM34_HMI_BIT[19]", "PM34_HMI_FLOAT[20]", 
"PM34_HMI_FLOAT[22]"]

    tags = []
    tagnames = []

    with PLC() as comm:
        comm = PLC()
        comm.IPAddress = "192.168.1.55"
        value = comm.Read(tag_list)
        for r in value:
            tags.append(r.Value)
            tagnames.append(r.TagName)

#for i, item in enumerate(tagnames):
    #print(f"{i}. {item}")

    print("Len(data): ", len(data))

    
    data = [{
    'CurrentTime':currentTime, 
    'PelletMill':'1', 
    'Bin':data[0][0], 
    'Run':data[0][1],
    'Item':data[0][2], 
    'Description':data[0][3],
    'Lbs':data[0][4],
    'DieSpeed':tags[0],
    'FeederSpeed':tags[5],
    'SteamPct':tags[2],
    'ConditionerTemp':tags[1],
    'ConditionerSpeed':tags[3],
    'ConditionerLoad':tags[4],
    'PelletMillLoad':tags[6],
    'DoorClosed':tags[9],
    "SlideGateOpen":tags[15],
    "BinActive":tags[7]
    },
    {
    'CurrentTime':currentTime, 
    'PelletMill':'1', 
    'Bin':data[1][0], 
    'Run':data[1][1],
    'Item':data[1][2], 
    'Description':data[1][3],
    'Lbs':data[1][4],
    'DieSpeed':tags[0],
    'FeederSpeed':tags[5],
    'SteamPct':tags[3],
    'ConditionerTemp':tags[1],
    'ConditionerSpeed':tags[3],
    'ConditionerLoad':tags[4],
    'PelletMillLoad':tags[6],
    'DoorClosed':tags[9],
    "SlideGateOpen":tags[16],
    "BinActive":tags[8]
    },
    {
    'CurrentTime':currentTime, 
    'PelletMill':'2', 
    'Bin':data[2][0], 
    'Run':data[2][1],
    'Item':data[2][2], 
    'Description':data[2][3],
    'Lbs':data[2][4],
    'DieSpeed':tags[17],
    'FeederSpeed':tags[22],
    'SteamPct':tags[19],
    'ConditionerTemp':tags[18],
    'ConditionerSpeed':tags[20],
    'ConditionerLoad':tags[21],
    'PelletMillLoad':tags[23],
    'DoorClosed':tags[26],
    "SlideGateOpen":tags[31],
    "BinActive":tags[24]
    },
    {
    'CurrentTime':currentTime, 
    'PelletMill':'2', 
    'Bin':data[3][0], 
    'Run':data[3][1],
    'Item':data[3][2], 
    'Description':data[3][3],
    'Lbs':data[3][4],
    'DieSpeed':tags[17],
    'FeederSpeed':tags[22],
    'SteamPct':tags[19],
    'ConditionerTemp':tags[18],
    'ConditionerSpeed':tags[20],
    'ConditionerLoad':tags[21],
    'PelletMillLoad':tags[23],
    'DoorClosed':tags[26],
    "SlideGateOpen":tags[33],
    "BinActive":tags[25]
    },
     {
    'CurrentTime':currentTime, 
    'PelletMill':'3/4', 
    'Bin':data[4][0], 
    'Run':data[4][1],
    'Item':data[4][2], 
    'Description':data[4][3],
    'Lbs':data[4][4],
    'DieSpeed':mean([tags[34],tags[35]]),
    'FeederSpeed':mean([tags[44],tags[45]]),
    'SteamPct':mean([tags[38],tags[39]]),
    'ConditionerTemp':mean([tags[36],tags[37]]),
    'ConditionerSpeed':mean([tags[40],tags[41]]),
    'ConditionerLoad':mean([tags[42],tags[43]]),
    'PelletMillLoad':mean([tags[46],tags[47]]),
    'DoorClosed':0 if tags[48] == False or tags[49] == False else 1,
    "SlideGateOpen":tags[53],
    "BinActive":tags[55]
    },
    {
    'CurrentTime':currentTime, 
    'PelletMill':'3/4', 
    'Bin':data[5][0], 
    'Run':data[5][1],
    'Item':data[5][2], 
    'Description':data[5][3],
    'Lbs':data[5][4],
    'DieSpeed':mean([tags[34],tags[35]]),
    'FeederSpeed':mean([tags[44],tags[45]]),
    'SteamPct':mean([tags[38],tags[39]]),
    'ConditionerTemp':mean([tags[36],tags[37]]),
    'ConditionerSpeed':mean([tags[40],tags[41]]),
    'ConditionerLoad':mean([tags[42],tags[43]]),
    'PelletMillLoad':mean([tags[46],tags[47]]),
    'DoorClosed':0 if tags[48] == False or tags[49] == False else 1,
    "SlideGateOpen":tags[54],
    "BinActive":tags[56]
    },
    {
    'CurrentTime':currentTime, 
    'PelletMill':'5', 
    'Bin':data[6][0], 
    'Run':data[6][1],
    'Item':data[6][2], 
    'Description':data[6][3],
    'Lbs':data[6][4],
    'DieSpeed':resp[0]['DieSpeed'],
    'FeederSpeed':resp[0]['FeederSpeed'],
    'SteamPct':resp[0]['SteamPct'],
    'ConditionerTemp':resp[0]['ConditionerTemp'],
    'ConditionerSpeed':resp[0]['ConditionerSpeed'],
    'ConditionerLoad':resp[0]['ConditionerLoad'],
    'PelletMillLoad':resp[0]['PelletMillLoad'],
    'DoorClosed':resp[0]['DoorClosed'],
    "SlideGateOpen":resp[0]['SlideGateOpen'],
    "BinActive":resp[0]['SlideGateOpen']
    },
       {
    'CurrentTime':currentTime, 
    'PelletMill':'5', 
    'Bin':data[7][0], 
    'Run':data[7][1],
    'Item':data[7][2], 
    'Description':data[7][3],
    'Lbs':data[7][4],
    'DieSpeed':resp[1]['DieSpeed'],
    'FeederSpeed':resp[1]['FeederSpeed'],
    'SteamPct':resp[1]['SteamPct'],
    'ConditionerTemp':resp[1]['ConditionerTemp'],
    'ConditionerSpeed':resp[1]['ConditionerSpeed'],
    'ConditionerLoad':resp[1]['ConditionerLoad'],
    'PelletMillLoad':resp[1]['PelletMillLoad'],
    'DoorClosed':resp[1]['DoorClosed'],
    "SlideGateOpen":resp[1]['SlideGateOpen'],
    "BinActive":resp[1]['SlideGateOpen']
    },
       {
    'CurrentTime':currentTime, 
    'PelletMill':'5', 
    'Bin':data[8][0], 
    'Run':data[8][1],
    'Item':data[8][2] , 
    'Description':data[8][3],
    'Lbs':data[8][4],
    'DieSpeed':resp[2]['DieSpeed'],
    'FeederSpeed':resp[2]['FeederSpeed'],
    'SteamPct':resp[2]['SteamPct'],
    'ConditionerTemp':resp[2]['ConditionerTemp'],
    'ConditionerSpeed':resp[2]['ConditionerSpeed'],
    'ConditionerLoad':resp[2]['ConditionerLoad'],
    'PelletMillLoad':resp[2]['PelletMillLoad'],
    'DoorClosed':resp[2]['DoorClosed'],
    "SlideGateOpen":resp[2]['SlideGateOpen'],
    "BinActive":resp[2]['SlideGateOpen']
    },
       {
    'CurrentTime':currentTime, 
    'PelletMill':'5', 
    'Bin':data[9][0], 
    'Run':data[9][1],
    'Item':data[9][2], 
    'Description':data[9][3],
    'Lbs':data[9][4],
    'DieSpeed':resp[3]['DieSpeed'],
    'FeederSpeed':resp[3]['FeederSpeed'],
    'SteamPct':resp[3]['SteamPct'],
    'ConditionerTemp':resp[3]['ConditionerTemp'],
    'ConditionerSpeed':resp[3]['ConditionerSpeed'],
    'ConditionerLoad':resp[3]['ConditionerLoad'],
    'PelletMillLoad':resp[3]['PelletMillLoad'],
    'DoorClosed':resp[3]['DoorClosed'],
    "SlideGateOpen":resp[3]['SlideGateOpen'],
    "BinActive":resp[3]['SlideGateOpen']
    }
    ]

    data = data[:len(data)-1]
    #print(data, "and this is line", lineno())
    #print(data[6][2], data[7][2], data[8][2], data[9][2])
    df = pd.DataFrame(data)
        #print(*df, sep="\n")

    for index, row in df.iterrows():
        cursor.execute("""INSERT INTO [Batching].[dbo].[PelletProduction] 
    (CurrentTime, PelletMill, Bin, Run, Item, Description, Lbs, DieSpeed, FeederSpeed, SteamPct, 
    ConditionerTemp, ConditionerSpeed, ConditionerLoad, PelletMillLoad, DoorClosed, SlideGateOpen, BinActive) 
    values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
    row.CurrentTime, row.PelletMill, row.Bin, row.Run, row.Item, row.Description, row.Lbs, row.DieSpeed, 
    row.FeederSpeed, row.SteamPct, row.ConditionerTemp, row.ConditionerSpeed, row.ConditionerLoad, 
    row.PelletMillLoad, row.DoorClosed, row.SlideGateOpen, row.BinActive)
    
        if cursor.rowcount == 1:
            print("Row inserted")
        else:
            print("Row not inserted")
        
    print(currentTime.strftime('%I:%M:%S %p'), "and this is line", lineno())
   
    cnxn.commit()
    cursor.close()
def run_timer(interval):
    while True:
        start_time = time.time()
        timed_execution()
        elapsed_time = time.time() - start_time

        if elapsed_time < interval:
            time.sleep(interval - elapsed_time)
        else:
            print("Execution time exceeded the interval.", "and this is line", lineno())


if __name__ == "__main__":
    interval = 300  # Interval in seconds

    # Start the timer in a separate thread
    timer_thread = threading.Thread(target=run_timer, args=(interval,))
    timer_thread.start()

    # Continue with other operations in the main thread
    while True:
        # Your other operations...
        # ...
        time.sleep(1)  # Add a small delay to avoid excessive CPU usage

