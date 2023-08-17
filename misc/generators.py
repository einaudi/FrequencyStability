# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox
)
from widgets.PlotCanvas import PlotCanvas


# ----- WIDGETS -----
def generate_widgets(widget_conf):

    ret = {}

    for widget_type in widget_conf:
            for widget in widget_conf[widget_type]:
                # QLineEdit
                if widget_type == 'QLineEdit':
                    tmp = QLineEdit()
                    if 'default' in widget.keys():
                        tmp.setText(widget['default'])
                # QPushButton
                elif widget_type == 'QPushButton':
                    tmp = QPushButton(widget['label'])
                # QCheckBox
                elif widget_type == 'QCheckBox':
                    tmp = QCheckBox()
                # PlotCanvas
                elif widget_type == 'PlotCanvas':
                    tmp = PlotCanvas(
                        widget["xlabel"],
                        widget["ylabel"]
                    )
                    tmp.set_style()
                    try:
                        tmp.prepare_axes(
                            **widget['settings']
                        )
                    except KeyError:
                        pass
                else:
                    print('Unknown widget type {}!'.format(widget_type))
                    quit()

                ret[widget['name']] = tmp
    
    return ret


# ----- LAYOUT -----
def generate_layout(layout_conf, widgets):

    layouts = {}

    # Generate sub-layouts
    for layout in layout_conf['layouts']:
            if layout['type'] == 'QGridLayout':
                tmp = QGridLayout()
                for widget in layout['widgets']:
                    if widget['type'] == 'QLabel':
                        tmp.addWidget(
                            QLabel(widget['label']),
                            widget['position'][0],
                            widget['position'][1]
                        )
                    else:
                        tmp.addWidget(
                            widgets[widget['name']],
                            widget['position'][0],
                            widget['position'][1]
                        )
            elif layout['type'] == 'QHBoxLayout':
                tmp = QHBoxLayout()
                for widget in layout['widgets']:
                    tmp.addWidget(widgets[widget['name']])
            
            layouts[layout['name']] = tmp

    mainLayout = generate_layout_tree(layout_conf['mainLayout'], layouts, widgets)

    return mainLayout

def generate_layout_tree(layoutTree, layouts, widgets):
    
    if layoutTree['type'] == 'QHBoxLayout':
        ret = QHBoxLayout()
    elif layoutTree['type'] == 'QVBoxLayout':
        ret = QVBoxLayout()
    elif layoutTree['type'] == 'QGroupBox':
        ret = QGroupBox(layoutTree['label'])
    elif layoutTree['type'] == 'layout':
        ret = layouts[layoutTree['name']]
    elif layoutTree['type'] == 'widget':
        return widgets[layoutTree['name']]
    else:
        print('Unknown layout type {}!'.format(layoutTree['type']))
        quit()

    if layoutTree['contents']:
        for item in layoutTree['contents']:
            tmp = generate_layout_tree(item, layouts, widgets)
            try:
                ret.addLayout(tmp)
            except TypeError:
                ret.addWidget(tmp)
            except AttributeError:
                ret.setLayout(tmp)

    return ret