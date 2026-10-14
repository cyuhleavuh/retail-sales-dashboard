## Cleaning And Prep ## 

original dataset: https://www.kaggle.com/datasets/ozlemilgun/online-retail-dataset


```python
import pandas as pd
import re
import os
```


```python
# Load Data
file_path = 'data/online_retail_II.xlsx'

sheet1 = pd.read_excel(file_path, sheet_name='Year 2009-2010')
sheet2 = pd.read_excel(file_path, sheet_name='Year 2010-2011')
raw_data = pd.concat([sheet1, sheet2], ignore_index=True)
```


```python
# Initial diagnostic checkpoint, looking for duplicates and nulls
raw_data.info()
print(raw_data.isnull().sum())
print(f"Duplicate rows: {raw_data.duplicated().sum()}")
```

    <class 'pandas.DataFrame'>
    RangeIndex: 1067371 entries, 0 to 1067370
    Data columns (total 8 columns):
     #   Column       Non-Null Count    Dtype         
    ---  ------       --------------    -----         
     0   Invoice      1067371 non-null  object        
     1   StockCode    1067371 non-null  object        
     2   Description  1062989 non-null  object        
     3   Quantity     1067371 non-null  int64         
     4   InvoiceDate  1067371 non-null  datetime64[us]
     5   Price        1067371 non-null  float64       
     6   Customer ID  824364 non-null   float64       
     7   Country      1067371 non-null  str           
    dtypes: datetime64[us](1), float64(2), int64(1), object(3), str(1)
    memory usage: 78.8+ MB
    Invoice             0
    StockCode           0
    Description      4382
    Quantity            0
    InvoiceDate         0
    Price               0
    Customer ID    243007
    Country             0
    dtype: int64
    Duplicate rows: 34335
    


```python
# Fixing Data Types
raw_data['Customer ID'] = raw_data['Customer ID'].astype('Int64')
raw_data['Invoice'] = raw_data['Invoice'].astype('str')
raw_data['StockCode'] = raw_data['StockCode'].astype('str')
```


```python
# Cleaning text formatting - 'Description' column
raw_data['Description'] = raw_data['Description'].str.strip().str.upper()
```


```python
# Removing exact duplicate rows
raw_data = raw_data.drop_duplicates()
print(f"Rows after dropping duplicates: {len(raw_data)}")
```

    Rows after dropping duplicates: 1033036
    


```python
# Removing junk/non-product descriptions
junk_patterns = [
    r'\?',
    r'\bDAMAGE\b', r'\bDAMAGED\b', r'\bDAMAGES\b', r'\bDAGAMED\b',
    r'\bWET\b', r'\bRUSTY\b',                    
    r'\bMOULDY\b', r'\bCRUSHED\b', r'\bBROKEN\b',
    r'\bTHROWN AWAY\b', r'\bTHROW AWAY\b',
    r'\bMISSING\b', r'\bMISSINGS\b', r"\bCAN'?T FIND\b", r'\bLOST\b',
    r'\bWRONG\b', r'\bWRONGLY\b', r'\bINCORRECT\b', r'\bINCORRECTLY\b',
    r'\bMIX UP\b', r'\bMIXED WITH\b',
    r'\bADJUST\b', r'\bADJUSTMENT\b',
    r'\bERROR\b', r'\bMISTAKE\b',
    r'\bSOLD AS\b', r'\bSOLD IN\b', r'\bSOLD SET\b', r'\bSOLD SETS\b', r'\bSOLD WITH\b',
    r'\bDOTCOM\b', r'\bAMAZON\b', r'\bEBAY\b', r'\bFBA\b', r'\bASOS\b',
    r'\bJOHN LEWIS\b', r'\bDEBENHAMS\b',
    r'\bSHOWROOM\b',                              
    r'\bCARTON\b', r'\bCTN\b', r'\bINVC\b', r'\bINVOICE\b', r'\bBARCODE\b',
    r'\bCREDIT\b', r'\bCREDITTED\b', r'\bRETURNS\b',
    r'\bFOUND\b', r'\bCHECK\?', r'\bREVERSE\b', r'\bTEMP FIX\b', r'\bQUICK FIX\b', r'\bFIXED\b',
    r'\bDIRTY\b', r'\bPOOR QUALITY\b', r'\bUNSELLABLE\b', r'\bUNEVEN\b', r'\bWONKY\b',
    r'^\d+[A-Z]?$',
    r'\bSAID SO\b', r'\bCANT MAMAGE\b', r'\bFOUND BY\b', r'\bOOPS\b',
]
junk_regex = re.compile('|'.join(junk_patterns), flags=re.IGNORECASE)
junk_mask = raw_data['Description'].fillna('').str.contains(junk_regex)

junk_data = raw_data[junk_mask]          # keep for loss analysis
clean_data = raw_data[~junk_mask]      

print(f"Rows flagged as junk: {len(junk_data)}")
print(f"Rows remaining: {len(clean_data)}")
```

    Rows flagged as junk: 2215
    Rows remaining: 1030821
    


```python
# Standardizing Description to most common variant per StockCode, accounting for nulls
def get_most_common_description(x):
    counts = x.value_counts()
    if counts.empty:
        return None  # no valid description exists for this StockCode
    return counts.idxmax()

description_lookup = (
    clean_data.groupby('StockCode')['Description']
    .agg(get_most_common_description)
    .reset_index()
    .rename(columns={'Description': 'Clean_Description'})
)

no_desc_codes = description_lookup.loc[description_lookup['Clean_Description'].isnull(), 'StockCode'].tolist()
print(f"{len(no_desc_codes)} of {len(description_lookup):,} StockCodes have no valid description")
```

    360 of 5,292 StockCodes have no valid description
    

Decision: StockCodes with no usable description (360 codes, 6.8%) cover 369 rows, all priced £0.00 (likely internal or promotional entries), so they are removed.


```python
affected = clean_data[clean_data['StockCode'].isin(no_desc_codes)]
affected_revenue = (affected['Price'] * affected['Quantity']).sum()
print(f"Rows affected: {len(affected):,} | Revenue affected: £{affected_revenue:,.2f}")

assert abs(affected_revenue) < 0.01, "No-description codes carry revenue; review before removing"
clean_data = clean_data[~clean_data['StockCode'].isin(no_desc_codes)]
```

    Rows affected: 369 | Revenue affected: £0.00
    

Decision: Codes that don’t match the usual product-code pattern (4-6 digits plus up to 3 letters) were reviewed by hand. The DCGS…, 47503J, PADS and SP1002 codes are real products and are kept. Administrative codes (bank charges, carriage, discounts, samples, manual entries, test products, gift vouchers) are removed.


```python
# Review: codes that don't match the typical product pattern (no-description codes are already gone)
product_code_pattern = re.compile(r'^\d{4,6}[A-Za-z]{0,3}$')
codes_left = description_lookup[~description_lookup['StockCode'].isin(no_desc_codes)]
print(codes_left.loc[~codes_left['StockCode'].str.match(product_code_pattern),
                     ['StockCode', 'Clean_Description']].to_string(index=False))

# Confirmed administrative codes to exclude
non_product_codes = [
    'BANK CHARGES', 'C2', 'CRUK', 'D', 'M', 'm', 'POST', 'S',
    'TEST001', 'TEST002',
    'gift_0001_10', 'gift_0001_20', 'gift_0001_30', 'gift_0001_40',
    'gift_0001_50', 'gift_0001_70', 'gift_0001_80',
]
clean_data = clean_data[~clean_data['StockCode'].isin(non_product_codes)].copy()

# Apply the canonical description (every remaining code has one)
desc_map = description_lookup.set_index('StockCode')['Clean_Description']
clean_data['Description'] = clean_data['StockCode'].map(desc_map)

assert clean_data['Description'].notnull().all()
print(f"Remaining rows: {len(clean_data):,}")  
assert len(clean_data) == 1_026_194
```

       StockCode                  Clean_Description
         47503J    SET/3 FLORAL GARDEN TOOLS IN BAG
    BANK CHARGES                       BANK CHARGES
              C2                           CARRIAGE
            CRUK                    CRUK COMMISSION
               D                           DISCOUNT
        DCGS0003                BOXED GLASS ASHTRAY
        DCGS0004         HAYNES CAMPER SHOULDER BAG
        DCGS0037                 KEY-RING CORKSCREW
        DCGS0041   HAYNES MINI-COOPER PLAYING CARDS
        DCGS0044            HANDZ-OFF CAR FRESHENER
        DCGS0058                   MISO PRETTY  GUM
        DCGS0062            ROAD-RAGE CAR FRESHENER
       DCGS0066N            NAVY CUDDLES DOG HOODIE
        DCGS0068                  DOGS NIGHT COLLAR
        DCGS0069              OOH LA LA DOGS COLLAR
        DCGS0070              CAMOUFLAGE DOG COLLAR
        DCGS0072             CAT CAMOUFLAGUE COLLAR
        DCGS0075               CAMOUFLAGUE DOG LEAD
        DCGS0076       SUNJAR LED NIGHT NIGHT LIGHT
        DCGSSBOY                     BOYS PARTY BAG
       DCGSSGIRL                    GIRLS PARTY BAG
               M                             MANUAL
            PADS         PADS TO MATCH ALL CUSHIONS
            POST                            POSTAGE
               S                            SAMPLES
          SP1002             KID'S CHALKBOARD/EASEL
         TEST001            THIS IS A TEST PRODUCT.
         TEST002            THIS IS A TEST PRODUCT.
    gift_0001_10 DOTCOMGIFTSHOP GIFT VOUCHER £10.00
    gift_0001_20 DOTCOMGIFTSHOP GIFT VOUCHER £20.00
    gift_0001_30 DOTCOMGIFTSHOP GIFT VOUCHER £30.00
    gift_0001_40 DOTCOMGIFTSHOP GIFT VOUCHER £40.00
    gift_0001_50 DOTCOMGIFTSHOP GIFT VOUCHER £50.00
    gift_0001_70 DOTCOMGIFTSHOP GIFT VOUCHER £70.00
    gift_0001_80 DOTCOMGIFTSHOP GIFT VOUCHER £80.00
               m                             MANUAL
    Remaining rows: 1,026,194
    


```python
#Adding Revenue, Year, Month, MonthName, YearMonth, and DayofWeek columns
clean_data['Revenue'] = clean_data['Price'] * clean_data['Quantity']
clean_data['Year'] = clean_data['InvoiceDate'].dt.year
clean_data['Month'] = clean_data['InvoiceDate'].dt.month
clean_data['MonthName'] = clean_data['InvoiceDate'].dt.month_name()
clean_data['YearMonth'] = clean_data['InvoiceDate'].dt.to_period('M').astype(str)
clean_data['DayOfWeek'] = clean_data['InvoiceDate'].dt.day_name()
```


```python
# Orders placed and fully cancelled within minutes (entry errors, ~500-1,000x a typical order)
# Removing with their cancellations so neither side is counted
reversed_pairs = [
    ('581483', 'C581484', '23843'),
    ('541431', 'C541433', '23166'),
]

# Single outsized entry error: 60 units @ £649.50; a corrected line (1 unit @ £649.50) follows in 556446
entry_error_lines = [('556444', '22502')]

mask = pd.Series(False, index=clean_data.index)
for sale_inv, cancel_inv, code in reversed_pairs:
    mask |= clean_data['Invoice'].isin([sale_inv, cancel_inv]) & (clean_data['StockCode'] == code)
for inv, code in entry_error_lines:
    mask |= (clean_data['Invoice'] == inv) & (clean_data['StockCode'] == code)

assert mask.sum() == 5, f"Expected 5 rows to remove, found {mask.sum()}"

print(clean_data.loc[mask, ['Invoice', 'StockCode', 'Quantity', 'Price', 'Revenue']])
clean_data = clean_data[~mask].copy()

assert len(clean_data) == 1_026_189
```

             Invoice StockCode  Quantity   Price   Revenue
    587080    541431     23166     74215    1.04   77183.6
    587085   C541433     23166    -74215    1.04  -77183.6
    748132    556444     22502        60  649.50   38970.0
    1065882   581483     23843     80995    2.08  168469.6
    1065883  C581484     23843    -80995    2.08 -168469.6
    


```python
# Standardizing country names to common English names
country_map = {'EIRE': 'Ireland', 'RSA': 'South Africa', 'USA': 'United States of America'}
clean_data['Country'] = clean_data['Country'].replace(country_map)
```


```python
# Separating cancelled orders from completed sales
cncld = clean_data[clean_data['Invoice'].str.startswith('C')].copy()
sales = clean_data[~clean_data['Invoice'].str.startswith('C')].copy()

assert len(cncld) + len(sales) == len(clean_data)
```


```python
# Filtering out negative/zero Price & Quantity
cln_sales = sales[(sales['Price'] > 0) & (sales['Quantity'] > 0)].copy()
```


```python
# Splitting orders with no Customer ID from known-customer orders
no_custID_sales = cln_sales[cln_sales['Customer ID'].isnull()].copy()
custID_sales = cln_sales[cln_sales['Customer ID'].notnull()].copy()
```


```python
# Saving dataframes to disk
os.makedirs('data', exist_ok=True)

clean_data.to_parquet('data/clean_data.parquet')
sales.to_parquet('data/sales.parquet')
cln_sales.to_parquet('data/cln_sales.parquet')
custID_sales.to_parquet('data/custID_sales.parquet')
no_custID_sales.to_parquet('data/no_custID_sales.parquet')
cncld.to_parquet('data/cncld.parquet')
junk_data.to_parquet('data/junk_data.parquet')  # audit trail of removed junk rows
```

## Cleaning Summary

### Row-count funnel
| Step | Rows remaining | Removed |
|---|---|---|
| After dropping exact duplicates | 1,033,036 | 34,335 |
| After junk-description filter | 1,030,821 | 2,215 |
| After no-description and non-product codes | 1,026,194 | 4,627 |
| After the 5-line entry-error removal | 1,026,189 | 5 |

### Decisions
- **Gross-sales convention.** `cln_sales` is gross sales: orders that were later cancelled or returned stay in. Cancellations are tracked separately in `cncld`. The source has no field linking a cancellation to its original sale, so netting them out would require guesswork (matching on customer, product, quantity and date).
- **Entry-error removal (5 lines, 3 orders).** Two orders placed and reversed within minutes (581483 / C581484 and 541431 / C541433) were removed together with their cancellations, and one outsized single line (invoice 556444, 60 units of 22502 at £649.50, with a corrected line in 556446) was removed. In total this took out £284,623.20 (~1.4% of revenue), 3 orders and 155,270 units. Removing both sides of each reversed pair keeps the order and cancellation counts consistent.
- **Country names.** `EIRE` → `Ireland`, `RSA` → `South Africa`, `USA` → `United States of America`, names have been changed for English readability.
