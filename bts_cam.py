# pip install numpy               
# pip install opencv-python        
# pip install opencv-contrib-python
# https://www.youtube.com/watch?v=cx7VONjFEE0
# https://github.com/kairess/bts_cam/blob/master/main.py
# 범위 선택 후 스페이스바 클릭하면 해당 경로에 영상을 저장한다.

# 실행파일 만들기
# C:\Users\전융\Documents\GitHub\python\> 
# pyinstaller --noconsole --onefile ".\bts_cam.py"
# 파일을 가지고 오면 에러가 난다. - 실행경로와 파일의 경로가 다르기 때문으로 추측

# 커스터마이징 내역
# 변환할 영상 불러오기, 저장할 경로와 파일명 

# 변환할 파일 선택 인터페이스
# https://www.jbmpa.com/pyside2/9
from tkinter import *
from tkinter import filedialog
root = Tk()
root.withdraw()
root.filename = filedialog.askopenfilename(initialdir="./", title="Open Data files", filetypes=(("data files", "*.mp4"), ("all files", "*.*")))
# root.filename = filedialog.askopenfilename(initialdir="./", title="Open Data files", filetypes=(("data files", "*.csv;*.xls;*.xlsx"), ("all files", "*.*")))
print("불러올 영상 : " + root.filename)
video_path = root.filename

# 폴더 선택
# https://cjsal95.tistory.com/35
# root = tkinter.Tk()
# root.withdraw()
save_dir_path = filedialog.askdirectory(parent=root,initialdir="/",title='Please select a directory')
print("저장할 폴더 : ", save_dir_path)

from datetime import datetime
fileCreateTime = str(datetime.now())
# saveFileName = fileCreateTime + '%s_output.mp4' % (video_path.split('.')[0])
saveFileName =  '%s_output.mp4' % (fileCreateTime)
print('저장할 파일명  - ', saveFileName)
print('저장할 풀 경로와 파일명 - ', save_dir_path + saveFileName)


####
import cv2
import numpy as np

# open video file
video_path = 'sample_shotting_game.mp4'
cap = cv2.VideoCapture(video_path)

output_size = (375, 667) # (width, height)
fit_to = 'height'

# initialize writing video
fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
out = cv2.VideoWriter('%s_output.mp4' % (video_path.split('.')[0]), fourcc, cap.get(cv2.CAP_PROP_FPS), output_size)
# out = cv2.VideoWriter(save_dir_path + '\\'+saveFileName, fourcc, cap.get(cv2.CAP_PROP_FPS), output_size)
print('저장되는 정보 - ', '%s_output.mp4' % (video_path.split('.')[0]))
# check file is opened
if not cap.isOpened():
  exit()

# initialize tracker
OPENCV_OBJECT_TRACKERS = {
  "csrt": cv2.TrackerCSRT_create,
  "kcf": cv2.TrackerKCF_create,
  "boosting": cv2.TrackerBoosting_create,
  "mil": cv2.TrackerMIL_create,
  "tld": cv2.TrackerTLD_create,
  "medianflow": cv2.TrackerMedianFlow_create,
  "mosse": cv2.TrackerMOSSE_create
}

tracker = OPENCV_OBJECT_TRACKERS['csrt']()

# global variables
top_bottom_list, left_right_list = [], []
count = 0

# main
ret, img = cap.read()

cv2.namedWindow('Select Window')
cv2.imshow('Select Window', img)

# select ROI
rect = cv2.selectROI('Select Window', img, fromCenter=False, showCrosshair=True)
# rect = "(229, 708, 125, 82)"
cv2.destroyWindow('Select Window')
print(rect)
# initialize tracker
tracker.init(img, rect)

while True:
  count += 1
  # read frame from video
  ret, img = cap.read()

  if not ret:
    try:
        exit()
    except:
        pass
    

  # update tracker and get position from new frame
  success, box = tracker.update(img)
  # if success:
  left, top, w, h = [int(v) for v in box]
  right = left + w
  bottom = top + h

  # save sizes of image
  top_bottom_list.append(np.array([top, bottom]))
  left_right_list.append(np.array([left, right]))

  # use recent 10 elements for crop (window_size=10)
  if len(top_bottom_list) > 10:
    del top_bottom_list[0]
    del left_right_list[0]

  # compute moving average
  avg_height_range = np.mean(top_bottom_list, axis=0).astype(np.int)
  avg_width_range = np.mean(left_right_list, axis=0).astype(np.int)
  avg_center = np.array([np.mean(avg_width_range), np.mean(avg_height_range)]) # (x, y)

  # compute scaled width and height
  scale = 1.3
  avg_height = (avg_height_range[1] - avg_height_range[0]) * scale
  avg_width = (avg_width_range[1] - avg_width_range[0]) * scale

  # compute new scaled ROI
  avg_height_range = np.array([avg_center[1] - avg_height / 2, avg_center[1] + avg_height / 2])
  avg_width_range = np.array([avg_center[0] - avg_width / 2, avg_center[0] + avg_width / 2])

  # fit to output aspect ratio
  if fit_to == 'width':
    avg_height_range = np.array([
      avg_center[1] - avg_width * output_size[1] / output_size[0] / 2,
      avg_center[1] + avg_width * output_size[1] / output_size[0] / 2
    ]).astype(np.int).clip(0, 9999)

    avg_width_range = avg_width_range.astype(np.int).clip(0, 9999)
  elif fit_to == 'height':
    avg_height_range = avg_height_range.astype(np.int).clip(0, 9999)

    avg_width_range = np.array([
      avg_center[0] - avg_height * output_size[0] / output_size[1] / 2,
      avg_center[0] + avg_height * output_size[0] / output_size[1] / 2
    ]).astype(np.int).clip(0, 9999)

  # crop image
  # result_img = img[avg_height_range[0]:avg_height_range[1], avg_width_range[0]:avg_width_range[1]].copy()
  try:
    result_img = img[avg_height_range[0]:avg_height_range[1], avg_width_range[0]:avg_width_range[1]].copy()
  except:
    pass

  # resize image to output size
  result_img = cv2.resize(result_img, output_size)

  # visualize
  pt1 = (int(left), int(top))
  pt2 = (int(right), int(bottom))
  cv2.rectangle(img, pt1, pt2, (255, 255, 255), 3)

  # try:
  #   cv2.imshow('img', img)
  # except:
  #   continue
  cv2.imshow('img', img)
  cv2.imshow('result', result_img)

  # write video
  out.write(result_img)
  if cv2.waitKey(1) == ord('q'):
    break

# release everything
cap.release()
out.release()
cv2.destroyAllWindows()