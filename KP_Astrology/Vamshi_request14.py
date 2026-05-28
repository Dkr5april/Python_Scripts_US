# ... (Keep all previous V87 classes/logic same) ...

# ========================== EXECUTION ============================
engine = KPEngineV87(DOB, TOB, LAT, LON)
step = {"1m":timedelta(minutes=1), "15m":timedelta(minutes=15), "1h":timedelta(hours=1)}[FREQ]

rows = []
curr = START_DT
total_steps = int((END_DT - START_DT).total_seconds() / step.total_seconds())
current_step = 0

print(f"🚀 Starting KP Analysis for {NAME}...")
print(f"📅 Period: {START_DT} to {END_DT}")

while curr <= END_DT:
    engine.refresh(curr)
    dashas = engine.dasha6(curr)
    for lvl, p in zip(["MAHA","BHUKTI","ANTARA","SOOKSHMA","PRANA","DEHA"], dashas):
        instr, net, aspc, n = engine.analyze(p)
        rows.append({
            "Time": curr.strftime("%Y-%m-%d %H:%M"), "Level": lvl, "Planet": p,
            "Intensity_Strip": instr, "Net_Strength": net, 
            "Aspect_Score": aspc, "Western_Triggers": n
        })
    
    # Progress indicator
    current_step += 1
    if current_step % 10 == 0:
        print(f"⏳ Processing... {int((current_step/total_steps)*100)}% complete", end="\r")
        
    curr += step

print("\n\n✅ Analysis Complete!")
df = pd.DataFrame(rows)
df.to_excel(OUT_FILE, index=False)
print(f"📂 FILE SAVED: Open '{OUT_FILE}' to see the intensity data.")