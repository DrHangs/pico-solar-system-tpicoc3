
import utime
from machine import UART, Pin, RTC

CMDS = {
    'VERSION': b'AT+GMR',
    'TEST_AT': b'AT',
    'GETMODE': b'AT+CWMODE?',
    'SETMODE': b'AT+CWMODE=',
    'SCAN': b'AT+CWLAP',
    'GETTEMP': b'AT+SYSTEMP?',
    'SETSLEEP': b'AT+GSLP=',
    'CONNECT': b'AT+CWJAP',
    'DISCONNECT': b'AT+CWQAP',
    'SETNTP': b'AT+CIPSNTPCFG',
    'GETNTP': b'AT+CIPSNTPTIME?',
    'NTPINTERVAL': b'AT+CIPSNTPINTV'
}

class wifi:
    def __init__(self, uart=None):
        self.config(uart)
        for i in range(100):
            if self._test():
                break
            utime.sleep_ms(50)
        # Final Test, throw error if not working!
        assert(self._get('TEST_AT') == b'AT\r\n\r\nOK\r\n')
        
    def _test(self):
        try:
            assert(self._get('TEST_AT') == b'AT\r\n\r\nOK\r\n')
            return True
        except AssertionError:
            return False
    def config(self, uart=None):
        if(uart):
            self.uart = uart
        else:
            self.uart = UART(
                1, 
                baudrate=115200,
                tx=Pin(8), 
                rx=Pin(9), 
                cts=Pin(10), 
                rts=Pin(11),
                txbuf=1024,
                rxbuf=1024)
    def _get(self, cmd):
        timeout = 500 #timeout in ms
        if(cmd in CMDS):
            prep = CMDS[cmd] + '\r\n'
            self.uart.write(prep)
        else:
            self.uart.write(cmd)
        timeout_start = utime.ticks_ms()
        while self.uart.any() == 0:
            utime.sleep_ms(2)
            if(utime.ticks_ms() - timeout_start > timeout):
                return "TIMEOUT at AT"
        utime.sleep_ms(10)
        return self.uart.read()
    def _set(self, cmd, arg):
        if(cmd in CMDS):
            prep = CMDS[cmd] + bytes(str(arg),'UTF-8') +  bytes(str('\r\n'),'UTF-8')
            return self._get(prep)
        else:
            return self._get(cmd + arg + '\r\n')
    
    def setmode(self, mode):
        """
        – 0: Null mode. Wi-Fi RF will be disabled.
        – 1: Station mode.
        – 2: SoftAP mode.
        – 3: SoftAP+Station mode"""
        self._set('SETMODE', mode)
    def mode(self):
        resp = self._get('GETMODE')
        print(resp.decode())

    def connect(self, ssid, pwd):
        return self._set('CONNECT', 
            b'="' + ssid + b'","' + pwd + b'"')
    def disconnect(self):
        return self._get('DISCONNECT')

    def scan(self):
        out = self._get('SCAN')
        utime.sleep_ms(500)
        while not out.endswith(b'OK\r\n'):
            if b'ERROR' in out:
                break
            if(self.uart.any()):
                out += self.uart.read()
            utime.sleep_ms(10)
        print(out.decode())

    def test(self):
        print(self._get('TEST_AT').decode())
    def version(self):
        print(self._get('VERSION').decode())
    def temp(self):
        print(self._get('GETTEMP').decode())
    def sleep(self, millis=3600000):
        self._set('SETSLEEP', millis)
    
    def setNTP(self, interval=20):
        self._set('SETNTP', '=1,2,"0.pool.ntp.org","time.google.com"')
        self._set('NTPINTERVAL', interval)

    def setTime(self):
        resp = self._get('GETNTP')
        if(b'ERROR' in resp):
            return False
        assert(len(resp) > 32)
        ind = resp.index(b'+CIPSNTPTIME:')
        resp = resp[ind:].decode()
        # z.B.: b'+CIPSNTPTIME:Tue Oct 18 23:36:26 2022'
        assert(len(resp) > 32)
        if(int(resp[33:37]) == 1970): return False;
        timelist = [
            int(resp[33:37]),
            Time.months[resp[17:20]],
            int(resp[21:23]),
            Time.days.index(resp[13:16])+1,
            int(resp[24:26]),
            int(resp[27:29]),
            int(resp[30:32]),
            0
        ]
        Time.setRTC(timelist)
        return True

class Time:
    months = {
        "Jan": 1, 
        "Feb": 2, 
        "Mar": 3, 
        "Apr": 4, 
        "May": 5, 
        "Jun": 6, 
        "Jul": 7, 
        "Aug": 8, 
        "Sep": 9, 
        "Oct": 10, 
        "Nov": 11,
        "Dec": 12
    }
    days = [
        "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"
    ]
    def setRTC(timelist):
        rtc = RTC()
        rtc.datetime(tuple(timelist))