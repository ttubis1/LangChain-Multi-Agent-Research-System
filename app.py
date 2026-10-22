import streamlit as st
import sys
import os
from dotenv import load_dotenv

# טעינת משתנים מהקובץ .env
load_dotenv()

# הוספת תיקיית השורש לנתיב כדי שפייתון יכיר את תיקיית src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ייבוא הפונקציה מתוך src/pipelines/pipeline.py
from src.pipelines.pipeline import run_research_pipeline

# הגדרת מאפייני העמוד
st.set_page_config(
    page_title="Research Pipeline Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 מערכת מחקר מבוססת סוכנים")
st.write("הזן נושא למחקר והפעל את ה-Pipeline האוטומטי שלך.")

# תיבת קלט מהמשתמש
topic = st.text_input("נושא המחקר:", placeholder="לדוגמה: השפעת בינה מלאכותית על שוק העבודה")

# כפתור הפעלה
if st.button("התחל מחקר", type="primary"):
    if not topic.strip():
        st.warning("נא להזין נושא מחקר תקין לפני ההפעלה.")
    else:
        # פתיחת מסך טעינה בזמן שהפונקציה רצה
        with st.spinner("הסוכנים פועלים... מבצע מחקר וניתוח נתונים. אנא המתן..."):
            try:
                # קריאה לפונקציה מתוך הצינור
                result = run_research_pipeline(topic)
                
                st.success("המחקר הושלם בהצלחה!")
                
                # הצגת התוצאות
                st.markdown("### תוצאות המחקר:")
                if isinstance(result, str):
                    st.markdown(result)
                else:
                    st.json(result)
                    
            except Exception as e:
                st.error(f"אירעה שגיאה במהלך הרצת הצינור: {e}")