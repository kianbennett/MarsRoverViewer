import os
import json
import math
import threading
import requests
import asyncio
import aiohttp
import pygame
from io import BytesIO
from asyncio import sleep, to_thread

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if(response.status == 200):
                return await response.json()
            else:
                return f"Error: {response.status} - {response.reason}"
        
async def fetch_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if(response.status == 200):
                return await response.read()
            else:
                return f"Error: {response.status} - {response.reason}"
        
def set_centre_text(str):
    global centreText
    centreText = font.render(str, False, (255, 255, 255), (0, 0, 0))
    print(str)

def hide_centre_text():
    global centreText
    centreText = None

def set_photo(img_bytes):
    imageSurface = pygame.image.load(BytesIO(img_bytes))
    imageWidth, imageHeight = imageSurface.get_size()
    scale = min(screen.get_width() / imageWidth, screen.get_height() / imageHeight)
    newImageSize = (round(imageWidth * scale), round(imageHeight * scale))
    scaledImage = pygame.transform.smoothscale(imageSurface, newImageSize) 
    # scaledImage = pygame.transform.smoothscale(imageSurface, (screen.get_width(), screen.get_height()))
    global photoImage
    global photoRect
    photoImage = scaledImage
    photoRect = scaledImage.get_rect(center = (screen.get_width() // 2, screen.get_height() // 2))

def hide_photo():
    global photoImage
    photoImage = None

def set_camera_name(camera_name):
    global cameraText
    global cameraTextRect
    cameraText = font.render(camera_name, True, (255, 255, 255), None)
    cameraTextRect = pygame.Rect(screen.get_width() - cameraText.get_width() - 10, 10, cameraText.get_width(), cameraText.get_height())

def clear_camera_name():
    global cameraText
    cameraText = None

def update_spinner():
    global spinnerAngle
    spinnerAngle += spinnerSpeed
    if spinnerAngle > 2 * math.pi:
        spinnerAngle -= 2 * math.pi
    pygame.draw.arc(screen, white, spinnerRect, spinnerAngle, spinnerAngle + spinnerArcLength, spinnerArcWidth)

async def next_photo_task():
    global cachedRecentPhotos
    global currentPhotoIndex
    currentPhotoIndex += 1
    if(currentPhotoIndex >= len(cachedRecentPhotos['latest_photos'])):
        currentPhotoIndex = 0
    await set_photo_index_task(currentPhotoIndex)

async def set_photo_index_task(index):
    currentPhotoIndex = index
    photo = cachedRecentPhotos['latest_photos'][currentPhotoIndex]
    await fetch_photo_task(photo)

async def fetch_photo_task(photo):
    global showSpinner

    url = photo['img_src']
    camera_name = photo['camera']['full_name']

    hide_photo()
    hide_centre_text()
    showSpinner = True
    set_camera_name(camera_name)

    img_bytes = await fetch_image(url)

    if(img_bytes is not None):
        set_photo(img_bytes)
    else:
        set_centre_text('Failed to load image\n' + str(img_bytes))

    return

async def init_task():
    global cachedRecentPhotos
    global currentPhotoIndex
    set_centre_text('Updating image list...')
    url = 'https://api.nasa.gov/mars-photos/api/v1/rovers/perseverance/latest_photos?api_key=YGifLV2ZkyWicbgrcIQRCsqraitnMU27gbl4oXab'
    print(f"Fetching list of recent photos from {url}")
    cachedRecentPhotos = await fetch_json(url)
    currentPhotoIndex = 4
    await fetch_photo_task(cachedRecentPhotos['latest_photos'][currentPhotoIndex])

# Initialize pygame
pygame.init()

# Allow running from ssh
os.putenv("DISPLAY", ":0")

# Tell the RPi to use the TFT screen and that it's a touchscreen device
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV'      , '/dev/fb1')
os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')
os.environ['SDL_NOMOUSE'] = '1'

disp_no = os.getenv("DISPLAY")
if disp_no:
    print("I'm running under X display = {0}".format(disp_no))

# Check which frame buffer drivers are available
# Start with fbcon since directfb hangs with composite output
drivers = ['x11', 'fbcon', 'directfb', 'svgalib']
found = False
for driver in drivers:
    # Make sure that SDL_VIDEODRIVER is set
    if not os.getenv('SDL_VIDEODRIVER'):
        os.putenv('SDL_VIDEODRIVER', driver)
    try:
        pygame.display.init()
        print("Using driver: {0}".format(driver))
    except pygame.error:
        print("Driver: {0} failed.".format(driver))
        continue
    found = True
    break

if not found:
    raise Exception('No suitable video driver found!')

# Set up the display surfacea
# screen = pygame.display.set_mode([480, 320])
# For fullscreen use
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

camera_name_surface = pygame.Surface((480, 320), pygame.SRCALPHA)

centre = (screen.get_width() // 2, screen.get_height() // 2)

black = (0, 0, 0)
white = (255, 255, 255)

# Set window title
pygame.display.set_caption('Mars Rover Viewer')
# Hide the cursor
pygame.mouse.set_visible(False)  

# create a font object.
font = pygame.font.Font('freesansbold.ttf', 16)

# Spinner properties
spinnerRadius = 12
spinnerArcWidth = 4
spinnerArcLength = math.pi * 0.66  # Length of the arc (in radians)
spinnerSpeed = -0.2  # Rotation speed
spinnerRect = pygame.Rect(centre[0] - spinnerRadius, centre[1] - spinnerRadius, spinnerRadius * 2, spinnerRadius * 2)
spinnerAngle = 0

showSpinner = False

centreText = None
cameraText = None
cameraTextRect = None
photoImage = None
photoRect = None

cachedRecentPhotos = None
currentPhotoIndex = 0

clock = pygame.time.Clock()

def game_loop():
    is_running = True
    while is_running:
        # Did the user click the window close button?
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    is_running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                global loop
                asyncio.run_coroutine_threadsafe(next_photo_task(), loop)

        screen.fill(black)

        if showSpinner:
            update_spinner()

        if(centreText is not None):
            screen.blit(centreText, centreText.get_rect(center = (screen.get_width() // 2, screen.get_height() // 2)))

        if(photoImage is not None):
            screen.blit(photoImage, photoRect)

        if(cameraText is not None):
            backgroundRect = (cameraTextRect.x - 4, cameraTextRect.y - 2, cameraTextRect.width + 8, cameraTextRect.height + 4)
            camera_name_surface.fill((0, 0, 0, 0))
            pygame.draw.rect(camera_name_surface, (0, 0, 0, 120), backgroundRect, border_radius=2)
            screen.blit(camera_name_surface, screen.get_rect())
            screen.blit(cameraText, cameraTextRect)

        # Push the contents of the surface to the display
        pygame.display.flip()

        clock.tick(10)

    # After exiting while loop
    pygame.quit()

    print("Game loop exited")

# Create a new event loop in a separate thread
loop = asyncio.new_event_loop()
thread = threading.Thread(target=loop.run_forever)
thread.setDaemon(True)
thread.start()

# Run the asynchronous function in the new loop
init = asyncio.run_coroutine_threadsafe(init_task(), loop)

game_loop()

print("Quitting...")

loop.stop()

# thread never quits for some reason, so force application to quit by throwing an error
raise Exception('Exception: Quit')

thread.join()
print("Quit")
