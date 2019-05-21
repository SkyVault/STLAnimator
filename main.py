import sys
import math
import os
import random
from PIL import Image

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QOpenGLWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QLabel,
    QScrollArea,
    QSlider,
    QFileDialog)

from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtCore import pyqtSlot

from stl import mesh

from enum import Enum

import OpenGL.GL as gl
import OpenGL.GLU as glu


class ProgramStates(Enum):
    POSITIONING = 1
    RENDERING = 2


class StartStopButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("Start")


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'DevWindow'
        self.left = 10
        self.top = 10
        self.width = 940
        self.height = 480
        self.initUI()

        self.currentFrame = 0
        self.numberOfFrames = 100

    def initUI(self):
        self.setWindowTitle(self.title)

        self.models = {}
        self.models_ui = {}
        self.stl_models = {}

        self.setGeometry(self.left, self.top, self.width, self.height)

        self.programState = ProgramStates.POSITIONING
        self.glWidget = GLWidget(self.models, self.models_ui, self)

        self.mainContainerLayout = QVBoxLayout()
        self.mainLayout = QHBoxLayout()

        self.mainLayout.addWidget(self.glWidget)

        # Side bar
        self.sidePanel = QVBoxLayout()
        self.sidePanelWidget = QWidget()
        self.sidePanelWidget.setLayout(self.sidePanel)

        # Load model button
        self.loadModelBtn = QPushButton('Load STL file')
        self.loadModelBtn.clicked.connect(self.loadModel)

        self.renderAnimationBtn = QPushButton('Render Animation')
        self.renderAnimationBtn.clicked.connect(self.renderAnimation)

        self.sidePanel.addWidget(self.loadModelBtn)
        self.sidePanel.addWidget(self.renderAnimationBtn)

        self.sidePanelScroll = QScrollArea()
        self.sidePanelScroll.setWidgetResizable(True)
        self.sidePanelScroll.setWidget(self.sidePanelWidget)

        self.mainLayout.addWidget(self.sidePanelScroll)

        # Construct timeline
        self.timeLineLayout = QHBoxLayout()

        self.frameSlider = QSlider(Qt.Horizontal)
        self.frameSlider.setFocusPolicy(Qt.StrongFocus)
        self.frameSlider.setTickPosition(QSlider.TicksAbove)
        self.frameSlider.setTickInterval(1)
        self.frameSlider.setSingleStep(1)
        self.frameSlider.valueChanged.connect(self.frameChanged)

        self.currentFrameLabel = QLabel("Frame 0")

        self.timeLineLayout.addWidget(self.frameSlider)
        self.timeLineLayout.addWidget(self.currentFrameLabel)

        self.mainContainerLayout.addLayout(self.mainLayout)
        self.mainContainerLayout.addLayout(self.timeLineLayout)

        self.setLayout(self.mainContainerLayout)

        self.show()

    @pyqtSlot()
    def frameChanged(self):
        self.currentFrameLabel.setText(f"Frame {self.frameSlider.value()}")

    @pyqtSlot()
    def renderAnimation(self):
        self.frameSlider.setValue(0)
        self.programState = ProgramStates.RENDERING
        self.currentFrame = 0

    @pyqtSlot()
    def loadModel(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "All Files (*);;STL Files (*.stl)",
            options=options)

        if fileName:
            print(f"Loading STL model: {fileName}")

            stl_model = mesh.Mesh.from_file(fileName)

            fileName = fileName + str(len(self.models))

            self.stl_models[fileName] = stl_model

            model = Model(stl_model, self)
            model.translation = (0, 0.0, 0)
            model.rotation = (0.0, 0, 0)
            model.scale = (0.01, 0.01, 0.01)
            model.color = (
                0.05 + (random.random() * 0.08),
                0.05 + (random.random() * 0.08),
                0.05 + (random.random() * 0.08),
                1.0)
            print(model.color)
            self.models[fileName] = model

            # model.setKeyFrame(self.frameSlider.value())

            # Create the ui to edit the models properties
            flo = QFormLayout()

            translation = QHBoxLayout()
            rotation = QHBoxLayout()

            translationX = QLineEdit()
            translationX.setText(str(model.translation[0]))
            translationX.setValidator(QDoubleValidator(-99, 99, 2))
            translation.addWidget(translationX)

            translationY = QLineEdit()
            translationY.setText(str(model.translation[1]))
            translationY.setValidator(QDoubleValidator(-99, 99, 2))
            translation.addWidget(translationY)

            translationZ = QLineEdit()
            translationZ.setText(str(model.translation[2]))
            translationZ.setValidator(QDoubleValidator(-99, 99, 2))
            translation.addWidget(translationZ)

            rotationX = QLineEdit()
            rotationX.setText(str(model.rotation[0]))
            rotationX.setValidator(QDoubleValidator(-360, 360, 2))
            rotation.addWidget(rotationX)

            rotationY = QLineEdit()
            rotationY.setText(str(model.rotation[1]))
            rotationY.setValidator(QDoubleValidator(-360, 360, 2))
            rotation.addWidget(rotationY)

            rotationZ = QLineEdit()
            rotationZ.setText(str(model.rotation[2]))
            rotationZ.setValidator(QDoubleValidator(-360, 360, 2))
            rotation.addWidget(rotationZ)

            start = QPushButton('New Keyframe')
            hide = QPushButton('Hide')

            @pyqtSlot()
            def clickedStart():
                model.setKeyFrame(self.frameSlider.value())

            @pyqtSlot()
            def clickedHide():
                model.showing = not model.showing
                if hide.text() == 'Hide':
                    hide.setText('Show')
                else:
                    hide.setText('Hide')

            start.clicked.connect(clickedStart)
            hide.clicked.connect(clickedHide)

            self.models_ui[fileName] = {
                'X': translationX,
                'Y': translationY,
                'Z': translationZ,
                'RX': rotationX,
                'RY': rotationY,
                'RZ': rotationZ,
                'animToggle': start,
                'State': 'Start',
            }

            flo.addRow("Model: ", QLabel(os.path.basename(fileName)))
            flo.addRow("Translation", translation)
            flo.addRow("Rotation", rotation)

            buttons = QHBoxLayout()
            buttons.addWidget(start)
            buttons.addWidget(hide)

            flo.addRow("Controls", buttons)

            widget = QWidget()
            widget.setLayout(flo)

            self.sidePanel.addWidget(widget)

    def createModel(self, stl_file):
        pass


class GLWidget(QOpenGLWidget):
    def __init__(self, models, models_ui, parent=None):
        super().__init__(parent)
        self.setFixedSize(640, 480)

        self.models = models
        self.models_ui = models_ui

        self.timer = 0
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000/10.0)

        self.width = 640 / 2
        self.height = 480

        self.app = parent

    def resizeGL(self, width, height):
        side = min(width, height)
        if side < 0:
            return

        gl.glViewport((width - side) // 2, (height - side) // 2, side, side)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45, 1.0*self.width/self.height, 0.1, 100.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

        self.width = width
        self.height = height

    def initializeGL(self):
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)

    def paintGL(self):
        self.timer += 1

        gl.glClearColor(0.2, 0.2, 0.2, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(45, 1.0*self.width/self.height, 0.1, 100.0)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        glu.gluLookAt(
            0.0, -10.0, 10.0,
            0, 0, 0,
            0, 1.0, 0)

        # gl.glLoadIdentity()

        gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_EMISSION)
        gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)
        gl.glEnable(gl.GL_COLOR_MATERIAL)

        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        # gl.glEnable(gl.GL_BLEND)
        gl.glLight(gl.GL_LIGHT0, gl.GL_POSITION,  (1, 1, 1))
        gl.glLight(gl.GL_LIGHT0, gl.GL_AMBIENT, (0.02, 0.02, 0.02))
        gl.glLight(gl.GL_LIGHT0, gl.GL_DIFFUSE, (0.05, 0.05, 0.05))
        gl.glLightf(gl.GL_LIGHT0, gl.GL_CONSTANT_ATTENUATION, 0.4)

        if self.app.programState == ProgramStates.POSITIONING:
            for modName in self.models:
                mod = self.models[modName]
                ui = self.models_ui[modName]

                if not mod.showing:
                    continue
                try:
                    mod.translation = (
                        float(ui['X'].text()),
                        float(ui['Y'].text()),
                        float(ui['Z'].text()),
                    )
                    mod.rotation = (
                        float(ui['RX'].text()),
                        float(ui['RY'].text()),
                        float(ui['RZ'].text()),
                    )
                except ValueError:
                    pass

                gl.glPushMatrix()
                # gl.glLoadIdentity()
                gl.glTranslate(*mod.translation)

                gl.glRotatef(mod.rotation[0], 1, 0, 0)
                gl.glRotatef(mod.rotation[1], 0, 1, 0)
                gl.glRotatef(mod.rotation[2], 0, 0, 1)

                gl.glScale(*mod.scale)

                mod.draw()
                gl.glPopMatrix()

        elif self.app.programState == ProgramStates.RENDERING:
            if self.app.currentFrame >= self.app.numberOfFrames:
                self.app.programState = ProgramStates.POSITIONING
                self.app.currentFrame = 0
                return

            for modName in self.models:
                mod = self.models[modName]
                gl.glPushMatrix()

                def lerpP(a, b, p):
                    return a * p + (1 - p) * b

                start = mod.getStart()[1]
                frames, end = mod.getEnd()

                perc = float(self.app.currentFrame) / frames

                if perc <= 1:
                    trans = (
                        lerpP(float(end[0]), float(start[0]), perc),
                        lerpP(float(end[1]), float(start[1]), perc),
                        lerpP(float(end[2]), float(start[2]), perc),
                    )

                    gl.glTranslate(*trans)
                else:
                    gl.glTranslate(*end)

                gl.glRotatef(mod.rotation[0], 1, 0, 0)
                gl.glRotatef(mod.rotation[1], 0, 1, 0)
                gl.glRotatef(mod.rotation[2], 0, 0, 1)

                gl.glScale(*mod.scale)

                mod.draw()
                gl.glPopMatrix()

            # Capture the frame
            buff = gl.glReadPixels(
                    0, 0,
                    self.width, self.height,
                    gl.GL_RGB, gl.GL_UNSIGNED_BYTE)

            imgName = f"./tmp_frames/{self.app.currentFrame}.bmp"
            imout = Image.frombytes(
                    mode="RGB", size=(self.width, self.height), data=buff)
            imout = imout.transpose(Image.FLIP_TOP_BOTTOM)

            self.app.frameSlider.setValue(self.app.currentFrame)

            print(f"Rendering Frame {self.app.currentFrame}")

            imout.save(imgName)

            self.app.currentFrame += 1


class Model():
    def __init__(self, stl_model, app):
        self.stl = stl_model
        self.app = app

        self.showing = True

        # self.translation = (-9, -4, -30)
        # self.rotation = (-45.0, 1, 0, 0)
        # self.scale = (0.2, 0.2, 0.2)

        self.translation = (0, 0, 0)
        self.rotation = (0, 0, 0, 0)
        self.scale = (0, 0, 0)

        self.start = (0, 0, 0)
        self.end = (0, 0, 0)

        self.currentKeyframe = 0

        self.keyframes = []

        self.color = (0.6, 0.6, 0.6)

    def setKeyFrame(self, currentFrame):
        self.keyframes.append((
            currentFrame,
            self.translation
        ))

    def getStart(self):
        frame = self.app.currentFrame

        if self.currentKeyframe + 1 >= len(self.keyframes):
            return self.keyframes[self.currentKeyframe]

        if frame >= self.keyframes[self.currentKeyframe + 1][0]:
            if self.currentKeyframe < len(self.keyframes) - 1:
                self.currentKeyframe += 1

        return self.keyframes[self.currentKeyframe]

    def getEnd(self):
        if self.currentKeyframe + 1 >= len(self.keyframes):
            return self.keyframes[self.currentKeyframe]
        return self.keyframes[self.currentKeyframe + 1]

    def draw(self):
        if self.app.programState == ProgramStates.POSITIONING:
            self.currentKeyframe = 0

        gl.glShadeModel(gl.GL_SMOOTH)
        gl.glBegin(gl.GL_TRIANGLES)

        for i in range(0, len(self.stl.v0)):
            p0 = self.stl.v0[i]
            p1 = self.stl.v1[i]
            p2 = self.stl.v2[i]

            no = self.stl.normals[i]

            length = math.sqrt(no[0]**2 + no[1]**2 + no[2]**2)

            if length != 0:
                no = (no[0] / length, no[1] / length, no[2] / length)

            # gl.glNormal3f(no[0], no[1], no[2])
            gl.glNormal3f(*no)
            gl.glColor4f(*self.color, 1)
            gl.glVertex3f(*p0)
            gl.glVertex3f(*p1)
            gl.glVertex3f(*p2)

        gl.glEnd()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
