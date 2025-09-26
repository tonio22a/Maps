import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import warnings
import cartopy
warnings.filterwarnings('ignore', category=cartopy.io.DownloadWarning)


class DB_Map():
    def __init__(self, database):
        self.database = database
    
    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()

    def add_city(self,user_id, city_name ):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]  
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0

            
    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))

            cities = [row[0] for row in cursor.fetchall()]
            return cities


    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates

    def create_graph(self, path, cities):
        # Отключаем предупреждения о загрузке
        import warnings
        warnings.filterwarnings('ignore')
        
        # Создаем карту
        fig = plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        
        # Простой стиль карты без скачивания данных
        ax.stock_img()  # Используем встроенное изображение Земли
        ax.coastlines()  # Только береговая линия
        
        # Собираем координаты всех городов
        lats = []
        lons = []
        city_coords = []
        
        for city_name in cities:
            coords = self.get_coordinates(city_name)
            if coords:
                lat, lon = coords
                lats.append(lat)
                lons.append(lon)
                city_coords.append((city_name, lat, lon))
        
        if not city_coords:
            return None
        
        # Устанавливаем границы карты с запасом вокруг городов
        margin = 10  # градусы
        ax.set_extent([
            min(lons) - margin, 
            max(lons) + margin, 
            min(lats) - margin, 
            max(lats) + margin
        ], crs=ccrs.PlateCarree())
        
        # Отмечаем города на карте
        for city_name, lat, lon in city_coords:
            ax.plot(lon, lat, 'ro', markersize=8, transform=ccrs.PlateCarree())
            ax.text(lon + 1, lat, city_name, transform=ccrs.PlateCarree(), 
                fontsize=10, fontweight='bold', color='red')
        
        # Добавляем сетку
        ax.gridlines(draw_labels=True, color='gray', alpha=0.5)
        
        # Сохраняем карту
        plt.title('Карта городов', fontsize=16)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return path


if __name__=="__main__":
    
    m = DB_Map(DATABASE)
    m.create_user_table()