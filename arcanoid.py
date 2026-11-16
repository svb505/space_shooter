import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import math
import customtkinter as ctk
import os
import sqlite3
from customtkinter import CTkLabel
from datetime import datetime
from tkinter import messagebox,colorchooser
import tabulate


x = [0.0,0.1,0.2,0.3]
y = [-0.9,-0.8]
step = 0.05
x1 = x[1]
y1 = y[1]
gunX = x1+step
gunY = y1+step
bullet_active = False
bulletX = 0
bulletY = 0
bullets = []
score = 0
asteroids = []
aster_speed = 0.005
target_update = 100
damage = 1
health = 2
WIDTH,HEIGHT = 700,700
game_over = False
name_db = "arkanoid_db.db"
levl = ""
logged = False
show = False
flag = False
coof = 0
score_sh = 0
stars = []
connected = False
check_record = False
ship_color = ()

def get_score(name):
    conn = sqlite3.connect(name_db)
    cursor = conn.cursor()
    row = cursor.execute("SELECT score FROM users WHERE name = ?",(name,)).fetchone()
    if row:
        return row
    else:
        return [0]
def conn_to_bd():
    conn = sqlite3.connect(name_db)
    cursor = conn.cursor()
    rows = cursor.execute("""SELECT name,score FROM users 
                                    ORDER by SCORE
                                    DESC
                                    LIMIT 10""").fetchall()
    return rows
def show_tournament():
    conn = sqlite3.connect(name_db)
    cursor = conn.cursor()
    rows = cursor.execute("""SELECT name,score FROM users 
            ORDER by SCORE
            DESC
            LIMIT 10""").fetchall()
    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title("Турнирная сетка")

    sc_width = app.winfo_screenwidth()
    sc_height = app.winfo_screenheight()
    xT = sc_width // 2
    yT = sc_height // 2
    app.resizable(False, False)
    app.geometry(f"450x450+{xT}+{yT}")

    frm = ctk.CTkFrame(app)
    frm.pack(fill = "both",expand = True)

    headers = ["Место", "Имя", "Очки"]
    for i, header in enumerate(headers):
        label = ctk.CTkLabel(frm, text=header, font=ctk.CTkFont(weight="bold"))
        label.grid(row=0, column=i, padx=10, pady=5)

    # Таблица данных
    for index, (name, score) in enumerate(rows):
        place = index + 1
        ctk.CTkLabel(frm, text=str(place)).grid(row=index + 1, column=0, padx=10, pady=2)
        ctk.CTkLabel(frm, text=name).grid(row=index + 1, column=1, padx=10, pady=2)
        ctk.CTkLabel(frm, text=str(score)).grid(row=index + 1, column=2, padx=10, pady=2)

    btn = ctk.CTkButton(app, text="OK", command=lambda: app.destroy())
    btn.pack()

    app.mainloop()
def save_score(name,score):
    global name_db
    conn = sqlite3.connect(name_db)
    cursor = conn.cursor()
    row = cursor.execute("SELECT name,score FROM users WHERE name = ?",(name,)).fetchone()
    if row:
        if int(row[1]) < score:
            cursor.execute("UPDATE users SET score = ? WHERE name = ?", (score, name))
    else:
        cursor.execute("INSERT INTO users(name,score) VALUES(?,?)",(name,score))
    conn.commit()
def logging(data):
    timestamp = datetime.now().strftime('%d_%m_%Y_%H:%M:%S')

    if os.path.exists("arc_log.txt"):
        with open('arc_log.txt',"a",encoding='utf-8') as f:
            f.write(f"{timestamp} - {data}\n")
    else:
        with open('arc_log.txt',"w",encoding='utf-8') as f:
            f.write(f"{timestamp} - {data}\n")
def main_func(name,score):
    global WIDTH, HEIGHT
    def generate_stars():
        global stars
        if len(stars) < 60:
            for i in range(30):
                stars.append([random.uniform(-1.0,1.0),random.uniform(-1.0,1.0)])
    def move_stars():
        global stars
        stars = [a for a in stars if a[1] > -1]
        if stars:
            for i in range(len(stars)):
                stars[i][1] -= 0.002
    def draw_stars():
        global stars
        glColor3f(1,1,1)
        glBegin(GL_POINTS)
        for i in range(len(stars)):
            glVertex(stars[i][0],stars[i][1])
        glEnd()
    def render_text(text, px, py, size=20, line_spacing=5,color = (255,0,0)):
        font = pygame.font.SysFont('Courier', size)

        # Разбиваем текст на строки по символу \n
        lines = text.split('\n')

        # Начальная позиция
        y_offset = 0

        for line in lines:
            # создаём прозрачную поверхность для каждой строки
            text_surface = font.render(line, True, color, (0, 0, 0, 0))
            text_surface = text_surface.convert_alpha()

            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            width, height = text_surface.get_size()

            # включаем прозрачность
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # Рисуем каждую строку с учётом смещения по y
            glWindowPos2f(px, py - y_offset)
            glDrawPixels(width, height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

            glDisable(GL_BLEND)

            # смещение для следующей строки
            y_offset += height + line_spacing
    def generate_asteroids():
        global asteroids, health,levl
        if len(asteroids) <= 10:
            if levl == "1":
                asteroids.append([random.random() * random.choice([-1, 1]), 1, health,0])
            else:
                asteroids.append([random.random()*random.choice([-1,1]), 1, health,
                                  random.choice([0,-0.001,0.001,0.005,-0.005])])
    def draw_asteroids():
        global asteroids
        for ax, ay, hp,vect in asteroids:
            radius = 0.02 + (hp * 0.005)
            glColor3f(0.5, 0.5, 0.5)  # красный цвет
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(ax, ay)
            for i in range(37):
                angle = math.radians(i * 10)
                glVertex2f(ax + radius * math.cos(angle), ay + radius * math.sin(angle))
            glEnd()
        glColor3f(1, 1, 1)  # вернуть цвет на белый
    def move_asteroids():
        global aster_speed, asteroids
        asteroids = [a for a in asteroids if a[1] > -1]
        if asteroids:
            for i in range(len(asteroids)):
                asteroids[i][1] -= aster_speed
                asteroids[i][0] -= asteroids[i][3]
    def init(wdt, hgh):
        pygame.init()
        display = (wdt, hgh)
        pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    def draw_ship(x, y):
        global shi_color
        if ship_color:
            glColor3f(*ship_color)  # голубой цвет заливки
        else:
            glColor3f(0.0, 0.5, 1.0)  # голубой цвет заливки
        glBegin(GL_POLYGON)
        glVertex2f(x[0], y[0])
        glVertex2f(x[1], y[1])
        glVertex2f(x[2], y[1])
        glVertex2f(x[3], y[0])
        glEnd()

        glColor3f(0.5, 0.5, 0.5)  # вернуть цвет на белый для контура
        glBegin(GL_LINE_LOOP)
        glVertex2f(x[0], y[0])
        glVertex2f(x[1], y[1])
        glVertex2f(x[2], y[1])
        glVertex2f(x[3], y[0])
        glEnd()
    def draw_gun():
        global y1, step, gunX, gunY
        glBegin(GL_LINE_LOOP)
        glVertex2f(gunX, y1)
        glVertex2f(gunX, gunY)
        glEnd()
    def shoot():
        global bullet_active, bulletX, bulletY, gunX, gunY, step, bullets
        bullets.append([gunX, gunY + step])
    def draw_bullet():
        global bullets
        new_bullets = []
        glColor3f(1.0, 0.5, 0.0)  # зелёный цвет
        for x, y in bullets:
            glBegin(GL_LINES)
            glVertex2f(x, y)
            glVertex2f(x, y + step)
            glEnd()
            y += 0.02
            if y <= 1:
                new_bullets.append([x, y])
        glColor3f(1, 1, 1)  # вернуть цвет
        bullets = new_bullets
    def check_ship_collision():
        global x, y, asteroids, game_over
        # Позиция корабля - прямоугольник между x[0]..x[3] по X и y[0]..y[1] по Y
        ship_left = x[0]
        ship_right = x[3]
        ship_bottom = y[0]
        ship_top = y[1]

        for asteroid in asteroids:
            ax, ay, hp,vect = asteroid
            radius = 0.02 + (hp * 0.005)

            # Проверяем пересечение круга астероида с прямоугольником корабля
            closest_x = max(ship_left, min(ax, ship_right))
            closest_y = max(ship_bottom, min(ay, ship_top))

            dist_x = ax - closest_x
            dist_y = ay - closest_y

            distance = math.sqrt(dist_x ** 2 + dist_y ** 2)
            if distance < radius:
                logging('[инфо] Столкновение с кораблём!')
                game_over = True  # остановим игру, например
    def handle_key(key):
        global x,y, x1, y1, gunX, gunY
        if key == K_LEFT:
            if x[0] > -1:
                for i in range(len(x)):
                    x[i] -= 0.05
        if key == K_RIGHT:
            if x[3] < 1:
                for i in range(len(x)):
                    x[i] += 0.05

        elif key == K_SPACE:
            shoot()
        draw_ship(x, y)
        x1 = x[1]
        y1 = y[1]
        gunX = x1 + step
        gunY = y1 + step
        draw_gun()
        draw_bullet()
    def check_collisions():
        global bullets, asteroids, score,damage,score_sh
        radius = 0.02

        new_bullets = []
        for bx, by in bullets:
            hit = False
            for asteroid in asteroids:
                ax, ay, hp,vect = asteroid
                dist = math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
                if dist < radius*2:
                    logging("[инфо] Попадание по астероиду")
                    asteroid[2] -= damage  # уменьшаем HP
                    hit = True
                    if asteroid[2] <= 0:
                        logging("[инфо] Уничтожен астероид")
                        score += 1
                    break
            if not hit:
                new_bullets.append([bx, by])
        count = [a for a in asteroids if a[1] <= -1]
        if count:
            score_sh += 1
        asteroids = [a for a in asteroids if a[2] > 0]
        bullets = new_bullets
    def restart():
        global asteroids, x,y, game_over, bullets, score, gunX, gunY,show
        if score_sh > 0:
            score -= score_sh // 10
        save_score(name, score)
        bullets.clear()
        asteroids.clear()
        show = False
        x = [0.0, 0.1, 0.2, 0.3]
        game_over = False
        score = 0
        x1 = x[1]
        y1 = y[1]
        gunX = x1 + step
        gunY = y1 + step
        main(WIDTH, HEIGHT)
    def main(wdt, hgh):
        logging(f"[инфо] Игра запущена")
        global x, y_step, target_update, score, running, game_over,show,logged,aster_speed,scored,flag,connected,check_record
        init(wdt, hgh)
        count = 0
        running = True
        tableX = WIDTH // 2 - 100
        tableY = 0
        timetick = 0
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_score(name,score)
                    logging(f"[инфо] Выход из игры")
                    running = False
                elif event.type == KEYDOWN:
                    handle_key(event.key)
                    if event.key == pygame.K_r:
                        logging(f"[инфо] Рестарт из игры")
                        restart()
                    elif event.key == pygame.K_e:
                        logging(f"[инфо] Выход из игры")
                        save_score(name, score)
                        running = False
            if game_over:
                timetick += 1
                if not connected:
                    if score_sh > 0:
                        score -= score_sh // 10
                    save_score(name, score)
                    rows = conn_to_bd()
                    connected = True
                if not logged:
                    logging(f"[инфо] Очки: {score}")
                    logging(f"[инфо] Игры окончена")
                    logged = True
                if not show:
                    show_tournament()
                    show = True

                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                render_text(f"Игра окончена. Всего очков(с вычетом штрафа): {score}", WIDTH // 2 - 250, HEIGHT - 25,color = (0,255,0))
                if timetick % 5 == 0:
                    render_text(f"R - Рестарт | E - Выход", WIDTH // 2 - 250, HEIGHT - 45,color = (0,255,0))
                else:
                    render_text(f"R - Рестарт | E - Выход", WIDTH // 2 - 250, HEIGHT - 45, color=(255, 255, 255))
                table = tabulate.tabulate(rows, ["Имя", "Счет"])
                render_text(table,tableX,tableY)
                if tableY < HEIGHT - 75:
                    tableY += 10
                pygame.display.flip()
                pygame.time.wait(100)
            else:
                # Очистка экрана
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                draw_ship(x, y)
                draw_gun()
                draw_bullet()
                if count % target_update == 0:
                    generate_asteroids()
                if score % coof == 0:
                    aster_speed += 0.001
                    score += 1
                generate_stars()
                draw_stars()
                move_stars()
                move_asteroids()
                draw_asteroids()
                check_collisions()
                check_ship_collision()
                if not check_record:
                    user_record = get_score(name)[0]
                    check_record = True
                render_text(f"Привет {name}, ваш рекорд: {user_record}", 10, HEIGHT - 30, color=(255, 255, 255))
                render_text(f"Очки: {score}", 10, HEIGHT - 50,color = (0,255,0))
                render_text(f"Пропущеные цели: {score_sh}", 10, HEIGHT - 70)
                render_text('©Developped by Sergiy Bagach,Sviatoslav Bulygin', 10, 0,color=(255, 255, 255))
                glLoadIdentity()
                pygame.display.flip()
                pygame.time.wait(10)
                count += 1

        pygame.quit()
    main(WIDTH, HEIGHT)
def start():
    def settings():
        def choose_color():
            global ship_color
            color_code = colorchooser.askcolor(title="Выберите цвет")
            ship_color = color_code[0]
        sett_w = ctk.CTkToplevel(app)
        sett_w.geometry("300x200")
        sett_w.resizable(False,False)
        sett_w.title("Настройки")

        button = ctk.CTkButton(sett_w, text="Выбрать цвет корабля", command=choose_color)
        button.pack(pady=20)

    def on_submit(level,name):
        def insert_to_db(name):
            conn = sqlite3.connect(name_db)
            cursor = conn.cursor()
            row = cursor.execute("SELECT name FROM users WHERE name = ?",(name,)).fetchone()
            if not row:
                cursor.execute("INSERT INTO users(name,score) VALUES(?,?)",(name,0))
        def set_info(lvl,name):
            global health,target_update,aster_speed,levl,coof
            logging(f"[инфо] Выбран {lvl} уровень")
            if lvl == "1":
                health = 1
                target_update = 200
                aster_speed = 0.001
                coof = 4
            if lvl == "2":
                health = 2
                target_update = 100
                aster_speed = 0.003
                coof = 7
            if lvl == "3":
                health = 3
                target_update = 60
                aster_speed = 0.006
                coof = 10
            levl = lvl
            insert_to_db(name)
            app.destroy()
            main_func(name,0)
        set_info(level,name)
    def set_info(lvl):
        mes = ""
        if lvl == "1":
            mes = "Уровень 1\nЗдоровье астероидов: 1\n Скорость астероидов: низкая\nКол-во очков для увеличения скорости: 4"
        if lvl == "2":
            mes = "Уровень 2\nЗдоровье астероидов: 2\n Скорость астероидов: средняя\nКол-во очков для увеличения скорости: 7"
        if lvl == "3":
            mes = "Уровень 3\nЗдоровье астероидов: 3\n Скорость астероидов: высокая\nКол-во очков для увеличения скорости: 10"
        label.configure(frm,text = mes)
    global name_db
    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title("Вход")

    sc_width = app.winfo_screenwidth()
    sc_height = app.winfo_screenheight()
    x = sc_width // 2
    y = sc_height // 2
    app.resizable(False,False)
    app.geometry(f"350x350+{x}+{y}")

    user_name = ""

    if os.path.exists(name_db):
        conn = sqlite3.connect(name_db)
        cursor = conn.cursor()
        row = cursor.execute('SELECT name FROM users WHERE id = ?',(1,)).fetchone()
        if row:
            print(row)
            user_name = row[0]
        else:
            user_name = "Player"
        conn.close()
    else:
        conn = sqlite3.connect(name_db)
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE users (
            [id] INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL
                    UNIQUE,
            score   INTEGER NOT NULL
            );""")
        conn.commit()
        conn.close()

    lbl = ctk.CTkLabel(app, text="Введите имя")
    lbl.pack()

    name = ctk.CTkEntry(app, placeholder_text="Введите имя", width=100)
    name.pack(pady=20)
    name.insert(0,user_name)

    lbl = ctk.CTkLabel(app,text = "Выберите уровень(1-Легкий. 2-Средний. 3-Сложный)")
    lbl.pack()

    level = ctk.CTkComboBox(app,values = ["1","2","3"],command=lambda event:set_info(level.get()))
    level.pack(pady=20)
    level.configure(state="readonly")

    frm = ctk.CTkFrame(app)
    frm.pack(fill = "x")

    label = CTkLabel(frm,text = "")
    label.pack()

    set_info(level.get())

    btn = ctk.CTkButton(app, text="OK", command=lambda:on_submit(level.get(),name.get()))
    btn.pack()
    btn1 = ctk.CTkButton(app, text="Настройки", command=settings,fg_color="#808080",
    hover_color="#696969")
    btn1.pack()

    app.mainloop()

if __name__ == "__main__":
    start()