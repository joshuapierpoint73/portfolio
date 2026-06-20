using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class SettingsMenu : MonoBehaviour
{
    public Slider musicVolumeSlider;
    public Slider soundVolumeSlider;

    private string previousScene;

    void Start()
    {
        // Load saved values (or default to 1f)
        float savedMusicVolume = PlayerPrefs.GetFloat("MusicVolume", 1f);
        float savedSfxVolume = PlayerPrefs.GetFloat("SFXVolume", 1f);

        // Set slider values
        musicVolumeSlider.value = savedMusicVolume;
        soundVolumeSlider.value = savedSfxVolume;

        // Apply to AudioManager
        if (AudioManager.Instance != null)
        {
            AudioManager.Instance.SetMusicVolume(savedMusicVolume);
            AudioManager.Instance.SetSFXVolume(savedSfxVolume);
        }

        // Unlock cursor
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }

    public void SetMusicVolume(float volume)
    {
        AudioManager.Instance.SetMusicVolume(volume);
    }

    public void SetSFXVolume(float volume)
    {
        AudioManager.Instance.SetSFXVolume(volume);
    }

    public void BackToPreviousScene()
    {
        string previousScene = PlayerPrefs.GetString("PreviousScene", "MainMenu");

        // Only lock and hide the cursor if going back to the game
        if (previousScene == "Game") // Replace with your actual game scene name
        {
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }
        else
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        SceneManager.LoadScene(previousScene);
    }

}
