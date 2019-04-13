import gphoto2 as gp
context = gp.Context()
camera = gp.Camera()
try:
    camera.init(context)
except gp.GPhoto2Error:
    print("failed to open camera")
else:
    text = camera.get_summary(context)
    print('Summary')
    print('=======')
    print(str(text))
    camera.exit(context)
