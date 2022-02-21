# Name: WEH002004 Big Time
# Author: marksard
# Version: 1.0
# Python 3.6 or later (maybe)

# ***************************
import datetime
import weh002004a

# ***************************
__big_digit = [
    [   b'\xff\xff\xff', # 0
        b'\xff\x20\xff',
        b'\xff\x20\xff',
        b'\xff\xff\xff'
    ],
    [   b'\xff\xff\x20', # 1
        b'\x20\xff\x20',
        b'\x20\xff\x20',
        b'\xff\xff\xff'
    ],
    [   b'\xff\xff\xff', # 2
        b'\x20\x5f\xff',
        b'\xff\x20\x20',
        b'\xff\xff\xff'
    ],
    [   b'\xff\xff\xff', # 3
        b'\x20\x5f\xff',
        b'\x20\x20\xff',
        b'\xff\xff\xff'
    ],
    [   b'\xff\x20\x20', # 4
        b'\xff\x20\xff',
        b'\xff\xff\xff',
        b'\x20\x20\xff'
    ],
    [   b'\xff\xff\xff', # 5
        b'\xff\x5f\x20',
        b'\x20\x20\xff',
        b'\xff\xff\xff'
    ],
    [   b'\xff\xff\xff', # 6
        b'\xff\x5f\x20',
        b'\xff\x20\xff',
        b'\xff\xff\xff'
    ],
    [   b'\xff\xff\xff', # 7
        b'\xff\x20\xff',
        b'\x20\x20\xff',
        b'\x20\x20\xff'
    ],
    [   b'\xff\xff\xff', # 8
        b'\xff\x5f\xff',
        b'\xff\x20\xff',
        b'\xff\xff\xff'
    ],
    [   b'\xff\xff\xff', # 9
        b'\xff\x5f\xff',
        b'\x20\x20\xff',
        b'\xff\xff\xff'
    ],
    [   b'\x20\x20\xff\x20', # :
        b'\x20\xff\x20\x20',
        b'\x20\x20\xff\x20',
        b'\x20\xff\x20\x20'
    ],
    [   b'\x20\xff\x20\x20', # : (alternative)
        b'\x20\x20\xff\x20',
        b'\x20\xff\x20\x20',
        b'\x20\x20\xff\x20'
    ]
]

__week_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def write_clock_v1(disp: weh002004a.WEH002004A, tm: datetime):
    if tm.second & 1 == 1:
        st = tm.strftime('%H:%M')
    else:
        st = tm.strftime('%H;%M')

    line = [b'',b'',b'',b'']
    for i in range(0, 5):
        num = ord(st[i]) - 48
        line[0] = line[0] + __big_digit[num][0] + b'\x20'
        line[1] = line[1] + __big_digit[num][1] + b'\x20'
        line[2] = line[2] + __big_digit[num][2] + b'\x20'
        line[3] = line[3] + __big_digit[num][3] + b'\x20'

    disp.write_bytes(line[0], 0)
    disp.write_bytes(line[1], 1)
    disp.write_bytes(line[2], 2)
    disp.write_bytes(line[3], 3)

def write_clock_v2(disp: weh002004a.WEH002004A, tm: datetime):
    add_1 = tm.strftime(':%S')
    add_2 = '   '
    add_3 = tm.strftime('/%d')        
    add_4 = __week_name[tm.weekday()]

    st = tm.strftime('%H %M')

    line = [b'',b'',b'',b'']
    for i in range(0, 5):
        if st[i] == ' ':
            line[0] = line[0] + add_1.encode() + b'\x20'
            line[1] = line[1] + add_2.encode() + b'\x20'
            line[2] = line[2] + add_3.encode() + b'\x20'
            line[3] = line[3] + add_4.encode() + b'\x20'
        else:
            num = ord(st[i]) - 48
            line[0] = line[0] + __big_digit[num][0] + b'\x20'
            line[1] = line[1] + __big_digit[num][1] + b'\x20'
            line[2] = line[2] + __big_digit[num][2] + b'\x20'
            line[3] = line[3] + __big_digit[num][3] + b'\x20'

    disp.write_bytes(line[0], 0)
    disp.write_bytes(line[1], 1)
    disp.write_bytes(line[2], 2)
    disp.write_bytes(line[3], 3)

# ***************************
# Run Program (test)

if __name__ == '__main__':
    import time
    import weh002004a
    disp = weh002004a.WEH002004A()

    try:
        disp.initialize()
        last = datetime.datetime.min
        while True:
            now = datetime.datetime.now()
            if now.second == last.second:
                time.sleep(0.2)
                continue

            last = now
            write_clock_v1(disp, now)
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        disp.dispose()
