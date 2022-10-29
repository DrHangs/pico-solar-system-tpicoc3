from machine import Pin, PWM
from time import sleep_ms
import st7789
#import vga1_8x8 as smallfont

PIN_DEF = {
    'RESET':  0,
    'CS'   :  5,
    'DC'   :  1,
    'SCK'  :  2,
    'MOSI' :  3,
    'MISO' : 16,
    'POWER': 22,
    'BACKLIGHT': 4
}

# Color definitions
# Also in the st7789 package
# But I felt cute, so I included them :)
BLACK   = 0x0000
BLUE    = 0x001F
RED     = 0xF800
GREEN   = 0x07E0
CYAN    = 0x07FF
MAGENTA = 0xF81F
YELLOW  = 0xFFE0
WHITE   = 0xFFFF

_backlight = None
def brightness(percent):
    global _backlight
    if not _backlight:
        _backlight = PWM(Pin(PIN_DEF['BACKLIGHT'], 1))
        _backlight.freq(1000)
    current = int(_backlight.duty_u16())
    dest = int(65536*percent)
    diff = int((dest-current)/100)
    for duty in range(0,100):
        current += diff
        _backlight.duty_u16(current)
        sleep_ms(1)
    _backlight.duty_u16(dest)

def get():
    backlight=Pin(PIN_DEF['BACKLIGHT'], Pin.OUT) #Hier könnte ihr PWM stehen
    power=Pin(PIN_DEF['POWER'], Pin.OUT, value=1)
    reset=Pin(PIN_DEF['RESET'], Pin.OUT)
    cs = Pin(PIN_DEF['CS'], Pin.OUT)
    dc = Pin(PIN_DEF['DC'], Pin.OUT)
    sck=Pin(PIN_DEF['SCK'], Pin.OUT)
    mosi=Pin(PIN_DEF['MOSI'], Pin.OUT)
    miso=Pin(PIN_DEF['MISO'], Pin.IN)

    from machine import SoftSPI
    spi = SoftSPI(
        baudrate=20000000,
        polarity=1,
        phase=0,
        sck=sck,
        mosi=mosi,
        miso=miso)

    def _hard_reset():
        cs.off()
        reset.on()
        sleep_ms(50)
        reset.off()
        sleep_ms(50)
        reset.on()
        sleep_ms(150)
        cs.on()
    def _spi_write(command=None, data=None):
        """SPI write to the device: commands and data"""
        cs.off()
        if command is not None:
            dc.off()
            spi.write(bytes([command]))
        if data is not None:
            dc.on()
            spi.write(data)
        cs.on()
    def _soft_reset():
        _spi_write(0x01) # ST77XX_SWRESET
        sleep_ms(150)
        _spi_write(0x11) # ST77XX_SLPOUT
    def _pre_init():
        _spi_write(0x3A, bytes([0x50 & 0x77]))
            # ST77XX_COLMOD = const(0x3A)
            # ColorMode_65K = const(0x50)
        sleep_ms(50)
        _spi_write(0x36, bytes([0x10])) 
            # ST7789_MADCTL = const(0x36)
            # ST7789_MADCTL_ML = const(0x10)
        _spi_write(0x21) # ST77XX_INVON = const(0x21)
        sleep_ms(10)
        _spi_write(0x13) # ST77XX_NORON = const(0x13)
        sleep_ms(10)
        _spi_write(0x29) # ST77XX_DISPON = const(0x29)
        sleep_ms(500)
        backlight.on()

    _hard_reset()
    _soft_reset()
    _pre_init()

    tft = st7789.ST7789(
        spi,
        135,
        240,
        reset=reset,
        cs=cs,
        dc=dc,
        backlight=backlight,
        color_order=st7789.RGB, rotation=0, options=0,buffer_size=256)
    tft.init()
    tft.sleep_mode(False)
    tft.on()
    tft.fill(st7789.BLACK)
    return tft

def test_flag(display, loop=False):
    while True:
        display.fill(st7789.BLACK)
        display.fill_rect(0,0,45,240,st7789.BLACK)
        display.fill_rect(45,0,45,240,st7789.RED)
        display.fill_rect(90,0,45,240,st7789.YELLOW)

        sleep_ms(2000)
        
        # UKR
        display.fill(st7789.BLACK)
        display.fill_rect(0,0,67,240,st7789.BLUE)
        display.fill_rect(67,0,68,240,st7789.YELLOW)
        
        sleep_ms(2000)
        
        # SWE
        display.fill(st7789.BLUE)
        display.fill_rect(45,0,45,240,st7789.YELLOW)
        display.fill_rect(0,98,135,44,st7789.YELLOW)
        
        sleep_ms(2000)
        
        # JP
        display.fill(st7789.WHITE)
        display.fill_circle(67,120,40,st7789.RED)
        #tft.fill_rect(45,0,45,240,st7789.YELLOW)
        #tft.fill_rect(0,98,135,44,st7789.YELLOW)
        
        sleep_ms(2000)
        if not loop:
            break
    display.fill(st7789.BLACK)

def test_text(display, loop=False):
    """Fills the screen with Text
    """
    try:
        import vga1_bold_16x32 as font
        import vga1_8x8 as smallfont
        fonts = [font, smallfont]
    except ImportError:
        print("Please install some fonts!")
        display.fill(st7789.RED)
        display.fill(st7789.WHITE)
        display.fill(st7789.RED)
        display.fill(st7789.WHITE)
        return
    from random import choice
    chars = [c for c in "abcdefghijklmnopqrstuvwxyz1234567890,.;:!?()"]
    dh = display.height()
    dw = display.width()
    while True:
        y = 0
        while y < dh:
            f = choice(fonts)
            num_chars = int(dw / f.WIDTH) + 1
            text = "".join(choice(chars) for i in range(num_chars))
            display.text(
                f, text, 0, y, st7789.GREEN, st7789.BLACK
            )

            y += f.HEIGHT + 1
            sleep_ms(10)
        sleep_ms(3000)
        display.fill(0)
        if not loop:
            break