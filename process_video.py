import math
import sys
import traceback
import ground_detection

import cv2
import os
import numpy as np
from sys import platform
from datetime import datetime

try:
    # Import Openpose (Windows/Ubuntu/OSX)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    try:
        # Windows Import
        if platform == "win32":
            # Change these variables to point to the correct folder (Release/x64 etc.)
            sys.path.append(dir_path + '/../../python/openpose/Release')
            os.environ['PATH']  = os.environ['PATH'] + ';' + dir_path + '/../../x64/Release;' +  dir_path + '/../../bin;'
            import pyopenpose as op
        else:
            # Change these variables to point to the correct folder (Release/x64 etc.)
            sys.path.append('openpose/build/python')
            # If you run `make install` (default path is `/usr/local/python` for Ubuntu), you can also access the OpenPose/python module from there. This will install OpenPose and the python library at your desired installation path. Ensure that this is in your python path in order to use it.
            # sys.path.append('/usr/local/python')
            from openpose import pyopenpose as op
    except ImportError as e:
        print('Error: OpenPose library could not be found. Did you enable `BUILD_PYTHON` in CMake and have this Python script in the right folder?')
        raise e


    # refer to https://github.com/stuartcrobinson/andre_aigassi/blob/a549c84ffbcf7510d9e0b4c0886d07254855077a/brownlee_maskrcnn/ex4.py
    m_i_bodyPart = {0: "Nose",
                    1: "Neck",
                    2: "RShoulder",
                    3: "RElbow",
                    4: "RWrist",
                    5: "LShoulder",
                    6: "LElbow",
                    7: "LWrist",
                    8: "MidHip",
                    9: "RHip",
                    10: "RKnee",
                    11: "RAnkle",
                    12: "LHip",
                    13: "LKnee",
                    14: "LAnkle",
                    15: "REye",
                    16: "LEye",
                    17: "REar",
                    18: "LEar",
                    19: "LBigToe",
                    20: "LSmallToe",
                    21: "LHeel",
                    22: "RBigToe",
                    23: "RSmallToe",
                    24: "RHeel"}
    m_bodyPart_i = dict((v, k) for k, v in m_i_bodyPart.items())

    OP_START = OP_ONE_START = False
    OP_WRAPPER = ONE_OP_WRAPPER = None
    BOUND_PADDING = 5

    def init_op():
        global OP_START, OP_WRAPPER
        if not OP_START:
            # Custom Params (refer to include/openpose/flags.hpp for more parameters)
            params = dict()
            params["model_folder"] = "openpose/models/"
            # params["number_people_max"] = 3

            # Starting OpenPose
            opw = op.WrapperPython()
            opw.configure(params)
            opw.start()
            OP_WRAPPER = opw
            OP_START = True

        return OP_WRAPPER

    def init_one_person_op():
        global OP_ONE_START, ONE_OP_WRAPPER
        if not OP_ONE_START:
            # Custom Params (refer to include/openpose/flags.hpp for more parameters)
            params = dict()
            params["model_folder"] = "openpose/models/"
            params["number_people_max"] = 1

            # Starting OpenPose
            opw = op.WrapperPython()
            opw.configure(params)
            opw.start()
            ONE_OP_WRAPPER = opw
            OP_ONE_START = True

        return ONE_OP_WRAPPER

    # def find_nth_smallest(a, n):
    #     return np.partition(a, n - 1)[n - 1]

    # def find_non_zero_min(a):
    #     res = 0.0
    #     n = 1
    #     while res == 0.0:
    #         res = find_nth_smallest(a, n)
    #         n += 1
    #     return res

    def find_non_zero_min(a):
        min = 0.0
        arr = np.sort(a)
        for num in arr:
            if num != 0.0:
                min = num
                break
        return min

    def get_body_bound(body_keypoint):
        if body_keypoint is None:
            return None
        padding = BOUND_PADDING
        min_x = find_non_zero_min(body_keypoint[:, 0]) - padding
        max_x = body_keypoint[:, 0].max() + padding
        min_y = find_non_zero_min(body_keypoint[:, 1]) - padding
        max_y = body_keypoint[:, 1].max() + padding
        coord = [min_x, min_y, max_x, max_y]
        return coord

    def get_body_bounds(body_keypoints):
        """
        Get corners of all body keypoints
        :param body_keypoints: body_keypoints generated by openpose
        :return: corner coordinates
        """
        res = []
        for kp in body_keypoints:
            coord = get_body_bound(kp)
            res.append(coord)

        return res

    def draw_bound(image, coords, text):
        """
        :param image: the image
        :param coords: x,y,x2,y2 where x,y are coordinates of top-left corner and x2,y2 are the coordinates of opposite corner of the rectangle
        :param text: text on top of the rectangle
        :return:
        """
        if coords is None or len(coords) == 0:
            return image
        x, y, x2, y2 = np.array(coords).astype(int)
        out = cv2.rectangle(image, (x, y), (x2, y2), (36, 255, 12), 1)
        cv2.putText(out, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (36, 255, 12), 2)
        return out


    def process_video(vid_path, out_vid_path, f_height=720, f_width=1280, read_frame_rate=1, starting_frame=0, display=False):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_vid = cv2.VideoWriter(out_vid_path, fourcc, 20.0, (f_width, f_height))

        cap = cv2.VideoCapture(vid_path)
        count = starting_frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, count)
        while cap.isOpened():
            grab_success = cap.grab()
            if grab_success:
                if count % read_frame_rate == 0:
                    print('------- Frame ' + str(count) + ' ----------')
                    hasframe, frame = cap.retrieve()
                    if hasframe:
                        out_image = process_image_v2(frame, display)
                        if display:
                            cv2.imshow("Final Out Image: " + str(count), out_image)
                            cv2.waitKey(0)
                            cv2.destroyAllWindows()
                        out_vid.write(out_image)
                    else:
                        break
                count += 1
            else:
                break
        out_vid.release()


    def get_goal_post_coords(image):
        """
        Function to identify goal post coordinates
        :param image: main image
        :return: goal post top-left and opposite coordinates. [x,y,x2,y2]
        """
        coords = [720,240,1120,520]
        return coords


    def get_goal_post_image(image):
        """
        Get the goal post cropped image from the main image
        :param image: main image
        :return: goal post cropped image and goal post coordinates with reference to the main image
        """
        gp_coords = get_goal_post_coords(image)
        x,y,x2,y2 = gp_coords
        img = image[y:y2, x:x2]
        return img, gp_coords


    def get_gk_bodypoints(image, display=False):
        """
        Get the goal keeper body points by identifying the goalpost first and looking for bodies around the goalpost.
        :param image: original image
        :param display: boolean param to display the images
        :return: goalkeeper body points, marked image and goalpost coordinates
        """
        gp_coords = get_goal_post_coords(image)
        gk_keypoints, gk_image = crop_process_image(image, gp_coords, display)
        return gk_keypoints, gk_image, gp_coords


    def crop_process_image(image, crop_coords, display):
        """
        Process cropped image and returns one body detected in the coordinates
        :param image: original image
        :param crop_coords: extreme corners of the crop region, [x,y,x2,y2]
        :param display: boolean param to display image or not
        :return: body keypoints wrt the cropped image, cropped and marked image
        """
        opWrapper = init_one_person_op()
        datum = op.Datum()

        x, y, x2, y2 = crop_coords
        croppedImage = image[y:y2, x:x2].copy()
        if display:
            cv2.imshow("cropped image",croppedImage)
            cv2.waitKey(25)

        datum.cvInputData = croppedImage
        opWrapper.emplaceAndPop([datum])
        outImg = datum.cvOutputData
        if display:
            cv2.imshow("marked image", outImg)
            cv2.waitKey(25)

        keypoints = None
        if datum.poseKeypoints.shape != ():
            keypoints = datum.poseKeypoints[0]
        else:
            outImg = croppedImage

        return keypoints, outImg


    def draw_image_bound(image, body_points, text):
        """
        Draw image bounds around the keypoints detected with the text associated.
        Works if body_points are not empty.
        :param image: image on which the box is to be drawn
        :param body_points: body keypoints on the basis of which the rectangle is drawn
        :param text: Annotation of the bounding box
        :return: returns the image with rectangle drawn and text written.
        """
        if body_points is None or not is_valid_keypoints(body_points):
            return image

        out = image.copy()
        bound = get_body_bound(body_points)
        out = draw_bound(out, bound, text)
        return out


    def printKp(kp):
        if kp is None:
            return

        print("Nose:" + str(kp[m_bodyPart_i['Nose']]))
        print("Neck:" + str(kp[m_bodyPart_i['Neck']]))

        print("LWrist:" + str(kp[m_bodyPart_i['LWrist']]))
        print("RWrist:" + str(kp[m_bodyPart_i['RWrist']]))

        print("LElbow:" + str(kp[m_bodyPart_i['LElbow']]))
        print("RElbow:" + str(kp[m_bodyPart_i['RElbow']]))

        print("LHip:" + str(kp[m_bodyPart_i['LHip']]))
        print("RHip:" + str(kp[m_bodyPart_i['RHip']]))

        print("LKnee:" + str(kp[m_bodyPart_i['LKnee']]))
        print("RKnee:" + str(kp[m_bodyPart_i['RKnee']]))

        print("LAnkle:" + str(kp[m_bodyPart_i['LAnkle']]))
        print("RAnkle:" + str(kp[m_bodyPart_i['RAnkle']]))

        print("LHeel:" + str(kp[m_bodyPart_i['LHeel']]))
        print("RHeel:" + str(kp[m_bodyPart_i['RHeel']]))


    def is_valid_keypoints(keypoints):
        """
        Check if keypoints contain important features like legs which will be compared
        :param keypoints: body keypoints
        :return: True if keypoints are available
        """
        return keypoints[m_bodyPart_i['Neck']][2] != 0 \
               and keypoints[m_bodyPart_i['LHip']][2] != 0 and keypoints[m_bodyPart_i['RHip']][2] != 0 \
               and keypoints[m_bodyPart_i['LKnee']][2] != 0 and keypoints[m_bodyPart_i['RKnee']][2] != 0 \
               and keypoints[m_bodyPart_i['LAnkle']][2] != 0 and keypoints[m_bodyPart_i['RAnkle']][2] != 0


    HIP_THRESHOLD = 8
    def is_striker(kp):
        """
        nose and neck out of LHip and RHip range with some threshold
        LHip and RHip close to each other
        L/RElbow and L/RWrist vertical distance
        # LAnkle and RAnkle farther away from each other than threshold
        :param kp:
        :return:
        """
        res = False

        neck = kp[m_bodyPart_i['Neck']]
        lelbow = kp[m_bodyPart_i['LElbow']]
        relbow = kp[m_bodyPart_i['RElbow']]
        lwrist = kp[m_bodyPart_i['LWrist']]
        rwrist = kp[m_bodyPart_i['RWrist']]
        lhip = kp[m_bodyPart_i['LHip']]
        rhip = kp[m_bodyPart_i['RHip']]
        lknee = kp[m_bodyPart_i['LKnee']]
        rknee = kp[m_bodyPart_i['RKnee']]
        lankle = kp[m_bodyPart_i['LAnkle']]
        rankle = kp[m_bodyPart_i['RAnkle']]

        left = min(lhip[0], rhip[0])
        right = max(lhip[0], rhip[0])

        # if (abs(lhip[0] - rhip[0]) < HIP_THRESHOLD) and not (left < neck[0] < right):
        #     res = True
        # elif abs(lankle[0] - rankle[0]) > 20:
        #     res = True
        # elif abs(lwrist[1] - lelbow[1]) < 10 or abs(rwrist[1] - relbow[1]) < 10:
        #     res = True

        if not (left < neck[0] < right):
            res = True
        elif abs(lhip[0] - rhip[0]) < HIP_THRESHOLD:
            res = True
        # elif abs(lelbow[1] - lwrist[1]) < 6 or abs(relbow[1] - rwrist[1]) < 6:
        #     res = True

        return res


    def is_referee(kp):
        """
        Nose and neck between LHip and RHip
        LHip and RHip away from each other
        LAnkle and RAnkle away but not far
        :param kp:
        :return:
        """
        res = False

        neck = kp[m_bodyPart_i['Neck']]
        lelbow = kp[m_bodyPart_i['LElbow']]
        relbow = kp[m_bodyPart_i['RElbow']]
        lwrist = kp[m_bodyPart_i['LWrist']]
        rwrist = kp[m_bodyPart_i['RWrist']]
        lhip = kp[m_bodyPart_i['LHip']]
        rhip = kp[m_bodyPart_i['RHip']]
        lknee = kp[m_bodyPart_i['LKnee']]
        rknee = kp[m_bodyPart_i['RKnee']]
        lankle = kp[m_bodyPart_i['LAnkle']]
        rankle = kp[m_bodyPart_i['RAnkle']]

        left = min(lhip[0], rhip[0])
        right = max(lhip[0], rhip[0])

        if left < neck[0] < right:
            res = True

        return res


    def mid_bound_point(bound):
        x, y, x2, y2 = bound
        return (abs(x - x2) / 2, abs(y - y2) / 2)

    def identify_keypoints(image, keypoints, detect_gk=False):
        keypoints_list = []
        for kp in keypoints:
            if is_valid_keypoints(kp):
                keypoints_list.append(kp)

        striker_kp = None
        gk_kp = None

        gp_coords = get_goal_post_coords(image)
        gx, gy, gx2, gy2 = gp_coords
        g_mid = mid_bound_point(gp_coords)  # middle point of the goal post, [x,y]

        if detect_gk:
            # find gk and remove from list
            # goalkeeper will be in closest proximity to the goal post coordinates
            # goalkeeper will be inside the goal frame
            min_dist = 1000
            for kp in keypoints_list:
                bbox = get_body_bound(kp)
                bx, by, bx2, by2 = bbox
                mid = mid_bound_point(bbox)
                dist = math.sqrt((mid[0] - g_mid[0])*(mid[0] - g_mid[0]) + (mid[1] - g_mid[1])*(mid[1] - g_mid[1]))
                if gx < bx < gx2 and gy < by < gy2:
                    if dist < min_dist:
                        min_dist = dist
                        gk_kp = kp

            if gk_kp is not None:
                # removing gk_bp from main keypoints list
                temp = []
                for kp in keypoints_list:
                    if not np.equal(kp, gk_kp).all():
                        temp.append(kp)
                keypoints_list = temp

        # check if there exists any body point where neck is outside of LHip and RHip
        neckOutsideBp = []
        for kp in keypoints_list:
            neck = kp[m_bodyPart_i['Neck']]
            lhip = kp[m_bodyPart_i['LHip']]
            rhip = kp[m_bodyPart_i['RHip']]

            left = min(lhip[0], rhip[0])
            right = max(lhip[0], rhip[0])

            if not left < neck[0] < right:
                neckOutsideBp.append(kp)

        if len(neckOutsideBp) == 0:
            # If no striker found earlier check for body keypoint with thinnest hip size, that is most likely to be a
            # striker since the striker is facing sideways
            min_hip = 1000
            min_hip_kp = None
            for kp in keypoints_list:
                lhip = kp[m_bodyPart_i['LHip']]
                rhip = kp[m_bodyPart_i['RHip']]

                hipLength = abs(lhip[0] - rhip[0])
                if hipLength < min_hip:
                    min_hip = hipLength
                    min_hip_kp = kp
            striker_kp = min_hip_kp

        elif len(neckOutsideBp) == 1:
            striker_kp = neckOutsideBp[0]

        else:
            # Find body furthest away from the goal since the other referee next to the line is crouching
            min_dist = 1000
            min_dist_kp = None
            for kp in keypoints_list:
                mid = mid_bound_point(get_body_bound(kp))
                neck = kp[m_bodyPart_i['Neck']]
                dist = math.sqrt((mid[0] - g_mid[0]) * (mid[0] - g_mid[0]) + (mid[1] - g_mid[1]) * (mid[1] - g_mid[1]))
                if dist < min_dist:
                    min_dist = dist
                    min_dist_kp = kp
            striker_kp = min_dist_kp

        ref_arr = []
        for kp in keypoints_list:
            if not np.equal(kp, striker_kp).all():
                ref_arr.append(kp)

        print("\nStriker:: \n")
        printKp(striker_kp)

        if detect_gk:
            print("\nGoalkeeper:: \n")
            printKp(gk_kp)

        print("\nRefs:: \n")
        for kp in ref_arr:
            printKp(kp)
            print('\n')

        print("\n\n")
        return striker_kp, ref_arr, gk_kp


    def process_image_v2(image, display):
        opWrapper = init_op()
        datum = op.Datum()

        # removing crowd by generating a masked image on the basis of ground color
        masked_image = ground_detection.filter_ground_in_frame(image)

        datum.cvInputData = masked_image
        opWrapper.emplaceAndPop([datum])
        op_img = datum.cvOutputData.copy()

        out_image = cv2.bitwise_or(op_img, image)
        if display:
            cv2.imshow("Op Image",op_img)
            cv2.waitKey(0)
            # cv2.imshow("Out Image", out_image)
            # cv2.waitKey(30)

        body_keypoints = datum.poseKeypoints
        striker_bp, ref_bp_arr, gk_bp = identify_keypoints(image, body_keypoints, True)
        out_image = draw_image_bound(out_image, striker_bp, "Striker")
        out_image = draw_image_bound(out_image, gk_bp, "Goalkeeper")
        for kp in ref_bp_arr:
            out_image = draw_image_bound(out_image, kp, "Referee")

        if display:
            cv2.imshow("Out Image", out_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return out_image


    def process_image(image, display):
        opWrapper = init_op()
        datum = op.Datum()

        # marking goalkeeper in frame
        gk_bp, gk_img, gp_coords = get_gk_bodypoints(image, False)
        x,y,x2,y2 = gp_coords
        gk_proc_img = draw_image_bound(gk_img, gk_bp, "Goalkeeper")
        if display:
            cv2.imshow("gk proc", gk_proc_img)
            cv2.waitKey(25)

        # mask goalpost image area so as to avoid double identification by openpose
        image[y:y2, x:x2] = (255, 255, 255)

        datum.cvInputData = image
        opWrapper.emplaceAndPop([datum])
        out_image = datum.cvOutputData.copy()
        out_image[y:y2, x:x2] = gk_proc_img

        if display:
            cv2.imshow("Out Image", out_image)
            cv2.waitKey(0)

        body_keypoints = datum.poseKeypoints
        striker_bp, ref_bp_arr, _ = identify_keypoints(image, body_keypoints)
        out_image = draw_image_bound(out_image, striker_bp, "Striker")
        for kp in ref_bp_arr:
            out_image = draw_image_bound(out_image, kp, "Referee")

        if display:
            cv2.destroyAllWindows()
        return out_image


    def run():
        start_time = datetime.now().strftime("%H:%M:%S")

        print("Start Time:: " + start_time)

        frame_rate = 1
        starting_frame = 0
        img_path = "resources/img4.png"
        vid_path = "resources/videos/video1/video1.mp4"
        out_vid_path = "resources/output/video1-out.mp4"


        fheight = 720
        fwidth = 1280
        process_video(vid_path, out_vid_path, fheight, fwidth, frame_rate, starting_frame, False)

        # Test Code
        # process_video(vid_path, out_vid_path, fheight, fwidth, read_frame_rate=1, starting_frame=40, display=True)

        # image = cv2.imread(img_path)
        # process_image(image, False)

        print("Start Time:: " + start_time)
        end_time = datetime.now().strftime("%H:%M:%S")
        print("End Time:: " + end_time)

    if __name__ == '__main__':
        run()

except Exception as e:
    traceback.print_exc()
    sys.exit(-1)
