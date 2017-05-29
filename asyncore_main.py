import socket
import asyncore
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager

Builder.load_string("""
#:import C kivy.utils.get_color_from_hex
#:import RiseInTransition kivy.uix.screenmanager.RiseInTransition

<BoxLayout>:
    padding: 10
    spacing: 10

<GridLayout>:
    rows: 2
    cols: 2
    spacing: 10
    row_default_height: 90
    row_force_default: True

<Label>:
    font_size: 25

<Button>:
    font_size: 30
    height: 90
    size_hint: (1, None)
    background_normal: 'button_normal.png'
    background_down: 'button_down.png'
    border: (2, 2, 2, 2)

<TextInput>:
    font_size: 30
    multiline: False
    padding: [10, 0.5 * (self.height - self.line_height)]

<ScrollView>:
    canvas.before:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

<ChatLabel@Label>:
    color: C('#101010')
    text_size: (self.width, None)
    halign: 'left'
    valign: 'top'
    padding: (-10, 0)  # fixed in Kivy 1.8.1
    size_hint: (1, None)
    height: self.texture_size[1]
    markup: True


<RootWidget>:
    transition: RiseInTransition()

    Screen:
        name: 'login'

        BoxLayout:
            orientation: 'vertical'

            GridLayout:
                Label:
                    text: 'Server:'
                    size_hint: (0.4, 1)

                TextInput:
                    id: server
                    text: '127.0.0.1'

                Label:
                    text: 'Nickname:'
                    size_hint: (0.4, 1)

                TextInput:
                    id: nickname
                    text: 'Kivy'

            Button:
                text: 'Connect'
                on_press: app.connect()

    Screen:
        name: 'chatroom'

        BoxLayout:
            orientation: 'vertical'

            Button:
                text: 'Disconnect'
                on_press: app.disconnect()
                background_normal: 'red_button_normal.png'
                background_down: 'red_button_down.png'

            ScrollView:
                ChatLabel:
                    id: chat_logs
                    text: ''

            BoxLayout:
                height: 90
                orientation: 'horizontal'
                padding: 0
                size_hint: (1, None)

                TextInput:
                    id: message
                    on_text_validate: app.send_msg()

                Button:
                    text: 'Send'
                    on_press: app.send_msg()
                    size_hint: (0.3, 1)
""")


def esc_markup(msg):
    return (msg.replace('&', '&amp;')
            .replace('[', '&bl;')
            .replace(']', '&br;'))


class MySocketClient(asyncore.dispatcher):
    
    def __init__(self, server_address, app):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(server_address)
        self.app = app

    def handle_read(self):
        data = self.recv(8192)
        if data:
            text = data.decode('utf-8', 'ignore')
            nickname = ''
            msg = ''
            for num, i in enumerate(text.split(':'), start=0):
                if num == 0:
                    nickname = i
                else:
                    msg += i
            self.app.root.ids.chat_logs.text += (
            '\t[b][color=2980b9]{}:[/color][/b] {}\n'.format(nickname, esc_markup(msg))
            )


class RootWidget(ScreenManager):
    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)


class ChatApp(App):

    def build(self):
        return RootWidget()
    
    def connect(self):
        host = self.root.ids.server.text
        self.nick = self.root.ids.nickname.text

        self.client = MySocketClient((host, 5920), self)
        threading.Thread(target=asyncore.loop).start()
        
        print('-- connecting to ' + host)

        self.root.current = 'chatroom'

    def disconnect(self):
        self.client.close()
        print('-- disconnecting')
        
        self.root.current = 'login'
        self.root.ids.chat_logs.text = ''

    def send_msg(self):
        msg = self.root.ids.message.text
        self.client.send('{0}:{1}'.format(self.nick, msg).encode('utf-8', 'ignore'))
        self.root.ids.chat_logs.text += (
            '\t[b][color=2980b9]{}:[/color][/b] {}\n'
                .format(self.nick, esc_markup(msg)))
        self.root.ids.message.text = ''

    def on_stop(self):
        asyncore.close()
        exit()


if __name__ == '__main__':
    Config.set('graphics', 'width', '600')
    Config.set('graphics', 'height', '900')

    ChatApp().run()
