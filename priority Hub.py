# PriorityHub - Modern To-Do App
import json
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.anchorlayout import AnchorLayout

try:
    from plyer import notification
    PLYER_OK = True
except:
    PLYER_OK = False

Window.clearcolor = (0.97,0.97,0.97,1)
TASKS_FILE = "tasks.json"

CATEGORY_COLORS = {
    "General": (0.9,0.9,0.9,1),
    "Work": (0.8,0.9,1,1),
    "Personal": (0.95,0.85,1,1),
    "Study": (0.85,1,0.85,1),
    "Shopping": (1,0.9,0.8,1)
}
PRIORITY_COLORS = {
    "High": (1,0.5,0.5,1),
    "Medium": (1,0.8,0.5,1),
    "Low": (0.7,1,0.7,1)
}

class PriorityHub(App):
    def build(self):
        self.tasks = []
        main_layout = BoxLayout(orientation="vertical", padding=18, spacing=12)

        # Top-middle bold watermark
        water = AnchorLayout(anchor_x='center', anchor_y='top', size_hint=(1,None), height=20)
        wm = Label(
            text="[b]PriorityHub — by Adeoye Toluwalase[/b]",
            font_size=12,
            color=(0,0,0,0.18),
            markup=True
        )
        water.add_widget(wm)
        main_layout.add_widget(water)

        # Overview label
        self.overview_label = Label(
            text="", size_hint_y=None, height=40, font_size=16, color=(0,0,0,1)
        )
        main_layout.add_widget(self.overview_label)

        # Input row
        row = BoxLayout(size_hint_y=None, height=50, spacing=8)
        self.task_input = TextInput(
            hint_text="Task title...", multiline=False, size_hint_x=0.35, font_size=16
        )
        self.time_input = TextInput(
            hint_text="HH:MM (optional)", multiline=False, size_hint_x=0.15, font_size=16
        )
        self.category_input = Spinner(
            text="General",
            values=("General","Work","Personal","Study","Shopping"),
            size_hint_x=0.2
        )
        self.priority_input = Spinner(
            text="Medium",
            values=("High","Medium","Low"),
            size_hint_x=0.15
        )
        add_btn = Button(
            text="Add", size_hint_x=0.15, background_color=(0.12,0.55,0.95,1), color=(1,1,1,1)
        )
        add_btn.bind(on_press=self.on_add)

        row.add_widget(self.task_input)
        row.add_widget(self.time_input)
        row.add_widget(self.category_input)
        row.add_widget(self.priority_input)
        row.add_widget(add_btn)
        main_layout.add_widget(row)

        # Scrollable tasks
        self.scroll = ScrollView()
        self.task_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.task_layout.bind(minimum_height=self.task_layout.setter('height'))
        self.scroll.add_widget(self.task_layout)
        main_layout.add_widget(self.scroll)

        # Load tasks and start reminder checks
        self.load_tasks()
        self.update_tasks()
        Clock.schedule_interval(self.check_reminders,30)
        return main_layout

    def parse_time(self, text):
        text = text.strip()
        if not text: return None
        try:
            h,m = map(int,text.split(":"))
            now=datetime.now()
            dt=now.replace(hour=h,minute=m,second=0,microsecond=0)
            if dt<now: dt+=timedelta(days=1)
            return dt
        except: return None

    def on_add(self, instance):
        title = self.task_input.text.strip()
        if not title:
            self.show_popup("Error","Please enter a task title.")
            return
        sched_time = self.parse_time(self.time_input.text.strip())
        category = self.category_input.text
        priority = self.priority_input.text
        task = {
            'title': title,
            'time': sched_time,
            'category': category,
            'priority': priority,
            'notified': False
        }
        self.tasks.append(task)
        self.task_input.text = ""
        self.time_input.text = ""
        self.save_tasks()
        self.update_tasks()

    def update_tasks(self):
        self.task_layout.clear_widgets()
        today = datetime.now().date()
        this_week_start = today - timedelta(days=today.weekday())
        today_count = 0
        week_count = 0

        for idx, t in enumerate(self.tasks, start=1):
            if t['time'] and t['time'].date() == today: today_count += 1
            if t['time'] and this_week_start <= t['time'].date() <= today + timedelta(days=6): week_count += 1

            card = BoxLayout(size_hint_y=None, height=dp(70), spacing=8, padding=[10,6])
            bg_color = CATEGORY_COLORS.get(t['category'],(0.9,0.9,0.9,1))
            with card.canvas.before:
                Color(*bg_color)
                RoundedRectangle(pos=card.pos, size=card.size, radius=[12])

            label_text = f"{idx}. {t['title']}\nCategory: {t['category']} | Priority: {t['priority']}"
            if t['time']: label_text += f" | Due: {t['time'].strftime('%H:%M')}"
            lbl = Label(text=label_text, halign="left", valign="middle", font_size=16, color=(0,0,0,1))
            lbl.bind(size=lbl.setter('text_size'))

            done_btn = Button(text="Done", size_hint_x=None, width=80, background_color=(0.2,0.7,0.2,1), color=(1,1,1,1))
            done_btn.bind(on_press=lambda x,task=t:self.mark_done(task))
            rem_btn = Button(text="Remove", size_hint_x=None, width=90, background_color=(1,0.35,0.35,1), color=(1,1,1,1))
            rem_btn.bind(on_press=lambda x,task=t:self.remove_task(task))

            card.add_widget(lbl)
            card.add_widget(done_btn)
            card.add_widget(rem_btn)
            self.task_layout.add_widget(card)

        self.overview_label.text = f"Today: {today_count} tasks | This Week: {week_count} tasks"

    def mark_done(self, task):
        self.show_popup("Nice!", f"'{task['title']}' completed.")
        if task in self.tasks: self.tasks.remove(task)
        self.save_tasks()
        self.update_tasks()

    def remove_task(self, task):
        if task in self.tasks: self.tasks.remove(task)
        self.save_tasks()
        self.update_tasks()

    def check_reminders(self, dt):
        now = datetime.now()
        for task in list(self.tasks):
            sched = task.get('time')
            if sched and not task.get('notified') and now >= sched:
                self.notify_user(task)
                task['notified'] = True
                self.save_tasks()

    def notify_user(self, task):
        title = "Reminder"
        message = f"Time for: {task['title']}"
        if PLYER_OK:
            try: notification.notify(title=title, message=message, timeout=6)
            except: self.show_popup(title,message)
        else:
            self.show_popup(title,message)

    def show_popup(self, title, message):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        box.add_widget(Label(text=message))
        btn = Button(text="OK", size_hint_y=None, height=40, background_color=(0.12,0.55,0.95,1), color=(1,1,1,1))
        box.add_widget(btn)
        popup = Popup(title=title, content=box, size_hint=(0.8,0.35))
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def save_tasks(self):
        data = []
        for t in self.tasks:
            dt = t['time'].strftime('%Y-%m-%d %H:%M:%S') if t['time'] else None
            data.append({'title': t['title'], 'time': dt, 'category': t['category'], 'priority': t['priority'], 'notified': t['notified']})
        with open(TASKS_FILE,'w') as f:
            json.dump(data, f)

    def load_tasks(self):
        try:
            with open(TASKS_FILE,'r') as f:
                data = json.load(f)
                for t in data:
                    dt = datetime.strptime(t['time'],'%Y-%m-%d %H:%M:%S') if t['time'] else None
                    self.tasks.append({'title': t['title'], 'time': dt, 'category': t['category'], 'priority': t['priority'], 'notified': t['notified']})
        except:
            self.tasks = []

if __name__ == "__main__":
    PriorityHub().run()