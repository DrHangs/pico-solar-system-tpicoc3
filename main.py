import display as DISPLAY
PEN = DISPLAY.st7789.color565
import time
import math
import gc
import machine
from micropython import const
import vga1_8x8 as smallfont

class Button:
    def __init__(self, pin):
        self._pin = machine.Pin(pin, machine.Pin.IN)
    def is_pressed(self):
        return self._pin.value() == 0

gc.enable()
backlight = 0.7
plusDays = 0
change = 0

display = DISPLAY.get()
display.rotation(1)
colour = PEN(0,0,0)
button_a = Button(7)
button_b = Button(6)
button_x = Button(12)
button_y = Button(13)
led = machine.Pin(25, machine.Pin.OUT)
led.off()


def circle(xpos0, ypos0, rad):
    global colour
    x = rad - 1
    y = 0
    dx = 1
    dy = 1
    err = dx - (rad << 1)
    while x >= y:
        display.pixel(xpos0 + x, ypos0 + y, colour)
        display.pixel(xpos0 + y, ypos0 + x, colour)
        display.pixel(xpos0 - y, ypos0 + x, colour)
        display.pixel(xpos0 - x, ypos0 + y, colour)
        display.pixel(xpos0 - x, ypos0 - y, colour)
        display.pixel(xpos0 - y, ypos0 - x, colour)
        display.pixel(xpos0 + y, ypos0 - x, colour)
        display.pixel(xpos0 + x, ypos0 - y, colour)
        if err <= 0:
            y += 1
            err += dy
            dy += 2
        if err > 0:
            x -= 1
            dx += 2
            err += dx - (rad << 1)


def check_for_buttons():
    global backlight
    global plusDays
    global change
    if button_x.is_pressed():
        backlight += 0.05
        if backlight > 1:
            backlight = 1
        DISPLAY.brightness(backlight)
    elif button_y.is_pressed():
        backlight -= 0.05
        if backlight < 0:
            backlight = 0
        DISPLAY.brightness(backlight)
    if button_a.is_pressed() and button_b.is_pressed():
        plusDays = 0
        change = 2
        time.sleep(0.2)
    elif button_a.is_pressed():
        plusDays += 86400
        change = 3
        time.sleep(0.05)
    elif button_b.is_pressed():
        plusDays -= 86400
        change = 3
        time.sleep(0.05)


def set_internal_time(utc_time):
    rtc_base_mem = const(0x4005c000)
    atomic_bitmask_set = const(0x2000)
    (year, month, day, hour, minute, second, wday, yday) = time.localtime(utc_time)
    machine.mem32[rtc_base_mem + 4] = (year << 12) | (month << 8) | day
    machine.mem32[rtc_base_mem + 8] = ((hour << 16) | (minute << 8) | second) | (((wday + 1) % 7) << 24)
    machine.mem32[rtc_base_mem + atomic_bitmask_set + 0xc] = 0x10


def main():
    global change
    global colour
    import planets
    from pluto import Pluto
    set_time()

    def draw_planets(HEIGHT, ti):
        PL_CENTER = (68, int(HEIGHT / 2))
        planets_dict = planets.coordinates(ti[0], ti[1], ti[2], ti[3], ti[4])
        # t = time.ticks_ms()
        colour = PEN(255, 255, 0)
        display.fill_circle(int(PL_CENTER[0]), int(PL_CENTER[1]), 4, colour)
        for i, el in enumerate(planets_dict):
            r = 8 * (i + 1) + 2
            colour = PEN(40, 40, 40)
            #circle(PL_CENTER[0], PL_CENTER[1], r)
            display.circle(PL_CENTER[0], PL_CENTER[1], r, colour)
            feta = math.atan2(el[0], el[1])
            coordinates = (r * math.sin(feta), r * math.cos(feta))
            coordinates = (coordinates[0] + PL_CENTER[0], HEIGHT - (coordinates[1] + PL_CENTER[1]))
            for ar in range(0, len(planets.planets_a[i][0]), 5):
                x = planets.planets_a[i][0][ar] - 50 + coordinates[0]
                y = planets.planets_a[i][0][ar + 1] - 50 + coordinates[1]
                if x >= 0 and y >= 0:
                    colour = PEN(planets.planets_a[i][0][ar + 2], planets.planets_a[i][0][ar + 3],
                                    planets.planets_a[i][0][ar + 4])
                    display.pixel(int(x), int(y), colour)
        # print("draw = " + str(time.ticks_diff(t, time.ticks_ms())))

    w = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    m = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    colour = PEN(0, 0, 0)
    display.fill(colour)
    #display.update()
    DISPLAY.brightness(backlight)
    gc.collect()

    HEIGHT = const(135)

    mi = -1
    pl = Pluto(display)

    seconds_absolute = time.time()
    ti = time.localtime(seconds_absolute + plusDays)
    da = ti[2]

    draw_planets(HEIGHT, ti)
    start_int = time.ticks_ms()
    while True:
        ticks_dif = time.ticks_diff(time.ticks_ms(), start_int)
        if ticks_dif >= 1000 or time.time() != seconds_absolute:
            seconds_absolute = time.time()
            ti = time.localtime(seconds_absolute + plusDays)
            start_int = time.ticks_ms()
            ticks_dif = 0
        if change > 0:
            ti = time.localtime(seconds_absolute + plusDays)
        if da != ti[2]:
            da = ti[2]
            change = 3

        if change > 0:
            if change == 1:
                colour = PEN(0, 0, 0)
                display.fill(colour)
                draw_planets(HEIGHT, ti)
                if plusDays > 0:
                    led.on()
                elif plusDays < 0:
                    led.on()
                else:
                    led.off()
                change = 0
            else:
                change -= 1

        colour = PEN(0, 0, 0)
        #display.fill_rect(140, 0, 100, HEIGHT, colour)
        #display.fill_rect(130, 0, 110, 35, colour)
        #display.fill_rect(130, 93, 110, HEIGHT - 93, colour)

        if mi != ti[4]:
            mi = ti[4]
            pl.reset()
        #pl.reset()
        pl.step(ti[5], ticks_dif)
        pl.draw()

        colour = PEN(244, 170, 30)
        display.text(smallfont, "%02d %s %d " % (ti[2], m[ti[1] - 1], ti[0]), 132, 7, colour,PEN(0, 0, 0)) #70, 2, colour)
        colour = PEN(65, 129, 50)
        display.text(smallfont, w[ti[6]], 135, 93, colour,PEN(0, 0, 0)) #99, 2, colour)
        colour = PEN(130, 255, 100)
        display.text(smallfont, "%02d:%02d" % (ti[3], ti[4]), 132, 105, colour,PEN(0, 0, 0))#99, 4, colour)
        #display.update()
        check_for_buttons()
        time.sleep(0.01)


def set_time():
    try:
        import wifi_config
        set_time_c3(wifi_config)
    except ImportError:
        import ds3231
        ds = ds3231.ds3231()
        set_internal_time(ds.read_time())

def set_time_c3(wifi_config):
    from esp32c3 import wifi
    w = wifi()
    w.setmode(1)
    print("Connecting to Wifi...")
    w.connect(wifi_config.ssid, wifi_config.key)

    w.setNTP(interval=16)
    print("wait a few seconds for NTP:")
    for i in reversed(range(1,10)):
        #print(f"{i}", endline='\r')
        time.sleep(1)
    
    for i in range(100):
        #print(f"Get Time, try #{i} of 100", endline='\r')
        if(w.setTime()):
            break
        time.sleep_ms(100)
    print("")
    if(time.time() > 4000000000):
        print("Setting Time manual!")
        from machine import RTC
        RTC().datetime((2022,10,17,1,12,0,0,0))
    w.setmode(0) # Mode 0 -> deactivating Wifi

time.sleep(0.5)
main()