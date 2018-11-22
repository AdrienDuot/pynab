import sys, asyncio, json, re
from nabcommon import nabservice
from mastodon import Mastodon, StreamListener, MastodonError

class NabMastodond(nabservice.NabService,asyncio.Protocol,StreamListener):
  DAEMON_PIDFILE = '/var/run/nabmastodond.pid'

  RETRY_DELAY = 15 * 60 # Retry to reconnect every 15 minutes.
  NABPAIRING_MESSAGE_RE = 'NabPairing (?P<cmd>Proposal|Acceptation|Rejection|Divorce|Ears (?P<left>[0-9]+) (?P<right>[0-9]+)) - (?:<a href=")?https://github.com/nabaztag2018/pynab'
  PROTOCOL_MESSAGES = { \
    'proposal': 'Would you accept to be my spouse? (NabPairing Proposal - https://github.com/nabaztag2018/pynab)', \
    'acceptation': 'Oh yes, I do accept to be your spouse (NabPairing Acceptation - https://github.com/nabaztag2018/pynab)', \
    'rejection': 'Sorry, I cannot be your spouse right now (NabPairing Rejection - https://github.com/nabaztag2018/pynab)', \
    'divorce': 'I think we should split. Can we skip the lawyers? (NabPairing Divorce - https://github.com/nabaztag2018/pynab)', \
    'ears': 'Let\'s dance (NabPairing Ears {left} {right} - https://github.com/nabaztag2018/pynab)', \
  }

  def __init__(self):
    super().__init__()
    self.mastodon_client = None
    self.mastodon_stream_handle = None
    self.current_access_token = None

  def __config(self):
    from . import models
    return models.Config.load()

  async def reload_config(self):
    self.setup_streaming()

  def close_streaming(self):
    if self.mastodon_stream_handle:
      self.mastodon_stream_handle.close()
    self.current_access_token = None
    self.mastodon_stream_handle = None
    self.mastodon_client = None

  def on_update(self, status):
    asyncio.run_coroutine_threadsafe(self.loop_update(self.mastodon_client, status), self.loop)

  def on_notification(self, notification):
    if 'type' in notification and notification['type'] == 'mention' and 'status' in notification:
      asyncio.run_coroutine_threadsafe(self.loop_update(self.mastodon_client, notification['status']), self.loop)

  async def loop_update(self, mastodon_client, status):
    self.do_update(mastodon_client, status)

  def do_update(self, mastodon_client, status):
    config = self.__config()
    (status_id, status_date) = self.process_status(config, mastodon_client, status)
    if status_id != None and (config.last_processed_status_id == None or status_id > config.last_processed_status_id):
      config.last_processed_status_id = status_id
    if status_date != None and status_date > config.last_processed_status_date:
      config.last_processed_status_date = status_date
    config.save()

  def process_timeline(self, mastodon_client, timeline):
    config = self.__config()
    max_date = config.last_processed_status_date
    max_id = config.last_processed_status_id
    for status in timeline:
      (status_id, status_date) = self.process_status(config, mastodon_client, status)
      if status_id != None and (max_id == None or status_id > max_id):
        max_id = status_id
      if status_date != None and max_date > status_date:
        max_date = status_date
    config.last_processed_status_date = max_date
    config.last_processed_status_id = max_id
    config.save()

  def process_status(self, config, mastodon_client, status):
    try:
      status_id = status['id']
      status_date = status['created_at']
      skip = False
      if config.last_processed_status_id != None:
        skip = status_id <= config.last_processed_status_id
      skip = skip or config.last_processed_status_date > status_date
      if not skip:
        self.do_process_status(config, mastodon_client, status)
      return (status_id, status_date)
    except KeyError as e:
      print('Unexpected status from mastodon, missing slot {e}\n{status}'.format(status=status))
      return (None, None)

  def do_process_status(self, config, mastodon_client, status):
    if status['visibility'] == 'direct':
      sender_account = status['account']
      sender_url = sender_account['url']
      if sender_url != 'https://' + config.instance + '/@' + config.username:
        sender = sender_account['acct']
        if '@' not in sender:
          sender = sender + '@' + config.instance
        if 'display_name' in sender_account:
          sender_name = sender_account['display_name']
        else:
          sender_name = sender_account['username']
        type, params = self.decode_dm(status)
        if type != None:
          self.transition_state(config, mastodon_client, sender, sender_name, type, params, status['created_at'])

  def transition_state(self, config, mastodon_client, sender, sender_name, type, params, message_date):
    current_state = config.spouse_pairing_state
    matching = config.spouse_handle != None and config.spouse_handle == sender
    if current_state == None:
      if type == 'proposal':
        config.spouse_handle = sender
        config.spouse_pairing_state = 'waiting_approval'
        config.spouse_pairing_date = message_date
        self.play_message('proposal', sender_name)
      elif type == 'acceptation' or type == 'ears':
        NabMastodond.send_dm(mastodon_client, sender, 'divorce')
      # else ignore message
    elif current_state == 'proposed':
      if matching and type == 'rejection':
        config.spouse_handle = None
        config.spouse_pairing_state = None
        config.spouse_pairing_date = message_date
        self.play_message('rejection', sender_name)
      elif matching and type == 'divorce':
        config.spouse_handle = None
        config.spouse_pairing_state = None
        config.spouse_pairing_date = message_date
        self.play_message('rejection', sender_name)
      elif matching and type == 'acceptation':
        config.spouse_handle = sender
        config.spouse_pairing_state = 'married'
        config.spouse_pairing_date = message_date
        self.send_start_listening_to_ears()
        self.play_message('wedding', sender_name)
      elif matching and type == 'proposal':
        NabMastodond.send_dm(mastodon_client, sender, 'acceptation')
        config.spouse_handle = sender
        config.spouse_pairing_state = 'married'
        config.spouse_pairing_date = message_date
        self.send_start_listening_to_ears()
        self.play_message('wedding', sender_name)
      elif not matching and (type == 'acceptation' or type == 'ears'):
        NabMastodond.send_dm(mastodon_client, sender, 'divorce')
      elif not matching and type == 'proposal':
        NabMastodond.send_dm(mastodon_client, sender, 'rejection')
      # else ignore
    elif current_state == 'waiting_approval':
      if matching and type == 'rejection':
        config.spouse_handle = None
        config.spouse_pairing_state = None
        config.spouse_pairing_date = message_date
      elif matching and type == 'divorce':
        config.spouse_handle = None
        config.spouse_pairing_state = None
        config.spouse_pairing_date = message_date
        self.play_message('divorce', sender_name)
      elif matching and type == 'acceptation':
        NabMastodond.send_dm(mastodon_client, sender, 'divorce')
        config.spouse_handle = None
        config.spouse_pairing_state = None
        config.spouse_pairing_date = message_date
      elif type == 'proposal':
        if not matching:
          NabMastodond.send_dm(mastodon_client, config.spouse_handle, 'rejection')
          config.spouse_handle = sender
        config.spouse_pairing_date = message_date
        self.play_message('proposal', sender_name)
      elif matching and type == 'acceptation':
        NabMastodond.send_dm(mastodon_client, sender, 'divorce')
      elif not matching and (type == 'acceptation' or type == 'ears'):
        NabMastodond.send_dm(mastodon_client, sender, 'divorce')
      # else ignore
    elif current_state == 'married':
      if matching and type == 'rejection':
        config.spouse_handle = None
        config.spouse_pairing_state = None
        config.spouse_pairing_date = message_date
        self.send_stop_listening_to_ears()
        self.play_message('divorce', sender_name)
      elif matching and type == 'divorce':
        config.spouse_handle = None
        config.spouse_pairing_state = None
        config.spouse_pairing_date = message_date
        self.send_stop_listening_to_ears()
        self.play_message('divorce', sender_name)
      elif matching and type == 'acceptation':
        config.spouse_pairing_date = message_date
      elif matching and type == 'proposal':
        NabMastodond.send_dm(mastodon_client, sender, 'acceptation')
        config.spouse_pairing_date = message_date
      elif not matching and (type == 'acceptation' or type == 'ears'):
        NabMastodond.send_dm(mastodon_client, sender, 'divorce')
      elif not matching and type == 'proposal':
        NabMastodond.send_dm(mastodon_client, sender, 'rejection')
      elif matching and type == 'ears':
        self.play_message('ears', sender_name)
        config.spouse_left_ear_position = params['left']
        config.spouse_right_ear_position = params['right']
        config.spouse_pairing_date = message_date
        self.send_ears(params['left'], params['right'])
      # else ignore

  def play_message(self, message, sender_name):
    """
    Play pairing protocol message
    """
    # TODO: choregraphies per message & tts for sender_name
    if message == 'ears':
      packet = '{"type":"command","sequence":[{"audio":["nabmastodond/communion.wav"]}]}\r\n'
    else:
      packet = '{"type":"command","sequence":[{"audio":[]}]}\r\n'
    self.writer.write(packet.encode('utf8'))

  def send_start_listening_to_ears(self):
      packet = '{"type":"mode","mode":"idle","events":["ears"]}\r\n'
      self.writer.write(packet.encode('utf8'))

  def send_stop_listening_to_ears(self):
      packet = '{"type":"mode","mode":"idle","events":[]}\r\n'
      self.writer.write(packet.encode('utf8'))

  def send_ears(self, left_ear, right_ear):
      packet = '{{"type":"ears","left":{left_ear},"right":{right_ear}}}\r\n'.format(left_ear=left_ear, right_ear=right_ear)
      self.writer.write(packet.encode('utf8'))

  @staticmethod
  def send_dm(mastodon_client, target, message, params = {}):
    """
    Send a DM following pairing protocol
    """
    message_str = NabMastodond.PROTOCOL_MESSAGES[message].format(**params)
    status = '@' + target + ' ' + message_str
    return mastodon_client.status_post(status, visibility = 'direct')

  def decode_dm(self, status):
    m = re.search(NabMastodond.NABPAIRING_MESSAGE_RE, status['content'])
    if m:
      if 'Ears' in m.group('cmd'):
        return 'ears', {'left': int(m.group('left')), 'right': int(m.group('right'))}
      return m.group('cmd').lower(), None
    return None, None

  def setup_streaming(self):
    config = self.__config()
    if config.access_token == None:
      self.close_streaming()
    else:
      if config.access_token != self.current_access_token:
        self.close_streaming()
      if self.mastodon_client == None:
        try:
          self.mastodon_client = Mastodon(client_id = config.client_id, \
            client_secret = config.client_secret, \
            access_token = config.access_token,
            api_base_url = 'https://' + config.instance)
          self.current_access_token = config.access_token
        except MastodonUnauthorizedError:
          self.current_access_token = None
          config.access_token = None
          config.save()
        except MastodonError as e:
          print('Unexpected mastodon error: {e}'.format(e=e))
          self.loop.call_later(NabMastodond.RETRY_DELAY, self.setup_streaming)
      if self.mastodon_client != None and self.mastodon_stream_handle == None:
        self.mastodon_stream_handle = self.mastodon_client.stream_user(self, run_async=True, reconnect_async=True)
      if self.mastodon_client != None:
        timeline = self.mastodon_client.timeline(timeline="direct", since_id=config.last_processed_status_id)
        self.process_timeline(self.mastodon_client, timeline)

  async def process_nabd_packet(self, packet):
    if packet['type'] == 'ears_event':
      config = self.__config()
      if config.spouse_pairing_state == 'married':
        if self.mastodon_client:
          self.play_message('ears', config.spouse_handle)
          config.spouse_left_ear_position = packet['left']
          config.spouse_right_ear_position = packet['right']
          config.save()
          NabMastodond.send_dm(self.mastodon_client, config.spouse_handle, 'ears', {'left': packet['left'], 'right': packet['right']})

  def run(self):
    super().connect()
    self.setup_streaming()
    self.loop = asyncio.get_event_loop()
    config = self.__config()
    if config.spouse_pairing_state == 'married':
      self.send_start_listening_to_ears()
      if config.spouse_left_ear_position != None:
        self.send_ears(config.spouse_left_ear_position, config.spouse_right_ear_position)
    try:
      self.loop.run_forever()
    except KeyboardInterrupt:
      pass
    finally:
      self.running = False  # signal to exit
      self.writer.close()
      self.close_streaming()
      if sys.version_info >= (3,7):
        tasks = asyncio.all_tasks(self.loop)
      else:
        tasks = asyncio.Task.all_tasks(self.loop)
      for t in [t for t in tasks if not (t.done() or t.cancelled())]:
        self.loop.run_until_complete(t)    # give canceled tasks the last chance to run
      self.loop.close()

if __name__ == '__main__':
  NabMastodond.main(sys.argv[1:])
