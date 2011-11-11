import os
from time import sleep

images = []
for root, dirs, files in os.walk("../client/images/"):
    print root
    root = root[10:]
    print root
    for name in files:
        images.append('"' + root + '/' + name + '"')
    print(root, dirs, files)

with open('../client/imagelist.js', "w") as a:
    a.write('var imageList =[')
    a.write(', '.join(images))
    a.write('];')

sleep(125)
