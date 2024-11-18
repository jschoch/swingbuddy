import sys
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QWidget,QVBoxLayout,QHBoxLayout
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import QTimer, QRectF
import os
import random
import pandas as pd

class ImageOverlay(QGraphicsView):
    def __init__(self, pixmap, data,raw_frames=[]):
        super().__init__()

        self.data = data
        self.index = 0
        
        # Load the base image
        self.pixmap = pixmap
        self.raw_frames = raw_frames
        
        if not self.pixmap.isNull():
            # Create a QGraphicsScene and add the base image to it
            self.scene = QGraphicsScene(self)
            self.image_item = QGraphicsPixmapItem(self.pixmap)
            self.scene.addItem(self.image_item)

            self.static_item = self.make_static_frame()

            self.scene.addItem(self.static_item)
            # Pre-render all frames
            self.frames = []
            self.make_frames(self.raw_frames)
            # Create a QGraphicsPixmapItem for the overlay and add it to the scene
            self.overlay_item = QGraphicsPixmapItem(self.frames[self.index])
            self.scene.addItem(self.overlay_item)

            # Set the scene for the view
            self.setScene(self.scene)
            
        else:
            print(f"Failed to load image. {os.getcwd()}")

    def make_static_frame(self):
        frame_pixmap = QPixmap(pixmap.size())
        frame_pixmap.fill(QColor('transparent'))
        
        painter = QPainter(frame_pixmap)
        pen = QPen(QColor('green'), 5)  # Red color and 2 pixels thick line
        painter.setPen(pen)
        painter.drawLine(0,0, 800,600)
        painter.end()
        return QGraphicsPixmapItem(frame_pixmap)

    def make_frames(self,raw_frames):
        for i in range(len(raw_frames)):
                self.make_frame(i)
    

    def make_frame(self,i):
        frame_pixmap = QPixmap(pixmap.size())
        frame_pixmap.fill(QColor('transparent'))
        
        painter = QPainter(frame_pixmap)
        pen = QPen(QColor('red'), 2)  # Red color and 2 pixels thick line
        painter.setPen(pen)
        
        x_pos = self.data['HipMiddle_x'].iloc[i].copy()
        #ipainter.drawLine(0, random.randint(0, 600), point[0], point[1])
        h = frame_pixmap.height() 
        print(f" Xpos: {x_pos}, h: {h}")
        painter.drawLine(x_pos/2, 0, x_pos/2, h)
        #painter.drawLine(0,0,800,800)
        painter.end()
        self.frames.append(frame_pixmap)

    def next_frame(self):
        if self.index < len(self.frames):
            self.image_item.setPixmap(self.raw_frames[self.index])
            self.overlay_item.setPixmap(self.frames[self.index])
            self.index += 1
        else:
            #self.timer.stop()  # Stop the timer when all frames have been displayed
            self.index = 0

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        new_size = event.size()
        scene_rect = QRectF(0, 0, new_size.width(), new_size.height())
        self.scene.setSceneRect(scene_rect)

        # Scale the items to fit the new size
        scale_x = new_size.width() / self.pixmap.width()
        scale_y = new_size.height() / self.pixmap.height()
        scale_factor = min(scale_x, scale_y)
        
        self.image_item.setScale(scale_factor)
        self.overlay_item.setScale(scale_factor)
        self.static_item.setScale(scale_factor)  # Scale the static item as well
        print(f"scale factor was {scale_factor}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    image_path = "20241102-101435-left_screen.png"
    rdata = {'Unnamed: 0': {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}, 't': {0: 0.0, 1: 0.0335697399527186, 2: 0.0671394799054373, 3: 0.100709219858156, 4: 0.1342789598108747}, 'Hip_x': {0: 313.3020846048991, 1: 312.3631410598755, 2: 315.73167069753, 3: 313.3020846048991, 4: 313.5047060648601}, 'Hip_y': {0: 688.9698387384415, 1: 685.3385734558105, 2: 685.4398770332336, 3: 686.4925003051758, 4: 682.6849014759064}, 'Hip_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'RHip_x': {0: 303.053066889445, 1: 303.8222929636638, 2: 304.1423689524333, 3: 299.6367276509602, 4: 298.4873081843059}, 'RHip_y': {0: 688.9698387384415, 1: 687.0467430353165, 2: 685.4398770332336, 3: 684.7843306064606, 4: 682.6849014759064}, 'RHip_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'RKnee_x': {0: 352.5899858474731, 1: 351.65104230244947, 2: 352.1551904678345, 3: 350.8818162282307, 4: 346.8767013549804}, 'RKnee_y': {0: 864.9113054275513, 1: 864.6963793039322, 2: 862.5906407833099, 3: 859.017639875412, 4: 856.2192852497101}, 'RKnee_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'RAnkle_x': {0: 349.17364660898846, 1: 349.94287268320727, 2: 348.8439613978069, 3: 349.17364660898846, 4: 346.8767013549804}, 'RAnkle_y': {0: 1037.436432957649, 1: 1035.5133372545242, 2: 1036.4301753044128, 3: 1036.6672885417938, 4: 1034.7594685554504}, 'RAnkle_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'RBigToe_x': {0: 419.2086009979248, 1: 421.6859966913858, 2: 421.69100093841547, 3: 420.9167706171671, 4: 418.6264912287394}, 'RBigToe_y': {0: 1064.7671462297442, 1: 1061.135880947113, 2: 1062.9200091362002, 3: 1062.289834022522, 4: 1059.7884662151337}, 'RBigToe_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'RSmallToe_x': {0: 403.8350744247436, 1: 406.3124701182047, 2: 405.1348555882772, 3: 403.8350744247436, 4: 401.9404935836792}, 'RSmallToe_y': {0: 1071.5998245477676, 1: 1067.968559265137, 2: 1069.5424675941467, 3: 1069.1225128173828, 4: 1066.4628655910492}, 'RSmallToe_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'RHeel_x': {0: 333.80012003580737, 1: 334.5693461100261, 2: 335.599045117696, 3: 332.09195041656494, 4: 331.8593034744262}, 'RHeel_y': {0: 1054.5181287527084, 1: 1054.3032026290894, 2: 1054.6419360637665, 3: 1053.748985528946, 4: 1053.1140668392181}, 'RHeel_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'LHip_x': {0: 330.3837807973225, 1: 329.444837252299, 2: 335.599045117696, 3: 335.50828965504957, 4: 335.1965030034382}, 'LHip_y': {0: 688.9698387384415, 1: 687.0467430353165, 2: 688.751106262207, 3: 688.200670003891, 4: 687.690701007843}, 'LHip_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'LKnee_x': {0: 366.2553428014118, 1: 372.1490777333576, 2: 373.6781794230144, 3: 378.2125301361084, 4: 381.91729640960693}, 'LKnee_y': {0: 859.7867966890335, 1: 857.8637009859085, 2: 857.6237969398499, 3: 852.1849610805511, 4: 842.870486497879}, 'LKnee_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'LAnkle_x': {0: 344.0491377512614, 1: 343.1101942062378, 2: 343.8771177927653, 3: 345.7573073705036, 4: 345.20810159047437}, 'LAnkle_y': {0: 1018.646567583084, 1: 1015.0153023004531, 2: 1013.2515707015992, 3: 1016.1692521572112, 4: 1011.399070739746}, 'LAnkle_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'LBigToe_x': {0: 415.79226175944, 1: 413.1451485951742, 2: 415.06854279836017, 3: 419.2086009979248, 4: 416.9578914642334}, 'LBigToe_y': {0: 1044.269111275673, 1: 1038.929676413536, 2: 1039.741404533386, 3: 1041.7917976379395, 4: 1039.765268087387}, 'LBigToe_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'LSmallToe_x': {0: 408.95958328247065, 1: 406.3124701182047, 2: 408.4460846583048, 3: 412.3759225209554, 4: 410.2834924062093}, 'LSmallToe_y': {0: 1039.1446025371552, 1: 1033.8051676750183, 2: 1031.4633314609528, 3: 1034.9591188430788, 4: 1031.4222688674927}, 'LSmallToe_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'LHeel_x': {0: 323.55110232035327, 1: 322.6121587753296, 2: 324.0097433725993, 3: 325.25927193959546, 4: 323.5163046518962}, 'LHeel_y': {0: 1034.0200937986376, 1: 1032.0969980955124, 2: 1029.807716846466, 3: 1031.5427794456482, 4: 1028.085069179535}, 'LHeel_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'Neck_x': {0: 434.58212757110596, 1: 435.3513536453247, 2: 434.9359172185262, 3: 434.58212757110596, 4: 436.9810886383056}, 'Neck_y': {0: 495.9466762542724, 1: 495.7317501306534, 2: 495.04419636726374, 3: 496.8856637477875, 4: 495.8017189502716}, 'Neck_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'Head_x': {0: 521.6987781524658, 1: 520.7598346074423, 2: 521.0278730392456, 3: 519.9906085332235, 4: 520.4110768636068}, 'Head_y': {0: 422.4953843355178, 1: 422.2804582118988, 2: 422.1971533298492, 3: 421.7261970043182, 4: 424.0519256591797}, 'Head_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'Nose_x': {0: 508.03342119852704, 1: 508.80264727274573, 2: 509.4385712941488, 3: 508.03342119852704, 4: 508.7308785120646}, 'Nose_y': {0: 492.5303370952606, 1: 490.60724139213556, 2: 491.7329671382904, 3: 491.7611546516418, 4: 490.7959194183349}, 'Nose_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'RShoulder_x': {0: 391.8778870900472, 1: 390.9389435450235, 2: 390.23432477315265, 3: 383.33703899383545, 4: 388.591695467631}, 'RShoulder_y': {0: 504.48752415180206, 1: 504.27259802818304, 2: 501.66665482521057, 3: 503.7183425426484, 4: 504.144718170166}, 'RShoulder_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'RElbow_x': {0: 391.8778870900472, 1: 390.9389435450235, 2: 390.23432477315265, 3: 386.7533782323201, 4: 386.923095703125}, 'RElbow_y': {0: 641.1410905122757, 1: 640.9261643886566, 2: 637.4270532131195, 3: 638.6637487411499, 4: 639.3013055324554}, 'RElbow_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'RWrist_x': {0: 446.53931490580237, 1: 447.3085409800211, 2: 448.1808334986368, 3: 446.53931490580237, 4: 448.6612869898478}, 'RWrist_y': {0: 747.0476044416428, 1: 746.8326783180237, 2: 746.6976177692413, 3: 744.5702700614929, 4: 742.7544958591461}, 'RWrist_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'LShoulder_x': {0: 439.706636428833, 1: 440.4758625030517, 2: 444.8696044286092, 3: 446.53931490580237, 4: 445.3240874608358}, 'LShoulder_y': {0: 519.8610503673553, 1: 521.3542938232422, 2: 521.5340301990509, 3: 529.3408880233765, 4: 522.4993164539337}, 'LShoulder_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'LElbow_x': {0: 449.9556541442871, 1: 449.0167105992635, 2: 454.8032916386922, 3: 453.3719933827718, 4: 453.6670862833658}, 'LElbow_y': {0: 636.0165817737579, 1: 635.8016556501389, 2: 630.8045947551727, 3: 633.5392396450043, 4: 629.2897064685822}, 'LElbow_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'LWrist_x': {0: 461.91284147898347, 1: 460.97389793395996, 2: 464.7369788487752, 3: 465.3291807174682, 4: 463.678684870402}, 'LWrist_y': {0: 740.2149261236191, 1: 741.7081695795059, 2: 740.0751593112946, 3: 739.4457609653473, 4: 731.074296951294}, 'LWrist_z': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}, 'HipMiddle_x': {0: 316.7184238433838, 1: 316.63356510798144, 2: 319.87070703506464, 3: 317.5725086530049, 4: 316.84190559387207}, 'LWrist_Distance': {0: 1.7639135464330964, 1: 1.7639135464330964, 2: 4.102133653055507, 3: 0.8642021355936529, 4: 8.532616613898282}, 'LWrist_Speed': {0: 1.2535701636064136, 1: 1.2535701636064136, 2: 2.915285936204022, 3: 0.6141672956114108, 4: 6.063921684996805}, 'LWrist_Distance_filtered': {0: 1.6861427449640698, 1: 2.4198146796223323, 2: 3.0539619609024538, 3: 3.5217712952364235, 4: 3.7920184828730514}, 'LWrist_Speed_filtered': {0: 1.198300359415379, 1: 1.7197030375810867, 2: 2.170375981701492, 3: 2.5028366201287433, 4: 2.694894678702453}}
    data = pd.DataFrame(rdata)
    
    window = QWidget() 
    layout = QVBoxLayout(window)  # Create a layout manager for the main window

    pixmap = QPixmap(image_path)
    p2 = QPixmap("test1.png")    

    raw_frames = [pixmap,pixmap,pixmap,p2,p2]

    overlay = ImageOverlay(pixmap, data,raw_frames)


    layout.addWidget(overlay)  # Add the ImageOverlay to the layout

    # Start the timer to switch between frames
    timer = QTimer()
    timer.timeout.connect(overlay.next_frame)
    timer.start(1000)  # Change frame every second

    window.setWindowTitle("Image Overlay Example")
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())
