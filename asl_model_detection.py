import tensorflow as tf
import cv2
import numpy as np
import os
import sys
from pathlib import Path
import datetime
import time
from tensorflow.keras.applications.efficientnet import preprocess_input
from sklearn.preprocessing import LabelEncoder
import mediapipe as mp

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class ASLModelDetector:
    def __init__(self, model_path=os.path.join("models", "asl_model_efficientnetb000.h5"), confidence_threshold=0.7):
        """
        Initialize ASL EfficientNetB0 + LSTM detector (aligned with notebook)
        
        Args:
            model_path: Path to trained ASL model (default: models/asl_model_efficientnetb000.h5)
            confidence_threshold: Minimum confidence for valid predictions
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        
        # Frame sequence settings (from notebook)
        self.frame_width = 224  # Input size for EfficientNet
        self.frame_height = 224
        self.target_frames = 12  # Number of frames expected by the model
        self.frame_sequence = []
        
        # Prediction display settings
        self.predicted_class = None
        self.prediction_time = None
        self.prediction_display_time = 2  # Time to display prediction in seconds
        
        # Frame sequence timeout settings
        self.last_hand_detection_time = None
        self.hand_detection_timeout = 3  # Reset sequence if no hands detected for 3 seconds
        
        # MediaPipe hand detection
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # ASL class names (from notebook)
        self.class_names = [
            'again', 'bad', 'bathroom', 'book', 'busy', 'do not want', 'eat', 'father', 'fine', 'finish',
            'forget', 'go', 'good', 'happy', 'hello', 'help', 'how', 'i', 'learn', 'like', 'meet', 'milk',
            'more', 'mother', 'my', 'name', 'need', 'nice', 'no', 'please', 'question', 'right', 'sad',
            'same', 'see you later', 'thank you', 'want', 'what', 'when', 'where', 'which', 'who', 'why',
            'wrong', 'yes', 'you', 'your'
        ]
        
        # Set up Label Encoder
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(self.class_names)
        
        # Load model
        try:
            self._load_model()
            print(f"✅ ASL EfficientNetB0+LSTM model loaded successfully from {model_path}")
        except Exception as e:
            print(f"❌ Failed to load ASL model: {e}")
            self.model = None
    
    def _load_model(self):
        """Load the ASL sequence model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        # Load the Keras model
        self.model = tf.keras.models.load_model(self.model_path)
        
        # Get model info
        input_shape = self.model.input_shape
        output_shape = self.model.output_shape
        
        print(f"🔍 Model input shape: {input_shape}")
        print(f"🎯 Model output shape: {output_shape}")
        print(f"📋 Available classes: {len(self.class_names)}")
        print(f"📐 Frame size: {self.frame_width}x{self.frame_height}")
        print(f"📺 Target frames: {self.target_frames}")
    
    def detect_hands(self, frame):
        """
        Detect hands in frame using MediaPipe
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            Tuple: (hands_detected: bool, hand_landmarks: list, rgb_frame: np.array)
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame for hand detection
        results = self.hands.process(rgb_frame)
        
        # Check if hands are detected
        hands_detected = results.multi_hand_landmarks is not None
        hand_landmarks = results.multi_hand_landmarks if hands_detected else []
        
        return hands_detected, hand_landmarks, rgb_frame
    
    def add_frame_to_sequence(self, frame):
        """
        Add frame to sequence only when hands are detected (aligned with notebook approach)
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            Tuple: (sequence_ready: bool, hands_detected: bool, hand_landmarks: list)
        """
        # Detect hands in frame first
        hands_detected, hand_landmarks, _ = self.detect_hands(frame)
        
        current_time = time.time()
        
        # Only add frame to sequence if hands are detected
        if hands_detected:
            self.last_hand_detection_time = current_time
            
            # Resize frame for model input (as in notebook)
            resized_frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            self.frame_sequence.append(resized_frame)
            
            # Check if we have enough frames
            if len(self.frame_sequence) == self.target_frames:
                return True, hands_detected, hand_landmarks
        else:
            # Reset sequence if no hands detected for too long
            if (self.last_hand_detection_time is not None and 
                len(self.frame_sequence) > 0 and 
                current_time - self.last_hand_detection_time > self.hand_detection_timeout):
                print("🔄 Resetting sequence - no hands detected for too long")
                self.frame_sequence = []
        
        return False, hands_detected, hand_landmarks
    
    def predict_sequence(self):
        """
        Predict ASL sign from current frame sequence (notebook approach)
        
        Returns:
            Dictionary with prediction results or None
        """
        if self.model is None or len(self.frame_sequence) < self.target_frames:
            return None
        
        try:
            # Convert sequence to numpy array and preprocess (as in notebook)
            frame_sequence_array = np.array(self.frame_sequence)
            frame_sequence_array = np.expand_dims(frame_sequence_array, axis=0)  # Add batch dimension
            frame_sequence_array = preprocess_input(frame_sequence_array)
            
            # Prediction
            predictions = self.model.predict(frame_sequence_array, verbose=0)
            predicted_class_idx = np.argmax(predictions)
            confidence = float(np.max(predictions))
            
            # Get class name using label encoder
            predicted_class = self.label_encoder.inverse_transform([predicted_class_idx])[0]
            
            # Store prediction with timestamp (as in notebook)
            self.predicted_class = predicted_class
            self.prediction_time = time.time()
            
            # Reset frame sequence after prediction (as in notebook)
            self.frame_sequence = []
            
            return {
                'predicted_sign': predicted_class,
                'confidence': confidence,
                'class_id': predicted_class_idx,
                'all_predictions': predictions[0].tolist()
            }
        
        except Exception as e:
            print(f"Error in ASL sequence prediction: {e}")
            # Reset sequence on error
            self.frame_sequence = []
            return None
    
    def get_current_prediction(self):
        """
        Get current prediction if within display time (notebook approach)
        
        Returns:
            Current prediction or None if expired
        """
        if (self.predicted_class is not None and 
            self.prediction_time is not None and
            (time.time() - self.prediction_time) < self.prediction_display_time):
            return self.predicted_class
        else:
            return None
    
    def detect_sign(self, frame):
        """
        Process frame and detect ASL sign only when hands are present (notebook approach)
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            Dictionary with prediction results and hand detection status
        """
        # Add frame to sequence (only when hands detected)
        sequence_ready, hands_detected, hand_landmarks = self.add_frame_to_sequence(frame)
        
        result = {
            'hands_detected': hands_detected,
            'hand_landmarks': hand_landmarks,
            'predicted_sign': None,
            'confidence': 0.0,
            'class_id': -1,
            'from_cache': False
        }
        
        if sequence_ready:
            # Make prediction on full sequence
            prediction = self.predict_sequence()
            if prediction:
                result.update(prediction)
                result['hands_detected'] = hands_detected
                result['hand_landmarks'] = hand_landmarks
            return result
        else:
            # Check if we have a current prediction to display
            current_pred = self.get_current_prediction()
            if current_pred:
                result.update({
                    'predicted_sign': current_pred,
                    'confidence': 1.0,  # Display with full confidence
                    'class_id': -1,
                    'from_cache': True
                })
            return result
    
    def annotate_frame(self, frame, detection_result):
        """
        Draw prediction results and hand landmarks on frame (notebook style)
        
        Args:
            frame: Input frame
            detection_result: Result from detect_sign()
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        height, width = frame.shape[:2]
        
        # Draw hand landmarks if detected
        if detection_result and detection_result.get('hands_detected', False):
            hand_landmarks = detection_result.get('hand_landmarks', [])
            for hand_landmark in hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated_frame, hand_landmark, self.mp_hands.HAND_CONNECTIONS)
        
        # Show hand detection status
        hands_status = "Hands: DETECTED" if (detection_result and detection_result.get('hands_detected', False)) else "Hands: NOT DETECTED"
        status_color = (0, 255, 0) if (detection_result and detection_result.get('hands_detected', False)) else (0, 0, 255)
        cv2.putText(annotated_frame, hands_status, 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Show frame collection progress (only when hands detected)
        if detection_result and detection_result.get('hands_detected', False):
            progress_text = f"Frames: {len(self.frame_sequence)}/{self.target_frames}"
            cv2.putText(annotated_frame, progress_text, 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            # Show message when no hands detected
            cv2.putText(annotated_frame, "Show hands to start capturing frames", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        # Show prediction if available (notebook style)
        current_prediction = self.get_current_prediction()
        if current_prediction:
            prediction_text = f"Predicted: {current_prediction}"
            cv2.putText(annotated_frame, prediction_text, 
                       (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Show confidence if we have recent detection result
        if detection_result and not detection_result.get('from_cache', False) and detection_result.get('predicted_sign'):
            confidence = detection_result['confidence']
            confidence_text = f"Confidence: {confidence:.2f}"
            cv2.putText(annotated_frame, confidence_text, 
                       (10, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show collection status
        if detection_result and detection_result.get('hands_detected', False) and len(self.frame_sequence) < self.target_frames and not current_prediction:
            status_text = "Collecting frames..."
            cv2.putText(annotated_frame, status_text, 
                       (10, height - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return annotated_frame
    
    def process_frame_realtime(self, frame):
        """
        Process frame for real-time ASL detection (notebook aligned)
        
        Args:
            frame: Input frame
            
        Returns:
            Dictionary with detection results and annotated frame
        """
        detection_result = self.detect_sign(frame)
        annotated_frame = self.annotate_frame(frame.copy(), detection_result)
        
        # Determine if sign was detected with sufficient confidence
        sign_detected = False
        predicted_sign = None
        confidence = 0.0
        
        # Check current prediction
        current_prediction = self.get_current_prediction()
        if current_prediction:
            sign_detected = True
            predicted_sign = current_prediction
            confidence = 1.0 if detection_result and not detection_result.get('from_cache', False) else 0.8
        elif detection_result and detection_result['confidence'] >= self.confidence_threshold:
            sign_detected = True
            predicted_sign = detection_result['predicted_sign']
            confidence = detection_result['confidence']
        
        result = {
            'frame': annotated_frame,
            'detection_result': detection_result,
            'sign_detected': sign_detected,
            'predicted_sign': predicted_sign,
            'confidence': confidence,
            'frames_collected': len(self.frame_sequence),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return result
    
    def reset_sequence(self):
        """Reset the frame sequence buffer"""
        self.frame_sequence = []
        self.predicted_class = None
        self.prediction_time = None
        self.last_hand_detection_time = None
        print("🔄 Frame sequence buffer reset")
    
    def get_model_info(self):
        """Get information about the loaded model"""
        if self.model is None:
            return None
        
        return {
            'model_path': self.model_path,
            'target_frames': self.target_frames,
            'frame_size': f"{self.frame_width}x{self.frame_height}",
            'num_classes': len(self.class_names),
            'class_names': self.class_names[:10],  # Show first 10 classes
            'confidence_threshold': self.confidence_threshold,
            'architecture': 'EfficientNetB0 + LSTM (Notebook-aligned)',
            'prediction_display_time': self.prediction_display_time
        }

# Global detector instance
asl_detector = None

def initialize_asl_detector(model_path=os.path.join("models", "asl_model_efficientnetb000.h5"), confidence_threshold=0.7):
    """Initialize global ASL detector"""
    global asl_detector
    try:
        asl_detector = ASLModelDetector(model_path, confidence_threshold)
        return asl_detector is not None and asl_detector.model is not None
    except Exception as e:
        print(f"Failed to initialize ASL detector: {e}")
        return False

def get_asl_detector():
    """Get global ASL detector instance"""
    return asl_detector

# Test function (notebook style)
if __name__ == "__main__":
    print("🧪 Testing ASL Model Detection (Notebook Style)...")
    
    # Initialize detector
    detector = ASLModelDetector()
    
    if detector.model is not None:
        print("✅ Model loaded successfully")
        print("📊 Model info:", detector.get_model_info())
        
        # Test with webcam (following notebook approach)
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                print("📹 Testing with webcam... Press 'q' to quit, 'r' to reset sequence")
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Flip frame horizontally (as in notebook)
                    frame = cv2.flip(frame, 1)
                    
                    # Process frame
                    result = detector.process_frame_realtime(frame)
                    
                    # Display result
                    cv2.imshow('ASL Real-Time Detection (Notebook Style)', result['frame'])
                    
                    if result['sign_detected']:
                        print(f"🎯 Detected: {result['predicted_sign']} ({result['confidence']:.2f})")
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('r'):
                        detector.reset_sequence()
                
                cap.release()
                cv2.destroyAllWindows()
            else:
                print("⚠️ Webcam not available for testing")
        
        except Exception as e:
            print(f"Webcam test error: {e}")
    
    else:
        print("❌ Model failed to load") 