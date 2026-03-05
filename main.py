import os
import threading
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, BooleanProperty
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock, mainthread

Window.clearcolor = (0.118, 0.118, 0.118, 1)

store = JsonStore('settings.json')

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        title = Label(text='[b]Settings[/b]', markup=True, font_size=24, color=(1,1,1,1))
        layout.add_widget(title)
        
        url_label = Label(text='Server URL:', color=(1,1,1,1))
        layout.add_widget(url_label)
        
        self.url_input = TextInput(multiline=False, hint_text='https://xxx.ngrok.io', size_hint_y=None, height=50, font_size=16)
        self.url_input.text = store.get('settings').get('url', '') if store.exists('settings') else ''
        layout.add_widget(self.url_input)
        
        password_label = Label(text='Password (optional):', color=(1,1,1,1))
        layout.add_widget(password_label)
        
        self.password_input = TextInput(multiline=False, password=True, hint_text='Password', size_hint_y=None, height=50, font_size=16)
        self.password_input.text = store.get('settings').get('password', '') if store.exists('settings') else ''
        layout.add_widget(self.password_input)
        
        save_btn = Button(text='Save & Connect', size_hint_y=None, height=60, background_color=(0.157, 0.655, 0.271, 1), color=(1,1,1,1), background_normal='')
        save_btn.bind(on_press=self.save_settings)
        layout.add_widget(save_btn)
        
        self.status_label = Label(text='', color=(0,1,0,1), font_size=14)
        layout.add_widget(self.status_label)
        layout.add_widget(Widget())
        self.add_widget(layout)
    
    def save_settings(self, instance):
        url = self.url_input.text.strip()
        password = self.password_input.text.strip()
        if not url:
            self.status_label.text = 'Enter URL!'
            self.status_label.color = (1,0,0,1)
            return
        store.put('settings', url=url, password=password)
        app = App.get_running_app()
        app.server_url = url
        app.password = password
        self.status_label.text = 'Connecting...'
        self.status_label.color = (0,1,0,1)
        Clock.schedule_once(lambda dt: self.test_connection(url, password), 0.1)
    
    def test_connection(self, url, password):
        try:
            headers = {}
            if password:
                headers["Authorization"] = f"Bearer {password}"
            response = requests.get(f'{url}/api/bots/status', headers=headers, timeout=10)
            if response.status_code == 200:
                self.status_label.text = 'Connected!'
                app = App.get_running_app()
                app.root.current = 'bots'
                app.load_bots()
            else:
                self.status_label.text = f'Error: {response.status_code}'
                self.status_label.color = (1,0,0,1)
        except Exception as e:
            self.status_label.text = f'Error: {str(e)[:30]}'
            self.status_label.color = (1,0,0,1)

class BotCard(BoxLayout):
    bot_name = StringProperty()
    is_running = BooleanProperty(False)
    
    def __init__(self, bot_name, **kwargs):
        super().__init__(**kwargs)
        self.bot_name = bot_name
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 350
        self.padding = 10
        self.spacing = 10
        
        title = Label(text=f'[b]{bot_name}[/b]', markup=True, size_hint_y=None, height=40, font_size=18, color=(1,1,1,1))
        self.add_widget(title)
        
        btn_layout = GridLayout(cols=3, size_hint_y=None, height=60, spacing=10)
        
        self.start_btn = Button(text='Start', background_color=(0.157, 0.655, 0.271, 1), color=(1,1,1,1), background_normal='')
        self.start_btn.bind(on_press=lambda x: self.send_command('start'))
        
        self.restart_btn = Button(text='Restart', background_color=(1, 0.757, 0.027, 1), color=(1,1,1,1), background_normal='')
        self.restart_btn.bind(on_press=lambda x: self.send_command('restart'))
        
        self.stop_btn = Button(text='Stop', background_color=(0.863, 0.208, 0.271, 1), color=(1,1,1,1), background_normal='')
        self.stop_btn.bind(on_press=lambda x: self.send_command('stop'))
        
        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.restart_btn)
        btn_layout.add_widget(self.stop_btn)
        self.add_widget(btn_layout)
        
        self.log_label = Label(text='', size_hint_y=None, height=200, font_size=11, color=(1,1,1,1), halign='left', valign='top')
        self.add_widget(self.log_label)
        self.update_buttons(False)
    
    def update_buttons(self, running):
        self.is_running = running
        self.start_btn.disabled = running
        self.restart_btn.disabled = not running
        self.stop_btn.disabled = not running
    
    def append_log(self, message):
        self.log_label.text += message + '\n'
    
    def send_command(self, action):
        app = App.get_running_app()
        try:
            headers = {}
            if app.password:
                headers["Authorization"] = f"Bearer {app.password}"
            response = requests.post(f'{app.server_url}/api/bot/{self.bot_name}/{action}', headers=headers, timeout=10)
            if response.status_code == 200:
                self.append_log(f'Command {action} sent')
            else:
                self.append_log(f'Error: {response.status_code}')
        except Exception as e:
            self.append_log(f'Error: {str(e)[:50]}')

class BotsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bot_cards = {}
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        header = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.status_label = Label(text='Connected', color=(0,1,0,1), font_size=14)
        header.add_widget(self.status_label)
        
        settings_btn = Button(text='Settings', size_hint_x=None, width=120, background_color=(0.3, 0.3, 0.3, 1), color=(1,1,1,1), background_normal='')
        settings_btn.bind(on_press=self.go_to_settings)
        header.add_widget(settings_btn)
        layout.add_widget(header)
        
        scroll = ScrollView()
        self.bots_layout = BoxLayout(orientation='vertical', spacing=15, size_hint_y=None)
        self.bots_layout.bind(minimum_height=self.bots_layout.setter('height'))
        scroll.add_widget(self.bots_layout)
        layout.add_widget(scroll)
        self.add_widget(layout)
    
    def go_to_settings(self, instance):
        App.get_running_app().root.current = 'settings'
    
    def load_bots(self):
        app = App.get_running_app()
        for child in list(self.bots_layout.children):
            self.bots_layout.remove_widget(child)
        self.bot_cards.clear()
        try:
            headers = {}
            if app.password:
                headers["Authorization"] = f"Bearer {app.password}"
            response = requests.get(f'{app.server_url}/api/bots/status', headers=headers, timeout=10)
            if response.status_code == 200:
                bots_data = response.json()
                for bot_name in bots_data.keys():
                    card = BotCard(bot_name)
                    self.bot_cards[bot_name] = card
                    self.bots_layout.add_widget(card)
                    is_running = bots_data[bot_name].get('running', False)
                    card.update_buttons(is_running)
                self.start_sse_listener()
        except Exception as e:
            self.status_label.text = f'Error: {str(e)[:30]}'
            self.status_label.color = (1,0,0,1)
    
    def start_sse_listener(self):
        app = App.get_running_app()
        def listen():
            try:
                headers = {}
                if app.password:
                    headers["Authorization"] = f"Bearer {app.password}"
                url = f'{app.server_url}/stream/bots'
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str:
                                try:
                                    import json
                                    data = json.loads(data_str)
                                    message = data.get('message', '')
                                    for bot_name, card in self.bot_cards.items():
                                        if bot_name in message or message:
                                            Clock.schedule_once(lambda dt, m=message, bn=bot_name: self.update_log(bn, m))
                                except:
                                    pass
            except:
                pass
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
    
    @mainthread
    def update_log(self, bot_name, message):
        if bot_name in self.bot_cards:
            self.bot_cards[bot_name].append_log(message)
            if 'started' in message.lower() or 'started' in message.lower():
                self.bot_cards[bot_name].update_buttons(True)
            elif 'stopped' in message.lower() or 'stopped' in message.lower():
                self.bot_cards[bot_name].update_buttons(False)

class BotManagerApp(App):
    server_url = StringProperty('')
    password = StringProperty('')
    
    def build(self):
        sm = ScreenManager()
        settings_screen = SettingsScreen(name='settings')
        bots_screen = BotsScreen(name='bots')
        sm.add_widget(settings_screen)
        sm.add_widget(bots_screen)
        if store.exists('settings'):
            settings = store.get('settings')
            self.server_url = settings.get('url', '')
            self.password = settings.get('password', '')
            if self.server_url:
                sm.current = 'bots'
                Clock.schedule_once(lambda dt: bots_screen.load_bots(), 1)
        return sm

if __name__ == '__main__':
    BotManagerApp().run()
