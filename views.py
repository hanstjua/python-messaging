from chope import *
from chope.css import *
from chope.variable import Var

ROOT = html[
    head[
        link(href="https://fonts.googleapis.com/icon?family=Material+Icons",
             rel="stylesheet"),
        link(rel="stylesheet",
             href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css"),
        script(src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"),
        script(src="https://unpkg.com/htmx.org@2.0.2"),
        script(src="https://unpkg.com/htmx.org@1.9.12/dist/ext/ws.js"),
    ],
    body[
        div('#websocket'),
        div('#main-content')[Var('main_content', 'No content.')],
        script['M.AutoInit();']
    ]
]

REGISTER = div('.row.valign-wrapper', style='height: 100vh;')[
    form('.col.s12', onsubmit='return false;')[
        div('.row')[
            div('.col.s4'),
            h2('.col.s4.teal-text.text-darken-1')['Create an Account']
        ],
        div('.row')[
            div('.col.s4'),
            div('.input-field.col.s4')[
                input('#handle.validate',
                      name='username',
                      type='text',
                      placeholder='@username',
                      hx_post='/register/username-validation',
                      hx_target='#username-validation',
                      hx_trigger='input changed delay:500ms'),
                label(for_='handle')['Username'],
                p('#username-validation')
            ]
        ],
        div('.row')[
            div('.col.s4'),
            div('.input-field.col.s4')[
                input('#display-name.validate',
                      name='display-name',
                      type='text',
                      placeholder='e.g. John Doe',
                      hx_post='/register/display-name-validation',
                      hx_target='#display-name-validation',
                      hx_trigger='input changed delay:500ms'),
                label(for_='display-name')['Display Name'],
                p('#display-name-validation')
            ]
        ],
        div('.row')[
            div('.col.s4'),
            div('.col.s4')[
                a("#register-button.waves-effect.waves-light.btn.disabled",
                  hx_post='/user',
                  hx_target='#main-content')[
                    'Register',
                    i('.material-icons.right')['send']
                ]
            ]
        ],
        div('.row')[
            div('.col.s4'),
            div('.col.s4')["Have an account already? ", a(href='/login')['Login here']]
        ]
    ]
]

LOGIN = div('.row.valign-wrapper', style='height: 100vh;')[
    form('.col.s12', onsubmit='return false;')[
        div('.row')[
            div('.col.s4'),
            h2('.col.s4.teal-text.text-darken-1')['Welcome back!']
        ],
        div('.row')[
            div('.col.s4'),
            div('.input-field.col.s4')[
                input('#handle.validate',
                      name='username',
                      type='text',
                      hx_post='/login/username-validation',
                      hx_target='#username-validation',
                      hx_trigger='input change delay:500ms'),
                label(for_='handle')['Username'],
                p('#username-validation')['']
            ]
        ],
        div('.row')[
            div('.col.s4'),
            div('.col.s4')[
                a("#login-button.waves-effect.waves-light.btn.disabled",
                  hx_post='/main',
                  hx_target='html')[
                    'Login',
                    i('.material-icons.right')['send']
                ]
            ]
        ],
        div('.row')[
            div('.col.s4'),
            div('.col.s4')["Don't have an account yet? ", a(href='/')['Register here']]
        ]
    ]
]

CHAT = a('.collection-item.valign-wrapper',
         id=Var('chat_id'),
         href='#',
         style='padding-left: 30px',
         hx_get=Var('chat_get_url'),
         hx_target='#active-chat',
         hx_swap='outerHTML')[
    div('.row', style='margin-bottom: 0')[
        div('.col')[
            div('.truncate')[b[Var('chat_title', 'not set')]],
            div('.truncate', style='width: 180px')[Var('chat_latest_text', 'not set.')]
        ],
        div('.col')[Var('chat_latest_time', '99:99')]
    ]
]

CHAT_DATE = div('.row', style='margin: 0')[
    p('.center-align')[Var('chat_date')]
]

CHAT_MESSAGE_RECEIVED = div('.row', style='margin: 0')[
    div('.card.chat-message', style='display: inline-block')[
        div('.row', style='margin: 0')[
            div('.col')[
                div('.teal-text')[Var('chat_message_received_sender', 'Sender Name')],
                div(style='text-wrap: pretty; max-width: 400px')[Var('chat_message_received_content')]
            ]
        ],
        div('.row', style='margin: 0')[
            div('.col.grey-text')[Var('chat_message_received_time')]
        ]
    ]
]

CHAT_MESSAGE_SENT = div('.row', style='margin: 0')[
    div('.card.chat-message.green.lighten-4.right', style='display: inline-block')[
        div('.row', style='margin: 0')[
            div('.col')[
                div(style='text-wrap: pretty; max-width: 400px')[Var('chat_message_sent_content')]
            ]
        ],
        div('.row', style='margin: 0')[
            div('.col.grey-text.text-darken-1')[Var('chat_message_sent_time')]
        ]
    ]
]

_SIDEBAR_WIDTH = px/300
_ICON_WIDTH = px/50

ACTIVE_CHAT = div('#active-chat.col.teal.lighten-5',
                  style=f'height: 100%; width: calc( 100% - {_SIDEBAR_WIDTH} ); padding: 0; overflow: auto;')[
    script[
        "var e = document.getElementById('active-chat'); e.scrollTop = e.scrollHeight;"
    ],
    main('#messages.teal.lighten-5',
         chat_target=Var('active_chat_target_user'),
         style='position: relative; padding-top: 50px; padding-bottom: 70px; left: 0;')[
        style[
            Css[
                '.chat-message': {
                    'margin': rem/0.5,
                    'padding': rem/0.5
                }
            ]
        ],
        Var('active_chat_messages')
    ],
    header('.teal.darken-1.valign-wrapper', style=f'position: fixed; left: {_SIDEBAR_WIDTH}; top: 0; width: calc(100% - {_SIDEBAR_WIDTH}); height: 50px')[
        div('.row', style='margin: 0; width: 100%')[
            div('.col.valign-wrapper', style=f'width: calc( 100% - {_ICON_WIDTH} )')[
                p('.center-align.white-text', style='width: 100%')[b[Var('active_chat_title')]]
            ],
            
        ]
    ],
    footer('.teal.darken-1.valign-wrapper', style=f'position: fixed; left: {_SIDEBAR_WIDTH}; bottom: 0; width: calc( 100% - {_SIDEBAR_WIDTH} );')[
        form(style='margin: 0; width: 100%; height: 70px', onsubmit='return false;')[
            div(',row', style='margin: 0')[
                div('.input-field.col', style=f'width: calc( 100% - {_ICON_WIDTH} ); margin-top: 0.5rem; margin-bottom: 0.5rem')[
                    input('.validate.white-text',
                          name='message-content',
                          placeholder='Type a message',
                          hx_post=Var('active_chat_send_url'),
                          hx_target='#active-chat',
                          hx_swap='outerHTML',
                          hx_trigger="keyup[key=='Enter']")
                ],
                div('.input-field.col', style='margin-top: 0.5rem; margin-bottom: 0.5rem')[
                    input(name='current-user', type='hidden', value=Var('active_chat_current_user'))[''],
                    input(name='target-user', type='hidden', value=Var('active_chat_target_user'))[''],
                    a('.teal-text.text-lighten-3.valign-wrapper',
                      href='#',
                      hx_post=Var('active_chat_send_url'),
                      hx_target='#active-chat',
                      hx_swap='outerHTML')[
                        div('.valign-wrapper', style='height: 54px')[i('.material-icons')['send']]
                    ]
                ]
            ]
        ]
    ]
]

ADD_PRIVATE_MODAL = form('#add-private-modal.modal', onsubmit='return false;')[
    input(name='current-user', value=Var('add_private_modal_current_user', ''), type='hidden')[''],
    div('.modal-content')[
        h5['Private Chat'],
        '<br>',
        div('.input-field')[
            input('#username-input.validate', 
                  name='username-input', 
                  type='text', 
                  hx_post='/add-private-user-validation', 
                  hx_trigger='input change delay:500ms', 
                  hx_target='#add-private-modal-status'),
            label(for_='username-input')['Username']
        ],
        a('#add-private-modal-status.green-text')
    ],
    div('.modal-footer')[
        a('#confirm-button.modal-close.waves-effect.waves-light.btn-flat.teal-text.disabled')['Confirm'],
        a('.modal-close.waves-effect.waves-light.btn-flat.pink-text')['Cancel']
    ]
]

ADD_GROUP_MODAL = div('#add-group-modal.modal')[
    form[
        div('.modal-content')[
            input(name='current-user', type='hidden', value=Var('add_group_modal_user')),
            h5['Group Chat'],
            '<br>',
            div('.row')[
                div('.col.s10.input-field')[
                    input('#group-name-input.validate',
                        name='group-name-input',
                        type='text',
                        hx_post='/add-group-name-validation',
                        hx_trigger='input change delay:500ms',
                        hx_target='#confirm-button',
                        hx_swap='outerHTML'),
                    label(for_='group-name-input')['Group Name'],
                    a('#add-group-modal-group-name-status.green-text'),
                ],
                div('.col.s10.input-field')[
                    input('#username-input.validate',
                        name='username-input',
                        type='text',
                        hx_post='/add-group-user-validation',
                        hx_trigger='input change delay:500ms',
                        hx_target='#confirm-button',
                        hx_swap='outerHTML'),
                    label(for_='username-input')['Username'],
                    a('#add-group-modal-username-status.green-text'),
                ],
                div('.col.s1.input-field.')[
                    a('#add-user-button.btn.disabled',
                    href='#',
                    hx_target='#added',
                    hx_include="[attr='chip']",
                    hx_post='/group-modal')[i('.material-icons')['add']]
                ]
            ],
            div('#added.chips.input-field',
                hx_post='/add-group-user-validation',
                hx_trigger='mouseout',
                hx_target='#confirm-button',
                hx_swap='outerHTML')[
                div('.chip')[
                    Var('add_group_modal_user'), 
                    input(attr='chip', name='member', value=Var('add_group_modal_user'), type='hidden')
                ]
            ]
        ],
        div('.modal-footer')[
            a('#confirm-button.modal-close.waves-effect.waves-light.btn-flat.teal-text.disabled',
                href='#',
                hx_post='/group-chat',
                hx_include="[attr='chip']",
                hx_target='#active-chat')['Confirm'],
                input(type='hidden', name='username', value=Var('add_group_modal_user')),
                a('.modal-close.waves-effect.waves-light.btn-flat.pink-text',
                href='#',
                hx_post='/add-group-modal-reset',
                hx_target='#confirm-button')['Cancel']
        ]
    ]
]

NO_CHAT_SELECTED = div('#active-chat.row.teal.lighten-4', 
                        style=f'height: 100vh; padding-left: {_SIDEBAR_WIDTH}')[
    div('.col.s12.valign-wrapper',
        style='height: 100%')[
        h4('.center-align.teal-text.text-darken-3',
            style='width: 100%')[
            'Choose a chat to open'
        ]
    ]
]

MAIN = div(style='height: 100vh')[
    div('.row', style='height: 100%')[
        div('.col.card', style=f'padding: 0; margin: 0; height: 100%; width: {_SIDEBAR_WIDTH}')[
            div('.collection.with-header', style='margin: 0; height: 100vh')[
                div('.collection-item.row', style='height: 50px;')[
                    div('.col')[
                        h6('.teal-text.text-darken-1')[
                            Var('main_user_name')
                        ]
                    ],
                    div('.col.right', style='margin-top: 0.4rem')[
                        a('.dropdown-trigger.teal-text',
                        href='#',
                        data_target='settings-dropdown')[
                            i('.material-icons')['settings']
                        ],
                        ul('#settings-dropdown.dropdown-content')[
                            # li[
                            #     a('.red-text',
                            #     href='#',
                            #     hx_delete=Var('main_user_delete_url'),
                            #     hx_target='#main-content',
                            #     hx_swap='outerHTML')[
                            #         i('.material-icons')['delete_forever'],
                            #         'Delete account',
                            #     ],
                            # ],
                            li[
                                a('.amber-text.text-darken-2',
                                href='#',
                                hx_put=Var('main_user_logout_url'),
                                hx_target='#main-content',
                                hx_swap='innerHTML')[
                                    i('.material-icons')['exit_to_app'],
                                    'Logout',
                                ],
                            ]
                        ]
                    ],
                    div('.col.right', style='margin-top: 0.4rem')[
                        a('.secondary-content.modal-trigger', href='#add-group-modal')[i('.material-icons')['group_add']],
                        ADD_GROUP_MODAL
                    ],
                    div('.col.right', style='margin-top: 0.4rem')[
                        a('.secondary-content.modal-trigger', href='#add-private-modal')[i('.material-icons')['person_add']],
                        ADD_PRIVATE_MODAL
                    ]
                ],
                div('.divider'),
                div('#chats')[Var('main_chats')]
            ],
        ],
        Var(
            'active_chat',
            NO_CHAT_SELECTED
        ),
        script['M.AutoInit();']  ## initialize lazy added materialize css components
    ]
]
