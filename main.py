from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
import re


class CalculatorLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.expression = ""
        self.result_label = Label(
            text="0", font_size=48, size_hint=(1, 0.25),
            halign="right", valign="middle", color=(1, 1, 1, 1)
        )
        self.result_label.bind(size=self._update_text_size)
        self.add_widget(self.result_label)

        buttons = [
            ["C", "+/-", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["0", "00", ".", "="]
        ]

        grid = GridLayout(cols=4, spacing=4, size_hint=(1, 0.75))
        for row in buttons:
            for text in row:
                grid.add_widget(self._make_button(text))
        self.add_widget(grid)

    def _update_text_size(self, instance, value):
        instance.text_size = (instance.width - 20, None)

    def _make_button(self, text):
        btn = Button(
            text=text,
            font_size=32,
            background_normal='',
            background_color=self._get_color(text),
            color=(1, 1, 1, 1) if text not in (
                "C", "+/-", "%") else (0, 0, 0, 1),
            size_hint=(1, 1)
        )
        btn.bind(on_release=self._on_button_click)
        return btn

    def _get_color(self, text):
        if text in ("/", "*", "-", "+", "="):
            return (1, 0.58, 0, 1)  # orange
        elif text in ("C", "+/-", "%"):
            return (0.65, 0.65, 0.65, 1)  # light gray
        else:
            return (0.2, 0.2, 0.2, 1)  # dark gray

    def _on_button_click(self, instance):
        char = instance.text
        match char:
            case "C":
                self.expression = ""
                self.result_label.text = "0"
            case "=":
                try:
                    result = self._safe_eval(self.expression)
                    self.result_label.text = str(result)
                    self.expression = str(result)
                except Exception:
                    self.result_label.text = "Error"
                    self.expression = ""
            case "+/-":
                if self.expression:
                    self.expression = self._toggle_sign(self.expression)
                    self.result_label.text = self.expression
            case "%":
                try:
                    result = self._safe_eval(self.expression) / 100
                    if result == int(result):
                        result = int(result)
                    self.result_label.text = str(result)
                    self.expression = str(result)
                except Exception:
                    self.result_label.text = "Error"
                    self.expression = ""
            case _:
                if char in "0123456789.":
                    self.expression = self._append_number(
                        self.expression, char)
                else:
                    self.expression += char
                self.result_label.text = self.expression if self.expression else "0"

    def _append_number(self, expr, char):
        match = re.search(r'([\-]?\d*\.?\d*)$', expr)
        if match:
            last_number = match.group(1)
            start = match.start(1)
            if char in "0123456789":
                if last_number == "0":
                    expr = expr[:start] + char
                elif last_number.startswith("0") and not last_number.startswith("0."):
                    expr = expr[:start] + char
                else:
                    expr += char
            elif char == ".":
                if "." not in last_number:
                    if last_number == "":
                        expr += "0."
                    else:
                        expr += "."
            return expr
        else:
            if char == ".":
                return "0."
            elif char in "0123456789":
                return char
            else:
                return expr

    def _toggle_sign(self, expr):
        match = re.search(r'([\-]?\d*\.?\d*)$', expr)
        if match:
            last_number = match.group(1)
            start = match.start(1)
            if last_number.startswith("-"):
                expr = expr[:start] + last_number[1:]
            else:
                expr = expr[:start] + "-" + last_number
        return expr

    def _safe_eval(self, expr):
        if not re.match(r'^[\d\.\+\-\*/% ]*$', expr):
            raise ValueError("Invalid input")
        result = eval(expr)
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result


class CalculatorApp(App):
    icon = 'calculator.png'

    def build(self):
        Window.clearcolor = (0.13, 0.13, 0.13, 1)
        Window.size = (320, 480)
        return CalculatorLayout()


if __name__ == "__main__":
    CalculatorApp().run()
