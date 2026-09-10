import sys

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout

from widgets.lottie_widget import LottieWidget
from managers.animation_manager import AnimationManager


class TestWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Lottie Test")
        self.resize(400, 400)
        layout = QVBoxLayout()
        self.animation = LottieWidget()
        layout.addWidget(self.animation)
        self.setLayout(layout)
        self.animation.web_view.loadFinished.connect(
            self.load_animation
        )

    def load_animation(self, success):

        if success:

            self.animation.set_animation(
                AnimationManager.get_weather_animation(800)
            )

        path = AnimationManager.get_weather_animation(800)

        print(path)

        self.animation.set_animation(path)


app = QApplication(sys.argv)
window = TestWindow()
window.show()
sys.exit(app.exec_())