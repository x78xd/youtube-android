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
from kivy.uix.progressbar import ProgressBar
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
import yt_dlp
import os
import threading

# Importar APIs de Android de manera opcional
try:
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False

class YouTubeDownloaderApp(App):
    def build(self):
        # Solicitar permisos de almacenamiento solo en Android
        if ANDROID_AVAILABLE:
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.INTERNET
            ])
        
        # Directorios de descarga
        try:
            if ANDROID_AVAILABLE:
                self.external_path = primary_external_storage_path()
                self.video_dir = os.path.join(self.external_path, "Download", "Videos")
                self.audio_dir = os.path.join(self.external_path, "Download", "Audios")
            else:
                # Para Windows/Linux/Mac
                self.video_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Videos")
                self.audio_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Audios")
        except:
            # Fallback para cualquier sistema
            self.video_dir = "Videos"
            self.audio_dir = "Audios"
        
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Layout principal con fondo degradado
        main_layout = FloatLayout()
        
        # Fondo degradado
        with main_layout.canvas.before:
            Color(0.08, 0.08, 0.15, 1)  # Azul oscuro profundo
            self.bg_rect = RoundedRectangle(pos=(0, 0), size=(1000, 1000))
        
        # Container principal centrado
        container = BoxLayout(
            orientation='vertical',
            padding=[dp(25), dp(40), dp(25), dp(25)],
            spacing=dp(25),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(0.95, 0.95)
        )
        
        # HEADER - Título elegante
        header_layout = FloatLayout(size_hint_y=None, height=dp(100))
        with header_layout.canvas.before:
            Color(0.12, 0.12, 0.2, 0.9)
            self.header_rect = RoundedRectangle(radius=[15])
            Color(0.2, 0.6, 1, 0.3)
            self.header_border = Line(width=2, rounded_rectangle=[0, 0, 100, 100, 15])
        
        title = Label(
            text='[size=36][b][color=ffffff]YouTube[/color][/b][/size]\n[size=20][color=4da6ff]Downloader Pro[/color][/size]',
            markup=True,
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        header_layout.add_widget(title)
        container.add_widget(header_layout)
        
        # SECCIÓN URL - Con estilo moderno
        url_section = FloatLayout(size_hint_y=None, height=dp(80))
        with url_section.canvas.before:
            Color(0.15, 0.15, 0.22, 1)
            self.url_rect = RoundedRectangle(radius=[12])
            Color(0.3, 0.3, 0.4, 0.5)
            self.url_border = Line(width=1, rounded_rectangle=[0, 0, 100, 100, 12])
        
        url_container = BoxLayout(
            orientation='horizontal',
            padding=[dp(20), dp(15)],
            spacing=dp(15),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(1, None),
            height=dp(50)
        )
        
        # Icono URL
        url_icon = Label(
            text='🔗',
            size_hint_x=None,
            width=dp(40),
            font_size='24sp',
            color=(0.2, 0.6, 1, 1)
        )
        
        # Input URL estilizado
        self.url_input = TextInput(
            hint_text='Pega la URL de YouTube aquí...',
            multiline=False,
            background_color=(0.2, 0.2, 0.25, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.2, 0.6, 1, 1),
            font_size='16sp',
            padding=[dp(15), dp(10)]
        )
        self.url_input.bind(text=self.on_url_change)
        
        url_container.add_widget(url_icon)
        url_container.add_widget(self.url_input)
        url_section.add_widget(url_container)
        container.add_widget(url_section)
        
        # SECCIÓN VIDEO INFO - Card elegante
        info_section = FloatLayout(size_hint_y=None, height=dp(280))
        with info_section.canvas.before:
            Color(0.15, 0.15, 0.22, 1)
            self.info_rect = RoundedRectangle(radius=[12])
            Color(0.3, 0.3, 0.4, 0.3)
            self.info_border = Line(width=1, rounded_rectangle=[0, 0, 100, 100, 12])
        
        info_layout = BoxLayout(
            orientation='vertical',
            padding=[dp(20), dp(15)],
            spacing=dp(15),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(1, 1)
        )
        
        # Thumbnail con bordes redondeados
        thumbnail_container = FloatLayout(size_hint_y=None, height=dp(140))
        with thumbnail_container.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            self.thumb_rect = RoundedRectangle(radius=[10])
        
        self.thumbnail = AsyncImage(
            source='',
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(0.95, 0.9)
        )
        thumbnail_container.add_widget(self.thumbnail)
        info_layout.add_widget(thumbnail_container)
        
        # Título del video estilizado
        self.video_title = Label(
            text='[color=cccccc]Selecciona un video para ver la información[/color]',
            markup=True,
            text_size=(None, None),
            halign='center',
            valign='middle',
            font_size='16sp',
            size_hint_y=None,
            height=dp(60)
        )
        info_layout.add_widget(self.video_title)
        
        info_section.add_widget(info_layout)
        container.add_widget(info_section)
        
        # SECCIÓN CONTROLES - Botones modernos
        controls_section = FloatLayout(size_hint_y=None, height=dp(160))
        with controls_section.canvas.before:
            Color(0.15, 0.15, 0.22, 1)
            self.controls_rect = RoundedRectangle(radius=[12])
            Color(0.3, 0.3, 0.4, 0.3)
            self.controls_border = Line(width=1, rounded_rectangle=[0, 0, 100, 100, 12])
        
        controls_layout = BoxLayout(
            orientation='vertical',
            padding=[dp(20), dp(15)],
            spacing=dp(15),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(1, 1)
        )
        
        # Botones de formato con estilo
        format_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(15))
        
        self.video_btn = ToggleButton(
            text='📹 Video',
            group='format',
            state='down',
            background_color=(0.2, 0.8, 0.4, 1),
            background_normal='',
            font_size='16sp',
            color=(1, 1, 1, 1)
        )
        
        self.audio_btn = ToggleButton(
            text='🎵 Audio',
            group='format',
            background_color=(0.8, 0.4, 0.2, 1),
            background_normal='',
            font_size='16sp',
            color=(1, 1, 1, 1)
        )
        
        self.video_btn.bind(state=self.on_format_change)
        self.audio_btn.bind(state=self.on_format_change)
        
        format_layout.add_widget(self.video_btn)
        format_layout.add_widget(self.audio_btn)
        controls_layout.add_widget(format_layout)
        
        # Selector de calidad moderno
        self.quality_spinner = Spinner(
            text='⚙️ Selecciona calidad',
            values=[],
            size_hint_y=None,
            height=dp(45),
            background_color=(0.2, 0.2, 0.25, 1),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        controls_layout.add_widget(self.quality_spinner)
        
        controls_section.add_widget(controls_layout)
        container.add_widget(controls_section)
        
        # SECCIÓN DESCARGA - Botón principal
        download_section = FloatLayout(size_hint_y=None, height=dp(120))
        
        # Botón descargar con gradiente
        self.download_btn = Button(
            text='⬇️ DESCARGAR',
            size_hint=(0.8, None),
            height=dp(55),
            pos_hint={'center_x': 0.5, 'center_y': 0.7},
            background_color=(0.2, 0.6, 1, 1),
            background_normal='',
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1)
        )
        self.download_btn.bind(on_press=self.download_video)
        
        # Barra de progreso
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint=(0.8, None),
            height=dp(6),
            pos_hint={'center_x': 0.5, 'center_y': 0.3}
        )
        
        download_section.add_widget(self.download_btn)
        download_section.add_widget(self.progress_bar)
        container.add_widget(download_section)
        
        # ESTADO - Información de estado
        self.status_label = Label(
            text='✨ Listo para descargar',
            size_hint_y=None,
            height=dp(40),
            font_size='16sp',
            color=(0.8, 0.8, 0.8, 1),
            markup=True
        )
        container.add_widget(self.status_label)
        
        main_layout.add_widget(container)
        
        # Bind para actualizar gráficos
        main_layout.bind(size=self.update_graphics)
        header_layout.bind(size=self.update_header_graphics)
        url_section.bind(size=self.update_url_graphics)
        info_section.bind(size=self.update_info_graphics)
        controls_section.bind(size=self.update_controls_graphics)
        thumbnail_container.bind(size=self.update_thumb_graphics)
        
        self.video_info = None
        return main_layout
    
    def update_graphics(self, instance, size):
        self.bg_rect.size = size
    
    def update_header_graphics(self, instance, size):
        self.header_rect.pos = instance.pos
        self.header_rect.size = size
        self.header_border.rounded_rectangle = [*instance.pos, *size, 15]
    
    def update_url_graphics(self, instance, size):
        self.url_rect.pos = instance.pos
        self.url_rect.size = size
        self.url_border.rounded_rectangle = [*instance.pos, *size, 12]
    
    def update_info_graphics(self, instance, size):
        self.info_rect.pos = instance.pos
        self.info_rect.size = size
        self.info_border.rounded_rectangle = [*instance.pos, *size, 12]
    
    def update_controls_graphics(self, instance, size):
        self.controls_rect.pos = instance.pos
        self.controls_rect.size = size
        self.controls_border.rounded_rectangle = [*instance.pos, *size, 12]
    
    def update_thumb_graphics(self, instance, size):
        self.thumb_rect.pos = instance.pos
        self.thumb_rect.size = size
    
    def on_url_change(self, instance, value):
        if 'youtube.com' in value or 'youtu.be' in value:
            self.status_label.text = '🔄 [color=4da6ff]Cargando información...[/color]'
            self.progress_bar.value = 0
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
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'❌ [color=ff4444]Error: {str(e)[:30]}...[/color]'))
    
    def update_video_info(self, dt):
        if self.video_info:
            title = self.video_info.get("title", "")[:80]
            self.video_title.text = f'[color=ffffff][b]{title}[/b][/color]'
            self.thumbnail.source = self.video_info.get("thumbnail", "")
            self.update_quality_options()
            self.status_label.text = '✅ [color=4dff4d]Información cargada correctamente[/color]'
        else:
            self.status_label.text = '❌ [color=ff4444]Error al cargar información[/color]'
    
    def on_format_change(self, instance, value):
        if value == 'down':
            self.update_quality_options()
            # Cambiar colores según selección
            if instance == self.video_btn:
                instance.background_color = (0.2, 0.8, 0.4, 1)
                self.audio_btn.background_color = (0.4, 0.4, 0.5, 1)
            else:
                instance.background_color = (0.8, 0.4, 0.2, 1)
                self.video_btn.background_color = (0.4, 0.4, 0.5, 1)
    
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
                    quality = f"📺 {height}p"
                    if quality not in seen_qualities:
                        quality_options.append((quality, height))
                        seen_qualities.add(quality)
        else:
            for fmt in formats:
                abr = fmt.get("abr")
                if abr and fmt.get("acodec") and fmt["acodec"] != "none":
                    quality = f"🎵 {int(abr)}kbps"
                    if quality not in seen_qualities:
                        quality_options.append((quality, int(abr)))
                        seen_qualities.add(quality)
        
        quality_options.sort(key=lambda x: x[1], reverse=True)
        self.quality_spinner.values = [q[0] for q in quality_options]
        
        if quality_options:
            self.quality_spinner.text = quality_options[0][0]
    
    def download_video(self, instance):
        if not self.url_input.text.strip():
            self.show_popup("⚠️ Error", "Por favor ingresa una URL válida")
            return
        
        if not self.quality_spinner.text or 'Selecciona' in self.quality_spinner.text:
            self.show_popup("⚠️ Error", "Por favor selecciona una calidad")
            return
        
        self.status_label.text = '🚀 [color=4da6ff]Iniciando descarga...[/color]'
        self.download_btn.disabled = True
        self.download_btn.text = '⏳ DESCARGANDO...'
        self.progress_bar.value = 0
        
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
                    try:
                        percent_str = d.get('_percent_str', '0%')
                        percent_val = float(percent_str.replace('%', ''))
                        Clock.schedule_once(lambda dt: self.update_progress(percent_val, percent_str))
                    except:
                        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '📥 [color=4da6ff]Descargando...[/color]'))
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url_input.text.strip()])
            
            Clock.schedule_once(lambda dt: self.download_complete(True))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.download_complete(False, str(e)))
    
    def update_progress(self, percent_val, percent_str):
        self.progress_bar.value = percent_val
        self.status_label.text = f'📥 [color=4da6ff]Descargando {percent_str}[/color]'
    
    def download_complete(self, success, error_msg=None):
        self.download_btn.disabled = False
        self.download_btn.text = '⬇️ DESCARGAR'
        
        if success:
            self.status_label.text = '🎉 [color=4dff4d]¡Descarga completada con éxito![/color]'
            self.progress_bar.value = 100
            format_type = "📹 Video" if self.video_btn.state == 'down' else "🎵 Audio"
            folder = self.video_dir if self.video_btn.state == 'down' else self.audio_dir
            self.show_popup("🎉 ¡Éxito!", f"{format_type} descargado correctamente en:\n\n📁 {folder}")
        else:
            self.status_label.text = '❌ [color=ff4444]Error en la descarga[/color]'
            self.progress_bar.value = 0
            self.show_popup("❌ Error", f"Ocurrió un error durante la descarga:\n\n{str(error_msg)[:100]}...")
    
    def show_popup(self, title, message):
        content = BoxLayout(
            orientation='vertical',
            spacing=dp(15),
            padding=[dp(20), dp(15)]
        )
        
        # Estilo del popup
        with content.canvas.before:
            Color(0.12, 0.12, 0.2, 1)
            self.popup_rect = RoundedRectangle(radius=[15])
        
        content.bind(size=self.update_popup_graphics)
        
        message_label = Label(
            text=message,
            text_size=(dp(280), None),
            halign='center',
            valign='middle',
            font_size='16sp',
            color=(1, 1, 1, 1),
            markup=True
        )
        content.add_widget(message_label)
        
        close_btn = Button(
            text='✓ Cerrar',
            size_hint_y=None,
            height=dp(45),
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, 0.7),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0.8)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def update_popup_graphics(self, instance, size):
        self.popup_rect.pos = instance.pos
        self.popup_rect.size = size

if __name__ == '__main__':
    # Información del sistema
    if ANDROID_AVAILABLE:
        print("🤖 Ejecutando en Android")
    else:
        print("💻 Ejecutando en Desktop (Windows/Linux/Mac)")
    
    YouTubeDownloaderApp().run()
