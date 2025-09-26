import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import warnings
import os

warnings.filterwarnings('ignore')

class DB_Map():
    def __init__(self, database):
        self.database = database
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных при первом запуске"""
        # Проверяем существует ли файл базы данных
        if not os.path.exists(self.database):
            print("База данных не найдена, создаем новую...")
            self.create_database()
    
    def create_database(self):
        """Создает базу данных с необходимой структурой"""
        conn = sqlite3.connect(self.database)
        with conn:
            # Создаем таблицу пользователей и городов
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                city_id TEXT NOT NULL,
                                marker_color TEXT DEFAULT 'red',
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(user_id, city_id)
                            )''')
            
            # Создаем индекс для быстрого поиска
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_user_id 
                          ON users_cities(user_id)''')
            conn.commit()
        print("База данных создана успешно")

    def create_user_table(self):
        """Создает таблицу для пользователей (обратная совместимость)"""
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                city_id TEXT NOT NULL,
                                marker_color TEXT DEFAULT 'red',
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(user_id, city_id)
                            )''')
            conn.commit()
        print("Таблица users_cities готова")

    def add_city(self, user_id, city_name, marker_color='red'):
        """Добавляет город для пользователя"""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            
            # Ищем город в базе (пробуем разные варианты написания)
            search_variants = [
                city_name,
                city_name.title(),
                city_name.upper(),
                city_name.lower()
            ]
            
            city_id = None
            found_city = None
            
            for variant in search_variants:
                cursor.execute("SELECT id, city FROM cities WHERE city=?", (variant,))
                result = cursor.fetchone()
                if result:
                    city_id, found_city = result
                    break
            
            if city_id:
                # Проверяем, не добавлен ли уже город
                cursor.execute('''SELECT id FROM users_cities 
                               WHERE user_id=? AND city_id=?''', (user_id, city_id))
                existing = cursor.fetchone()
                
                if existing:
                    # Обновляем цвет если город уже есть
                    cursor.execute('''UPDATE users_cities SET marker_color=?
                                   WHERE user_id=? AND city_id=?''',
                                   (marker_color, user_id, city_id))
                    conn.commit()
                    return 1, found_city
                else:
                    # Добавляем новый город
                    cursor.execute('''INSERT INTO users_cities (user_id, city_id, marker_color)
                                   VALUES (?, ?, ?)''', (user_id, city_id, marker_color))
                    conn.commit()
                    return 1, found_city
            else:
                return 0, None

    def set_marker_color(self, user_id, city_name, color):
        """Устанавливает цвет маркера для города пользователя"""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            
            # Находим city_id по названию города
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            
            if city_data:
                city_id = city_data[0]
                cursor.execute('''UPDATE users_cities SET marker_color=?
                               WHERE user_id=? AND city_id=?''',
                               (color, user_id, city_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return True
                else:
                    # Если запись не найдена, создаем ее
                    cursor.execute('''INSERT INTO users_cities (user_id, city_id, marker_color)
                                   VALUES (?, ?, ?)''', (user_id, city_id, color))
                    conn.commit()
                    return True
            return False

    def get_cities_with_colors(self, user_id):
        """Возвращает список городов пользователя с цветами"""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city, users_cities.marker_color 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?
                            ORDER BY users_cities.created_at DESC''', (user_id,))
            return cursor.fetchall()

    def select_cities(self, user_id):
        """Возвращает список городов пользователя (обратная совместимость)"""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))
            return [row[0] for row in cursor.fetchall()]

    def get_coordinates(self, city_name):
        """Возвращает координаты города"""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng FROM cities WHERE city = ?''', (city_name,))
            return cursor.fetchone()

    def find_city_variants(self, city_name):
        """Поиск похожих названий городов"""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT city FROM cities 
                            WHERE city LIKE ? 
                            OR city LIKE ?
                            OR city LIKE ?
                            LIMIT 15''', 
                          (f'%{city_name}%', f'{city_name}%', f'%{city_name}'))
            return [row[0] for row in cursor.fetchall()]

    def remove_city(self, user_id, city_name):
        """Удаляет город из списка пользователя"""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT id FROM cities WHERE city=?''', (city_name,))
            city_data = cursor.fetchone()
            
            if city_data:
                city_id = city_data[0]
                cursor.execute('''DELETE FROM users_cities 
                               WHERE user_id=? AND city_id=?''', (user_id, city_id))
                conn.commit()
                return cursor.rowcount > 0
            return False

    def get_user_stats(self, user_id):
        """Возвращает статистику пользователя"""
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT COUNT(*) FROM users_cities WHERE user_id=?''', (user_id,))
            total_cities = cursor.fetchone()[0]
            
            cursor.execute('''SELECT COUNT(DISTINCT marker_color) 
                            FROM users_cities WHERE user_id=?''', (user_id,))
            unique_colors = cursor.fetchone()[0]
            
            return {
                'total_cities': total_cities,
                'unique_colors': unique_colors
            }

    def create_graph(self, path, cities_data, map_style='detailed'):
        """Создает карту с городами"""
        try:
            # Создаем карту
            fig = plt.figure(figsize=(14, 10))
            ax = plt.axes(projection=ccrs.PlateCarree())
            
            # Разные стили карты
            if map_style == 'detailed':
                # Детальная карта с заливкой
                ax.add_feature(cfeature.LAND, color='#f5f5f5', alpha=0.9)
                ax.add_feature(cfeature.OCEAN, color='#e0f0ff', alpha=0.9)
                ax.add_feature(cfeature.COASTLINE, linewidth=0.8, color='#333333')
                ax.add_feature(cfeature.BORDERS, linestyle='--', linewidth=0.5, color='#666666')
                ax.add_feature(cfeature.LAKES, color='#e0f0ff', alpha=0.7)
                ax.add_feature(cfeature.RIVERS, color='#e0f0ff', linewidth=0.5)
                
            elif map_style == 'physical':
                # Физическая карта
                ax.stock_img()
                ax.add_feature(cfeature.COASTLINE, linewidth=1.2, color='#333333')
                ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.7, color='#555555')
                
            else:  # simple
                # Простая карта
                ax.add_feature(cfeature.COASTLINE, linewidth=1, color='#000000')
                ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.7, color='#444444')

            # Собираем координаты и цвета
            lats, lons = [], []
            city_coords = []
            
            for city_item in cities_data:
                if isinstance(city_item, tuple):
                    city_name, color = city_item
                else:
                    city_name, color = city_item, 'red'
                
                coords = self.get_coordinates(city_name)
                if coords:
                    lat, lon = coords
                    lats.append(lat)
                    lons.append(lon)
                    city_coords.append((city_name, lat, lon, color))

            if not city_coords:
                print("Нет координат для отображения")
                return None

            # Устанавливаем границы карты
            if len(city_coords) == 1:
                # Для одного города - фиксированный масштаб
                lat, lon = city_coords[0][1], city_coords[0][2]
                margin = 8
                ax.set_extent([lon - margin, lon + margin, lat - margin, lat + margin], 
                             crs=ccrs.PlateCarree())
            else:
                # Для нескольких городов - адаптивный масштаб
                margin = 15
                ax.set_extent([
                    min(lons) - margin, max(lons) + margin,
                    min(lats) - margin, max(lats) + margin
                ], crs=ccrs.PlateCarree())

            # Отмечаем города
            for city_name, lat, lon, color in city_coords:
                ax.plot(lon, lat, 'o', markersize=14, color=color, 
                       transform=ccrs.PlateCarree(), markeredgecolor='black', 
                       markeredgewidth=2, alpha=0.8)
                ax.text(lon + 0.8, lat + 0.5, city_name, transform=ccrs.PlateCarree(),
                       fontsize=10, fontweight='bold', 
                       bbox=dict(boxstyle="round,pad=0.4", facecolor='white', 
                               alpha=0.9, edgecolor='gray'))

            # Сетка
            gl = ax.gridlines(draw_labels=True, alpha=0.3, linestyle='--')
            gl.top_labels = False
            gl.right_labels = False

            plt.title('🗺️ Карта городов', fontsize=18, fontweight='bold', pad=20)
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"Карта успешно создана: {path}")
            return path
            
        except Exception as e:
            print(f"Ошибка в create_graph: {e}")
            return None

    def draw_distance(self, city1, city2, path):
        """Рисует линию между двумя городами"""
        try:
            coords1 = self.get_coordinates(city1)
            coords2 = self.get_coordinates(city2)
            
            if not coords1 or not coords2:
                return None

            fig = plt.figure(figsize=(12, 8))
            ax = plt.axes(projection=ccrs.PlateCarree())
            ax.stock_img()
            
            lat1, lon1 = coords1
            lat2, lon2 = coords2
            
            # Рисуем линию расстояния
            ax.plot([lon1, lon2], [lat1, lat2], 'r-', linewidth=3, 
                   transform=ccrs.Geodetic(), alpha=0.7)
            ax.plot(lon1, lat1, 'o', markersize=12, color='red', 
                   transform=ccrs.PlateCarree(), markeredgecolor='black', markeredgewidth=2)
            ax.plot(lon2, lat2, 'o', markersize=12, color='blue', 
                   transform=ccrs.PlateCarree(), markeredgecolor='black', markeredgewidth=2)
            
            # Подписи городов
            ax.text(lon1, lat1 + 1.5, city1, transform=ccrs.PlateCarree(),
                   fontweight='bold', ha='center', fontsize=11,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
            ax.text(lon2, lat2 + 1.5, city2, transform=ccrs.PlateCarree(),
                   fontweight='bold', ha='center', fontsize=11,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
            
            plt.title(f'📏 Расстояние: {city1} - {city2}', fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return path
            
        except Exception as e:
            print(f"Ошибка в draw_distance: {e}")
            return None


if __name__=="__main__":
    # Тестирование класса
    m = DB_Map(DATABASE)
    m.create_user_table()
    print("✅ Класс DB_Map протестирован успешно")