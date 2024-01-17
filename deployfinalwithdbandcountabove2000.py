#pip install mysql-connector-python

import PIL
import streamlit as st
from ultralytics import YOLO
import mysql.connector

model_path = r"C:\Users\DELL\Downloads\bestyolo.pt"
# MySQL database configuration
db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Dhanya.k11!",
    "database": "yolo_db",
}

# Page layout
st.set_page_config(page_title="YOLOv8 Object Detection - Pipe Inventory Management System", layout="wide", initial_sidebar_state="expanded")

# Sidebar
with st.sidebar:
    st.header("Image selection")
    source_img = st.file_uploader("Upload an image", type=("jpg", "jpeg", "png"))
    confidence = float(st.slider("Select model confidence", 25, 100, 40)) / 100

st.title("YOLOv8 Object Detection - Pipe Inventory Management System")
st.caption("STEP 1: Upload an image(jpg, jpeg, png) by clicking on 'Browse files'")
st.caption("STEP 2: Adjust the model confidence value")
st.caption("STEP 3: Click on the DETECT OBJECTS button to see the pipes detected and their count")

col1, col2 = st.columns(2)

with col1:
    if source_img:
        uploaded_image = PIL.Image.open(source_img)
        st.image(source_img, caption="Uploaded image", use_column_width=True)

try:
    model = YOLO(model_path)
except Exception as ex:
    st.error("Unable to load the model. Check the specified path: " + model_path)
    st.error(ex)

# ...

with col2:
    if st.sidebar.button('DETECT OBJECTS'):
        # Your existing object detection code here...
        res = model.predict(uploaded_image, conf=confidence,max_det=2000)
        boxes = res[0].boxes
       
       
        num_boxes = len(boxes)  # Total count of detected boxes
    
          
    
            # Create a dictionary to count each class separately
        class_counts = {}
        class_name_map = {
                0: 'C 32 2.5' ,
                1: 'C 38 2.9' ,
                2: 'C 48 2.9' ,
                3: 'R 20 40 1.9' ,
                4: 'R 25 75 1.9' ,
                5: 'R 48 96 2.0' ,
                6: 'R 48 96 2.9' ,
                7: 'R 60 40 1.9' ,
                8: 'R 80 40 1.2' ,
                9: 'R 96 48 2.0' ,
                10: 'R 96 48 2.9' ,
                11: 'S 20 20 1.2' ,
                12: 'S 20 20 1.5' ,
                13: 'S 20 20 1.9' ,
                14: 'S 25 25 1.9' ,
                15: 'S 25 25 2.5' ,
                16: 'S 38 38 1.9' ,
                17: 'S 40 40 2.5' ,
                18: 'S 50 50 1.5' ,
                19: 'S 50 50 1.9' ,
                20: 'S 50 50 4.0' ,
                21: 'S 60 60 2.0' ,
                22: 'S 72 72 4.0' ,
                23: 'S 72 72 4.8' ,
                
        }
        for box in boxes:
                # Access the last element of the tensor to get the class label
                class_label = int(box.cls)  # Convert to integer
                class_name = class_name_map.get(class_label , "Unknown")
                if class_name not in class_counts:
                    class_counts[class_name] = 1
                else:
                    class_counts[class_name] += 1
                    
        res_plotted = res[0].plot()[:, :, ::-1]
    
        
        st.image(res_plotted, caption='Detected image with classes', use_column_width=True)
        if num_boxes == 0:
                st.error("No objects detected in the image.")
        else:
                st.write(f"Number of detected objects: {num_boxes}")
        st.write("Count of each class:")
        for class_name, count in class_counts.items():
                st.write(f"{class_name}: {count}")

    
        try:
                with st.expander("Detected results"):
                    for box in boxes:
                        st.write(box.data)
                    
        except Exception as ex:
                st.write("No image uploaded yet!!!")
        
        # Calculate the total number of detected objects
        total_objects = sum(class_counts.values())
        
        # Establish a connection to the MySQL database
        # ... (previous code)

# Establish a connection to the MySQL database
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
        except Exception as db_error:
            st.error("Unable to connect to the MySQL database.")
            st.error(db_error)
            st.stop()
        
        # Create a list of class names from the class_name_map dictionary
        class_names = list(class_name_map.values())
        
        # Replace problematic characters in class names with underscores
        def sanitize_class_name(class_name):
            return class_name.replace(" ", "_").replace(".", "_").replace("-", "_")
        
        # Create a table if it doesn't exist
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS detected_objects (
                
                session_id INT,
                total_objects INT,
                {}
            )
        '''.format(', '.join(["{} INT DEFAULT 0".format(sanitize_class_name(class_name)) for class_name in class_names]))
        
        cursor.execute(create_table_query)
        conn.commit()
        
        # Get the last session ID to keep track of sessions
        get_last_session_id_query = "SELECT MAX(session_id) FROM detected_objects"
        cursor.execute(get_last_session_id_query)
        last_session_id = cursor.fetchone()[0]
        
        if last_session_id is None:
            last_session_id = 0
        session_id = last_session_id + 1
        
        # Insert the total count of objects and session ID into the MySQL database
        t_insert_query = "INSERT INTO detected_objects (session_id, total_objects) VALUES (%s, %s)"
        t_insert_data = (session_id, total_objects)
        cursor.execute(t_insert_query, t_insert_data)
        conn.commit()
        
        # Insert the detected objects counts into the respective sanitized class columns
        for class_name, count in class_counts.items():
            sanitized_class_name = sanitize_class_name(class_name)
            insert_query = "UPDATE detected_objects SET {} = %s WHERE session_id = %s".format(sanitized_class_name)
            insert_data = (count, session_id)
            cursor.execute(insert_query, insert_data)
            conn.commit()
            st.write(f"Inserted into MySQL: {class_name}: {count} (Session ID: {session_id})")
        
        # Close the database connection when you're done
        conn.close()
        
        
