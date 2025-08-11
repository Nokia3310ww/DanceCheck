
import pygame
import cv2
import numpy as np
import time
import pose_module as pm
from scipy.spatial.distance import cosine
from fastdtw import fastdtw
from ffpyplayer.player import MediaPlayer
import tkinter as tk
from tkinter import filedialog
import json
import os
import subprocess
import sys

video_history = []  # ใส่ไว้ด้านบนของไฟล์ หรือ global
MAX_HISTORY = 5     # จำกัดประวัติล่าสุดไว้ที่ 5 ไฟล์

# ฟังก์ชันสำหรับบันทึกประวัติลงไฟล์
def save_video_history():
    try:
        with open("video_history.json", "w") as f:
            json.dump(video_history, f)
    except Exception as e:
        print("Error saving history:", e)

# ฟังก์ชันสำหรับโหลดประวัติจากไฟล์
def load_video_history():
    global video_history
    if os.path.exists("video_history.json"):
        try:
            with open("video_history.json", "r") as f:
                video_history = json.load(f)
        except Exception as e:
            print("Error loading history:", e)
    else:
        video_history = []

# เริ่มต้น Pygame
pygame.init()

# ตั้งค่าหน้าจอ
WIDTH, HEIGHT = 1500, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Navigation Example")

# ตั้งค่าฟอนต์
font = pygame.font.Font(None, 50)

# โหลดรูปภาพ
image_paths = { 
}

button_images = {}

for key, path in image_paths.items():
    try:
        image = pygame.image.load(path)  # โหลดรูปภาพ
        button_images[key] = pygame.transform.scale(image, (250, 250))  # ปรับขนาด
    except pygame.error:
        print(f"Error loading image: {path}")

# คำนวณตำแหน่งรูปภาพให้อยู่ตรงกลางเฉพาะหน้าที่สอง
image_spacing = 50
columns = 3  # จำนวนรูปภาพต่อแถว
rows = (len(button_images) + columns - 1) // columns  # คำนวณจำนวนแถว

total_width = columns * 250 + (columns - 1) * image_spacing
start_x = (WIDTH - total_width) // 2

total_height = rows * 250 + (rows - 1) * image_spacing
start_y = (HEIGHT - total_height) // 2

image_positions = {}
keys = list(button_images.keys())

for i, key in enumerate(keys):
    x = start_x + (i % columns) * (250 + image_spacing)
    y = start_y + (i // columns) * (250 + image_spacing)
    image_positions[key] = (x, y)

image_rects = {key: pygame.Rect(pos[0], pos[1], 250, 250) for key, pos in image_positions.items()}

# ปุ่ม Back, Next, และ Home
back_button_rect = pygame.Rect(20, 20, 150, 60)
back_text = font.render("BACK", True, (255, 255, 255))

next_button_rect = pygame.Rect(WIDTH - 170, HEIGHT - 90, 150, 60)
next_text = font.render("NEXT", True, (255, 255, 255))

home_button_rect = pygame.Rect(WIDTH - 170, HEIGHT - 90, 150, 60)
home_text = font.render("HOME", True, (255, 255, 255))

# ตัวแปรตรวจสอบการเลือก
selected_image = None
prev_selected_image = None

def main_menu():
    global selected_image, prev_selected_image
    selected_image = None
    prev_selected_image = None
    running = True
    while running:
        screen.fill((20, 100, 150))
        start_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 40, 200, 80)
        pygame.draw.rect(screen, (0, 200, 0), start_rect, border_radius=10)
        screen.blit(font.render("START", True, (255, 255, 255)), (start_rect.x + 50, start_rect.y + 20))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    game_screen()
        
        pygame.display.flip()

def game_screen():
    global selected_image, prev_selected_image, video_history
    selected_image = None
    prev_selected_image = None

    # โหลดประวัติจากไฟล์
    load_video_history()

    running = True
    history_rects = []  # สร้าง list สำหรับเก็บ rect ของประวัติ
    while running:
        screen.fill((20, 100, 150))
        
        # ปุ่มเลือกวิดีโอใหม่
        select_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 100, 300, 60)
        pygame.draw.rect(screen, (70, 130, 180), select_rect, border_radius=10)
        screen.blit(font.render("Select New Video", True, (255, 255, 255)), (select_rect.x + 10, select_rect.y + 15))

         # ปุ่มเปิดโฟลเดอร์ record
        replay_button_rect = pygame.Rect(WIDTH - 170, HEIGHT - 90, 150, 60)
        pygame.draw.rect(screen, (255, 215, 0), replay_button_rect, border_radius=10)
        screen.blit(font.render("Replay", True, (0, 0, 0)), (replay_button_rect.x + 20, replay_button_rect.y + 10))

        # ปุ่ม BACK
        pygame.draw.rect(screen, (200, 0, 0), back_button_rect, border_radius=10)
        screen.blit(back_text, (back_button_rect.x + 20, back_button_rect.y + 10))

        # วาดข้อความ "History" และไฮไลท์เป็นกล่อง
        history_label_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 10, 200, 50)
        pygame.draw.rect(screen, (0, 0, 200), history_label_rect, border_radius=10)  # สีกล่องเป็นสีน้ำเงิน
        screen.blit(font.render("History", True, (255, 255, 255)), (history_label_rect.x + 50, history_label_rect.y + 10))  # ข้อความในกล่อง

        # ปรับค่า y_offset เพื่อให้รายการวิดีโอเริ่มแสดงที่ตำแหน่งด้านล่าง "History"
        y_offset = HEIGHT // 2 + 60  # ปรับให้เริ่มแสดงที่ต่ำกว่าข้อความ "History"
        history_rects.clear()  # ล้าง list ก่อนแสดงใหม่
        for idx, video_path in enumerate(video_history[-MAX_HISTORY:][::-1]):  # แสดงย้อนหลัง
            hist_rect = pygame.Rect(WIDTH // 2 - 200, y_offset + idx * 50, 400, 40)
            pygame.draw.rect(screen, (100, 180, 100), hist_rect, border_radius=8)
            display_name = os.path.basename(video_path)
            screen.blit(font.render(f"{display_name}", True, (0, 0, 0)), (hist_rect.x + 10, hist_rect.y + 10))

            # เก็บ rect และตำแหน่งของ video history ใน list
            history_rects.append((hist_rect, video_path))  # เก็บ rect กับ video_path

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if select_rect.collidepoint(event.pos):
                    root = tk.Tk()
                    root.withdraw()
                    file_path = filedialog.askopenfilename(
                        title="Select Video", 
                        filetypes=[("Video Files", "*.mp4 *.avi *.mov")]
                    )
                    root.destroy()
                    if file_path:
                        if file_path not in video_history:
                            video_history.append(file_path)
                            if len(video_history) > MAX_HISTORY:
                                video_history.pop(0)
                        save_video_history()  # บันทึกประวัติหลังเลือกวิดีโอ
                        next_screen(file_path)

                elif back_button_rect.collidepoint(event.pos):
                    main_menu()

                elif replay_button_rect.collidepoint(event.pos):
                    try:
                        folder_path = os.path.abspath("record")
                        if os.name == 'nt':  # Windows
                            os.startfile(folder_path)
                        elif sys.platform == 'darwin':  # macOS
                            subprocess.Popen(['open', folder_path])
                        else:  # Linux
                            subprocess.Popen(['xdg-open', folder_path])
                    except Exception as e:
                        print(f"Error opening folder: {e}")

                # ตรวจสอบการคลิกจากประวัติ
                for hist_rect, video_path in history_rects:
                    if hist_rect.collidepoint(event.pos):
                        next_screen(video_path)

        pygame.display.flip()


def draw_loading_bar(progress):
    """ ฟังก์ชันวาดแถบโหลดสีขาว """
    
    bar_width = 400
    bar_height = 30
    x = (WIDTH - bar_width) // 2
    y = (HEIGHT - bar_height) // 2

    # วาดบาร์สีขาว
    pygame.draw.rect(screen, (255, 255, 255), (x, y, int(bar_width * progress), bar_height))  

    # ข้อความ Loading...
    loading_text = font.render("Loading...", True, (255, 255, 255))
    screen.blit(loading_text, (x + bar_width // 3, y - 40))

    pygame.display.flip()  # อัปเดตหน้าจอ

def next_screen(video_path):
    global selected_image
    # เริ่มต้นหน้าจอและแสดงแถบโหลด
    screen.fill((20, 100, 150))

    
    for i in range(1, 11):
        draw_loading_bar(i / 10)
        time.sleep(0.2)
    for i in range(3, 0, -1):
        screen.fill((20, 100, 150))  # clear the screen
        countdown_text = font.render(str(i), True, (255, 255, 255))  # white color
        screen.blit(countdown_text, (WIDTH // 2 - 50, HEIGHT // 2 - 50))
        pygame.display.flip()
        time.sleep(1)  # Wait for 1 second
        
    pygame.display.flip()

   
    # เปิดกล้องและไฟล์วิดีโอตัวอย่าง
    cap = cv2.VideoCapture(0)  # กล้องเว็บแคม
    benchmark_cap = cv2.VideoCapture(video_path)
    player = None

    # สร้าง detector สำหรับผู้ใช้และ benchmark
    detector_user = pm.poseDetector()
    detector_benchmark = pm.poseDetector()

    # ตั้งค่า VideoWriter สำหรับบันทึกวิดีโอ
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join("record", f'gameplay_{timestamp}.avi')

    
    # ตั้งค่า FPS เป็น 30 (ต้องตรงกับค่าที่ใช้ใน clock.tick())
    out = cv2.VideoWriter(output_filename, fourcc, 10.0, (1500, 800))

    fps_time = time.time()
    skip_frames = 1  # ลองเปลี่ยนเป็น 3 หรือ 4 ถ้าต้องการให้เร็วขึ้น
    frame_skip_counter = 0
    frame_counter = 0
    correct_frames = 0
    start_time = time.time()
    
    running = True
    try:
        while running:
            ret_bench, frame_bench = benchmark_cap.read()
            if not ret_bench:
                benchmark_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret_bench, frame_bench = benchmark_cap.read()

            if frame_counter >= 1:
                if player is None:
                    player = MediaPlayer(video_path)
                audio_frame, val = player.get_frame()
                if val != 'eof' and audio_frame is not None:
                    img, t = audio_frame
                else:
                    t = time.time() - start_time
                benchmark_cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)

            ret_cam, frame_cam = cap.read()
            if not ret_cam:
                break

            frame_skip_counter += 1
            if frame_skip_counter < skip_frames:
                continue
            frame_skip_counter = 0

            frame_cam = cv2.flip(frame_cam, 1)
            
            # สำหรับการประมวลผล ปรับขนาดเฟรมเป็น 640x480
            process_size = (640, 480)
            frame_cam_proc = cv2.resize(frame_cam, process_size)
            frame_bench_proc = cv2.resize(frame_bench, process_size)

            # ตรวจจับท่าทางในแต่ละเฟรม
            frame_cam_proc = detector_user.findPose(frame_cam_proc)
            lmList_user = detector_user.findPosition(frame_cam_proc, draw=False)
            
            frame_bench_proc = detector_benchmark.findPose(frame_bench_proc, draw=False)
            lmList_bench = detector_benchmark.findPosition(frame_bench_proc, draw=False)
            
            frame_counter += 1

            # คำนวณ error โดยใช้ FastDTW กับ cosine distance
            try:
                error, _ = fastdtw(lmList_user, lmList_bench, dist=cosine)
            except Exception as e:
                error = 1.0

            error_text = "Error: {}%".format(round(100 * float(error), 2))
            cv2.putText(frame_cam_proc, error_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            if error < 0.3:
                cv2.putText(frame_cam_proc, "CORRECT STEPS", (40, 450),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                correct_frames += 1
            else:
                cv2.putText(frame_cam_proc, "INCORRECT STEPS", (40, 450),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            curr_time = time.time()
            fps = 1.0 / (curr_time - fps_time) if (curr_time - fps_time) > 0 else 0
            fps_time = curr_time
            cv2.putText(frame_cam_proc, "FPS: {:.2f}".format(fps), (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            accuracy = round(100 * correct_frames / frame_counter, 2)
            cv2.putText(frame_cam_proc, "Dance Steps Accurately Done: {}%".format(accuracy),
                        (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

            bench_width = int(WIDTH * 0.3)
            cam_width = WIDTH - bench_width
            display_height = HEIGHT

            frame_bench_disp = cv2.resize(frame_bench_proc, (bench_width, display_height))
            frame_cam_disp = cv2.resize(frame_cam_proc, (cam_width, display_height))
            
            # บันทึกเฟรมลงวิดีโอ
            original_combined = np.hstack((frame_bench_disp, frame_cam_disp))
            out.write(original_combined)

            combined_frame = cv2.cvtColor(original_combined, cv2.COLOR_BGR2RGB)
            combined_surface = pygame.surfarray.make_surface(combined_frame.swapaxes(0, 1))
            
            screen.blit(combined_surface, (0, 0))

            pygame.draw.rect(screen, (200, 0, 0), back_button_rect, border_radius=10)
            screen.blit(back_text, (back_button_rect.x + 20, back_button_rect.y + 10))
            pygame.draw.rect(screen, (255, 165, 0), home_button_rect, border_radius=10)
            screen.blit(home_text, (home_button_rect.x + 25, home_button_rect.y + 10))
            pygame.display.flip()
            ret_bench, frame_bench = benchmark_cap.read()
            if not ret_bench:
                cap.release()
                player = None
                benchmark_cap.release()
                # เมื่อเกมจบ
                screen.fill((20, 100, 150))
            
                # แสดงสกอร์
                final_score_text = f"Final Score: {accuracy}%"
                screen.blit(font.render(final_score_text, True, (255, 255, 255)), (WIDTH // 2 - 100, HEIGHT // 2 - 50))
                        
                # เพิ่มปุ่ม Restart
                restart_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 10, 200, 60)
                pygame.draw.rect(screen, (0, 255, 0), restart_button_rect, border_radius=10)
                screen.blit(font.render("Restart", True, (255, 255, 255)), (restart_button_rect.x + 40, restart_button_rect.y + 15))
                # เพิ่มปุ่ม Next
                next_button_rect = pygame.Rect(WIDTH - 170, HEIGHT - 90, 150, 60)
                pygame.draw.rect(screen, (0, 255, 0), next_button_rect, border_radius=10)
                screen.blit(font.render("Next", True, (255, 255, 255)), (next_button_rect.x + 40, next_button_rect.y + 15))

                pygame.display.flip()

                # ตรวจสอบการคลิกปุ่ม Restart
                running = True
                while running:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            exit()
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if restart_button_rect.collidepoint(event.pos):
                                cap.release()
                                player = None
                                benchmark_cap.release()
                                next_screen(video_path)  # เริ่มเกมใหม่
                            elif next_button_rect.collidepoint(event.pos):
                                cap.release()
                                player = None
                                benchmark_cap.release()
                                selected_image = prev_selected_image
                                game_screen()


            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release()
                    benchmark_cap.release()
                    player = None
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button_rect.collidepoint(event.pos):
                        cap.release()
                        player = None
                        benchmark_cap.release()
                        # เมื่อเกมจบ
                        screen.fill((20, 100, 150))
                        
                        # แสดงสกอร์
                        final_score_text = f"Final Score: {accuracy}%"
                        screen.blit(font.render(final_score_text, True, (255, 255, 255)), (WIDTH // 2 - 100, HEIGHT // 2 - 50))
                        
                        # เพิ่มปุ่ม Restart
                        restart_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 10, 200, 60)
                        pygame.draw.rect(screen, (0, 255, 0), restart_button_rect, border_radius=10)
                        screen.blit(font.render("Restart", True, (255, 255, 255)), (restart_button_rect.x + 40, restart_button_rect.y + 15))
                        # เพิ่มปุ่ม Next
                        next_button_rect = pygame.Rect(WIDTH - 170, HEIGHT - 90, 150, 60)
                        pygame.draw.rect(screen, (0, 255, 0), next_button_rect, border_radius=10)
                        screen.blit(font.render("Next", True, (255, 255, 255)), (next_button_rect.x + 40, next_button_rect.y + 15))

                        pygame.display.flip()

                        # ตรวจสอบการคลิกปุ่ม Restart
                        running = True
                        while running:
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    exit()
                                elif event.type == pygame.MOUSEBUTTONDOWN:
                                    if restart_button_rect.collidepoint(event.pos):
                                        cap.release()
                                        player = None
                                        benchmark_cap.release()
                                        next_screen(video_path)  # เริ่มเกมใหม่
                                    elif next_button_rect.collidepoint(event.pos):
                                        cap.release()
                                        player = None
                                        benchmark_cap.release()
                                        selected_image = prev_selected_image
                                        game_screen()

                    elif home_button_rect.collidepoint(event.pos):
                        cap.release()
                        player = None
                        benchmark_cap.release()
                        # เมื่อเกมจบ
                        screen.fill((20, 100, 150))
                        
                        # แสดงสกอร์
                        final_score_text = f"Final Score: {accuracy}%"
                        screen.blit(font.render(final_score_text, True, (255, 255, 255)), (WIDTH // 2 - 100, HEIGHT // 2 - 50))
                        
                        # เพิ่มปุ่ม Restart
                        restart_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 10, 200, 60)
                        pygame.draw.rect(screen, (0, 255, 0), restart_button_rect, border_radius=10)
                        screen.blit(font.render("Restart", True, (255, 255, 255)), (restart_button_rect.x + 40, restart_button_rect.y + 15))
                        next_button_rect = pygame.Rect(WIDTH - 170, HEIGHT - 90, 150, 60)
                        pygame.draw.rect(screen, (0, 255, 0), next_button_rect, border_radius=10)
                        screen.blit(font.render("Next", True, (255, 255, 255)), (next_button_rect.x + 40, next_button_rect.y + 15))

                        pygame.display.flip()

                        # ตรวจสอบการคลิกปุ่ม Restart
                        running = True
                        while running:
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    exit()
                                elif event.type == pygame.MOUSEBUTTONDOWN:
                                    if restart_button_rect.collidepoint(event.pos):
                                        cap.release()
                                        player = None
                                        benchmark_cap.release()
                                        next_screen(video_path)  # เริ่มเกมใหม่
                                    elif home_button_rect.collidepoint(event.pos):
                                        cap.release()
                                        player = None
                                        benchmark_cap.release()
                                        main_menu()

            pygame.display.flip()
    finally:
        # ปล่อยทรัพยากรเมื่อเกมจบ
        out.release()
        cap.release()
        benchmark_cap.release()
        if player is not None:
            player.close()

    

    cap.release()
    benchmark_cap.release()
    player.close()

main_menu()
