import telebot
from config import *
from logic import *
import os
import tempfile

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я бот, который может показывать города на карте. Напиши /help для списка команд.")

@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id, '''
Доступные команды: \n
- /start - начать работу с ботом и получить приветственное сообщение.
- /help - получить список доступных команд.
- /show_city <city_name> - отобразить указанный город на карте.
- /remember_city <city_name> - сохранить город в список избранных.
- /show_my_cities - показать все сохраненные города.
                     ''')
    

@bot.message_handler(commands=['show_city'])
def handle_show_city(message):
    try:
        # Получаем название города из команды
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Пожалуйста, укажите название города после команды: /show_city London")
            return
        
        city_name = ' '.join(parts[1:])
        
        # Проверяем существование города в базе
        coords = manager.get_coordinates(city_name)
        if not coords:
            bot.send_message(message.chat.id, 'Такого города я не знаю. Убедись, что он написан на английском!')
            return
        
        # Создаем временный файл для карты
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Создаем карту с одним городом
        manager.create_graph(temp_path, [city_name])
        
        # Отправляем карту пользователю
        with open(temp_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f'Город: {city_name}')
        
        # Удаляем временный файл
        os.unlink(temp_path)
        
    except Exception as e:
        bot.send_message(message.chat.id, 'Произошла ошибка при создании карты. Попробуйте еще раз.')
        print(f"Error in show_city: {e}")


@bot.message_handler(commands=['remember_city'])
def handle_remember_city(message):
    user_id = message.chat.id
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Пожалуйста, укажите название города после команды: /remember_city London")
        return
    
    city_name = ' '.join(parts[1:])
    if manager.add_city(user_id, city_name):
        bot.send_message(message.chat.id, f'Город {city_name} успешно сохранен!')
    else:
        bot.send_message(message.chat.id, 'Такого города я не знаю. Убедись, что он написан на английском!')


@bot.message_handler(commands=['show_my_cities'])
def handle_show_visited_cities(message):
    try:
        cities = manager.select_cities(message.chat.id)
        
        if not cities:
            bot.send_message(message.chat.id, 'У вас пока нет сохраненных городов. Используйте /remember_city чтобы добавить город.')
            return
        
        # Создаем временный файл для карты
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Создаем карту со всеми городами пользователя
        manager.create_graph(temp_path, cities)
        
        # Отправляем карту пользователю
        with open(temp_path, 'rb') as photo:
            cities_list = "\n".join([f"• {city}" for city in cities])
            caption = f"Ваши сохраненные города:\n{cities_list}"
            bot.send_photo(message.chat.id, photo, caption=caption)
        
        # Удаляем временный файл
        os.unlink(temp_path)
        
    except Exception as e:
        bot.send_message(message.chat.id, 'Произошла ошибка при создании карты. Попробуйте еще раз.')
        print(f"Error in show_my_cities: {e}")


if __name__=="__main__":
    manager = DB_Map(DATABASE)
    bot.polling()