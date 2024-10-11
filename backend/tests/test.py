import pyautogui

def skip_to_next_song():
    # Simulates pressing the "Next Track" media key
    pyautogui.hotkey('prevtrack')
    pyautogui.hotkey('prevtrack')
    
    pyautogui.hotkey('nexttrack')

# Call the function to skip the song
skip_to_next_song()
