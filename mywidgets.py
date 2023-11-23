import numpy

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import *


class FovDisplay(QWidget):
    '''
    Widget affichant le schéma montrant l'angle de vue de l'appareil photo
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFixedSize(300, 142)
        self._renderer = QSvgRenderer()

        self._min_m = 0.01
        self._max_m = 999
        self._focal_length = float(24)
        self._sensor_size = (22.2, 14.8)
        self._focusing_distance = 3.0 # distance du capteur au plan de netteté

    @property
    def focus_plane_width(self):
        return (self._focusing_distance-0.001*self._focal_length) * self._sensor_size[0] / self._focal_length

    @property
    def focus_plane_height(self):
        return (self._focusing_distance-0.001*self._focal_length) * self._sensor_size[1] / self._focal_length

    @property
    def fov_angle(self):
        return 2*numpy.arctan(numpy.sqrt(self._sensor_size[0]**2 + self._sensor_size[1]**2) / (2*self._focal_length)) * 180/numpy.pi

    @property
    def focusing_distance(self):
        return self._focusing_distance

    def setFocusDistance(self, d):
        self._focusing_distance = float(self.clip(d, self._min_m, self._max_m))
        self.update()

    def setFocalLength(self, f):
        self._focal_length = float(self.clip(f, 1.0, 1000.0))
        self.update()
    
    def setSensorSize(self, size):
        if len(size) != 2:
            raise ValueError("`size` should be a tuple (w, h)")
        self._sensor_size = size
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        svg_bytes = self.generate_svg()
        self._renderer.load(svg_bytes)
        self._renderer.render(painter)
        painter.end()

    def sizeHint(self):
        return QSize(300, 142)

    @staticmethod
    def clip(x, vmin, vmax):
        if x < vmin:
            return vmin
        if x > vmax:
            return vmax
        return x

    def generate_svg(self):
        width = self.size().width()
        height = self.size().height()

        svg = list()
        svg.append('''<?xml version="1.0" encoding="utf-8"?>
<svg
xmlns="http://www.w3.org/2000/svg"
version="1.1"
width="{w}px"
height="{h}px"
viewBox="0 0 {w} {h}"
>'''.format(w=int(width), h=int(height)))

        svg.append('''  <g
    id="fov"
    transform="translate(0.5,0.5)">
    <rect
        fill="white"
        stroke="#888888"
        stroke-width="1"
        x="0" y="0"
        width="{w}" height="{h}"
        rx="4" ry="4" />
    <path
      fill="#fff9e5"
      stroke="none"
      stroke-width="1"
      d="M 15,70 l 150,-60 80,120 z" />
    <path
      fill="#f0ead6"
      stroke="none"
      stroke-width="1"
      d="M 165,10 l 80,120 l -80,-42 z" />
    <path
      fill="#eeeeee"
      stroke="none"
      stroke-width="1"
      d="M 165,10 l 80,40 v 80 z" />
    <path
      fill="none"
      stroke="#ffcf31"
      stroke-width="1"
      d="M 15,70 l 150,-60 80,120 z" />
    <path
      fill="none"
      stroke="red"
      stroke-width="1"
      stroke-dasharray="5,5"
      d="M 20,70 h 185" />
    <path
      fill="none"
      stroke="black"
      stroke-width="1"
      d="M 165,10 l 80,40 v 80" />
    <path
      fill="none"
      stroke="#c0ad71"
      stroke-width="1"
      d="M 165,10 v 78 l 80,42" />
    <g
      id="distance"
      transform="translate(91,63)">
      <rect
        fill="white"
        stroke="red"
        stroke-width="1"
        x="0" y="0"
        width="38" height="14"
        rx="3" ry="3" />
      <text
        x="19" y="10.5"
        text-anchor="middle"
        font-family="Segoe UI"
        font-size="10"
        fill="red">
        {focus_num:.3g} m
      </text>
    </g>
    <g
      id="largeur"
      transform="translate(200,20)">
      <text
        x="0" y="0"
        text-anchor="left"
        font-family="Segoe UI"
        font-size="12"
        fill="black">
        {w_num:.3g} m
      </text>
    </g>
    <g
      id="hauteur"
      transform="translate(250,93)">
      <text
        x="0" y="0"
        text-anchor="left"
        font-family="Segoe UI"
        font-size="12"
        fill="black">
        {h_num:.3g} m
      </text>
    </g>
    <g
      id="angle"
      transform="translate(0,60)">
      <path
        fill="none"
        stroke="black"
        stroke-width="1"
        d="M 30,-2 c 14,4,18,15,14,26" />
      <text
        x="35" y="-10"
        text-anchor="middle"
        font-family="Segoe UI"
        font-size="12"
        fill="black">
        {angle_num:.3g} °
      </text>
    </g>
  </g>'''.format(w=int(width-1), h=int(height-1),
                 focus_num=self.focusing_distance,
                 w_num=self.focus_plane_width,
                 h_num=self.focus_plane_height,
                 angle_num=self.fov_angle))
        svg.append("</svg>")
        
        return '\n'.join(svg).encode('utf-8')


class FNumberBar(QAbstractSlider):
    '''
    Slider de sélection de l'ouverture de l'appariel photo
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setFixedHeight(27)
        self.setMinimumWidth(300)
        self.setOrientation(Qt.Horizontal)
        self._renderer = QSvgRenderer()

        # self.f_true_values = 2**((numpy.arange(25)+3)/6)
        self._f_true_values = numpy.array([1.4142135623730951, 1.5874010519681994, 1.7817974362806785, 2.0,
            2.244924096618746, 2.5198420997897464, 2.8284271247461903, 3.174802103936399, 3.563594872561357, 4.0,
            4.489848193237491, 5.039684199579493, 5.656854249492381, 6.3496042078727974, 7.127189745122715, 8.0,
            8.979696386474982, 10.079368399158986, 11.313708498984761, 12.699208415745595, 14.25437949024543, 16.0,
            17.959392772949972, 20.158736798317967, 22.627416997969522], dtype=float)
        self._f_values = numpy.array([1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 2.8, 3.2, 3.5, 4.0, 4.5, 5.0, 5.6, 6.3, 7.1, 8.0, 9.0, 10.0, 11.0, 13.0, 14.0, 16.0, 18.0, 20.0, 22.0], dtype=float)
        self.setRange(0, len(self._f_values)-1)

        self._sensor_size = (22.2, 14.8)
        self._confusion = float(0.015)
        
        self.setValue(15)
    
    @property
    def confusion_size(self):
        '''
        Retourne le diamètre du cercle de confusion pour une taille de capteur donnée.
        `sensor_size` : (l, h) en mm
        '''
        return self._confusion

    @property
    def f_number(self):
        return float(self._f_true_values[self.value()])

    def setFNumber(self, f):
        index = numpy.argmin(numpy.abs(f-self._f_values))
        self.setValue(index)

    def setSensorSize(self, size):
        if len(size) != 2:
            raise ValueError("`size` should be a tuple (w, h)")
        self._sensor_size = size
        self.update()
    
    def setConfusionSize(self, size):
        self._confusion = size
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)

        svg_bytes = self.generate_svg()
        self._renderer.load(svg_bytes)
        self._renderer.render(painter)
        painter.end()

    def sizeHint(self):
        return QSize(400, 27)

    def _update_f_number(self, e):
        e.accept()
        vmin, vmax = self.minimum(), self.maximum()
        d_width = self.size().width() - 30 - 2
        step_size = d_width / (vmax-vmin)
        click_x = e.x() - 15 + step_size/2
        pc = click_x / d_width
        value = int(vmin + pc * (vmax-vmin))
        self.setValue(value)

    def mouseMoveEvent(self, e):
        self._update_f_number(e)

    def mousePressEvent(self, e):
        self._update_f_number(e)
    
    @staticmethod
    def airy_disc_size(f_number):
        '''
        Limite de diffraction (tache d'Airy)
        '''
        lambda_ = 550e-9 # m   longueur d'onde de la lumière
        return 2.44*lambda_*f_number*1000 # mm

    def generate_svg(self):
        width = self.size().width()
        height = 27
        d_width = int(width-1 - 30)
        steps = len(self._f_values)

        f_values = [i for i in range(steps) if i%3==0]
        f_minors = [i for i in range(steps) if i%3!=0]

        f_number_px = int(15 + d_width * self.value()/(steps - 1))

        svg = list()
        svg.append('''<?xml version="1.0" encoding="utf-8"?>
<svg
xmlns="http://www.w3.org/2000/svg"
version="1.1"
width="{w}px"
height="{h}px"
viewBox="0 0 {w} {h}"
>'''.format(w=int(width), h=int(height)))

        svg.append('''  <g
    id="f-number"
    transform="translate(0.5,0.5)">
    <rect
      fill="white"
      stroke="#888888"
      stroke-width="1"
      x="0" y="0"
      width="{w}" height="26"
      rx="4" ry="4" />
    <text
      x="28" y="16.5"
      text-anchor="left"
      font-family="Segoe UI"
      font-size="10"
      fill="#0066c5">
      f ⁄
    </text>'''.format(w=int(width-1)))

        for value in f_values:
            if self.airy_disc_size(self._f_true_values[value]) > self.confusion_size:
                color = "#ff6a25"
            else:
                color = "black"
            location_px = int(15 + d_width * value/(steps - 1))
            svg.append('''    <text
      x="{}" y="17"
      text-anchor="middle"
      font-family="Segoe UI"
      font-size="12"
      fill="{}">
      {:.3g}
    </text>'''.format(int(location_px), color, self._f_values[value]))

        for value in f_minors:
            if self.airy_disc_size(self._f_true_values[value]) > self.confusion_size:
                color = "#ff6a25"
            else:
                color = "black"
            location_px = int(15 + d_width * value/(steps - 1))
            svg.append('''    <text
      x="{}" y="17"
      text-anchor="middle"
      font-family="Segoe UI"
      font-size="12"
      fill="{}">
      &#183;
    </text>'''.format(int(location_px), color))

        if self.airy_disc_size(self._f_true_values[self.value()]) > self.confusion_size:
            color = "#ff6a25"
        else:
            color = "#0066c5"
        svg.append('''    <g
      id="f-line">
      <line
        stroke="{color}"
        stroke-width="1"
        x1="{f}" y1="0"
        x2="{f}" y2="26" />
      <rect
        fill="white"
        stroke="{color}"
        stroke-width="1"
        x="{f_left}" y="6"
        width="26" height="14"
        rx="3" ry="3" />
      <text
        x="{f}" y="16.5"
        text-anchor="middle"
        font-family="Segoe UI"
        font-size="10"
        fill="{color}">
        {f_num:.3g}
      </text>
    </g>'''.format(f_num=self._f_values[self.value()],
                   f=f_number_px,
                   f_left=f_number_px-13,
                   color=color))
        svg.append('''  </g>
</svg>''')
        
        return '\n'.join(svg).encode('utf-8')


class DofBar(QAbstractSlider):
    '''
    Slider de sélection de la distance de mise au point de l'appareil photo
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setFixedHeight(58)
        self.setMinimumWidth(300)
        self.setOrientation(Qt.Horizontal)
        self._renderer = QSvgRenderer()

        self.setRange(0, 999) # slider avec 1000 positions

        self._origin = float(0.125)
        # self._origin = float(0.25)
        self._max_m = float(999.0)

        self._focal_length = float(24)
        self._f_number = 8.0
        self._sensor_size = (22.2, 14.8)
        self._confusion = float(0.015)
        self._focusing_distance = float(3.0)

    @property
    def confusion_size(self):
        '''
        Retourne le diamètre du cercle de confusion pour une taille de capteur donnée.
        `sensor_size` : (l, h) en mm
        '''
        return self._confusion

    @property
    def minimum_focusing_distance(self):
        Dn = float(self._origin)
        f = float(self._focal_length)
        N = float(self._f_number)
        c = float(self.confusion_size)
        H = f + f**2/(N*c)
        return float(Dn*(2*f - H)/(1000*Dn + f - H))

    @property
    def focusing_distance(self):
        return self._focusing_distance

    @property
    def hyperfocal_distance(self):
        '''
        Distance hyperfocale en m
        '''
        f = float(self._focal_length)
        N = float(self._f_number)
        c = float(self.confusion_size)
        return (f + f**2/(N*c)) / 1000

    @property
    def focusing_distance_near(self):
        '''
        Distance minimale de netteté (m)
        '''
        s = self.focusing_distance
        f = float(self._focal_length)
        H = self.hyperfocal_distance
        return s * (H - f/1000) / (H + s - 2*f/1000)

    @property
    def focusing_distance_far(self):
        '''
        Distance maximale de netteté (m)
        '''
        s = self.focusing_distance
        H = self.hyperfocal_distance
        if (H - s) <= 0:
            return numpy.Infinity
        else:
            f = float(self._focal_length)
            return s * (H - f/1000) / (H - s)

    def setFocusDistance(self, d):
        self._focusing_distance = float(self.clip(d, self.minimum_focusing_distance, self._max_m))
        vmin, vmax = self.minimum(), self.maximum()
        pc = self._scalein(self._focusing_distance)
        value = int(vmin + pc * (vmax-vmin))
        self.setValue(value)
        # self.update()

    def setFocalLength(self, f):
        self._focal_length = float(self.clip(f, 1.0, 1000.0))
        self.update()
    
    def setFNumber(self, f):
        self._f_number = float(self.clip(f, 1.0, 22.0))
        self.update()
    
    def setSensorSize(self, size):
        if len(size) != 2:
            raise ValueError("`size` should be a tuple (w, h)")
        self._sensor_size = size
        self.update()

    def setConfusionSize(self, size):
        self._confusion = size
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        svg_bytes = self.generate_svg()
        self._renderer.load(svg_bytes)
        self._renderer.render(painter)
        painter.end()

    def sizeHint(self):
        return QSize(400, 58)

    def _scalein(self, x_m):
        if x_m >= self._origin:
            a = numpy.exp(self._origin**(1/3))
            return float(1.0-a*numpy.exp(-x_m**(1/3)))
        else:
            return float(0.0)

    def _scaleout(self, y_pc):
        if y_pc < 0.0:
            return self._origin
        elif y_pc < 1.0:
            a = numpy.exp(self._origin**(1/3))
            return numpy.log(-a/(y_pc - 1.0))**3
        else:
            return self._max_m

    def _update_focusing_distance(self, e):
        e.accept()
        vmin, vmax = self.minimum(), self.maximum()
        d_width = self.size().width() - 30 - 2
        step_size = d_width / (vmax-vmin)
        click_x = e.x() - 15 + step_size/2
        pc = click_x / d_width
        self.setFocusDistance(self._scaleout(pc))

    def mouseMoveEvent(self, e):
        self._update_focusing_distance(e)

    def mousePressEvent(self, e):
        if (26-8) < e.y(): #  < (52+8)
            self._update_focusing_distance(e)
        else:
            e.ignore()

    @staticmethod
    def clip(x, vmin, vmax):
        if x < vmin:
            return vmin
        if x > vmax:
            return vmax
        return x

    def generate_svg(self):
        s = self.focusing_distance
        
        f = float(self._focal_length)
        N = float(self._f_number)
        c = float(self.confusion_size)

        # # Formules fonctions de Dn et Df
        # s = 2*Df*Dn/(Df + Dn) # distance de mise au point
        # c = f**2*(Df - Dn)/(N*(2000*Df*Dn - f*(Df + Dn))) # diamètre du cercle de confusion 

        # Distance hyperfocale en m
        H = (f + f**2/(N*c)) / 1000
        # Distance minimale de netteté
        Dn = s * (H - f/1000) / (H + s - 2*f/1000)
        # Distance maximale de netteté
        if (H - s) <= 0:
            Df = numpy.Infinity
        else:
            Df = s * (H - f/1000) / (H - s)
        
        width = self.size().width()
        height = 58
        d_width = int(width - 30 - 2)

        dof_origin = self._origin
        dof_values = [v for v in (0.125, 0.25, 1, 2, 3, 4, 6, 10, 20, 50) if v > dof_origin]
        dof_values.insert(0, dof_origin)
        dof_minors = [v for v in (0.5, 1.5, 2.5, 5) if v > dof_origin]

        Dn_hyperfocal = H/2

        Dn_h_px = int(15 + d_width * self._scalein(Dn_hyperfocal))
        H_px = int(15 + d_width * self._scalein(H))
        focusing_distance_px = int(15 + d_width * self._scalein(s))
        Dn_px = int(15 + d_width * self._scalein(Dn))
        Df_px = int(15 + d_width * self._scalein(Df))

        if Df >= 999.5:
            dof_px = (int(width-1 + 5) - Dn_px)
        else:
            dof_px = (Df_px - Dn_px)
        
        spacing = Df_px - Dn_px
        if spacing < 30:
            offset1 = (30 - spacing) // 2
        else:
            offset1 = 0
        if Dn_px - offset1 < 15:
            offset2 = 15 - (Dn_px - offset1)
        elif Df_px + offset1 > (width-1 - 15):
            offset2 = (width-1 - 15) - (Df_px + offset1)
        else:
            offset2 = 0

        if Df >= 999.5:
            Df_str = '&#8734;' # infinity
        else:
            Df_str = '{:.3g}'.format(Df)

        svg = list()
        svg.append('''<?xml version="1.0" encoding="utf-8"?>
<svg
xmlns="http://www.w3.org/2000/svg"
version="1.1"
width="{w}px"
height="{h}px"
viewBox="0 0 {w} {h}"
>'''.format(w=int(width), h=int(height)))

        svg.append('''  <g
    id="dof-line"
    transform="translate(0.5,25.5)">
    <rect
    fill="white"
    stroke="none"
    stroke-width="1"
    x="0" y="0"
    width="{w}" height="26"
    rx="4" ry="4" />
    <path
    fill="#b6ddff"
    stroke="none"
    d="M {Dn_h},22 h {H_w} a 4,4 0 0 1 -4,4 h {H_wb} z" />
    <line
        stroke="#0066c5"
        stroke-width="1"
        x1="{H}" y1="22"
        x2="{H}" y2="26" />
    <rect
    fill="none"
    stroke="#888888"
    stroke-width="1"
    x="0" y="0"
    width="{w}" height="26"
    rx="4" ry="4" />
    <text
    x="32" y="16"
    text-anchor="left"
    font-family="Segoe UI"
    font-size="10"
    fill="red">
    m
    </text>'''.format(w=int(width-1), Dn_h=Dn_h_px, H=H_px, H_w=int(width-1 - Dn_h_px), H_wb=-int(width-1 - Dn_h_px - 4)))

        for dof_value in dof_values: # (0.3, 1, 2, 3, 4, 6, 10, 20, 50)
            location_pc = self._scalein(dof_value)
            location_px = 15 + d_width * location_pc
            svg.append('''    <text
    x="{}" y="17"
    text-anchor="middle"
    font-family="Segoe UI"
    font-size="12"
    fill="black">
    {:.3g}
    </text>'''.format(int(location_px), dof_value))

        for dof_value in dof_minors: # (0.5, 1.5, 2.5)
            location_pc = self._scalein(dof_value)
            location_px = 15 + d_width * location_pc
            svg.append('''    <text
    x="{}" y="17"
    text-anchor="middle"
    font-family="Segoe UI"
    font-size="12"
    fill="black">
    &#183;
    </text>'''.format(int(location_px)))

        svg.append('''    <text
    x="{}" y="17"
    text-anchor="left"
    font-family="Segoe UI"
    font-size="12"
    fill="black">
    &#8734;
    </text>'''.format(int(width-1 - 15)))

        svg.append('''    <g
    id="focus-line">
    <rect
        fill="none"
        stroke="black"
        stroke-width="1"
        x="{Dn}" y="-6"
        width="{dof}" height="38"
        rx="3" ry="3" />
    <line
        stroke="red"
        stroke-width="1"
        x1="{focus}" y1="-6"
        x2="{focus}" y2="32" />'''.format(Dn=Dn_px, Df=Df_px, focus=focusing_distance_px, dof=dof_px))

        svg.append('''      <g
        id="near"
        transform="translate(0,-25)">
        <line
        stroke="#0066c5"
        stroke-width="1"
        x1="{Dn}" y1="11"
        x2="{Dn}" y2="18" />
        <rect
        fill="#0066c5"
        stroke="#0066c5"
        stroke-width="1"
        x="{Dn_left}" y="0"
        width="30" height="14"
        rx="3" ry="3" />
        <text
        x="{Dn_center}" y="10"
        text-anchor="middle"
        font-family="Segoe UI"
        font-size="10"
        fill="white">
        {Dn_num:.3g}
        </text>
    </g>
    <g
        id="far"
        transform="translate(0,-25)">
        <line
        stroke="#0066c5"
        stroke-width="1"
        x1="{Df}" y1="11"
        x2="{Df}" y2="18" />
        <rect
        fill="#0066c5"
        stroke="#0066c5"
        stroke-width="1"
        x="{Df_left}" y="0"
        width="30" height="14"
        rx="3" ry="3" />
        <text
        x="{Df_center}" y="10"
        text-anchor="middle"
        font-family="Segoe UI"
        font-size="10"
        fill="white">
        {Df_num}
        </text>
    </g>
    <g
        id="focus"
        transform="translate(0,6)">
        <rect
        fill="white"
        stroke="red"
        stroke-width="1"
        x="{focus_left}" y="0"
        width="30" height="14"
        rx="3" ry="3" />
        <text
        x="{focus}" y="10.5"
        text-anchor="middle"
        font-family="Segoe UI"
        font-size="10"
        fill="red">
        {focus_num:.3g}
        </text>
    </g>'''.format(Dn_num=Dn,
                    Dn=Dn_px,
                    Dn_left=Dn_px-15-offset1+offset2,
                    Dn_center=Dn_px-offset1+offset2,
                    Df_num=Df_str,
                    Df=Df_px,
                    Df_left=Df_px-15+offset1+offset2,
                    Df_center=Df_px+offset1+offset2,
                    focus_num=s,
                    focus=focusing_distance_px,
                    focus_left=focusing_distance_px-15))

        svg.append('''    </g>
</g>
</svg>''')

        return '\n'.join(svg).encode('utf-8')

