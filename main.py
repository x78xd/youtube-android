from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import AsyncImage
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
import yt_dlp
import os
import threading
import re
from android.permissions import request_permissions, Permission
from android.storage import primary_external_storage_path

class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.2, 0.6, 1, 1)  # Color azul
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(8)])
        self.bind(size=self._update_rect, pos=self._update_rect)
        self.background_color = (0, 0, 0, 0)  # Transparente para usar el custom
        
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class RoundedTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # Fondo gris claro
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(8)])
            Color(0.8, 0.8, 0.8, 1)  # Borde gris
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=1)
        self.bind(size=self._update_graphics, pos=self._update_graphics)
        self.background_color = (0, 0, 0, 0)  # Transparente
        
    def _update_graphics(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.border.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))

class YouTubeDownloaderApp(App):
    def build(self):
        # Solicitar permisos de almacenamiento
        try:
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.INTERNET
            ])
        except Exception as e:
            print(f"Error solicitando permisos: {e}")
        
        # Directorios de descarga en Android
        try:
            self.external_path = primary_external_storage_path()
            self.video_dir = os.path.join(self.external_path, "Download", "Videos")
            self.audio_dir = os.path.join(self.external_path, "Download", "Audios")
        except Exception as e:
            print(f"Error configurando rutas: {e}")
            # Fallback para testing
            self.video_dir = "Videos"
            self.audio_dir = "Audios"
        
        # Crear directorios si no existen
        try:
            os.makedirs(self.video_dir, exist_ok=True)
            os.makedirs(self.audio_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creando directorios: {e}")
        
        # ScrollView principal para hacer la app scrolleable
        scroll = ScrollView()
        
        # Layout principal con mejor espaciado y colores
        main_layout = BoxLayout(
            orientation='vertical', 
            padding=[dp(20), dp(30), dp(20), dp(20)], 
            spacing=dp(15),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))
        
        # Título con mejor diseño
        title = Label(
            text='📱 YouTube Downloader',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(24),
            color=(0.1, 0.1, 0.1, 1),
            bold=True,
            halign='center'
        )
        main_layout.add_widget(title)
        
        # Separador visual
        separator = Widget(size_hint_y=None, height=dp(10))
        main_layout.add_widget(separator)
        
        # Campo URL mejorado
        url_label = Label(
            text='🔗 URL del Video:',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16),
            color=(0.2, 0.2, 0.2, 1),
            halign='left',
            text_size=(None, None)
        )
        main_layout.add_widget(url_label)
        
        self.url_input = RoundedTextInput(
            hint_text='Pega aquí la URL de YouTube...',
            multiline=False,
            size_hint_y=None,
            height=dp(50),
            font_size=dp(14),
            foreground_color=(0.1, 0.1, 0.1, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1),
            padding=[dp(15), dp(10)]
        )
        self.url_input.bind(text=self.on_url_change)
        main_layout.add_widget(self.url_input)
        
        # Container para thumbnail e info
        info_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(280),
            spacing=dp(10)
        )
        
        # Imagen thumbnail con bordes redondeados
        self.thumbnail = AsyncImage(
            source='',
            size_hint_y=None,
            height=dp(200),
            allow_stretch=True,
            keep_ratio=True
        )
        info_container.add_widget(self.thumbnail)
        
        # Título del video con mejor formato
        self.video_title = Label(
            text='Información del video aparecerá aquí...',
            text_size=(None, None),
            size_hint_y=None,
            height=dp(70),
            valign='middle',
            halign='center',
            font_size=dp(14),
            color=(0.3, 0.3, 0.3, 1)
        )
        info_container.add_widget(self.video_title)
        main_layout.add_widget(info_container)
        
        # Label para formato
        format_label = Label(
            text='📁 Tipo de Descarga:',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16),
            color=(0.2, 0.2, 0.2, 1),
            halign='left'
        )
        main_layout.add_widget(format_label)
        
        # Botones de formato mejorados
        format_layout = BoxLayout(
            size_hint_y=None, 
            height=dp(50), 
            spacing=dp(10)
        )
        
        self.video_btn = ToggleButton(
            text='🎥 Video', 
            group='format', 
            state='down',
            font_size=dp(16),
            background_color=(0.2, 0.7, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        self.audio_btn = ToggleButton(
            text='🎵 Audio', 
            group='format',
            font_size=dp(16),
            background_color=(0.7, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        
        self.video_btn.bind(state=self.on_format_change)
        self.audio_btn.bind(state=self.on_format_change)
        
        format_layout.add_widget(self.video_btn)
        format_layout.add_widget(self.audio_btn)
        main_layout.add_widget(format_layout)
        
        # Label para calidad
        quality_label = Label(
            text='⚙️ Calidad:',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16),
            color=(0.2, 0.2, 0.2, 1),
            halign='left'
        )
        main_layout.add_widget(quality_label)
        
        # Selector de calidad mejorado
        self.quality_spinner = Spinner(
            text='Selecciona calidad',
            values=[],
            size_hint_y=None,
            height=dp(50),
            font_size=dp(14),
            background_color=(0.95, 0.95, 0.95, 1),
            color=(0.1, 0.1, 0.1, 1)
        )
        main_layout.add_widget(self.quality_spinner)
        
        # Barra de progreso
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(20)
        )
        self.progress_bar.opacity = 0  # Inicialmente oculta
        main_layout.add_widget(self.progress_bar)
        
        # Botón descargar mejorado
        self.download_btn = RoundedButton(
            text='⬇️ DESCARGAR',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(18),
            bold=True,
            color=(1, 1, 1, 1)
        )
        self.download_btn.bind(on_press=self.download_video)
        main_layout.add_widget(self.download_btn)
        
        # Estado con mejor diseño
        self.status_label = Label(
            text='✅ Listo para descargar',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(14),
            color=(0.2, 0.6, 0.2, 1),
            halign='center'
        )
        main_layout.add_widget(self.status_label)
        
        # Espacio adicional al final
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(20)))
        
        scroll.add_widget(main_layout)
        self.video_info = None
        return scroll
    
    def is_valid_youtube_url(self, url):
        """Valida si la URL es de YouTube"""
        youtube_patterns = [
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/',
            r'(https?://)?(m\.)?youtube\.com/',
            r'(https?://)?youtu\.be/'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in youtube_patterns)
    
    def on_url_change(self, instance, value):
        value = value.strip()
        if value and self.is_valid_youtube_url(value):
            self.status_label.text = '🔄 Cargando información...'
            self.status_label.color = (0.8, 0.6, 0.2, 1)
            # Limpiar información anterior
            self.video_title.text = 'Cargando...'
            self.thumbnail.source = ''
            self.quality_spinner.values = []
            self.quality_spinner.text = 'Cargando calidades...'
            
            threading.Thread(target=self.fetch_video_info, args=(value,), daemon=True).start()
        elif value and not self.is_valid_youtube_url(value):
            self.status_label.text = '❌ URL no válida de YouTube'
            self.status_label.color = (0.8, 0.2, 0.2, 1)
    
    def fetch_video_info(self, url):
        try:
            ydl_opts = {
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'socket_timeout': 30,
                'retries': 3
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    self.video_info = {
                        "title": info.get("title", "Video sin título"),
                        "thumbnail": info.get("thumbnail", ""),
                        "formats": info.get("formats", []),
                        "duration": info.get("duration", 0),
                        "uploader": info.get("uploader", "Desconocido")
                    }
                    Clock.schedule_once(self.update_video_info)
                else:
                    self.video_info = None
                    Clock.schedule_once(lambda dt: self.update_error_status('No se pudo obtener información del video'))
                    
        except Exception as e:
            self.video_info = None
            error_msg = str(e)
            if "Video unavailable" in error_msg:
                error_msg = "Video no disponible o privado"
            elif "network" in error_msg.lower():
                error_msg = "Error de conexión de red"
            else:
                error_msg = f"Error: {error_msg[:50]}..."
            
            Clock.schedule_once(lambda dt: self.update_error_status(error_msg))
    
    def update_error_status(self, message):
        self.status_label.text = f'❌ {message}'
        self.status_label.color = (0.8, 0.2, 0.2, 1)
        self.video_title.text = 'Error al cargar información'
        self.thumbnail.source = ''
        self.quality_spinner.values = []
        self.quality_spinner.text = 'Error en carga'
    
    def update_video_info(self, dt):
        if self.video_info:
            title = self.video_info.get("title", "")
            uploader = self.video_info.get("uploader", "")
            duration = self.video_info.get("duration", 0)
            
            # Formatear duración
            if duration:
                mins, secs = divmod(duration, 60)
                duration_str = f" • {int(mins)}:{int(secs):02d}"
            else:
                duration_str = ""
            
            # Título completo con información adicional
            full_title = f"{title[:80]}{'...' if len(title) > 80 else ''}"
            if uploader:
                full_title += f"\n👤 {uploader}{duration_str}"
            
            self.video_title.text = full_title
            self.video_title.text_size = (self.video_title.width - dp(20), None)
            self.thumbnail.source = self.video_info.get("thumbnail", "")
            self.update_quality_options()
            self.status_label.text = '✅ Información cargada correctamente'
            self.status_label.color = (0.2, 0.6, 0.2, 1)
        else:
            self.update_error_status('Error al procesar información')
    
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
            # Para video, buscar formatos con video y audio
            for fmt in formats:
                height = fmt.get("height")
                vcodec = fmt.get("vcodec", "")
                acodec = fmt.get("acodec", "")
                
                if height and height > 0 and vcodec != "none":
                    quality = f"{height}p"
                    if quality not in seen_qualities:
                        # Priorizar formatos que tienen audio
                        has_audio = acodec and acodec != "none"
                        quality_options.append((quality, height, has_audio))
                        seen_qualities.add(quality)
        else:
            # Para audio
            for fmt in formats:
                abr = fmt.get("abr")
                acodec = fmt.get("acodec", "")
                if abr and acodec and acodec != "none":
                    quality = f"{int(abr)}kbps"
                    if quality not in seen_qualities:
                        quality_options.append((quality, int(abr), True))
                        seen_qualities.add(quality)
        
        # Ordenar por calidad (y priorizar los que tienen audio para video)
        if is_video:
            quality_options.sort(key=lambda x: (x[2], x[1]), reverse=True)
        else:
            quality_options.sort(key=lambda x: x[1], reverse=True)
        
        self.quality_spinner.values = [q[0] for q in quality_options]
        
        if quality_options:
            self.quality_spinner.text = quality_options[0][0]
        else:
            self.quality_spinner.text = 'Sin calidades disponibles'
    
    def download_video(self, instance):
        if not self.url_input.text.strip():
            self.show_popup("❌ Error", "Por favor ingresa una URL válida")
            return
        
        if not self.video_info:
            self.show_popup("❌ Error", "Primero carga la información del video")
            return
        
        if not self.quality_spinner.text or 'Selecciona' in self.quality_spinner.text:
            self.show_popup("❌ Error", "Por favor selecciona una calidad")
            return
        
        self.status_label.text = '🚀 Iniciando descarga...'
        self.status_label.color = (0.2, 0.2, 0.8, 1)
        self.download_btn.disabled = True
        self.progress_bar.opacity = 1
        self.progress_bar.value = 0
        
        threading.Thread(target=self.perform_download, daemon=True).start()
    
    def perform_download(self):
        try:
            is_video = self.video_btn.state == 'down'
            folder = self.video_dir if is_video else self.audio_dir
            
            # Configuración más robusta para descarga
            if is_video:
                ydl_opts = {
                    'format': 'best[height<=1080]/best',  # Limitar a 1080p para evitar problemas
                    'outtmpl': os.path.join(folder, '%(title).100s.%(ext)s'),  # Limitar longitud del nombre
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                    'socket_timeout': 60,
                    'retries': 5,
                    'fragment_retries': 5,
                    'ignoreerrors': False,
                }
            else:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(folder, '%(title).100s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'socket_timeout': 60,
                    'retries': 5,
                    'fragment_retries': 5,
                    'ignoreerrors': False,
                }
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    if '_percent_str' in d:
                        percent_str = d['_percent_str'].strip()
                        try:
                            # Extraer el número del porcentaje
                            percent_num = float(percent_str.replace('%', ''))
                            Clock.schedule_once(lambda dt: self.update_progress(percent_num, f'📥 Descargando {percent_str}'))
                        except:
                            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'📥 Descargando {percent_str}'))
                elif d['status'] == 'finished':
                    Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '🔄 Procesando archivo...'))
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url_input.text.strip()])
            
            Clock.schedule_once(lambda dt: self.download_complete(True))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.download_complete(False, str(e)))
    
    def update_progress(self, percent, text):
        self.progress_bar.value = min(percent, 100)
        self.status_label.text = text
        self.status_label.color = (0.2, 0.2, 0.8, 1)
    
    def download_complete(self, success, error_msg=None):
        self.download_btn.disabled = False
        self.progress_bar.opacity = 0
        
        if success:
            self.status_label.text = '🎉 ¡Descarga completada!'
            self.status_label.color = (0.2, 0.6, 0.2, 1)
            format_type = "Video" if self.video_btn.state == 'down' else "Audio"
            folder = self.video_dir if self.video_btn.state == 'down' else self.audio_dir
            self.show_popup("🎉 ¡Éxito!", f"{format_type} descargado correctamente en:\n\n📂 {folder}")
        else:
            self.status_label.text = '❌ Error en la descarga'
            self.status_label.color = (0.8, 0.2, 0.2, 1)
            
            # Mensajes de error más amigables
            if "HTTP Error 403" in str(error_msg):
                error_msg = "Acceso denegado. El video puede estar restringido."
            elif "network" in str(error_msg).lower():
                error_msg = "Error de conexión. Verifica tu internet."
            elif "No space left" in str(error_msg):
                error_msg = "No hay espacio suficiente en el dispositivo."
            else:
                error_msg = str(error_msg)[:150] + "..." if len(str(error_msg)) > 150 else str(error_msg)
            
            self.show_popup("❌ Error de Descarga", f"No se pudo completar la descarga:\n\n{error_msg}")
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(15))
        
        # Mensaje con scroll si es muy largo
        scroll_message = ScrollView(size_hint_y=0.8)
        message_label = Label(
            text=message, 
            text_size=(dp(280), None),
            halign='center',
            valign='top',
            font_size=dp(14),
            color=(0.2, 0.2, 0.2, 1)
        )
        message_label.bind(texture_size=message_label.setter('size'))
        scroll_message.add_widget(message_label)
        content.add_widget(scroll_message)
        
        # Botón de cerrar mejorado
        close_btn = RoundedButton(
            text='✅ Entendido',
            size_hint_y=None,
            height=dp(45),
            font_size=dp(16)
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.85, 0.7),
            auto_dismiss=False,
            separator_color=(0.2, 0.6, 1, 1),
            title_color=(0.1, 0.1, 0.1, 1)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    YouTubeDownloaderApp().run()
