import streamlit as st
from pathlib import Path
import io
import numpy as np
import pandas as pd
from PIL import Image
import openpyxl

output_fn = None

st.title("Extrahierung der Datenmatrix aus Digitalen Bildern")

st.write('''Die Pixel-Intensitäten werden aus den Bild-Dateien in eine xlsx-Datei extrahiert. Falls ein einzelnes Bild
         hochgeladen wird, wird für jeden Farbkanal ein separates Worksheet mit der entsprechenden Pixel-Matrix an
         Intensitätswerten Bild-Höhe x Breite  erstellt. Graustufen-Bilder ergeben ein einzelnes Worksheet.\\
         Wenn mehrere Bild-Dateien hochgeladen werden, wird nur ein einzelnes Sheet erstellt. Alle Pixel-Intensitäten
         der der einzelnen Bilder (und deren Farbkanäle) werden in einzelne Zeilen umgeordnet und mit den ursprünglichen 
         Dateinamen indiziert. Achtung: Ungleiche Pixel-Dimensionen der Bilder führen to einer inkonsistenten Anzahl von 
         Spalten im Excel-Sheet.''')

to_greyscale = st.checkbox('In Graustufen kovertieren')

# sheet_per_channel = st.checkbox('arrays of multi-channel input images will be split into separate worksheets of the resulting Excel (one worksheet per channel)')

# reshape_to_row = st.checkbox('Reshape the image array to one row in resulting xlsx-Worksheet. Automatic behaviour for multi-images upload')

scale_to_width = st.number_input('Auf Breite skalieren', value=0)
scale_to_height = st.number_input('Auf Höhe skalieren', value=0)


uploaded_files = st.file_uploader("Wähle eine oder mehrere Bilddatei(en)", accept_multiple_files=True)
if len(uploaded_files) > 1:
    reshape_to_row = True


# create xlsx

#if single image: one sheet per channel, 2d-matrix height x width pixels
#else: one sheet. one row per file, channels appended

if len(uploaded_files) == 1:
    img = Image.open(uploaded_files[0])
    if to_greyscale:
        img = img.convert('L')
    
    if scale_to_width > 0 and scale_to_height > 0:
        img = img.resize((scale_to_width, scale_to_height),               # Tuple representing size
                        resample=None,      # Optional resampling filter
                        box=None,           # Optional bounding box to resize
                        reducing_gap=None   # Optional optimization
                        )
    
    bands = img.getbands() # ('R', 'G', 'B') and for a typical gray-scale image would be ('L',).

    arr = np.asarray(img) # shape: (height, width, n_channels)

    st.write(bands)
    st.write(arr.shape)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        if len(bands) == 1:
            df_tmp = pd.DataFrame(data=arr[:,:]) # ,band_idx
            df_tmp.to_excel(writer, sheet_name=bands[0], index=False, header=False)
        else:
            for band_idx, band_label in enumerate(bands):
                df_tmp = pd.DataFrame(data=arr[:,:,band_idx])
                df_tmp.to_excel(writer, sheet_name=band_label, index=False, header=False)

    output_fn = Path(uploaded_files[0].name).stem + '.xlsx'

if len(uploaded_files) > 1:

    fns = []
    pixel_arrays = []
    
    for uploaded_file in uploaded_files:
        img = Image.open(uploaded_file)
        if to_greyscale:
            img = img.convert('L')
        
        if scale_to_width > 0 and scale_to_height > 0:
            img = img.resize((scale_to_width, scale_to_height),               # Tuple representing size
                            resample=None,      # Optional resampling filter
                            box=None,           # Optional bounding box to resize
                            reducing_gap=None   # Optional optimization
                            )
        
        # bands = img.getbands() # ('R', 'G', 'B') and for a typical gray-scale image would be ('L',).

        arr = np.asarray(img) # shape: (height, width, n_channels)
        st.write(arr.shape)
        n_pixels = 1
        for val in arr.shape:
            n_pixels *= val
        # st.write(arr.reshape(n_pixels).shape)
        
        fns.append(uploaded_file.name)
        pixel_arrays.append(list(arr.reshape(n_pixels)))

    buffer = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.worksheets[0]

    for fn, p_array in zip(fns, pixel_arrays):
        ws.append([fn] + p_array)

    wb.save(buffer)
    output_fn = 'pixel_intensities.xlsx'

if output_fn:
    st.download_button(
            label="Pixel-Intensitäten als xlsx-Datei herunterladen",
            data=buffer,
            file_name=output_fn,
            mime='application/vnd.ms-excel',
        )
