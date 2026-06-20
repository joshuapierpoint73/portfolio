using UnityEngine;
using UnityEngine.UI;

public class SettingsInGame : MonoBehaviour
{
    public Slider musicVolumeSlider;
    public Slider soundVolumeSlider;
    public GameObject settingsPanel;  // The pop-out canvas panel

    public static SettingsInGame Instance;  // Reference to the instance of this script
    public bool isSettingsMenuOpen = false;  // Track if the settings menu is open

    void Start()
    {
        // Make sure the instance is set correctly
        if (Instance == null)
            Instance = this;

        // Load saved values (or default to 1f)
        float savedMusicVolume = PlayerPrefs.GetFloat("MusicVolume", 1f);
        float savedSfxVolume = PlayerPrefs.GetFloat("SFXVolume", 1f);

        // Set slider values
        musicVolumeSlider.value = savedMusicVolume;
        soundVolumeSlider.value = savedSfxVolume;

        // Apply to AudioManager (make sure AudioManager has instance and methods to adjust volume)
        if (AudioManager.Instance != null)
        {
            AudioManager.Instance.SetMusicVolume(savedMusicVolume);
            AudioManager.Instance.SetSFXVolume(savedSfxVolume);
        }

        // Hide settings panel on start (assuming it is inactive by default)
        settingsPanel.SetActive(false);

        // Ensure the cursor is locked by default (if not in settings menu)
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }

    public void SetMusicVolume(float volume)
    {
        // Update the music volume in AudioManager
        AudioManager.Instance.SetMusicVolume(volume);
        PlayerPrefs.SetFloat("MusicVolume", volume);  // Save to PlayerPrefs
    }

    public void SetSFXVolume(float volume)
    {
        // Update the SFX volume in AudioManager
        AudioManager.Instance.SetSFXVolume(volume);
        PlayerPrefs.SetFloat("SFXVolume", volume);  // Save to PlayerPrefs
    }

    // Show the settings menu panel and unlock the cursor
    public void ShowSettingsMenu()
    {
        settingsPanel.SetActive(true);
        Cursor.lockState = CursorLockMode.None;  // Unlock the cursor
        Cursor.visible = true;  // Show the cursor
        isSettingsMenuOpen = true;  // Set settings menu as open
    }

    // Hide the settings menu panel and lock the cursor again
    public void HideSettingsMenu()
    {
        settingsPanel.SetActive(false);
        Cursor.lockState = CursorLockMode.Locked;  // Lock the cursor when exiting the menu
        Cursor.visible = false;  // Hide the cursor again
        isSettingsMenuOpen = false;  // Set settings menu as closed
    }

    // Call this function when the 'Q' key is pressed to toggle the menu
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Q))
        {
            if (settingsPanel.activeSelf)
            {
                HideSettingsMenu();
            }
            else
            {
                ShowSettingsMenu();
            }
        }
    }
}
