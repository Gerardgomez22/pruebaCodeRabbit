import cv2

import math

import time

import threading

from HandTrackingModule import HandDetector

from VolumeHandControl import VolumeController

from dao.mongodb_dao import MongoDBDAO

from models.session import Session

from models.volume_event import VolumeEvent



def main():

    cap = cv2.VideoCapture(0) # Recuerda cambiarlo a 1 si la cámara no abre

    detector = HandDetector()

    vol_ctrl = VolumeController()

    db = MongoDBDAO()

   

    current_session = Session()

    db_status = "DB: CONECTADO" if db.connected else "DB: OFFLINE"

    color_db = (255, 0, 0) if db.connected else (0, 0, 255) #

   

    volBar = 400

    volPer = 0

   

    # --- VARIABLES DEL TEMPORIZADOR ---

    last_saved_vol = vol_ctrl.get_current_volume()

    target_vol = None

    start_time = 0

    status_text = ""



    try:

        while True:

            success, img = cap.read()

            if not success:

                break

               

            img = detector.findHands(img)

            lmList = detector.findPosition(img)

           

            status_text = "" # Borrar texto por defecto



            if len(lmList) != 0:

                x1, y1 = lmList[4][1], lmList[4][2]

                x2, y2 = lmList[8][1], lmList[8][2]

                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2



                cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)

                cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)

                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)



                length = math.hypot(x2 - x1, y2 - y1)



                if len(lmList) != 0:

                    fingers = detector.fingersUp()

                    totalFingers = fingers.count(1)



                    x1, y1 = lmList[4][1], lmList[4][2]

                    x2, y2 = lmList[8][1], lmList[8][2]

                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2



                    length = math.hypot(x2 - x1, y2 - y1)

                    can_save = (totalFingers == 2 and fingers[0] == 1 and fingers[4] == 0)



                if can_save:

                    cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

                    volBar, volPer = vol_ctrl.set_volume_by_distance(length)

                    new_vol = vol_ctrl.get_current_volume()



                    if abs(new_vol - last_saved_vol) > 2:

                        if target_vol is not None and abs(new_vol - target_vol) <= 3:

                            elapsed_time = time.time() - start_time

                            if elapsed_time >= 2.0:

                                try:

                                    event = VolumeEvent(last_saved_vol, new_vol, length)

                                    hilo_bd = threading.Thread(target=db.insert_volume_event, args=(event.to_dict(),))

                                    hilo_bd.start()

                                    last_saved_vol = new_vol

                                    target_vol = None

                                    status_text = "¡GUARDADO!"

                                except Exception as e:

                                    print(f"Error: {e}")

                            else:

                                status_text = f"Fijando... {2.0 - elapsed_time:.1f}s"

                        else:

                            target_vol = new_vol

                            start_time = time.time()

                    else:

                        target_vol = None

                else:

                    target_vol = None

                    if totalFingers == 5:

                        status_text = "MANO ABIERTA - BLOQUEADO"



            # --- DIBUJOS DE LA INTERFAZ ---

            cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)

            cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)

            cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)

            cv2.putText(img, db_status, (400, 50), cv2.FONT_HERSHEY_COMPLEX, 1, color_db, 2)

           

            # Dibujar el texto de la cuenta atrás

            if status_text:

                cv2.putText(img, status_text, (200, 400), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 2)



            cv2.imshow("Control Volumen Manos", img)



            if cv2.waitKey(1) & 0xFF == ord('q'):

                break

            if cv2.getWindowProperty("Control Volumen Manos", cv2.WND_PROP_VISIBLE) < 1:

                break



    finally:

        current_session.end_session()

        try:

            hilo_sesion = threading.Thread(target=db.insert_session, args=(current_session.to_dict(),))

            hilo_sesion.start()

        except Exception as e:

            print(f"Error al iniciar guardado de sesión: {e}")

           

        cap.release()

        cv2.destroyAllWindows()



if __name__ == "__main__":

    main()