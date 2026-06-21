from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner 
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import Clock
import random, os
import threading
import urllib.request  
import json            

import arabic_reshaper
from bidi.algorithm import get_display

Window.size = (450, 750)
Window.clearcolor = (0.04, 0.04, 0.12, 1)

FILE = "words.txt"
SCORE_FILE = "highscore.txt"
ARABIC_FONT = "C:\\Windows\\Fonts\\arial.ttf" 

DEFAULT_WORDS = [
    {"q": "House", "a": "Maison"},
    {"q": "Book", "a": "Livre"},
    {"q": "Car", "a": "Voiture"},
    {"q": "Cat", "a": "Chat"},
    {"q": "Dog", "a": "Chien"}
]

LANGUAGES = {
    "English": "en",
    "French": "fr",
    "Arabic": "ar",
    "Spanish": "es",
    "German": "de"
}

def fix_arabic_text(text):
    try:
        if any("\u0600" <= char <= "\u06FF" for char in text):
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
    except Exception:
        pass
    return text

def load_words():
    if not os.path.exists(FILE):
        return DEFAULT_WORDS
    words = []
    with open(FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "," in line:
                q, a = line.strip().split(",", 1)
                if q.strip() and a.strip():
                    words.append({"q": q.strip(), "a": a.strip()})
    if len(words) < 3:
        return DEFAULT_WORDS
    return words

def save_words(words):
    with open(FILE, "w", encoding="utf-8") as f:
        for w in words:
            f.write(f"{w['q']},{w['a']}\n")

def get_high_score():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_high_score(score):
    current_high = get_high_score()
    if score > current_high:
        with open(SCORE_FILE, "w") as f:
            f.write(str(score))


class NeonButton(Button):
    def __init__(self, bg_color=(0.05, 0.45, 0.9, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = '16sp'
        self.bold = True
        self.bg_color = bg_color
        if os.path.exists(ARABIC_FONT): self.font_name = ARABIC_FONT
        
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[18])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class StyledTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0.08, 0.08, 0.22, 1) 
        self.foreground_color = (1, 1, 1, 1)          
        self.cursor_color = (0, 1, 0.8, 1)            
        self.hint_text_color = (0.5, 0.5, 0.7, 1)     
        self.padding = [15, 12, 15, 12]
        self.font_size = '16sp'
        self.multiline = False
        if os.path.exists(ARABIC_FONT): 
            self.font_name = ARABIC_FONT


class StyledSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0.12, 0.12, 0.3, 1)
        self.color = (0, 1, 0.8, 1)
        self.bold = True
        self.option_cls.background_color = (0.08, 0.08, 0.22, 1)
        self.option_cls.color = (1, 1, 1, 1)
        
        with self.canvas.before:
            Color(0.05, 0.45, 0.9, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_layout = FloatLayout()
        
        # حاوية اللعب الأساسية (كتخفى فاش كتخسر)
        self.game_layout = FloatLayout()
        
        # حاوية شاشة الـ Game Over (كتكون مخفية ف الأول)
        self.gameover_layout = BoxLayout(orientation='vertical', pos_hint={'center_x': 0.5, 'center_y': 0.5}, size_hint=(0.85, 0.6), spacing=20, padding=20)
        with self.gameover_layout.canvas.before:
            Color(0.08, 0.08, 0.25, 0.95)
            self.go_rect = RoundedRectangle(radius=[25])
        self.gameover_layout.bind(pos=self.update_go_rect, size=self.update_go_rect)
        
        self.score = 0
        self.lives = 3
        self.words_db = load_words()
        self.round_active = False
        self.game_active = False 
        
        font_settings = {'font_name': ARABIC_FONT} if os.path.exists(ARABIC_FONT) else {}
        
        # عناصر واجهة اللعب
        self.score_lbl = Label(text="Score: 0", pos_hint={'x': 0.08, 'top': 0.98}, size_hint=(None, None), font_size='20sp', color=(0, 1, 0.8, 1), bold=True)
        self.lives_lbl = Label(text="Lives: ❤❤❤", pos_hint={'right': 0.92, 'top': 0.98}, size_hint=(None, None), font_size='20sp', color=(1, 0.2, 0.4, 1), bold=True)
        self.question_lbl = Label(text="Loading...", pos_hint={'center_x': 0.5, 'top': 0.92}, size_hint=(1, None), height=60, font_size='38sp', bold=True, color=(1, 1, 1, 1), **font_settings)
        self.player = Label(text="◄■►", font_size='28sp', color=(0, 1, 0.8, 1), size_hint=(None, None), pos=(Window.width/2 - 40, 60), bold=True)
        
        self.options = []
        for i in range(3):
            btn = Label(text="", font_size='24sp', size_hint=(None, None), y=Window.height, bold=True, color=(1, 0.8, 0, 1), **font_settings)
            self.options.append(btn)
            self.game_layout.add_widget(btn)

        settings_btn = Button(text="⚙", size_hint=(None, None), size=(60, 60), pos_hint={'right': 0.96, 'y': 0.02}, background_color=(0,0,0,0), font_size='28sp', color=(0.4, 0.4, 0.6, 1))
        settings_btn.bind(on_press=self.go_to_dict)

        self.game_layout.add_widget(self.score_lbl)
        self.game_layout.add_widget(self.lives_lbl)
        self.game_layout.add_widget(self.question_lbl)
        self.game_layout.add_widget(self.player)
        self.game_layout.add_widget(settings_btn)
        
        # عناصر شاشة الـ Game Over
        self.go_title = Label(text="GAME OVER", font_size='36sp', bold=True, color=(1, 0.2, 0.2, 1), size_hint_y=None, height=60)
        self.go_score = Label(text="Your Score: 0", font_size='24sp', color=(1, 1, 1, 1))
        self.go_best = Label(text="Best Score: 0", font_size='22sp', color=(0, 1, 0.8, 1))
        
        self.play_again_btn = NeonButton(text="🔄 Play Again", bg_color=(0, 0.7, 0.4, 1), size_hint_y=None, height=55)
        self.play_again_btn.bind(on_press=self.restart_game)
        
        self.go_dict_btn = NeonButton(text="⚙ Dictionary", bg_color=(0.25, 0.25, 0.35, 1), size_hint_y=None, height=50)
        self.go_dict_btn.bind(on_press=self.go_to_dict)
        
        self.gameover_layout.add_widget(self.go_title)
        self.gameover_layout.add_widget(self.go_score)
        self.gameover_layout.add_widget(self.go_best)
        self.gameover_layout.add_widget(self.play_again_btn)
        self.gameover_layout.add_widget(self.go_dict_btn)
        
        # إضافة الحاويات للرئيسية
        self.main_layout.add_widget(self.game_layout)
        self.add_widget(self.main_layout)

    def update_go_rect(self, instance, value):
        self.go_rect.pos = instance.pos
        self.go_rect.size = instance.size

    def on_touch_down(self, touch):
        if not self.game_active or self.lives <= 0: return super().on_touch_down(touch)
        if touch.x < Window.width / 3: self.player.x = Window.width * 0.12 - 20
        elif touch.x > Window.width * 0.66: self.player.x = Window.width * 0.78 - 20
        else: self.player.x = Window.width * 0.45 - 20
        return super().on_touch_down(touch)

    def on_enter(self):
        self.words_db = load_words()
        self.game_active = True
        if self.lives <= 0:
            self.restart_game()
        else:
            self.reset_game_stats()
            Clock.schedule_once(lambda dt: self.start_round(), 0.2)

    def on_leave(self):
        self.game_active = False
        self.round_active = False
        Clock.unschedule(self.start_round)
        for opt in self.options: 
            Animation.stop_all(opt)

    def reset_game_stats(self):
        self.score = 0
        self.lives = 3
        if self.gameover_layout in self.main_layout.children:
            self.main_layout.remove_widget(self.gameover_layout)
        self.game_layout.opacity = 1
        self.update_ui()

    def restart_game(self, *args):
        self.reset_game_stats()
        self.start_round()

    def update_ui(self):
        self.score_lbl.text = f"Score: {self.score}"
        self.lives_lbl.text = f"Lives: {'❤' * max(0, self.lives)}"

    def start_round(self, *args):
        if not self.game_active: return 
        
        if self.lives <= 0:
            save_high_score(self.score)
            # إظهار شاشة النتيجة بوحدها وإخفاء اللعب الأساسي
            self.go_score.text = f"Your Score: {self.score}"
            self.go_best.text = f"Best Score: {get_high_score()}"
            self.game_layout.opacity = 0.15
            if self.gameover_layout not in self.main_layout.children:
                self.main_layout.add_widget(self.gameover_layout)
            return

        self.round_active = True
        target = random.choice(self.words_db)
        
        self.question_lbl.text = fix_arabic_text(target['q'])
        self.correct_ans = target['a']

        opts = [self.correct_ans]
        while len(opts) < 3:
            w = random.choice(self.words_db)['a']
            if w not in opts: 
                opts.append(w)
        random.shuffle(opts)

        lanes = [Window.width * 0.22, Window.width * 0.5, Window.width * 0.78]
        for i, btn in enumerate(self.options):
            Animation.stop_all(btn)
            btn.color = (1, 0.8, 0, 1) 
            btn.text = fix_arabic_text(opts[i])
            btn.x = lanes[i] - btn.width/2
            btn.y = Window.height - 140 
            
            duration = max(1.4, 3.8 - (self.score / 120))
            anim = Animation(y=25, duration=duration)
            if i == 0:
                anim.bind(on_complete=self.check_collision)
            anim.start(btn)

    def check_collision(self, anim, widget):
        if not self.game_active or not self.round_active: return
        self.round_active = False

        for opt in self.options: 
            Animation.stop_all(opt)

        player_center = self.player.x + 40
        player_lane = "left" if player_center < Window.width * 0.3 else ("mid" if player_center < Window.width * 0.6 else "right")
        
        correct_lbl = None
        chosen_lbl = None

        for btn in self.options:
            if btn.text == fix_arabic_text(self.correct_ans):
                correct_lbl = btn
            
            btn_lane = "left" if (btn.x + btn.width/2) < Window.width * 0.3 else ("mid" if (btn.x + btn.width/2) < Window.width * 0.6 else "right")
            if player_lane == btn_lane:
                chosen_lbl = btn

        if chosen_lbl == correct_lbl:
            self.score += 10
            if correct_lbl: correct_lbl.color = (0, 1, 0, 1)
        else:
            self.lives -= 1
            if chosen_lbl: chosen_lbl.color = (1, 0, 0, 1)   
            if correct_lbl: correct_lbl.color = (0, 1, 0, 1) 
            
        self.update_ui()
        if self.game_active:
            Clock.schedule_once(lambda dt: self.start_round(), 1.0)

    def go_to_dict(self, *args):
        self.manager.current = 'dict'


class DictionaryScreen(Screen):
    def on_enter(self):
        self.refresh_list()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=25, spacing=15)
        
        layout.add_widget(Label(text="DICTIONARY", font_size='26sp', bold=True, size_hint_y=None, height=60, color=(0, 1, 0.8, 1)))
        
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=12, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        
        self.scroll.add_widget(self.grid)
        layout.add_widget(self.scroll)
        
        btn_layout = BoxLayout(size_hint_y=None, height=55, spacing=15)
        add_btn = NeonButton(text="+ Add Word", bg_color=(0.0, 0.6, 0.9, 1))
        add_btn.bind(on_press=lambda *args: self.open_edit(-1))
        back_btn = NeonButton(text="🎮 Play Game", bg_color=(0.6, 0.1, 0.8, 1))
        back_btn.bind(on_press=lambda *args: setattr(self.manager, 'current', 'game'))
        
        btn_layout.add_widget(add_btn)
        btn_layout.add_widget(back_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)

    def refresh_list(self):
        self.grid.clear_widgets()
        words = load_words()
        font_settings = {'font_name': ARABIC_FONT} if os.path.exists(ARABIC_FONT) else {}
        
        for i, w in enumerate(words):
            row = BoxLayout(size_hint_y=None, height=55, spacing=8)
            
            with row.canvas.before:
                Color(0.08, 0.08, 0.22, 1)
                RoundedRectangle(size=row.size, pos=row.pos, radius=[10])
            row.bind(pos=self.update_row_bg, size=self.update_row_bg)
            
            fixed_q = fix_arabic_text(w['q'])
            fixed_a = fix_arabic_text(w['a'])
            
            lbl = Label(text=f"  {fixed_q}  ＝  {fixed_a}", halign='left', text_size=(Window.width*0.5, None), color=(1,1,1,1), **font_settings)
            row.add_widget(lbl)
            
            edit_btn = Button(text="Edit", size_hint_x=None, width=60, background_color=(0,0,0,0), color=(1, 0.7, 0, 1), font_size='15sp', bold=True)
            edit_btn.bind(on_press=lambda *args, idx=i: self.open_edit(idx))
            
            del_btn = Button(text="Del", size_hint_x=None, width=60, background_color=(0,0,0,0), color=(1, 0.2, 0.2, 1), font_size='15sp', bold=True)
            del_btn.bind(on_press=lambda *args, idx=i: self.delete_word(idx))
            
            row.add_widget(edit_btn)
            row.add_widget(del_btn)
            self.grid.add_widget(row)

    def update_row_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.08, 0.08, 0.22, 1)
            RoundedRectangle(size=instance.size, pos=instance.pos, radius=[10])

    def delete_word(self, index):
        words = load_words()
        if 0 <= index < len(words):
            words.pop(index)
            save_words(words)
            self.refresh_list()

    def open_edit(self, index):
        self.manager.get_screen('edit').editing_index = index
        self.manager.current = 'edit'


class EditScreen(Screen):
    editing_index = -1
    
    def on_enter(self):
        words = load_words()
        if self.editing_index != -1 and self.editing_index < len(words):
            self.q_input.text = words[self.editing_index]['q']
            self.a_input.text = words[self.editing_index]['a']
        else:
            self.q_input.text = ""
            self.a_input.text = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=18)
        
        layout.add_widget(Label(text="EDIT WORD", font_size='26sp', bold=True, size_hint_y=None, height=40, color=(0, 1, 0.8, 1)))
        
        lang_layout = BoxLayout(size_hint_y=None, height=45, spacing=12)
        self.src_spinner = StyledSpinner(text='English', values=list(LANGUAGES.keys()), size_hint_x=0.45)
        self.target_spinner = StyledSpinner(text='Arabic', values=list(LANGUAGES.keys()), size_hint_x=0.45)
        
        lang_layout.add_widget(self.src_spinner)
        lang_layout.add_widget(Label(text="➔", size_hint_x=0.1, font_size="20sp", color=(0, 1, 0.8, 1)))
        lang_layout.add_widget(self.target_spinner)
        layout.add_widget(lang_layout)
        
        self.q_input = StyledTextInput(hint_text="Enter word here...")
        layout.add_widget(self.q_input)
        
        translate_btn = NeonButton(text="✨ Auto-Translate", size_hint_y=None, height=50, bg_color=(0.1, 0.5, 0.9, 1))
        translate_btn.bind(on_press=self.start_translation)
        layout.add_widget(translate_btn)
        
        self.a_input = StyledTextInput(hint_text="Translation will appear here...")
        layout.add_widget(self.a_input)
        
        save_btn = NeonButton(text="Save Word", bg_color=(0.0, 0.7, 0.4, 1))
        save_btn.bind(on_press=self.save_data)
        
        cancel_btn = NeonButton(text="Cancel", bg_color=(0.25, 0.25, 0.35, 1))
        cancel_btn.bind(on_press=lambda *args: setattr(self.manager, 'current', 'dict'))
        
        layout.add_widget(save_btn)
        layout.add_widget(cancel_btn)
        self.add_widget(layout)

    def start_translation(self, *args):
        if self.q_input.text.strip():
            self.a_input.text = "Translating..."
            threading.Thread(target=self.translate_worker, daemon=True).start()

    def translate_worker(self):
        text_to_translate = self.q_input.text.strip()
        src_lang = LANGUAGES.get(self.src_spinner.text, "en")
        target_lang = LANGUAGES.get(self.target_spinner.text, "fr")
        
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(text_to_translate)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode('utf-8'))
            translated = data[0][0][0]
            
            Clock.schedule_once(lambda dt: self.update_a_input(translated))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_a_input("Error! Check Internet."))

    def update_a_input(self, text):
        self.a_input.text = fix_arabic_text(text)

    def save_data(self, *args):
        if not self.q_input.text.strip() or not self.a_input.text.strip(): return
        words = load_words()
        new_data = {"q": self.q_input.text.strip(), "a": self.a_input.text.strip()}
        
        if self.editing_index == -1:
            words.append(new_data)
        else:
            if self.editing_index < len(words):
                words[self.editing_index] = new_data
            
        save_words(words)
        self.manager.current = 'dict'


class WordMasterApp(App):
    def build(self):
        self.title = "Global Word Master Pro"
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(DictionaryScreen(name='dict'))
        sm.add_widget(EditScreen(name='edit'))
        return sm

if __name__ == '__main__':
    WordMasterApp().run()