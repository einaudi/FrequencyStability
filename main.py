# -*- coding: utf-8 -*-

import sys
import os

import yaml

import numpy as np

from misc.generators import generate_widgets, generate_layout
from widgets.DialogProgress import calcDeviationProgress
import src.frequency_stability as fs
from utils import read_csv

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFileDialog,
    QProgressDialog,
    QMessageBox
)


available_files = '(*.csv *.txt)'
tau_ext_margin = 0.001 # Hz

def dialogWarning(msg):
    msgBox = QMessageBox()
    msgBox.setText(msg)
    msgBox.setIcon(QMessageBox.Warning)
    msgBox.exec()


class FrequencyStability(QMainWindow):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Configuration files
        widgets_conf = self.getWidgetsConfig()
        layout_conf = self.getLayoutConfig()

        # Variables
        self._data = None
        self._meta = None
        self._params = {}

        self._taus = [] # averaging times
        self._devs = {} # deviations
        self._conf_int = {} # confidence intervals
        self._noise_type = []

        self.initWidgets(widgets_conf)
        self.initLayout(layout_conf)
        self.initUI()

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

        self._widgets['checkAllanOvlp'].setChecked(True)

        print('Widgets initialised!')

    def initLayout(self, layout_conf):

        print('Initialising layout...')
        layouts = {}

        mainLayout = generate_layout(layout_conf, self._widgets)

        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

        print('Layout initialised!')

    def initUI(self):

        self._widgets['btnFileInput'].clicked.connect(self.loadFile)
        self._widgets['btnMeta'].clicked.connect(self.loadMeta)
        self._widgets['btnAnalyse'].clicked.connect(self.analyse)
        self._widgets['checkTauMin'].stateChanged.connect(self.TauMinChanged)
        self._widgets['checkTauMax'].stateChanged.connect(self.TauMaxChanged)

    def loadFile(self):

        inputPaths = QFileDialog.getOpenFileNames(
            self,
            'Open file',
            '~/',
            available_files
        )

        if len(inputPaths[0]) > 1:
            dialogWarning('Choose only one file!')
            return False
        else:
            data, meta = read_csv(inputPaths[0][0])
            if 'Frequency [Hz]' not in data.columns:
                dialogWarning('Could not find frequency column in data!')
                return False
            self._data = data
            self._meta = meta
            self._widgets['editFileInput'].setText(inputPaths[0][0])
            return True

    def loadMeta(self):

        if self._meta is None:
            dialogWarning('Load data first!')
            return False
        elif not self._meta:
            dialogWarning('No metadata in loaded file!')
            return False
        
        tmp = {}
        try:
            tmp['Central frequency [Hz]'] = self._meta['Central frequency [Hz]']
            tmp['Sampling frequency [Hz]'] = self._meta['Sampling frequency [Hz]']
        except KeyError:
            dialogWarning('Could not find needed parameters!')
            return False
        
        self._widgets['freqCentral'].setText('{:.2e}'.format(tmp['Central frequency [Hz]']))
        self._widgets['freqSampling'].setText('{:.2e}'.format(tmp['Sampling frequency [Hz]']))
        return True

    def getParams(self):

        tmp = {}

        # Data length
        if self._data is None:
            dialogWarning('Load data first!')
            return False
        try:
            tmp['N'] = self._data['Frequency [Hz]'].size
        except KeyError:
            dialogWarning('Could not find frequency column in data!')
            return False
        
        # Parameters from settings section
        try:
            tmp['Central frequency [Hz]'] = float(self._widgets['freqCentral'].text())
            tmp['Sampling frequency [Hz]'] = float(self._widgets['freqSampling'].text())
            tmp['Tau min [s]'] = float(self._widgets['tauMin'].text())
            tmp['Tau max [s]'] = float(self._widgets['tauMax'].text())
            tmp['Tau N'] = int(self._widgets['tauN'].text())
        except ValueError:
            dialogWarning('Could not read parameters!')
            return False

        # Tau ranges
        if tmp['Tau min [s]'] < 1/tmp['Sampling frequency [Hz]']:
            dialogWarning('Minimal tau below sampling limit!')
            return False
        if tmp['Tau max [s]'] > tmp['N']/2/tmp['Sampling frequency [Hz]']:
            dialogWarning('Maximal tau above sampling limit!')
            return False
        if tmp['Tau max [s]'] <= tmp['Tau min [s]']:
            dialogWarning('Tau max lower or equal than tau min!')
            return False
        
        # Check if mean frequency option is enabled
        if self._widgets['checkCentral'].isChecked():
            tmp['Central frequency [Hz]'] = np.average(self._data['Frequency [Hz]'])
        
        self._params = tmp

    def _clearDeviations(self):

        self._taus = [] # averaging times
        self._devs = {} # deviations
        self._conf_int = {} # confidence intervals
        self._noise_type = []

    def analyse(self):

        self.getParams() # already checks if data exists

        # Clear previous data
        self._clearDeviations()

        # Generate taus
        self._taus = np.linspace(
            self._params['Tau min [s]'],
            self._params['Tau max [s]'],
            self._params['Tau N']
        )

        # Clear plots
        self._widgets['canvasHist'].prepare_axes()
        self._widgets['canvasFreq'].prepare_axes()
        self._widgets['canvasDev'].prepare_axes(yLog=True, Grid=True)

        # Plot frequency histogram
        self.plotFrequencyHistogram()

        # Calculate and plot fractional frequency
        fs_frac = fs.calc_fractional_frequency(
            self._data['Frequency [Hz]'],
            self._params['Central frequency [Hz]']
        )
        ts = np.arange(self._params['N']) / self._params['Sampling frequency [Hz]']
        self.plotFractionalFrequency(ts, fs_frac)

        # Calculate phase error
        phase_error = fs.calc_phase_error(fs_frac, self._params['Sampling frequency [Hz]'])

        # Calculate deviations
        try:
            if self._widgets['checkAllan'].isChecked():
                self._devs['ADEV'] = calcDeviationProgress(
                    dev='ADEV',
                    parent=self,
                    taus=self._taus,
                    phase_error=phase_error,
                    f_sampling=self._params['Sampling frequency [Hz]']
                )
            if self._widgets['checkAllanOvlp'].isChecked():
                self._devs['ADEV ovlp'] = calcDeviationProgress(
                    dev='ADEV ovlp',
                    parent=self,
                    taus=self._taus,
                    phase_error=phase_error,
                    f_sampling=self._params['Sampling frequency [Hz]']
                )
            if self._widgets['checkHadamard'].isChecked():
                self._devs['HDEV'] = calcDeviationProgress(
                    dev='HDEV',
                    parent=self,
                    taus=self._taus,
                    phase_error=phase_error,
                    f_sampling=self._params['Sampling frequency [Hz]']
                )
        except InterruptedError:
            return False
        
        # Calculate noise types
        alphas = fs.calc_noise_id(
            self._data['Frequency [Hz]'],
            self._taus,
            self._params['Sampling frequency [Hz]']
        )
        self._noise_type = fs.dominant_noise(alphas)

        # Calculate confidence intervals
        if self._widgets['checkAllan'].isChecked():
            self._conf_int['ADEV'] = fs.calc_confidence_interval(
                self._devs['ADEV'],
                self._taus,
                self._params['Sampling frequency [Hz]'],
                alphas,
                self._params['N']
            )
        if self._widgets['checkAllanOvlp'].isChecked():
            self._conf_int['ADEV ovlp'] = fs.calc_confidence_interval(
                self._devs['ADEV ovlp'],
                self._taus,
                self._params['Sampling frequency [Hz]'],
                alphas,
                self._params['N']
            )
        if self._widgets['checkHadamard'].isChecked():
            self._conf_int['HDEV'] = fs.calc_confidence_interval(
                self._devs['HDEV'],
                self._taus,
                self._params['Sampling frequency [Hz]'],
                alphas,
                self._params['N']
            )

        # Plot deviations
        self.plotDeviations()

    def plotFrequencyHistogram(self):

        counts, bins = np.histogram(
            self._data['Frequency [Hz]'],
            100
        )

        self._widgets['canvasHist'].histogram(counts, bins)
        self._widgets['canvasHist'].refresh()

    def plotFractionalFrequency(self, ts, fs_frac):

        self._widgets['canvasFreq'].plot(ts, fs_frac)
        self._widgets['canvasFreq'].refresh()

    def plotDeviations(self):

        for key, value in self._devs.items():
            self._widgets['canvasDev'].errorbar(
                self._taus,
                value,
                yerr=self._conf_int[key],
                label=key,
                fmt='o',
                markersize=4
            )

        self._widgets['canvasDev'].add_legend()
        self._widgets['canvasDev'].refresh()

    def TauMinChanged(self):

        if self._widgets['checkTauMin'].isChecked():
            try:
                f_s = float(self._widgets['freqSampling'].text()) - tau_ext_margin
                self._widgets['tauMin'].setText('{:.4e}'.format(1/f_s))
            except (ValueError, ZeroDivisionError):
                dialogWarning('Incorrect sampling frequency!')
                self._widgets['checkTauMin'].setChecked(False)
            self._widgets['tauMin'].setReadOnly(True)
        else:
            self._widgets['tauMin'].setReadOnly(False)

    def TauMaxChanged(self):

        if self._data is None:
            dialogWarning('Load data first!')
            self._widgets['checkTauMax'].setChecked(False)
            return False
        else:
            N = self._data['Frequency [Hz]'].size

        if self._widgets['checkTauMax'].isChecked():
            try:
                f_s = float(self._widgets['freqSampling'].text()) + tau_ext_margin
                self._widgets['tauMax'].setText('{:.4e}'.format(N/2/f_s))
            except (ValueError, ZeroDivisionError):
                dialogWarning('Incorrect sampling frequency!')
                self._widgets['checkTauMax'].setChecked(False)
            self._widgets['tauMax'].setReadOnly(True)
        else:
            self._widgets['tauMax'].setReadOnly(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = FrequencyStability()
    sys.exit(app.exec_())