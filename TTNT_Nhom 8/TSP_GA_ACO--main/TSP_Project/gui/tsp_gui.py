import sys
import csv
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Import logic
from utils.tsp_utils import generate_cities
from algorithms.ga import GA
from algorithms.aco import ACO

# --- THEME ---
THEME = {
    "bg_main": "#121212",       
    "bg_card": "#1e1e1e",       
    "accent_ga": "#00d4ff",     
    "accent_aco": "#ff007f",    
    "text_main": "#ffffff",     
    "text_dim": "#aaaaaa",      
    "btn_run": "#00C853",       
    "btn_stop": "#D50000",      
    "btn_pause": "#FFAB00"      
}

class ModernSpinBox(QSpinBox):
    def __init__(self):
        super().__init__()
        self.setRange(5, 100)
        self.setValue(20)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QSpinBox {{
                background-color: {THEME['bg_main']};
                color: {THEME['accent_ga']};
                border: 2px solid {THEME['bg_card']};
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }}
            QSpinBox:focus {{
                border: 2px solid {THEME['accent_ga']};
            }}
        """)

class TSPApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Solver Dashboard | GA Chasing ACO")
        self.resize(1366, 768)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet(f"background-color: {THEME['bg_main']}; color: {THEME['text_main']};")
        self.cities = []
        self._build_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.stepupdate)
        self.showMaximized()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # === SIDEBAR ===
        sidebar = QFrame()
        sidebar.setFixedWidth(320)
        sidebar.setStyleSheet(f"background-color: {THEME['bg_card']}; border-radius: 15px;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 30)
        sidebar_layout.setSpacing(20)

        # Header
        lbl_title = QLabel("TSP SOLVER")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: 900; letter-spacing: 2px; color: {THEME['text_main']}; border: none;")
        
        self.city_spin = ModernSpinBox()

        # Buttons
        self.run_btn = self._create_btn("KHỞI CHẠY (RACE)", THEME['btn_run'])
        self.run_btn.clicked.connect(self.run)
        self.pause_btn = self._create_btn("TẠM DỪNG", THEME['btn_pause'])
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.stop_btn = self._create_btn("KẾT THÚC", THEME['btn_stop'])
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.force_stop)

        # Slider
        self.lbl_speed_display = QLabel("Tốc độ: 10x (Bình thường)")
        self.lbl_speed_display.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {THEME['accent_ga']}; border: none; margin-top: 10px;")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100) 
        self.speed_slider.setValue(10)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        self.speed_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ border: 1px solid {THEME['bg_main']}; height: 8px; background: {THEME['bg_main']}; margin: 2px 0; border-radius: 4px; }}
            QSlider::handle:horizontal {{ background: {THEME['accent_ga']}; width: 18px; height: 18px; margin: -7px 0; border-radius: 9px; }}
        """)

        # STATS
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"background-color: {THEME['bg_main']}; border-radius: 10px; border: none;")
        stats_layout = QVBoxLayout(stats_frame)
        
        # CPU Time Label
        self.lbl_cpu_ga = QLabel("GA CPU: --")
        self.lbl_cpu_aco = QLabel("ACO CPU: --")
        
        # Real Time Label
        self.lbl_real_ga = QLabel("GA Time: --")
        self.lbl_real_aco = QLabel("ACO Time: --")
        
        for lbl, color in [(self.lbl_cpu_ga, THEME['accent_ga']), (self.lbl_cpu_aco, THEME['accent_aco'])]:
            lbl.setStyleSheet(f"font-family: 'Consolas'; font-size: 11px; color: {color}; border: none;")
            lbl.setAlignment(Qt.AlignCenter)
            stats_layout.addWidget(lbl)
            
        stats_layout.addSpacing(10)

        for lbl, color in [(self.lbl_real_ga, THEME['accent_ga']), (self.lbl_real_aco, THEME['accent_aco'])]:
            lbl.setStyleSheet(f"font-family: 'Consolas'; font-size: 13px; font-weight: bold; color: {color}; border: none;")
            lbl.setAlignment(Qt.AlignCenter)
            stats_layout.addWidget(lbl)

        self.lbl_status = QLabel("READY")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {THEME['text_dim']}; margin-top: 10px; border: none;")
        stats_layout.addWidget(self.lbl_status)

        self.save_btn = QPushButton("Xuất dữ liệu CSV")
        self.save_btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {THEME['text_dim']}; border: 1px solid {THEME['text_dim']}; border-radius: 8px; padding: 8px; }} QPushButton:hover {{ color: white; border: 1px solid white; }}")
        self.save_btn.clicked.connect(self.save_csv)

        sidebar_layout.addWidget(lbl_title)
        sidebar_layout.addWidget(QLabel("SỐ LƯỢNG THÀNH PHỐ"))
        sidebar_layout.addWidget(self.city_spin)
        sidebar_layout.addWidget(self.run_btn)
        sidebar_layout.addWidget(self.pause_btn)
        sidebar_layout.addWidget(self.stop_btn)
        sidebar_layout.addWidget(self.lbl_speed_display)
        sidebar_layout.addWidget(self.speed_slider)
        sidebar_layout.addWidget(stats_frame)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.save_btn)

        # GRAPHS
        graphs_area = QWidget()
        graphs_layout = QHBoxLayout(graphs_area)
        self.panel_ga, self.fig_ga, self.can_ga = self._create_graph_panel("GENETIC ALGORITHM", THEME['accent_ga'])
        self.panel_aco, self.fig_aco, self.can_aco = self._create_graph_panel("ANT COLONY", THEME['accent_aco'])
        graphs_layout.addWidget(self.panel_ga)
        graphs_layout.addWidget(self.panel_aco)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(graphs_area, 1)

    def _create_btn(self, text, color):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background-color: {color}; color: white; border: none; border-radius: 8px; padding: 12px; font-weight: bold; }} QPushButton:hover {{ background-color: {color}dd; margin-top: 2px; }} QPushButton:disabled {{ background-color: #333; color: #555; }}")
        return btn

    def _create_graph_panel(self, title, color):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {THEME['bg_card']}; border-radius: 15px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 15, 0, 5) 
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px; letter-spacing: 1px; border: none;")
        fig = Figure(facecolor=THEME['bg_card'])
        canvas = FigureCanvasQTAgg(fig)
        canvas.setStyleSheet("background-color: transparent; border-radius: 10px;")
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(lbl)
        layout.addWidget(canvas, 1)
        return frame, fig, canvas

    def update_speed_label(self, value):
        text = "(Chậm)" if value < 10 else "(Bình thường)" if value < 30 else "(Nhanh)" if value < 80 else "(Tối đa)"
        self.lbl_speed_display.setText(f"Tốc độ: {value}x {text}")

    # Logic chạy
    def run(self):
        if self.timer.isActive(): return
        try:
            self.cities = generate_cities(self.city_spin.value(), width=1000, height=1000)
        except: return

        COMMON_POP = 50
        
        # 1. ACO: Chạy chuẩn 500 vòng
        self.aco = ACO(self.cities, n_ants=COMMON_POP, n_iter=500, patience=500)

        # 2. GA: Chạy vô tận đến khi tìm ra đường ngắn nhất
        # Mục đích: Bắt buộc nó phải chạy cho đến khi đuổi kịp ACO
        self.ga = GA(self.cities, pop_size=COMMON_POP, generations=1000000, patience=999999)

        self.ga_gen = self.ga.run_stepwise()
        self.aco_gen = self.aco.run_stepwise()

        self.ga_done = False; self.aco_done = False
        self.ga_step = 0; self.aco_step = 0
        
        self.ga_cpu_total = 0.0; self.aco_cpu_total = 0.0
        self.start_time_wall = time.time()
        self.ga_time_best = 0.0; self.aco_time_best = 0.0
        
        # Reset khoảng cách về Vô cùng
        self.current_dist_ga = float('inf')
        self.current_dist_aco = float('inf')

        self.lbl_status.setText("SIMULATION RUNNING...")
        self.lbl_status.setStyleSheet(f"color: {THEME['accent_ga']}; border: none; font-weight: bold;")
        self.run_btn.setEnabled(False); self.pause_btn.setEnabled(True); self.stop_btn.setEnabled(True); self.city_spin.setEnabled(False)
        self.timer.start(16)

    def force_stop(self):
        self.timer.stop()
        self.ga_done = True; self.aco_done = True
        self.finish_run()
        QMessageBox.information(self, "Stop", "Đã dừng chương trình!")

    def toggle_pause(self):
        if self.timer.isActive():
            self.timer.stop(); self.pause_btn.setText("TIẾP TỤC"); self.lbl_status.setText("PAUSED")
        else:
            self.timer.start(16); self.pause_btn.setText("TẠM DỪNG"); self.lbl_status.setText("RUNNING...")

    def stepupdate(self):
        steps_limit = self.speed_slider.value()
        current_wall_time = time.time() - self.start_time_wall

        # Xử lý ACO
        if not self.aco_done:
            t_cpu_start = time.perf_counter()
            steps_run = 0
            while steps_run < steps_limit:
                try:
                    it, path, dist, improved = next(self.aco_gen)
                    self.aco_step = it
                    self.current_path_aco = path
                    self.current_dist_aco = dist
                    steps_run += 1
                    if improved: 
                        self.aco_time_best = current_wall_time
                except StopIteration:
                    self.aco_done = True
                    break
            self.aco_cpu_total += (time.perf_counter() - t_cpu_start)
            if hasattr(self, 'current_path_aco'):
                self.draw_graph(self.fig_aco, self.can_aco, self.current_path_aco, self.current_dist_aco, THEME['accent_aco'], f"ITER: {self.aco_step}")

        # Xử lý GA
        if not self.ga_done:
            t_cpu_start = time.perf_counter()
            steps_run = 0
            while steps_run < steps_limit:
                try:
                    gen, path, dist, improved = next(self.ga_gen)
                    self.ga_step = gen
                    self.current_path_ga = path
                    self.current_dist_ga = dist
                    steps_run += 1
                    if improved: 
                        self.ga_time_best = current_wall_time

                    # Chỉ dừng khi ACO đã xong
                    if self.aco_done:
                        # CHO PHÉP SAI SỐ: Nếu GA chỉ kém ACO dưới 0.5 đơn vị khoảng cách -> COI NHƯ BẰNG NHAU -> DỪNG
                        # Điều này giúp tránh việc GA bị kẹt vì 0.00001 chênh lệch
                        TOLERANCE = 0.5 
                        
                        if self.current_dist_ga <= (self.current_dist_aco + TOLERANCE):
                            self.ga_done = True
                            self.lbl_status.setText("GA ĐÃ ĐUỔI KỊP (SẤP XỈ)!")
                            break
                        
                except StopIteration:
                    self.ga_done = True
                    break
            
            self.ga_cpu_total += (time.perf_counter() - t_cpu_start)
            if hasattr(self, 'current_path_ga'):
                self.draw_graph(self.fig_ga, self.can_ga, self.current_path_ga, self.current_dist_ga, THEME['accent_ga'], f"GEN: {self.ga_step}")

        # --- UPDATE LABELS ---
        self.lbl_cpu_ga.setText(f"GA CPU: {self.ga_cpu_total:.3f}s")
        self.lbl_cpu_aco.setText(f"ACO CPU: {self.aco_cpu_total:.3f}s")
        
        self.lbl_real_aco.setText(f"Best Found: {self.aco_time_best:.1f}s")

        if not self.ga_done and self.aco_done:
            diff = self.current_dist_ga - self.current_dist_aco
            self.lbl_real_ga.setText(f"ĐANG ĐUỔI THEO... (+{diff:.1f})")
            self.lbl_real_ga.setStyleSheet(f"color: #FF5555; font-family: 'Consolas'; font-size: 13px; font-weight: bold;")
        else:
            self.lbl_real_ga.setText(f"Best Found: {self.ga_time_best:.1f}s")
            self.lbl_real_ga.setStyleSheet(f"color: {THEME['accent_ga']}; font-family: 'Consolas'; font-size: 13px; font-weight: bold;")

        # Chỉ dừng khi cả 2 cùng xong
        if self.ga_done and self.aco_done:
            self.timer.stop()
            self.finish_run()

    def finish_run(self):
        self.run_btn.setEnabled(True); self.pause_btn.setEnabled(False); self.stop_btn.setEnabled(False); self.city_spin.setEnabled(True)
        self.lbl_status.setText("COMPLETED")
        self.lbl_status.setStyleSheet(f"color: {THEME['btn_run']}; border: none; font-weight: bold;")
        
        dist_ga = self.current_dist_ga
        dist_aco = self.current_dist_aco
        
        # So sánh thời gian
        diff_time = abs(self.ga_time_best - self.aco_time_best)
        
        # Vì ta ép GA chạy đến khi bằng ACO, nên Chất lượng coi như tương đương (hoặc GA tốt hơn xíu)
        # Ta sẽ so sánh xem GA mất bao lâu để đuổi kịp
        msg = f"⏱ GA đã mất thêm {diff_time:.2f}s để đuổi kịp ACO!"
        if self.ga_time_best < self.aco_time_best:
            msg = f"🚀 Bất ngờ chưa! GA tìm ra sớm hơn ACO {diff_time:.2f}s!"

        QMessageBox.information(self, "KẾT QUẢ", 
            f"ĐÃ HOÀN THÀNH!\n\n"
            f"Kết quả cuối cùng:\n"
            f"• GA: {dist_ga:.2f} (Tìm thấy ở giây thứ {self.ga_time_best:.1f})\n"
            f"• ACO: {dist_aco:.2f} (Tìm thấy ở giây thứ {self.aco_time_best:.1f})\n\n"
            f"-> {msg}"
        )

    def draw_graph(self, fig, canvas, path, dist, color, label_text):
        fig.clear()
        fig.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.08)
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME['bg_card'])

        xs = [self.cities[i][0] for i in path] + [self.cities[path[0]][0]]
        ys = [self.cities[i][1] for i in path] + [self.cities[path[0]][1]]

        ax.plot(xs, ys, color=color, linewidth=2, alpha=0.9, zorder=1)
        ax.plot(xs, ys, color=color, linewidth=6, alpha=0.2, zorder=1) 
        ax.scatter([c[0] for c in self.cities], [c[1] for c in self.cities], c='white', s=25, alpha=0.7, zorder=2)
        
        start = self.cities[path[0]]
        ax.scatter([start[0]], [start[1]], c=THEME['btn_run'], s=100, marker='*', zorder=3)
        ax.grid(True, color='#444444', linestyle='--', linewidth=0.5, alpha=0.4)
        ax.tick_params(axis='both', colors='#888888', labelsize=9)
        for spine in ax.spines.values(): spine.set_edgecolor('#333333')

        ax.text(0.98, 0.02, f"DIST: {dist:.1f}", transform=ax.transAxes, 
                color=color, fontsize=12, fontweight='bold', ha='right', va='bottom',
                bbox=dict(facecolor=THEME['bg_main'], alpha=0.7, edgecolor=color, boxstyle='round,pad=0.3'))
        
        ax.text(0.02, 0.98, label_text, transform=ax.transAxes, 
                color="white", fontsize=10, fontweight='bold', ha='left', va='top',
                bbox=dict(facecolor="#333", alpha=0.6, edgecolor="none", boxstyle='round,pad=0.2'))

        canvas.draw()

    def save_csv(self):
        try:
            with open("ga_history.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Generation", "BestDistance"])
                writer.writerows(self.ga.history)
            with open("aco_history.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Iteration", "BestDistance"])
                writer.writerows(self.aco.history)
            QMessageBox.information(self, "Export", "Xuất file thành công!")
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TSPApp()
    window.show()
    sys.exit(app.exec_())