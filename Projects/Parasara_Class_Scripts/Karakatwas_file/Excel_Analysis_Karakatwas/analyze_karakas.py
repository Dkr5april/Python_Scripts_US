import pandas as pd

def run_all_analysis():
    # 1. Load Data
    df = pd.read_csv('fixed_karakas_database.csv')
    
    # Define Domain Mapping
    def get_domain(item):
        item = str(item).lower()
        mapping = {
            'Identity': ['body', 'health', 'vitality', 'head', 'face', 'self'],
            'Wealth': ['wealth', 'money', 'speech', 'family', 'savings', 'food'],
            'Skills': ['courage', 'writing', 'siblings', 'communication', 'effort', 'hobby'],
            'Home': ['property', 'vehicle', 'mother', 'comfort', 'education', 'house'],
            'Progeny': ['child', 'creativity', 'intellect', 'romance', 'wisdom', 'past life'],
            'Conflict': ['debt', 'enemy', 'illness', 'disease', 'competition', 'service'],
            'Partnership': ['marriage', 'spouse', 'partner', 'contract', 'wife', 'husband'],
            'Transformation': ['longevity', 'obstacle', 'research', 'inheritance', 'sudden'],
            'Dharma': ['guru', 'religion', 'father', 'travel', 'luck', 'dharma'],
            'Career': ['career', 'profession', 'job', 'honor', 'fame', 'boss', 'ambition'],
            'Spiritual': ['liberation', 'moksha', 'meditation', 'detachment', 'spirit'],
            'Hidden': ['secret', 'occult', 'intuitive', 'mystery', 'psychic']
        }
        for dom, keys in mapping.items():
            if any(k in item for k in keys): return dom
        return 'General'

    df['Domain'] = df['Item'].apply(get_domain)

    # 2. Prepare the Excel Writer
    with pd.ExcelWriter('Parasara_Master_Lab_Results.xlsx', engine='xlsxwriter') as writer:
        
        # --- METHOD 1: Domain Distribution ---
        df.groupby('Domain').size().to_frame('Count').to_excel(writer, sheet_name='01_Domain_Count')
        
        # --- METHOD 2: Affliction Contrast ---
        df.pivot_table(index='Item', columns='Is_Afflicted', values='Karaka', aggfunc=lambda x: ', '.join(set(x))).to_excel(writer, sheet_name='02_Affliction_Contrast')
        
        # --- METHOD 3: Item Lookup Dictionary ---
        df.groupby('Item')['Karaka'].apply(lambda x: ', '.join(set(x))).to_excel(writer, sheet_name='03_Item_Lookup')
        
        # --- METHOD 4: Karaka/Domain Matrix ---
        pd.crosstab(df['Karaka'], df['Domain']).to_excel(writer, sheet_name='04_Karaka_Domain_Matrix')
        
        # --- METHOD 5: Affliction Risk Ranking ---
        (df.groupby('Karaka')['Is_Afflicted'].mean() * 100).to_frame('Affliction_Rate').sort_values(by='Affliction_Rate', ascending=False).to_excel(writer, sheet_name='05_Risk_Ranking')
        
        # --- METHOD 6: Domain Categorization ---
        df.to_excel(writer, sheet_name='06_Categorized_Master', index=False)
        
        # --- METHOD 7: Top 10 Influential Karakas ---
        df['Karaka'].value_counts().head(10).to_excel(writer, sheet_name='07_Top_Karakas')
        
        # --- METHOD 8: Domain-Specific Affliction Rates ---
        df.groupby('Domain')['Is_Afflicted'].mean().to_excel(writer, sheet_name='08_Domain_Risk')
        
        # --- METHOD 9: Unique Item Count per Planet ---
        df.groupby('Karaka')['Item'].nunique().to_excel(writer, sheet_name='09_Variety_Score')
        
        # --- METHOD 10: Multi-Planetary Items ---
        multi = df.groupby('Item').filter(lambda x: len(x) > 1)
        multi.to_excel(writer, sheet_name='10_Shared_Concepts', index=False)

    print("Success: 'Parasara_Master_Lab_Results.xlsx' created with 10 analytical tabs.")

run_all_analysis()