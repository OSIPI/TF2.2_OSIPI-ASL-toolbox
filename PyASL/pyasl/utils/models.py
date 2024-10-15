from tensorflow.keras.layers import (
    Input,
    Conv2D,
    Activation,
    Add,
    concatenate,
)
from tensorflow.keras.models import Model


def dilated_net_wide(depth, image_channels=1, filters=32, expansion=4):
    inpt = Input(shape=(None, None, image_channels))
    x = Conv2D(
        filters=filters,
        kernel_size=(3, 3),
        strides=(1, 1),
        kernel_initializer="Orthogonal",
        padding="same",
    )(inpt)
    m = Conv2D(
        filters=filters,
        kernel_size=(3, 3),
        strides=(1, 1),
        kernel_initializer="Orthogonal",
        padding="same",
    )(inpt)
    for i in range(depth):
        shortcut = x
        x = Conv2D(
            filters=filters * expansion,
            kernel_size=(3, 3),
            strides=(1, 1),
            kernel_initializer="Orthogonal",
            padding="same",
            use_bias=False,
        )(
            x
        )  # why not use bias?
        x = Activation("relu")(x)
        x = Conv2D(
            filters=filters,
            kernel_size=(3, 3),
            strides=(1, 1),
            kernel_initializer="Orthogonal",
            padding="same",
            use_bias=False,
        )(x)
        x = Add()([shortcut, x])

    for i in range(1, depth + 1):
        shortcut = m
        m = Conv2D(
            filters=filters * expansion,
            kernel_size=(3, 3),
            strides=(1, 1),
            kernel_initializer="Orthogonal",
            dilation_rate=2**depth,
            padding="same",
            use_bias=False,
        )(m)
        m = Activation("relu")(m)
        m = Conv2D(
            filters=filters,
            kernel_size=(3, 3),
            strides=(1, 1),
            kernel_initializer="Orthogonal",
            padding="same",
            use_bias=False,
        )(m)
        m = Add()([shortcut, m])
    x = concatenate([x, m])
    x = Conv2D(
        filters=image_channels,
        kernel_size=1,
        strides=1,
        kernel_initializer="Orthogonal",
        padding="same",
        use_bias=False,
    )(
        x
    )  # why not use bias?
    s = Conv2D(
        filters=image_channels,
        kernel_size=1,
        strides=1,
        kernel_initializer="Orthogonal",
        padding="same",
        use_bias=False,
    )(inpt)
    x = Add()([s, x])  # input - noise
    model = Model(inputs=inpt, outputs=x)

    return model
