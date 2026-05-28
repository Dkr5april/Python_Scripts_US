import time
from datetime import datetime, timedelta
from pynput import keyboard
from rich.live import Live

# Import our modules
import config
from engine.astro_engine import AstroEngine
from engine.market_dasa import get_market_dasa_levels
from logic.rules_processor import evaluate_market_rules
from ui.dashboard import create_dashboard_layout

# Initialize
astro = AstroEngine()
view_date = datetime.now().replace(hour=config.MARKET_OPEN_HOUR, minute=config.MARKET_OPEN_MINUTE)
is_running = True

def on_press(key):
    global view_date, is_running
    try:
        if key == keyboard.Key.right: view_date += timedelta(minutes=5)
        elif key == keyboard.Key.left: view_date -= timedelta(minutes=5)
        elif key == keyboard.Key.up: view_date += timedelta(days=1)
        elif key == keyboard.Key.down: view_date -= timedelta(days=1)
        elif key == keyboard.Key.esc: is_running = False
    except: pass

if __name__ == "__main__":
    keyboard.Listener(on_press=on_press).start()
    
    with Live(screen=True, refresh_per_second=4) as live:
        while is_running:
            # 1. Get Data
            data = astro.get_full_snapshot(view_date)
            # 2. Process Logic
            logic = evaluate_market_rules(data, view_date)
            # 3. Get Dasa
            dasa = get_market_dasa_levels(view_date)
            # 4. Update UI
            layout = create_dashboard_layout(data, logic, dasa, view_date, "Live Analysis")
            live.update(layout)
            time.sleep(0.1)