from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import AsyncImage
from kivy.clock import Clock
from kivy.uix.popup import Popup
import yt_dlp
import os
import threading
from android.permissions import request_permissions, Permission
from android.storage import primary_external_storage_path


class YouTubeDownloaderApp(App):
    def build(self):
        # Solicitar permisos de almacenamiento
        request_permissions([
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.INTERNET
        ])
        
        # Directorios de descarga en Android
        try:
            self.external_path = primary_external_storage_path()
            self.video_dir = os.path.join(self.external_path, "Download", "Videos")
            self.audio_dir = os.path.join(self.external_path, "Download", "Audios")
        except:
            # Fallback para testing
            self.video_dir = "Videos"
            self.audio_dir = "Audios"
        
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Layout principal
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Título
        title = Label(
            text='YouTube Downloader',
            size_hint_y=None,
            height='48dp',
            font_size='20sp',
            color=(1, 1, 1, 1)
        )
        main_layout.add_widget(title)
        
        # Campo URL
        self.url_input = TextInput(
            hint_text='Pega la URL del video aquí...',
            multiline=False,
            size_hint_y=None,
            height='48dp'
        )
        self.url_input.bind(text=self.on_url_change)
        main_layout.add_widget(self.url_input)
        
        # Imagen thumbnail
        self.thumbnail = AsyncImage(
            source='',
            size_hint_y=None,
            height='200dp'
        )
        main_layout.add_widget(self.thumbnail)
        
        # Título del video
        self.video_title = Label(
            text='',
            text_size=(None, None),
            size_hint_y=None,
            height='60dp',
            valign='middle'
        )
        main_layout.add_widget(self.video_title)
        
        # Botones de formato
        format_layout = BoxLayout(size_hint_y=None, height='48dp', spacing=10)
        self.video_btn = ToggleButton(text='Video', group='format', state='down')
        self.audio_btn = ToggleButton(text='Audio', group='format')
        self.video_btn.bind(state=self.on_format_change)
        self.audio_btn.bind(state=self.on_format_change)
        
        format_layout.add_widget(self.video_btn)
        format_layout.add_widget(self.audio_btn)
        main_layout.add_widget(format_layout)
        
        # Selector de calidad
        self.quality_spinner = Spinner(
            text='Selecciona calidad',
            values=[],
            size_hint_y=None,
            height='48dp'
        )
        main_layout.add_widget(self.quality_spinner)
        
        # Botón descargar
        self.download_btn = Button(
            text='Descargar',
            size_hint_y=None,
            height='48dp',
            background_color=(0.2, 0.6, 1, 1)
        )
        self.download_btn.bind(on_press=self.download_video)
        main_layout.add_widget(self.download_btn)
        
        # Estado
        self.status_label = Label(
            text='Listo para descargar',
            size_hint_y=None,
            height='48dp'
        )
        main_layout.add_widget(self.status_label)
        
        self.video_info = None
        return main_layout
    
    def on_url_change(self, instance, value):
        if 'youtube.com' in value or 'youtu.be' in value:
            self.status_label.text = 'Cargando información...'
            threading.Thread(target=self.fetch_video_info, args=(value.strip(),), daemon=True).start()
    
    def fetch_video_info(self, url):
        try:
            ydl_opts = {
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.video_info = {
                    "title": info.get("title", "Video sin título"),
                    "thumbnail": info.get("thumbnail", ""),
                    "formats": info.get("formats", [])
                }
                Clock.schedule_once(self.update_video_info)
        except Exception as e:
            self.video_info = None
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'Error: {str(e)[:50]}...'))
    
    def update_video_info(self, dt):
        if self.video_info:
            self.video_title.text = self.video_info.get("title", "")[:100]
            self.thumbnail.source = self.video_info.get("thumbnail", "")
            self.update_quality_options()
            self.status_label.text = 'Información cargada ✓'
        else:
            self.status_label.text = 'Error al cargar información'
    
    def on_format_change(self, instance, value):
        if value == 'down':
            self.update_quality_options()
    
    def update_quality_options(self):
        if not self.video_info:
            return
        
        formats = self.video_info["formats"]
        quality_options = []
        seen_qualities = set()
        
        is_video = self.video_btn.state == 'down'
        
        if is_video:
            for fmt in formats:
                height = fmt.get("height")
                if height and height > 0:
                    quality = f"{height}p"
                    if quality not in seen_qualities:
                        quality_options.append((quality, height))
                        seen_qualities.add(quality)
        else:
            for fmt in formats:
                abr = fmt.get("abr")
                if abr and fmt.get("acodec") and fmt["acodec"] != "none":
                    quality = f"{int(abr)}kbps"
                    if quality not in seen_qualities:
                        quality_options.append((quality, int(abr)))
                        seen_qualities.add(quality)
        
        # Ordenar por calidad
        quality_options.sort(key=lambda x: x[1], reverse=True)
        self.quality_spinner.values = [q[0] for q in quality_options]
        
        if quality_options:
            self.quality_spinner.text = quality_options[0][0]
    
    def download_video(self, instance):
        if not self.url_input.text.strip():
            self.show_popup("Error", "Por favor ingresa una URL")
            return
        
        if not self.quality_spinner.text or self.quality_spinner.text == 'Selecciona calidad':
            self.show_popup("Error", "Por favor selecciona una calidad")
            return
        
        self.status_label.text = 'Iniciando descarga...'
        self.download_btn.disabled = True
        
        threading.Thread(target=self.perform_download, daemon=True).start()
    
    def perform_download(self):
        try:
            is_video = self.video_btn.state == 'down'
            folder = self.video_dir if is_video else self.audio_dir
            
            if is_video:
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                }
            else:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', '0%')
                    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'Descargando {percent}'))
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url_input.text.strip()])
            
            Clock.schedule_once(lambda dt: self.download_complete(True))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.download_complete(False, str(e)))
    
    def download_complete(self, success, error_msg=None):
        self.download_btn.disabled = False
        if success:
            self.status_label.text = '✅ Descarga completada!'
            format_type = "Video" if self.video_btn.state == 'down' else "Audio"
            folder = self.video_dir if self.video_btn.state == 'down' else self.audio_dir
            self.show_popup("Éxito", f"{format_type} descargado en:\n{folder}")
        else:
            self.status_label.text = f'❌ Error en descarga'
            self.show_popup("Error", f"Error: {str(error_msg)[:100]}...")
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message, text_size=(250, None), halign='center'))
        
        close_btn = Button(text='Cerrar', size_hint_y=None, height='40dp')
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, 0.6),
            auto_dismiss=False
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    YouTubeDownloaderApp().run()
