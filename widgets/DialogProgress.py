# -*- coding: utf-8 -*-

import time
import numpy as np

from PyQt5.QtWidgets import QProgressDialog

from src.frequency_stability import calc_ADEV_single, calc_ADEV_overlapped_single, calc_HDEV_single


dev_msg = {
    'ADEV': 'Calculating Allan deviation',
    'ADEV ovlp': 'Calculating Allan overlapping deviation',
    'HDEV': 'Calculating Hadamard deviation'
}

def calcDeviationProgress(*args, **kwargs):

    ret = []
    N = kwargs['taus'].size

    progress = QProgressDialog(dev_msg[kwargs['dev']], "Cancel", 0, N, kwargs['parent'])
    progress.setModal(True)
    for i, tau in enumerate(kwargs['taus']):
        start = time.time()
        progress.setValue(i)

        if kwargs['dev'] == 'ADEV':
            tmp = calc_ADEV_single(kwargs['phase_error'], tau)
        elif kwargs['dev'] == 'ADEV ovlp':
            tmp = calc_ADEV_overlapped_single(kwargs['phase_error'], tau, kwargs['f_sampling'])
        elif kwargs['dev'] == 'HDEV':
            tmp = calc_HDEV_single(kwargs['phase_error'], tau, kwargs['f_sampling'])
        else:
            tmp = 0

        ret.append(tmp)

        if progress.wasCanceled():
            raise InterruptedError
        stop = time.time()
        speed = 1/(stop-start)
        time_left = (N-i)/speed
        progress.setLabelText('{0}\neta: {1:.2f} s ({2:.2f}/s)'.format(
            dev_msg[kwargs['dev']],
            time_left,
            speed
        ))

    progress.setValue(N)

    if len(ret) == N:
        ret = np.array(ret)

    return ret
