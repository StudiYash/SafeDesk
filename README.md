> This project is under development and features mentioned below might differ in actual implementation.

# SafeDesk

**SafeDesk** is a security-focused application designed to protect your laptop when unattended. It leverages face detection to monitor for unauthorized access, disables input devices, and triggers alarms based on user-defined settings. With SafeDesk, you can ensure your device remains secure while you're away.

---

## Features

- **Face Detection :** Continuously monitors the environment using your laptop's camera to detect intruders.
- **Input Locking :** Disables keyboard, mouse, and external mouse inputs to prevent unauthorized use.
- **Alarm Trigger :** Plays an audio warning message if an intruder is detected or input is attempted.
- **Customizable Settings :**
  - Set the time duration for monitoring.
  - Enable or disable alarm sounds.
  - Define the duration of the alarm.
- **Intruder Image Capture :** Saves photos of detected faces for review.
- **Authentication :** Allows reactivation using a password or facial recognition.
- **Automatic Stop :** Program stops after the predefined monitoring time or upon reactivation by the authorized user.

---

## Getting Started

### Prerequisites

- Required Python libraries :
  - `opencv-python`
  - `playsound`
  - `pynput`
  - `face_recognition`

Install the dependencies using :
```bash
pip install opencv-python playsound pynput face_recognition
```

### How to Run

1. **Clone this repository :**
   ```bash
   git clone https://github.com/your-username/safedesk.git
   ```

2. **Navigate to the project directory :**
   ```bash
   cd safedesk
   ```

3. **Run the program :**
   ```bash
   python safedesk.py
   ```

## Usage Instructions

1. **Run the application**:
   - The program will ask you three setup questions:
     - Time duration for monitoring (in minutes).
     - Whether to enable the alarm (Yes/No).
     - Alarm duration (in seconds).

2. **Program Behavior**:
   - Displays a welcome screen and starts monitoring.
   - Disables all input devices while monitoring.
   - Captures images if a face is detected.
   - Shows a warning message and plays an alarm if unauthorized access is detected.

3. **Stopping the Program**:
   - Press and hold the **Escape** key.
   - Enter your password or use facial recognition to authenticate.

## Future Enhancements

- Multi-platform support (Windows, Linux, macOS).
- Customizable audio alarms.
- Integration with cloud storage for saving captured images.
- Advanced authentication methods (e.g., OTP, fingerprint).
- Enhanced logging and reporting for detected incidents.
