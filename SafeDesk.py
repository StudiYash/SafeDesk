import cv2
import os
import time
import smtplib
import random
import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageTk
import ctypes

# Email credentials (Replace with your actual credentials)
SENDER_EMAIL = "sender_email"
APP_PASSWORD = "app_password"  # Replace with your app password
RECEIVER_EMAIL = "receiver_email"  # Replace with your email

# Password for authentication
CORRECT_PASSWORD = "authentication_password"

# Path to the SafeDesk Logo (update this path as needed)
SAFEDESK_LOGO_PATH = "Path to SafeDesk App Banner Image"
BSOD_IMG = " Path to Blue Screen of Death Image"  # Replace with your image path

# Directories
OWNER_IMAGES_DIR = "Path to Owner Images Directory"

# Global variables
otp_code = ""
otp_expiry_time = None

# Input blocking/unblocking functions
def block_input():
    """Block keyboard and mouse inputs."""
    try:
        ctypes.windll.user32.BlockInput(True)
        print("Inputs blocked.")
    except Exception as e:
        print(f"Failed to block inputs: {e}")

def unblock_input():
    """Unblock keyboard and mouse inputs."""
    try:
        ctypes.windll.user32.BlockInput(False)
        print("Inputs unblocked.")
    except Exception as e:
        print(f"Failed to unblock inputs: {e}")

# Owner image initialization
def initialize_owner_images():
    """Check for owner images and capture if not present."""
    if not os.path.exists(OWNER_IMAGES_DIR):
        os.makedirs(OWNER_IMAGES_DIR)
    
    images = os.listdir(OWNER_IMAGES_DIR)
    if len(images) < 10:
        print("Owner images not found. Capturing owner images...")
        capture_owner_images()
    else:
        print("Owner images already exist.")

def capture_owner_images():
    """Capture 10 images of the owner with a 3-second interval in a styled full-screen window."""
    cap = cv2.VideoCapture(0)
    count = 0

    # Create the full-screen window with a gold background
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.overrideredirect(1)  # Remove window controls
    root.configure(bg="black")  # Set the entire window's background to gold

    # Title Label (Top Message)
    title_label = tk.Label(
        root,
        text="Owner images have not been found.",
        font=("Arial", 32),
        bg="light pink",
        fg="blue",
        pady=20
    )
    title_label.pack(fill="x")

    # Frame for Camera Feed (centered)
    camera_frame_container = tk.Frame(root, bg="black")  # Keep the container background gold
    camera_frame_container.pack(expand=True, pady=20)

    # Camera Feed with black border
    camera_frame = tk.Label(camera_frame_container, bg="goldenrod", padx=10, pady=10)  # Black border using padding
    camera_frame.pack()

    # Progress Label (Bottom Message)
    progress_label = tk.Label(
        root,
        text="",
        font=("Arial", 24),
        bg="light pink",
        fg="blue",
        pady=20
    )
    progress_label.pack(fill="x", side="bottom")

    def update_feed():
        """Update the camera feed in the Tkinter window."""
        nonlocal count
        ret, frame = cap.read()
        if not ret:
            print("Error accessing the camera.")
            root.destroy()
            return

        # Resize the frame to a rectangle format
        frame_height = int(root.winfo_screenheight() * 0.6)
        frame_width = int(frame_height * 1.8)  # Aspect ratio 3:2
        frame_resized = cv2.resize(frame, (frame_width, frame_height))

        # Convert the frame to a format Tkinter can display
        cv2_image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2_image)
        imgtk = ImageTk.PhotoImage(image=img)
        camera_frame.imgtk = imgtk
        camera_frame.configure(image=imgtk)

        # Save the current frame as an image
        if count < 10:
            cv2.imwrite(f"{OWNER_IMAGES_DIR}/owner_{count}.jpg", frame)
            count += 1
            progress_label.config(text=f"Capturing image {count} of 10")
            root.after(3000, update_feed)  # Capture next image after 3 seconds
        else:
            # Capture complete, close the window
            root.destroy()

    # Start capturing images
    update_feed()
    root.mainloop()

    cap.release()
    print("Owner images captured and saved.")

def countdown_dialog(seconds, message, safedesk_logo_path):
    """Display a full-screen countdown dialog with the SafeDesk Logo at the top and styled countdown text."""
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.overrideredirect(1)  # Disable window controls
    
    # Set up the layout
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
    
    # Load and display the SafeDesk Logo at the top 80% of the screen
    try:
        logo_img = Image.open(safedesk_logo_path)
        logo_img = logo_img.resize((root.winfo_screenwidth(), int(root.winfo_screenheight() * 0.8)), Image.Resampling.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(root, image=logo_photo)
        logo_label.place(x=0, y=0, relwidth=1, relheight=0.8)
    except Exception as e:
        print(f"Error loading SafeDesk Logo: {e}")
        root.destroy()
        return

    # Display the countdown message at the bottom 20% of the screen
    msg_frame = tk.Frame(root, height=int(root.winfo_screenheight() * 0.2), bg="light pink")
    msg_frame.place(x=0, rely=0.8, relwidth=1, relheight=0.2)
    label = tk.Label(
        msg_frame,
        text="",
        font=("Arial", 32),  # Font size and style
        bg="light pink",  # Background color
        fg="blue",  # Text color
        justify="center",  # Center the text
        anchor="center",  # Center alignment within the frame
    )
    label.pack(expand=True)

    # Update the countdown
    for i in range(seconds, 0, -1):
        label.config(text=f"{message}\n{i} seconds remaining")
        root.update()
        time.sleep(1)

    root.destroy()

# Display full-screen image
def display_fullscreen_image(BSOD_IMG):
    """Display a full-screen image."""
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.overrideredirect(1)
    img = Image.open(BSOD_IMG)
    img = img.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=photo)
    label.pack()
    root.update()
    return root  # Return the root to keep the window open

# Face recognition
def face_recognition():
    """Perform face recognition and return True if face matches owner."""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    owner_encodings = []
    
    # Load owner images and compute encodings
    for img_name in os.listdir(OWNER_IMAGES_DIR):
        img_path = os.path.join(OWNER_IMAGES_DIR, img_name)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        owner_encodings.append(img)
    
    # Start video capture for face detection
    cap = cv2.VideoCapture(0)
    match_found = False
    start_time = time.time()
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, 1.3, 6)
        for (x, y, w, h) in faces:
            face_roi = gray_frame[y:y+h, x:x+w]
            try:
                face_roi_resized = cv2.resize(face_roi, (owner_encodings[0].shape[1], owner_encodings[0].shape[0]))
            except Exception as e:
                continue
            # Compare with owner encodings
            for owner_face in owner_encodings:
                res = cv2.matchTemplate(face_roi_resized, owner_face, cv2.TM_CCOEFF_NORMED)
                threshold = 0.6
                loc = np.where(res >= threshold)
                if len(loc[0]) > 0:
                    match_found = True
                    break
            if match_found:
                break
        if match_found or (time.time() - start_time) > 15:
            break
        if not match_found:
            print("Face detection running in the background...")
    cap.release()
    cv2.destroyAllWindows()
    return match_found

# OTP functions
def send_otp_via_email():
    """Send an OTP to the user's email."""
    global otp_code, otp_expiry_time
    otp_code = str(random.randint(100000, 999999))
    otp_expiry_time = time.time() + 120  # OTP valid for 2 minutes
    subject = "Your OTP Code"
    message = f"Your OTP code is: {otp_code}"
    text = f"Subject: {subject}\n\n{message}"
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, text)
        server.quit()
        print(f"OTP sent to {RECEIVER_EMAIL}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def otp_dialog():
    """Display a full-screen OTP entry dialog."""
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.overrideredirect(1)
    root.focus_force()
    countdown_time = 120  # 2 minutes
    otp_sent_time = time.time()
    otp_var = tk.StringVar()
    timer_id = None  # To store the ID of the scheduled after() event

    def validate_otp():
        """Validate the entered OTP."""
        user_input = otp_var.get().strip()
        if user_input == otp_code:
            messagebox.showinfo("Success", "OTP verified successfully!")
            if timer_id:
                root.after_cancel(timer_id)  # Cancel the timer if running
            root.destroy()  # Close the OTP dialog
            final_success_dialog(SAFEDESK_LOGO_PATH)  # Display the success dialog and terminate
        else:
            error_label.config(text="Incorrect OTP. Try again.")
            otp_var.set("")  # Clear the entry field

    def resend_otp():
        """Resend the OTP to the user's email."""
        if time.time() - otp_sent_time >= 20:
            send_otp_via_email()
            error_label.config(text="OTP resent to your email.")
        else:
            error_label.config(text="Please wait before resending OTP.")

    def update_timer():
        """Update the countdown timer."""
        nonlocal timer_id
        remaining_time = int(otp_expiry_time - time.time())
        if remaining_time <= 0:
            messagebox.showinfo("Timeout", "OTP entry time expired.")
            if timer_id:
                root.after_cancel(timer_id)  # Cancel the timer if running
            root.destroy()  # Close the OTP dialog
            block_input()  # Block inputs again
            main_workflow()
        else:
            timer_label.config(text=f"Time remaining: {remaining_time} seconds")
            timer_id = root.after(1000, update_timer)  # Schedule the next timer update

    def on_close():
        """Handle the window close event."""
        if timer_id:
            root.after_cancel(timer_id)  # Cancel the timer if running
        root.destroy()

    unblock_input()  # Unblock inputs for OTP entry

    # OTP Entry UI
    label = tk.Label(root, text="Enter the OTP sent to your email:", font=("Arial", 24))
    label.pack(pady=20)
    entry = tk.Entry(root, textvariable=otp_var, font=("Arial", 24), width=10)
    entry.pack(pady=10)
    entry.focus()
    entry.bind('<Return>', lambda event: validate_otp())  # Bind "Enter" key to validate
    submit_button = tk.Button(root, text="Submit", command=validate_otp, font=("Arial", 18))
    submit_button.pack(pady=10)
    resend_button = tk.Button(root, text="Resend OTP", command=resend_otp, font=("Arial", 14))
    resend_button.pack(pady=5)
    error_label = tk.Label(root, text="", fg="red", font=("Arial", 16))
    error_label.pack(pady=5)
    timer_label = tk.Label(root, text="", font=("Arial", 18))
    timer_label.pack(pady=10)

    # Start the countdown timer
    update_timer()

    # Bind the close event to cancel the timer
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

    block_input()  # Block inputs again if OTP not verified

def password_dialog():
    """Display a full-screen password entry dialog."""
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.overrideredirect(1)
    root.focus_force()
    countdown_time = 20  # 20 seconds
    password_var = tk.StringVar()
    timer_id = None  # To keep track of the timer ID

    def validate_password(event=None):
        """Validate the password entered by the user."""
        nonlocal timer_id
        if password_var.get() == CORRECT_PASSWORD:
            if timer_id is not None:
                root.after_cancel(timer_id)  # Cancel the countdown timer
            messagebox.showinfo("Success", "Password verified successfully!")
            root.destroy()  # Close the password dialog
            unblock_input()  # Ensure inputs are unblocked for OTP entry
            send_otp_via_email()  # Start the OTP process
            otp_dialog()  # Show the OTP dialog
        else:
            error_label.config(text="Incorrect password. Try again.")
            password_var.set("")  # Clear the password field

    def timer_expired():
        """Handle the case when the timer expires."""
        nonlocal timer_id
        timer_id = None  # Clear the timer ID
        messagebox.showinfo("Timeout", "Password entry time expired.")
        root.destroy()  # Close the password dialog
        block_input()  # Block inputs again
        main_workflow()  # Restart the process with the 10-second timer

    def update_timer():
        """Update the countdown timer."""
        nonlocal countdown_time, timer_id
        countdown_time -= 1
        if countdown_time <= 0:
            timer_expired()  # Trigger timeout when the countdown reaches zero
        else:
            timer_label.config(text=f"Time remaining: {countdown_time} seconds")
            timer_id = root.after(1000, update_timer)  # Update every second

    # Unblock inputs for password entry
    unblock_input()

    # Password Entry UI
    label = tk.Label(root, text="Enter your password:", font=("Arial", 24))
    label.pack(pady=20)
    entry = tk.Entry(root, textvariable=password_var, show="*", font=("Arial", 24), width=15)
    entry.pack(pady=10)
    entry.focus()  # Set focus to the password entry field
    entry.bind('<Return>', validate_password)  # Bind "Enter" key to validate the password

    submit_button = tk.Button(root, text="Submit", command=validate_password, font=("Arial", 18))
    submit_button.pack(pady=10)

    error_label = tk.Label(root, text="", fg="red", font=("Arial", 16))
    error_label.pack(pady=5)

    timer_label = tk.Label(root, text="", font=("Arial", 18))
    timer_label.pack(pady=10)

    # Start the countdown timer
    update_timer()

    root.mainloop()

def final_success_dialog(safedesk_logo_path):
    """Display a full-screen success message after OTP verification."""
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.overrideredirect(1)  # Remove window controls
    root.configure(bg="goldenrod")  # Set the entire window's background to gold

    # Load and display the SafeDesk Logo at the top 80% of the screen
    try:
        logo_img = Image.open(safedesk_logo_path)
        logo_img = logo_img.resize((root.winfo_screenwidth(), int(root.winfo_screenheight() * 0.8)), Image.Resampling.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(root, image=logo_photo, bg="goldenrod")
        logo_label.place(x=0, y=0, relwidth=1, relheight=0.8)
    except Exception as e:
        print(f"Error loading SafeDesk Logo: {e}")
        root.destroy()
        return

    # Success Message in the Bottom 20%
    msg_frame = tk.Frame(root, bg="light pink", height=int(root.winfo_screenheight() * 0.2))
    msg_frame.place(x=0, rely=0.8, relwidth=1, relheight=0.2)
    label = tk.Label(
        msg_frame,
        text="User Identity Verified Successfully!",
        font=("Arial", 36, "bold"),  # Bold text
        bg="light pink",
        fg="green",
        pady=20
    )
    label.pack(expand=True)

    # Display the window for 10 seconds
    root.update()
    time.sleep(10)  # Display for 10 seconds
    root.destroy()
    print("Authentication complete. Program terminating.")
    exit()  # Terminate the program

def main_workflow():
    """Main workflow of the application."""
    initialize_owner_images()
    countdown_dialog(10, "Inputs will be blocked soon.", SAFEDESK_LOGO_PATH)
    block_input()  # Block inputs
    if not os.path.exists(BSOD_IMG):
        print(f"Image not found at {BSOD_IMG}. Please check the path.")
        exit()
    image_window = display_fullscreen_image(BSOD_IMG)
    if face_recognition():
        image_window.destroy()
        unblock_input()  # Unblock inputs
        send_otp_via_email()
        otp_dialog()
    else:
        image_window.destroy()
        unblock_input()  # Unblock inputs for password entry
        password_dialog()

if __name__ == "__main__":
    main_workflow()