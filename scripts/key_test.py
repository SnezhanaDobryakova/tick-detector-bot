import cv2
import numpy as np

img = np.zeros((400, 600, 3), dtype=np.uint8)
cv2.putText(img, "Press keys (ESC to quit)", (50, 200),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
cv2.imshow("Test", img)

while True:
    key = cv2.waitKey(0) & 0xFF
    if key == 27:  # ESC
        break
    if 32 <= key < 127:
        print(f"Key: {key} = '{chr(key)}'")
    else:
        print(f"Key: {key}")
    cv2.imshow("Test", img)

cv2.destroyAllWindows()
print("Done")
