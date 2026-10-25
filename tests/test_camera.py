import cv2


def main():

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("Unable to open camera.")

    print("Camera started.")
    print("Press Q to exit.")

    while True:

        success, frame = camera.read()

        if not success:
            print("Unable to read frame.")
            break

        cv2.imshow("Camera Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()