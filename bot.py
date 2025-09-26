import telebot
from config import *
from logic import *
import os
import tempfile
from datetime import datetime

bot = telebot.TeleBot(TOKEN)

# Доступные цвета маркеров
AVAILABLE_COLORS = {
    'red': '🔴 Красный',
    'blue': '🔵 Синий', 
    'green': '🟢 Зеленый',
    'yellow': '🟡 Желтый',
    'purple': '🟣 Фиолетовый',
    'orange': '🟠 Оранжевый',
    'pink': '🌸 Розовый',
    'brown': '🟤 Коричневый',
    'black': '⚫ Черный',
    'white': '⚪ Белый'
}

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    first_name = message.chat.first_name or "Пользователь"
    
    welcome_text = f"""
🗺️ Добро пожаловать, {first_name}!

Я - бот для создания персональных карт городов! 🌍

✨ Что я умею:
• Сохранять ваши любимые города
• Показывать их на красивых картах
• Изменять цвета маркеров
• Показывать расстояния между городами

🚀 Начните с этих команд:
/remember_city London - добавить город
/show_my_cities - посмотреть ваши города
/map_detailed - создать карту

💡 Используйте /help для полного списка команд
"""
    
    bot.send_message(user_id, welcome_text)
    
    # Создаем таблицу если нужно
    manager.create_user_table()

@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = """
🗺️ ПОЛНЫЙ СПИСОК КОМАНД:

📍 ОСНОВНЫЕ КОМАНДЫ:
/start - начать работу
/help - показать все команды
/my_stats - моя статистика

🏙️ РАБОТА С ГОРОДАМИ:
/remember_city <город> - добавить город
/forget_city <город> - удалить город
/show_my_cities - мои сохраненные города
/search_city <название> - поиск города

🎨 ВНЕШНИЙ ВИД:
/set_color <город> <цвет> - изменить цвет маркера
/colors - доступные цвета

🗾 ТИПЫ КАРТ:
/map_simple - простая карта
/map_detailed - детальная карта
/map_physical - физическая карта

📏 ДОПОЛНИТЕЛЬНО:
/show_city <город> - показать один город
/distance <город1> <город2> - расстояние

📝 ПРИМЕРЫ:
/remember_city London
/set_color London blue
/map_detailed
/forget_city Paris
/my_stats
"""
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['my_stats'])
def handle_my_stats(message):
    try:
        user_id = message.chat.id
        stats = manager.get_user_stats(user_id)
        cities_data = manager.get_cities_with_colors(user_id)
        
        if stats['total_cities'] == 0:
            bot.send_message(user_id, 
                "📊 ВАША СТАТИСТИКА:\n\n"
                "🏙️ Сохраненных городов: 0\n\n"
                "💡 Добавьте первый город:\n"
                "/remember_city London")
            return
        
        # Создаем красивую статистику
        stats_text = f"📊 СТАТИСТИКА ДЛЯ {message.chat.first_name or 'Пользователя'}:\n\n"
        stats_text += f"🏙️ Сохраненных городов: {stats['total_cities']}\n"
        stats_text += f"🎨 Использовано цветов: {stats['unique_colors']}\n\n"
        
        # Статистика по цветам
        color_stats = {}
        for city, color in cities_data:
            color_stats[color] = color_stats.get(color, 0) + 1
        
        stats_text += "🎨 РАСПРЕДЕЛЕНИЕ ПО ЦВЕТАМ:\n"
        for color, count in color_stats.items():
            color_name = AVAILABLE_COLORS.get(color, color)
            stats_text += f"• {color_name}: {count} городов\n"
        
        bot.send_message(user_id, stats_text)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка получения статистики: {str(e)}")

@bot.message_handler(commands=['colors'])
def handle_colors(message):
    colors_text = "🎨 ДОСТУПНЫЕ ЦВЕТА МАРКЕРОВ:\n\n"
    for color_key, color_desc in AVAILABLE_COLORS.items():
        colors_text += f"{color_desc} - /set_color город {color_key}\n"
    
    colors_text += "\n📝 ПРИМЕРЫ:\n"
    colors_text += "/set_color London blue\n"
    colors_text += "/set_color Paris red\n"
    colors_text += "/set_color Tokyo green"
    
    bot.send_message(message.chat.id, colors_text)

@bot.message_handler(commands=['set_color'])
def handle_set_color(message):
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, 
                "❌ НЕПРАВИЛЬНЫЙ ФОРМАТ\n\n"
                "📝 Правильно: /set_color <город> <цвет>\n\n"
                "🔹 Примеры:\n"
                "/set_color London blue\n"
                "/set_color New York red\n\n"
                "🎨 Цвета: /colors")
            return
        
        city_name = parts[1]
        color = parts[2].lower()
        
        if color not in AVAILABLE_COLORS:
            error_text = f"❌ ЦВЕТ '{color}' НЕ ПОДДЕРЖИВАЕТСЯ\n\n"
            error_text += "🎨 Доступные цвета:\n"
            for color_key, color_desc in AVAILABLE_COLORS.items():
                error_text += f"• {color_key} - {color_desc}\n"
            bot.send_message(message.chat.id, error_text)
            return
            
        success = manager.set_marker_color(message.chat.id, city_name, color)
        if success:
            bot.send_message(message.chat.id, 
                f"✅ ЦВЕТ ИЗМЕНЕН!\n\n"
                f"🏙️ Город: {city_name}\n"
                f"🎨 Цвет: {AVAILABLE_COLORS[color]}")
        else:
            bot.send_message(message.chat.id, 
                f"❌ Не удалось изменить цвет.\n"
                f"Убедитесь, что город '{city_name}' сохранен.\n\n"
                f"💡 Сначала добавьте город:\n"
                f"/remember_city {city_name}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['map_simple', 'map_detailed', 'map_physical'])
def handle_map_style(message):
    try:
        command = message.text.split()[0]
        style = command.replace('/map_', '')
        user_id = message.chat.id
        
        cities_data = manager.get_cities_with_colors(user_id)
        
        if not cities_data:
            bot.send_message(message.chat.id, 
                "❌ У ВАС НЕТ СОХРАНЕННЫХ ГОРОДОВ\n\n"
                "💡 Добавьте первый город:\n"
                "/remember_city London\n"
                "/remember_city Paris\n"
                "/remember_city Tokyo")
            return
            
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        bot.send_message(user_id, "🔄 Создаю вашу персональную карту...")
        result = manager.create_graph(temp_path, cities_data, style)
        
        if not result:
            bot.send_message(user_id, "❌ Ошибка при создании карты")
            return
            
        style_names = {
            'simple': '🗺️ ПРОСТАЯ КАРТА',
            'detailed': '🗾 ДЕТАЛЬНАЯ КАРТА', 
            'physical': '⛰️ ФИЗИЧЕСКАЯ КАРТА'
        }
        
        with open(temp_path, 'rb') as photo:
            caption = f"{style_names.get(style, 'КАРТА')}\n"
            caption += f"👤 Пользователь: {message.chat.first_name or 'Аноним'}\n"
            caption += f"🏙️ Городов: {len(cities_data)}\n"
            caption += f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            bot.send_photo(user_id, photo, caption=caption)
        
        os.unlink(temp_path)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['remember_city'])
def handle_remember_city(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, 
                "❌ НЕПРАВИЛЬНЫЙ ФОРМАТ\n\n"
                "📝 Правильно: /remember_city <город>\n\n"
                "🔹 Примеры:\n"
                "/remember_city London\n"
                "/remember_city New York\n"
                "/remember_city Tokyo")
            return
        
        city_name = ' '.join(parts[1:])
        user_id = message.chat.id
        
        success, found_city = manager.add_city(user_id, city_name)
        
        if success == 1:
            bot.send_message(user_id, 
                f"✅ ГОРОД ДОБАВЛЕН!\n\n"
                f"🏙️ Город: {found_city or city_name}\n"
                f"🎨 Цвет: 🔴 Красный (по умолчанию)\n\n"
                f"💡 Изменить цвет:\n"
                f"/set_color {found_city or city_name} <цвет>\n\n"
                f"🗺️ Посмотреть карту:\n"
                f"/map_detailed")
        else:
            similar_cities = manager.find_city_variants(city_name)
            if similar_cities:
                cities_list = "\n".join([f"• {city}" for city in similar_cities[:5]])
                bot.send_message(user_id, 
                    f"❌ ГОРОД НЕ НАЙДЕН\n\n"
                    f"🔍 Возможно вы имели в виду:\n{cities_list}\n\n"
                    f"💡 Убедитесь в правильности написания на английском")
            else:
                bot.send_message(user_id, 
                    f"❌ ГОРОД '{city_name}' НЕ НАЙДЕН\n\n"
                    f"💡 Попробуйте:\n"
                    f"• Проверить написание\n"
                    f"• Использовать английское название\n"
                    f"• Поискать похожие города:\n"
                    f"/search_city {city_name}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['forget_city'])
def handle_forget_city(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, 
                "❌ НЕПРАВИЛЬНЫЙ ФОРМАТ\n\n"
                "📝 Правильно: /forget_city <город>\n\n"
                "🔹 Пример:\n"
                "/forget_city London")
            return
        
        city_name = ' '.join(parts[1:])
        user_id = message.chat.id
        
        success = manager.remove_city(user_id, city_name)
        
        if success:
            bot.send_message(user_id, 
                f"✅ ГОРОД УДАЛЕН!\n\n"
                f"🏙️ Город: {city_name}\n"
                f"💡 Текущие города: /show_my_cities")
        else:
            bot.send_message(user_id, 
                f"❌ ГОРОД НЕ НАЙДЕН\n\n"
                f"Убедитесь, что город '{city_name}' был сохранен.\n"
                f"💡 Ваши города: /show_my_cities")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['show_my_cities'])
def handle_show_my_cities(message):
    try:
        user_id = message.chat.id
        cities_data = manager.get_cities_with_colors(user_id)
        
        if not cities_data:
            bot.send_message(user_id, 
                "❌ У ВАС НЕТ СОХРАНЕННЫХ ГОРОДОВ\n\n"
                "💡 Добавьте первый город:\n"
                "/remember_city London")
            return
            
        cities_list = "\n".join([f"🏙️ {city} - {AVAILABLE_COLORS.get(color, color)}" 
                               for city, color in cities_data])
        
        bot.send_message(user_id, 
            f"🗺️ ВАШИ СОХРАНЕННЫЕ ГОРОДА:\n\n{cities_list}\n\n"
            f"💡 КОМАНДЫ:\n"
            f"/map_detailed - показать на карте\n"
            f"/forget_city <город> - удалить город\n"
            f"/my_stats - статистика")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['show_city'])
def handle_show_city(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, 
                "❌ НЕПРАВИЛЬНЫЙ ФОРМАТ\n\n"
                "📝 Правильно: /show_city <город>\n\n"
                "🔹 Пример:\n"
                "/show_city London")
            return
        
        city_name = ' '.join(parts[1:])
        user_id = message.chat.id
        
        coords = manager.get_coordinates(city_name)
        if not coords:
            bot.send_message(user_id, 
                f"❌ ГОРОД НЕ НАЙДЕН\n\n"
                f"💡 Попробуйте:\n"
                f"/search_city {city_name}")
            return
            
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        bot.send_message(user_id, "🔄 Создаю карту...")
        result = manager.create_graph(temp_path, [city_name], 'detailed')
        
        if result:
            with open(temp_path, 'rb') as photo:
                bot.send_photo(user_id, photo, 
                              caption=f"🏙️ {city_name}\n"
                                      f"📍 Широта: {coords[0]:.4f}°\n"
                                      f"📍 Долгота: {coords[1]:.4f}°\n\n"
                                      f"💡 Сохранить город:\n"
                                      f"/remember_city {city_name}")
        else:
            bot.send_message(user_id, "❌ Ошибка при создании карты")
        
        os.unlink(temp_path)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['search_city'])
def handle_search_city(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, 
                "❌ НЕПРАВИЛЬНЫЙ ФОРМАТ\n\n"
                "📝 Правильно: /search_city <название>\n\n"
                "🔹 Примеры:\n"
                "/search_city Mos\n"
                "/search_city New\n"
                "/search_city York")
            return
        
        search_term = ' '.join(parts[1:])
        similar_cities = manager.find_city_variants(search_term)
        
        if similar_cities:
            cities_list = "\n".join([f"• {city}" for city in similar_cities[:10]])
            bot.send_message(message.chat.id, 
                f"🔍 РЕЗУЛЬТАТЫ ПОИСКА:\n\n{cities_list}\n\n"
                f"💡 Добавить город:\n"
                f"/remember_city <название>")
        else:
            bot.send_message(message.chat.id, 
                f"❌ НИЧЕГО НЕ НАЙДЕНО\n\n"
                f"По запросу '{search_term}' нет результатов.\n"
                f"💡 Проверьте написание.")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['distance'])
def handle_distance(message):
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, 
                "❌ НЕПРАВИЛЬНЫЙ ФОРМАТ\n\n"
                "📝 Правильно: /distance <город1> <город2>\n\n"
                "🔹 Пример:\n"
                "/distance London Paris")
            return
            
        city1, city2 = parts[1], parts[2]
        user_id = message.chat.id
        
        coords1 = manager.get_coordinates(city1)
        coords2 = manager.get_coordinates(city2)
        
        if not coords1 or not coords2:
            missing = []
            if not coords1: missing.append(city1)
            if not coords2: missing.append(city2)
            bot.send_message(user_id, 
                f"❌ ГОРОДА НЕ НАЙДЕНЫ: {', '.join(missing)}\n\n"
                f"💡 Используйте: /search_city <название>")
            return
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        bot.send_message(user_id, "🔄 Рассчитываю расстояние...")
        if manager.draw_distance(city1, city2, temp_path):
            with open(temp_path, 'rb') as photo:
                bot.send_photo(user_id, photo, 
                              caption=f"📏 РАССТОЯНИЕ\n\n"
                                      f"🏙️ {city1} → {city2}\n"
                                      f"📍 Рассчитано по координатам")
        else:
            bot.send_message(user_id, "❌ Ошибка при создании карты")
        
        os.unlink(temp_path)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

# Обработчик для любых текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    bot.send_message(message.chat.id,
        "❌ НЕИЗВЕСТНАЯ КОМАНДА\n\n"
        "💡 Используйте /help для просмотра всех команд\n"
        "🔹 Или начните с /start")

if __name__ == "__main__":
    print("🔄 Запуск бота для всех пользователей...")
    print("🗃️ Инициализация базы данных...")
    manager = DB_Map(DATABASE)
    manager.create_user_table()
    print("✅ База данных готова")
    print("👥 Бот доступен для ВСЕХ пользователей!")
    print("🚀 Запускаю polling...")
    bot.polling()