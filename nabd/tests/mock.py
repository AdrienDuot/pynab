import asyncio
from nabd.nabio import NabIO
from nabd.ears import Ears
from nabd.leds import Leds
from nabd.sound import Sound

class NabIOMock(NabIO):
  def __init__(self):
    self.played_infos = []
    self.played_sequences = []
    self.called_list = []
    self.left_ear = 0
    self.right_ear = 0

  async def setup_ears(self, left_ear, right_ear):
    self.left_ear = left_ear
    self.right_ear = right_ear
    self.called_list.append('setup_ears({left}, {right})'.format(left=left_ear, right=right_ear))

  async def move_ears(self, left_ear, right_ear):
    self.left_ear = left_ear
    self.right_ear = right_ear
    self.called_list.append('move_ears({left}, {right})'.format(left=left_ear, right=right_ear))

  async def detect_ears_positions(self):
    self.called_list.append('detect_ears_positions()')
    return (self.left_ear, self.right_ear)

  def set_leds(self, left, center, right, nose, bottom):
    self.left_led = left
    self.center_led = center
    self.right_led = right
    self.nose_led = nose
    self.bottom_led = bottom

  def bind_button_event(self, loop, callback):
    self.button_event_cb = {'callback': callback, 'loop': loop}

  def bind_ears_event(self, loop, callback):
    self.ears_event_cb = {'callback': callback, 'loop': loop}

  async def play_info(self, tempo, colors):
    self.played_infos.append({'tempo':tempo, 'colors': colors})
    await asyncio.sleep(1)

  async def play_sequence(self, sequence):
    self.played_sequences.append(sequence)
    await asyncio.sleep(10)

  def cancel(self):
    pass

  def button(self, button_event):
    self.button_event_cb.loop.call_soon_threadsafe(self.button_event_cb.callback, button_event)

  def ears(self, left, right):
    self.ears_event_cb.loop.call_soon_threadsafe(self.ears_event_cb.callback, left, right)

class EarsMock(Ears):
  def __init__(self):
    self.called_list = []
    self.left = 0
    self.right = 0

  def on_move(self, loop, callback):
    self.called_list.append('on_move()')
    self.cb = (loop, callback)

  async def reset_ears(self, target_left, target_right):
    self.called_list.append('reset_ears({l},{r})'.format(l=target_left, r=target_right))

  async def move(self, ear, delta, direction):
    self.called_list.append('move({ear},{delta},{direction})'.format(ear=ear, delta=delta, direction=direction))
    if ear == Ears.LEFT_EAR:
      self.left = (self.left + delta) % Ears.STEPS
    else:
      self.right = (self.right + delta) % Ears.STEPS

  async def detect_positions(self):
    self.called_list.append('detect_positions()')
    return (self.left, self.right)

  async def go(self, ear, position, direction):
    self.called_list.append('go({ear},{position},{direction})'.format(ear=ear, position=position, direction=direction))
    if ear == Ears.LEFT_EAR:
      self.left = position % Ears.STEPS
    else:
      self.right = position % Ears.STEPS

  async def wait_while_running(self):
    self.called_list.append('wait_while_running()')

class LedsMock(Leds):
  def __init__(self):
    self.called_list = []

  def set1(self, led, red, green, blue):
    self.called_list.append('set1({led},{red},{green},{blue})'.format(led=led, red=red, green=green, blue=blue))

  def setall(self, red, green, blue):
    self.called_list.append('setall({red},{green},{blue})'.format(red=red, green=green, blue=blue))

class SoundMock(Sound):
  def __init__(self):
    self.called_list = []

  async def start(self, filename):
    self.called_list.append('start({filename})'.format(filename=filename))

  async def wait_until_done(self):
    self.called_list.append('wait_until_done()')

  async def stop(self):
    self.called_list.append('stop()')
