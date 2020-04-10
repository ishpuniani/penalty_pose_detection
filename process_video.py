# From Python
# It requires OpenCV installed for Python
import sys
import cv2
import os
from sys import platform
import argparse

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

    if __name__ == '__main__':
        # Flags
        img_path = "resources/img1.png"
        vid_path = "resources/videos/video1.mp4"
        output_path = "output/"

        # Custom Params (refer to include/openpose/flags.hpp for more parameters)
        # --write_json ./output/ --display 0  --write_video ../openpose.avi
        params = dict()
        params["model_folder"] = "openpose/models/"
        params["number_people_max"] = 3
        # params["hand"] = True
        # params["face"] = True
        # params["face_detector"] = 0
        # params["face_detector"] = 2
        # params["body"] = 0

        # params["tracking"] = 5
        # params["number_people_max"] = 1
        # params["video"] = vid_path
        # params["write_json"] = output_path + '/json/'
        # params["display"] = 0
        # params["write_video"] = 'openpose.avi'
        # params["write_images"] = output_path + '/img/'

        # Starting OpenPose
        opWrapper = op.WrapperPython()
        opWrapper.configure(params)
        opWrapper.start()
        # opWrapper.execute()

        # Process Videos
        datum = op.Datum()
        cap = cv2.VideoCapture(vid_path)
        cap.set(1, 155)
        while cap.isOpened():
            hasframe, frame = cap.read()
            if hasframe:
                datum.cvInputData = frame
                opWrapper.emplaceAndPop([datum])

                # Display Image
                print("Body keypoints: \n" + str(datum.poseKeypoints))
                print("Face keypoints: \n" + str(datum.faceKeypoints))
                print("Left hand keypoints: \n" + str(datum.handKeypoints[0]))
                print("Right hand keypoints: \n" + str(datum.handKeypoints[1]))
                cv2.imshow("OpenPose 1.5.0 - Python", datum.cvOutputData)
                cv2.waitKey(10)
            else:
                break

except Exception as e:
    print(e)
    sys.exit(-1)
