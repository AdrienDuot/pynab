from rpi_ws281x import Adafruit_NeoPixel, Color
from .leds import Leds

class LedsNeoPixel(Leds):
  LED_COUNT      = 5      # Number of LED pixels.
  LED_PIN        = 13      # GPIO pin connected to the pixels (18 uses PWM!).
  LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
  LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
  LED_BRIGHTNESS = 200     # Set to 0 for darkest and 255 for brightest
  LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
  LED_CHANNEL    = 1       # set to '1' for GPIOs 13, 19, 41, 45 or 53

  def __init__(self):
    self.strip = Adafruit_NeoPixel(
      LedsNeoPixel.LED_COUNT,
      LedsNeoPixel.LED_PIN,
      LedsNeoPixel.LED_FREQ_HZ,
      LedsNeoPixel.LED_DMA,
      LedsNeoPixel.LED_INVERT,
      LedsNeoPixel.LED_BRIGHTNESS,
      LedsNeoPixel.LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    self.strip.begin()

  def set1(self, led, red, green, blue):
    self.strip.setPixelColor(led, Color(red, green, blue))
    self.strip.show()

  def setall(self, red, green, blue):
    for led in range(LedsNeoPixel.LED_COUNT):
      self.strip.setPixelColor(led, Color(red, green, blue))
    self.strip.show()
