import os
import cv2
import json
import urllib.request
import numpy as np
import subprocess
import re
from PIL import Image, ImageDraw, ImageFont

def download_fonts():
    fonts_queries = {
        'Cinzel.ttf': 'https://fonts.googleapis.com/css2?family=Cinzel:wght@600',
        'CinzelDecorative.ttf': 'https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700',
        'CormorantGaramond-Italic.ttf': 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@1,400',
        'DMSans-Regular.ttf': 'https://fonts.googleapis.com/css2?family=DM+Sans'
    }
    for name, url in fonts_queries.items():
        if not os.path.exists(name):
            print(f"Downloading {name}...")
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    css = response.read().decode('utf-8')
                urls = re.findall(r'url\((https://[^\)]+\.ttf)\)', css)
                if urls:
                    print(f"  Fetching from: {urls[0]}")
                    urllib.request.urlretrieve(urls[0], name)
                    print(f"Successfully downloaded {name}")
                else:
                    print(f"  Error: No font URL found in CSS for {name}")
            except Exception as e:
                print(f"Failed to download {name}: {e}")

font_cache = {}
def get_font(font_name, size):
    key = (font_name, size)
    if key in font_cache:
        return font_cache[key]
    if os.path.exists(font_name):
        font = ImageFont.truetype(font_name, size)
    else:
        font = ImageFont.load_default()
    font_cache[key] = font
    return font

def wrap_text(text, font, max_width, draw):
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        line_text = ' '.join(current_line)
        if hasattr(draw, 'textbbox'):
            bbox = draw.textbbox((0, 0), line_text, font=font)
            w = bbox[2] - bbox[0]
        else:
            w, _ = draw.textsize(line_text, font=font)
        if w > max_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def draw_centered_text(draw, text, x, y, font, color, shadow_color=None, shadow_offset=(3, 3)):
    if hasattr(draw, 'textbbox'):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    else:
        w, h = draw.textsize(text, font=font)
        
    tx = x - w / 2
    ty = y - h / 2
    
    if shadow_color and len(shadow_color) == 4 and shadow_color[3] > 0:
        draw.text((tx + shadow_offset[0], ty + shadow_offset[1]), text, font=font, fill=shadow_color)
    draw.text((tx, ty), text, font=font, fill=color)

def format_student_name(raw_name):
    match = re.match(r"(.+)\s+\((\d+)\)", raw_name)
    if match:
        name = match.group(1).strip()
        roll = match.group(2).strip()
        return f"({roll} {name})"
    return raw_name

def main():
    print("Initializing video renderer...")
    
    # 1. Download Google Fonts
    download_fonts()
    
    # 2. Check files
    video_path = "fixed.mp4"
    names_path = "names.json"
    audio_path = "../music.mpeg"
    
    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found.")
        return
    if not os.path.exists(names_path):
        print(f"Error: {names_path} not found.")
        return
        
    # Load names
    with open(names_path, 'r') as f:
        names_data = json.load(f)
    birt_names = [format_student_name(n) for n in names_data.get("birt", [])]
    birts_names = [format_student_name(n) for n in names_data.get("birts", [])]
    
    print(f"Loaded {len(birt_names)} BIRT names and {len(birts_names)} BIRTS names.")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"Input Video: {width}x{height} @ {fps:.2f} FPS, {total_frames} frames ({duration:.2f}s)")
    
    # We will render exactly 150 seconds (4500 frames at 30 FPS)
    target_fps = 30.0
    render_frames = int(150 * target_fps)
    
    temp_output = "temp_silent.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, target_fps, (width, height))
    
    # Pre-define fonts
    font_cinzel = 'Cinzel.ttf'
    font_cinzel_dec = 'CinzelDecorative.ttf'
    font_garamond = 'CormorantGaramond-Italic.ttf'
    
    # Prepare Intro scrolling content items (with compressed spacings matching reel.html)
    intro_items_data = [
        {"type": "text", "text": "DASTAAN 2K26", "font": "cinzel_dec", "size": 95, "color": (231, 201, 138, 255), "spacing": 30},
        {"type": "text", "text": "THE FINAL GOOD BYE", "font": "cinzel", "size": 50, "color": (245, 238, 228, 255), "spacing": 110},
        
        {"type": "text", "text": "THE END", "font": "cinzel_dec", "size": 75, "color": (231, 201, 138, 255), "spacing": 30},
        {"type": "text", "text": "CSE DEPARTMENT", "font": "cinzel", "size": 50, "color": (245, 238, 228, 255), "spacing": 25},
        {"type": "text", "text": "BATCH 2022-2026 BIRT & BIRTS", "font": "cinzel", "size": 38, "color": (231, 201, 138, 255), "spacing": 70},
        
        {"type": "sentence", "text": "Some journeys end, but the memories stay forever.", "font": "garamond", "size": 42, "color": (245, 238, 228, 255), "spacing": 50},
        {"type": "sentence", "text": "One day, it just became the last day...", "font": "garamond", "size": 42, "color": (245, 238, 228, 255), "spacing": 50},
        
        {"type": "paragraph", "text": "From the pressure of attendance and assignments to the laughter of canteen talks, from stressful exams and last-minute studies to mass bunks, culturals, photoshoots, crushes, fights, and lifelong memories—every chapter added meaning to our story.", "font": "garamond", "size": 38, "color": (176, 171, 164, 255), "spacing": 50, "max_width": 880},
        
        {"type": "sentence", "text": "What once felt like forever is now a memory we'll keep replaying.", "font": "garamond", "size": 42, "color": (245, 238, 228, 255), "spacing": 50},
        
        {"type": "paragraph", "text": "Late-night submissions, lab vivas, fest preparations, proxy attendance, group studies, endless laughter... these years gave us more than a degree.", "font": "garamond", "size": 38, "color": (176, 171, 164, 255), "spacing": 50, "max_width": 880},
        
        {"type": "paragraph", "text": "To the seniors who inspired, guided, and supported us thank you for leaving behind memories that will echo through these corridors forever.", "font": "garamond", "size": 38, "color": (176, 171, 164, 255), "spacing": 50, "max_width": 880},
        
        {"type": "sentence", "text": "The end of an era, but the beginning of everything else.", "font": "garamond", "size": 42, "color": (245, 238, 228, 255), "spacing": 50},
        
        {"type": "sentence", "text": "Once a part of CSE, always a part of this family.", "font": "garamond", "size": 42, "color": (245, 238, 228, 255), "spacing": 80},
        
        {"type": "credit", "role": "WRITTEN BY", "name": "The Directors", "spacing": 50},
        {"type": "credit", "role": "PRODUCED BY", "name": "CSE Department", "spacing": 50},
        {"type": "credit", "role": "DIRECTED BY", "name": "Respected Faculties", "spacing": 50}
    ]

    # Pre-calculating Layout for Intro Scroll
    print("Performing layout calculation for intro stage...")
    layout_lines = []
    current_y = 0
    dummy_img = Image.new('RGB', (100, 100))
    dummy_draw = ImageDraw.Draw(dummy_img)

    for item in intro_items_data:
        t_type = item["type"]
        spacing = item["spacing"]
        
        if t_type in ["text", "sentence"]:
            font_path = font_cinzel_dec if item["font"] == "cinzel_dec" else (font_garamond if item["font"] == "garamond" else font_cinzel)
            font = get_font(font_path, item["size"])
            color = item["color"]
            text = item["text"]
            
            if hasattr(dummy_draw, 'textbbox'):
                bbox = dummy_draw.textbbox((0, 0), text, font=font)
                h = bbox[3] - bbox[1]
            else:
                _, h = dummy_draw.textsize(text, font=font)
                
            layout_lines.append((text, font, color, current_y + h/2))
            current_y += h + spacing
            
        elif t_type == "paragraph":
            font = get_font(font_garamond, item["size"])
            color = item["color"]
            max_w = item["max_width"]
            lines = wrap_text(item["text"], font, max_w, dummy_draw)
            line_spacing = 12
            for line in lines:
                if hasattr(dummy_draw, 'textbbox'):
                    bbox = dummy_draw.textbbox((0, 0), line, font=font)
                    h = bbox[3] - bbox[1]
                else:
                    _, h = dummy_draw.textsize(line, font=font)
                layout_lines.append((line, font, color, current_y + h/2))
                current_y += h + line_spacing
            current_y += spacing - line_spacing
            
        elif t_type == "credit":
            f_role = get_font(font_cinzel, 28)
            c_role = (231, 201, 138, 255)
            f_name = get_font(font_cinzel, 40)
            c_name = (245, 238, 228, 255)
            
            if hasattr(dummy_draw, 'textbbox'):
                bbox_r = dummy_draw.textbbox((0, 0), item["role"], font=f_role)
                h_r = bbox_r[3] - bbox_r[1]
            else:
                _, h_r = dummy_draw.textsize(item["role"], font=f_role)
                
            layout_lines.append((item["role"], f_role, c_role, current_y + h_r/2))
            current_y += h_r + 15
            
            if hasattr(dummy_draw, 'textbbox'):
                bbox_n = dummy_draw.textbbox((0, 0), item["name"], font=f_name)
                h_n = bbox_n[3] - bbox_n[1]
            else:
                _, h_n = dummy_draw.textsize(item["name"], font=f_name)
                
            layout_lines.append((item["name"], f_name, c_name, current_y + h_n/2))
            current_y += h_n + spacing

    h_intro = current_y
    d_intro = h_intro + height
    
    # Layout config for Phase 2: Student Credits Scroll
    y_start = 190
    y_end = 1820
    viewport_h = y_end - y_start
    line_h = 45 # height per student name line
    
    h_birt = len(birt_names) * line_h
    h_birts = len(birts_names) * line_h
    
    d_birt = h_birt + viewport_h
    d_birts = h_birts + viewport_h

    # Pre-calculating Layout for Outro Stage Scroll (Phase 3)
    outro_items_data = [
        {"type": "text", "text": "We'll miss you all", "font": "cinzel_dec", "size": 64, "color": (231, 201, 138, 255), "spacing": 32},
        {"type": "text", "text": "SPECIAL THANKS", "font": "cinzel", "size": 36, "color": (231, 201, 138, 255), "spacing": 8},
        {"type": "text", "text": "TO Our Faculties, Seniors & Families", "font": "garamond", "size": 32, "color": (245, 238, 228, 255), "spacing": 6},
        {"type": "text", "text": "Who Made These Years So Beautiful", "font": "garamond", "size": 32, "color": (245, 238, 228, 255), "spacing": 22},
        {"type": "text", "text": "THANK YOU FOR THE MEMORIES", "font": "cinzel", "size": 44, "color": (231, 201, 138, 255), "spacing": 0}
    ]
    outro_layout_lines = []
    current_y_o = 0
    for item in outro_items_data:
        font_path = font_cinzel_dec if item["font"] == "cinzel_dec" else (font_garamond if item["font"] == "garamond" else font_cinzel)
        font = get_font(font_path, item["size"])
        color = item["color"]
        text = item["text"]
        
        if hasattr(dummy_draw, 'textbbox'):
            bbox = dummy_draw.textbbox((0, 0), text, font=font)
            h = bbox[3] - bbox[1]
        else:
            _, h = dummy_draw.textsize(text, font=font)
            
        outro_layout_lines.append((text, font, color, current_y_o + h/2))
        current_y_o += h + item["spacing"]
        
    h_outro_scroll = current_y_o

    print("Starting frame rendering...")
    for frame_idx in range(render_frames):
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))
            
        t = frame_idx / target_fps
               # 1. Process background (Blur & brightness) in OpenCV
        if t < 30.0:
            # 0.5% blur (approx 0.5px CSS / kernel 3x3) + 60% brightness
            blurred = cv2.GaussianBlur(frame, (3, 3), 0)
            processed = cv2.convertScaleAbs(blurred, alpha=0.60, beta=0)
        else:
            # 1% blur (approx 1px CSS / kernel 5x5) + 55% brightness
            blurred = cv2.GaussianBlur(frame, (5, 5), 0)
            processed = cv2.convertScaleAbs(blurred, alpha=0.55, beta=0)
            
        # Optimization: nothing is visible for the first 1 sec
        if t < 1.0:
            out.write(processed)
            if frame_idx % 150 == 0:
                print(f"Rendered {frame_idx}/{render_frames} frames ({t:.1f}s)...")
            continue

        # Zero-copy conversion to PIL Image and convert to RGBA to draw with alpha blending
        processed_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
        pil_img = Image.frombuffer("RGB", (width, height), processed_rgb.data, "raw", "RGB", 0, 1).convert("RGBA")
        draw = ImageDraw.Draw(pil_img)
        
        # Calculate Scroll Math for Intro Stage
        Y_start = height
        Y_end = -h_intro + 10
        
        if t < 1.0:
            translateY = Y_start
        else:
            p = (t - 1.0) / 29.0
            translateY = Y_start + p * (Y_end - Y_start)

        if t < 150.0:
            # Phase 1, 2 & 3: College Headers scrolling together and locking at 50.0
            if t < 30.0:
                y_headers_scroll = translateY + h_intro + 10.0
                y_headers = max(50.0, y_headers_scroll)
            elif 30.0 <= t < 115.0:
                y_headers = 50.0
            else:
                # Headers scroll off: 115s to 123s
                p_header = (t - 115.0) / 8.0
                y_headers = 50.0 - p_header * 300.0
                
            if t >= 0.0:
                # Draw College titles
                draw_centered_text(
                    draw, "BIRT", width // 4, y_headers,
                    get_font(font_cinzel, 36), (231, 201, 138, 255),
                    shadow_color=(0, 0, 0, 255), shadow_offset=(2, 2)
                )
                draw_centered_text(
                    draw, "BIRTS", 3 * width // 4, y_headers,
                    get_font(font_cinzel, 36), (231, 201, 138, 255),
                    shadow_color=(0, 0, 0, 255), shadow_offset=(2, 2)
                )

            # Phase 1: Intro Scroll (0s to 30s)
            if 0.0 <= t < 30.0:
                # Draw intro items
                for line_text, font, color, y_rel in layout_lines:
                    y_pos = translateY + y_rel
                    if -100 <= y_pos <= height + 100:
                        draw_centered_text(
                            draw, line_text, width // 2, y_pos, font, color,
                            shadow_color=(0, 0, 0, color[3]), shadow_offset=(3, 3)
                        )
                
                # Draw BIRT/BIRTS names scrolling up behind the college headers
                y_scroll_birt = y_headers_scroll - 20
                y_scroll_birts = y_headers_scroll - 20
                
                # BIRT names
                x_birt = width // 4
                for j, name in enumerate(birt_names):
                    y_name = y_scroll_birt + j * line_h
                    if y_start <= y_name <= height + 50:
                        alpha = 255
                        if y_name < y_start + 130:
                            alpha = int(255 * (y_name - y_start) / 130)
                        alpha = max(0, min(255, alpha))
                        if alpha > 0:
                            draw_centered_text(
                                draw, name, x_birt, y_name,
                                get_font(font_cinzel, 24), (245, 238, 228, alpha),
                                shadow_color=(0, 0, 0, alpha), shadow_offset=(2, 2)
                            )
                
                # BIRTS names
                x_birts = 3 * width // 4
                for j, name in enumerate(birts_names):
                    y_name = y_scroll_birts + j * line_h
                    if y_start <= y_name <= height + 100:
                        alpha = 255
                        if y_name < y_start + 130:
                            alpha = int(255 * (y_name - y_start) / 130)
                        alpha = max(0, min(255, alpha))
                        if alpha > 0:
                            draw_centered_text(
                                draw, name, x_birts, y_name,
                                get_font(font_cinzel, 24), (245, 238, 228, alpha),
                                shadow_color=(0, 0, 0, alpha), shadow_offset=(2, 2)
                            )

            # Phase 2 & 3: Credits & Outro Scroll (30s to 148s)
            elif 30.0 <= t < 148.0:
                p_names = (t - 30.0) / 93.0
                
                y_scroll_birt = y_start - p_names * (h_birt + 250)
                y_scroll_birts = y_start - p_names * (h_birts + 250)
                
                # Left Column (BIRT)
                x_birt = width // 4
                for j, name in enumerate(birt_names):
                    y_name = y_scroll_birt + j * line_h
                    if y_start <= y_name <= height + 50:
                        alpha = 255
                        if y_name < y_start + 130:
                            alpha = int(255 * (y_name - y_start) / 130)
                        alpha = max(0, min(255, alpha))
                        if alpha > 0:
                            draw_centered_text(
                                draw, name, x_birt, y_name,
                                get_font(font_cinzel, 24), (245, 238, 228, alpha),
                                shadow_color=(0, 0, 0, alpha), shadow_offset=(2, 2)
                            )
                            
                # Right Column (BIRTS)
                x_birts = 3 * width // 4
                for j, name in enumerate(birts_names):
                    y_name = y_scroll_birts + j * line_h
                    if y_start <= y_name <= height + 100:
                        alpha = 255
                        if y_name < y_start + 130:
                            alpha = int(255 * (y_name - y_start) / 130)
                        alpha = max(0, min(255, alpha))
                        if alpha > 0:
                            draw_centered_text(
                                draw, name, x_birts, y_name,
                                get_font(font_cinzel, 24), (245, 238, 228, alpha),
                                shadow_color=(0, 0, 0, alpha), shadow_offset=(2, 2)
                            )

                # Special Thanks starts off-screen and scrolls up to center starting at 115s
                if t < 115.0:
                    y_scroll_outro = height
                else:
                    p_outro = min((t - 115.0) / 33.0, 1.0)
                    y_scroll_outro_start = height
                    y_scroll_outro_end = (height - h_outro_scroll) / 2
                    y_scroll_outro = y_scroll_outro_start + p_outro * (y_scroll_outro_end - y_scroll_outro_start)
                    
                for line_text, font, color, y_rel in outro_layout_lines:
                    y_pos = y_scroll_outro + y_rel
                    if -100 <= y_pos <= height + 200:
                        draw_centered_text(
                            draw, line_text, width // 2, y_pos, font, color,
                            shadow_color=(0, 0, 0, color[3]), shadow_offset=(3, 3)
                        )

            # Phase 4: Wait/Hold at center (148s to 150s)
            elif 148.0 <= t < 150.0:
                y_scroll_outro = (height - h_outro_scroll) / 2
                
                # Special Thanks remains perfectly centered
                for line_text, font, color, y_rel in outro_layout_lines:
                    y_pos = y_scroll_outro + y_rel
                    if -100 <= y_pos <= height + 200:
                        draw_centered_text(
                            draw, line_text, width // 2, y_pos, font, color,
                            shadow_color=(0, 0, 0, color[3]), shadow_offset=(3, 3)
                        )
            
        # Convert back to numpy array via np.asarray (zero-copy wrapper) and convert back to BGR
        cv_frame = cv2.cvtColor(np.asarray(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)
        out.write(cv_frame)
        
        # Display progress every 150 frames
        if frame_idx % 150 == 0:
            print(f"Rendered {frame_idx}/{render_frames} frames ({t:.1f}s)...")
            
    cap.release()
    out.release()
    print("Frames rendering complete! Saved silent video to temp_silent.mp4.")
    
    # 4. Merge Audio using imageio-ffmpeg
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"FFmpeg binary found: {ffmpeg_exe}")
        
        output_file = "Dastaan_2K26.mp4"
        if os.path.exists(output_file):
            os.remove(output_file)
            
        print("Merging audio using FFmpeg...")
        cmd = [
            ffmpeg_exe, "-y",
            "-i", temp_output,
            "-i", audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-ss", "0",
            "-t", "150.0",
            "-shortest",
            output_file
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"Success! Finished rendering video: {output_file}")
            # Clean up temp file
            if os.path.exists(temp_output):
                os.remove(temp_output)
        else:
            print(f"FFmpeg audio merge failed with code {result.returncode}")
            print(result.stderr)
            print("Retaining temp_silent.mp4 as backup.")
    except Exception as e:
        print(f"Could not merge audio: {e}")
        print("Silent video file is saved at temp_silent.mp4")

if __name__ == "__main__":
    main()
