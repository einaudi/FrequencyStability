# -*- coding: utf-8 -*-

import sys
import os

import yaml

from misc.generators import generate_widgets, generate_layout

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget
)


class FrequencyStability(QMainWindow):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        widgets_conf = self.getWidgetsConfig()
        layout_conf = self.getLayoutConfig()

        self.initWidgets(widgets_conf)
        self.initLayout(layout_conf)

        print('Running application')
        self.show()

    def getWidgetsConfig(self):

        config_path = os.path.join("./", "config", "widgets_config.yml")
        with open(config_path) as config_file:
            widgets_conf = yaml.safe_load(config_file)

        return widgets_conf

    def getLayoutConfig(self):

        config_path = os.path.join("./", "config", "layout_config.yml")
        with open(config_path) as config_file:
            layout_conf = yaml.safe_load(config_file)

        return layout_conf

    def initWidgets(self, widget_conf):

        print('Initialising widgets...')

        self._widgets = generate_widgets(widget_conf)

        print('Widgets initialised!')

    def initLayout(self, layout_conf):

        print('Initialising layout...')
        layouts = {}

        mainLayout = generate_layout(layout_conf, self._widgets)

        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

        print('Layout initialised!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = FrequencyStability()
    sys.exit(app.exec_())