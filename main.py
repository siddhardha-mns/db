import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import re

# Supabase Configuration from Streamlit secrets
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to Supabase: {str(e)}")
        st.info("Please configure your Supabase credentials in .streamlit/secrets.toml")
        st.stop()

supabase: Client = init_supabase()

# Validation functions
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

# Database operations
def register_user(user_data):
    try:
        response = supabase.table('users').insert(user_data).execute()
        return True, "Registration successful!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def check_email_exists(email):
    try:
        response = supabase.table('users').select("email").eq("email", email).execute()
        return len(response.data) > 0
    except Exception as e:
        return False

def check_username_exists(username):
    try:
        response = supabase.table('users').select("username").eq("username", username).execute()
        return len(response.data) > 0
    except Exception as e:
        return False

# Main app
def main():
    st.set_page_config(page_title="User Registration", page_icon="📝", layout="centered")
    
    st.title("📝 User Registration Form")
    st.markdown("Please fill in all the required information to create your account.")
    st.markdown("---")
    
    # Create tabs for Registration and View Users
    tab1, tab2 = st.tabs(["Register", "View Users"])
    
    with tab1:
        with st.form("registration_form", clear_on_submit=True):
            st.subheader("Personal Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name *", placeholder="John")
                last_name = st.text_input("Last Name *", placeholder="Doe")
                username = st.text_input("Username *", placeholder="johndoe123")
            
            with col2:
                email = st.text_input("Email Address *", placeholder="john.doe@example.com")
                phone = st.text_input("Phone Number *", placeholder="+1234567890")
                date_of_birth = st.date_input("Date of Birth *", 
                    min_value=datetime(1900, 1, 1),
                    max_value=datetime.now())
            
            st.markdown("---")
            st.subheader("Account Security")
            
            col3, col4 = st.columns(2)
            
            with col3:
                password = st.text_input("Password *", type="password", 
                    placeholder="Min 8 chars, 1 uppercase, 1 number")
            
            with col4:
                confirm_password = st.text_input("Confirm Password *", type="password")
            
            st.markdown("---")
            st.subheader("Additional Information")
            
            col5, col6 = st.columns(2)
            
            with col5:
                gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other", "Prefer not to say"])
                country = st.text_input("Country", placeholder="United States")
            
            with col6:
                city = st.text_input("City", placeholder="New York")
                occupation = st.text_input("Occupation", placeholder="Software Engineer")
            
            address = st.text_area("Address", placeholder="123 Main Street, Apt 4B")
            
            st.markdown("---")
            
            # Terms and conditions
            terms_accepted = st.checkbox("I agree to the Terms and Conditions *")
            newsletter = st.checkbox("Subscribe to newsletter")
            
            # Submit button
            submitted = st.form_submit_button("Register", type="primary", use_container_width=True)
            
            if submitted:
                # Validation
                errors = []
                
                if not all([first_name, last_name, username, email, phone, password, confirm_password]):
                    errors.append("⚠️ Please fill in all required fields marked with *")
                
                if not validate_email(email):
                    errors.append("⚠️ Invalid email format")
                
                if not validate_phone(phone):
                    errors.append("⚠️ Invalid phone number format")
                
                is_valid_pwd, pwd_msg = validate_password(password)
                if not is_valid_pwd:
                    errors.append(f"⚠️ {pwd_msg}")
                
                if password != confirm_password:
                    errors.append("⚠️ Passwords do not match")
                
                if not terms_accepted:
                    errors.append("⚠️ You must accept the Terms and Conditions")
                
                if gender == "Select":
                    gender = None
                
                # Check for existing username/email
                if check_username_exists(username):
                    errors.append("⚠️ Username already exists")
                
                if check_email_exists(email):
                    errors.append("⚠️ Email already registered")
                
                # Display errors or proceed with registration
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Prepare user data
                    user_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "username": username,
                        "email": email,
                        "phone": phone,
                        "password": password,  # In production, hash this!
                        "date_of_birth": str(date_of_birth),
                        "gender": gender,
                        "country": country,
                        "city": city,
                        "address": address,
                        "occupation": occupation,
                        "newsletter_subscribed": newsletter,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Register user
                    success, message = register_user(user_data)
                    
                    if success:
                        st.success("✅ " + message)
                        st.balloons()
                        st.info("You can now login with your credentials!")
                    else:
                        st.error(message)
    
    with tab2:
        st.subheader("📋 Registered Users")
        
        try:
            response = supabase.table('users').select("id, first_name, last_name, username, email, created_at").execute()
            
            if response.data:
                import pandas as pd
                df = pd.DataFrame(response.data)
                st.dataframe(df, use_container_width=True)
                st.success(f"Total registered users: {len(df)}")
            else:
                st.info("No users registered yet.")
        except Exception as e:
            st.error(f"Error fetching users: {str(e)}")

if __name__ == "__main__":
    main()
