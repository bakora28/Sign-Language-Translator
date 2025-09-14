
import os
import cv2
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
# Arabic processing imports - keeping for potential future use
# from arabic_reshaper import reshape  
# from bidi.algorithm import get_display
# PIL imports removed - no longer needed for frame drawing
import datetime

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Initialize Hands
hands = mp_hands.Hands(
    min_tracking_confidence=0.7,
    min_detection_confidence=0.7,
    max_num_hands=2,
    static_image_mode=True
)

# Load model
modelLSTM = load_model("action3.h5")

# Actions and translations
actions = ['Act', 'Alhamdullah', 'all', 'Baba', 'Basis', 'because', 'Boy', 'Brave', 'calls', 'calm',
           'College', 'Confused', 'conversation', 'Crying', 'daily', 'danger', 'disagree with', 'drinks',
           'Eats', 'effort', 'Egypt', 'Enters', 'Excelent', 'explanation', 'Fasting', 'Female', 'First',
           'For Us', 'fuel', 'Gift', 'Girl', 'Glass', 'good bye', 'government', 'Happy', 'hates', 'hears',
           'Help', 'Here You Are', 'how_are_u', 'Humanity', 'hungry', 'I', 'ignorance', 'immediately',
           'Important', 'Intelligent', 'Last', 'leader', 'Liar', 'Loves', 'male', 'Mama', 'memory', 'model',
           'mostly', 'motive', 'Muslim', 'must', 'my home land', 'no', 'nonsense', 'obvious', 'Old',
           'Palestine', 'prevent', 'ready', 'rejection', 'Right', 'selects', 'shut up', 'Sing', 'sleeps',
           'smells', 'Somkes', 'Spoon', 'Summer', 'symposium', 'Tea', 'teacher', 'terrifying', 'Thanks',
           'time', 'to boycott', 'to cheer', 'to go', 'to live', 'to spread', 'Toilet', 'trap', 'University',
           'ur_welcome', 'victory', 'walks', 'Where', 'wheres_ur_house', 'Window', 'Winter', 'yes', 'You']

reverb = {
    'Act': 'تتصرف', 'Alhamdullah': 'الحمدلله', 'all': 'جميعا', 'Baba': 'بابا', 'Basis': 'اساسيات',
    'because': 'بسبب', 'Boy': 'ولد', 'Brave': 'شجاع', 'calls': 'اتصل', 'calm': 'هادئ', 'College': 'كليه',
    'Confused': 'متوتر', 'conversation': 'محادثه', 'Crying': 'بكاء', 'daily': 'يوميا', 'danger': 'خطر',
    'disagree with': 'اختلف مع', 'drinks': 'اشرب', 'Eats': 'اكل', 'effort': 'مجهود', 'Egypt': 'مصر',
    'Enters': 'دخول', 'Excelent': 'ممتاز', 'explanation': 'الشرح', 'Fasting': 'في الصيام', 'Female': 'انثي',
    'First': 'اولا', 'For Us': 'لنا', 'fuel': 'الوقود', 'Gift': 'الهديه', 'Girl': 'البنت', 'Glass': 'الكوب',
    'good bye': 'الي اللقاء', 'government': 'الحكومه', 'Happy': 'بسعاده', 'hates': 'اكره', 'hears': 'اسمع',
    'Help': 'تساعد', 'Here You Are': 'تفضل', 'how_are_u': 'كيف حالك', 'Humanity': 'البشريه', 'hungry': 'اشعر بالجوع',
    'I': 'انا', 'ignorance': 'تجاهل', 'immediately': 'حالا', 'Important': 'المهم', 'Intelligent': 'الذكاء',
    'Last': 'الاخير', 'leader': 'القائد', 'Liar': 'الكاذب', 'Loves': 'احب', 'male': 'ذكر', 'Mama': 'ماما',
    'memory': 'الذاكره', 'model': 'نموذج', 'mostly': 'في الغالب', 'motive': 'الدافع', 'Muslim': 'مسلم',
    'must': 'لازم', 'my home land': 'وطني', 'no': 'لا', 'nonsense': 'الهراء', 'obvious': 'بديهي', 'Old': 'القديمه',
    'Palestine': 'فلسطين', 'prevent': 'اوقف', 'ready': 'جاهز_ل', 'rejection': 'الرفض', 'Right': 'صحيح',
    'selects': 'تختار', 'shut up': 'اصمت', 'Sing': 'الغني', 'sleeps': 'النوم', 'smells': 'اشم', 'Somkes': 'يسمح بالتدخين',
    'Spoon': 'بالمعلقه', 'Summer': 'الصيف', 'symposium': 'الندوه', 'Tea': 'الشاي', 'teacher': 'معلمي',
    'terrifying': 'مخيف', 'Thanks': 'شكرا لكم', 'time': 'الوقت', 'to boycott': 'تقاطع لاجل', 'to cheer': 'تهتف ل',
    'to go': 'ذاهب الي', 'to live': 'ل اعيش', 'to spread': 'تنتشر', 'Toilet': 'دوره المياه', 'trap': 'فخ',
    'University': 'الجامعه', 'ur_welcome': 'مرحباً بكم', 'victory': 'النصر', 'walks': 'المشي', 'Where': 'اين',
    'wheres_ur_house': 'اين تسكن', 'Window': 'الشباك', 'Winter': 'الشتاء', 'yes': 'نعم', 'You': 'انت'
}

def mediapipe_detection(image, model):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = model.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return image, results

def draw_styled_landmarks(image, results):
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

def extract_keypoints(results):
    data_aux = []
    x_ = []
    y_ = []
    if results.multi_hand_landmarks:
        print(f"Detected {len(results.multi_hand_landmarks)} hands")
        if len(results.multi_hand_landmarks) == 1:
            for hand_landmarks in results.multi_hand_landmarks:
                for i in range(len(hand_landmarks.landmark)):
                    x_.append(hand_landmarks.landmark[i].x)
                    y_.append(hand_landmarks.landmark[i].y)
                for i in range(len(hand_landmarks.landmark)):
                    data_aux.append(hand_landmarks.landmark[i].x - min(x_))
                    data_aux.append(hand_landmarks.landmark[i].y - min(y_))
                for i in range(42, 84):
                    data_aux.append(0.0)
        elif len(results.multi_hand_landmarks) == 2:
            for hand_landmarks in results.multi_hand_landmarks:
                for i in range(len(hand_landmarks.landmark)):
                    x_.append(hand_landmarks.landmark[i].x)
                    y_.append(hand_landmarks.landmark[i].y)
                for i in range(len(hand_landmarks.landmark)):
                    data_aux.append(hand_landmarks.landmark[i].x - min(x_))
                    data_aux.append(hand_landmarks.landmark[i].y - min(y_))
    else:
        print("No hands detected")
        for i in range(84):
            data_aux.append(0.0)
    print(f"Keypoints length: {len(data_aux)}")
    return data_aux

def process_frame(frame, sequence, sentence, last_update_time, threshold=0.95):
    image, results = mediapipe_detection(frame, hands)
    if results.multi_hand_landmarks:
        keypoints = extract_keypoints(results)
        if len(keypoints) == 84:
            sequence.append(keypoints)
            if len(sequence) == 15:
                res = modelLSTM.predict(np.expand_dims(sequence, axis=0))[0]
                EN = actions[np.argmax(res)]
                confidence = res[np.argmax(res)]
                print(f"Predicted: {reverb[EN]} with confidence {confidence}")
                if confidence > threshold:
                    if not sentence or reverb[EN] != sentence[-1][0]:
                        sentence.append((reverb[EN], confidence))
                        last_update_time = datetime.datetime.now()
                sequence.clear()
    else:
        sequence.clear()

    timeout_minutes = 0.5
    current_time = datetime.datetime.now()
    if sentence:
        time_elapsed_minutes = (current_time - last_update_time).total_seconds() / 60
        if time_elapsed_minutes > timeout_minutes:
            sentence.clear()

    # Process Arabic text for frontend display (no frame overlay needed)
    if sentence:
        # Join the individual Arabic words in detection order
        arabic_words = [word[0] for word in sentence]
        
        # Simple approach: just join the words - browser handles RTL correctly
        reshaped_sentence = ' '.join(arabic_words)
        print(f"🔤 Arabic sentence: '{reshaped_sentence}'")
    else:
        reshaped_sentence = ""
    
    # Only draw hand landmarks on frame (no text overlay)
    draw_styled_landmarks(frame, results)

    return frame, sequence, sentence, last_update_time, reshaped_sentence

def main():
    sequence = []
    sentence = []
    threshold = 0.99
    last_update_time = datetime.datetime.now()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        frame = cv2.flip(frame, 1)
        frame, sequence, sentence, last_update_time, reshaped_sentence = process_frame(
            frame, sequence, sentence, last_update_time, threshold
        )

        cv2.imshow('Frame', frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()