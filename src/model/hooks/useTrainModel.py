import tensorflow as tf
from tensorflow.keras.layers import Input, Conv1D, MaxPooling1D, SimpleRNN, GRU, LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.regularizers import l2
from tensorflow.keras.losses import LogCosh
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
# ✅ นำเข้าตัวแปรคุมสอบจาก Config ครบถ้วนตามสเปคของคุณ
from config.Config import Colors, Epochs, BatchSize, KernelSize, Filters, KernelRegularizer, Activation, DropoutValue, Units, Optimizer, Metrics, PoolSize, DenseValue, PATIENCE_VALUE

def get_recurrent_layer(model_type, units, return_sequences=False, **kwargs):
    layer_args = {"units": units, "return_sequences": return_sequences, **kwargs}

    model_type = model_type.upper()
    if model_type == "RNN":
        return SimpleRNN(**layer_args)
    elif model_type == "LSTM":
        return LSTM(**layer_args)
    elif model_type == "GRU":
        return GRU(**layer_args)
    else:
        raise ValueError(f"❌ Unsupported architecture: {model_type} (Supports RNN, GRU, LSTM)")

def UseTrainModel(X_train, X_test, y_train, y_test, model_type, gpus):
    print(f"{Colors.CYAN}   -> [1/3] Building GOD-TIER BOOTCAMP (CNN-{model_type.upper()} Hybrid) architecture...{Colors.RESET}")
    
    with tf.device('/GPU:0') if gpus else tf.device('/CPU:0'):
        model = Sequential()
        
        # 1. ชั้นรับข้อมูล Input ไดนามิก (เช่น 180 steps, 4 features)
        model.add(Input(shape=(X_train.shape[1], X_train.shape[2]))) 

        # =====================================================================
        # 👓 ท่อนที่ 1: แว่นตา Conv1D สองชั้น (ดึง Filters และ KernelSize จาก Config)
        # =====================================================================
        # ชั้นที่ 1.1: สแกนหาคลื่นความถี่พื้นฐาน
        model.add(Conv1D(filters=Filters, kernel_size=KernelSize, activation=Activation, kernel_regularizer=l2(KernelRegularizer)))
        model.add(BatchNormalization())

        # ชั้นที่ 1.2: สแกนเชิงลึก (ขยายฟิลเตอร์เป็น 2 เท่าตามหลัก Deep Learning สากล)
        model.add(Conv1D(filters=Filters * 2, kernel_size=KernelSize, activation=Activation))
        model.add(MaxPooling1D(pool_size=PoolSize))
        model.add(BatchNormalization())
        model.add(Dropout(DropoutValue))

        # =====================================================================
        # 🧠 ท่อนที่ 2: สมองกลอนุกรมเวลาแบบ Double-Stack (เค้นความจำระยะยาว)
        # =====================================================================
        # สมองส่วนหน้า: ถักทอสายใยเวลา
        model.add(get_recurrent_layer(
            model_type, units=Units, return_sequences=True,
            activation=Activation, kernel_regularizer=l2(KernelRegularizer)
        ))
        model.add(BatchNormalization())
        model.add(Dropout(DropoutValue))

        # สมองส่วนหลัง: ตกผลึกข้อสรุปสุดท้ายก่อนทายผล
        model.add(get_recurrent_layer(
            model_type, units=Units // 2, return_sequences=False, # ✅ แก้เป็น // 2
            activation='relu'
        ))
        model.add(Dropout(DropoutValue + 0.1))

        # =====================================================================
        # 🎯 ท่อนที่ 3: Fully Connected ชั้นสังเคราะห์คำตอบความละเอียดสูง
        # =====================================================================
        model.add(Dense(DenseValue, activation='relu'))
        model.add(Dense(DenseValue // 2, activation='relu')) # ✅ แก้เป็น // 2
        model.add(Dense(DenseValue // 16))

        model.compile(optimizer=Optimizer, loss=LogCosh(), metrics=[Metrics])
        
    print(f"{Colors.CYAN}   -> [2/3] Configuring Marathon Callbacks (Patience=50)...{Colors.RESET}")
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss', 
        factor=0.2,       # ปรับตัวเลขแม่นยำขึ้นเมื่อเจอทางตัน
        patience=10,      # รอก่อน 10 รอบถ้า Loss ไม่ลงค่อยลด LR
        min_lr=1e-7,      # ยอมให้ LR เล็กลงไปได้ลึกถึงระดับอะตอม
        verbose=1
    )
    early_stop = EarlyStopping(
        monitor='val_loss', 
        patience=PATIENCE_VALUE, # ให้รอสูงสุด 50 รอบก่อนตัดใจหยุด
        restore_best_weights=True, 
        verbose=1
    )
    
    print(f"{Colors.CYAN}   -> [3/3] Started Bootcamp training CNN-{model_type.upper()}...{Colors.RESET}")
    
    dataset = tf.data.Dataset.from_tensor_slices((X_train, y_train))
    dataset = dataset.shuffle(1000).batch(BatchSize).prefetch(tf.data.AUTOTUNE)
    
    history = model.fit(
        dataset,
        epochs=Epochs,        # ✅ ดึงจาก Config
        batch_size=BatchSize, # ✅ ดึงจาก Config
        validation_data=(X_test, y_test), 
        callbacks=[reduce_lr, early_stop]
    )

    print(f"{Colors.GREEN}   -> [Done] Hardcore Hybrid Training completed successfully!{Colors.RESET}")
    return model, history