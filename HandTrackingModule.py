import cv2
import mediapipe as mp
import math

class HandDetector:
    def __init__(self, detectionCon=0.7, trackCon=0.5):
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(min_detection_confidence=detectionCon, min_tracking_confidence=trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        # IMPORTANTE: Definir los IDs de las puntas de los dedos
        self.tipIds = [4, 8, 12, 16, 20] 

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0):
        self.lmList = [] # Usamos self.lmList para que fingersUp pueda verla
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
        return self.lmList

    def checkPinkyDown(self, lmList):
        if len(lmList) != 0:
            # El punto 20 es la punta, el 17 es la base del meñique
            return lmList[20][2] > lmList[17][2] 
        return False
    
    def fingersUp(self):
        fingers = []
        if len(self.lmList) == 0:
            return [0, 0, 0, 0, 0]

        # Pulgar (Lógica para mano derecha, compara eje X)
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Los otros 4 dedos (compara eje Y)
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers