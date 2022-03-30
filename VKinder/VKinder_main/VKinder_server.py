from random import randrange
from datetime import datetime
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from VKinder.VKinder_main.VKinder_chat_cache import relations, sex, user_search_result
import VKinder.VKinder_database.database_main as database


class VKinder:

    # InitializationAndLaunchMethods

    def __init__(self):
        self.token = input('Input group token: ')
        self.access_token = input('Input user access token: ')
        self.vk = VkApi(token=self.token)
        self.vk_search = VkApi(token=self.access_token)
        self.long_poll = VkLongPoll(self.vk)
        self.db = database.DB()
        print('VKinder initialization is DONE. Call "launch" method.')

    def launch(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:

                    if event.text.lower() == 'старт':
                        self.start(event)

                    elif 'back_to_menu' in str(event.raw[6].get('payload')):
                        self.menu(event)

                    elif 'set_settings' in str(event.raw[6].get('payload')):
                        self.settings(event)

                    elif 'set_param_' in str(event.raw[6].get('payload')):
                        self.set_settings(event)

                    elif 'start_search' in str(event.raw[6].get('payload')):
                        self.start_search(event)

                    elif 'view_matches' in str(event.raw[6].get('payload')):
                        self.print_matches(event)

                    else:
                        get_city_id = self.vk_search.method('database.getCities', {'country_id': 1,
                                                                                   'q': event.text,
                                                                                   'count': 1})['items']

                        if len(get_city_id) == 0:
                            self.write_msg(event.user_id,
                                           'Не понял твоего сообщения. Для начала отправь мне "Старт", '
                                           'а в дальнейшем выбор делай кнопками.')
                        else:
                            try:
                                self.settings(event)
                            except:  # Тут нужно ловить KeyError однако при наступлении события, почему-то Python
                                # говорит что нельзя отлавливать исключения других классов
                                self.start(event)

    # Keyboards

    @staticmethod
    def city_keyboard():
        payload = ['set_settings']
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(label='Москва', color=VkKeyboardColor.SECONDARY, payload=payload)
        keyboard.add_button(label='Санкт-Петербург', color=VkKeyboardColor.SECONDARY, payload=payload)
        return keyboard.get_keyboard()

    @staticmethod
    def sex_keyboard():
        keyboard = VkKeyboard(one_time=True)
        for gender in sex:
            if isinstance(gender, str):
                keyboard.add_button(label=gender, color=VkKeyboardColor.SECONDARY, payload=['set_settings'])
        return keyboard.get_keyboard()

    @staticmethod
    def year_keyboard(payload):
        keyboard = VkKeyboard(one_time=True)
        now_year = datetime.now().year
        element = 0
        if 'set_param_bdate' in payload:
            start_year = int(str(now_year - 60)[:3] + '0')
            end_year = now_year-18
            for year in range(start_year, end_year, 10):
                keyboard.add_button(label=str(year) + '-e', color=VkKeyboardColor.SECONDARY,
                                    payload=[f'set_param__{year}'])
                element += 1
                if element == 3:
                    element -= 3
                    keyboard.add_line()
        elif 'set_param__' in payload:
            index = payload.find('_', 7) + 1
            start_year = int(payload[index + 1:index + 5])
            end_year = start_year + 10
            for year in range(start_year, end_year):
                if year > now_year-18:
                    break
                keyboard.add_button(label=str(year), color=VkKeyboardColor.SECONDARY,
                                    payload=['set_settings'])
                element += 1
                if element == 3:
                    element -= 3
                    keyboard.add_line()

        return keyboard.get_keyboard()

    @staticmethod
    def status_keyboard():
        keyboard = VkKeyboard(one_time=True)
        element = 0
        for relation in relations:
            if isinstance(relation, str):
                keyboard.add_button(label=relation, color=VkKeyboardColor.SECONDARY, payload=['set_settings'])
                element += 1
                if element == 2:
                    element -= 2
                    keyboard.add_line()
        return keyboard.get_keyboard()

    @staticmethod
    def menu_keyboard():
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(label='Начать поиск', color=VkKeyboardColor.PRIMARY, payload=['start_search'])
        keyboard.add_button(label='Изменить настройки поиска', color=VkKeyboardColor.SECONDARY,
                            payload=['set_settings'])
        keyboard.add_line()
        keyboard.add_button(label='Посмотреть совпадения', color=VkKeyboardColor.NEGATIVE, payload=['view_matches'])
        return keyboard.get_keyboard()

    @staticmethod
    def settings_keyboard():
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(label='Пол', color=VkKeyboardColor.SECONDARY, payload=['set_param_sex'])
        keyboard.add_button(label='Город', color=VkKeyboardColor.SECONDARY, payload=['set_param_city'])
        keyboard.add_line()
        keyboard.add_button(label='Год рождения', color=VkKeyboardColor.SECONDARY, payload=['set_param_bdate'])
        keyboard.add_button(label='Статус', color=VkKeyboardColor.SECONDARY, payload=['set_param_relations'])
        keyboard.add_line()
        keyboard.add_button(label='Назад в меню', color=VkKeyboardColor.SECONDARY, payload=['back_to_menu'])
        return keyboard.get_keyboard()

    @staticmethod
    def like_keyboard(user_id=None):
        keyboard = VkKeyboard()
        keyboard.add_button(label='Нравится', color=VkKeyboardColor.POSITIVE,
                            payload=['start_search_like', user_id])
        keyboard.add_button(label='Не нравится', color=VkKeyboardColor.NEGATIVE,
                            payload=['start_search_dislike', user_id])
        keyboard.add_line()
        keyboard.add_button(label='Назад в меню', color=VkKeyboardColor.PRIMARY, payload=['back_to_menu'])
        return keyboard.get_keyboard()

    @staticmethod
    def matches_keyboard():
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(label='Назад в меню', color=VkKeyboardColor.SECONDARY, payload=['back_to_menu'])
        return keyboard.get_keyboard()

    # DefaultMethods

    def write_msg(self, user_id, message, keyboard=None):
        self.vk.method('messages.send',
                       {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), 'keyboard': keyboard})

    def get_user_info(self, user_id):
        return self.vk.method('users.get', {'user_ids': user_id, 'fields': 'bdate, sex, city, relation'})

    def check_close_account(self, user_list: list):
        while len(user_list) != 0:
            user = user_list.pop(0)
            if self.vk_search.method('users.get', {'user_ids': user})[0]['is_closed']:
                continue
            else:
                return user
        return None

    # DialogMethods

    def start(self, vk_event):
        user_info = self.get_user_info(vk_event.user_id)[0]
        if self.db.get_user_settings(int(vk_event.user_id)):
            self.write_msg(vk_event.user_id, f"Рад снова тебя видеть {user_info['first_name']}.")
        else:
            self.write_msg(vk_event.user_id, f"Привет, {user_info['first_name']}.\n"
                                             f"Давай найдем тебе пару.")

            if user_info.get('bdate'):
                if user_info.get('bdate')[-4:].isdigit():
                    user_bdate = int(user_info.get('bdate')[-4:])
                else:
                    year = datetime.now().year - 18
                    user_bdate = year
                    self.write_msg(vk_event.user_id, 'Не удалось определить год рождения для поиска. По умолчанию '
                                                     f'будет задан {year} год.'
                                                     'Параметр можно будет изменить в настройках.')
            else:
                year = datetime.now().year - 18
                user_bdate = year
                self.write_msg(vk_event.user_id, 'Не удалось определить год рождения для поиска. По умолчанию '
                                                 f'задан {year} год. Параметр можно будет изменить в настройках.')

            if user_info.get('sex') in [1, 2]:
                sex_for_search = [1, 2]
                sex_for_search.remove(user_info.get('sex'))
                user_sex = sex_for_search[0]
            else:
                user_sex = 0
                self.write_msg(vk_event.user_id, 'Не удалось определить пол для поиска, '
                                                 'поиск будет осуществлен по Мужчинам и Женщинам. '
                                                 'Параметр можно будет изменить в настройках.')

            if user_info.get('city'):
                user_city = user_info.get('city')['title']
            else:
                user_city = 'Москва'
                self.write_msg(vk_event.user_id, 'Не удалось определить ваш город. По умолчанию '
                                                 f'задан город Москва. Параметр можно будет изменить в настройках.')

            if user_info.get('relation'):
                user_relation = user_info.get('relation')
            else:
                user_relation = 6
                self.write_msg(vk_event.user_id, 'Не удалось определить статус отношений для поиска. По умолчанию '
                                                 f'задан статус "В активном поиске". '
                                                 f'Параметр можно будет изменить в настройках.')

            data_to_db = database.UserSearchSettings(vk_user=int(vk_event.user_id), bdate=user_bdate, sex=user_sex,
                                                     city=user_city, relation=user_relation)
            self.db.write_to_db(data_to_db)

        self.menu(vk_event)

    def menu(self, vk_event):
        self.write_msg(vk_event.user_id, 'Начни поиск или измени параметры', self.menu_keyboard())

    def settings(self, vk_event):
        user = self.db.get_user_settings(int(vk_event.user_id))
        user_search_params = {'bdate': user.bdate, 'sex': user.sex, 'relation': user.relation,
                              'city': user.city}

        for param, value in user_search_params.items():
            if value is None:
                user_search_result[vk_event.user_id] = []
                text = vk_event.text
                if param == 'relation':
                    text = relations[vk_event.text]
                elif param == 'sex':
                    text = sex[vk_event.text]

                user_search_params.update({param: text})
                self.db.update_settings(int(vk_event.user_id), param, text)

        self.write_msg(vk_event.user_id, f'Параметры поиска:\n'
                                         f'Ищем: {sex[user_search_params["sex"]]}\n'
                                         f'В городе: {user_search_params["city"]}\n'
                                         f'Статус: {relations[user_search_params["relation"]]}\n'
                                         f'Год рождения:  {user_search_params["bdate"]}\n'
                                         f'Какой параметр изменить?', self.settings_keyboard())

    def set_settings(self, vk_event):
        payload = vk_event.raw[6].get('payload')
        if 'set_param_sex' in payload:
            self.db.update_settings(int(vk_event.user_id), 'sex', None)
            self.write_msg(vk_event.user_id, 'Выберите пол человека для поиска', self.sex_keyboard())
        elif 'set_param_city' in payload:
            self.db.update_settings(int(vk_event.user_id), 'city', None)
            self.write_msg(vk_event.user_id, 'Выберите город для поиска или укажите свой',
                           self.city_keyboard())
        elif 'set_param_bdate' in payload or 'set_param__' in payload:
            self.db.update_settings(int(vk_event.user_id), 'bdate', None)
            self.write_msg(vk_event.user_id, 'Выберите год рождения для поиска', self.year_keyboard(payload))
        elif 'set_param_relations' in payload:
            self.db.update_settings(int(vk_event.user_id), 'relation', None)
            self.write_msg(vk_event.user_id, 'Выберите статус отношений человека для поиска',
                           self.status_keyboard())

    def start_search(self, vk_event):
        user = self.db.get_user_settings(int(vk_event.user_id))
        user_search_params = {'bdate': user.bdate, 'sex': user.sex, 'relation': user.relation,
                              'city': user.city}

        if user_search_result.get(vk_event.user_id) is None:
            user_search_result[vk_event.user_id] = []

        if not len(user_search_result[vk_event.user_id]):
            city_id = self.vk_search.method('database.getCities', {'country_id': 1,
                                                                   'q': user_search_params['city'],
                                                                   'count': 1})['items'][0]['id']

            user_search_response = self.vk_search.method('users.search',
                                                         {'birth_year': user_search_params['bdate'],
                                                          'sex': user_search_params['sex'],
                                                          'status': user_search_params['relation'],
                                                          'city': city_id,
                                                          'country': 1,
                                                          'count': 1000})
            for user in user_search_response['items']:
                user_in_like_table = self.db.get_like_user(int(vk_event.user_id), int(user['id']))
                user_in_dislike_table = self.db.get_dislike_user(int(vk_event.user_id), int(user['id']))
                user_in_match_table = self.db.check_matches(int(vk_event.user_id), int(user['id']))

                if user_in_like_table or user_in_dislike_table or user_in_match_table:
                    continue
                user_search_result[vk_event.user_id].append(user['id'])

            if not len(user_search_result[vk_event.user_id]):
                self.write_msg(vk_event.user_id, 'Новых анкет нет, повторите поиск позднее', self.menu_keyboard())
                return None

        data = vk_event.raw[6]['payload']
        if 'back_to_menu' in data:
            self.write_msg(vk_event.user_id, 'Начни поиск или измени параметры', self.menu_keyboard())
            return

        elif 'start_search_dislike' in data:
            data_to_db = database.DislikeTable(vk_user=int(vk_event.user_id),
                                               dislike_user=int(data[data.find(',') + 1:data.find(']')]))
            self.db.write_to_db(data_to_db)

        elif 'start_search_like' in data:
            data_to_db = database.LikeTable(vk_user=int(vk_event.user_id),
                                            like_user=int(data[data.find(',') + 1:data.find(']')]))
            self.db.write_to_db(data_to_db)
            self.db.like_move_to_match(vk_user=int(vk_event.user_id),
                                       like_user=int(data[data.find(',') + 1:data.find(']')]))

        for_grade = self.check_close_account(user_search_result[vk_event.user_id])

        if for_grade:
            user_for_grade_info = self.vk_search.method('users.get', {'user_ids': for_grade})
            user_for_grade_photo_response = self.vk_search.method('photos.get', {'owner_id': for_grade,
                                                                                 'album_id': 'profile',
                                                                                 'extended': 1})

            user_for_grade_photo_lib = dict()
            for photo in user_for_grade_photo_response['items']:
                rating = photo['comments']['count'] + photo['likes']['count']
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
                photo_for_attachment += f'photo{for_grade}_{photo}_{self.access_token},'

            photo_for_attachment = photo_for_attachment.rstrip(',')

            name_of_for_grade = f'{user_for_grade_info[0]["first_name"]}'

            message_variant = [f'Как тебе {name_of_for_grade}?',
                               f'Нравится {name_of_for_grade}?',
                               f'{name_of_for_grade} вроде ничего. Как думаешь?',
                               f'Может понравится {name_of_for_grade}?']

            self.vk.method('messages.send',
                           {'user_id': vk_event.user_id,
                            'message': message_variant[randrange(0, 3, 1)],
                            'random_id': randrange(10 ** 7),
                            'attachment': photo_for_attachment,
                            'keyboard': self.like_keyboard(for_grade)})
        else:
            self.write_msg(vk_event.user_id, 'Анкеты закончились, повторите поиск позднее', self.menu_keyboard())
            return

    def print_matches(self, vk_event):
        matches = self.db.get_matches(int(vk_event.user_id))
        if len(matches):
            match_string = ''
            for match in matches:
                user_for_grade_info = self.vk_search.method('users.get', {'user_ids': match.vk_user2})
                text = f'Образована пара с [id{match.vk_user2}|{user_for_grade_info[0]["first_name"]} ' \
                       f'{user_for_grade_info[0]["last_name"]}]\n'
                match_string += text
            self.write_msg(vk_event.user_id, match_string, self.matches_keyboard())

        else:
            self.write_msg(vk_event.user_id, 'Вы пока не образовали пары. Подождите, пока '
                                             'понравившееся вам пользователи лайкнут вас в ответ.',
                           self.matches_keyboard())
