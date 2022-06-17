from tensorflow.keras.layers import  Input,Conv2D,Conv3D,BatchNormalization,Activation,Subtract, Add, Lambda, MaxPooling2D,MaxPooling3D, Dropout, concatenate, UpSampling3D, UpSampling2D, LeakyReLU
from tensorflow.keras.models import Model
def DnCNN(depth,filters=64,image_channels=1, use_bnorm=False):
    layer_count = 0
    inpt = Input(shape=(None,None,image_channels),name = 'input'+str(layer_count))
    # 1st layer, Conv+relu
    layer_count += 1
    x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',name = 'conv'+str(layer_count))(inpt)
    layer_count += 1
    x = Activation('relu',name = 'relu'+str(layer_count))(x)
    # depth-2 layers, Conv+BN+relu
    for i in range(depth-2):
        layer_count += 1
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
        if use_bnorm:
            layer_count += 1
            x = BatchNormalization(axis=3, momentum=0.0,epsilon=0.0001, name = 'bn'+str(layer_count))(x)
        layer_count += 1
        x = Activation('relu',name = 'relu'+str(layer_count))(x)  
    # last layer, Conv
    layer_count += 1
    x = Conv2D(filters=image_channels, kernel_size=(3,3), strides=(1,1), kernel_initializer='Orthogonal',padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
    layer_count += 1
    x = Subtract(name = 'subtract' + str(layer_count))([inpt, x])   # input - noise
    model = Model(inputs=inpt, outputs=x)
    
    return model


def unet_res(image_channels = 1):
    inputs = Input(shape=(None,None,image_channels))
    conv1 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(inputs)
    conv1 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv1)                 
    res1  = Add()([inputs,conv1])

    pool1 = MaxPooling2D(pool_size=(2, 2),padding='same')(res1)
    conv21 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool1)
    conv2 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv21)
    res2  = Add()([conv2,conv21])

    pool2 = MaxPooling2D(pool_size=(2, 2))(res2)
    conv31 = Conv2D(96, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool2)
    conv3 = Conv2D(96, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv31)
    res3  = Add()([conv3,conv31])

    pool3 = MaxPooling2D(pool_size=(2, 2))(res3)
    conv41 = Conv2D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool3)
    conv4 = Conv2D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv41)
    res4  = Add()([conv41,conv4])


    #pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)
    #conv5 = Conv2D(1024, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool4)
    #conv5 = Conv2D(1024, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv5)
    up5 = UpSampling2D(size = (2,2))(res4)
    merge5 = concatenate([res3,up5], axis = 3)
    conv51 = Conv2D(96, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge5)
    conv5 = Conv2D(96, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv51)
    res5 = Add()([conv5,conv51])

    up6 = UpSampling2D(size = (2,2))(res5)
    merge6 = concatenate([res2,up6], axis = 3)
    conv61 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge6)
    conv6 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv61)
    res6 = Add()([conv6,conv61])

    up7 = UpSampling2D(size = (2,2))(res6)
    merge7 = concatenate([res1,up7], axis = 3)
    conv71 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge7)
    conv7 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv71)
    res7 = Add()([conv71,conv7])


    conv8 = Conv2D(1, 1)(res7)
    res8 = Add()([conv8,inputs])

    model = Model(input = inputs, output = res8)
    return model

def unet_res_BN(image_channels = 1):
    inputs = Input(shape=(None,None,image_channels))
    conv1 = conv_bn_relu(inputs,24)
    conv1 = conv_bn_relu(conv1,24)                 
    res1  = Add()([inputs,conv1])

    pool1 = MaxPooling2D(pool_size=(2, 2),padding='same')(res1)
    conv21 = conv_bn_relu(pool1,48)
    conv2 = conv_bn_relu(conv21,48)
    res2  = Add()([conv2,conv21])

    pool2 = MaxPooling2D(pool_size=(2, 2))(res2)
    conv31 = conv_bn_relu(pool2,96)
    conv3 = conv_bn_relu(conv31,96)
    res3  = Add()([conv3,conv31])

    pool3 = MaxPooling2D(pool_size=(2, 2))(res3)
    conv41 = conv_bn_relu(pool3,192)
    conv4 = conv_bn_relu(conv41,192)
    res4  = Add()([conv41,conv4])


    #pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)
    #conv5 = Conv2D(1024, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool4)
    #conv5 = Conv2D(1024, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv5)
    up5 = UpSampling2D(size = (2,2))(res4)
    merge5 = concatenate([res3,up5], axis = 3)
    conv51 = conv_bn_relu(merge5,96)
    conv5 = conv_bn_relu(conv51,96)
    res5 = Add()([conv5,conv51])

    up6 = UpSampling2D(size = (2,2))(res5)
    merge6 = concatenate([res2,up6], axis = 3)
    conv61 = conv_bn_relu(merge6,48)
    conv6 = conv_bn_relu(conv61,48)
    res6 = Add()([conv6,conv61])

    up7 = UpSampling2D(size = (2,2))(res6)
    merge7 = concatenate([res1,up7], axis = 3)
    conv71 = conv_bn_relu(merge7,24)
    conv7 = conv_bn_relu(conv71,24)
    res7 = Add()([conv71,conv7])


    conv8 = Conv2D(1, 1)(res7)
    res_in = Conv2D(1, 1)(inputs)
    res8 = Add()([conv8,res_in])

    model = Model(input = inputs, output = res8)
    return model

def unet_res_small(image_channels = 1):
    inputs = Input(shape=(None,None,image_channels))
    conv1 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(inputs)
    conv1 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv1)                 
    res1  = Add()([inputs,conv1])

    pool1 = MaxPooling2D(pool_size=(2, 2),padding='same')(res1)
    conv21 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool1)
    conv2 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv21)
    res2  = Add()([conv2,conv21])


    pool3 = MaxPooling2D(pool_size=(2, 2))(res2)
    conv41 = Conv2D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool3)
    conv4 = Conv2D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv41)
    res3 = Add()([conv41,conv4])


    up6 = UpSampling2D(size = (2,2))(res3)
    merge6 = concatenate([res2,up6], axis = 3)
    conv61 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge6)
    conv6 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv61)
    res6 = Add()([conv6,conv61])

    up7 = UpSampling2D(size = (2,2))(res6)
    merge7 = concatenate([res1,up7], axis = 3)
    conv71 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge7)
    conv7 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv71)
    res7 = Add()([conv71,conv7])


    conv8 = Conv2D(1, 1)(res7)
    res8 = Add()([conv8,inputs])

    model = Model(input = inputs, output = res8)
    return model

def unet_res_small_3D(image_channels = 1):
    inputs = Input(shape=(None,None,None,image_channels))
    conv1 = Conv3D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(inputs)
    conv1 = Conv3D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv1)                 
    res1  = Add()([inputs,conv1])

    pool1 = MaxPooling3D(pool_size=(2, 2,2),padding='same')(res1)
    conv21 = Conv3D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool1)
    conv2 = Conv3D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv21)
    res2  = Add()([conv2,conv21])


    pool3 = MaxPooling3D(pool_size=(2, 2,2))(res2)
    conv41 = Conv3D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool3)
    conv4 = Conv3D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv41)
    res3 = Add()([conv41,conv4])


    up6 = UpSampling3D(size = (2,2,2))(res3)
    merge6 = concatenate([res2,up6], axis = 3)
    conv61 = Conv3D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge6)
    conv6 = Conv3D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv61)
    res6 = Add()([conv6,conv61])

    up7 = UpSampling3D(size = (2,2,2))(res6)
    merge7 = concatenate([res1,up7], axis = 3)
    conv71 = Conv3D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge7)
    conv7 = Conv3D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv71)
    res7 = Add()([conv71,conv7])


    conv8 = Conv3D(1, 1)(res7)
    res8 = Add()([conv8,inputs])

    model = Model(input = inputs, output = res8)
    return model

def unet_res_small_alternative(image_channels = 1):
    inputs = Input(shape=(None,None,image_channels))
    conv1 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(inputs)
    conv1 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv1)                 
    res1  = Add()([inputs,conv1])

    pool1 = MaxPooling2D(pool_size=(2, 2),padding='same')(res1)
    conv21 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool1)
    conv2 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv21)
    res2  = Add()([pool1,conv2])


    pool3 = MaxPooling2D(pool_size=(2, 2))(res2)
    conv41 = Conv2D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool3)
    conv4 = Conv2D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv41)
    res3 = Add()([pool3,conv4])


    up6 = UpSampling2D(size = (2,2))(res3)
    merge6 = concatenate([res2,up6], axis = 3)
    conv61 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge6)
    conv6 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv61)
    res6 = Add()([merge6,conv6])

    up7 = UpSampling2D(size = (2,2))(res6)
    merge7 = concatenate([res1,up7], axis = 3)
    conv71 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge7)
    conv7 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv71)
    res7 = Add()([merge7,conv7])


    conv8 = Conv2D(1, 1)(res7)
    res8 = Add()([conv8,inputs])

    model = Model(input = inputs, output = res8)
    return model

def unet_res_bn_small(image_channels = 1):
    inputs = Input(shape=(None,None,image_channels))
    conv1 = conv_bn_relu(inputs,24)
    conv1 = conv_bn_relu(conv1,24)           
    res1  = Add()([inputs,conv1])

    pool1 = MaxPooling2D(pool_size=(2, 2),padding='same')(res1)
    conv21 = conv_bn_relu(pool1,24)
    conv2 = conv_bn_relu(conv21,24)
    res2  = Add()([conv2,conv21])


    pool3 = MaxPooling2D(pool_size=(2, 2))(res2)
    conv41 = conv_bn_relu(pool3)
    conv4 = Conv2D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv41)
    res3 = Add()([conv41,conv4])


    up6 = UpSampling2D(size = (2,2))(res3)
    merge6 = concatenate([res2,up6], axis = 3)
    conv61 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge6)
    conv6 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv61)
    res6 = Add()([conv6,conv61])

    up7 = UpSampling2D(size = (2,2))(res6)
    merge7 = concatenate([res1,up7], axis = 3)
    conv71 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge7)
    conv7 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv71)
    res7 = Add()([conv71,conv7])


    conv8 = Conv2D(1, 1)(res7)
    res8 = Add()([conv8,inputs])

    model = Model(input = inputs, output = res8)
    return model

def conv_bn_relu(x,num_filters=32,kernel_size=3):
    x = Conv2D(num_filters, kernel_size, padding = 'same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    return x

def unet(image_channels = 1):
    inputs = Input(shape=(None,None,image_channels))
    conv1 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(inputs)
    conv1 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv1)                 
    

    pool1 = MaxPooling2D(pool_size=(2, 2),padding='same')(conv1)
    conv2 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool1)
    conv2 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv2)


    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)
    conv3 = Conv2D(96, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool2)
    conv3 = Conv2D(96, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv3)


    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)
    conv4 = Conv2D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(pool3)
    conv4 = Conv2D(192, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv4)


    up5 = UpSampling2D(size = (2,2))(conv4)
    merge5 = concatenate([conv3,up5], axis = 3)
    conv5 = Conv2D(96, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge5)
    conv5 = Conv2D(96, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv5)

    up6 = UpSampling2D(size = (2,2))(conv5)
    merge6 = concatenate([conv2,up6], axis = 3)
    conv6 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge6)
    conv6 = Conv2D(48, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv6)

    up7 = UpSampling2D(size = (2,2))(conv6)
    merge7 = concatenate([conv1,up7], axis = 3)
    conv7 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(merge7)
    conv7 = Conv2D(24, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal')(conv7)


    conv8 = Conv2D(1, 1)(conv7)
    res_in = Conv2D(1, 1)(inputs)
    res8 = Add()([conv8,res_in])

    model = Model(input = inputs, output = res8)
    return model

def unet_BN(image_channels = 1):
    inputs = Input(shape=(None,None,image_channels))
    conv1 = conv_bn_relu(inputs,24)
    conv1 = conv_bn_relu(conv1,24)                 
    

    pool1 = MaxPooling2D(pool_size=(2, 2),padding='same')(conv1)
    conv2 = conv_bn_relu(pool1,48)
    conv2 = conv_bn_relu(conv2,48)


    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)
    conv3 = conv_bn_relu(pool2,96)
    conv3 =conv_bn_relu(conv3,96)


    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)
    conv4 = conv_bn_relu(pool3,192)
    conv4 = conv_bn_relu(conv4,192)


    up5 = UpSampling2D(size = (2,2))(conv4)
    merge5 = concatenate([conv3,up5], axis = 3)
    conv5 = conv_bn_relu(merge5,96)
    conv5 = conv_bn_relu(conv5,96)

    up6 = UpSampling2D(size = (2,2))(conv5)
    merge6 = concatenate([conv2,up6], axis = 3)
    conv6 = conv_bn_relu(merge6,48)
    conv6 = conv_bn_relu(conv6,48)

    up7 = UpSampling2D(size = (2,2))(conv6)
    merge7 = concatenate([conv1,up7], axis = 3)
    conv7 = conv_bn_relu(merge7,24)
    conv7 = conv_bn_relu(conv7,24)


    conv8 = Conv2D(1, 1)(conv7)
    res_in = Conv2D(1, 1)(inputs)
    res8 = Add()([conv8,res_in])

    model = Model(input = inputs, output = res8)
    return model

def EDSR(depth=16,filters=64,image_channels=1, use_bnorm=False,scaling=None):
    layer_count = 0
    inpt = Input(shape=(None,None,image_channels),name = 'input'+str(layer_count))
    # 1st layer, Conv+relu
    layer_count += 1
    x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',name = 'conv'+str(layer_count))(inpt)
    # depth-2 layers, Conv+BN+relu
    for i in range(depth):
        shortcut = x
        layer_count += 1
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
        layer_count += 1
        x = Activation('relu',name = 'relu'+str(layer_count))(x)  
        layer_count += 1
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
        layer_count += 1
        x = Add(name = 'Add' + str(layer_count))([shortcut, x]) 
        if scaling:
            x = Lambda(lambda t: t * scaling)(x)
    # last layer, Conv
    layer_count += 1
    x = Conv2D(filters=image_channels, kernel_size=(3,3), strides=(1,1), kernel_initializer='Orthogonal',padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
    layer_count += 1
    x = Add(name = 'Add' + str(layer_count))([inpt, x])   # input - noise
    model = Model(inputs=inpt, outputs=x)
    
    return model

def WDSR(depth,filters=32, expansion = 4, image_channels=1, use_bnorm=False,scaling=None,):
    layer_count = 0
    inpt = Input(shape=(None,None,image_channels),name = 'input'+str(layer_count))
    # 1st layer, Conv+relu
    layer_count += 1
    x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1), padding='same',name = 'conv'+str(layer_count))(inpt)
    # depth-2 layers, Conv+BN+relu
    for i in range(depth):
        shortcut = x
        layer_count += 1
        x = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
        layer_count += 1
        x = Activation('relu',name = 'relu'+str(layer_count))(x)  
        #x = LeakyReLU()(x)
        layer_count += 1
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1), padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
        layer_count += 1
        x = Add(name = 'Add' + str(layer_count))([shortcut, x]) 
        if scaling:
            x = Lambda(lambda t: t * scaling)(x)
    # last layer, Conv
    layer_count += 1
    x = Conv2D(filters=image_channels, kernel_size=1, strides=1, padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
    layer_count += 1
    s = Conv2D(filters=image_channels, kernel_size=1, strides=1, padding='same',use_bias = False,name = 'conv'+str(layer_count))(inpt)
    x = Add(name = 'Add' + str(layer_count))([s, x])   # input - noise
    model = Model(inputs=inpt, outputs=x)
    
    return model


def res_block_b(x_in, num_filters, expansion, kernel_size, scaling):
    linear = 0.8
    x = Conv2D(num_filters * expansion, 1, padding='same')(x_in)
    x = Activation('relu')(x)
    x = Conv2D(int(num_filters * linear), 1, padding='same')(x)
    x = Conv2D(num_filters, kernel_size, padding='same')(x)
    x = Add()([x_in, x])
    if scaling:
        x = Lambda(lambda t: t * scaling)(x)
    return x

def wdsr_b(scale, num_filters, num_res_blocks, res_block_expansion, res_block_scaling, res_block):
    x_in = Input(shape=(None, None, 1))

    # main branch (revise padding)
    m = Conv2D(num_filters, 3, padding='same')(x_in)
    for i in range(num_res_blocks):
        m = res_block(m, num_filters, res_block_expansion, kernel_size=3, scaling=res_block_scaling)
    m = Conv2D(1, 3, padding='same', name='conv2d_main_scale_1')(m)
    # skip branch
    s = Conv2D(1, 5, padding='same', name='conv2d_skip_scale_1')(x_in)

    x = Add()([m, s])


    return Model(x_in, x, name="wdsr-b")

def wdsr2(scale, num_filters=32, num_res_blocks=8, res_block_expansion=6, res_block_scaling=None):
    return wdsr_b(scale, num_filters, num_res_blocks, res_block_expansion, res_block_scaling, res_block_b)


def WIN(depth=5,filters=128,image_channels=1):
    layer_count = 0
    inpt = Input(shape=(None,None,image_channels),name = 'input'+str(layer_count))
    layer_count += 1
    x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1), kernel_initializer='he_normal', bias_initializer='constant', padding='same', name='conv'+str(layer_count))(inpt)
    layer_count += 1
    x = Activation('relu',name = 'relu'+str(layer_count))(x)
    for i in range(depth-2):
        layer_count += 1
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1), kernel_initializer='he_normal',padding='same', bias_initializer='constant',name='conv'+str(layer_count))(x)
        layer_count += 1
        x = Activation('relu',name = 'relu'+str(layer_count))(x)
    x = Conv2D(filters=image_channels, kernel_size=(3,3), strides=(1,1), kernel_initializer='he_normal',padding='same',bias_initializer='constant',name = 'conv'+str(layer_count))(x)
    layer_count += 1
    x = Add(name = 'Add' + str(layer_count))([inpt, x])   # input + -noise
    model = Model(inputs=inpt, outputs=x)
    return model


def dilated_net(image_channels=1):
    inpt = Input(shape=(None,None,image_channels))
    m = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal')(inpt)

    x = Conv2D(64, 3, padding = 'same', kernel_initializer = 'Orthogonal')(m)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    
    for _ in range(3):
        x = Conv2D(64, 3, padding = 'same', kernel_initializer = 'Orthogonal')(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
    
    local = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=2)(m)
    local = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=4)(local)
    local = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=8)(local)
    local = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=16)(local)

    concat = concatenate([x,local],axis=3)
    out = Conv2D(1,1, padding = 'same', kernel_initializer = 'Orthogonal')(concat)
    z = Conv2D(1, 1, padding = 'same', kernel_initializer = 'Orthogonal')(inpt)
    out = Add()([out,z])
    model = Model(inputs=inpt, outputs=out)
    return model

#conv_bn_relu
def _dilated_net_no_BN_3D(image_channels=1,filters=64):
    inpt = Input(shape=(None,None,None,image_channels))
    m = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal')(inpt)
    x = Conv3D(filters, 3, padding = 'same', kernel_initializer = 'Orthogonal')(m)
    x = Activation('relu')(x)
    
    for _ in range(3):
        x = Conv2D(filters, 3, padding = 'same', kernel_initializer = 'Orthogonal')(x)
        x = Activation('relu')(x)
    
    local = Conv2D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=2)(m)
    local = Conv2D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=4)(local)
    local = Conv2D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=8)(local)
    local = Conv2D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=16)(local)

    concat = concatenate([x,local],axis=3)
    out = Conv2D(1,1, padding = 'same', kernel_initializer = 'Orthogonal')(concat)
    z = Conv2D(1, 1, padding = 'same', kernel_initializer = 'Orthogonal')(inpt)
    out = Add()([out,z])
    model = Model(inputs=inpt, outputs=out)
    return model

def dilated_net_no_BN_full_3D(image_channels=1,filters=64):  #not working, loss explode
    inpt = Input(shape=(None,None,None,image_channels))
    m = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal')(inpt)
    x = Conv3D(filters, 3, padding = 'same', kernel_initializer = 'Orthogonal')(m)
    x = Activation('relu')(x)
    
    for _ in range(3):
        x = Conv3D(filters, 3, padding = 'same', kernel_initializer = 'Orthogonal')(x)
        x = Activation('relu')(x)
    
    local = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=2)(m)
    local = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=4)(local)
    local = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=8)(local)
    local = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=16)(local)

    concat = Add()([x,local])#concatenate([x,local],axis=4)
    out = Conv3D(1, 1, padding = 'same', kernel_initializer = 'Orthogonal')(concat)
    z = Conv3D(1, 1, padding = 'same', kernel_initializer = 'Orthogonal')(inpt)
    out = Add()([out,z])
    model = Model(inputs=inpt, outputs=out)
    return model

def dilated_net_BN_full_3D(image_channels=1,filters=64):  #not working, loss explode
    inpt = Input(shape=(None,None,None,image_channels))
    m = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal')(inpt)
    m = BatchNormalization()(m)
    x = Conv3D(filters, 3, padding = 'same', kernel_initializer = 'Orthogonal')(m)
    x = Activation('relu')(x)
    x = BatchNormalization()(x)
    
    for _ in range(3):
        x = Conv3D(filters, 3, padding = 'same', kernel_initializer = 'Orthogonal')(x)
        x = Activation('relu')(x)
        x = BatchNormalization()(x)
    
    local = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=2)(m)
    local = BatchNormalization()(local)
    local = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=4)(local)
    local = BatchNormalization()(local)
    local = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=8)(local)
    local = BatchNormalization()(local)
    local = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=16)(local)
    local = BatchNormalization()(local)

    concat = concatenate([x,local],axis=4)
    out = Conv3D(1, 1, padding = 'same', kernel_initializer = 'Orthogonal')(concat)
    z = Conv3D(1, 1, padding = 'same', kernel_initializer = 'Orthogonal')(inpt)
    out = Add()([out,z])
    model = Model(inputs=inpt, outputs=out)
    return model


def dilated_net_no_BN_3D(image_channels=1,filters=64):
    inpt = Input(shape=(None,None,None,image_channels))
    m = Conv3D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal')(inpt)
    x = Conv3D(filters, 3, padding = 'same', kernel_initializer = 'Orthogonal')(m)
    x = Activation('relu')(x)
    
    for _ in range(3):
        x = Conv2D(filters, 3, padding = 'same', kernel_initializer = 'Orthogonal')(x)
        x = Activation('relu')(x)
    
    local = Conv2D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=2)(m)
    local = Conv2D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=4)(local)
    local = Conv2D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=8)(local)
    local = Conv2D(filters, 3, activation = 'relu', padding = 'same', kernel_initializer = 'Orthogonal',dilation_rate=16)(local)

    concat = Add()([x,local])#concatenate([x,local],axis=4)
    out = Conv2D(1, 1, padding = 'same', kernel_initializer = 'Orthogonal')(concat)
    z = Conv2D(1, 1, padding = 'same', kernel_initializer = 'Orthogonal')(inpt)
    out = Add()([out,z])
    model = Model(inputs=inpt, outputs=out)
    return model

def dilated_net_wide(depth, image_channels=1, filters=32, expansion=4):
    inpt = Input(shape=(None,None,image_channels))
    x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same')(inpt) 
    m = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same')(inpt)
    for i in range(depth):
        shortcut = x
        x = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)  #why not use bias?
        x = Activation('relu')(x)  
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)
        x = Add()([shortcut, x]) 

    for i in range(1,depth+1):
        shortcut = m
        m = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal',dilation_rate=2**depth, padding='same',use_bias = False)(m)
        m = Activation('relu')(m)  
        m = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(m)
        m = Add()([shortcut, m]) 
    x = concatenate([x,m])
    x = Conv2D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(x)  #why not use bias?
    s = Conv2D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(inpt)
    x = Add()([s, x])   # input - noise
    model = Model(inputs=inpt, outputs=x)

    return model

def dilated_net_wide_3D(depth, image_channels=1, filters=32, expansion=4):
    inpt = Input(shape=(None,None,None,image_channels))
    x = Conv3D(filters=filters, kernel_size=3, strides=1,kernel_initializer='Orthogonal', padding='same')(inpt) 
    m = Conv3D(filters=filters, kernel_size=3, strides=1,kernel_initializer='Orthogonal', padding='same')(inpt)
    for i in range(depth):
        shortcut = x
        x = Conv3D(filters=filters * expansion, kernel_size=3, strides=1,kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)  #why not use bias?
        x = Activation('relu')(x)  
        x = Conv3D(filters=filters, kernel_size=3, strides=1,kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)
        x = Add()([shortcut, x]) 

    for i in range(1,depth+1):
        shortcut = m
        m = Conv3D(filters=filters * expansion, kernel_size=3, strides=1,kernel_initializer='Orthogonal',dilation_rate=2**depth, padding='same',use_bias = False)(m)
        m = Activation('relu')(m)  
        m = Conv3D(filters=filters, kernel_size=3, strides=1,kernel_initializer='Orthogonal', padding='same',use_bias = False)(m)
        m = Add()([shortcut, m]) 
    x = concatenate([x,m])
    x = Conv3D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(x)  #why not use bias?
    s = Conv3D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(inpt)
    x = Add()([s, x])   # input - noise
    model = Model(inputs=inpt, outputs=x)

    return model


def dilated_net_wide_superASL(depth, image_channels=1, filters=32, expansion=4):

    input1 = Input(shape=(None,None,image_channels))
    input2 = Input(shape=(None,None,image_channels))
    input3 = Input(shape=(None,None,image_channels))
    input4 = Input(shape=(None,None,image_channels))
    input5 = Input(shape=(None,None,image_channels))

    inpt1 = Conv2D(6, 3, padding='same')(input1)
    inpt2 = Conv2D(6, 3, padding='same')(input2)
    inpt3 = Conv2D(8, 3, padding='same')(input3)
    inpt4 = Conv2D(6, 3, padding='same')(input4)
    inpt5 = Conv2D(6, 3, padding='same')(input5)

    x = concatenate([inpt1,inpt2,inpt3,inpt4,inpt5])
    m = concatenate([inpt1,inpt2,inpt3,inpt4,inpt5])

    #x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same')(inpt) 
    #m = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same')(inpt)
    for i in range(depth):
        shortcut = x
        x = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)  #why not use bias?
        x = Activation('relu')(x)  
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)
        x = Add()([shortcut, x]) 

    for i in range(1,depth+1):
        shortcut = m
        m = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal',dilation_rate=2**depth, padding='same',use_bias = False)(m)
        m = Activation('relu')(m)  
        m = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(m)
        m = Add()([shortcut, m]) 
    x = concatenate([x,m])
    x = Conv2D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(x)  #why not use bias?
    s = Conv2D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(inpt3)
    x = Add()([s, x])   # input - noise
    model = Model(inputs=[input1,input2,input3,input4,input5], outputs=x)

    return model

def dilated_net_wide_bn(depth, image_channels=1, filters=32, expansion=4):
    inpt = Input(shape=(None,None,image_channels))
    x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same')(inpt) 
    m = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same')(inpt)
    for i in range(depth):
        shortcut = x
        x = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)  #why not use bias?
        x = BatchNormalization()(x)
        x = Activation('relu')(x)  
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)
        x = BatchNormalization()(x)
        x = Add()([shortcut, x]) 

    for i in range(1,depth+1):
        shortcut = m
        m = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal',dilation_rate=2**depth, padding='same',use_bias = False)(m)
        m = BatchNormalization()(m)
        m = Activation('relu')(m)  
        m = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(m)
        m = BatchNormalization()(m)
        m = Add()([shortcut, m]) 
    x = concatenate([x,m])
    x = Conv2D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(x)  #why not use bias?
    s = Conv2D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(inpt)
    x = Add()([s, x])   # input - noise
    model = Model(inputs=inpt, outputs=x)

    return model

def dilated_net_wide_no_res(depth, image_channels=1, filters=32, expansion=4):
    inpt = Input(shape=(None,None,image_channels))
    x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same')(inpt) 
    m = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same')(inpt)
    for i in range(depth):
        shortcut = x
        x = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)  #why not use bias?
        x = Activation('relu')(x)  
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)
        x = Add()([shortcut, x]) 

    for i in range(1,depth+1):
        shortcut = m
        m = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal',dilation_rate=2**depth, padding='same',use_bias = False)(m)
        m = Activation('relu')(m)  
        m = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False)(m)
        m = Add()([shortcut, m]) 
    x = concatenate([x,m])
    x = Conv2D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(x)  #why not use bias?
    #s = Conv2D(filters=image_channels, kernel_size=1, strides=1, kernel_initializer='Orthogonal',padding='same',use_bias = False)(inpt)
    #x = Add()([s, x])   # input - noise
    model = Model(inputs=inpt, outputs=x)

    return model

def wdsr_block(x,filters=32,expansion=4):
    shortcut = x
    x = Conv2D(filters=filters * expansion, kernel_size=3, strides=1,kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)  #why not use bias?
    x = Activation('relu')(x)  
    x = Conv2D(filters=filters, kernel_size=3, strides=1,kernel_initializer='Orthogonal', padding='same',use_bias = False)(x)
    x = Add()([shortcut, x]) 
    return x

def unet_wide(image_channels = 1):
    inputs = Input(shape=(None,None,image_channels))
    conv1 = Conv2D(32, 3, activation = 'relu', padding = 'same')(inputs)
    conv1 = wdsr_block(conv1)                 #32

    pool1 = MaxPooling2D(pool_size=(2, 2),padding='same')(conv1)
    conv2 = wdsr_block(pool1)               #32

    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)
    conv3 = wdsr_block(pool2)       #32

    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)
    conv4 = wdsr_block(pool3)   #32

    up5 = UpSampling2D(size = (2,2))(conv4) 
    merge5 = concatenate([conv3,up5], axis = 3)     #64
    conv5 = wdsr_block(merge5,64)

    up6 = UpSampling2D(size = (2,2))(conv5)    #96
    merge6 = concatenate([conv2,up6], axis = 3)
    conv6 = wdsr_block(merge6,96,2)

    up7 = UpSampling2D(size = (2,2))(conv6)       #128
    merge7 = concatenate([conv1,up7], axis = 3)
    conv7 = wdsr_block(merge7,128,1)

    conv8 = Conv2D(1, 1, activation = 'relu', padding = 'same')(conv7)
    m = Conv2D(1, 1, activation = 'relu', padding = 'same')(inputs)
    res8 = Add()([conv8,m])

    model = Model(input = inputs, output = res8)
    return model




### not good performance
def WDSR_dilated(depth,filters=32, expansion = 4, image_channels=1, use_bnorm=False,scaling=None,):
    layer_count = 0
    inpt = Input(shape=(None,None,image_channels),name = 'input'+str(layer_count))
    # 1st layer, Conv+relu
    layer_count += 1
    x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',name = 'conv'+str(layer_count))(inpt)

    local = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal',dilation_rate=2)(x)
    local = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal',dilation_rate=4)(local)
    local = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal',dilation_rate=8)(local)
    local = Conv2D(64, 3, activation = 'relu', padding = 'same', kernel_initializer = 'he_normal',dilation_rate=16)(local)
    # depth-2 layers, Conv+BN+relu
    for i in range(depth):
        shortcut = x
        layer_count += 1
        x = Conv2D(filters=filters * expansion, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
        layer_count += 1
        x = Activation('relu',name = 'relu'+str(layer_count))(x)  
        #x = LeakyReLU()(x)
        layer_count += 1
        x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
        layer_count += 1
        x = Add(name = 'Add' + str(layer_count))([shortcut, x]) 
        if scaling:
            x = Lambda(lambda t: t * scaling)(x)
    # last layer, Conv
    layer_count += 1
    x = Conv2D(filters=image_channels, kernel_size=(3,3), strides=(1,1), kernel_initializer='Orthogonal',padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
    x = concatenate()([x,local])
    layer_count += 1
    s = Conv2D(filters=image_channels, kernel_size=(3,3), strides=(1,1), kernel_initializer='Orthogonal',padding='same',use_bias = False,name = 'conv'+str(layer_count))(inpt)
    x = Add(name = 'Add' + str(layer_count))([s, x])   # input - noise
    model = Model(inputs=inpt, outputs=x)
    
    return model