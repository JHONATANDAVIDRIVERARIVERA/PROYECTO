import os
import json
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

MODEL = 'garbage_model.h5'
DATASET = 'dataset'
IMG_SIZE = (128,128)

# encontrar primera imagen en dataset
first_img = None
for root, dirs, files in os.walk(DATASET):
    for f in files:
        if f.lower().endswith(('.png','.jpg','.jpeg')):
            first_img = os.path.join(root,f)
            break
    if first_img:
        break

if not first_img:
    print('No se encontró ninguna imagen en dataset/')
    raise SystemExit(1)

print('Usando imagen de prueba:', first_img)

# cargar indices de clase
cls_path = 'class_indices.json'
if os.path.exists(cls_path):
    with open(cls_path,'r') as fh:
        class_indices = json.load(fh)
    # invertir mapping
    inv = {v:k for k,v in class_indices.items()}
    print('Class indices:', class_indices)
else:
    inv = None
    print('No existe class_indices.json')

# cargar modelo
print('Cargando modelo', MODEL)
model = load_model(MODEL)
print('Modelo cargado OK')

# procesar imagen
img = image.load_img(first_img, target_size=IMG_SIZE)
arr = image.img_to_array(img)
arr = np.expand_dims(arr,0)/255.0

pred = model.predict(arr)
print('Raw pred vector (first 10):', pred[0][:10])
idx = int(np.argmax(pred[0]))
conf = float(pred[0][idx])*100
if inv:
    label = inv.get(idx, str(idx))
else:
    label = str(idx)
print(f'Predicción: {label} ({conf:.2f}%)')
