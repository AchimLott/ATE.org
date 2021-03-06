# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 18:56:05 2019

@author: hoeren
"""
import os
import re

from ATE.org.listings import dict_project_paths, list_hardwaresetups, list_tests
from ATE.org.Templates import templating, translation_template
from ATE.org.validation import is_ATE_project, is_valid_test_name
from PyQt5 import QtCore, QtGui, QtWidgets, uic


class NewTestWizard(QtWidgets.QDialog):

    def __init__(self, parent):
        self.parent = parent
        super().__init__()

        my_ui = __file__.replace('.py', '.ui')
        if not os.path.exists(my_ui):
            raise Exception("can not find %s" % my_ui)
        uic.loadUi(my_ui, self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' '.join(re.findall('.[^A-Z]*', os.path.basename(__file__).replace('.py', ''))))

        self.parent = parent
        self.project_path = os.path.join(self.parent.workspace_path, self.parent.active_project)


        self.existing_tests = [''] + list_tests(self.project_path)
        self.existing_hardwaresetups = list_hardwaresetups(self.project_path)

        from ATE.org.validation import valid_test_name_regex
        rxTestName = QtCore.QRegExp(valid_test_name_regex)
        TestName_validator = QtGui.QRegExpValidator(rxTestName, self)
        self.TestName.setText("")
        self.TestName.setValidator(TestName_validator)
        self.TestName.textChanged.connect(self.verify)

        self.ForHardwaresetup.blockSignals(True)
        self.ForHardwaresetup.clear()
        self.ForHardwaresetup.addItems(self.existing_hardwaresetups)
        self.ForHardwaresetup.setCurrentIndex(0) # this is the empty string !
        self.ForHardwaresetup.currentIndexChanged.connect(self.verify)
        self.ForHardwaresetup.blockSignals(False)

        self.Finaltest.setChecked(True)
        self.Probing.setChecked(False)

        #TODO: add the whole flow thing

        self.Feedback.setStyleSheet('color: orange')

        self.CancelButton.clicked.connect(self.CancelButtonPressed)
        self.OKButton.clicked.connect(self.OKButtonPressed)
        self.OKButton.setEnabled(False)

        self.verify()
        self.show()

    def verify(self):
        self.Feedback.setText("")
        if not is_valid_test_name(self.TestName.text()):
            self.Feedback.setText("The test name can not contain the word 'TEST' in any form!")
        else:
            if self.Finaltest.isChecked():
                TestName = "%s_FT" % self.TestName.text()
            else:
                TestName = "%s_PR" % self.TestName.text()
            if TestName in self.existing_tests:
                self.Feedback.setText("Test already existing")
            else:
                pass #TODO: implement the whole flow thing

        if self.Feedback.text() == "":
            self.OKButton.setEnabled(True)
        else:
            self.OKButton.setEnabled(False)

    def CancelButtonPressed(self):
        self.accept()

    def OKButtonPressed(self):
        test_data = {}
        test_data['defines'] = 'test'
        test_data['test_name'] = self.TestName.text()
        test_data['for_hardwaresetup'] = self.ForHardwaresetup.currentText()
        if self.Finaltest.isChecked():
            test_data['test_target'] = 'FT'
        else:
            test_data['test_target'] = 'PR'
        create_new_test(self.parent.active_project_path, test_data)
        self.accept()

def create_new_test(project_path, test_data):
    '''
    given a project_path, a product_name (in product_data),
    create the appropriate definition file for this new product.

        test_data = {'defines' : 'test',
                     'test_name' : str,
                     'for_hardwaresetup' : str
                     'test_target' : str --> is 'FT' for Final Test and 'PR' for probing
                     #TODO: add the whole flow stuff here
                     }
    '''
    if is_ATE_project(project_path):
        test_class = "%s_%s%s" % (test_data['test_name'], test_data['for_hardwaresetup'], test_data['test_target'])
        if test_data['test_target'] == 'FT':
            test_root = dict_project_paths(project_path)['test_product_root']
        else:
            test_root = dict_project_paths(project_path)['test_die_root']
        test_path = os.path.join(test_root, "%s.py" % test_class)

        translation = translation_template(project_path)
        translation['TSTCLASS'] = test_class
        templating('test.py', test_path, translation)

def new_test_dialog(parent):
    newTestWizard = NewTestWizard(parent)
    newTestWizard.exec_()
    del(newTestWizard)

if __name__ == '__main__':
    import sys, qdarkstyle
    from ATE.org.actions.dummy_main import DummyMainWindow

    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    dummyMainWindow = DummyMainWindow()
    dialog = NewTestWizard(dummyMainWindow)
    dummyMainWindow.register_dialog(dialog)
    sys.exit(app.exec_())
