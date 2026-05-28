import swisseph as swe
import pandas as pd
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import track
from rich.panel import Panel
import os
import re

console = Console()

# ==================== KP ENGINE LOGIC ====================
class KPHoraryHunter:
    def __init__(self, lat, lon, horary_num, rotate_to):
        self.lat = lat
        self.lon = lon
        self.horary_num = horary_num
        self.rotate_to = rotate_to
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        
        self.PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
        self.DAS_YRS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

    def get_horary_lagna(self, num):
        segments = []
        start = 0.0
        for star in range(27):
            for sub in range(9):
                sub_lord_idx = (star + sub) % 9
                length = (self.DAS_YRS[sub_lord_idx] / 120.0) * (360/27)
                segments.append((start, self.PLANET_LIT[sub_lord_idx]))
                start += length
        return segments[num-1][0]

    def get_lords(self, lon):
        nak_len = 360/27
        rem = lon % nak_len
        star_idx = int(lon // nak_len) % 9
        acc = 0
        sub_lord, ss_lord = "", ""
        for i in range(9):
            idx = (star_idx + i) % 9
            part = (self.DAS_YRS[idx] / 120) * nak_len
            if acc + part >= rem:
                sub_lord = self.PLANET_LIT[idx]
                sub_rem = rem - acc
                ss_acc = 0
                for j in range(9):
                    ss_idx = (idx + j) % 9
                    ss_part = (self.DAS_YRS[ss_idx] / 120) * part
                    if ss_acc + ss_part >= sub_rem:
                        ss_lord = self.PLANET_LIT[ss_idx]
                        break
                    ss_acc += ss_part
                break
            acc += part
        return [self.PLANET_LIT[star_idx], sub_lord, ss_lord]

    def get_target_cusp_details(self, dt):
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60 + dt.second/3600 - 5.5)
        cusps, ascmc = swe.houses_ex(t_jd, self.lat, self.lon, b'P', swe.FLG_SIDEREAL)
        horary_start = self.get_horary_lagna(self.horary_num)
        shift = horary_start - cusps[0]
        idx = (self.rotate_to + 12 - 2) % 12
        target_lon = (cusps[idx] + shift) % 360
        return self.get_lords(target_lon)

def parse_date(date_str):
    """Robust parser for DD/MM/YYYY HH:MM:SS."""
    # Remove any leading/trailing spaces and replace separators
    clean = date_str.strip()
    clean = re.sub(r'[./-]', '/', clean)
    # This format is very strict: must be exactly DD/MM/YYYY HH:MM:SS
    return datetime.strptime(clean, "%d/%m/%Y %H:%M:%S")

# ==================== MAIN PROGRAM ====================
def main():
    console.print("\n[bold cyan]STEP 1: REFERENCE CHART DATA[/]\n")
    
    try:
        h_num = int(input("Enter Horary Number (1-249): ") or 1)
        rotate = int(input("Rotate Lagna to House (1-12) [Default 1]: ") or 1)
        lat = float(input("Latitude: ") or 17.40)
        lon = float(input("Longitude: ") or 78.47)
        
        console.print("[dim italic]Enter as DD/MM/YYYY HH:MM:SS (Include seconds!)[/]")
        ref_date_in = input("Reference Time: ")
        ref_dt = parse_date(ref_date_in)
        
    except Exception as e:
        console.print(f"[bold red]Input Error:[/] {e}")
        return

    engine = KPHoraryHunter(lat, lon, h_num, rotate)
    lords = engine.get_target_cusp_details(ref_dt)
    target_sl = lords[1]

    summary = f"""
    [bold yellow]Horary:[/] {h_num} | [bold yellow]Reference:[/] {ref_dt.strftime('%d/%m/%Y %H:%M:%S')}
    [bold yellow]House:[/] 12th from H{rotate}
    
    [bold green]TARGET SUB-LORD (SL):[/] [reverse] {target_sl} [/]
    """
    console.print(Panel(summary, title="REFERENCE CAPTURED", border_style="bright_blue"))

    console.print("\n[bold cyan]STEP 2: SCANNING RANGE[/]")
    try:
        scan_start_in = input("Scan START (DD/MM/YYYY HH:MM:SS): ")
        scan_end_in = input("Scan END   (DD/MM/YYYY HH:MM:SS): ")
        
        start_dt = parse_date(scan_start_in)
        end_dt = parse_date(scan_end_in)
    except Exception as e:
        console.print(f"[bold red]Format Error:[/] {e}")
        console.print("[yellow]Ensure you use 2-digit seconds, e.g., 19:30:00[/]")
        return

    console.print(f"\n[cyan]Hunting for windows where 12th SS-Lord is {target_sl}...[/]\n")
    results, current = [], start_dt
    
    check_interval = 5 
    step = timedelta(seconds=check_interval)
    
    is_active, entry_time = False, None
    total_seconds = int((end_dt - start_dt).total_seconds())
    total_steps = total_seconds // check_interval

    for _ in track(range(total_steps), description="High-Speed Scan"):
        cur_lords = engine.get_target_cusp_details(current)
        if cur_lords[2] == target_sl and not is_active:
            is_active, entry_time = True, current
            console.print(f"[bold green]>> ENTRY:[/][white] {current.strftime('%H:%M:%S')}[/]")
        elif cur_lords[2] != target_sl and is_active:
            is_active = False
            duration = current - entry_time
            results.append({
                "Horary": h_num, "Base_H": rotate, "Target_SL": target_sl,
                "Start_Time": entry_time.strftime("%d/%m/%Y %H:%M:%S"),
                "End_Time": current.strftime("%d/%m/%Y %H:%M:%S"),
                "Duration": str(duration)
            })
            console.print(f"[bold red]<< EXIT :[/][white] {current.strftime('%H:%M:%S')} (Dur: {duration})[/]")
        current += step

    if results:
        df = pd.DataFrame(results)
        fname = f"Sports_Scan_H{rotate}_{target_sl}.xlsx"
        df.to_excel(fname, index=False)
        console.print(f"\n[bold green]COMPLETED![/] Results in [white]{fname}[/]")
    else:
        console.print("\n[bold red]No Sub-Sub-Lord matches found.[/]")

if __name__ == "__main__":
    main()