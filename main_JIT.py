from PIL import Image
import numpy as np
from hashlib import sha256
import tkinter as t
from tkinter import filedialog
from time import time
from ctypes import c_uint8
from numba import jit
from threading import Thread

root = t.Tk()
root.withdraw()
# filetypes=[("Image files","*.bmp")] #*.eps *.gif *.icns *.ico *.im *.jpeg *.jpg *.msp *.pcx *.png *.ppm *.sgi *.spider *.tiff *.webp *.xbm")]
file = filedialog.askopenfilename()  # filetypes=filetypes)
if not file:
    exit()
operation = input("Crypt(c)/decrypt(d): ")
password = input("Password: ")
password = sha256(password.encode('utf-8')).hexdigest()

print("processing image")
image = Image.open(file)
width, height = image.size
bands=len(image.getbands())
image_array_1D = np.array(image).reshape(height * width * bands)

print("creating chunks")
chunks = [image_array_1D[a:a + height * width * 3 // 8] for a in range(0, height * width * 3, height * width * 3 // 8)]

print("processing password")
password = [int(password[i] + password[i + 1], 16) for i in range(0, len(password), 2)]
password = [(password[i % len(password)] + int(i ** 2.7365)) % 256 for i in range(int(width * 3 * 17 / 19))]
password_len = len(password)
password = np.array(password, c_uint8)

print("processing finished")
start = time()


@jit(parallel=True, nogil=1)
def add(m, n, res):  # , image_array):
    #position1 = (height * width * 3 // 8 * n) % password_len
    #position2 = 0
    position1 = (n*height//8*width * 3) % password_len + (password[0]+password[5])
    position2 = (width * 3) % password_len
    idk = 0
    start = height * width * 3 // 8 * n
    for j in range(len(m)):
        res[start + j] = (m[j] + password[position1 % password_len] + password[position2 % password_len]) % 256
        position1 += 1
        position2 += 1
        idk += 15 if position2 == width * 3 else 0
        position2 = position2 % (width * 3 + idk)


@jit(parallel=True, nogil=1)
def subtract(m, n, res):  # , image_array):
    #position1 = (height * width * 3 // 8 * n) % password_len
    #position2 = 0
    position1 = (n*height//8*width * 3) % password_len + (password[0]+password[5])
    position2 = (width * 3) % password_len
    idk=0
    start = height * width * 3 // 8 * n
    for j in range(len(m)):
        res[start + j] = (m[j] - password[position1 % password_len] - password[position2 % password_len]) % 256
        position1 += 1
        position2 += 1
        idk+= 15 if position2==width*3 else 0
        position2 = position2%(width*3+idk)


result = np.zeros(height * width * 3, c_uint8)
if operation == "c":
    print("encryption started")
    threads = []
    for j, i in enumerate(chunks):
        thread = Thread(target=lambda: add(i, j, result))  # , image_array))
        thread.start()
        threads.append(thread)
    for i in threads:
        i.join()

elif operation == "d":
    print("decryption started")
    threads=[]
    for j, i in enumerate(chunks):
        thread = Thread(target=lambda: subtract(i, j, result))  # , image_array))
        thread.start()
        threads.append(thread)
    for i in threads:
        i.join()

arr = result.reshape((height, width, bands))
new_im = Image.fromarray(arr)

print("time:", time() - start)

if input("Show? (n/y): ").lower() == "y":
    new_im.show()

if input("Save? (n/y): ").lower() == "y":
    if operation == "c":
        new_im.save("".join(file.split(".")[0:-1]) + " (crypted)" + ".png")
    elif operation == "d":
        new_im.save("".join(file.split(".")[0:-1]).split(" (crypted)")[0] + " (original)" + ".png")
