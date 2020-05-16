# ref: https://github.com/stephanj/basketballVideoAnalysis/blob/master/court-detection/court_detection1.py

# USAGE
# python ground_detection.py --input resources/img4.png
#
# author: Stephan Janssen
#

# import the necessary packages
import sys
import traceback

import cv2
import numpy as np
import matplotlib.pyplot as plt

try:

    def generate_ground_mask(image):
        # convert to HSV image
        hsv_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Green color
        low_green = np.array([25, 52, 72])
        high_green = np.array([102, 255, 255])
        green_mask = cv2.inRange(hsv_img, low_green, high_green)
        # green_img = cv2.bitwise_and(img, img, mask=green_mask)

        # Erosion
        er_kernel = np.ones((4, 4), np.uint8)
        erosions = cv2.erode(green_mask, er_kernel, iterations=20)

        # Dilation
        dil_kernel = np.ones((10, 10), np.uint8)
        dilation = cv2.dilate(erosions, dil_kernel, iterations=28)
        return dilation


    def filter_ground_in_frame(frame):
        ground_mask = generate_ground_mask(frame)
        masked_image = cv2.bitwise_and(frame, frame, mask=ground_mask).copy()
        return masked_image


    def filter_ground_in_video(vid_path, out_vid_path, f_height=720, f_width=1280, read_frame_rate=1, starting_frame=0,
                               display=False):
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
                        out_image = filter_ground_in_frame(frame)
                        if display:
                            cv2.imshow("Final Out Image: " + str(count), out_image)
                            cv2.waitKey(30)
                            cv2.destroyAllWindows()
                        out_vid.write(out_image)
                    else:
                        break
                count += 1
            else:
                break
        out_vid.release()


    def detect_goalpost(image):
        img = image.copy()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        plt.imshow(gray)
        plt.title("Gray")
        plt.show()

        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        plt.imshow(edges)
        plt.title("Edges")
        plt.show()

        minLineLength = 200
        maxLineGap = 5
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength, maxLineGap)
        print(lines[0])
        print(lines[1])
        print(lines[2])
        print(lines[3])

        LINE_COLOR = (255, 0, 0)

        for line in lines:
            for x1, y1, x2, y2 in line:
                # cv2.line(image, start_point, end_point, color, thickness)
                img = cv2.line(img, (x1, y1), (x2, y2), LINE_COLOR, 5)
        #
        # for x1, y1, x2, y2 in lines[1]:
        #     cv2.line(img, (x1, y1), (x2, y2), LINE_COLOR, 75)
        #
        # for x1, y1, x2, y2 in lines[2]:
        #     cv2.line(img, (x1, y1), (x2, y2), LINE_COLOR, 125)

        plt.imshow(img)
        plt.title('Hough Lines')
        plt.show()


    def run():
        input = 'resources/img4.png'

        vid_path = "resources/videos/video1/video1.mp4"
        out_vid_path = "resources/output/video1-bgRem-out.mp4"

        # filter_ground_in_video(vid_path, out_vid_path, read_frame_rate=5, display=False)

        # read image from input arg
        img = cv2.imread(input)
        # masked_image = filter_ground_in_frame(img)
        # cv2.imshow("masked image", masked_image)
        # cv2.waitKey(0)
        # cv2.imwrite("img4-masked.png", masked_image)
        gp_coords = detect_goalpost(img)
        # im2 = cv2.rectangle(img, (gp_coords[0], gp_coords[1]), (gp_coords[2], gp_coords[3]), (255,0,0))
        # cv2.imshow("goalposts", im2)
        # cv2.waitKey(0)

        # plt.imshow(masked_image)
        # plt.title('Masked Image')
        # plt.show()
        # img2 = cv2.bitwise_or(masked_image, img)
        # plt.imshow(img2)
        # plt.title('Image2')
        # plt.show()


    if __name__ == '__main__':
        run()
        sys.exit(0)

except Exception as e:
    traceback.print_exc()
    sys.exit(-1)
