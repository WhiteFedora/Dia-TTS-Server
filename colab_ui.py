# colab_ui.py
# Interactive UI for Dia TTS in Google Colab using ipywidgets

import ipywidgets as widgets
from IPython.display import display, Audio, HTML, clear_output
import numpy as np
import os
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime

# Import Colab-specific modules
from colab_config import config_manager, get_config, update_config
from colab_files import get_reference_files, get_predefined_voices, save_uploaded_file
from engine_colab import load_model, generate_speech, get_model_status

# Global variables for UI state
current_audio_data = None
current_sample_rate = 44100
generation_in_progress = False


def create_file_upload_widget() -> widgets.FileUpload:
    """Create file upload widget for reference audio."""

    def on_upload_change(change):
        if change['new']:
            for filename, file_info in change['new'].items():
                # Save uploaded file
                file_path = save_uploaded_file(
                    file_info['content'],
                    filename,
                    "reference_audio"
                )

                # Refresh reference files list
                if hasattr(create_file_upload_widget, '_ref_files_dropdown'):
                    create_file_upload_widget._ref_files_dropdown.options = get_reference_files()

                print(f"✅ Uploaded: {filename}")

    upload_widget = widgets.FileUpload(
        accept='.wav,.mp3',
        multiple=True,
        description='Upload Reference Audio',
        style={'description_width': 'initial'}
    )

    upload_widget.observe(on_upload_change, names='value')
    return upload_widget


def create_voice_mode_selector() -> widgets.Dropdown:
    """Create voice mode selection dropdown."""

    voice_modes = [
        ('Random / Dialogue', 'dialogue'),
        ('Voice Cloning (Reference)', 'clone'),
        ('Predefined Voices', 'predefined')
    ]

    dropdown = widgets.Dropdown(
        options=voice_modes,
        value=get_config().last_voice_mode,
        description='Voice Mode:',
        style={'description_width': 'initial'}
    )

    return dropdown


def create_text_input() -> widgets.Textarea:
    """Create text input widget."""

    text_input = widgets.Textarea(
        value=get_config().last_text,
        placeholder='Enter text to synthesize...',
        description='Text:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='100%', height='120px')
    )

    return text_input


def create_parameter_sliders() -> Dict[str, widgets.FloatSlider]:
    """Create parameter control sliders."""

    config = get_config()

    sliders = {
        'speed_factor': widgets.FloatSlider(
            value=config.speed_factor,
            min=0.5, max=2.0, step=0.1,
            description='Speed Factor:',
            style={'description_width': 'initial'},
            readout_format='.1f'
        ),

        'cfg_scale': widgets.FloatSlider(
            value=config.cfg_scale,
            min=1.0, max=5.0, step=0.1,
            description='CFG Scale:',
            style={'description_width': 'initial'},
            readout_format='.1f'
        ),

        'temperature': widgets.FloatSlider(
            value=config.temperature,
            min=0.1, max=1.5, step=0.05,
            description='Temperature:',
            style={'description_width': 'initial'},
            readout_format='.2f'
        ),

        'top_p': widgets.FloatSlider(
            value=config.top_p,
            min=0.1, max=1.0, step=0.01,
            description='Top P:',
            style={'description_width': 'initial'},
            readout_format='.2f'
        ),

        'cfg_filter_top_k': widgets.IntSlider(
            value=config.cfg_filter_top_k,
            min=1, max=100, step=1,
            description='Top K:',
            style={'description_width': 'initial'}
        ),

        'seed': widgets.IntText(
            value=config.seed,
            description='Seed:',
            style={'description_width': 'initial'},
            placeholder='42 or -1 for random'
        ),

        'chunk_size': widgets.IntSlider(
            value=config.chunk_size,
            min=50, max=400, step=10,
            description='Chunk Size:',
            style={'description_width': 'initial'}
        )
    }

    return sliders


def create_voice_selection_widgets() -> Dict[str, widgets.Widget]:
    """Create voice selection widgets."""

    # Reference files dropdown
    ref_files = get_reference_files()
    ref_dropdown = widgets.Dropdown(
        options=['-- Select Reference File --'] + ref_files,
        description='Reference Audio:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='70%')
    )

    # Predefined voices dropdown
    predefined_voices = get_predefined_voices()
    voice_dropdown = widgets.Dropdown(
        options=['-- Select Voice --'] + [v['display_name'] for v in predefined_voices],
        description='Predefined Voice:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='70%')
    )

    # File upload widget
    upload_widget = create_file_upload_widget()

    return {
        'reference': ref_dropdown,
        'predefined': voice_dropdown,
        'upload': upload_widget
    }


def create_control_buttons() -> Dict[str, widgets.Button]:
    """Create control buttons."""

    generate_btn = widgets.Button(
        description='🎵 Generate Speech',
        button_style='primary',
        icon='volume-up',
        layout=widgets.Layout(width='200px')
    )

    load_model_btn = widgets.Button(
        description='🤖 Load Model',
        button_style='info',
        icon='download',
        layout=widgets.Layout(width='150px')
    )

    play_btn = widgets.Button(
        description='▶️ Play',
        button_style='success',
        icon='play',
        disabled=True,
        layout=widgets.Layout(width='100px')
    )

    download_btn = widgets.Button(
        description='💾 Download',
        button_style='warning',
        icon='download',
        disabled=True,
        layout=widgets.Layout(width='120px')
    )

    return {
        'generate': generate_btn,
        'load_model': load_model_btn,
        'play': play_btn,
        'download': download_btn
    }


def create_status_display() -> widgets.HTML:
    """Create status display widget."""

    status_html = widgets.HTML(
        value="<div style='padding: 10px; background-color: #f0f8ff; border-left: 4px solid #007bff; margin: 10px 0;'>"
              "<strong>Status:</strong> Ready to load model</div>"
    )

    return status_html


def create_progress_bar() -> widgets.FloatProgress:
    """Create progress bar for generation."""

    progress = widgets.FloatProgress(
        value=0.0,
        min=0.0,
        max=1.0,
        description='Generating:',
        bar_style='info',
        style={'bar_color': '#007bff'},
        layout=widgets.Layout(width='100%')
    )

    return progress


def update_voice_widgets_visibility(voice_mode: str, widgets_dict: Dict[str, widgets.Widget]):
    """Update visibility of voice selection widgets based on mode."""

    if voice_mode == 'clone':
        widgets_dict['reference'].layout.display = 'block'
        widgets_dict['predefined'].layout.display = 'none'
    elif voice_mode == 'predefined':
        widgets_dict['reference'].layout.display = 'none'
        widgets_dict['predefined'].layout.display = 'block'
    else:  # dialogue
        widgets_dict['reference'].layout.display = 'none'
        widgets_dict['predefined'].layout.display = 'none'


def generate_audio_handler(button, ui_elements: Dict[str, Any]):
    """Handle audio generation button click."""

    global current_audio_data, current_sample_rate, generation_in_progress

    if generation_in_progress:
        return

    # Get UI elements
    text_input = ui_elements['text_input']
    voice_mode_dropdown = ui_elements['voice_mode']
    sliders = ui_elements['sliders']
    voice_widgets = ui_elements['voice_widgets']
    status_display = ui_elements['status']
    progress_bar = ui_elements['progress']
    buttons = ui_elements['buttons']

    # Validate inputs
    text = text_input.value.strip()
    if not text:
        status_display.value = "<div style='padding: 10px; background-color: #ffebee; border-left: 4px solid #f44336; margin: 10px 0;'>" \
                              "<strong>Error:</strong> Please enter some text to synthesize</div>"
        return

    # Check if model is loaded
    if not get_model_status()['loaded']:
        status_display.value = "<div style='padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; margin: 10px 0;'>" \
                              "<strong>Warning:</strong> Please load the model first</div>"
        return

    # Get voice file based on mode
    voice_file = None
    if voice_mode_dropdown.value == 'clone':
        selected_ref = voice_widgets['reference'].value
        if selected_ref and selected_ref != '-- Select Reference File --':
            voice_file = selected_ref
    elif voice_mode_dropdown.value == 'predefined':
        predefined_voices = get_predefined_voices()
        voice_names = [v['display_name'] for v in predefined_voices]
        selected_voice = voice_widgets['predefined'].value

        if selected_voice and selected_voice != '-- Select Voice --':
            voice_index = voice_names.index(selected_voice)
            voice_file = predefined_voices[voice_index]['filename']

    if voice_mode_dropdown.value in ['clone', 'predefined'] and not voice_file:
        status_display.value = "<div style='padding: 10px; background-color: #ffebee; border-left: 4px solid #f44336; margin: 10px 0;'>" \
                              f"<strong>Error:</strong> Please select a {voice_mode_dropdown.value} file</div>"
        return

    # Update status
    generation_in_progress = True
    buttons['generate'].disabled = True
    buttons['generate'].description = '⏳ Generating...'

    status_display.value = "<div style='padding: 10px; background-color: #e8f5e8; border-left: 4px solid #4caf50; margin: 10px 0;'>" \
                          "<strong>Status:</strong> Starting generation...</div>"

    progress_bar.value = 0.0
    progress_bar.bar_style = 'info'

    # Get parameters
    params = {
        'text_to_process': text,
        'voice_mode': voice_mode_dropdown.value,
        'clone_reference_filename': voice_file,
        'speed_factor': sliders['speed_factor'].value,
        'cfg_scale': sliders['cfg_scale'].value,
        'temperature': sliders['temperature'].value,
        'top_p': sliders['top_p'].value,
        'cfg_filter_top_k': sliders['cfg_filter_top_k'].value,
        'seed': sliders['seed'].value if sliders['seed'].value != '' else None,
        'split_text': get_config().split_text,
        'chunk_size': sliders['chunk_size'].value,
    }

    try:
        # Generate audio in background
        result = generate_speech(**params)

        if result is None:
            status_display.value = "<div style='padding: 10px; background-color: #ffebee; border-left: 4px solid #f44336; margin: 10px 0;'>" \
                                  "<strong>Error:</strong> Generation failed</div>"
            progress_bar.bar_style = 'danger'
        else:
            audio_array, sample_rate = result
            current_audio_data = audio_array
            current_sample_rate = sample_rate

            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dia_tts_{voice_mode_dropdown.value}_{timestamp}.wav"

            # Convert to bytes for saving
            audio_bytes = audio_array.astype(np.float32).tobytes()

            # Save file (you might want to implement this)
            # save_generated_audio(audio_bytes, filename)

            # Update UI
            status_display.value = "<div style='padding: 10px; background-color: #e8f5e8; border-left: 4px solid #4caf50; margin: 10px 0;'>" \
                                  f"<strong>Success:</strong> Generated audio ({len(audio_array)/sample_rate:.2f}s)</div>"

            progress_bar.value = 1.0
            progress_bar.bar_style = 'success'

            # Enable playback and download buttons
            buttons['play'].disabled = False
            buttons['download'].disabled = False

            # Update config with current settings
            update_config({
                'last_text': text,
                'last_voice_mode': voice_mode_dropdown.value,
                'speed_factor': sliders['speed_factor'].value,
                'cfg_scale': sliders['cfg_scale'].value,
                'temperature': sliders['temperature'].value,
                'top_p': sliders['top_p'].value,
                'cfg_filter_top_k': sliders['cfg_filter_top_k'].value,
                'seed': sliders['seed'].value,
                'chunk_size': sliders['chunk_size'].value,
            })

    except Exception as e:
        status_display.value = f"<div style='padding: 10px; background-color: #ffebee; border-left: 4px solid #f44336; margin: 10px 0;'>" \
                              f"<strong>Error:</strong> {str(e)}</div>"
        progress_bar.bar_style = 'danger'

    finally:
        generation_in_progress = False
        buttons['generate'].disabled = False
        buttons['generate'].description = '🎵 Generate Speech'


def play_audio_handler(button):
    """Handle play button click."""

    global current_audio_data, current_sample_rate

    if current_audio_data is not None:
        # Normalize audio data to int16 for playback
        audio_int16 = (current_audio_data * 32767).astype(np.int16)

        # Display audio player
        display(Audio(audio_int16, rate=current_sample_rate, autoplay=True))


def download_audio_handler(button):
    """Handle download button click."""

    global current_audio_data, current_sample_rate

    if current_audio_data is not None:
        # Create download link
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dia_tts_audio_{timestamp}.wav"

        # Convert to bytes
        audio_int16 = (current_audio_data * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()

        # Create download (this is a simple approach - in practice you might want to save to file first)
        from google.colab import files
        with open(f"/content/{filename}", 'wb') as f:
            f.write(audio_bytes)
        files.download(f"/content/{filename}")


def load_model_handler(button, status_display: widgets.HTML):
    """Handle load model button click."""

    button.disabled = True
    button.description = '⏳ Loading...'

    status_display.value = "<div style='padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107; margin: 10px 0;'>" \
                          "<strong>Status:</strong> Loading model...</div>"

    try:
        success = load_model()

        if success:
            status_display.value = "<div style='padding: 10px; background-color: #e8f5e8; border-left: 4px solid #4caf50; margin: 10px 0;'>" \
                                  "<strong>Success:</strong> Model loaded successfully</div>"
        else:
            status_display.value = "<div style='padding: 10px; background-color: #ffebee; border-left: 4px solid #f44336; margin: 10px 0;'>" \
                                  "<strong>Error:</strong> Failed to load model</div>"

    except Exception as e:
        status_display.value = f"<div style='padding: 10px; background-color: #ffebee; border-left: 4px solid #f44336; margin: 10px 0;'>" \
                              f"<strong>Error:</strong> {str(e)}</div>"

    finally:
        button.disabled = False
        button.description = '🤖 Load Model'


def create_tts_interface() -> widgets.Widget:
    """Create the main TTS interface."""

    # Create UI elements
    status_display = create_status_display()
    progress_bar = create_progress_bar()

    text_input = create_text_input()
    voice_mode_dropdown = create_voice_mode_selector()
    voice_widgets = create_voice_selection_widgets()
    sliders = create_parameter_sliders()
    buttons = create_control_buttons()

    # Create layout containers
    header_box = widgets.HTML(
        value="<h2 style='color: #007bff; margin-bottom: 20px;'>🎵 Dia TTS for Google Colab</h2>"
    )

    # Model loading section
    model_section = widgets.HBox([
        buttons['load_model'],
        widgets.HTML(value="<small style='color: #666; margin-left: 10px;'>Load the TTS model before generating audio</small>")
    ])

    # Text input section
    text_section = widgets.VBox([
        widgets.HTML(value="<h3 style='margin: 15px 0 10px 0; color: #333;'>📝 Text Input</h3>"),
        text_input
    ])

    # Voice mode section
    voice_section = widgets.VBox([
        widgets.HTML(value="<h3 style='margin: 15px 0 10px 0; color: #333;'>🎭 Voice Settings</h3>"),
        voice_mode_dropdown,
        voice_widgets['reference'],
        voice_widgets['predefined'],
        voice_widgets['upload']
    ])

    # Parameters section
    params_section = widgets.VBox([
        widgets.HTML(value="<h3 style='margin: 15px 0 10px 0; color: #333;'>⚙️ Generation Parameters</h3>"),
        widgets.GridBox([
            sliders['speed_factor'],
            sliders['cfg_scale'],
            sliders['temperature'],
            sliders['top_p'],
            sliders['cfg_filter_top_k'],
            sliders['seed'],
            sliders['chunk_size']
        ], layout=widgets.Layout(grid_template_columns="repeat(2, 1fr)"))
    ])

    # Control buttons section
    controls_section = widgets.VBox([
        widgets.HTML(value="<h3 style='margin: 15px 0 10px 0; color: #333;'>🎵 Generate & Play</h3>"),
        widgets.HBox([
            buttons['generate'],
            buttons['play'],
            buttons['download']
        ]),
        progress_bar
    ])

    # Status section
    status_section = widgets.VBox([
        widgets.HTML(value="<h3 style='margin: 15px 0 10px 0; color: #333;'>📊 Status</h3>"),
        status_display
    ])

    # Main layout
    main_layout = widgets.VBox([
        header_box,
        model_section,
        widgets.HTML(value="<hr style='margin: 20px 0;'>"),
        text_section,
        voice_section,
        params_section,
        controls_section,
        status_section
    ])

    # Set up event handlers
    voice_mode_dropdown.observe(
        lambda change: update_voice_widgets_visibility(change['new'], voice_widgets),
        names='value'
    )

    buttons['generate'].on_click(
        lambda button: generate_audio_handler(button, {
            'text_input': text_input,
            'voice_mode': voice_mode_dropdown,
            'sliders': sliders,
            'voice_widgets': voice_widgets,
            'status': status_display,
            'progress': progress_bar,
            'buttons': buttons
        })
    )

    buttons['load_model'].on_click(
        lambda button: load_model_handler(button, status_display)
    )

    buttons['play'].on_click(play_audio_handler)
    buttons['download'].on_click(download_audio_handler)

    # Initialize voice widgets visibility
    update_voice_widgets_visibility(voice_mode_dropdown.value, voice_widgets)

    return main_layout


def display_tts_interface():
    """Display the complete TTS interface."""

    # Check if running in Colab
    try:
        from google.colab import output
        output.enable_custom_widget_manager()
    except ImportError:
        print("Not running in Google Colab")

    interface = create_tts_interface()
    display(interface)

    # Display some helpful information
    display(HTML("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h4 style="color: #007bff; margin-top: 0;">💡 Tips for Dia TTS in Colab:</h4>
        <ul style="margin-bottom: 0;">
            <li><strong>Model Loading:</strong> Click "Load Model" first - this downloads ~1.6GB of model files</li>
            <li><strong>Voice Cloning:</strong> Upload reference audio files and create matching .txt transcript files</li>
            <li><strong>Predefined Voices:</strong> Place .wav files in the voices folder for consistent voice generation</li>
            <li><strong>Text Format:</strong> Use [S1] and [S2] tags for dialogue, (laughs), (sighs) for emotions</li>
            <li><strong>GPU Support:</strong> Enable GPU in Runtime settings for faster generation</li>
        </ul>
    </div>
    """))


# Convenience function for quick generation
def quick_generate(text: str, voice_mode: str = "dialogue", **kwargs) -> Optional[Audio]:
    """Quick generation function for simple use cases."""

    # Ensure model is loaded
    if not get_model_status()['loaded']:
        print("Loading model...")
        if not load_model():
            print("Failed to load model")
            return None

    # Generate audio
    result = generate_speech(text, voice_mode=voice_mode, **kwargs)

    if result is None:
        print("Generation failed")
        return None

    audio_array, sample_rate = result

    # Normalize for playback
    audio_int16 = (audio_array * 32767).astype(np.int16)

    return Audio(audio_int16, rate=sample_rate, autoplay=False)
