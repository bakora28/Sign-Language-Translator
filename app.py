from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, send_from_directory, abort
from flask_socketio import SocketIO, emit, join_room
import os
import cv2
from tensorflow.keras.models import load_model
import mediapipe as mp
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from PIL import ImageFont, ImageDraw, Image
import base64
import threading
from spellchecker import SpellChecker
from difflib import get_close_matches
import firebase_admin
from firebase_admin import credentials, auth, firestore
from flask_session import Session
from skimage.feature import hog
from skimage import io, color, transform
import joblib
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import requests
import time
import sys
import traceback
import numpy as np
import datetime
from realtime_sign import process_frame
from asl_model_detection import initialize_asl_detector, get_asl_detector

# Force UTF-8 console streams on Windows to avoid print-time Unicode crashes.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def handle_exception(exc_type, exc_value, exc_traceback):
    print('Uncaught exception:', exc_value, file=sys.stderr)
    traceback.print_tb(exc_traceback, file=sys.stderr)

sys.excepthook = handle_exception

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'Uploads/'
app.config['SECRET_KEY'] = 'a3214f61d2e294feb9af7ffe60462e5'  # Replace with a strong secret key
app.config['SESSION_TYPE'] = 'filesystem'

# Email and Name Configuration
app.config['ADMIN_EMAIL'] = 'admin@tawasol.com'  # Default admin email
app.config['APP_NAME'] = 'Tawasol - Sign Language Translator'  # Application name
app.config['SUPPORT_EMAIL'] = 'support@tawasol.com'  # Support contact email
app.config['ORGANIZATION_NAME'] = 'Tawasol Team'  # Organization name

Session(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to get configuration values
def get_config(key, default=None):
    """
    Get configuration value by key
    
    Args:
        key (str): Configuration key
        default: Default value if key not found
    
    Returns:
        Configuration value or default
    """
    return app.config.get(key, default)

# Initialize Flask-SocketIO with CORS support
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Initialize Firebase Admin SDK
cred = credentials.Certificate('sign-language-f0172-firebase-adminsdk-fbsvc-67cb4487da.json')
firebase_admin.initialize_app(cred)

# Initialize ASL EfficientNetB0 detector for enhanced sign language detection
print("Initializing ASL EfficientNetB0 detector...")
asl_success = initialize_asl_detector()
if asl_success:
    print("ASL EfficientNetB0 detector initialized successfully")
else:
    print("Warning: ASL detector initialization failed, falling back to MediaPipe only")

# Set up Firestore
db = firestore.client()

# Firebase REST API key
FIREBASE_API_KEY = 'AIzaSyBMdkPK4CZHF1KoAfc37_UV27AJbIY9KgE'

# Text-to-GIF conversion logic
dictionary = {
    "ام": ["ماما", "امي", "مامتي", "الام"],
    "اب": ["بابا", "ابي", "ابويا", "والدي", "الاب"],
    "هو": ["انتي", "هي", "انت", "ده", "ديه", "هوه", "هو نفسه"],
    "مول": ["مركز تسوق", "مول تجاري", "مركز تجاري", "المول", "مركز التسوق"],
    "ياكل": ["باكل", "اكل", "جعان", "هاكل", "الاكل"],
    "يسمع": ["بسمع", "نسمع", "اسمع", "تسمع", "سامع"],
    "كذاب": ["كداب", "بكدب", "الكدب", "الكذب", "كدبه", "كذبه", "كذية", "كدبة"],
    "لو سمحت": ["من فضلك"],
    "ما فهمت عليك": ["مش فاهمك", "مفهمتش", "مش فاهم", "مفهمتكش"],
    "متنوع": ["متنوعه"],
    "محادثه": ["مناقشه", "المنقشه", "المحادثه", "المناقشة", "المحادثة", "محادثة", "مناقشة"],
    "معني": ["معنى", "المعني", "المعنى", "يعني", "قصدك", "تقصد"],
    "مهمه": ["مهمة", "المهمه"],
    "مهمات": ["مهماة", "مهام", "المهمات", "المهماة"],
    "مهم": ["المهم"],
    "موضوع": ["الموضوع", "حوار", "الحوار"],
    "حب": ["الحب", "احب", "بتحب", "بحب"],
    "دائم": ["دايم", "دايما", "دائما", "عل طول"],
    "دقائق": ["الدقائق", "دقايق", "الدقايق"],
    "دقيقه": ["دقيقة", "الدقيقه", "الدقيقة"],
    "ساعه": ["ساعة", "الساعه", "الساعة", "ميعاد", "وقت", "الوقت"],
    "سر": ["السر"],
    "سعيد": ["مبسوط", "سعيده", "مبسوطه", "فراحان", "فرحانه", "سعيدة", "مبسوطة", "فرحانة"],
    "سهل": ["سهله", "سهلة", "سهوله", "سهولة", "السهوله", "السهولة"],
    "شكرا": ["الشكر", "اشكر", "بشكر"],
    "صادق": ["الصادق", "صادقه", "صادقة"],
    "ضمير": ["ضميري", "الضمير"],
    "طفل": ["طلفة", "طفله", "الطفل", "الطفله", "الطفلة", "طفل رضيع", "صغير في السن", "صغيره في السن", "صغيرة في السن"],
    "علي مهلك": ["على مهلك", "براحه", "براحة"],
    "قف": ["اقف", "اقفي", "توقف", "توقفي", "الوقف", "التوقف", "قفي"],
    "قلق": ["قلقان", "القلق", "قلقانه", "قلقانة"],
    "الجامع": ["المسجد", "جامع", "مسجد"],
    "انا استأذنك": ["بستاذنك", "بستأذنك", "بعد اذنك", "بعد أذنك", "انا استاذنك"],
    "انهاء": ["أنهاء", "انتهى", "خلص", "خلصت", "بخلص"],
    "انهارده": ["انهاردة"],
    "بيت": ["البيت", "المنزل", "منزل"],
    "تحتاج مساعده": ["تحتاج مساعدة", "عايز مساعده", "عايز مساعدة", "اساعدك"],
    "تفكير": ["يفكر", "التفكير", "تفكر", "تفتكر", "بفكر", "نفكر", "هفكر", "افكار"],
    "ثانيه": ["ثواني", "ثانية", "الثانيه", "الثانية"],
    "جيد": ["كويس", "تمام", "كويسه", "كويسة"],
    "0": ["صفر", "الصفر"],
    "1": ["واحد"],
    "2": ["اتنين", "اثنين"],
    "3": ["تلاته", "ثلاثة"],
    "4": ["أربعة", "اربعه", "أربعه", "اربعة"],
    "5": ["خمسة", "خمسه"],
    "6": ["ستة", "سته"],
    "7": ["سبعة", "سبعه"],
    "8": ["تمانية", "تمانيه", "ثمانيه", "ثمانية"],
    "9": ["تسعة", "تسعه"],
    "10": ["عشرة", "عشره"],
    "11": ["احد عشر", "حداشر"],
    "12": ["اثنا عشر", "اتناشر"],
    "20": ["عشرين"],
    "30": ["ثلاثين"],
    "40": ["أربعين", "اربعين"],
    "60": ["ستين"],
    "70": ["سبعين"],
    "80": ["تمانين"],
    "90": ["تسعين"],
    "100": ["مية", "مائة", "ميه"],
    "200": ["ميتين"],
    "1000": ["ألف", "الف"],
    "احنا": ["نحن", "إحنا", "كلنا"],
    "ازاي": ["كيف", "إزاي"],
    "اسبوع": ["أسبوع", "الاسبوع", "الأسبوع"],
    "اسف": ["آسف", "آسفه", "اسفه", "بعتذر", "بعتزر", "بتاسف", "بتأسف"],
    "اسم": ["الاسم", "المسمى", "المسمي", "اسمي", "أسم", "الأسم","اسمك"],
    "الا": ["ما عدا", "إلا"],
    "الاتنين": ["الأتنين"],
    "الاحد": ["الأحد", "الحد"],
    "الاربعاء": ["الأربعاء", "الاربع", "الأربع"],
    "البقاء لله": ["الله يرحمه", "ربنا يرحمه"],
    "الثلاثاء": ["التلات"],
    "الجمعه": ["الجمعة"],
    "العنوان": ["المكان", "عنوان", "مكان"],
    "الف سلامه": ["سلامتك", "شفاك الله"],
    "الف مبروك": ["مبروك", "تهانينا"],
    "امتى": ["متى", "إمتى"],
    "انا": ["أنا"],
    "اه": ["نعم", "أيوه"],
    "او": ["أو", "ولا"],
    "ايه": ["ما", "إيه", "شنو"],
    "حاضر": ["تمام", "ماشي", "من عنيا", "من عنيه"],
    "حزين": ["زعلان", "كئيب", "زعلانه", "زعلانة", "كئيبه", "كئيبة", "مكتأب", "مكتأبه", "حزينه", "حزينة"],
    "ربع ساعه": ["15 دقيقة", "15 دقيقه", "ربع ساعة", "ربع"],
    "سنه": ["عام", "سنة", "السنه", "السنة"],
    "شاي": ["كوب شاي", "شاي سخن"],
    "شتاء": ["الشتا", "الشتاء", "شتا"],
    "شهر": ["شهر كامل", "مدة شهر", "الشهر"],
    "صباح": ["الصبح", "صبح", "نهار"],
    "صلاه": ["الصلاة", "صلاة", "صلات"],
    "صيف": ["الصيف"],
    "ظهر": ["الظهر", "منتصف النهار"],
    "عامل": ["بتعمل"],
    "عشاء": ["العشاء", "عشا", "العشا"],
    "عصر": ["العصر"],
    "عفوا": ["العفو", "ولا يهمك"],
    "فجر": ["الفجر"],
    "فين": ["أين"],
    "قهوه": ["قهوة", "كوب قهوة"],
    "كرم": ["كرم الضيافة", "كرم الضيافه"],
    "لبن": ["حليب", "لبن"],
    "مساء": ["المساء", "ليل"],
    "مسا": ["مسا الخير", "مساء الخير"],
    "متى": ["امتى", "متى"],
    "نهار": ["الصبح", "النهار"],
    "وقت": ["الوقت"],
    "ولد": ["الولد", "صبي"],
    "لا":["مش"],
    "و": ["و"],
    "الخميس":["الخميس"]
}

all_words = set()
for k, vals in dictionary.items():
    all_words.add(k)
    all_words.update(vals)

spell = SpellChecker(language=None)
spell.word_frequency.load_words(all_words)

def correct_word(word):
    return spell.correction(word)

def split_text(text):
    return text.split()

def find_best_match(word, dictionary):
    for key, synonyms in dictionary.items():
        if word == key or word in synonyms:
            return key
    all_keys_and_syns = list(dictionary.keys()) + [syn for syns in dictionary.values() for syn in syns]
    matches = get_close_matches(word, all_keys_and_syns, n=1, cutoff=0.7)
    return matches[0] if matches else word

def process_text(text):
    words = split_text(text)
    corrected_words = [correct_word(w) for w in words]
    return [find_best_match(w, dictionary) for w in corrected_words]

base_path = "static/gif"
english_gif_path = "gif_ASL"  # Path to English GIF directory

# English dictionary for text-to-GIF conversion
english_dictionary = {
    "hello": ["hi", "hey", "greetings", "good morning", "good afternoon", "good evening"],
    "thank": ["thanks", "thank you", "appreciate", "grateful"],
    "you": ["u", "yourself"],
    "please": ["pls", "kindly"],
    "yes": ["yeah", "yep", "sure", "ok", "okay", "correct", "right"],
    "no": ["nope", "nah", "negative", "wrong"],
    "good": ["great", "excellent", "nice", "wonderful", "amazing", "awesome"],
    "bad": ["terrible", "awful", "horrible", "poor"],
    "help": ["assist", "support", "aid"],
    "sorry": ["apologies", "excuse me", "pardon"],
    "welcome": ["greetings"],
    "goodbye": ["bye", "farewell", "see you", "later"],
    "morning": ["am", "dawn"],
    "night": ["evening", "pm"],
    "eat": ["eating", "food", "meal"],
    "drink": ["drinking", "beverage"],
    "water": ["h2o"],
    "love": ["adore", "like very much"],
    "like": ["enjoy", "prefer"],
    "want": ["need", "desire", "wish"],
    "go": ["going", "leave", "depart"],
    "come": ["coming", "arrive"],
    "stop": ["halt", "pause", "wait"],
    "time": ["clock", "hour", "minute"],
    "money": ["cash", "dollar", "payment"],
    "work": ["job", "employment", "career"],
    "home": ["house", "residence"],
    "family": ["relatives", "parents", "siblings"],
    "friend": ["buddy", "pal", "companion"],
    "happy": ["joy", "cheerful", "glad", "pleased"],
    "sad": ["unhappy", "depressed", "down"],
    "angry": ["mad", "furious", "upset"],
    "beautiful": ["pretty", "gorgeous", "lovely"],
    "big": ["large", "huge", "enormous"],
    "small": ["little", "tiny", "mini"],
    "hot": ["warm", "heated"],
    "cold": ["cool", "freezing", "chilly"],
    "a": ["an", "one"],
    "about": ["regarding", "concerning"],
    "able": ["capable", "can"],
    "accept": ["agree", "approve"],
    "across": ["over", "through"],
    "act": ["action", "perform"],
    "add": ["plus", "include"],
    "after": ["following", "later"],
    "again": ["once more", "repeat"],
    "against": ["opposite", "versus"],
    "all": ["everything", "entire"],
    "allow": ["permit", "let"],
    "almost": ["nearly", "about"],
    "alone": ["solo", "single"],
    "also": ["too", "as well"],
    "always": ["forever", "constantly"],
    "and": ["plus", "&"],
    "answer": ["reply", "response"],
    "any": ["some", "either"],
    "appear": ["show", "seem"],
    "ask": ["question", "inquire"],
    "away": ["gone", "distant"],
    "what": ["which", "wat"],
    "where": ["were"],
    "when": ["wen"],
    "who": ["hu"],
    "why": ["y"],
    "how": ["hw"],
    "name": ["names", "called"],
    "my": ["mine"],
    "your": ["yours", "ur"],
    "his": ["he"],
    "her": ["she"],
    "our": ["ours"],
    "their": ["theirs"]
}

def get_gif_paths_for_word(word, language='arabic'):
    """
    Get GIF paths for a word in specified language
    language: 'arabic' or 'english'
    """
    if language == 'english':
        # Use gif_ASL directory for English GIFs
        word_folder = os.path.join(english_gif_path, word.lower())
        if not os.path.exists(word_folder):
            return []
        # Create proper Flask static URL paths
        gif_files = []
        for f in os.listdir(word_folder):
            if f.endswith('.gif'):
                # Create proper URL path: /gif_ASL/word/filename.gif
                static_path = f"/gif_ASL/{word.lower()}/{f}"
                gif_files.append(static_path)
        return sorted(gif_files)
    else:
        # Use static/gif for Arabic GIFs
        word_folder = os.path.join(base_path, word)
        if not os.path.exists(word_folder):
            return []
        gif_files = [f"/{os.path.join(word_folder, f).replace(os.sep, '/')}" for f in os.listdir(word_folder) if f.endswith('.gif')]
        return sorted(gif_files)

def process_english_text(text):
    """Process English text for GIF conversion"""
    words = text.lower().split()
    processed_words = []
    
    for word in words:
        # Remove punctuation
        clean_word = ''.join(char for char in word if char.isalnum())
        
        # Find best match in English dictionary
        best_match = find_best_english_match(clean_word, english_dictionary)
        processed_words.append(best_match)
    
    return processed_words

def find_best_english_match(word, dictionary):
    """Find best match for English word in dictionary"""
    # Direct match
    if word in dictionary:
        return word
    
    # Check synonyms
    for key, synonyms in dictionary.items():
        if word in synonyms:
            return key
    
    # Fuzzy matching
    from difflib import get_close_matches
    all_keys_and_syns = list(dictionary.keys()) + [syn for syns in dictionary.values() for syn in syns]
    matches = get_close_matches(word, all_keys_and_syns, n=1, cutoff=0.7)
    
    if matches:
        matched_word = matches[0]
        # If match is a synonym, return the key
        for key, synonyms in dictionary.items():
            if matched_word in synonyms:
                return key
        return matched_word
    
    return word  # Return original if no match found

# Sign language to text conversion setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    min_tracking_confidence=0.7,
    min_detection_confidence=0.7,
    max_num_hands=2,
    static_image_mode=True  # Match Word_real_time.ipynb
)
# Load LSTM model with error handling
try:
    modelLSTM = load_model("action3.h5")
    print("✅ LSTM model loaded successfully")
except Exception as e:
    print(f"⚠️ Failed to load LSTM model: {e}")
    modelLSTM = None



peer_connections = {}
client_sequences = {}
client_sentences = {}
client_last_update = {}
client_last_sent_translation = {}  # Track last sent translation to avoid duplicates
client_last_processed_time = {}  # Track last processing time per user for load balancing


# def video_processing(sid):
#     try:
#         client_sequences[sid] = []
#         client_sentences[sid] = []
#         for index in range(3):
#             cap = cv2.VideoCapture(index)
#             if cap.isOpened():
#                 print(f"Webcam opened successfully with index {index}")
#                 break
#         else:
#             print("Error: Could not open any webcam.")
#             socketio.emit('error', {'message': 'تعذر فتح الكاميرا. تحقق من اتصال الكاميرا أو جرب فهرسًا آخر.'}, namespace='/video', to=sid)
#             return

#         timeout_minutes = 0.5
#         last_update_time = datetime.datetime.now()

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 print("Error: Failed to capture frame.")
#                 break

#             frame = cv2.flip(frame, 1)
#             image, results = mediapipe_detection(frame, hands)

#             if results.multi_hand_landmarks:
#                 keypoints = extract_keypoints(results)
#                 if len(keypoints) == 84:
#                     client_sequences[sid].append(keypoints)
#                     if len(client_sequences[sid]) == 15:
#                         res = modelLSTM.predict(np.expand_dims(client_sequences[sid], axis=0))[0]
#                         EN = actions[np.argmax(res)]
#                         confidence = res[np.argmax(res)]
#                         print(f"Predicted: {reverb[EN]} with confidence {confidence} for sid {sid}")
#                         if confidence > 0.8:
#                             if not client_sentences[sid] or reverb[EN] != client_sentences[sid][-1][0]:
#                                 client_sentences[sid].append((reverb[EN], confidence, datetime.datetime.now()))
#                                 reshaped_sentence = [get_display(reshape(word[0])) for word in client_sentences[sid]]
#                                 socketio.emit('sign_language_translation', {
#                                     'sentence': [{'word': word[0], 'confidence': float(word[1])} for word in client_sentences[sid]],
#                                     'reshaped_sentence': ' '.join(reshaped_sentence[::-1]),  # Reverse for correct Arabic display
#                                     'sid': sid
#                                 }, namespace='/video', broadcast=True)
#                         client_sequences[sid] = []
#             else:
#                 client_sequences[sid] = []

#             current_time = datetime.datetime.now()
#             if client_sentences[sid]:
#                 last_update_time = client_sentences[sid][-1][2]
#                 time_elapsed_minutes = (current_time - last_update_time).total_seconds() / 60
#                 if time_elapsed_minutes > timeout_minutes:
#                     client_sentences[sid].clear()

#             time.sleep(0.033)

#     except Exception as e:
#         print(f"Error in video_processing: {str(e)}")
#         socketio.emit('error', {'message': f'خطأ في معالجة الفيديو: {str(e)}'}, namespace='/video', to=sid)
#     finally:
#         if 'cap' in locals():
#             cap.release()

@socketio.on('connect', namespace='/video')
def handle_connect():
    print(f'Client connected: {request.sid}')
    peer_connections[request.sid] = None
    room = session.get('friend', request.sid)
    join_room(room)
    print(f"Client {request.sid} joined room {room}")

@socketio.on('disconnect', namespace='/video')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    sid = request.sid
    
    # Clean up regular peer connections
    if sid in peer_connections:
        del peer_connections[sid]
    if sid in client_sequences:
        del client_sequences[sid]
    if sid in client_sentences:
        del client_sentences[sid]
    if sid in client_last_update:
        del client_last_update[sid]
    if sid in client_last_sent_translation:
        del client_last_sent_translation[sid]
    if sid in client_last_processed_time:
        del client_last_processed_time[sid]
    
    # Clean up test room participants
    test_room = session.get('test_room')
    if test_room and test_room in test_room_participants:
        if sid in test_room_participants[test_room]:
            user_info = test_room_participants[test_room][sid]
            print(f"Removing test user {user_info['user_uid']} from room {test_room}")
            del test_room_participants[test_room][sid]
            
            # Notify remaining participants
            emit('user_left_test_room', {
                'user_uid': user_info['user_uid'],
                'sid': sid,
                'participants_count': len(test_room_participants[test_room])
            }, room=test_room)
            
            # Clean up empty rooms
            if len(test_room_participants[test_room]) == 0:
                del test_room_participants[test_room]

@socketio.on('offer', namespace='/video')
def handle_offer(data):
    # Check if we're in test mode
    test_room = session.get('test_room')
    if test_room:
        print(f"Broadcasting offer in test room {test_room} from {request.sid}")
        emit('offer', {
            'offer': data['offer'],
            'sid': request.sid
        }, room=test_room, include_self=False)
    else:
        # Regular mode - route to specific SID
        emit('offer', {
            'offer': data['offer'],
            'sid': request.sid
        }, to=data['target_sid'])

@socketio.on('answer', namespace='/video')
def handle_answer(data):
    # Check if we're in test mode
    test_room = session.get('test_room')
    if test_room:
        print(f"Broadcasting answer in test room {test_room} from {request.sid}")
        emit('answer', {
            'answer': data['answer'],
            'sid': request.sid
        }, room=test_room, include_self=False)
    else:
        # Regular mode - route to specific SID
        emit('answer', {
            'answer': data['answer'],
            'sid': request.sid
        }, to=data['target_sid'])

@socketio.on('ice_candidate', namespace='/video')
def handle_ice_candidate(data):
    # Check if we're in test mode
    test_room = session.get('test_room')
    if test_room:
        print(f"Broadcasting ICE candidate in test room {test_room} from {request.sid}")
        emit('ice_candidate', {
            'candidate': data['candidate'],
            'sid': request.sid
        }, room=test_room, include_self=False)
    else:
        # Regular mode - route to specific SID
        emit('ice_candidate', {
            'candidate': data['candidate'],
            'sid': request.sid
        }, to=data['target_sid'])
rooms = {}

@socketio.on('join_room', namespace='/video')
def handle_join_room(data):
    room = data['room']
    sid = data['sid']
    join_room(room)
    if room not in rooms:
        rooms[room] = []
    if sid not in rooms[room]:
        rooms[room].append(sid)
    
    is_initiator = len(rooms[room]) > 1
    emit('initiator_set', {'isInitiator': is_initiator}, room=sid)
    
    # إشعار للمستخدم الآخر بعد ما الغرفة تكتمل
    if len(rooms[room]) == 2:
        for user_sid in rooms[room]:
            if user_sid != sid:
                emit('user_joined', {'sid': sid}, room=user_sid)
            emit('user_joined', {'sid': user_sid}, room=sid)

# @socketio.on('chat_message', namespace='/video')
# def handle_chat_message(data):
#     sid = request.sid
#     room = session.get('friend', sid)
#     emit('chat_response', {'message': data['message']}, namespace='/video', room=room)
@socketio.on('chat_message', namespace='/video')
def handle_chat_message(data):
    print('Received chat message:', data)
    message = data['message']
    print(f'Original message: "{message}"')
    
    processed_words = process_text(message)
    print(f'Processed words: {processed_words}')
    
    gif_paths = []
    for word in processed_words:
        word_gifs = get_gif_paths_for_word(word)
        print(f'Word "{word}" -> {len(word_gifs)} GIFs: {word_gifs}')
        gif_paths.extend(word_gifs)
    
    print(f'Total GIF paths found: {len(gif_paths)} -> {gif_paths}')
    
    # Determine target room - test room or regular room
    test_room = session.get('test_room')
    regular_room = session.get('friend', request.sid)
    target_room = test_room if test_room else regular_room
    
    print(f'Sending chat message with {len(gif_paths)} GIFs to room: {target_room}')
    
    response_data = {
        'message': ' '.join(processed_words), 
        'gifs': gif_paths,
        'sender_sid': request.sid
    }
    print(f'Response data: {response_data}')
    
    if target_room:
        emit('chat_response', response_data, room=target_room, namespace='/video')
    else:
        # Fallback to broadcast if no specific room
        emit('chat_response', response_data, broadcast=True, namespace='/video')
    
@socketio.on('video_frame', namespace='/video')
def handle_video_frame(data):
    sid = request.sid
    try:
        # Load balancing: limit processing rate per user when multiple users are active
        current_time = datetime.datetime.now()
        active_users = len(client_sequences)
        
        # Adaptive frame throttling based on user count
        if active_users > 1:
            min_interval = 0.4  # 400ms between frames when multiple users (2.5 FPS per user)
            if sid not in client_last_processed_time or sid == list(client_sequences.keys())[0]:
                print(f"🚥 Multi-user mode: {active_users} users, throttling to {min_interval}s per user")
        else:
            min_interval = 0.2  # 200ms when single user (5 FPS)
        
        # Check if enough time has passed since last processing for this user
        if sid in client_last_processed_time:
            time_since_last = (current_time - client_last_processed_time[sid]).total_seconds()
            if time_since_last < min_interval:
                return  # Skip this frame - too soon for this user
        
        client_last_processed_time[sid] = current_time
        
        # Initialize client data structures
        if sid not in client_sequences:
            client_sequences[sid] = []
        if sid not in client_sentences:
            client_sentences[sid] = []
        if sid not in client_last_update:
            client_last_update[sid] = datetime.datetime.now()

        image_data = base64.b64decode(data['frame'].split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            print(f"Error: Could not decode frame for sid {sid}")
            emit('error', {'message': 'تعذر فك تشفير الإطار.'}, namespace='/video', to=sid)
            return

        # Optimize frame processing for multiple users
        if active_users > 1 and frame.shape[0] > 480:
            # Resize frame to reduce processing load when multiple users
            height, width = frame.shape[:2]
            new_height = 480
            new_width = int(width * (new_height / height))
            frame = cv2.resize(frame, (new_width, new_height))

        # Store previous sentence length to detect clearing
        previous_sentence_length = len(client_sentences[sid]) if sid in client_sentences else 0
        
        # Process frame using realtime_sign.py with MediaPipe error handling
        try:
            _, client_sequences[sid], client_sentences[sid], client_last_update[sid], reshaped_sentence = process_frame(
                frame, client_sequences[sid], client_sentences[sid], client_last_update[sid]
            )
        except Exception as e:
            # Handle MediaPipe timestamp errors gracefully
            error_msg = str(e)
            if "timestamp mismatch" in error_msg or "Graph has errors" in error_msg:
                print(f"⚠️ MediaPipe timestamp error (skipping frame): {error_msg[:100]}...")
                return  # Skip this problematic frame and continue
            else:
                # Re-raise other unexpected errors
                raise e
        
        # If sentence was cleared (timeout), reset last sent translation
        if previous_sentence_length > 0 and len(client_sentences[sid]) == 0:
            if sid in client_last_sent_translation:
                print(f"🔄 Backend - Sentence cleared for {sid}, resetting last sent translation")
                del client_last_sent_translation[sid]

        # Send translation to clients - check if in test room or regular room
        if client_sentences[sid]:
            # Create a translation key to check for duplicates
            current_translation = reshaped_sentence.strip()
            
            # Only send if the translation is new/different from last sent
            if sid not in client_last_sent_translation or client_last_sent_translation[sid] != current_translation:
                test_room = session.get('test_room')
                regular_room = session.get('friend', sid)
                target_room = test_room if test_room else regular_room
                
                # Debug the Arabic text
                original_words = [word[0] for word in client_sentences[sid]]
                print(f"✅ Backend - NEW translation: '{current_translation}' (Users: {active_users})")
                print(f"✅ Backend - Arabic words: {original_words}")
                print(f"Sending sign language translation from sid {sid} to room {target_room}")
                
                # Get user information for chat-style display
                user_info = session.get('user', {})
                username = user_info.get('username', 'مستخدم غير معروف')
                
                emit('sign_language_translation', {
                    'sentence': [{'word': word[0], 'confidence': float(word[1])} for word in client_sentences[sid]],
                    'reshaped_sentence': current_translation,
                    'sid': sid,
                    'username': username,
                    'timestamp': datetime.datetime.now().isoformat()
                }, namespace='/video', room=target_room)
                
                # Update the last sent translation
                client_last_sent_translation[sid] = current_translation
            else:
                print(f"🔄 Backend - Skipping duplicate translation: '{current_translation}'")

    except Exception as e:
        print(f"Error processing frame for sid {sid}: {str(e)}")
        emit('error', {'message': f'خطأ: {str(e)}'}, namespace='/video', to=sid)

class EnglishHandler:
    def __init__(self):
        try:
            self.models = {
                'SVM': joblib.load('svm_asl_model.joblib')
            }
            print("English model loaded successfully.")
        except FileNotFoundError:
            print("⚠️ Error: Model file 'svm_asl_model.joblib' not found. Running in fallback mode.")
            self.models = {}
        except Exception as e:
            print(f"⚠️ Error loading English model: {e}. Running in fallback mode.")
            self.models = {}

    def preprocess_and_predict(self, image_path, model):
        try:
            if not self.models or 'SVM' not in self.models:
                print("⚠️ English model not available, returning fallback prediction")
                return "Hello"  # Fallback prediction
            image_data = io.imread(image_path)
            image_resized = transform.resize(image_data, (64, 64))
            image_gray = color.rgb2gray(image_resized)
            hog_features = hog(image_gray, pixels_per_cell=(8, 8), cells_per_block=(2, 2), feature_vector=True).reshape(1, -1)
            return self.models['SVM'].predict(hog_features)[0]
        except Exception as e:
            print(f"Error in English preprocessing or prediction: {e}")
            return "Hello"  # Fallback prediction

class ArabicHandler:
    def __init__(self):
        try:
            self.arabic_class_mapping = {
                0: "ع", 1: "ا ل", 2: "ا", 3: "ب", 4: "ض", 5: "د", 6: "ف", 7: "غ", 8: "ح", 9: "ه",
                10: "ج", 11: "ك", 12: "خ", 13: "لا", 14: "ل", 15: "م", 16: "ن", 17: "ق", 18: "ر", 19: "ص",
                20: "س", 21: "ش", 22: "ط", 23: "ت", 24: "ة", 25: "ذ", 26: "ث", 27: "و", 28: "ي", 29: "ظ", 30: "ز"
            }
            self.models = {
                'MobileNet_Arabic': tf.keras.models.load_model('mobilenet_arabic_sign_model.h5')
            }
            print("Arabic MobileNet model loaded successfully.")
        except FileNotFoundError:
            print("⚠️ Error: Arabic model file not found. Running in fallback mode.")
            self.models = {}
        except Exception as e:
            print(f"⚠️ Error loading Arabic model: {e}. Running in fallback mode.")
            self.models = {}

    def preprocess_and_predict(self, image_path, model):
        try:
            if not self.models or 'MobileNet_Arabic' not in self.models:
                print("⚠️ Arabic model not available, returning fallback prediction")
                return "مرحبا"  # Fallback prediction
            img = image.load_img(image_path, target_size=(64, 64))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            predictions = self.models['MobileNet_Arabic'].predict(img_array)
            predicted_index = np.argmax(predictions)
            return self.arabic_class_mapping[predicted_index]
        except Exception as e:
            print(f"Error in Arabic preprocessing or prediction: {e}")
            return "مرحبا"  # Fallback prediction

english_handler = EnglishHandler()
arabic_handler = ArabicHandler()

@app.route('/')
def index():
    return redirect(url_for('ARhome'))

@app.route('/ARhome')
def ARhome():
    user = session.get('user')
    print("🧪 session['user']:", user)
    return render_template("home.html", user=user)

@app.route('/ENhome')
def ENhome():
    user = session.get('user')
    print("🧪 session['user']:", user)
    return render_template("EN home.html", user=user)

@app.route('/ENtest')
def ENtest():
    user = session.get('user')
    print("🧪 session['user']:", user)
    return render_template("test_video_clean_en.html", user=user)

@app.route('/ENpic', methods=['GET', 'POST'])
def index_eng():
    if not session.get('user'):
        return redirect(url_for('ENlogin'))
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            return "No file selected"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        model_name = request.form.get('model')
        model = english_handler.models.get(model_name)
        if not model:
            return "Invalid model"
        label = english_handler.preprocess_and_predict(filepath, model)
        return render_template('EN result pic.html', label=label, model=model_name)
    return render_template('EN pic.html', models=english_handler.models.keys(), user=session.get('user'))

@app.route('/ARpic', methods=['GET', 'POST'])
def index_ar():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            return "لا يوجد ملف مرفوع"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        model_name = request.form.get('model')
        model = arabic_handler.models.get(model_name)
        if not model:
            return "النموذج غير صالح"
        label = arabic_handler.preprocess_and_predict(filepath, model)
        return render_template('AR result pic.html', label=label, model=model_name)
    return render_template('AR pic.html', models=arabic_handler.models.keys(), user=session.get('user'))

@app.route('/ARlogin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['username']
            password = request.form['password']
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            response = requests.post(url, json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            })
            data = response.json()
            if 'error' in data:
                return render_template('AR login.html', error=data['error']['message'])
            uid = data['localId']
            user_doc = db.collection('users').document(uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                username = user_data.get('username', 'مستخدم')
            else:
                username = 'مستخدم'
            session['user'] = {
                'uid': uid,
                'email': data['email'],
                'username': username
            }
            print("✅ session['user']:", session['user'])
            return redirect(url_for('ARhome'))
        except Exception as e:
            return render_template('AR login.html', error=f"خطأ في تسجيل الدخول: {str(e)}")
    return render_template('AR login.html')

@app.route('/ARsignup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')
            if password != confirm:
                return render_template('AR signup.html', error="كلمات المرور غير متطابقة")
            if not username or not email or not password:
                return render_template('AR signup.html', error="الرجاء تعبئة جميع الحقول")
            user = auth.create_user(
                email=email,
                password=password,
                display_name=username
            )
            db.collection('users').document(user.uid).set({
                'username': username,
                'email': email,
                'friends': []
            })
            session['user'] = {
                'uid': user.uid,
                'email': email,
                'username': username
            }
            return redirect(url_for('ARhome'))
        except auth.EmailAlreadyExistsError:
            return render_template('AR signup.html', error="البريد الإلكتروني مسجل بالفعل")
        except Exception as e:
            return render_template('AR signup.html', error=f"حدث خطأ: {str(e)}")
    return render_template('AR signup.html')

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
        response = requests.post(url, json={"requestType": "PASSWORD_RESET", "email": email})
        if response.status_code == 200:
            return jsonify({"message": "تم إرسال رابط إعادة تعيين كلمة المرور"})
        return jsonify({"error": "خطأ أثناء الإرسال"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/ENlogin', methods=['GET', 'POST'])
def ENlogin():
    if request.method == 'POST':
        try:
            email = request.form['username']
            password = request.form['password']
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            response = requests.post(url, json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            })
            data = response.json()
            if 'error' in data:
                return render_template('EN login.html', error=data['error']['message'])
            uid = data['localId']
            user_doc = db.collection('users').document(uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                username = user_data.get('username', 'user')
            else:
                username = 'user'
            session['user'] = {
                'uid': uid,
                'email': data['email'],
                'username': username
            }
            print("✅ session['user']:", session['user'])
            return redirect(url_for('ENhome'))
        except Exception as e:
            return render_template('EN login.html', error=f"Login error: {str(e)}")
    return render_template('EN login.html')

@app.route('/ENsignup', methods=['GET', 'POST'])
def ENsignup():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')
            if password != confirm:
                return render_template('EN signup.html', error="Passwords do not match")
            if not username or not email or not password:
                return render_template('EN signup.html', error="Please fill in all fields")
            user = auth.create_user(
                email=email,
                password=password,
                display_name=username
            )
            db.collection('users').document(user.uid).set({
                'username': username,
                'email': email,
                'friends': []
            })
            session['user'] = {
                'uid': user.uid,
                'email': email,
                'username': username
            }
            return redirect(url_for('ENhome'))
        except auth.EmailAlreadyExistsError:
            return render_template('EN signup.html', error="Email already registered")
        except Exception as e:
            return render_template('EN signup.html', error=f"Error: {str(e)}")
    return render_template('EN signup.html')

@app.route('/ENforgot-password', methods=['POST'])
def ENforgot_password():
    email = request.form.get('email')
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
        response = requests.post(url, json={"requestType": "PASSWORD_RESET", "email": email})
        if response.status_code == 200:
            return jsonify({"message": "Password reset link has been sent"})
        return jsonify({"error": "Error during submission"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/chats')
def chats():
    if 'user' not in session or 'uid' not in session['user']:
        return redirect(url_for('ARlogin'))
    try:
        user_ref = db.collection('users').document(session['user']['uid'])
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            friends = user_data.get('friends', [])
            print(f"Fetched friends for {session['user']['username']}: {friends}")
        else:
            friends = []
        messages = {}
        for friend in friends:
            messages_ref = db.collection('messages') \
                .where(filter=firestore.FieldFilter('from_username', 'in', [session['user']['username'], friend])) \
                .where(filter=firestore.FieldFilter('to', 'in', [session['user']['username'], friend])) \
                .get()
            messages[friend] = [{
                'sender': msg.get('from_username'),
                'text': msg.get('message'),
                'isCurrentUser': msg.get('from_username') == session['user']['username']
            } for msg in messages_ref]
            print(f"Found {len(messages[friend])} messages with {friend}")
        return render_template('chats.html', 
                             user=session.get('user'), 
                             friends=friends,
                             messages=messages)
    except Exception as e:
        print(f"Error accessing Firestore: {e}")
        return render_template('chats.html', 
                             user=session.get('user'), 
                             friends=[],
                             messages={})

@app.route('/add-friend', methods=['POST'])
def add_friend():
    if 'user' not in session or 'uid' not in session['user']:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    data = request.get_json()
    friend_username = data.get('friendUsername')
    if not friend_username:
        return jsonify({'error': 'اسم المستخدم للصديق مطلوب'}), 400
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', friend_username).limit(1).get()
        if not query or len(query) == 0:
            return jsonify({'error': 'لا يوجد مستخدم مسجل بهذا الاسم'}), 404
        friend_doc = query[0]
        if not friend_doc.exists:
            return jsonify({'error': 'المستند غير موجود'}), 404
        if friend_doc.id == session['user']['uid']:
            return jsonify({'error': 'لا يمكنك إضافة نفسك كصديق'}), 400
        friend_data = friend_doc.to_dict()
        friend_uid = friend_doc.id
        friend_username = friend_data.get('username')
        current_user_ref = db.collection('users').document(session['user']['uid'])
        current_user_ref.update({
            'friends': firestore.ArrayUnion([friend_username])
        })
        friend_user_ref = db.collection('users').document(friend_uid)
        current_username = session['user'].get('username')
        if current_username:
            friend_user_ref.update({
                'friends': firestore.ArrayUnion([current_username])
            })
        return jsonify({
            'message': f'تم إضافة {friend_username} كصديق بنجاح',
            'friendUsername': friend_username
        })
    except Exception as e:
        print(f"Error adding friend: {str(e)}")
        return jsonify({'error': 'حدث خطأ أثناء إضافة الصديق'}), 500

@app.route('/remove-friend', methods=['POST'])
def remove_friend():
    if 'user' not in session or 'uid' not in session['user']:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    data = request.get_json()
    friend_username = data.get('friendUsername')
    if not friend_username:
        return jsonify({'error': 'اسم المستخدم للصديق مطلوب'}), 400
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', friend_username).limit(1).get()
        if not query or len(query) == 0:
            return jsonify({'error': 'لا يوجد مستخدم مسجل بهذا الاسم'}), 404
        friend_doc = query[0]
        if not friend_doc.exists:
            return jsonify({'error': 'المستند غير موجود'}), 404
        friend_uid = friend_doc.id
        current_user_ref = db.collection('users').document(session['user']['uid'])
        current_user_ref.update({
            'friends': firestore.ArrayRemove([friend_username])
        })
        current_username = session['user'].get('username')
        if current_username:
            friend_user_ref = db.collection('users').document(friend_uid)
            friend_user_ref.update({
                'friends': firestore.ArrayRemove([current_username])
            })
        return jsonify({
            'message': f'تم إزالة {friend_username} من قائمة الأصدقاء',
            'success': True
        })
    except Exception as e:
        print(f"Error removing friend: {str(e)}")
        return jsonify({'error': 'حدث خطأ أثناء إزالة الصديق'}), 500

@app.route('/send-message', methods=['POST'])
def send_message():
    if not session.get('user'):
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
    data = request.get_json()
    to_friend = data.get('to')
    message_text = data.get('message')
    if not to_friend or not message_text:
        return jsonify({'error': 'معلومات غير كاملة'}), 400
    try:
        messages_ref = db.collection('messages')
        messages_ref.add({
            'from': session['user']['email'],
            'from_username': session['user']['username'],
            'to': to_friend,
            'message': message_text,
            'isCurrentUser': True
        })
        return jsonify({
            'message': 'تم إرسال الرسالة',
            'success': True
        })
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return jsonify({'error': 'حدث خطأ أثناء إرسال الرسالة'}), 500

@app.route('/video')
def video():
    friend = request.args.get('friend')
    return render_template('video.html', user={'username': session.get('username')}, friend=friend)

@app.route('/ENchats')
def ENchats():
    if 'user' not in session or 'uid' not in session['user']:
        return redirect(url_for('ENlogin'))
    try:
        user_ref = db.collection('users').document(session['user']['uid'])
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            friends = user_data.get('friends', [])
            print(f"Fetched friends for {session['user']['username']}: {friends}")
        else:
            friends = []
        messages = {}
        for friend in friends:
            messages_ref = db.collection('messages') \
                .where(filter=firestore.FieldFilter('from_username', 'in', [session['user']['username'], friend])) \
                .where(filter=firestore.FieldFilter('to', 'in', [session['user']['username'], friend])) \
                .get()
            messages[friend] = [{
                'sender': msg.get('from_username'),
                'text': msg.get('message'),
                'isCurrentUser': msg.get('from_username') == session['user']['username']
            } for msg in messages_ref]
            print(f"Found {len(messages[friend])} messages with {friend}")
        return render_template('EN chats.html', 
                             user=session.get('user'), 
                             friends=friends,
                             messages=messages)
    except Exception as e:
        print(f"Error accessing Firestore: {e}")
        return render_template('EN chats.html', 
                             user=session.get('user'), 
                             friends=[],
                             messages={})

@app.route('/ENadd-friend', methods=['POST'])
def ENadd_friend():
    if 'user' not in session or 'uid' not in session['user']:
        return jsonify({'error': 'You must log in first'}), 401
    data = request.get_json()
    friend_username = data.get('friendUsername')
    if not friend_username:
        return jsonify({'error': 'Friend username is required'}), 400
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', friend_username).limit(1).get()
        if not query or len(query) == 0:
            return jsonify({'error': 'No user registered with this name'}), 404
        friend_doc = query[0]
        if not friend_doc.exists:
            return jsonify({'error': 'Document not found'}), 404
        if friend_doc.id == session['user']['uid']:
            return jsonify({'error': 'You cannot add yourself as a friend'}), 400
        friend_data = friend_doc.to_dict()
        friend_uid = friend_doc.id
        friend_username = friend_data.get('username')
        current_user_ref = db.collection('users').document(session['user']['uid'])
        current_user_ref.update({
            'friends': firestore.ArrayUnion([friend_username])
        })
        friend_user_ref = db.collection('users').document(friend_uid)
        current_username = session['user'].get('username')
        if current_username:
            friend_user_ref.update({
                'friends': firestore.ArrayUnion([current_username])
            })
        return jsonify({
            'message': f'Successfully added {friend_username} as a friend',
            'friendUsername': friend_username
        })
    except Exception as e:
        print(f"Error adding friend: {str(e)}")
        return jsonify({'error': 'An error occurred while adding the friend'}), 500

@app.route('/ENremove-friend', methods=['POST'])
def ENremove_friend():
    if 'user' not in session or 'uid' not in session['user']:
        return jsonify({'error': 'You must login first'}), 401
    data = request.get_json()
    friend_username = data.get('friendUsername')
    if not friend_username:
        return jsonify({'error': 'Friend username is required'}), 400
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', friend_username).limit(1).get()
        if not query or len(query) == 0:
            return jsonify({'error': 'No user registered with this name'}), 404
        friend_doc = query[0]
        if not friend_doc.exists:
            return jsonify({'error': 'Document not found'}), 404
        friend_uid = friend_doc.id
        current_user_ref = db.collection('users').document(session['user']['uid'])
        current_user_ref.update({
            'friends': firestore.ArrayRemove([friend_username])
        })
        current_username = session['user'].get('username')
        if current_username:
            friend_user_ref = db.collection('users').document(friend_uid)
            friend_user_ref.update({
                'friends': firestore.ArrayRemove([current_username])
            })
        return jsonify({
            'message': f'Successfully removed {friend_username} from the friends list',
            'success': True
        })
    except Exception as e:
        print(f"Error removing friend: {str(e)}")
        return jsonify({'error': 'An error occurred while removing the friend'}), 500

@app.route('/ENsend-message', methods=['POST'])
def ENsend_message():
    if not session.get('user'):
        return jsonify({'error': 'You must log in first'}), 401
    data = request.get_json()
    to_friend = data.get('to')
    message_text = data.get('message')
    if not to_friend or not message_text:
        return jsonify({'error': 'Incomplete information'}), 400
    try:
        messages_ref = db.collection('messages')
        messages_ref.add({
            'from': session['user']['email'],
            'from_username': session['user']['username'],
            'to': to_friend,
            'message': message_text,
            'isCurrentUser': True
        })
        return jsonify({
            'message': 'Message sent successfully',
            'success': True
        })
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return jsonify({'error': 'An error occurred while sending the message'}), 500

@app.route('/ENvideo')
def ENvideo():
    friend = request.args.get('friend')
    return render_template('EN video.html', user={'username': session.get('username')}, friend=friend)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/ENlogout')
def ENlogout():
    session.clear()
    return redirect(url_for('ENlogin'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if not session.get('user'):
        return redirect(url_for('ARlogin'))
    if request.method == 'POST':
        rating = request.form.get('rating')
        opinion = request.form.get('opinion')
        source = request.form.get('source')
        other_source = request.form.get('otherSource') if source == 'other' else None
        suggestions = request.form.get('suggestions')
        feedback_data = {
            'user_id': session['user']['uid'],
            'username': session['user']['username'],
            'rating': int(rating),
            'opinion': opinion,
            'source': other_source if source == 'other' else source,
            'suggestions': suggestions,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        db.collection('feedback').add(feedback_data)
        flash('تم إرسال تقييمك بنجاح!', 'success')
        return redirect(url_for('feedback'))
    return render_template('feedback.html', user=session.get('user'))

@app.route('/ENfeedback', methods=['GET', 'POST'])
def ENfeedback():
    if not session.get('user'):
        return redirect(url_for('ENlogin'))
    if request.method == 'POST':
        rating = request.form.get('rating')
        opinion = request.form.get('opinion')
        source = request.form.get('source')
        other_source = request.form.get('otherSource') if source == 'other' else None
        suggestions = request.form.get('suggestions')
        feedback_data = {
            'user_id': session['user']['uid'],
            'username': session['user']['username'],
            'rating': int(rating),
            'opinion': opinion,
            'source': other_source if source == 'other' else source,
            'suggestions': suggestions,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        db.collection('ENfeedback').add(feedback_data)
        flash('Your feedback sent successifly!', 'success')
        return redirect(url_for('ENfeedback'))
    return render_template('EN feedback.html', user=session.get('user'))

@app.route('/ARabout')
def about():
    return render_template('AR about.html', user=session.get('user'))

@app.route('/ENabout')
def ENabout():
    return render_template('EN about.html', user=session.get('user'))

@app.route('/ARprivacy')
def privacy():
    return render_template('AR privacy.html', user=session.get('user'))

@app.route('/ENprivacy')
def ENprivacy():
    return render_template('EN privacy.html', user=session.get('user'))

# Testing route for 2 specific users
TEST_USER_1_UID = "0rxQowitqnhZmO9Mq7jWieA0q4J3"  # Replace with actual UID from your database
TEST_USER_2_UID = "xB4pfR4CI4fap7WGIqRYGKuMLQk2"  # Replace with actual UID from your database
TEST_ROOM = "test_room_fixed"

@app.route('/test-video')
def test_video():
    if not session.get('user'):
        return redirect('/ARlogin')
    
    user_uid = session['user']['uid']
    
    # Only allow specific test users
    if user_uid not in [TEST_USER_1_UID, TEST_USER_2_UID]:
        return "Access denied. This is a testing route for specific users only.", 403
    
    # Determine the other user
    other_user_uid = TEST_USER_2_UID if user_uid == TEST_USER_1_UID else TEST_USER_1_UID
    
    return render_template('test_video_clean.html', 
                         user=session.get('user'), 
                         other_user_uid=other_user_uid,
                         test_room=TEST_ROOM,
                         is_initiator=(user_uid == TEST_USER_1_UID))

@app.route('/ENtest-video')
def ENtest_video():
    if not session.get('user'):
        return redirect('/ENlogin')
    
    user_uid = session['user']['uid']
    
    # Only allow specific test users (same users as Arabic version)
    if user_uid not in [TEST_USER_1_UID, TEST_USER_2_UID]:
        return "Access denied. This is a testing route for specific users only.", 403
    
    # Determine the other user
    other_user_uid = TEST_USER_2_UID if user_uid == TEST_USER_1_UID else TEST_USER_1_UID
    
    return render_template('test_video_clean_en.html', 
                         user=session.get('user'), 
                         other_user_uid=other_user_uid,
                         test_room=TEST_ROOM + "_en",  # Separate English room
                         is_initiator=(user_uid == TEST_USER_1_UID))

# Add test room tracking
test_room_participants = {}

@socketio.on('join_test_room', namespace='/video')
def handle_join_test_room(data):
    user_uid = data.get('user_uid')
    test_room = data.get('test_room')
    
    # Validate test users
    if user_uid not in [TEST_USER_1_UID, TEST_USER_2_UID]:
        emit('error', {'message': 'Unauthorized test user'})
        return
    
    join_room(test_room)
    session['test_room'] = test_room
    session['test_user_uid'] = user_uid
    
    # Track participants in the test room
    if test_room not in test_room_participants:
        test_room_participants[test_room] = {}
    
    test_room_participants[test_room][request.sid] = {
        'user_uid': user_uid,
        'sid': request.sid
    }
    
    print(f"Test user {user_uid} (SID: {request.sid}) joined room {test_room}")
    print(f"Current participants in {test_room}: {len(test_room_participants[test_room])}")
    
    # Emit to everyone in the room about the new participant
    emit('user_joined_test_room', {
        'user_uid': user_uid,
        'sid': request.sid,
        'participants_count': len(test_room_participants[test_room])
    }, room=test_room)
    
    # When both test users are ready, start the connection
    if len(test_room_participants[test_room]) >= 2:
        print(f"Both test users ready in room {test_room}")
        emit('test_room_ready', {
            'room': test_room,
            'user_uid': user_uid,
            'can_initiate': user_uid == TEST_USER_1_UID,
            'all_participants': list(test_room_participants[test_room].values())
        }, room=test_room)
    else:
        emit('waiting_for_other_user', {
            'room': test_room,
            'user_uid': user_uid
        }, to=request.sid)

@app.route('/test-arabic')
def test_arabic():
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    
    # Test different Arabic processing approaches
    test_words = ['انا', 'احب', 'البرمجة']
    
    # Join normally
    normal_join = ' '.join(test_words)
    
    # Apply reshaping only
    reshaped_only = reshape(normal_join)
    
    # Apply full bidi processing
    full_bidi = get_display(reshaped_only)
    
    # Reverse the word order (maybe this is what we need?)
    reversed_words = test_words[::-1]
    reversed_join = ' '.join(reversed_words)
    reversed_reshaped = get_display(reshape(reversed_join))
    
    return f"""
    <div style="font-family: Arial; direction: rtl; text-align: right;">
        <h2>Arabic Text Processing Test</h2>
        <p><strong>Original words:</strong> {test_words}</p>
        <p><strong>Normal join:</strong> {normal_join}</p>
        <p><strong>Reshaped only:</strong> {reshaped_only}</p>
        <p><strong>Full bidi:</strong> {full_bidi}</p>
        <p><strong>Reversed words:</strong> {reversed_words}</p>
        <p><strong>Reversed join:</strong> {reversed_join}</p>
        <p><strong>Reversed + reshaped:</strong> {reversed_reshaped}</p>
        
        <h3>How they look in RTL context:</h3>
        <div style="border: 1px solid #ccc; padding: 10px; margin: 5px;">
            <strong>Normal:</strong> {normal_join}
        </div>
        <div style="border: 1px solid #ccc; padding: 10px; margin: 5px;">
            <strong>Reshaped:</strong> {reshaped_only}
        </div>
        <div style="border: 1px solid #ccc; padding: 10px; margin: 5px;">
            <strong>Full bidi:</strong> {full_bidi}
        </div>
        <div style="border: 1px solid #ccc; padding: 10px; margin: 5px;">
            <strong>Reversed + reshaped:</strong> {reversed_reshaped}
        </div>
    </div>
    """

@app.route('/test-gifs')
def test_gifs():
    test_words = ['شكرا', 'اه', 'لا', 'انا', 'هو']
    results = {}
    
    for word in test_words:
        processed_words = process_text(word)
        gif_paths = []
        for processed_word in processed_words:
            gif_paths.extend(get_gif_paths_for_word(processed_word))
        results[word] = {
            'processed': processed_words,
            'gif_paths': gif_paths,
            'gif_count': len(gif_paths)
        }
    
    return f"""
    <h2>GIF Processing Test</h2>
    <pre>{results}</pre>
    <br><br>
    <h3>Test some words:</h3>
    <ul>
        {''.join([f'<li><strong>{word}</strong>: {result["gif_count"]} GIFs found<br>Paths: {result["gif_paths"]}</li>' for word, result in results.items()])}
    </ul>
    """

@app.route('/setup-test-users')
def setup_test_users():
    if not session.get('user'):
        return redirect('/ARlogin')
    
    # Get current user info
    current_user = session['user']
    
    # Get all users for selection
    try:
        users_ref = db.collection('users').limit(10).get()
        all_users = []
        for user_doc in users_ref:
            user_data = user_doc.to_dict()
            all_users.append({
                'uid': user_doc.id,
                'username': user_data.get('username', 'N/A'),
                'email': user_data.get('email', 'N/A')
            })
    except Exception as e:
        all_users = []
        print(f"Error fetching users: {e}")
    
    return f"""
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>إعداد المستخدمين للاختبار</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; direction: rtl; }}
            .user-card {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .current {{ background: #e8f5e8; border: 2px solid #28a745; }}
            button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }}
            button:hover {{ background: #0056b3; }}
            .instructions {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>إعداد المستخدمين للاختبار</h1>
        
        <div class="instructions">
            <h3>تعليمات:</h3>
            <ol>
                <li>حدد معرفين من المستخدمين أدناه</li>
                <li>انسخ المعرفات (UID) وضعها في الملف app.py</li>
                <li>استبدل TEST_USER_1_UID و TEST_USER_2_UID بالمعرفات الفعلية</li>
                <li>اذهب إلى /test-video للاختبار</li>
            </ol>
        </div>
        
        <h2>المستخدم الحالي:</h2>
        <div class="user-card current">
            <strong>UID:</strong> {current_user['uid']}<br>
            <strong>اسم المستخدم:</strong> {current_user['username']}<br>
            <strong>البريد الإلكتروني:</strong> {current_user['email']}
        </div>
        
        <h2>جميع المستخدمين:</h2>
        {''.join([f'''
        <div class="user-card">
            <strong>UID:</strong> {user['uid']}<br>
            <strong>اسم المستخدم:</strong> {user['username']}<br>
            <strong>البريد الإلكتروني:</strong> {user['email']}<br>
            <button onclick="copyToClipboard('{user['uid']}')">نسخ المعرف</button>
        </div>
        ''' for user in all_users])}
        
        <div style="margin-top: 30px;">
            <h3>الخطوات التالية:</h3>
            <p>1. اختر مستخدمين من القائمة أعلاه</p>
            <p>2. انسخ معرفاتهم</p>
            <p>3. قم بتحديث المتغيرات في app.py:</p>
            <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
TEST_USER_1_UID = "معرف_المستخدم_الأول"
TEST_USER_2_UID = "معرف_المستخدم_الثاني"
            </pre>
            <p>4. أعد تشغيل الخادم</p>
            <p>5. اذهب إلى <a href="/test-video">/test-video</a> للاختبار</p>
        </div>
        
        <script>
            function copyToClipboard(text) {{
                navigator.clipboard.writeText(text).then(function() {{
                    alert('تم نسخ المعرف: ' + text);
                }});
            }}
        </script>
    </body>
    </html>
    """

# English Sign Language Video Generation Helper
def create_english_sign_video(text):
    """
    Generate sign language video from English text
    Based on the video generation logic from complete_communication_app.py
    """
    try:
        import os
        import time
        import tempfile
        from datetime import datetime
        
        # Create directory for English sign videos if it doesn't exist
        english_videos_dir = os.path.join('static', 'english_sign_videos')
        os.makedirs(english_videos_dir, exist_ok=True)
        
        print(f"📝 Processing English text: '{text}'")
        
        # Clean and process the input text
        cleaned_text = text.strip().lower()
        if not cleaned_text:
            return None
            
        # Split text into words for individual sign video lookup
        words = cleaned_text.split()
        print(f"📝 Processing {len(words)} words: {words}")
        
        # Try to use existing video generation if available
        try:
            # Attempt to import the video_utils module if it exists
            from video_utils import create_sentence_video
            print("📹 Using existing video_utils.create_sentence_video()")
            
            # Generate video using existing system
            video_path = create_sentence_video(text)
            
            if video_path and os.path.exists(video_path):
                # Move the generated video to our English videos directory
                timestamp = int(time.time())
                filename = f"english_sign_{timestamp}.mp4"
                destination = os.path.join(english_videos_dir, filename)
                
                # Copy the file to our directory
                import shutil
                shutil.copy2(video_path, destination)
                
                print(f"✅ Video generated and copied to: {destination}")
                return f"/static/english_sign_videos/{filename}"
            else:
                print("⚠️ video_utils returned invalid path, falling back to custom implementation")
                
        except ImportError:
            print("📹 video_utils not available, using custom English sign video generation")
        except Exception as e:
            print(f"⚠️ Error with video_utils: {str(e)}, falling back to custom implementation")
        
        # Custom English sign language video generation
        # This is where you would implement your actual ASL video generation
        
        # Step 1: Map English words to sign language videos
        # You would have a database/directory of ASL videos for common words
        asl_video_mapping = {
            'hello': 'asl_hello.mp4',
            'thank': 'asl_thank.mp4', 
            'you': 'asl_you.mp4',
            'please': 'asl_please.mp4',
            'yes': 'asl_yes.mp4',
            'no': 'asl_no.mp4',
            'good': 'asl_good.mp4',
            'bad': 'asl_bad.mp4',
            'help': 'asl_help.mp4',
            'sorry': 'asl_sorry.mp4',
            'welcome': 'asl_welcome.mp4',
            'goodbye': 'asl_goodbye.mp4',
            'bye': 'asl_goodbye.mp4',
            'morning': 'asl_morning.mp4',
            'night': 'asl_night.mp4',
            'eat': 'asl_eat.mp4',
            'drink': 'asl_drink.mp4',
            'water': 'asl_water.mp4',
            'food': 'asl_food.mp4',
            'love': 'asl_love.mp4',
            'like': 'asl_like.mp4',
            'want': 'asl_want.mp4',
            'need': 'asl_need.mp4',
            'go': 'asl_go.mp4',
            'come': 'asl_come.mp4',
            'stop': 'asl_stop.mp4',
            'wait': 'asl_wait.mp4',
            'time': 'asl_time.mp4',
            'money': 'asl_money.mp4',
            'work': 'asl_work.mp4',
            'home': 'asl_home.mp4',
            'family': 'asl_family.mp4',
            'friend': 'asl_friend.mp4',
            'happy': 'asl_happy.mp4',
            'sad': 'asl_sad.mp4',
            'angry': 'asl_angry.mp4',
            'beautiful': 'asl_beautiful.mp4',
            'ugly': 'asl_ugly.mp4',
            'big': 'asl_big.mp4',
            'small': 'asl_small.mp4',
            'hot': 'asl_hot.mp4',
            'cold': 'asl_cold.mp4'
        }
        
        # Directory where ASL video files are stored
        asl_videos_base_dir = os.path.join('static', 'asl_videos')
        
        # Step 2: Find available videos for the words
        available_videos = []
        missing_words = []
        
        for word in words:
            # Clean word (remove punctuation)
            clean_word = ''.join(char.lower() for char in word if char.isalnum())
            
            if clean_word in asl_video_mapping:
                video_filename = asl_video_mapping[clean_word]
                video_path = os.path.join(asl_videos_base_dir, video_filename)
                
                if os.path.exists(video_path):
                    available_videos.append(video_path)
                    print(f"✅ Found ASL video for '{clean_word}': {video_filename}")
                else:
                    print(f"⚠️ ASL video file missing: {video_path}")
                    missing_words.append(clean_word)
            else:
                print(f"⚠️ No ASL video mapping for word: '{clean_word}'")
                missing_words.append(clean_word)
        
        # Step 3: Generate video if we have at least some videos
        if available_videos:
            try:
                # Use moviepy or cv2 to concatenate videos
                import cv2
                
                timestamp = int(time.time())
                output_filename = f"english_sign_{timestamp}.mp4"
                output_path = os.path.join(english_videos_dir, output_filename)
                
                # Simple video concatenation using OpenCV
                # Note: This is a basic implementation. For production, consider using moviepy
                concatenate_videos_cv2(available_videos, output_path)
                
                print(f"✅ Generated English sign video: {output_path}")
                print(f"📊 Video stats: {len(available_videos)} clips, {len(missing_words)} missing words")
                
                if missing_words:
                    print(f"⚠️ Missing ASL videos for: {missing_words}")
                
                return f"/static/english_sign_videos/{output_filename}"
                
            except Exception as video_error:
                print(f"❌ Error concatenating videos: {str(video_error)}")
                # Fall back to creating a placeholder response
                return create_placeholder_video_response(text, english_videos_dir)
        else:
            print(f"❌ No ASL videos found for any words in: '{text}'")
            return create_placeholder_video_response(text, english_videos_dir)
            
    except Exception as e:
        print(f"❌ Error in create_english_sign_video: {str(e)}")
        return None

def concatenate_videos_cv2(video_paths, output_path):
    """
    Concatenate multiple video files using OpenCV
    This is a basic implementation - consider using moviepy for production
    """
    try:
        if not video_paths:
            print("❌ No video paths provided")
            return False
        
        print(f"🔗 Concatenating {len(video_paths)} videos to {output_path}")
        
        # Read the first video to get properties
        first_video = cv2.VideoCapture(video_paths[0])
        if not first_video.isOpened():
            print(f"❌ Could not open first video: {video_paths[0]}")
            return False
        
        # Get video properties
        fps = int(first_video.get(cv2.CAP_PROP_FPS))
        width = int(first_video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(first_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"📐 Video properties: {width}x{height} @ {fps}fps")
        
        # Define codec and create VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            print(f"❌ Could not create output video writer")
            first_video.release()
            return False
        
        first_video.release()
        
        # Process each video
        total_frames = 0
        for i, video_path in enumerate(video_paths):
            print(f"📹 Processing video {i+1}/{len(video_paths)}: {video_path}")
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"⚠️ Could not open video: {video_path}")
                continue
            
            video_frames = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize frame if dimensions don't match
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, (width, height))
                
                out.write(frame)
                video_frames += 1
                total_frames += 1
            
            cap.release()
            print(f"✅ Added {video_frames} frames from {video_path}")
        
        out.release()
        
        # Verify output file
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"✅ Successfully created concatenated video with {total_frames} total frames")
            return True
        else:
            print(f"❌ Output video file was not created properly")
            return False
        
    except Exception as e:
        print(f"❌ Error in video concatenation: {str(e)}")
        return False

def create_placeholder_video_response(text, videos_dir):
    """
    Create a placeholder response when actual video generation fails
    """
    try:
        timestamp = int(time.time())
        placeholder_filename = f"placeholder_{timestamp}.txt"
        placeholder_path = os.path.join(videos_dir, placeholder_filename)
        
        # Create a text file with the original text (as a placeholder)
        with open(placeholder_path, 'w', encoding='utf-8') as f:
            f.write(f"English Sign Language Video Placeholder\n")
            f.write(f"Original Text: {text}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Note: This is a placeholder. Actual video generation failed.\n")
        
        print(f"📝 Created placeholder file: {placeholder_path}")
        
        # Return a special placeholder path that the frontend can handle
        return f"/static/english_sign_videos/placeholder_{timestamp}.txt"
        
    except Exception as e:
        print(f"❌ Error creating placeholder: {str(e)}")
        return None

@socketio.on('english_text_to_sign_video', namespace='/video')
def handle_english_text_to_sign_video(data):
    """Handle English text to sign language video generation"""
    try:
        message = data.get('message', '').strip()
        if not message:
            emit('error', {'message': 'No message provided'}, namespace='/video')
            return
        
        print(f"📝 Processing English text for sign video: '{message}'")
        
        # Use GIF generation instead of video for now
        # Process text to find matching words
        processed_words = process_english_text(message)
        
        # Get GIF paths for each word
        gif_data = []
        found_gifs = 0
        
        for word in processed_words:
            gif_paths = get_gif_paths_for_word(word, language='english')
            if gif_paths:
                gif_data.append({
                    'word': word,
                    'gif_path': gif_paths[0],
                    'found': True
                })
                found_gifs += 1
            else:
                gif_data.append({
                    'word': word,
                    'gif_path': None,
                    'found': False
                })
        
        if found_gifs == 0:
            emit('error', {'message': 'No sign language content found for this text'}, namespace='/video')
            return
        
        # Determine target room - test room or regular room
        test_room = session.get('test_room')
        regular_room = session.get('friend', request.sid)
        target_room = test_room if test_room else regular_room
        
        # Create concatenated video from GIFs
        video_path = None
        if found_gifs > 0:
            try:
                video_path = create_english_gif_video(gif_data, message)
                print(f"✅ Created concatenated video: {video_path}")
            except Exception as video_error:
                print(f"⚠️ Error creating video: {str(video_error)}")
        
        response_data = {
            'gif_data': gif_data,
            'video_path': video_path,
            'found_count': found_gifs,
            'total_count': len(processed_words),
            'success_rate': round((found_gifs / len(processed_words)) * 100, 1) if processed_words else 0,
            'original_text': message,
            'language': 'english',
            'sender_sid': request.sid,
            'success': True
        }
        
        print(f"📤 Sending English sign video response to room: {target_room}")
        
        if target_room:
            emit('english_sign_video_response', response_data, room=target_room, namespace='/video')
        else:
            emit('english_sign_video_response', response_data, broadcast=True, namespace='/video')
            
    except Exception as e:
        print(f"Error processing English text to sign video: {str(e)}")
        emit('error', {'message': f'Error generating sign video: {str(e)}'}, namespace='/video')

@socketio.on('english_video_frame', namespace='/video')
def handle_english_video_frame(data):
    """
    Handle English video frame processing for sign language to text conversion
    Enhanced with ASL EfficientNetB0 detection
    """
    sid = request.sid
    try:
        # Load balancing for multiple users
        current_time = datetime.datetime.now()
        active_users = len(client_sequences)
        
        if active_users > 1:
            min_interval = 0.4
        else:
            min_interval = 0.2
        
        if sid in client_last_processed_time:
            time_since_last = (current_time - client_last_processed_time[sid]).total_seconds()
            if time_since_last < min_interval:
                return
        
        client_last_processed_time[sid] = current_time
        
        # Initialize client data structures
        if sid not in client_sequences:
            client_sequences[sid] = []
        if sid not in client_sentences:
            client_sentences[sid] = []
        if sid not in client_last_update:
            client_last_update[sid] = datetime.datetime.now()

        # Decode base64 frame
        image_data = base64.b64decode(data['frame'].split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            print(f"Error: Could not decode frame for English processing, sid {sid}")
            emit('error', {'message': 'Could not decode frame.'}, namespace='/video', to=sid)
            return

        # Try ASL EfficientNetB0 detection first, fall back to MediaPipe
        asl_detector = get_asl_detector()
        asl_result = None
        
        if asl_detector and asl_detector.model:
            try:
                asl_result = asl_detector.process_frame_realtime(frame)
                if asl_result['sign_detected']:
                    # Send ASL detection result
                    test_room = session.get('test_room')
                    regular_room = session.get('friend', sid)
                    target_room = test_room if test_room else regular_room
                    
                    user_info = session.get('user', {})
                    username = user_info.get('username', 'Unknown User')
                    
                    emit('sign_language_translation', {
                        'sentence': [{'word': asl_result['predicted_sign'], 'confidence': float(asl_result['confidence'])}],
                        'translated_text': asl_result['predicted_sign'],
                        'language': 'english',
                        'detection_method': 'ASL EfficientNetB0',
                        'sid': sid,
                        'username': username,
                        'timestamp': datetime.datetime.now().isoformat()
                    }, namespace='/video', room=target_room)
                    
                    print(f"🎯 ASL detected: {asl_result['predicted_sign']} ({asl_result['confidence']:.2f}) from {username}")
                    return  # Use ASL result, skip MediaPipe
            except Exception as asl_error:
                print(f"ASL detection error: {asl_error}")
        
        # Fallback to MediaPipe processing
        try:
            sequence = client_sequences[sid]
            sentence = client_sentences[sid]
            last_update_time = client_last_update[sid]
            
            # Use the process_frame function from realtime_sign.py
            processed_frame, new_sequence, new_sentence, new_last_update, reshaped_sentence = process_frame(
                frame, sequence, sentence, last_update_time, threshold=0.85
            )
            
            # Update client data
            client_sequences[sid] = new_sequence
            client_sentences[sid] = new_sentence
            client_last_update[sid] = new_last_update
            
            # Send MediaPipe translation if sentence changed
            if new_sentence and (not sentence or len(new_sentence) != len(sentence)):
                # Convert Arabic to English equivalent
                english_translation = translate_arabic_to_english(reshaped_sentence)
                
                test_room = session.get('test_room')
                regular_room = session.get('friend', sid)
                target_room = test_room if test_room else regular_room
                
                user_info = session.get('user', {})
                username = user_info.get('username', 'Unknown User')
                
                emit('sign_language_translation', {
                    'sentence': [{'word': word[0], 'confidence': float(word[1])} for word in new_sentence],
                    'translated_text': english_translation,
                    'language': 'english',
                    'detection_method': 'MediaPipe',
                    'sid': sid,
                    'username': username,
                    'timestamp': datetime.datetime.now().isoformat()
                }, namespace='/video', room=target_room)
                
                print(f"📤 MediaPipe translation: {english_translation} from {username}")
        
        except Exception as processing_error:
            print(f"Error processing English video frame: {str(processing_error)}")

    except Exception as e:
        print(f"Error in handle_english_video_frame for sid {sid}: {str(e)}")
        emit('error', {'message': f'Error: {str(e)}'}, namespace='/video', to=sid)

@socketio.on('english_text_to_gif', namespace='/video')
def handle_english_text_to_gif(data):
    """
    Handle English text to GIF conversion using gif_ASL directory
    """
    try:
        text = data.get('text', '').strip()
        if not text:
            emit('english_gif_error', {'error': 'No text provided'})
            return
        
        print(f"🔤 Processing English text to GIF: '{text}'")
        
        # Process text to find matching words
        processed_words = process_english_text(text)
        
        # Get GIF paths for each word
        gif_data = []
        found_gifs = 0
        
        for word in processed_words:
            gif_paths = get_gif_paths_for_word(word, language='english')
            if gif_paths:
                gif_data.append({
                    'word': word,
                    'gif_path': gif_paths[0],  # Use first GIF
                    'found': True
                })
                found_gifs += 1
                print(f"✅ Found GIF for '{word}': {gif_paths[0]}")
            else:
                gif_data.append({
                    'word': word,
                    'gif_path': None,
                    'found': False
                })
                print(f"❌ No GIF found for '{word}'")
        
        # Send response
        emit('english_gif_response', {
            'original_text': text,
            'processed_words': processed_words,
            'gif_data': gif_data,
            'found_count': found_gifs,
            'total_count': len(processed_words),
            'success_rate': (found_gifs / len(processed_words)) * 100 if processed_words else 0
        })
        
        print(f"📊 GIF conversion stats: {found_gifs}/{len(processed_words)} words found ({(found_gifs/len(processed_words)*100):.1f}%)")
        
    except Exception as e:
        print(f"Error in handle_english_text_to_gif: {str(e)}")
        emit('english_gif_error', {'error': str(e)})

def translate_arabic_to_english(arabic_text):
    """
    Simple Arabic to English translation mapping
    This is a basic implementation - you can enhance with a proper translation API
    """
    arabic_to_english = {
        'تتصرف': 'act', 'الحمدلله': 'praise be to God', 'جميعا': 'all', 'بابا': 'dad',
        'اساسيات': 'basics', 'بسبب': 'because', 'ولد': 'boy', 'شجاع': 'brave',
        'اتصل': 'call', 'هادئ': 'calm', 'كليه': 'college', 'متوتر': 'confused',
        'محادثه': 'conversation', 'بكاء': 'crying', 'يوميا': 'daily', 'خطر': 'danger',
        'اختلف مع': 'disagree with', 'اشرب': 'drink', 'اكل': 'eat', 'مجهود': 'effort',
        'مصر': 'Egypt', 'دخول': 'enter', 'ممتاز': 'excellent', 'الشرح': 'explanation',
        'في الصيام': 'fasting', 'انثي': 'female', 'اولا': 'first', 'لنا': 'for us',
        'الوقود': 'fuel', 'الهديه': 'gift', 'البنت': 'girl', 'الكوب': 'glass',
        'الي اللقاء': 'goodbye', 'الحكومه': 'government', 'بسعاده': 'happy',
        'اكره': 'hate', 'اسمع': 'hear', 'تساعد': 'help', 'تفضل': 'here you are',
        'كيف حالك': 'how are you', 'البشريه': 'humanity', 'اشعر بالجوع': 'hungry',
        'انا': 'I', 'تجاهل': 'ignorance', 'حالا': 'immediately', 'المهم': 'important',
        'الذكاء': 'intelligent', 'الاخير': 'last', 'القائد': 'leader', 'الكاذب': 'liar',
        'احب': 'love', 'ذكر': 'male', 'ماما': 'mom', 'الذاكره': 'memory',
        'نموذج': 'model', 'في الغالب': 'mostly', 'الدافع': 'motive', 'مسلم': 'Muslim',
        'لازم': 'must', 'وطني': 'my homeland', 'لا': 'no', 'الهراء': 'nonsense',
        'بديهي': 'obvious', 'القديمه': 'old', 'فلسطين': 'Palestine', 'اوقف': 'prevent',
        'جاهز_ل': 'ready', 'الرفض': 'rejection', 'صحيح': 'right', 'تختار': 'select',
        'اصمت': 'shut up', 'الغني': 'sing', 'النوم': 'sleep', 'اشم': 'smell',
        'يسمح بالتدخين': 'smoke', 'بالمعلقه': 'spoon', 'الصيف': 'summer',
        'الندوه': 'symposium', 'الشاي': 'tea', 'معلمي': 'teacher', 'مخيف': 'terrifying',
        'شكرا لكم': 'thank you', 'الوقت': 'time', 'تقاطع لاجل': 'boycott',
        'تهتف ل': 'cheer', 'ذاهب الي': 'go to', 'ل اعيش': 'to live', 'تنتشر': 'spread',
        'دوره المياه': 'toilet', 'فخ': 'trap', 'الجامعه': 'university',
        'مرحباً بكم': 'welcome', 'النصر': 'victory', 'المشي': 'walk', 'اين': 'where',
        'اين تسكن': 'where do you live', 'الشباك': 'window', 'الشتاء': 'winter',
        'نعم': 'yes', 'انت': 'you'
    }
    
    # Split text and translate each word
    words = arabic_text.split()
    english_words = []
    
    for word in words:
        english_word = arabic_to_english.get(word, word)  # Keep original if not found
        english_words.append(english_word)
    
    return ' '.join(english_words)

def create_english_gif_video(gif_data, text):
    """
    Create a single concatenated GIF from multiple English GIF files
    Combines all GIFs into one seamless animated GIF
    """
    try:
        import os
        import time
        from PIL import Image
        from datetime import datetime
        
        # Create directory for English sign videos if it doesn't exist
        english_videos_dir = os.path.join('static', 'english_sign_videos')
        os.makedirs(english_videos_dir, exist_ok=True)
        
        print(f"🎬 Creating concatenated GIF for: '{text}'")
        
        # Collect GIF files that were found
        gif_files = []
        for word_data in gif_data:
            if word_data['found'] and word_data['gif_path']:
                # Convert URL path to file system path
                gif_path = word_data['gif_path'].replace('/gif_ASL/', 'gif_ASL/')
                if os.path.exists(gif_path):
                    gif_files.append(gif_path)
                    print(f"📄 Adding GIF: {gif_path}")
                else:
                    print(f"⚠️ GIF file not found: {gif_path}")
        
        if not gif_files:
            print("❌ No valid GIF files found")
            return None
        
        # Load and process all GIF frames
        all_frames = []
        target_size = None
        
        for gif_path in gif_files:
            try:
                # Open GIF and extract frames
                gif = Image.open(gif_path)
                gif_frames = []
                
                # Extract all frames from this GIF
                frame_count = 0
                while True:
                    try:
                        gif.seek(frame_count)
                        frame = gif.copy()
                        
                        # Convert to RGB if necessary
                        if frame.mode != 'RGB':
                            frame = frame.convert('RGB')
                        
                        # Set target size from first frame
                        if target_size is None:
                            target_size = frame.size
                        else:
                            # Resize frame to match target size
                            frame = frame.resize(target_size, Image.Resampling.LANCZOS)
                        
                        gif_frames.append(frame)
                        frame_count += 1
                        
                    except EOFError:
                        break
                
                # Add frames multiple times for proper duration (about 2 seconds per word)
                repeat_count = max(1, int(20 / len(gif_frames))) if gif_frames else 1  # 20 frames ≈ 2 seconds
                
                for _ in range(repeat_count):
                    all_frames.extend(gif_frames)
                
                print(f"✅ Loaded {len(gif_frames)} frames from {gif_path} (repeated {repeat_count} times)")
                
            except Exception as e:
                print(f"❌ Error processing {gif_path}: {str(e)}")
                continue
        
        if not all_frames:
            print("❌ No frames extracted from GIFs")
            return None
        
        # Create output filename
        timestamp = int(time.time())
        output_filename = f"english_sign_{timestamp}.gif"
        output_path = os.path.join(english_videos_dir, output_filename)
        
        # Save concatenated GIF
        print(f"💾 Saving concatenated GIF with {len(all_frames)} frames...")
        
        # Save the first frame with all subsequent frames
        all_frames[0].save(
            output_path,
            save_all=True,
            append_images=all_frames[1:],
            duration=100,  # 100ms per frame = 10 FPS
            loop=0,  # Infinite loop
            optimize=True
        )
        
        # Verify output file
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"✅ Created concatenated GIF: {output_path}")
            return f"/static/english_sign_videos/{output_filename}"
        else:
            print("❌ Failed to create concatenated GIF")
            return None
        
    except Exception as e:
        print(f"❌ Error in create_english_gif_video: {str(e)}")
        return None

def convert_gif_to_video(gif_path, output_path, duration_per_frame=0.1):
    """
    Convert GIF file to MP4 video using OpenCV
    """
    try:
        # Read GIF frames
        cap = cv2.VideoCapture(gif_path)
        if not cap.isOpened():
            print(f"❌ Could not open GIF: {gif_path}")
            return False
        
        # Get GIF properties
        fps = 10  # Standard FPS for sign language videos
        frames = []
        
        # Read all frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        
        cap.release()
        
        if not frames:
            print(f"❌ No frames found in GIF: {gif_path}")
            return False
        
        # Get frame dimensions
        height, width, channels = frames[0].shape
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Write frames multiple times to create desired duration
        # Each GIF should play for about 2-3 seconds
        repeat_count = max(1, int(2.0 * fps / len(frames)))  # 2 seconds minimum
        
        for _ in range(repeat_count):
            for frame in frames:
                out.write(frame)
        
        out.release()
        
        # Verify video was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"✅ Successfully converted GIF to video: {output_path}")
            return True
        else:
            print(f"❌ Video file was not created properly: {output_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error converting GIF to video: {str(e)}")
        return False

# Add route to serve gif_ASL directory as static content
@app.route('/gif_ASL/<path:filename>')
def serve_gif_asl(filename):
    """Serve GIF files from gif_ASL directory"""
    try:
        return send_from_directory('gif_ASL', filename)
    except Exception as e:
        print(f"Error serving GIF file {filename}: {str(e)}")
        abort(404)

if __name__ == '__main__':
    import argparse
    import ssl
    
    parser = argparse.ArgumentParser(description='Run Sign Language Translator Server')
    parser.add_argument('--https', action='store_true', help='Run with HTTPS (required for camera access in production)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to (default: 5001)')
    parser.add_argument('--cert', help='Path to SSL certificate file')
    parser.add_argument('--key', help='Path to SSL private key file')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Sign Language Translator Server")
    print("=" * 60)
    
    if args.https:
        print("🔒 HTTPS mode enabled (required for camera access)")
        
        # Check for SSL certificate files
        cert_file = args.cert or 'cert.pem'
        key_file = args.key or 'key.pem'
        
        # Try to create self-signed certificate if not exists
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            print("📄 SSL certificate files not found. Creating self-signed certificate...")
            try:
                # Create self-signed certificate
                import subprocess
                subprocess.run([
                    'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-keyout', key_file, 
                    '-out', cert_file, '-sha256', '-days', '365', '-nodes',
                    '-subj', '/CN=localhost'
                ], check=True, capture_output=True)
                print(f"✅ Created self-signed certificate: {cert_file}, {key_file}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ Could not create self-signed certificate.")
                print("🔧 Please install OpenSSL or provide certificate files manually.")
                print("🔗 For testing, you can also use HTTP with localhost")
                exit(1)
        
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        
        print(f"🌐 Server will run on https://{args.host}:{args.port}")
        print("🎥 Camera access should work with HTTPS")
        print("⚠️  For self-signed certificates, you may need to accept the security warning")
        
        socketio.run(app, host=args.host, port=args.port, debug=True, ssl_context=context)
    else:
        print("🔓 HTTP mode (camera may not work except on localhost)")
        print(f"🌐 Server will run on http://{args.host}:{args.port}")
        print("💡 For camera access, use --https or access via localhost")
        print("📝 Example: python app.py --https")
        
        socketio.run(app, host=args.host, port=args.port, debug=True)