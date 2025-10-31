"""
train.py
Script de entrenamiento mejorado para el proyecto CLASIFICADOR.

Características:
- Usa transfer learning con MobileNetV2 (pesos imagenet) para mejorar precisión.
- Aumento de datos (rotaciones, zoom, flips, shifts).
- Callbacks: ModelCheckpoint (mejor modelo), EarlyStopping, ReduceLROnPlateau.
- Guarda el mejor modelo en `garbage_model_best.h5` y el último en `garbage_model.h5`.

Uso:
    python train.py --data_dir dataset --epochs 15

Requisitos:
    tensorflow (o tensorflow-cpu), numpy, Pillow

"""
import argparse
import os
import json
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau


def build_transfer_model(input_shape=(128,128,3), num_classes=6):
    base = MobileNetV2(include_top=False, weights='imagenet', input_shape=input_shape)
    base.trainable = False  # congelar base al inicio

    x = layers.GlobalAveragePooling2D()(base.output)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model = models.Model(inputs=base.input, outputs=outputs)
    return model


def main(args):
    data_dir = args.data_dir
    img_size = (args.img_size, args.img_size)
    batch_size = args.batch_size

    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"No se encontró la carpeta de datos: {data_dir}")

    # Aumentos + valid split
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.1,
        zoom_range=0.15,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=0.2
    )

    train_gen = train_datagen.flow_from_directory(
        data_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',
        subset='training'
    )

    val_gen = train_datagen.flow_from_directory(
        data_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation'
    )

    num_classes = train_gen.num_classes
    print("Clases detectadas:", train_gen.class_indices)

    model = build_transfer_model(input_shape=(img_size[0], img_size[1], 3), num_classes=num_classes)
    model.compile(optimizer=optimizers.Adam(learning_rate=1e-3), loss='categorical_crossentropy', metrics=['accuracy'])

    # Callbacks
    checkpoint = ModelCheckpoint('garbage_model_best.h5', monitor='val_accuracy', save_best_only=True, verbose=1)
    earlystop = EarlyStopping(monitor='val_loss', patience=6, restore_best_weights=True, verbose=1)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6, verbose=1)

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=args.epochs,
        callbacks=[checkpoint, earlystop, reduce_lr]
    )

    # Guardar modelo final (último estado) y exportar mapping de clases
    model.save('garbage_model.h5')
    print('\nModelo guardado en garbage_model.h5 y mejor modelo en garbage_model_best.h5')

    # Guardar mapping de clases para referencia
    with open('class_indices.json', 'w') as f:
        json.dump(train_gen.class_indices, f)
    print('Class indices guardados en class_indices.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Entrenar modelo de clasificación de basura')
    parser.add_argument('--data_dir', type=str, default='dataset', help='Carpeta con subcarpetas por clase')
    parser.add_argument('--img_size', type=int, default=128, help='Tamaño de imagen (px)')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--epochs', type=int, default=12, help='Número máximo de épocas')
    args = parser.parse_args()

    main(args)
