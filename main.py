import json
import os
from datetime import datetime
from pathlib import Path
import threading
import time
import sys

# File untuk menyimpan data tugas
DATA_FILE = "tasks.json"

class TodoApp:
    def __init__(self):
        self.tasks = []
        self.load_tasks()
        self.alarm_threads = {}
    
    def load_tasks(self):
        """Memuat tugas dari file JSON"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.tasks = json.load(f)
        else:
            self.tasks = []
    
    def save_tasks(self):
        """Menyimpan tugas ke file JSON"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
    
    def add_task(self, nama_tugas, mata_pelajaran, deadline, guru):
        """Menambah tugas baru"""
        try:
            # Validasi format deadline (YYYY-MM-DD HH:MM)
            datetime.strptime(deadline, "%Y-%m-%d %H:%M")
        except ValueError:
            print("❌ Format deadline tidak valid! Gunakan format: YYYY-MM-DD HH:MM")
            return False
        
        task = {
            "id": len(self.tasks) + 1,
            "nama_tugas": nama_tugas,
            "mata_pelajaran": mata_pelajaran,
            "deadline": deadline,
            "guru": guru,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed": False
        }
        
        self.tasks.append(task)
        self.save_tasks()
        print(f"✅ Tugas '{nama_tugas}' berhasil ditambahkan!")
        
        # Mulai alarm untuk tugas ini
        self.start_alarm(task)
        return True
    
    def view_tasks(self):
        """Menampilkan semua tugas dalam format tabel"""
        if not self.tasks:
            print("\n📋 Belum ada tugas. Tambahkan tugas baru!")
            return
        
        print("\n" + "="*130)
        print("📚 DAFTAR TUGAS SEKOLAH")
        print("="*130)
        
        # Header tabel
        header = f"{'ID':<4} | {'Status':<10} | {'Nama Tugas':<18} | {'Mata Pelajaran':<16} | {'Guru':<14} | {'Deadline':<19} | {'Sisa Waktu':<12}"
        print(header)
        print("-"*130)
        
        # Isi tabel
        for task in self.tasks:
            status = "✅ Selesai" if task["completed"] else "⏳ Pending"
            
            # Hitung sisa waktu
            try:
                deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                sisa = deadline - datetime.now()
                if sisa.total_seconds() > 0:
                    days = sisa.days
                    hours = (sisa.seconds // 3600) % 24
                    mins = (sisa.seconds // 60) % 60
                    sisa_waktu = f"{days}d {hours}h {mins}m"
                else:
                    sisa_waktu = "TERLEWAT"
            except:
                sisa_waktu = "Tidak Valid"
            
            # Batasi panjang teks
            nama_tugas = task['nama_tugas'][:18]
            mata_pelajaran = task['mata_pelajaran'][:16]
            guru = task['guru'][:14]
            
            print(f"{task['id']:<4} | {status:<10} | {nama_tugas:<18} | {mata_pelajaran:<16} | "
                  f"{guru:<14} | {task['deadline']:<19} | {sisa_waktu:<12}")
        
        print("="*130 + "\n")
    
    def mark_completed(self, task_id):
        """Menandai tugas sebagai selesai"""
        for task in self.tasks:
            if task["id"] == task_id:
                task["completed"] = True
                self.save_tasks()
                print(f"✅ Tugas '{task['nama_tugas']}' ditandai selesai!")
                return True
        
        print("❌ Tugas tidak ditemukan!")
        return False
    
    def delete_task(self, task_id):
        """Menghapus tugas"""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                nama = task["nama_tugas"]
                self.tasks.pop(i)
                self.save_tasks()
                print(f"🗑️  Tugas '{nama}' berhasil dihapus!")
                return True
        
        print("❌ Tugas tidak ditemukan!")
        return False
    
    def alarm_checker(self, task):
        """Thread untuk mengecek dan mengingatkan deadline"""
        task_id = task["id"]
        last_reminder = None
        
        while task_id in self.alarm_threads:
            try:
                deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                now = datetime.now()
                sisa = deadline - now
                
                # Reload task untuk cek status terbaru
                for t in self.tasks:
                    if t["id"] == task_id:
                        task = t
                        break
                
                # Jika tugas sudah selesai, hentikan alarm
                if task["completed"]:
                    break
                
                # Jika deadline sudah berlalu
                if sisa.total_seconds() < 0:
                    if last_reminder != "LEWAT":
                        self.trigger_alarm(task)
                        last_reminder = "LEWAT"
                
                # Pengingat 24 jam sebelumnya
                elif 86400 <= sisa.total_seconds() < 86460:  # 24 jam
                    if last_reminder != "24JAM":
                        print(f"\n⏰ PENGINGAT: Tugas '{task['nama_tugas']}' tinggal 24 jam lagi!")
                        last_reminder = "24JAM"
                
                # Pengingat 12 jam sebelumnya
                elif 43200 <= sisa.total_seconds() < 43260:  # 12 jam
                    if last_reminder != "12JAM":
                        print(f"\n🔔 PENGINGAT: Tugas '{task['nama_tugas']}' tinggal 12 jam lagi!")
                        last_reminder = "12JAM"
                
                # Pengingat 1 jam sebelumnya
                elif 3600 <= sisa.total_seconds() < 3660:  # 1 jam
                    if last_reminder != "1JAM":
                        print(f"\n🔔🔔 PENGINGAT MENDESAK: Tugas '{task['nama_tugas']}' tinggal 1 jam lagi!")
                        last_reminder = "1JAM"
                
                # Cek setiap 10 detik untuk pengingat yang akurat
                time.sleep(10)
                
            except Exception as e:
                print(f"❌ Error pada alarm: {e}")
                break
    
    def trigger_alarm(self, task):
        """Memicu alarm saat deadline tiba"""
        print("\n" + "🚨"*40)
        print("⚠️  ALARM DEADLINE! ⚠️")
        print("🚨"*40)
        print(f"\n📌 Tugas: {task['nama_tugas']}")
        print(f"📚 Mata Pelajaran: {task['mata_pelajaran']}")
        print(f"👨‍🏫 Guru: {task['guru']}")
        print(f"⏰ Deadline: {task['deadline']}")
        print(f"\n⏱️  Deadline Anda telah tiba! Segera selesaikan tugas ini!\n")
        print("🚨"*40 + "\n")
        
        # Mainkan system beep sebagai notifikasi
        for _ in range(3):
            print("\a")  # System beep
            time.sleep(0.5)
    
    def start_alarm(self, task):
        """Mulai thread untuk monitoring deadline"""
        task_id = task["id"]
        self.alarm_threads[task_id] = True
        
        thread = threading.Thread(target=self.alarm_checker, args=(task,), daemon=True)
        thread.start()
        print(f"🔔 Pengingat deadline aktif untuk tugas: {task['nama_tugas']}")
    
    def start_all_alarms(self):
        """Mulai alarm untuk semua tugas yang belum selesai"""
        for task in self.tasks:
            if not task["completed"]:
                self.start_alarm(task)
    
    def show_upcoming_deadlines(self):
        """Menampilkan tugas yang mendekati deadline dalam format tabel"""
        if not self.tasks:
            print("\n📋 Belum ada tugas!")
            return
        
        print("\n" + "="*130)
        print("⏰ DEADLINE YANG MENDEKATI")
        print("="*130)
        
        upcoming = []
        for task in self.tasks:
            if not task["completed"]:
                try:
                    deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                    sisa = deadline - datetime.now()
                    if sisa.total_seconds() >= 0:
                        upcoming.append((task, sisa))
                except:
                    pass
        
        upcoming.sort(key=lambda x: x[1].total_seconds())
        
        if not upcoming:
            print("✅ Tidak ada tugas yang mendekati deadline!")
        else:
            header = f"{'ID':<4} | {'Nama Tugas':<18} | {'Mata Pelajaran':<16} | {'Guru':<14} | {'Deadline':<19} | {'Sisa Waktu':<15}"
            print(header)
            print("-"*130)
            
            for task, sisa in upcoming:
                days = sisa.days
                hours = (sisa.seconds // 3600) % 24
                mins = (sisa.seconds // 60) % 60
                sisa_waktu = f"{days}d {hours}h {mins}m"
                
                nama_tugas = task['nama_tugas'][:18]
                mata_pelajaran = task['mata_pelajaran'][:16]
                guru = task['guru'][:14]
                
                print(f"{task['id']:<4} | {nama_tugas:<18} | {mata_pelajaran:<16} | "
                      f"{guru:<14} | {task['deadline']:<19} | {sisa_waktu:<15}")
        
        print("="*130 + "\n")
    
    def run(self):
        """Menjalankan aplikasi"""
        print("\n" + "="*50)
        print("📚 APLIKASI TODO LIST TUGAS SEKOLAH 📚")
        print("="*50)
        
        # Mulai alarm untuk tugas yang ada
        self.start_all_alarms()
        
        while True:
            print("\n" + "="*50)
            print("📋 MENU UTAMA:")
            print("="*50)
            print("1. ➕ Tambah Tugas")
            print("2. 📂 Lihat Semua Tugas")
            print("3. ⏰ Lihat Deadline Mendekati")
            print("4. ✅ Tandai Tugas Selesai")
            print("5. 🗑️  Hapus Tugas")
            print("6. 🚪 Keluar")
            print("="*50)
            
            pilihan = input("\nPilih menu (1-6): ").strip()
            
            if pilihan == "1":
                print("\n" + "-"*50)
                print("--- Tambah Tugas Baru ---")
                print("-"*50)
                nama_tugas = input("Nama tugas: ").strip()
                mata_pelajaran = input("Mata pelajaran: ").strip()
                deadline = input("Deadline (format: YYYY-MM-DD HH:MM): ").strip()
                guru = input("Nama guru: ").strip()
                
                if nama_tugas and mata_pelajaran and deadline and guru:
                    self.add_task(nama_tugas, mata_pelajaran, deadline, guru)
                else:
                    print("❌ Semua field harus diisi!")
            
            elif pilihan == "2":
                self.view_tasks()
            
            elif pilihan == "3":
                self.show_upcoming_deadlines()
            
            elif pilihan == "4":
                self.view_tasks()
                try:
                    task_id = int(input("Masukkan ID tugas yang selesai: "))
                    self.mark_completed(task_id)
                except ValueError:
                    print("❌ ID harus berupa angka!")
            
            elif pilihan == "5":
                self.view_tasks()
                try:
                    task_id = int(input("Masukkan ID tugas untuk dihapus: "))
                    self.delete_task(task_id)
                except ValueError:
                    print("❌ ID harus berupa angka!")
            
            elif pilihan == "6":
                print("\n👋 Terima kasih! Selesaikan tugas-tugas Anda dengan baik!")
                break
            
            else:
                print("❌ Menu tidak valid! Pilih menu 1-6")


if __name__ == "__main__":
    app = TodoApp()
    app.run()
