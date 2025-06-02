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
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
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
        
        # Layout principal con estilo mejorado
        main_layout = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(15))
        
        # Fondo con gradiente elegante
        with main_layout.canvas.before:
            Color(0.1, 0.1, 0.15, 1)  # Fondo oscuro elegante
            self.bg_rect = RoundedRectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(size=self.update_bg, pos=self.update_bg)
        
        # Título con estilo mejorado
        title_layout = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(10))
        
        # Icono emoji como decoración
        icon_label = Label(
            text='📺',
            font_size='32sp',
            size_hint_x=None,
            width=dp(50),
            valign='middle'
        )
        
        title = Label(
            text='YouTube Downloader',
            font_size='28sp',
            bold=True,
            color=(1, 1, 1, 1),
            valign='middle'
        )
        
        title_layout.add_widget(icon_label)
        title_layout.add_widget(title)
        main_layout.add_widget(title_layout)
        
        # Separador decorativo
        separator = Widget(size_hint_y=None, height=dp(2))
        with separator.canvas:
            Color(0.2, 0.6, 1, 0.5)
            Line(points=[0, dp(1), 800, dp(1)], width=2)
        main_layout.add_widget(separator)
        
        # Card contenedor para la entrada de URL
        url_card = self.create_card(dp(70))
        url_layout = BoxLayout(padding=dp(15))
        
        self.url_input = self.create_modern_textinput(
            hint_text='🔗 Pega la URL del video de YouTube aquí...',
            multiline=False,
            font_size='16sp'
        )
        self.url_input.bind(text=self.on_url_change)
        
        url_layout.add_widget(self.url_input)
        url_card.add_widget(url_layout)
        main_layout.add_widget(url_card)
        
        # Card para thumbnail y título
        info_card = self.create_card(dp(280))
        info_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # Imagen thumbnail
        self.thumbnail = AsyncImage(
            source='',
            size_hint_y=None,
            height=dp(180)
        )
        info_layout.add_widget(self.thumbnail)
        
        # Título del video
        self.video_title = Label(
            text='Selecciona un video para ver la información',
            text_size=(None, None),
            size_hint_y=None,
            height=dp(60),
            valign='middle',
            halign='center',
            font_size='16sp',
            color=(0.9, 0.9, 0.9, 1),
            bold=True
        )
        info_layout.add_widget(self.video_title)
        
        info_card.add_widget(info_layout)
        main_layout.add_widget(info_card)
        
        # Card para controles de formato
        format_card = self.create_card(dp(80))
        format_main_layout = BoxLayout(padding=dp(20))
        format_layout = BoxLayout(spacing=dp(15))
        
        self.video_btn = self.create_modern_toggle_button('🎬 Video', 'format', 'down')
        self.audio_btn = self.create_modern_toggle_button('🎵 Audio', 'format')
        
        self.video_btn.bind(state=self.on_format_change)
        self.audio_btn.bind(state=self.on_format_change)
        
        format_layout.add_widget(self.video_btn)
        format_layout.add_widget(self.audio_btn)
        format_main_layout.add_widget(format_layout)
        format_card.add_widget(format_main_layout)
        main_layout.add_widget(format_card)
        
        # Card para selector de calidad
        quality_card = self.create_card(dp(80))
        quality_layout = BoxLayout(padding=dp(20))
        
        self.quality_spinner = self.create_modern_spinner(
            text='⚙️ Selecciona calidad',
            values=[],
            font_size='16sp'
        )
        
        quality_layout.add_widget(self.quality_spinner)
        quality_card.add_widget(quality_layout)
        main_layout.add_widget(quality_card)
        
        # Barra de progreso
        self.progress_bar = ProgressBar(
            size_hint_y=None,
            height=dp(8),
            max=100,
            value=0
        )
        main_layout.add_widget(self.progress_bar)
        
        # Botón de descarga
        self.download_btn = self.create_modern_button(
            text='⬇️ DESCARGAR',
            size_hint_y=None,
            height=dp(60),
            font_size='18sp'
        )
        self.download_btn.bind(on_press=self.download_video)
        main_layout.add_widget(self.download_btn)
        
        # Estado
        self.status_label = Label(
            text='✨ Listo para descargar',
            size_hint_y=None,
            height=dp(40),
            font_size='16sp',
            color=(0.8, 0.8, 0.8, 1),
            halign='center'
        )
        main_layout.add_widget(self.status_label)
        
        # Espaciador
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(20)))
        
        self.video_info = None
        return main_layout
    
    def update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def create_card(self, height):
        """Crea una tarjeta con bordes redondeados"""
        card = Widget(size_hint_y=None, height=height)
        def update_card_graphics(*args):
            card.canvas.before.clear()
            with card.canvas.before:
                Color(1, 1, 1, 0.1)  # Fondo semi-transparente
                RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(15)])
                Color(0.8, 0.8, 0.8, 0.3)  # Borde sutil
                Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(15)), width=1)
        card.bind(size=update_card_graphics, pos=update_card_graphics)
        return card
    
    def create_modern_button(self, **kwargs):
        """Crea un botón moderno con bordes redondeados"""
        btn = Button(background_normal='', background_down='', bold=True, color=(1, 1, 1, 1), **kwargs)
        def update_btn_graphics(*args):
            btn.canvas.before.clear()
            with btn.canvas.before:
                Color(0.2, 0.6, 1, 1)  # Azul moderno
                RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(10)])
        btn.bind(size=update_btn_graphics, pos=update_btn_graphics)
        return btn
    
    def create_modern_toggle_button(self, text, group, state='normal'):
        """Crea un toggle button moderno"""
        btn = ToggleButton(
            text=text, 
            group=group, 
            state=state,
            background_normal='', 
            background_down='',
            font_size='16sp',
            bold=True
        )
        def update_toggle_graphics(*args):
            btn.canvas.before.clear()
            with btn.canvas.before:
                if btn.state == 'down':
                    Color(0.2, 0.6, 1, 1)  # Azul cuando está activo
                else:
                    Color(0.3, 0.3, 0.3, 1)  # Gris cuando no está activo
                RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])
        btn.bind(size=update_toggle_graphics, pos=update_toggle_graphics, state=update_toggle_graphics)
        return btn
    
    def create_modern_textinput(self, **kwargs):
        """Crea un campo de texto moderno"""
        text_input = TextInput(
            background_normal='', 
            background_active='',
            foreground_color=(0.2, 0.2, 0.2, 1),
            hint_text_color=(0.6, 0.6, 0.6, 1),
            **kwargs
        )
        def update_input_graphics(*args):
            text_input.canvas.before.clear()
            with text_input.canvas.before:
                Color(0.95, 0.95, 0.95, 1)  # Fondo blanco
                RoundedRectangle(pos=text_input.pos, size=text_input.size, radius=[dp(8)])
                if text_input.focus:
                    Color(0.2, 0.6, 1, 1)  # Borde azul cuando está enfocado
                else:
                    Color(0.8, 0.8, 0.8, 1)  # Borde gris normal
                Line(rounded_rectangle=(text_input.x, text_input.y, text_input.width, text_input.height, dp(8)), width=2)
        text_input.bind(size=update_input_graphics, pos=update_input_graphics, focus=update_input_graphics)
        return text_input
    
    def create_modern_spinner(self, **kwargs):
        """Crea un spinner moderno"""
        spinner = Spinner(
            background_normal='', 
            background_down='',
            color=(0.2, 0.2, 0.2, 1),
            **kwargs
        )
        def update_spinner_graphics(*args):
            spinner.canvas.before.clear()
            with spinner.canvas.before:
                Color(0.95, 0.95, 0.95, 1)
                RoundedRectangle(pos=spinner.pos, size=spinner.size, radius=[dp(8)])
                Color(0.8, 0.8, 0.8, 1)
                Line(rounded_rectangle=(spinner.x, spinner.y, spinner.width, spinner.height, dp(8)), width=1)
        spinner.bind(size=update_spinner_graphics, pos=update_spinner_graphics)
        return spinner
    
    def on_url_change(self, instance, value):
        if 'youtube.com' in value or 'youtu.be' in value:
            self.status_label.text = '🔄 Cargando información...'
            self.progress_bar.value = 25
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
            Clock.schedule_once(lambda dt: self.update_error_status(str(e)))
    
    def update_error_status(self, error):
        self.status_label.text = f'❌ Error: {error[:30]}...'
        self.progress_bar.value = 0
    
    def update_video_info(self, dt):
        if self.video_info:
            self.video_title.text = self.video_info.get("title", "")[:80] + "..."
            self.thumbnail.source = self.video_info.get("thumbnail", "")
            self.update_quality_options()
            self.status_label.text = '✅ Información cargada correctamente'
            self.progress_bar.value = 100
            # Resetear la barra después de un momento
            Clock.schedule_once(lambda dt: setattr(self.progress_bar, 'value', 0), 2)
        else:
            self.status_label.text = '❌ Error al cargar información'
            self.progress_bar.value = 0
    
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
        
        # Ordenar por calidad
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
        
        self.status_label.text = '🚀 Iniciando descarga...'
        self.download_btn.disabled = True
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
                    percent_str = d.get('_percent_str', '0%')
                    try:
                        percent_val = float(percent_str.replace('%', ''))
                        Clock.schedule_once(lambda dt: self.update_download_progress(percent_val, percent_str))
                    except:
                        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'📥 Descargando...'))
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url_input.text.strip()])
            
            Clock.schedule_once(lambda dt: self.download_complete(True))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.download_complete(False, str(e)))
    
    def update_download_progress(self, percent_val, percent_str):
        self.progress_bar.value = percent_val
        self.status_label.text = f'📥 Descargando {percent_str}'
    
    def download_complete(self, success, error_msg=None):
        self.download_btn.disabled = False
        self.progress_bar.value = 0
        
        if success:
            self.status_label.text = '🎉 ¡Descarga completada!'
            format_type = "Video" if self.video_btn.state == 'down' else "Audio"
            folder = self.video_dir if self.video_btn.state == 'down' else self.audio_dir
            self.show_popup("🎉 ¡Éxito!", f"✅ {format_type} descargado exitosamente\n\n📁 Ubicación:\n{folder}")
        else:
            self.status_label.text = '❌ Error en la descarga'
            self.show_popup("❌ Error", f"⚠️ Ocurrió un problema:\n\n{str(error_msg)[:100]}...")
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        # Mensaje con mejor formato
        msg_label = Label(
            text=message, 
            text_size=(dp(280), None), 
            halign='center',
            valign='middle',
            font_size='16sp',
            color=(0.2, 0.2, 0.2, 1)
        )
        content.add_widget(msg_label)
        
        # Botón de cerrar mejorado
        close_btn = self.create_modern_button(
            text='✖️ Cerrar', 
            size_hint_y=None, 
            height=dp(50),
            font_size='16sp'
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, 0.7),
            auto_dismiss=False,
            title_size='20sp'
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    YouTubeDownloaderApp().run()
