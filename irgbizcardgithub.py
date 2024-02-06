#importing the necessary libraries
import mysql.connector as sql
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re

# Main Streamlit app
if __name__ == "__main__":
    # Main Streamlit code starts
    # SETTING PAGE CONFIGURATIONS
    icon = Image.open("guvi_logo.png")
    st.set_page_config(
        page_title="BizCardX: Extracting Business Card Data with OCR | By IRG",
        page_icon= icon,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={'About': """# This application is created for GUVI Capstone Project3 by *IRG!*"""}
    )
    st.header("BizCardX: Extracting Business Card Data with OCR | By IRG")
    
    # CREATING OPTION MENU
    with st.sidebar:
        selected = option_menu(None, ["Home", "Add Business Card", "Existing Card Details"], 
                                icons=["house-door-fill","plus-circle","search"],
                                default_index=0,
                                orientation="vertical",
                                styles={"nav-link": {"font-size": "24px", "text-align": "centre", "margin": "0px", 
                                                        "--hover-color": "#FF4B4B"},
                                        "icon": {"font-size": "24px"},
                                        "container" : {"max-width": "7000px"},
                                        "nav-link-selected": {"background-color": "Reds"}})
    # MySQL connection parameters
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'xxxxxx', ## Acutal password
        'auth_plugin': 'mysql_native_password',  # Use a compatible authentication plugin

    }

    # Establish the connection and create a cursor
    mydb = sql.connect(**config)
    mycursor = mydb.cursor(buffered=True)

    # Create the 'bizcardx_db' database if it doesn't exist
    mycursor.execute("CREATE DATABASE IF NOT EXISTS bizcardx_db")

    # Commit the changes and close the connection
    mydb.commit()
    mydb.close()

    # To connect to the 'bizcardx_db' database
    config['database'] = 'bizcardx_db'
    mydb = sql.connect(**config)
    mycursor = mydb.cursor(buffered=True)

    # Table creating
    mycursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                    (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        company_name TEXT,
                        card_holder TEXT,
                        designation TEXT,
                        mobile_number VARCHAR(50),
                        email TEXT,
                        website TEXT,
                        area TEXT,
                        city TEXT,
                        state TEXT,
                        pin_code VARCHAR(10),
                        image LONGBLOB
                        )''')
    # Commit the changes and close the connection
    mydb.commit()
    mydb.close()

    # INITIALIZING THE EasyOCR READER FOR ENGLISH
    reader = easyocr.Reader(['en'], model_storage_directory=".")

    # HOME MENU
    if selected == "Home":
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("#### :red[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
            st.markdown("#### :red[**Overview :**] BizCardX is a user-friendly tool designed for effortless extraction of information from business cards, leveraging the power of Optical Character Recognition (OCR) through the EasyOCR Python library. This project simplifies the OCR process with its straightforward installation, minimal dependencies, and easy integration into your development environment.")
        with col2:
            st.image("guvi_logo.png")

    # BUSINESS CARD MENU
    if selected == "Add Business Card":
        st.markdown("### Upload a Business Card")
        uploaded_card = st.file_uploader("upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"])

        if uploaded_card is not None:
            user_home = os.path.expanduser("~")
            save_path = os.path.join(user_home, "uploaded_cards", uploaded_card.name)
            os.makedirs(os.path.join(user_home, "uploaded_cards"), exist_ok=True)
            saved_img = save_path.replace("\\", "/")

            def save_card(uploaded_card, save_path):
                with open(save_path, "wb") as f:
                    f.write(uploaded_card.getbuffer())

            save_card(uploaded_card, save_path)

            # Extraction logic
            
            def image_preview(image,res): 
                for (bbox, text, prob) in res: 
                # unpack the bounding box
                    (tl, tr, br, bl) = bbox
                    tl = (int(tl[0]), int(tl[1]))
                    tr = (int(tr[0]), int(tr[1]))
                    br = (int(br[0]), int(br[1]))
                    bl = (int(bl[0]), int(bl[1]))
                    cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                    cv2.putText(image, text, (tl[0], tl[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                plt.rcParams['figure.figsize'] = (15,15)
                plt.axis('off')
                plt.imshow(image)
            
            # DISPLAYING THE UPLOADED CARD
            col1,col2 = st.columns(2,gap="large")
            with col1:
                st.markdown("#     ")
                st.markdown("#     ")
                st.markdown("##### You have uploaded the card")
                st.image(uploaded_card)
            # DISPLAYING THE CARD WITH HIGHLIGHTS
            with col2:
                st.markdown("#     ")
                with st.spinner("Please wait Business Card getting processed..."):
                    st.set_option('deprecation.showPyplotGlobalUse', False)
                    image = cv2.imread(saved_img)
                    res = reader.readtext(saved_img)
                    st.markdown("##### Business Card Image is processed and Details Extracted")
                    st.pyplot(image_preview(image,res))  

            #easy OCR
            result = reader.readtext(saved_img,detail = 0,paragraph=False)
            
            def postprocess_ocr(results):
                processed_results = []
                current_line = []

                for text in results:
                    if current_line and text.lower() != current_line[-1].lower() and text[0].isupper():
                        processed_results.append(' '.join(current_line))
                        current_line = [text]
                    else:
                        current_line.append(text)

                if current_line:
                    processed_results.append(' '.join(current_line))
                return processed_results

            # Usage
            processed_result = postprocess_ocr(result)
                  
            # CONVERTING IMAGE TO BINARY TO UPLOAD TO SQL DATABASE
            def img_to_binary(file):
                # Convert image data to binary format
                with open(file, 'rb') as file:
                    binaryData = file.read()
                return binaryData
            
            data = {"company_name" : [],
                    "card_holder" : [],
                    "designation" : [],
                    "mobile_number" :[],
                    "email" : [],
                    "website" : [],
                    "area" : [],
                    "city" : [],
                    "state" : [],
                    "pin_code" : [],
                    "image" : img_to_binary(saved_img)
                }

            def get_data(res):
                for ind,i in enumerate(res):

                    # To get WEBSITE_URL
                    if "www " in i.lower() or "www." in i.lower():
                        data["website"].append(i)
                    elif "WWW" in i:
                        data["website"] = res[4] +"." + res[5]

                    # To get EMAIL ID
                    elif "@" in i:
                        data["email"].append(i)

                    # To get MOBILE NUMBER
                    elif "-" in i:
                        data["mobile_number"].append(i)
                        if len(data["mobile_number"]) ==2:
                            data["mobile_number"] = " & ".join(data["mobile_number"])

                    # To get COMPANY NAME (Need to refine further for optimized output) 
                    elif ind == len(res)-1:
                        data["company_name"].append(i)

                    # To get CARD HOLDER NAME
                    elif ind == 0:
                        data["card_holder"].append(i)

                    # To get DESIGNATION
                    elif ind == 1:
                        data["designation"].append(i)

                    # To get AREA
                    if re.findall('^[0-9].+, [a-zA-Z]+',i):
                        data["area"].append(i.split(',')[0])
                    elif re.findall('[0-9] [a-zA-Z]+',i):
                        data["area"].append(i)

                    # To get CITY NAME
                    match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                    match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                    match3 = re.findall('^[E].*',i)
                    if match1:
                        data["city"].append(match1[0])
                    elif match2:
                        data["city"].append(match2[0])
                    elif match3:
                        data["city"].append(match3[0])

                    # To get STATE
                    state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                    if state_match:
                        data["state"].append(i[:9])
                    elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
                        data["state"].append(i.split()[-1])
                    if len(data["state"])== 2:
                        data["state"].pop(0)

                    # To get PINCODE        
                    if len(i)>=6 and i.isdigit():
                        data["pin_code"].append(i)
                    elif re.findall('[a-zA-Z]{9} +[0-9]',i):
                        data["pin_code"].append(i[10:])
            get_data(result)
            
            #FUNCTION TO CREATE DATAFRAME
            def create_df(data):
                df = pd.DataFrame(data)
                return df
            df = create_df(data)
            st.success("### Business Card Details Extracted!")
            st.write(df)
            
            if st.button("SAVE"):
                config['database'] = 'bizcardx_db'
                mydb = sql.connect(**config)
                mycursor = mydb.cursor(buffered=True)
                for i,row in df.iterrows():
                    #here %S means string values 
                    sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                    #mycursor.execute(sql, tuple(row))
                    mycursor.execute(sql, tuple(row))
                    # the connection is not auto committed by default, so we must commit to save our changes
                    mydb.commit()
                    # Close the database connection
                    mydb.close()
                st.success("#### Saved the business card details successfully!")
            
    # MODIFY MENU    
    if selected == "Existing Card Details":
        st.markdown("### Existing Card Details to View / Modify / Delete")
        tab1, tab2, tab3 = st.tabs(["View", "Modify", "Delete"])
        column1,column2 = st.columns(2,gap="large")
        config['database'] = 'bizcardx_db'
        mydb = sql.connect(**config)
        mycursor = mydb.cursor(buffered=True)

        with tab1:
            st.markdown("#### View Business Card Details")
            config['database'] = 'bizcardx_db'
            mydb = sql.connect(**config)
            mycursor = mydb.cursor(buffered=True)
            if st.button("Refresh"):
                mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data")
                updated_df = pd.DataFrame(mycursor.fetchall(),columns=["Company_Name","Card_Holder","Designation","Mobile_Number","Email","Website","Area","City","State","Pin_Code"])
                updated_df.index = updated_df.index + 1
                st.write(updated_df)
            # Close the database connection
            mydb.close()

        with tab2:
            config['database'] = 'bizcardx_db'
            mydb = sql.connect(**config)
            mycursor = mydb.cursor(buffered=True)
            try:
                mycursor.execute("SELECT card_holder FROM card_data")
                result = mycursor.fetchall()
                business_cards = {}
                for row in result:
                    business_cards[row[0]] = row[0]
                selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))
                st.markdown("#### Update or modify any data below")
                mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder=%s",
                                (selected_card,))
                result = mycursor.fetchone()

                # DISPLAYING ALL THE INFORMATIONS
                company_name = st.text_input("Company_Name", result[0])
                card_holder = st.text_input("Card_Holder", result[1])
                designation = st.text_input("Designation", result[2])
                mobile_number = st.text_input("Mobile_Number", result[3])
                email = st.text_input("Email", result[4])
                website = st.text_input("Website", result[5])
                area = st.text_input("Area", result[6])
                city = st.text_input("City", result[7])
                state = st.text_input("State", result[8])
                pin_code = st.text_input("Pin_Code", result[9])

                if st.button("Save Card Details"):
                    # Update the information for the selected business card in the database
                    mycursor.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                        WHERE card_holder=%s""", (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,selected_card))
                    mydb.commit()
                    st.success("Business Card Details Updated Successfully.")

            except:
                st.warning("There is no data available in the storage")
                # Close the database connection
                mydb.close()
     
        with tab3:
            config['database'] = 'bizcardx_db'
            mydb = sql.connect(**config)
            mycursor = mydb.cursor(buffered=True)
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
            st.write(f"### You have selected :red[**{selected_card}'s**] card to delete")
            mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder=%s",
                            (selected_card,))
            result = pd.DataFrame(mycursor.fetchall(),columns=["Company_Name","Card_Holder","Designation","Mobile_Number","Email","Website","Area","City","State","Pin_Code"])
            result.index = result.index + 1
            st.write(result)
            if st.button("DELETE"):
                mycursor.execute(f"DELETE FROM card_data WHERE card_holder='{selected_card}'")
                mydb.commit()
                st.success("Business card information deleted successfully.")
                # Close the database connection
                mydb.close()
