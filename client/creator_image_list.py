import os
from time import sleep

images = []
for root, dirs, files in os.walk("images/"):
	for name in files:
		images.append('"' + root + '/' + name + '"')
	print(root, dirs, files)
		
with open('imagelist.js', "w") as a:
	a.write('var imageList =[')
	a.write(', '.join(images))
	a.write('];')

sleep(125)
