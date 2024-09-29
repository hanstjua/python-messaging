from datetime import datetime
import functools
import logging
from time import sleep
from flask import Flask, request
from importlib import import_module as imp, reload as rel

from flask_sock import Sock, ConnectionClosed

from simple_websocket import Server

from database import Database
from models import GroupChat, Message, PrivateMessage, User

from chope import *


def catch_exception(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception('Unhandled error.')
            raise

    return wrapped


class WebApp(Flask):
    def __init__(self):
        super().__init__(__name__)

        self.__database = Database()
        self.__sock = Sock(self)
        self.__websockets = {}

        self.__sock.route('/ws/<string:username>')(self.ws)

        self.get('/')(self.register)
        self.get('/login')(self.login)
        self.post('/login')(self.post_login)
        self.put('/logout')(self.put_logout)
        self.get('/user/<string:handle>/<string:name>')(self.create_user)
        self.post('/user')(self.post_user)
        self.delete('/user/<string:username>')(self.delete_user)
        self.get('/users')(self.get_users)

        self.get('/private-chat')(self.get_private_chat)
        self.post('/private-chat')(self.post_private_chat)

        self.post('/private-message')(self.post_private_message)

        self.get('/group-chat')(self.get_group_chat)
        self.post('/group-chat')(self.post_group_chat)
        self.post('/view-group-chat')(self.post_view_group_chat)

        self.post('/group-message')(self.post_group_message)

        self.post('/main')(self.main)

        self.post('/add-group-modal-reset')(self.post_add_group_modal_reset)
        self.post('/add-group-user-validation')(self.add_group_create_validation)
        self.post('/add-group-name-validation')(self.add_group_create_validation)
        self.post('/add-group-create-validation')(self.add_group_create_validation)
        self.post('/add-private-user-validation')(self.add_private_username_validation)
        self.post('/group-modal')(self.group_modal)

        self.post('/login/username-validation')(self.post_login_username_validation)
        self.post('/register/username-validation')(self.post_register_username_validation)
        self.post('/register/display-name-validation')(self.post_register_display_name_validation)

    def ws(self, ws: Server, username: str):
        if username in self.__websockets:
            self.__websockets[username].append(ws)
        else:
            self.__websockets[username] = [ws]

        print(f'{username} connected a websocket. (count: {len(self.__websockets[username])})')

        while True:
            try:
                ws.receive(0)
                sleep(1)
            except ConnectionClosed:
                if ws in self.__websockets[username]:
                    self.__websockets[username].remove(ws)

                print(f'A {username} websocket is closed. (count: {len(self.__websockets[username])})')

                break

    @catch_exception
    def post_login_username_validation(self):
        if self.__database.get_user_by_handle(request.form.get('username', '')) is not None:
            validation = a('#user-validation.green-text')[
                i('.material-icons.tiny')['check'],
                'User exists.'
            ].render()
            login = a("#login-button.waves-effect.waves-light.btn",
                        hx_post='/login',
                        hx_target='#main-content',
                        hx_swap_oob='outerHTML')[
                'Login',
                i('.material-icons.right')['send']
            ].render()
            
            return ''.join((validation, login))
        else:
            validation = a('#user-validation.red-text')[
                i('.material-icons.tiny')['close'],
                'User not found.'
            ].render()
            login = a("#login-button.waves-effect.waves-light.btn.disabled",
                        hx_post='/login',
                        hx_target='#main-content',
                        hx_swap_oob='outerHTML')[
                'Login',
                i('.material-icons.right')['send']
            ].render()
            
            return ''.join((validation, login))

    @catch_exception
    def post_register_username_validation(self):
        username = request.form.get('username', '')
        display = request.form.get('display-name', '')

        is_username_valid = False
        is_display_name_valid = bool(display)
        if self.__database.get_user_by_handle(username) is not None:
            validation = a('#username-validation.red-text')[
                i('.material-icons.tiny')['close'],
                'User already exists.'
            ].render()
        elif not username:
            validation = a('#username-validation.red-text')[
                i('.material-icons.tiny')['close'],
                'Username cannot be empty.'
            ].render()
        else:
            validation = a('#username-validation.green-text')[
                i('.material-icons.tiny')['check'],
                'Username available.'
            ].render()
            is_username_valid = True
        
        if is_username_valid and is_display_name_valid:
            register = a("#register-button.waves-effect.waves-light.btn",
                        hx_post='/user',
                        hx_target='#main-content',
                        hx_swap_oob='outerHTML')[
                'Register',
                i('.material-icons.right')['send']
            ].render()
        else:
            register = a("#register-button.waves-effect.waves-light.btn.disabled",
                        hx_post='/user',
                        hx_target='#main-content',
                        hx_swap_oob='outerHTML')[
                'Register',
                i('.material-icons.right')['send']
            ].render()

        return ''.join((validation, register))
    
    @catch_exception
    def post_register_display_name_validation(self):
        username = request.form.get('username', '')
        display = request.form.get('display-name', '')

        is_username_valid = username and self.__database.get_user_by_handle(username) is None
        is_display_name_valid = bool(display)
        if not is_display_name_valid:
            validation = a('#user-validation.red-text')[
                i('.material-icons.tiny')['close'],
                'Display name cannot be empty.'
            ].render()
        else:
            validation = a('#user-validation.green-text')[
                i('.material-icons.tiny')['check'],
                'Display name is valid.'
            ].render()
        
        if is_username_valid and is_display_name_valid:
            register = a("#register-button.waves-effect.waves-light.btn",
                        hx_post='/user',
                        hx_target='#main-content',
                        hx_swap_oob='outerHTML')[
                'Register',
                i('.material-icons.right')['send']
            ].render()
        else:
            register = a("#register-button.waves-effect.waves-light.btn.disabled",
                        hx_post='/user',
                        hx_target='#main-content',
                        hx_swap_oob='outerHTML')[
                'Register',
                i('.material-icons.right')['send']
            ].render()

        return ''.join((validation, register))

    @catch_exception
    def group_modal(self):
        current_user = request.form['current-user']

        chips = [
            div('.chip')[
                v, 
                i('.material-icons.close',
                  hx_delete='/add-group-modal-member')['close'],
                input(attr='chip', name='member', value=v, type='hidden')
            ] if v != current_user else
            div('.chip')[
                v,
                input(attr='chip', name='member', value=v, type='hidden')
            ]
            for v in request.form.getlist('member')
        ]
        
        if request.form['username-input'] and request.form['username-input'] != current_user:
            name = request.form['username-input']
            chips += [
                div('.chip')[
                    name, 
                    i('.material-icons.close')['close'], 
                    input(attr='chip', name='member', value=name, type='hidden')
                ]
            ]

        added = div('#added.chips.input-field',
                    hx_post='/add-group-user-validation',
                    hx_trigger='mouseout',
                    hx_target='#confirm-button',
                    hx_swap='outerHTML')[
            chips
        ].render(0)

        username_input = input('#username-input.validate',
                      name='username-input',
                      type='text',
                      hx_post='/add-group-create-validation',
                      hx_trigger='input change delay:500ms',
                      hx_target='#add-private-modal-status',
                      hx_swap_oob='outerHTML').render()
        
        status_text = a('#add-private-modal-status', hx_swap_oob='innerHTML')[''].render(0)

        confirm_button = a('#confirm-button.modal-close.waves-effect.waves-light.btn-flat.teal-text',
                            href='#',
                            hx_post='/group-chat',
                            hx_target='#active-chat',
                            hx_swap_oob='outerHTML')[
                                'Confirm'
                            ].render(0) if len(chips) > 1 else a('#confirm-button.modal-close.waves-effect.waves-light.btn-flat.teal-text.disabled',
                                                                 href='#',
                                                                 hx_post='/group-chat',
                                                                 hx_target='#active-chat',
                                                                 hx_swap_oob='outerHTML')['Confirm'].render(0)
        
        add_button = a('#add-user-button.btn.disabled',
                        href='#',
                        hx_target='#added',
                        hx_swap='outerHTML',
                        hx_include="[attr='chip']",
                        hx_post='/group-modal',
                        hx_swap_oob='outerHTML')[i('.material-icons')['add']].render(0)

        return '\n'.join((added, username_input, status_text, confirm_button, add_button))

    @catch_exception
    def add_private_username_validation(self):
        if self.__database.get_user_by_handle(request.form.get('username-input', '')) is not None:
            validation = a('#add-private-modal-status.green-text')[
                i('.material-icons.tiny')['check'],
                'User exists.'
            ].render()
            confirm = a('#confirm-button.modal-close.waves-effect.waves-light.btn-flat.teal-text',
                        hx_swap_oob='outerHTML',
                        hx_post='/private-chat')['Confirm'].render(0)
            
            return ''.join((validation, confirm))
        else:
            validation = a('#add-private-modal-status.red-text')[
                i('.material-icons.tiny')['close'],
                'User not found.'
            ].render()
            confirm = a('#confirm-button.modal-close.waves-effect.waves-light.btn-flat.teal-text.disabled',
                        hx_swap_oob='outerHTML')['Confirm'].render(0)
            
            return ''.join((validation, confirm))
    
    @catch_exception
    def post_add_group_modal_reset(self):
        username = request.form['username']

        group_name_input = input('#group-name-input.validate',
                                 name='group-name-input',
                                 type='text',
                                 hx_post='/add-group-name-validation',
                                 hx_trigger='input change delay:500ms',
                                 hx_target='#confirm-button',
                                 hx_swap='outerHTML',
                                 hx_swap_oob='outerHTML').render(0)

        username_input = input('#username-input.validate',
                                name='username-input',
                                type='text',
                                hx_post='/add-group-user-validation',
                                hx_trigger='input change delay:500ms',
                                hx_target='#confirm-button',
                                hx_swap='outerHTML',
                                hx_swap_oob='outerHTML').render(0)

        username_validation = a('#add-group-modal-username-status', hx_swap_oob='outerHTML').render(0)

        add_user_button = a('#add-user-button.btn.disabled',
                            href='#',
                            hx_target='#added',
                            hx_swap='outerHTML',
                            hx_include="[attr='chip']",
                            hx_post='/group-modal',
                            hx_swap_oob='outerHTML')[i('.material-icons')['add']].render(0)
        
        name_validation = a('#add-group-modal-group-name-status',
                            hx_swap_oob='outerHTML').render(0)
        
        added = div('#added.chips.input-field',
                    hx_post='/add-group-user-validation',
                    hx_trigger='mouseout',
                    hx_target='#confirm-button',
                    hx_swap='outerHTML',
                    hx_swap_oob='outerHTML')[
            div('.chip')[
                username, 
                input(attr='chip', name='member', value=username, type='hidden')
            ]
        ].render(0)
        
        confirm = a('#confirm-button.modal-close.waves-effect.waves-light.btn-flat.teal-text.disabled',
                    href='#',
                    hx_post='/group-chat',
                    hx_target='#active-chat')[
                'Confirm'
        ].render(0)

        return group_name_input + username_input + username_validation + add_user_button + name_validation + added + confirm
    
    @catch_exception
    def add_group_create_validation(self):
        username = request.form.get('username-input', '')
        if self.__database.get_user_by_handle(username) is not None:
            username_validation = a('#add-group-modal-username-status.green-text',
                                    hx_swap_oob='outerHTML')[
                                    i('.material-icons.tiny')['check'],
                                    'User exists.'
            ].render()
            
            add_user_button = a('#add-user-button.btn.blue',
                                href='#',
                                hx_target='#added',
                                hx_swap='outerHTML',
                                hx_include="[attr='chip']",
                                hx_post='/group-modal',
                                hx_swap_oob='outerHTML')[i('.material-icons')['add']].render(0)
        
        else:
            username_validation = a('#add-group-modal-username-status.red-text',
                                    hx_swap_oob='outerHTML')[
                                    i('.material-icons.tiny')['close'],
                                    'User not found.'
            ].render() if username else a('#add-group-modal-username-status.red-text',
                                          hx_swap_oob='outerHTML').render(0)

            add_user_button = a('#add-user-button.btn.disabled',
                                href='#',
                                hx_target='#added',
                                hx_swap='outerHTML',
                                hx_include="[attr='chip']",
                                hx_post='/group-modal',
                                hx_swap_oob='outerHTML')[i('.material-icons')['add']].render(0)
            
        if request.form.get('group-name-input', ''):
            name_validation = a('#add-group-modal-group-name-status.green-text',
                                hx_swap_oob='outerHTML')[
                                i('.material-icons.tiny')['check'],
                                'Group name OK.'
            ].render(0)
        else:
            name_validation = a('#add-group-modal-group-name-status.red-text',
                                hx_swap_oob='outerHTML')[
                                i('.material-icons.tiny')['close'],
                                'Group name cannot be empty.'
            ].render(0)
            
        confirm = a('#confirm-button.modal-close.waves-effect.waves-light.btn-flat.teal-text.disabled',
                    href='#',
                    hx_post='/group-chat',
                    hx_target='#active-chat')[
                'Confirm'
        ].render(0) if len(request.form.getlist('member')) <= 1 or not request.form.get('group-name-input', '') \
              else a('#confirm-button.modal-close.waves-effect.waves-light.btn-flat.teal-text',
                     href='#',
                     hx_post='/group-chat',
                     hx_target='#active-chat')['Confirm'].render(0)
        
        return username_validation + add_user_button + name_validation + confirm

    @catch_exception
    def main(self, username: str):
        messages = self.__database.get_latest_group_messages_by_user(username) + self.__database.get_latest_private_messages_by_user(username)
        sorted_messages = sorted(messages, key=lambda x: x.message.created, reverse=True)
        main_user = self.__database.get_user_by_handle(username).name
        all_chats = {g.name: None for g in self.__database.get_group_chats_by_username(username)}
        for c in all_chats: print('c',c)
        all_chats.update({
            (((m.recipient.handle, m.recipient.name) if m.message.sender.handle == username else(m.message.sender.handle,  m.message.sender.name)) if isinstance(m, PrivateMessage) else m.group.name) : m for m in sorted_messages
        })

        print(all_chats)
        
        v = rel(imp('views'))

        chats = tuple(
            v.CHAT.set_vars(
                chat_id=f'{n[0]}-chat',
                chat_get_url=f'/private-chat?current-user={username}&target-user={n[0]}',
                chat_title=n[1] if isinstance(m, PrivateMessage) else m.group.name,
                chat_latest_text=f'You: {m.message.content}?' if m.message.sender.handle == username
                else f'{m.message.sender.name}: {m.message.content}',
                chat_latest_time=m.message.created.strftime('%H:%M')
            ) if isinstance(n, tuple) else
            v.CHAT.set_vars(
                chat_id=f'{n}-chat',
                chat_get_url=f'/group-chat?current-user={username}&group-name={n}',
                chat_title=n,
                chat_latest_text='<em>No message yet</em>' if m is None else f'You: {m.message.content}?' if m.message.sender.handle == username
                else f'{m.message.sender.name}: {m.message.content}',
                chat_latest_time='' if m is None else m.message.created.strftime('%H:%M')
            ) for n, m in all_chats.items()
        )

        content = v.MAIN.set_vars(
            main_user_name=main_user,
            main_chats=chats,
            main_user_delete_url=f'/user/{username}',
            main_user_logout_url='/logout',
            add_private_modal_current_user=username,
            add_group_modal_user=username,
        ).render(0)

        websocket = div('#websocket', hx_swap_oob='outerHTML', hx_ext='ws', ws_connect=f'/ws/{username}').render(0)

        return content + websocket

    def register(self):
        v = rel(imp('views'))
        return v.ROOT.set_vars(main_content=v.REGISTER).render(0)
    
    def login(self):
        v = rel(imp('views'))
        return v.ROOT.set_vars(main_content=v.LOGIN).render(0)
    
    def post_login(self):
        username = request.form['username']

        return self.main(username)
    
    def put_logout(self):
        v = rel(imp('views'))
        return v.LOGIN.render(0)
    
    def post_user(self):
        v = rel(imp('views'))
        user = self.__database.create_user(User(
            request.form['username'],
            request.form['display-name']
        ))

        return self.main(user.handle)

    def create_user(self, handle, name):
        ret = self.__database.create_user(User(handle, name))

        return str(ret)
    
    def get_users(self):
        return self.__database.get_users()
    
    @catch_exception
    def delete_user(self, username: str):
        v = rel(imp('views'))

        self.__database.delete_user(username)

        return v.LOGIN.render(0)
    
    @catch_exception
    def post_private_chat(self):
        v = rel(imp('views'))

        current_user = request.form['current-user']
        target_user = request.form['username-input']

        messages = self.__database.get_private_messages(current_user, target_user) + \
        self.__database.get_private_messages(target_user, current_user)
        sorted_messages = sorted(messages, key=lambda x: x.message.created)

        active_chat = v.ACTIVE_CHAT(hx_swap_oob='outerHTML').set_vars(
            active_chat_messages=[
                v.CHAT_MESSAGE_RECEIVED.set_vars(chat_message_received_sender=m.message.sender.name,
                                                 chat_message_received_content=m.message.content,
                                                 chat_message_received_time=m.message.created.strftime('%H:%M'))
                if m.recipient.handle == current_user
                else v.CHAT_MESSAGE_SENT.set_vars(chat_message_sent_content=m.message.content,
                                                  chat_message_sent_time=m.message.created.strftime('%H:%M'))
                for m in sorted_messages
            ],
            active_chat_current_user=current_user,
            active_chat_target_user=target_user,
            active_chat_title=target_user,
            active_chat_send_url='/private-message',
        ).render(0)

        return active_chat
    
    @catch_exception
    def post_private_message(self):
        v = rel(imp('views'))

        current_user = request.form['current-user']
        target_user = request.form['target-user']
        message_content = request.form['message-content']

        current_user_obj = self.__database.get_user_by_handle(current_user)
        target_user_obj = self.__database.get_user_by_handle(target_user)

        self.__database.create_private_message(
            Message(content=message_content,
                    sender=current_user_obj,
                    created=datetime.now(),
                    modified=None),
            self.__database.get_user_by_handle(target_user)
        )

        messages = self.__database.get_private_messages(current_user, target_user)
        sorted_messages = sorted(messages, key=lambda x: x.message.created)

        active_chat = v.ACTIVE_CHAT.set_vars(
            active_chat_messages=[
                v.CHAT_MESSAGE_RECEIVED.set_vars(chat_message_received_sender=m.message.sender.name,
                                                 chat_message_received_content=m.message.content,
                                                 chat_message_received_time=m.message.created.strftime('%H:%M'))
                if m.recipient.handle == current_user
                else v.CHAT_MESSAGE_SENT.set_vars(chat_message_sent_content=m.message.content,
                                                  chat_message_sent_time=m.message.created.strftime('%H:%M'))
                for m in sorted_messages
            ],
            active_chat_current_user=current_user,
            active_chat_target_user=target_user,
            active_chat_title=target_user,
            active_chat_send_url='/private-message',
        ).render(0)

        latest_message = sorted_messages[-1].message

        user_updated_chat = v.CHAT.set_vars(
            chat_id=f'{target_user}-chat',
            chat_title=target_user_obj.name,
            chat_latest_text=f'You: {latest_message.content}',
            chat_latest_time=latest_message.created.strftime('%H:%M')
        )(hx_swap_oob='innerHTML').render(0)

        if len(self.__websockets.get(target_user, [])) > 0:
            print(f'{target_user} has {len(self.__websockets.get(target_user, []))} websockets.')
            target_updated_chat = v.CHAT.set_vars(
                chat_id=f'{current_user}-chat',
                chat_get_url=f'/private-chat?current-user={current_user}&target-user={target_user}',
                chat_title=current_user_obj.name,
                chat_latest_text=f'{current_user_obj.name}: {latest_message.content}',
                chat_latest_time=latest_message.created.strftime('%H:%M')
            )(hx_swap_oob='innerHTML').render(0)

            for ws in self.__websockets[target_user]:
                message_bubble = div('.row', style='margin: 0')[
                    v.CHAT_MESSAGE_RECEIVED.set_vars(
                        chat_message_received_sender=latest_message.sender.name,
                        chat_message_received_content=latest_message.content,
                        chat_message_received_time=latest_message.created.strftime('%H:%M')
                    )
                ](hx_swap_oob=f'beforeend:[chat-target={current_user}]').render(0)

                ws.send(target_updated_chat + message_bubble)

        return active_chat + user_updated_chat
    
    @catch_exception
    def get_private_chat(self):
        v = rel(imp('views'))

        current_user = request.args['current-user']
        target_user = request.args['target-user']

        messages = self.__database.get_private_messages(current_user, target_user)
        sorted_messages = sorted(messages, key=lambda x: x.message.created)

        return v.ACTIVE_CHAT.set_vars(
            active_chat_messages=[
                v.CHAT_MESSAGE_RECEIVED.set_vars(chat_message_received_sender=m.message.sender.name,
                                                 chat_message_received_content=m.message.content,
                                                 chat_message_received_time=m.message.created.strftime('%H:%M'))
                if m.recipient.handle == current_user
                else v.CHAT_MESSAGE_SENT.set_vars(chat_message_sent_content=m.message.content,
                                                  chat_message_sent_time=m.message.created.strftime('%H:%M'))
                for m in sorted_messages
            ],
            active_chat_current_user=current_user,
            active_chat_target_user=target_user,
            active_chat_title=target_user,
            active_chat_send_url='/private-message',
        ).render(0)
    
    @catch_exception
    def get_group_chat(self):
        v = rel(imp('views'))

        current_user = request.args['current-user']
        group_name = request.args['group-name']

        messages = self.__database.get_group_messages(group_name)

        return v.ACTIVE_CHAT.set_vars(
            active_chat_messages=[
                v.CHAT_MESSAGE_RECEIVED.set_vars(chat_message_received_sender=m.message.sender.name,
                                                 chat_message_received_content=m.message.content,
                                                 chat_message_received_time=m.message.created.strftime('%H:%M'))
                if m.message.sender.handle != current_user
                else v.CHAT_MESSAGE_SENT.set_vars(chat_message_sent_content=m.message.content,
                                                  chat_message_sent_time=m.message.created.strftime('%H:%M'))
                for m in messages
            ],
            active_chat_current_user=current_user,
            active_chat_target_user=group_name,
            active_chat_title=group_name,
            active_chat_send_url='/group-message',
        ).render(0)
    
    @catch_exception
    def post_group_chat(self):
        v = rel(imp('views'))

        member_usernames = request.form.getlist('member')
        group_name = request.form['group-name-input']
        current_user = request.form['current-user']

        self.__database.create_group_chat(group_name, member_usernames)

        target_updated_chat = div(hx_swap_oob='beforeend:#chats')[
            v.CHAT.set_vars(
                chat_id=f'{group_name}-chat',
                chat_get_url=f'/group-chat?current-user={current_user}&group-name={group_name}',
                chat_title=group_name,
                chat_latest_text='<em>No message yet</em>',
                chat_latest_time=''
            )
        ].render(0)
        
        for member in member_usernames:
            if member != current_user and len(self.__websockets.get(member, [])) > 0:
                print(f'{member} has {len(self.__websockets.get(member, []))} websockets.')
                for ws in self.__websockets[member]:
                    ws.send(target_updated_chat)

        return target_updated_chat + v.ACTIVE_CHAT.set_vars(
            active_chat_messages='',
            active_chat_current_user=current_user,
            active_chat_target_user=group_name,
            active_chat_title=group_name,
            active_chat_send_url='/group-message',
        ).render(0)

    @catch_exception
    def post_view_group_chat(self):
        v = rel(imp('views'))

        current_user = request.args['current-user']
        group_name = request.args['group-name']

        messages = self.__database.get_group_messages(group_name)

        active_chat = v.ACTIVE_CHAT(hx_swap_oob='outerHTML').set_vars(
            active_chat_messages=[
                v.CHAT_MESSAGE_RECEIVED.set_vars(chat_message_received_sender=m.message.sender.name,
                                                 chat_message_received_content=m.message.content,
                                                 chat_message_received_time=m.message.created.strftime('%H:%M'))
                if m.recipient.handle == current_user
                else v.CHAT_MESSAGE_SENT.set_vars(chat_message_sent_content=m.message.content,
                                                  chat_message_sent_time=m.message.created.strftime('%H:%M'))
                for m in messages
            ],
            active_chat_current_user=current_user,
            active_chat_target_user=group_name,
            active_chat_title=group_name,
            active_chat_send_url='/group-message',
        ).render(0)

        return active_chat
    
    @catch_exception
    def post_group_message(self):
        v = rel(imp('views'))

        current_user = request.form['current-user']
        group_name = request.form['target-user']
        message_content = request.form['message-content']

        current_user_obj = self.__database.get_user_by_handle(current_user)

        self.__database.create_group_message(
            Message(content=message_content,
                    sender=current_user_obj,
                    created=datetime.now(),
                    modified=None),
            GroupChat(name=group_name)
        )

        messages = self.__database.get_group_messages(group_name)

        active_chat = v.ACTIVE_CHAT.set_vars(
            active_chat_messages=[
                v.CHAT_MESSAGE_RECEIVED.set_vars(chat_message_received_sender=m.sender.name,
                                                 chat_message_received_content=m.content,
                                                 chat_message_received_time=m.created.strftime('%H:%M'))
                if m.sender.handle != current_user
                else v.CHAT_MESSAGE_SENT.set_vars(chat_message_sent_content=m.content,
                                                  chat_message_sent_time=m.created.strftime('%H:%M'))
                for m in (gm.message for gm in messages)
            ],
            active_chat_current_user=current_user,
            active_chat_target_user=group_name,
            active_chat_title=group_name,
            active_chat_send_url='/group-message',
        ).render(0)

        latest_message = messages[-1].message

        user_updated_chat = v.CHAT.set_vars(
            chat_id=f'{group_name}-chat',
            chat_title=group_name,
            chat_latest_text=f'You: {latest_message.content}',
            chat_latest_time=latest_message.created.strftime('%H:%M')
        )(hx_swap_oob='innerHTML').render(0)


        for user in self.__database.get_users_in_group_chat(GroupChat(name=group_name)):
            if len(self.__websockets.get(user.handle, [])) > 0:
                print(f'{user.handle} has {len(self.__websockets.get(user.handle, []))} websockets.')
                target_updated_chat = v.CHAT.set_vars(
                    chat_id=f'{group_name}-chat',
                    chat_title=group_name,
                    chat_latest_text=f'{current_user_obj.name}: {latest_message.content}',
                    chat_latest_time=latest_message.created.strftime('%H:%M')
                )(hx_swap_oob='innerHTML').render(0)

                for ws in self.__websockets[user.handle]:
                    message_bubble = div('.row', style='margin: 0')[
                        v.CHAT_MESSAGE_RECEIVED.set_vars(
                            chat_message_received_sender=latest_message.sender.name,
                            chat_message_received_content=latest_message.content,
                            chat_message_received_time=latest_message.created.strftime('%H:%M')
                        )
                    ](hx_swap_oob=f'beforeend:[chat-target={group_name}]').render(0)

                    ws.send(target_updated_chat + message_bubble)

        return active_chat + user_updated_chat

if __name__ == '__main__':
    WebApp().run()