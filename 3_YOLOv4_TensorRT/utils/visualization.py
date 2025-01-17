"""visualization.py

The BBoxVisualization class implements drawing of nice looking
bounding boxes based on object detection results.
"""


import numpy as np
import cv2


# Constants
ALPHA = 0.5
FONT = cv2.FONT_HERSHEY_PLAIN
TEXT_SCALE = 1.0
TEXT_THICKNESS = 1
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def gen_colors(num_colors):
    """Generate different colors.

    # Arguments
      num_colors: total number of colors/classes.

    # Output
      bgrs: a list of (B, G, R) tuples which correspond to each of
            the colors/classes.
    """
    import random
    import colorsys

    hsvs = [[float(x) / num_colors, 1., 0.7] for x in range(num_colors)]
    random.seed(1234)
    random.shuffle(hsvs)
    rgbs = list(map(lambda x: list(colorsys.hsv_to_rgb(*x)), hsvs))
    bgrs = [(int(rgb[2] * 255), int(rgb[1] * 255),  int(rgb[0] * 255))
            for rgb in rgbs]
    return bgrs


def draw_boxed_text(img, text, topleft, color):
    """Draw a transluent boxed text in white, overlayed on top of a
    colored patch surrounded by a black border. FONT, TEXT_SCALE,
    TEXT_THICKNESS and ALPHA values are constants (fixed) as defined
    on top.

    # Arguments
      img: the input image as a numpy array.
      text: the text to be drawn.
      topleft: XY coordinate of the topleft corner of the boxed text.
      color: color of the patch, i.e. background of the text.

    # Output
      img: note the original image is modified inplace.
    """
    assert img.dtype == np.uint8
    img_h, img_w, _ = img.shape
    if topleft[0] >= img_w or topleft[1] >= img_h:
        return img
    margin = 3
    size = cv2.getTextSize(text, FONT, TEXT_SCALE, TEXT_THICKNESS)
    w = size[0][0] + margin * 2
    h = size[0][1] + margin * 2
    # the patch is used to draw boxed text
    patch = np.zeros((h, w, 3), dtype=np.uint8)
    patch[...] = color
    cv2.putText(patch, text, (margin+1, h-margin-2), FONT, TEXT_SCALE,
                WHITE, thickness=TEXT_THICKNESS, lineType=cv2.LINE_8)
    cv2.rectangle(patch, (0, 0), (w-1, h-1), BLACK, thickness=1)
    w = min(w, img_w - topleft[0])  # clip overlay at image boundary
    h = min(h, img_h - topleft[1])
    # Overlay the boxed text onto region of interest (roi) in img
    roi = img[topleft[1]:topleft[1]+h, topleft[0]:topleft[0]+w, :]
    cv2.addWeighted(patch[0:h, 0:w, :], ALPHA, roi, 1 - ALPHA, 0, roi)
    return img

def get_info_from_tracker(tracker_elements_draw):
    tracker_id = []
    boxes = []
    confs = []
    clss = []
    change_lane_flg = []
    distance_driver = []
    distance_driver_loc = []
    coordinate_vehicle_and_driver = []
    for ele in tracker_elements_draw:
        tracker_id.append(ele[0])
        boxes.append(ele[1])
        confs.append(ele[2])
        clss.append(ele[3])
        change_lane_flg.append(ele[4])
        distance_driver.append(ele[5])
        distance_driver_loc.append(ele[6])
        coordinate_vehicle_and_driver.append(ele[7])
    return tracker_id, boxes, confs, clss, change_lane_flg, distance_driver, distance_driver_loc, coordinate_vehicle_and_driver

count_alert = 0
class BBoxVisualization():
    """BBoxVisualization class implements nice drawing of boudning boxes.

    # Arguments
      cls_dict: a dictionary used to translate class id to its name.
    """

    def __init__(self, cls_dict):
        self.cls_dict = cls_dict
        self.colors = gen_colors(len(cls_dict))

    def draw_bboxes(self, img, tracker_elements_draw):
        global count_alert
        count_alert += 1
        if count_alert%2 == 0:
            scale_add_weighted = 0.5
        else:
            scale_add_weighted = 0.8
            
        tracker_id, boxes, confs, clss, change_lane_flg, \
            distance_driver, distance_driver_loc, coordinate_vehicle_and_driver = get_info_from_tracker(tracker_elements_draw)
        """Draw detected bounding boxes on the original image."""
        for trk_id, bb, cf, cl, chg_lane_flg, dis_driver, dis_driver_loc, coor_veh_driver \
                                            in zip(tracker_id, boxes, confs, clss, change_lane_flg, \
                                                   distance_driver, distance_driver_loc, coordinate_vehicle_and_driver):
            cl = int(cl)

            # Show bounding box of all
            # if a >= 0:

            # Show bounding box of car and truck only (class car = 2, truck = 7)
            if cl == 2 or cl == 7:
                x_min, y_min, x_max, y_max = bb[0], bb[1], bb[2], bb[3]
                color = self.colors[cl]
                cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color, 2)
                cv2.circle(img, (int((x_min+x_max)/2), int((y_min+y_max)/2)), 4, (0, 255, 0), -1)
                cv2.putText(img, str(trk_id), (int((x_min+x_max)/2), int((y_min+y_max)/2)), 0, 1, (0, 0, 255), 2)
                
                if chg_lane_flg is not False:
                    # Make bounding box of vehicle changing lane flash (bling bling)
                    mask = np.zeros_like(img)
                    region_vehicle = np.array([[(x_min, y_max),
                                                (x_min, y_min),
                                                (x_max, y_min),
                                                (x_max, y_max),]], np.int32)
                    cv2.fillPoly(mask, region_vehicle, (255,0,255))
                    img = cv2.addWeighted(img, 1, mask, scale_add_weighted, 1)
                    
                    # Show ID vehicle which is changing lane
                    cv2.putText(img, str(trk_id) + ": change lane", (int((x_min+x_max)/2), int((y_min+y_max)/2) + 25), 0, 1, (0, 0, 255), 2)

                if dis_driver is not None:
                    # Draw a line from driver to vehicle in front
                    img = cv2.line(img, (coor_veh_driver[0],coor_veh_driver[1]),\
                                        (coor_veh_driver[2],coor_veh_driver[3]), color, 2)
                    # Draw box mention distance between driver and vehicle in front
                    img = draw_boxed_text(img, str(dis_driver) + "m", (dis_driver_loc[0]+10,dis_driver_loc[1]), (0,0,0))
                    
                    if dis_driver < 10:
                        # Make bounding box of vehicle changing lane flash (bling bling)
                        mask = np.zeros_like(img)
                        region_vehicle = np.array([[(x_min, y_max),
                                                    (x_min, y_min),
                                                    (x_max, y_min),
                                                    (x_max, y_max),]], np.int32)
                        cv2.fillPoly(mask, region_vehicle, (255,0,255))
                        img = cv2.addWeighted(img, 1, mask, scale_add_weighted, 1)
                        
                        cv2.putText(img, str(trk_id) + ": too close", (int((x_min+x_max)/2), int((y_min+y_max)/2) + 25), 0, 1, (0, 0, 255), 2)
                    
                txt_loc = (max(x_min+2, 0), max(y_min+2, 0))
                cls_name = self.cls_dict.get(cl, 'CLS{}'.format(cl))
                txt = '{} {:.2f}'.format(cls_name, cf)
                img = draw_boxed_text(img, txt, txt_loc, color)
        return img
