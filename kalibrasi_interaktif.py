import cv2
import numpy as np

# --- Variabel Global ---
pts_src_clicks_original_coords = [] # Akan menyimpan koordinat asli (setelah dikonversi dari klik di gambar display)
pts_scale_clicks_original_coords = [] # Akan menyimpan koordinat asli untuk skala
current_interaction_mode = "dlt_selection" # Mode: "dlt_selection", "scale_selection", "done"

final_pts_src = None
final_pts_dst = None
final_output_rect_wh = None
final_pixels_per_meter = None
homography_matrix_M = None

original_frame_from_file = None    # Frame asli dari file
display_image_for_interaction = None # Frame yang mungkin di-resize untuk ditampilkan
interactive_window_name = "Kalibrasi DLT & Skala - 'q': Keluar | 'r': Reset DLT pts | 'x': Reset Skala pts"
display_scale_factor = 1.0 # Faktor skala antara gambar asli dan yang ditampilkan

# --- Fungsi Callback Mouse ---
def mouse_callback_for_calibration(event, x_clicked, y_clicked, flags, param):
    global pts_src_clicks_original_coords, pts_scale_clicks_original_coords
    global current_interaction_mode, display_image_for_interaction, display_scale_factor

    if event == cv2.EVENT_LBUTTONDOWN:
        # Konversi koordinat klik di gambar display ke koordinat di gambar asli
        original_x_coord = int(x_clicked / display_scale_factor)
        original_y_coord = int(y_clicked / display_scale_factor)

        if current_interaction_mode == "dlt_selection" and len(pts_src_clicks_original_coords) < 4:
            pts_src_clicks_original_coords.append([original_x_coord, original_y_coord])
            # Gambar titik di gambar display (yang mungkin sudah di-resize)
            cv2.circle(display_image_for_interaction, (x_clicked, y_clicked), 7, (0, 255, 0), -1) # Hijau
            cv2.putText(display_image_for_interaction, f"P{len(pts_src_clicks_original_coords)}", (x_clicked + 10, y_clicked - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow(interactive_window_name, display_image_for_interaction)
            print(f"Titik DLT ke-{len(pts_src_clicks_original_coords)} (di gbr asli): ({original_x_coord}, {original_y_coord}) | Klik di display: ({x_clicked},{y_clicked})")
            if len(pts_src_clicks_original_coords) == 4:
                print("==> 4 Titik DLT (pts_src) selesai dipilih.")
                print("==> Tekan 's' pada keyboard (pastikan jendela gambar aktif) untuk lanjut.")

        elif current_interaction_mode == "scale_selection" and len(pts_scale_clicks_original_coords) < 2:
            pts_scale_clicks_original_coords.append([original_x_coord, original_y_coord]) # Simpan koordinat asli
            cv2.circle(display_image_for_interaction, (x_clicked, y_clicked), 7, (255, 0, 0), -1) # Biru
            cv2.putText(display_image_for_interaction, f"S{len(pts_scale_clicks_original_coords)}", (x_clicked + 10, y_clicked + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.imshow(interactive_window_name, display_image_for_interaction)
            print(f"Titik Skala ke-{len(pts_scale_clicks_on_original)} (di gbr asli): ({original_x_coord}, {original_y_coord}) | Klik di display: ({x_clicked},{y_clicked})")
            if len(pts_scale_clicks_original_coords) == 2:
                print("==> 2 Titik untuk pengukuran skala selesai dipilih.")
                print("==> Tekan 'c' pada keyboard (pastikan jendela gambar aktif) untuk menghitung pixels_per_meter.")

# --- Mulai Skrip Kalibrasi ---
if __name__ == '__main__':
    path_to_representative_frame_image = input("Masukkan path lengkap ke file gambar frame representatif: ")
    original_frame_from_file = cv2.imread(path_to_representative_frame_image)

    if original_frame_from_file is None:
        print(f"Error: Tidak bisa membaca gambar dari '{path_to_representative_frame_image}'. Pastikan path benar.")
        exit()

    # --- Resize Gambar untuk Tampilan ---
    orig_h, orig_w = original_frame_from_file.shape[:2]
    MAX_DISPLAY_WIDTH = 1200  # Atur lebar maksimum tampilan yang nyaman
    MAX_DISPLAY_HEIGHT = 700 # Atur tinggi maksimum tampilan yang nyaman

    scale_w = MAX_DISPLAY_WIDTH / orig_w
    scale_h = MAX_DISPLAY_HEIGHT / orig_h
    display_scale_factor = min(scale_w, scale_h, 1.0) # Jangan perbesar jika gambar sudah kecil

    if display_scale_factor < 1.0: # Hanya resize jika gambar terlalu besar
        display_w = int(orig_w * display_scale_factor)
        display_h = int(orig_h * display_scale_factor)
        resized_for_display = cv2.resize(original_frame_from_file, (display_w, display_h), interpolation=cv2.INTER_AREA)
        print(f"Gambar asli: {orig_w}x{orig_h}, ditampilkan sebagai: {display_w}x{display_h} (skala: {display_scale_factor:.3f})")
    else:
        resized_for_display = original_frame_from_file
        print(f"Gambar ditampilkan dalam ukuran asli: {orig_w}x{orig_h}")
    
    display_image_for_interaction = resized_for_display.copy()
    # --- Akhir Resize ---

    cv2.namedWindow(interactive_window_name)
    cv2.setMouseCallback(interactive_window_name, mouse_callback_for_calibration)

    print("\n--- PANDUAN KALIBRASI INTERAKTIF ---")
    print(f"Menampilkan gambar (mungkin di-resize untuk tampilan): {path_to_representative_frame_image}")
    print("\nTAHAP 1: PEMILIHAN 4 TITIK SUMBER UNTUK DLT (pts_src)")
    print(" > Klik pada 4 titik di permukaan jalan pada gambar.")
    print(" > Urutan penting: Titik Kiri Atas -> Kanan Atas -> Kiri Bawah -> Kanan Bawah dari area yang ingin 'diluruskan'.")
    print(" > Setelah 4 titik terpilih, tekan tombol 's' pada keyboard (pastikan jendela gambar aktif).")
    print(" > Tekan 'r' untuk mereset pilihan titik DLT jika salah.")
    print(" > Tekan 'q' kapan saja untuk keluar.")

    while True:
        cv2.imshow(interactive_window_name, display_image_for_interaction)
        keyboard_key = cv2.waitKey(20) & 0xFF

        if keyboard_key == ord('q'):
            print("Proses kalibrasi dihentikan oleh pengguna.")
            break
        
        if keyboard_key == ord('r') and current_interaction_mode == "dlt_selection":
            pts_src_clicks_original_coords = []
            display_image_for_interaction = resized_for_display.copy() # Reset gambar tampilan
            print("\nPilihan titik DLT direset. Silakan pilih ulang 4 titik.")

        if keyboard_key == ord('s') and current_interaction_mode == "dlt_selection" and len(pts_src_clicks_original_coords) == 4:
            final_pts_src = np.float32(pts_src_clicks_original_coords) # Ini sudah koordinat asli
            print("\n--- Hasil Pilihan pts_src (Koordinat di Gambar Asli) ---")
            print(f"pts_src = np.float32({final_pts_src.tolist()})")

            print("\nTAHAP 1B: PENENTUAN DIMENSI TARGET BIRD'S-EYE VIEW (pts_dst)")
            try:
                W_bev_target_str = input(" > Masukkan LEBAR pandangan atas (BEV) yang diinginkan dalam piksel (misal, 300): ")
                H_bev_target_str = input(" > Masukkan TINGGI pandangan atas (BEV) yang diinginkan dalam piksel (misal, 600): ")
                W_bev_target = int(W_bev_target_str)
                H_bev_target = int(H_bev_target_str)
                if W_bev_target <= 0 or H_bev_target <= 0: raise ValueError("Dimensi harus positif.")
            except ValueError:
                print("Input dimensi tidak valid. Menggunakan nilai default (Lebar=300, Tinggi=600).")
                W_bev_target = 300
                H_bev_target = 600

            final_output_rect_wh = (W_bev_target, H_bev_target)
            final_pts_dst = np.float32([
                [0, 0], [W_bev_target - 1, 0],
                [0, H_bev_target - 1], [W_bev_target - 1, H_bev_target - 1]
            ])
            print("\n--- Hasil Penentuan pts_dst dan output_rect_wh ---")
            print(f"pts_dst = np.float32({final_pts_dst.tolist()})")
            print(f"output_rect_wh = {final_output_rect_wh}")

            homography_matrix_M = cv2.getPerspectiveTransform(final_pts_src, final_pts_dst) # Menggunakan pts_src asli
            print("\nMatriks Homografi (M) berhasil dihitung.")

            print("\nTAHAP 2: PEMILIHAN 2 TITIK UNTUK SKALA JARAK")
            print(" > Sekarang, klik pada 2 titik di gambar ASLI (jendela yang sama).")
            print(" > Kedua titik ini harus menandai ujung-ujung objek yang panjang NYATA-nya (dalam meter) kamu ketahui.")
            print(" > Setelah 2 titik terpilih, tekan tombol 'c' pada keyboard.")
            print(" > Tekan 'x' untuk mereset pilihan titik skala jika salah.")
            current_interaction_mode = "scale_selection"

        if keyboard_key == ord('x') and current_interaction_mode == "scale_selection":
            pts_scale_clicks_original_coords = []
            # Gambar ulang, pertahankan titik DLT yang sudah digambar di display_image_for_interaction
            # Untuk simpelnya, kita reset display_image_for_interaction dan gambar ulang titik DLT
            display_image_for_interaction = resized_for_display.copy()
            for i_src, pt_src_orig in enumerate(pts_src_clicks_original_coords):
                # Konversi koordinat asli DLT ke koordinat display untuk digambar
                disp_x = int(pt_src_orig[0] * display_scale_factor)
                disp_y = int(pt_src_orig[1] * display_scale_factor)
                cv2.circle(display_image_for_interaction, (disp_x, disp_y), 7, (0, 255, 0), -1)
                cv2.putText(display_image_for_interaction, f"P{i_src+1}", (disp_x+10, disp_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0),2)
            print("\nPilihan titik skala direset. Silakan pilih ulang 2 titik.")

        if keyboard_key == ord('c') and current_interaction_mode == "scale_selection" and len(pts_scale_clicks_original_coords) == 2:
            if homography_matrix_M is None:
                print("Matriks Homografi M belum dihitung. Selesaikan Tahap 1 dulu (pilih 4 titik DLT lalu tekan 's').")
                continue

            # pts_scale_clicks_original_coords sudah berisi koordinat di gambar asli
            pts_scale_original_np_array = np.float32([pts_scale_clicks_original_coords]) 
            
            pts_scale_bev_np_array = cv2.perspectiveTransform(pts_scale_original_np_array, homography_matrix_M) # Transformasi dari koordinat asli
            
            bev_point1_coordinates = pts_scale_bev_np_array[0][0]
            bev_point2_coordinates = pts_scale_bev_np_array[0][1]
            distance_in_bev_pixels_value = np.linalg.norm(bev_point1_coordinates - bev_point2_coordinates)
            print(f"\nJarak objek di pandangan atas (BEV) adalah: {distance_in_bev_pixels_value:.2f} piksel.")

            try:
                real_world_length_str_value = input(" > Masukkan PANJANG NYATA objek tersebut dalam METER (gunakan titik '.' sebagai desimal, misal: 2.5): ")
                real_world_length_meters_value = float(real_world_length_str_value)
                if real_world_length_meters_value <= 0: raise ValueError("Panjang nyata harus positif.")
            except ValueError:
                print("Input panjang nyata tidak valid. Perhitungan skala dibatalkan. Tekan 'x' untuk pilih ulang titik skala, atau 'q' untuk keluar.")
                continue

            final_pixels_per_meter = distance_in_bev_pixels_value / real_world_length_meters_value
            print(f"\n--- pixels_per_meter yang dihitung: {final_pixels_per_meter:.4f} ---")
            
            print("\n===> PROSES KALIBRASI SELESAI! <===")
            print("Nilai-nilai di bawah ini siap untuk disalin ke dictionary 'SCENE_CALIBRATION' di kode Colab-mu.")
            print("\n------------------------------------------------------------------")
            scene_name_for_output = input("Masukkan Nama Scene untuk output ini (misal, Amplaz01): ")
            print(f"\"{scene_name_for_output}\": {{") # Menggunakan nama scene yang diinput pengguna
            print(f"    \"pts_src\": np.float32({final_pts_src.tolist()}),") # final_pts_src sudah koordinat asli
            print(f"    \"pts_dst\": np.float32({final_pts_dst.tolist()}),")
            print(f"    \"output_rect_wh\": {final_output_rect_wh},")
            print(f"    \"pixels_per_meter\": {final_pixels_per_meter:.4f}")
            print(f"}},")
            print("------------------------------------------------------------------")
            print("\nTekan 'q' untuk keluar dari skrip kalibrasi.")
            current_interaction_mode = "done"

    cv2.destroyAllWindows()

    if current_interaction_mode != "done":
        print("\nProses kalibrasi tidak diselesaikan sepenuhnya atau dibatalkan.")