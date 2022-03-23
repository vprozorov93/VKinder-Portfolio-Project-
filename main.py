import copy
from pprint import pprint
from random import randrange
from chat_db import chat_status, user_search_params, user_search_result, like_table, dislike_table, relations, sex
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# token = input('Token: ')

token = 'f7baadc7490ec0520331971bddda08772410ea38e0f15d48be4f941ee89a94f2b58dc51d7747c7f084679'
access_token = 'fef60d2678def882ef2a2336622271c1f76b4703c0f15175173147eebd21f9c60c80b3ed29c515b8a5c09'
vk = VkApi(token=token)
vk_search = VkApi(token=access_token)
long_poll = VkLongPoll(vk)


# Keyboards


def city_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(label='Москва', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button(label='Санкт-Петербург', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def sex_keyboard():
    keyboard = VkKeyboard(one_time=True)
    for element in sex:
        if isinstance(element, str):
            keyboard.add_button(label=element, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def status_keyboard():
    keyboard = VkKeyboard(one_time=True)
    element = 0
    for relation in relations:
        if isinstance(relation, str):
            keyboard.add_button(label=relation, color=VkKeyboardColor.SECONDARY)
            element += 1
            if element == 2:
                element -= 2
                keyboard.add_line()
    return keyboard.get_keyboard()


def menu_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(label='Начать поиск', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(label='Изменить настройки поиска', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def settings_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(label='Пол', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button(label='Город', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button(label='Год рождения', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button(label='Статус', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button(label='Назад в меню', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def like_keyboard(user_id=None):
    keyboard = VkKeyboard()
    keyboard.add_button(label='Нравится', color=VkKeyboardColor.POSITIVE, payload=['like', user_id])
    keyboard.add_button(label='Не нравится', color=VkKeyboardColor.NEGATIVE, payload=['dislike', user_id])
    keyboard.add_line()
    keyboard.add_button(label='Назад в меню', color=VkKeyboardColor.PRIMARY, payload=['Back'])
    return keyboard.get_keyboard()


# EndKeyboards

# DefaultMethods


def write_msg(user_id, message, keyboard=None):
    vk.method('messages.send',
              {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), 'keyboard': keyboard})


def accept_settings_message(vk_event):
    sex_ = sex[user_search_params[vk_event.user_id]["sex"]]
    city_ = user_search_params[vk_event.user_id]["city"]
    year_ = user_search_params[vk_event.user_id]["bdate"]
    status_ = relations[user_search_params[vk_event.user_id]["relation"]]
    write_msg(vk_event.user_id, f'Мы ищем тебе\n{sex_} в городе '
                                f'{city_} '
                                f'{year_} года рождения '
                                f'со статусом: {status_}')


def get_user_info(user_id):
    return vk.method('users.get', {'user_ids': user_id, 'fields': 'bdate, sex, city, relation'})


# EndDefaultMethods

# StartMethods


def start(vk_event):
    user_info = get_user_info(vk_event.user_id)[0]

    write_msg(vk_event.user_id, f"Привет, {user_info['first_name']}.\n"
                                f"Давай найдем тебе пару.")

    user_search_params[vk_event.user_id] = dict()
    user_search_result[vk_event.user_id] = list()
    like_table[vk_event.user_id] = list()
    dislike_table[vk_event.user_id] = list()
    params_status_is_ok = True

    if user_info.get('bdate'):
        if user_info.get('bdate')[-4:].isdigit():
            user_search_params[vk_event.user_id].update({'bdate': user_info.get('bdate')[-4:]})
        else:
            user_search_params[vk_event.user_id].update({'bdate': None})
            params_status_is_ok = False
    else:
        user_search_params[vk_event.user_id].update({'bdate': None})
        params_status_is_ok = False

    if user_info.get('sex') in [1, 2]:
        sex_for_search = [1, 2]
        sex_for_search.remove(user_info.get('sex'))
        user_search_params[vk_event.user_id].update({'sex': sex_for_search[0]})
    else:
        user_search_params[vk_event.user_id].update({'sex': None})
        params_status_is_ok = False

    if user_info.get('city'):
        user_search_params[vk_event.user_id].update({'city': user_info.get('city')['title']})
    else:
        user_search_params[vk_event.user_id].update({'city': None})
        params_status_is_ok = False

    if user_info.get('relation'):
        user_search_params[vk_event.user_id].update({'relation': user_info.get('relation')})
    else:
        user_search_params[vk_event.user_id].update({'relation': None})
        params_status_is_ok = False

    if params_status_is_ok:
        accept_settings_message(vk_event)
        chat_status[event.user_id] = 'menu'
    else:
        write_msg(vk_event.user_id, 'Перед поиском партнера, необходимо уточнить некоторые параметры.')
        chat_status[vk_event.user_id] = 'check_params'


def check_params(vk_event):
    pending = False
    for param, value in user_search_params[vk_event.user_id].items():
        if value == 'pending' or value is None:
            pending = True
            if value == 'pending':
                text = vk_event.text
                if param == 'relation':
                    text = relations[vk_event.text]
                user_search_params[vk_event.user_id].update({param: text})

    if pending:
        if not user_search_params[vk_event.user_id].get('city'):
            write_msg(vk_event.user_id, 'Выберите город для поиска или укажите свой', city_keyboard())
            user_search_params[vk_event.user_id].update({'city': 'pending'})
        elif not user_search_params[vk_event.user_id].get('sex'):
            write_msg(vk_event.user_id, 'Выберите пол человека для поиска', sex_keyboard())
            user_search_params[vk_event.user_id].update({'sex': 'pending'})
        elif not user_search_params[vk_event.user_id].get('bdate'):
            write_msg(vk_event.user_id, 'Введите год рождения человека для поиска')
            user_search_params[vk_event.user_id].update({'bdate': 'pending'})
        elif not user_search_params[vk_event.user_id].get('relation'):
            write_msg(vk_event.user_id, 'Выберите статус отношений человека для поиска', status_keyboard())
            user_search_params[vk_event.user_id].update({'relation': 'pending'})

    for param, value in user_search_params[vk_event.user_id].items():
        if value not in ['pending', None]:
            pending = False
        else:
            pending = True
            break

    if not pending:
        accept_settings_message(vk_event)
        chat_status[event.user_id] = 'menu'


# EndStartMethods

# MenuAndSettingsMethod


def menu(vk_event):
    write_msg(vk_event.user_id, 'Начни поиск или измени параметры', menu_keyboard())
    chat_status[vk_event.user_id] = 'choose_menu'


def choose_menu(vk_event):
    if vk_event.text == 'Начать поиск':
        chat_status[vk_event.user_id] = 'start_search'
    elif vk_event.text == 'Изменить настройки поиска':
        chat_status[vk_event.user_id] = 'change_settings'
    # else:
    #     chat_status[vk_event.user_id] = 'menu'


def settings(vk_event):
    for param, value in user_search_params[vk_event.user_id].items():
        if value == 'pending':
            text = vk_event.text
            if param == 'relation':
                text = relations[vk_event.text]
            elif param == 'sex':
                text = sex[vk_event.text]
            user_search_params[vk_event.user_id].update({param: text})

    sex_ = sex[user_search_params[vk_event.user_id]['sex']]
    bdate_ = user_search_params[vk_event.user_id]['bdate']
    city_ = user_search_params[vk_event.user_id]['city']
    relation_ = relations[user_search_params[vk_event.user_id]['relation']]

    write_msg(vk_event.user_id, f'Параметры поиска:\n'
                                f'Ищем: {sex_}\n'
                                f'В городе: {city_}\n'
                                f'Статус: {relation_}\n'
                                f'Год рождения:  {bdate_}\n'
                                f'Какой параметр изменить?', settings_keyboard())
    chat_status[vk_event.user_id] = 'choose_settings'


def choose_settings(vk_event):
    if vk_event.text == 'Пол':
        set_sex(vk_event)
    elif vk_event.text == 'Город':
        set_city(vk_event)
    elif vk_event.text == 'Год рождения':
        set_bdate(vk_event)
    elif vk_event.text == 'Статус':
        set_status(vk_event)
    elif vk_event.text == 'Назад в меню':
        write_msg(vk_event.user_id, 'Начни поиск или измени параметры', menu_keyboard())
        chat_status[vk_event.user_id] = 'choose_menu'
    # else:
    #     chat_status[vk_event.user_id] = 'change_settings'


def set_sex(vk_event):
    user_search_params[vk_event.user_id].update({'sex': 'pending'})
    write_msg(vk_event.user_id, 'Выберите пол человека для поиска', sex_keyboard())
    chat_status[vk_event.user_id] = 'change_settings'


def set_city(vk_event):
    user_search_params[vk_event.user_id].update({'city': 'pending'})
    write_msg(vk_event.user_id, 'Выберите город для поиска или укажите свой', city_keyboard())
    chat_status[vk_event.user_id] = 'change_settings'


def set_bdate(vk_event):
    user_search_params[vk_event.user_id].update({'bdate': 'pending'})
    write_msg(vk_event.user_id, 'Введите год рождения человека для поиска')
    chat_status[vk_event.user_id] = 'change_settings'


def set_status(vk_event):
    user_search_params[vk_event.user_id].update({'relation': 'pending'})
    write_msg(vk_event.user_id, 'Выберите статус отношений человека для поиска', status_keyboard())
    chat_status[vk_event.user_id] = 'change_settings'


# EndMenuAndSettingsMethod

# SearchMethod


def start_search(vk_event):
    if not len(user_search_result[vk_event.user_id]):
        get_city_id = vk_search.method('database.getCities', {'country_id': 1,
                                                              'q': user_search_params[vk_event.user_id]['city'],
                                                              'count': 1})['items'][0]['id']

        user_search_response = vk_search.method('users.search',
                                                {'birth_year': user_search_params[vk_event.user_id]['bdate'],
                                                 'sex': user_search_params[vk_event.user_id]['sex'],
                                                 'status': user_search_params[vk_event.user_id]['relation'],
                                                 'city': get_city_id,
                                                 'country': 1,
                                                 'count': 10})
        for user in user_search_response['items']:
            if user['id'] in like_table[vk_event.user_id] or user['id'] in dislike_table[vk_event.user_id]:
                continue
            user_search_result[vk_event.user_id].append(user['id'])

        if not len(user_search_result[vk_event.user_id]):
            write_msg(vk_event.user_id, 'Новых анкет нет, повторите поиск позднее', menu_keyboard())
            chat_status[event.user_id] = 'menu'
            return

    if vk_event.raw[6].get('payload'):
        if 'Back' in vk_event.raw[6]['payload']:
            write_msg(vk_event.user_id, 'Начни поиск или измени параметры', menu_keyboard())
            chat_status[vk_event.user_id] = 'choose_menu'
            return

        data = vk_event.raw[6]['payload']
        if 'dislike' in data:
            dislike_table[vk_event.user_id].append(int(data[data.find(',')+1:data.find(']')]))
        else:
            like_table[vk_event.user_id].append(int(data[data.find(',')+1:data.find(']')]))

    for_grade = user_search_result[vk_event.user_id].pop(0)

    if vk_search.method('users.get', {'user_ids': for_grade})[0]['is_closed']:
        dislike_table[vk_event.user_id].append(for_grade)
        start_search(vk_event)
    else:
        user_for_grade_info = vk_search.method('users.get', {'user_ids': for_grade})
        user_for_grade_photo_response = vk_search.method('photos.get', {'owner_id': for_grade,
                                                                        'album_id': 'profile',
                                                                        'extended': 1})

        user_for_grade_photo_lib = dict()
        for photo in user_for_grade_photo_response['items']:
            rating = photo['comments']['count'] * photo['likes']['count']
            photo = photo['id']

            if user_for_grade_photo_lib.get(rating):
                user_for_grade_photo_lib[rating].append(photo)
            else:
                user_for_grade_photo_lib[rating] = [photo]

        best_rating_photo = sorted(user_for_grade_photo_lib, reverse=True)[:3]
        user_for_grade_photo_list = []
        for rating in best_rating_photo:
            for photo in user_for_grade_photo_lib[rating]:
                if len(user_for_grade_photo_list) == 3:
                    break
                user_for_grade_photo_list.append(photo)

        photo_for_attachment = ''
        for photo in user_for_grade_photo_list:
            photo_for_attachment += f'photo{for_grade}_{photo}_{access_token},'

        photo_for_attachment = photo_for_attachment.rstrip(',')

        vk.method('messages.send',
                  {'user_id': vk_event.user_id,
                   'message': f'Как тебе [id{for_grade}|{user_for_grade_info[0]["first_name"]} '
                              f'{user_for_grade_info[0]["last_name"]}] ?',
                   'random_id': randrange(10 ** 7),
                   'attachment': photo_for_attachment,
                   'keyboard': like_keyboard(for_grade)})


# EndSearchMethod


if __name__ == '__main__':
    for event in long_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                if chat_status.get(event.user_id) is None:
                    start(event)

                if chat_status.get(event.user_id) == 'check_params':
                    check_params(event)

                if chat_status.get(event.user_id) == 'menu':
                    menu(event)

                if chat_status.get(event.user_id) == 'choose_menu':
                    choose_menu(event)

                if chat_status.get(event.user_id) == 'change_settings':
                    settings(event)

                if chat_status.get(event.user_id) == 'choose_settings':
                    choose_settings(event)

                if chat_status.get(event.user_id) == 'start_search':
                    start_search(event)
